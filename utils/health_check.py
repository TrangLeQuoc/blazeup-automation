"""Backend service health-check engine.

Probes the ``/health`` endpoint of each microservice and prints an up/down
table. It is **per-domain**: each domain has a thin entry point at
``runner/<domain>/health.py`` that resolves that domain's ``API_BASE_URL`` and
service list, then calls :func:`check_services` here. The engine itself is
domain-agnostic and never needs editing when a domain is added.

Run (mirrors ``run_test``)::

    python -m runner.blazeup_admin.health
    python -m runner.blazeup_partner.health

No authentication is used — ``/health`` is a public liveness probe. A 2xx/3xx
response means the service is up; 502/timeout means it is down or not deployed.
"""

import asyncio
import io
import re
import time
import tokenize
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Matches a BlazeUp service prefix like "/sa-partners-api/", "/sa-auth-api/".
_SERVICE_RE = re.compile(r"/([a-z0-9]+(?:-[a-z0-9]+)*-api)/")

# Minimal ANSI colors (consistent with runner/test_runner.py).
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# Transient statuses worth one retry (gateway/service still warming up or flapping).
_RETRY_STATUSES = {502, 503, 504}
_RETRY_DELAY_S = 0.5

# OPTIONAL richer descriptions. Any service NOT listed here gets a readable label
# auto-derived from its name (see _default_label), so this map never needs to grow
# with the number of services — add an entry only when you want a fuller wording
# than the auto-derived one.
_SERVICE_LABELS = {
    "sa-partners-api": "Partner module API (partners, deals, commissions)",
}

# Tokens shown upper-cased in auto-derived labels (acronyms, not Title-cased).
_ACRONYMS = {"sa", "crm", "hr", "msp", "api", "ui", "ai", "id", "url", "kpi"}


def _default_label(service: str) -> str:
    """Derive a readable description from a service name when none is configured.

    Examples: ``sa-auth-api`` -> ``SA Auth`` · ``billing-api`` -> ``Billing``.
    So 200 services need 0 hand-written labels — only override the few you want
    to word more richly via _SERVICE_LABELS.
    """
    stem = service.removesuffix("-api").replace("-", " ").strip()
    if not stem:
        return service
    return " ".join(w.upper() if w in _ACRONYMS else w.capitalize() for w in stem.split())


def discover_services(domain: str) -> set[str]:
    """Return service prefixes used by ``api_clients/<domain>/``.

    Scans that domain's API client modules for ``/<name>-api/`` path prefixes
    that appear inside **string literals only** (real endpoint paths), so the
    health-check auto-covers whatever services the domain's tests actually call.

    Comments are ignored on purpose — otherwise a TODO example like
    ``# TODO: real path, e.g. "/partner-api/deals"`` in a scaffold client would
    register a fictional service that doesn't exist (a false 404).
    """
    base = _PROJECT_ROOT / "api_clients" / domain
    services: set[str] = set()
    if not base.exists():
        return services
    for py in base.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        source = py.read_text(encoding="utf-8")
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source).readline):
                if tok.type == tokenize.STRING:
                    for match in _SERVICE_RE.finditer(tok.string):
                        services.add(match.group(1))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # Fallback for unparseable files: scan code with comments stripped.
            for line in source.splitlines():
                for match in _SERVICE_RE.finditer(line.split("#", 1)[0]):
                    services.add(match.group(1))
    return services


def extra_services(domain: str) -> list[str]:
    """Services to monitor even if no API client references them yet.

    Read from ``config/<domain>/config.yaml`` (top-level ``services:`` list) — the
    single source of truth, shared by health.py + swagger_check.py. Combined with
    :func:`discover_services` (which auto-finds services used by client code).
    Returns ``[]`` when the file/key is absent.
    """
    import yaml  # local import: health-check only, keep module import-light

    cfg = _PROJECT_ROOT / "config" / domain / "config.yaml"
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        return list(data.get("services") or [])
    except Exception:  # noqa: BLE001 — missing/bad config → no extras
        return []


def _classify(status: int | None) -> str:
    """Map an HTTP status to a health state.

    up      = 2xx/3xx (service alive)
    missing = 404 (no /health route — service may be up but exposes no probe)
    down    = 5xx / other / no response (service dead or unreachable)
    """
    if status is None:
        return "down"
    if 200 <= status < 400:
        return "up"
    if status == 404:
        return "missing"
    return "down"


