"""Swagger / OpenAPI drift detector.

For each service of a domain, fetches the live OpenAPI spec
(``<api_base_url>/<service>/api-docs-json``), extracts its endpoint set, and
compares it to a saved baseline so you can see what the backend team
added / removed / changed.

It is **per-domain** (like health-check): a thin entry point at
``runner/<domain>/swagger_check.py`` resolves that domain's ``API_BASE_URL`` and
service list, then calls :func:`check_swagger`.

Two modes:
    python -m runner.<domain>.swagger_check          # compare → show drift (no write)
    python -m runner.<domain>.swagger_check --save   # save baseline + append CHANGELOG

Files (under ``docs/api-snapshots/<domain>/``):
    <service>.endpoints.json   — per-service baseline (endpoint index)
    CHANGELOG.md               — per-domain history (all services, newest on top)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SNAPSHOT_ROOT = _PROJECT_ROOT / "docs" / "api-snapshots"

# Candidate paths for the JSON spec (NestJS default is /api-docs-json).
_SPEC_PATHS = ("/api-docs-json", "/api-docs/json", "/api-docs.json", "/swagger.json")

_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _extract_endpoints(spec: dict) -> dict[str, dict]:
    """Reduce an OpenAPI spec to ``{"METHOD /path": {params, body_required, responses}}``.

    Structured (not a flat string) so a CHANGED endpoint can report exactly which
    params / responses / body-requirement changed.
    """
    index: dict[str, dict] = {}
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            index[f"{method.upper()} {path}"] = {
                "params": sorted(p.get("name", "") for p in (op.get("parameters") or [])),
                "body_required": bool((op.get("requestBody") or {}).get("required")),
                "responses": sorted(str(c) for c in (op.get("responses") or {})),
            }
    return index


def _describe_change(old: dict, new: dict) -> list[str]:
    """Return human-readable notes on what differs between two endpoint specs."""
    if not isinstance(old, dict) or not isinstance(new, dict):
        return ["(baseline re-formatted — re-saved)"]
    notes: list[str] = []
    for field in ("params", "responses"):
        old_set, new_set = set(old.get(field, [])), set(new.get(field, []))
        if old_set != new_set:
            parts = []
            if new_set - old_set:
                parts.append(f"+{sorted(new_set - old_set)}")
            if old_set - new_set:
                parts.append(f"-{sorted(old_set - new_set)}")
            notes.append(f"{field}: {' '.join(parts)}")
    if old.get("body_required") != new.get("body_required"):
        notes.append(f"body_required: {old.get('body_required')} → {new.get('body_required')}")
    return notes or ["(spec changed)"]


async def _fetch_spec(host: str, service: str, timeout: float = 20.0) -> tuple[dict | None, str]:
    """Fetch a service's OpenAPI JSON. Returns ``(spec, "")`` or ``(None, reason)``.

    Retries the whole path-scan once when nothing responds, so a service that
    momentarily flaps (e.g. a transient 404/5xx while restarting) is not skipped
    as "missing spec" — same robustness as the health-check.
    """
    async with httpx.AsyncClient(base_url=host, timeout=timeout) as client:
        last = "no spec path responded"
        for attempt in range(1, 3):  # 2 attempts: a transient flap shouldn't skip a real service
            for suffix in _SPEC_PATHS:
                try:
                    resp = await client.get(f"/{service}{suffix}")
                except (httpx.HTTPError, OSError) as exc:
                    last = type(exc).__name__
                    continue
                if resp.status_code == 200:
                    try:
                        return resp.json(), ""
                    except ValueError:
                        last = "200 but not JSON"
                        continue
                last = f"HTTP {resp.status_code}"
            if attempt == 1:
                await asyncio.sleep(0.5)  # brief backoff before the retry
        return None, last


def _diff(
    old: dict[str, dict], new: dict[str, dict]
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    added = sorted(k for k in new if k not in old)
    removed = sorted(k for k in old if k not in new)
    changed = {
        k: _describe_change(old[k], new[k]) for k in sorted(new) if k in old and old[k] != new[k]
    }
    return added, removed, changed


def _append_changelog(
    changelog: Path, domain: str, ts: str, service: str, diff: tuple, baseline: bool, count: int
) -> None:
    """Prepend a dated entry (newest on top) to the per-domain CHANGELOG."""
    added, removed, changed = diff
    lines = [f"## {ts} · {service}"]
    if baseline:
        lines.append(f"- baseline ({count} endpoints)")
    else:
        lines += [f"- 🟢 ADDED   {k}" for k in added]
        lines += [f"- 🔴 REMOVED {k}" for k in removed]
        for k, notes in changed.items():
            lines.append(f"- 🟡 CHANGED {k}")
            lines += [f"    · {n}" for n in notes]
    entry = "\n".join(lines) + "\n\n"

    header = f"# API Change Log — {domain}\n"
    if changelog.exists():
        body = changelog.read_text(encoding="utf-8")
        rest = body[len(header) :].lstrip("\n") if body.startswith(header) else body
        content = f"{header}\n{entry}{rest}"
    else:
        content = f"{header}\n{entry}"
    changelog.parent.mkdir(parents=True, exist_ok=True)
    changelog.write_text(content, encoding="utf-8", newline="\n")


def check_swagger(
    domain: str,
    api_base_url: str,
    services: set[str] | list[str],
    *,
    save: bool = False,
) -> int:
    """Compare each service's live spec to its baseline. Returns an exit code:

    ``0`` no drift · ``3`` drift detected · ``2`` config error (bad host).
    """
    host = str(api_base_url or "").rstrip("/")
    domain_dir = _SNAPSHOT_ROOT / domain
    changelog = domain_dir / "CHANGELOG.md"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    mode = "save baseline" if save else "compare"
    print(f"\n{_BOLD}{_CYAN}Swagger drift — {domain}{_RESET}  ({mode})")
    print(f"{_DIM}Host: {host or '(empty)'}{_RESET}")
    print("-" * 78)

    if not host.startswith(("http://", "https://")):
        print(f"  {_RED}❌ API_BASE_URL is missing or invalid: {api_base_url!r}{_RESET}")
        print()
        return 2

    total_drift = 0
    for service in sorted(services):
        spec, err = asyncio.run(_fetch_spec(host, service))
        if spec is None:
            print(f"  {_YELLOW}⚠ {service}{_RESET}: cannot fetch spec ({err}) — skipped")
            continue

        new_index = _extract_endpoints(spec)
        snap_file = domain_dir / f"{service}.endpoints.json"
        old_index: dict[str, str] = {}
        if snap_file.exists():
            old_index = json.loads(snap_file.read_text(encoding="utf-8"))

        added, removed, changed = _diff(old_index, new_index)
        is_baseline = not snap_file.exists()
        n = len(added) + len(removed) + len(changed)
        total_drift += n

        if is_baseline:
            print(f"  {_DIM}{service}: baseline ({len(new_index)} endpoints){_RESET}")
        elif n == 0:
            print(f"  {_GREEN}{service}: no changes{_RESET}")
        else:
            print(
                f"  {_BOLD}{service}{_RESET}: 🟢 {len(added)} · 🔴 {len(removed)} · 🟡 {len(changed)}"
            )
            for k in added:
                print(f"     {_GREEN}🟢 ADDED  {k}{_RESET}")
            for k in removed:
                print(f"     {_RED}🔴 REMOVED {k}{_RESET}")
            for k, notes in changed.items():
                print(f"     {_YELLOW}🟡 CHANGED {k}{_RESET}")
                for note in notes:
                    print(f"         {_DIM}{note}{_RESET}")

        if save:
            snap_file.parent.mkdir(parents=True, exist_ok=True)
            snap_file.write_text(
                json.dumps(new_index, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
            )
            if is_baseline or n:
                _append_changelog(
                    changelog,
                    domain,
                    ts,
                    service,
                    (added, removed, changed),
                    is_baseline,
                    len(new_index),
                )

    print("-" * 78)
    if save:
        print(f"  {_GREEN}✓ Baseline saved{_RESET} → {domain_dir}/  (CHANGELOG updated)")
    elif total_drift == 0:
        print(f"  {_GREEN}✓ No drift — specs match the saved baseline.{_RESET}")
    else:
        print(
            f"  {_YELLOW}⚠ {total_drift} change(s) detected.{_RESET} Review, then re-run with --save."
        )
    print()
    return 0 if (save or total_drift == 0) else 3
