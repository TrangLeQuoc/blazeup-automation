"""Pre-run environment gate — fail in 10 seconds instead of 40 minutes.

Why this exists
---------------
When staging is unreachable, every test still runs: each one opens a browser or a
client, waits out its timeouts, and reports BLOCKED. A full suite burns tens of
minutes to tell you one thing — "the environment is down". Worse, the real reason
is buried in the middle of the log.

A concrete case (2026-08-07): ``stgpartners.blazeup.ai`` served a certificate
Chromium rejected. The session-scoped partner login failed once, and **21 partner
UI test cases** went BLOCKED behind it. One infrastructure fault, 21 red rows and
a run that took minutes to say so.

What it checks — and why not just the existing health-check
-----------------------------------------------------------
``utils.health_check.check_services`` probes the backend ``/health`` endpoints over
httpx. That is the right tool for "is a microservice alive", but it would NOT have
caught the case above, for two reasons:

1. it only looks at ``API_BASE_URL`` — the fault was on a **UI origin**;
2. httpx and Chromium do not share a trust store. On the day of the incident Python
   verified that certificate happily while Chromium refused it.

So UI origins are probed with **Chromium itself** — the same engine the tests use —
which is the only way to answer "can the browser actually load the login page?".

Scope of the abort (deliberately narrow)
----------------------------------------
The run is aborted **only when every probed surface is down** — i.e. when nothing
could possibly run. If one surface is dead and another is alive, the run CONTINUES
with a loud warning.

That rule comes straight from measuring the incident above: the 21 blocked TCs cost
**10.8 seconds in total**, not minutes — the session-scoped login fails once (10.8 s)
and the other 20 skip in 0.00 s. Meanwhile that same run still produced 98 real
results (85 pass / 13 fail) from the API and SA surfaces, which were healthy.

Aborting everything would therefore have traded 98 results for an 8-second saving —
a bad deal, and worse on CI where nobody can add ``--no-preflight`` by hand. So the
gate only pays for itself in the total-outage case; in a partial outage its job is to
say clearly WHICH surface is down and get out of the way.
"""

import asyncio
from typing import Any

import httpx
from loguru import logger

# Same palette as runner/test_runner.py and utils/health_check.py.
_GREEN = "\033[92m"
_RED = "\033[91m"
_CYAN = "\033[96m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# One retry: an edge/CDN hiccup can resolve within a second, and aborting a whole
# suite on a single blip would make the gate itself the flaky part.
_ATTEMPTS = 2
_RETRY_DELAY_S = 2.0
_BROWSER_TIMEOUT_MS = 20_000
_API_TIMEOUT_S = 15.0


async def _probe_origin(browser: Any, name: str, url: str) -> dict[str, Any]:
    """Load *url* in Chromium. Any HTTP response means the origin is serving."""
    login_url = url.rstrip("/") + "/login"
    last = "unknown"
    for attempt in range(1, _ATTEMPTS + 1):
        context = await browser.new_context()
        page = await context.new_page()
        try:
            response = await page.goto(login_url, wait_until="commit", timeout=_BROWSER_TIMEOUT_MS)
            status = response.status if response else 0
            return {"name": name, "url": login_url, "ok": True, "detail": f"HTTP {status}"}
        except Exception as exc:  # noqa: BLE001 — any navigation failure is a red flag
            last = str(exc).splitlines()[0][:120]
        finally:
            await context.close()
        if attempt < _ATTEMPTS:
            await asyncio.sleep(_RETRY_DELAY_S)
    return {"name": name, "url": login_url, "ok": False, "detail": last}


async def _probe_ui_origins(origins: dict[str, str], browser_name: str) -> list[dict[str, Any]]:
    """Probe every UI origin with one shared Chromium instance."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        launcher = getattr(p, browser_name)
        browser = await launcher.launch(headless=True)
        try:
            return [await _probe_origin(browser, n, u) for n, u in origins.items()]
        finally:
            await browser.close()


async def _probe_api(api_base_url: str) -> dict[str, Any]:
    """Is the API gateway answering at all? (any HTTP status counts as alive)."""
    last = "unknown"
    for attempt in range(1, _ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=_API_TIMEOUT_S) as client:
                r = await client.get(api_base_url.rstrip("/") + "/", follow_redirects=True)
            return {
                "name": "API gateway",
                "url": api_base_url,
                "ok": True,
                "detail": f"HTTP {r.status_code}",
            }
        except Exception as exc:  # noqa: BLE001 — connect/TLS/timeout all mean "not usable"
            last = f"{type(exc).__name__}: {str(exc).splitlines()[0][:90]}".strip()
        if attempt < _ATTEMPTS:
            await asyncio.sleep(_RETRY_DELAY_S)
    return {"name": "API gateway", "url": api_base_url, "ok": False, "detail": last}


def run_preflight(
    *,
    api_base_url: str | None,
    ui_origins: dict[str, str],
    browser: str = "chromium",
) -> tuple[bool, list[str]]:
    """Probe what the selected run needs. Returns ``(should_abort, failures)``.

    ``should_abort`` is True only when EVERY probed surface failed — a partial outage
    returns ``(False, [...])`` so the caller runs anyway with the failures reported.

    ``ui_origins`` maps a human label to a base URL and should contain ONLY the
    origins the selected tests actually use.
    """
    checks: list[dict[str, Any]] = []

    print(f"\n{_BOLD}{_CYAN}Preflight — is the environment usable?{_RESET}")
    print(f"{_DIM}Checked before running, so an outage costs seconds, not the whole suite.{_RESET}")
    print("-" * 78)

    if api_base_url:
        checks.append(asyncio.run(_probe_api(api_base_url)))
    if ui_origins:
        # Chromium, not httpx: the browser has its own trust store, and it is the
        # browser that has to load these pages.
        checks.extend(asyncio.run(_probe_ui_origins(ui_origins, browser)))

    for c in checks:
        badge = f"{_GREEN}OK  {_RESET}" if c["ok"] else f"{_RED}FAIL{_RESET}"
        print(f"  {badge}  {c['name']:<18} {c['detail']:<34} {_DIM}{c['url']}{_RESET}")
    print("-" * 78)

    failures = [f"{c['name']} ({c['url']}) — {c['detail']}" for c in checks if not c["ok"]]
    abort = bool(checks) and len(failures) == len(checks)

    if abort:
        print(f"  {_RED}Every surface is down — aborting before any test runs.{_RESET}")
        for f in failures:
            print(f"    - {f}")
        print(f"  {_DIM}Skip this gate with --no-preflight if you want to run anyway.{_RESET}\n")
    elif failures:
        # Partial outage: the healthy surfaces still produce real results, and the tests
        # bound to the dead one fail fast on their own (a session-scoped login fails once,
        # the rest skip in ~0s). Blocking the whole run here would cost far more than it saves.
        print(f"  {_RED}Partially down — running anyway.{_RESET}")
        for f in failures:
            print(f"    - {f}")
        print(
            f"  {_DIM}Tests that need the surface above will report BLOCKED; "
            f"everything else runs normally.{_RESET}\n"
        )
    else:
        print(f"  {_GREEN}All reachable — starting the run.{_RESET}\n")
    return abort, failures


def log_preflight_failure(failures: list[str]) -> None:
    """Mirror the failure into the run log so post-mortems see it too."""
    for f in failures:
        logger.error("PREFLIGHT: {}", f)