async def _probe(
    client: httpx.AsyncClient, service: str, health_path: str, retries: int = 1
) -> dict:
    """Probe one service's /health, retrying once on a transient error/status."""
    url = f"/{service}{health_path}"
    for attempt in range(retries + 1):
        started = time.perf_counter()
        try:
            resp = await client.get(url)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            if resp.status_code in _RETRY_STATUSES and attempt < retries:
                await asyncio.sleep(_RETRY_DELAY_S)
                continue
            return {
                "service": service,
                "status": resp.status_code,
                "ms": elapsed_ms,
                "state": _classify(resp.status_code),
                "error": None,
            }
        except (httpx.HTTPError, OSError) as exc:
            if attempt < retries:
                await asyncio.sleep(_RETRY_DELAY_S)
                continue
            return {
                "service": service,
                "status": None,
                "ms": None,
                "state": "down",
                "error": type(exc).__name__,
            }
    return {"service": service, "status": None, "ms": None, "state": "down", "error": "unknown"}


async def _run(
    api_base_url: str, services: list[str], health_path: str, timeout: float
) -> list[dict]:
    async with httpx.AsyncClient(base_url=api_base_url.rstrip("/"), timeout=timeout) as client:
        return await asyncio.gather(*[_probe(client, s, health_path) for s in services])


def check_services(
    domain: str,
    api_base_url: str,
    services: set[str] | list[str],
    *,
    health_path: str = "/health",
    timeout: float = 15.0,
    labels: dict[str, str] | None = None,
) -> int:
    """Probe every service's health endpoint, print a self-explanatory table.

    Returns ``0`` when every service is up, ``1`` when at least one is down,
    ``2`` when the API host is missing/invalid (config error).
    """
    labels = {**_SERVICE_LABELS, **(labels or {})}
    services = sorted(services)
    host = str(api_base_url or "").rstrip("/")

    # ── Header: explain WHAT this is checking ────────────────────────────────
    print(f"\n{_BOLD}{_CYAN}BlazeUp API Health Check — {domain}{_RESET}")
    print(f"{_DIM}Is each backend API service alive? (sends HTTP GET {health_path}){_RESET}")
    print(f"{_DIM}Host: {host or '(empty)'}{_RESET}")
    print("-" * 78)

    # ── Guard: bad/missing host — fail clearly instead of probing a junk URL ──
    if not host.startswith(("http://", "https://")):
        print(f"  {_RED}❌ API_BASE_URL is missing or invalid: {api_base_url!r}{_RESET}")
        print(
            f"  {_DIM}→ Set a valid URL in config/{domain}/.env (API_BASE_URL=https://...){_RESET}"
        )
        print()
        return 2

    if not services:
        print("  (no services discovered — add an API client or config.yaml `services:`)")
        print("-" * 78)
        return 0

    print(f"  {'STATE':<13} {'SERVICE':<20} {'RESPONSE':<16} WHAT IT IS")
    results = asyncio.run(_run(host, services, health_path, timeout))

    # state → (color, fixed-width label)
    fmt = {
        "up": (_GREEN, "✅ UP"),
        "missing": (_YELLOW, "⚠ NO /health"),
        "down": (_RED, "❌ DOWN"),
    }
    counts = {"up": 0, "missing": 0, "down": 0}
    for r in sorted(results, key=lambda x: x["service"]):
        desc = labels.get(r["service"]) or _default_label(r["service"])
        state = r["state"]
        counts[state] += 1
        color, label_text = fmt[state]
        badge = f"{color}{label_text:<12}{_RESET}"
        response = r["error"] if r["status"] is None else f"{r['status']}, {r['ms']}ms"
        print(f"  {badge} {r['service']:<20} {response:<16} {_DIM}{desc}{_RESET}")

    print("-" * 78)
    up, missing, down = counts["up"], counts["missing"], counts["down"]
    total = len(results)
    if down:
        names = ", ".join(r["service"] for r in results if r["state"] == "down")
        print(f"  {_RED}⚠  {up}/{total} UP — DOWN: {names}{_RESET}")
        print(f"  {_DIM}→ Tests calling the down service(s) will fail until they recover.{_RESET}")
    elif missing:
        names = ", ".join(r["service"] for r in results if r["state"] == "missing")
        print(f"  {_YELLOW}✓ {up}/{total} reachable, but no /health route on: {names}{_RESET}")
        print(
            f"  {_DIM}→ 404 = service likely up but exposes no /health (can't confirm here).{_RESET}"
        )
    else:
        print(
            f"  {_GREEN}✅ {up}/{total} services UP{_RESET} "
            f"— backend reachable; API tests for {domain} can run."
        )
    print()
    # Exit 1 only on a genuine DOWN; a missing /health route is a warning, not a failure.
    return 1 if down else 0
