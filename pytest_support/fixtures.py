"""Shared pytest fixtures for UI and API automation."""

import contextlib
import logging
import os
import re
import sys
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from faker import Faker
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from api_clients.base_client import SETUP_RESPONSE_TIME_MS
from api_clients.blazeup.admin.auth_client import AuthClient
from api_clients.blazeup.admin.partner.sa_commissions_client import SaCommissionsClient
from api_clients.blazeup.admin.partner.sa_deals_client import SaDealsClient
from api_clients.blazeup.admin.partner.sa_partners_client import SaPartnersClient
from config.settings import Settings, get_settings
from pages.blazeup.partner.login_page import PartnerLoginPage
from utils.helpers import blocked_reason, require_credentials
from utils.login_helpers import login_api, login_ui
from utils.screenshot_on_fail import attach_screenshot
from utils.ui_cleanup import SaCleanup

PROJECT_ROOT = Path(__file__).resolve().parents[1]


logging.getLogger("faker").setLevel(logging.WARNING)
logging.getLogger("faker.factory").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Return typed runtime settings."""

    return get_settings()


@pytest.fixture(scope="session")
def result_dir() -> Path:
    """Return the current run artifact directory and configure loguru sinks.

    The path is resolved here (at first fixture call = test-execution time),
    NOT at module-import time.  This ensures the fallback timestamp is
    accurate even when test collection takes several seconds.

    Priority:
      1. $BLAZEUP_RESULT_DIR env var  — set by runner/test_runner.py
      2. Fallback: results/run_<timestamp>  — used when pytest is run directly
    """
    run_dir = Path(
        os.getenv(
            "BLAZEUP_RESULT_DIR",
            f"results/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
    )

    for subfolder in ["logs", "videos", "screenshots", "traces", "allure-results"]:
        (run_dir / subfolder).mkdir(parents=True, exist_ok=True)

    # Ensure custom log levels (STEP, START, PASSED, FAILED) are registered.
    import utils.log_helper  # noqa: F401 — side-effect import registers levels

    log_level = os.getenv("BLAZEUP_LOG_LEVEL", "INFO")
    logger.remove()

    # ── Terminal: compact & beautiful ────────────────────────────────────────
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        ),
        level=log_level,
        enqueue=True,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # ── File: detailed & grep-friendly ───────────────────────────────────────
    def _add_tc_id_default(record: dict) -> bool:
        record["extra"].setdefault("tc_id", "--")
        return True

    logger.add(
        run_dir / "logs" / "test.log",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{extra[tc_id]: <10} | "
            "{file.name}:{function}:{line} | "
            "{message}"
        ),
        level=log_level,
        filter=_add_tc_id_default,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
    return run_dir


# ---------------------------------------------------------------------------
# TC-logger helpers
# ---------------------------------------------------------------------------


def _split_node_name(node_name: str) -> tuple[str, str]:
    """Split a pytest node name into (base_func_name, param_suffix).

    Parametrized tests carry a ``[param]`` suffix, e.g.::

        test_shell_ui_load_time_page_001[dashboard]
        ->  ("test_shell_ui_load_time_page_001", "[dashboard]")

    The base name is what TC_REGISTRY stores in ``test_func``; the suffix is
    kept for the log banner so each parametrized run is distinguishable.
    """
    base, sep, params = node_name.partition("[")
    return base, (f"[{params}" if sep else "")


def _parse_tc_id(node_name: str) -> str:
    """Return the registry TC ID string for a pytest node name.

    Looks up TC_REGISTRY by test_func — single source of truth, handles
    any numbering scheme (sequential demo IDs, structured Partner IDs, …).
    The pytest ``[param]`` suffix is stripped before matching so every
    parametrized run resolves to its function's TC ID.
    Falls back to regex extraction for tests not yet registered.
    """
    base_name, _ = _split_node_name(node_name)
    try:
        from runner.tc_registry import TC_REGISTRY

        for tc_id, tc in TC_REGISTRY.items():
            if tc.test_func == base_name:
                return str(tc_id)
    except ImportError:
        pass

    # Fallback: parse from function name (unregistered tests)
    m = re.search(r"test_tc(a?)(\d+)", base_name)
    if not m:
        return "???"
    if m.group(1):
        return f"A{int(m.group(2)):02d}"
    return str(1000 + int(m.group(2)))


def _parse_tc_title(item: pytest.Item) -> str:
    """Return the first docstring line of the test function (strips TC prefix)."""
    fn = getattr(item, "function", None) or getattr(item, "obj", None)
    doc = (getattr(fn, "__doc__", None) or "").strip()
    if not doc:
        return item.name
    first_line = doc.split("\n")[0]
    return first_line.split(": ", 1)[-1] if ": " in first_line else first_line


@pytest_asyncio.fixture(autouse=True)
async def tc_logger(
    request: pytest.FixtureRequest,
    result_dir: Path,
) -> AsyncGenerator[None]:
    """Autouse fixture: emits TC START/PASSED/FAILED banners and binds the
    TC ID to every log record produced during the test via loguru contextualize.
    """
    tc_id = _parse_tc_id(request.node.name)
    _, param = _split_node_name(request.node.name)  # e.g. "[dashboard]" for parametrized runs
    title = _parse_tc_title(request.node)
    start = time.perf_counter()

    # Label shown in every banner: TC-<id> plus the parametrize case (if any),
    # so 15 parametrized runs of one TC are distinguishable instead of looking
    # like 15 identical START lines.
    label = f"TC-{tc_id}{param}"

    with logger.contextualize(tc_id=label):
        print("", file=sys.stderr, flush=True)
        logger.log("START", "[{}] {}", label, title)
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            rep_call = getattr(request.node, "rep_call", None)
            rep_setup = getattr(request.node, "rep_setup", None)

            failed = (rep_call is not None and rep_call.failed) or (
                rep_setup is not None and rep_setup.failed
            )
            # A skip raised by a FIXTURE (the BLOCKED path: shared login down, missing
            # credentials) lands on rep_setup and leaves rep_call as None — checking only
            # rep_call made every BLOCKED test fall through to the else branch and log
            # "PASSED". The summary table read the pytest report directly and correctly
            # said BLOCK, so the log and the table disagreed on the same test case.
            skipped = (rep_call is not None and rep_call.skipped) or (
                rep_setup is not None and rep_setup.skipped
            )

            # Optional verdict detail set by the test body via
            # utils.log_helper.finalize_checks (e.g. "2/15 pages failed: ...").
            detail = getattr(request.node, "_tc_detail", "")
            suffix = f" - {detail}" if detail else ""

            # ── Test-case verdict (right before FINISH) ──────────────────────
            if failed:
                logger.log("FAILED", "[{}] FAILED ({:.2f}s){}", label, elapsed, suffix)
            elif skipped:
                logger.warning("[{}] SKIPPED ({:.2f}s)", label, elapsed)
            else:
                logger.log("PASSED", "[{}] PASSED ({:.2f}s){}", label, elapsed, suffix)

            # ── End-of-test marker (include the title so the line isn't bare) ─
            logger.log("FINISH", "[{}] {} — done", label, title)


@pytest.fixture(scope="session")
def fake() -> Faker:
    """Return a Faker generator for dynamic test data."""

    return Faker()


# ---------------------------------------------------------------------------
# Browser context helper
# ---------------------------------------------------------------------------


async def _create_browser_context(
    playwright_obj: Any,
    settings: Settings,
    result_dir: Path,
    storage_state: dict | None = None,
    base_url: str | None = None,
    viewport: dict | None = None,
) -> tuple[Browser, BrowserContext]:
    """Launch a browser and create a context.

    Args:
        playwright_obj: The async_playwright instance.
        settings:       Runtime settings (browser type, viewport, etc.).
        result_dir:     Artifact directory for video recording.
        storage_state:  Playwright storage state dict (cookies + localStorage) to
                        pre-authenticate the context, or ``None`` to log in fresh.

    Returns:
        ``(Browser, BrowserContext)`` — both must be closed by the caller.
    """
    browser_launcher = getattr(playwright_obj, settings.browser)
    launch_options: dict[str, Any] = {
        "headless": settings.headless,
        "slow_mo": settings.slow_mo,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
    if settings.browser == "chromium":
        launch_options["channel"] = "chromium"

    browser: Browser = await browser_launcher.launch(**launch_options)

    vp = viewport or {"width": settings.viewport_width, "height": settings.viewport_height}
    context_options: dict[str, Any] = {
        "viewport": vp,
        "base_url": base_url or str(settings.base_url),
        "record_video_dir": str(result_dir / "videos"),
        "record_video_size": vp,  # match the viewport so the video has no dead margin
    }
    if storage_state is not None:
        context_options["storage_state"] = storage_state

    context = await browser.new_context(**context_options)
    await context.tracing.start(screenshots=True, snapshots=True, sources=True)
    return browser, context


async def _save_page_artifacts(
    page_obj: Page,
    request: pytest.FixtureRequest,
    result_dir: Path,
) -> None:
    """Take a screenshot (pass or fail) and attach it to the run artifacts."""
    report = getattr(request.node, "rep_call", None)
    status = "failed" if report and report.failed else "passed"
    timestamp = datetime.now().strftime("%H%M%S")
    safe_name = request.node.name.replace("/", "_").replace("\\", "_")
    screenshot_name = f"{safe_name}_{status}_{timestamp}"
    if status == "failed":
        await attach_screenshot(
            page_obj, screenshot_name, output_dir=str(result_dir / "screenshots")
        )
    else:
        screenshot_path = result_dir / "screenshots" / f"{screenshot_name}.png"
        await page_obj.screenshot(path=str(screenshot_path), full_page=True)
        logger.info("Saved final screenshot to {}", screenshot_path)


async def _rename_video(video, request: pytest.FixtureRequest, result_dir: Path) -> None:
    """Rename the auto-generated ``page@<hash>.webm`` to ``TC-<id>_<status>.webm``.

    Playwright names each context's video by a random hash, so it's impossible to
    tell which run a video belongs to. This renames it to the test-case id + verdict
    once the video is finalized (called AFTER the context is closed). A timestamp is
    appended only if a same-named file already exists (e.g. parametrized runs), so we
    never clobber a sibling video.
    """
    if video is None:
        return
    with contextlib.suppress(Exception):
        src = Path(await video.path())
        if not src.exists():
            return
        tc_id = _parse_tc_id(request.node.name)
        report = getattr(request.node, "rep_call", None)
        status = "failed" if report and report.failed else "passed"
        dst = src.with_name(f"TC-{tc_id}_{status}{src.suffix}")
        if dst.exists():
            dst = src.with_name(f"TC-{tc_id}_{status}_{datetime.now():%H%M%S}{src.suffix}")
        src.rename(dst)
        logger.info("Saved run video to {}", dst.name)


# ---------------------------------------------------------------------------
# Unauthenticated browser fixtures  (login-page tests, non-auth scenarios)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def browser_context(
    request: pytest.FixtureRequest,
    settings: Settings,
    result_dir: Path,
) -> AsyncGenerator[BrowserContext]:
    """Unauthenticated browser context.

    Use this (via the ``page`` fixture) when the test itself exercises the
    login flow or does not require an authenticated session.
    """
    trace_name = request.node.name.replace("/", "_").replace("\\", "_")
    async with async_playwright() as playwright:
        browser, context = await _create_browser_context(playwright, settings, result_dir)
        try:
            yield context
        finally:
            await context.tracing.stop(path=str(result_dir / "traces" / f"{trace_name}.zip"))
            # capture the page's video (set by the `page` fixture) before closing the context
            _pg = getattr(request.node, "_playwright_page", None)
            _video = _pg.video if _pg else None
            await context.close()
            await _rename_video(_video, request, result_dir)
            await browser.close()


@pytest_asyncio.fixture
async def page(
    request: pytest.FixtureRequest,
    browser_context: BrowserContext,
    result_dir: Path,
) -> AsyncGenerator[Page]:
    """Unauthenticated page — one fresh page per test."""

    page_obj = await browser_context.new_page()
    request.node._playwright_page = page_obj
    yield page_obj
    if "ui" in request.node.keywords:
        await _save_page_artifacts(page_obj, request, result_dir)
    await page_obj.close()


# ---------------------------------------------------------------------------
# Auth — SA UI (fresh login per test; see authenticated_page for why)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def authenticated_page(
    request: pytest.FixtureRequest,
    settings: Settings,
    result_dir: Path,
) -> AsyncGenerator[Page]:
    """Pre-authenticated stgsa page — a FRESH UI login per test.

    Why re-login (not one shared ``auth_state`` snapshot injected into every
    context): the stgsa SA auth uses a rotating, single-use refresh cookie. The
    first page load refreshes the token and the server invalidates the old refresh
    cookie, so a 2nd+ context that replays the SAME captured storage_state 401s on
    ``current-user`` / ``refresh-cookie-token`` and the SA micro-frontend never
    renders (the "1st SA test passes, the rest time out at 90s" flaky).

    Tests run sequentially, so a fresh login per test keeps exactly ONE active
    session at a time — no cross-context cookie rotation. Everything (context,
    login, the test) runs on the SAME function-scoped event loop, so there is no
    cross-loop hazard (a shared live BrowserContext would deadlock across loops).
    """
    trace_name = request.node.name.replace("/", "_").replace("\\", "_")
    async with async_playwright() as playwright:
        browser, context = await _create_browser_context(playwright, settings, result_dir)
        page_obj = await context.new_page()
        request.node._playwright_page = page_obj
        try:
            email, password = require_credentials(settings.test_email, settings.test_password)
            await login_ui(page_obj, str(settings.base_url), email, password)
        except Exception as exc:  # noqa: BLE001 — precondition failure → BLOCKED, not a defect
            logger.error("SA UI login FAILED — blocking this test: {}", exc)
            await context.tracing.stop(path=str(result_dir / "traces" / f"{trace_name}.zip"))
            await context.close()
            await browser.close()
            pytest.skip(f"BLOCKED: SA UI login failed — {blocked_reason(exc)}")
        try:
            yield page_obj
        finally:
            await _save_page_artifacts(page_obj, request, result_dir)
            await context.tracing.stop(path=str(result_dir / "traces" / f"{trace_name}.zip"))
            video = page_obj.video
            await page_obj.close()
            await context.close()
            await _rename_video(video, request, result_dir)
            await browser.close()


@pytest.fixture
def make_page(authenticated_page: Page, settings: Settings):
    """Factory for building authenticated page objects without boilerplate.

    Replaces the repeated ``XPage(authenticated_page, str(settings.base_url))``::

        async def test_x(make_page):
            shell = make_page(ShellPage)
            dash  = make_page(DashboardPage)

    For UNAUTHENTICATED flows (e.g. the login page), construct directly with the
    ``page`` fixture instead: ``LoginPage(page, str(settings.base_url))``.
    """

    def _make(page_cls):
        return page_cls(authenticated_page, str(settings.base_url))

    return _make


# ---------------------------------------------------------------------------
# Partner-portal UI auth — separate origin (stgpartners) + single-step login
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def partner_auth_state(settings: Settings) -> AsyncGenerator[dict]:
    """Log in to the PARTNER portal once and cache its storage state.

    Session-scoped snapshot for the partner portal (stgpartners.blazeup.ai): partner
    credentials + the single-step ``PartnerLoginPage`` + the partner base URL, run
    once per session. (The SA side re-logs in per test instead — see
    ``authenticated_page`` — because stgsa's rotating refresh cookie breaks a shared
    snapshot; the partner portal does not, so a single shared snapshot is fine here.)
    """
    partner_url = settings.partner_base_url
    if partner_url is None:
        pytest.skip("BLOCKED: PARTNER_BASE_URL not configured — cannot run partner UI tests")
    partner_url = str(partner_url)
    logger.log("START", "Login UI (partner) - establishing the shared partner-portal session")
    async with async_playwright() as p:
        browser_launcher = getattr(p, settings.browser)
        browser = await browser_launcher.launch(headless=settings.headless)
        context = await browser.new_context(
            viewport={"width": settings.viewport_width, "height": settings.viewport_height},
            base_url=partner_url,
        )
        page_obj = await context.new_page()
        email, password = require_credentials(settings.partner_email, settings.partner_password)
        try:
            await login_ui(
                page_obj,
                partner_url,
                email,
                password,
                login_page_cls=PartnerLoginPage,
                totp_secret=settings.partner_totp_secret,
            )
            state = await context.storage_state()
        except Exception as exc:  # noqa: BLE001 — precondition failure → BLOCKED, not a defect
            logger.error("Login UI (partner) FAILED — blocking the run: {}", exc)
            pytest.skip(f"BLOCKED: shared partner UI login failed — {blocked_reason(exc)}")
        finally:
            await context.close()
            await browser.close()

    logger.info("Login UI (partner) complete - storage state cached")
    yield state
    logger.log("FINISH", "Logout UI (partner) - shared partner session closed")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def partner_session_started_at(partner_auth_state: dict) -> float:
    """When the shared partner snapshot was captured (``time.monotonic``).

    A separate fixture rather than a field on the state dict: that dict is handed
    straight to Playwright as ``storage_state``, so it must stay exactly what Playwright
    produced. Depending on ``partner_auth_state`` means this is stamped right after the
    login, once per session.

    Its only job is the diagnostic in ``partner_authenticated_page``: when the session
    turns out to be dead, the log says how long it had been alive, which is the number
    you need to decide "token TTL" vs "invalidated server-side".
    """
    return time.monotonic()


@pytest_asyncio.fixture
async def partner_authenticated_page(
    request: pytest.FixtureRequest,
    settings: Settings,
    partner_auth_state: dict,
    partner_session_started_at: float,
    result_dir: Path,
) -> AsyncGenerator[Page]:
    """Pre-authenticated PARTNER-portal page — fresh context per test, login once.

    Tests marked ``@pytest.mark.mobile`` get a mobile-sized context (375×812) so the
    viewport AND the recorded video match — no need to resize at runtime (which would
    leave the video canvas at the desktop size with a grey dead margin).

    Logs the age of the shared session on every test. Measured on run_20260810_170831
    the snapshot was reused across 358 s, comfortably inside a normal token lifetime —
    but that window grows with every partner TC added, and when it finally crosses the
    TTL the age printed here is what turns "the page did not render" into "the session
    aged out at N minutes" (``PartnerShellPage.wait_ready`` raises the matching error).
    """
    age_s = time.monotonic() - partner_session_started_at
    logger.info("shared partner session age: {:.0f}m{:02.0f}s", age_s // 60, age_s % 60)
    trace_name = request.node.name.replace("/", "_").replace("\\", "_")
    viewport = {"width": 375, "height": 812} if request.node.get_closest_marker("mobile") else None
    async with async_playwright() as playwright:
        browser, context = await _create_browser_context(
            playwright,
            settings,
            result_dir,
            storage_state=partner_auth_state,
            base_url=str(settings.partner_base_url),
            viewport=viewport,
        )
        page_obj = await context.new_page()
        request.node._playwright_page = page_obj
        try:
            yield page_obj
        finally:
            await _save_page_artifacts(page_obj, request, result_dir)
            await context.tracing.stop(path=str(result_dir / "traces" / f"{trace_name}.zip"))
            video = page_obj.video
            await page_obj.close()
            await context.close()
            await _rename_video(video, request, result_dir)
            await browser.close()


@pytest.fixture
def make_partner_page(partner_authenticated_page: Page, settings: Settings):
    """Factory for partner-portal page objects (bound to the partner base URL)."""

    def _make(page_cls):
        return page_cls(partner_authenticated_page, str(settings.partner_base_url))

    return _make


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def api_token(settings: Settings) -> AsyncGenerator[str]:
    """JWT token valid for the entire test session.

    Session-scoped: one API login per run.  Tokens typically live for hours,
    so there is no need to re-authenticate before every test.

    Logs an INFO line on login and a ``FINISH Disconnect API`` banner at
    session teardown so API runs are bracketed the same way UI runs are.

    Delegates to :func:`utils.login_helpers.login_api`.
    """
    logger.info("Login API - requesting the shared session token for all API tests")
    email, password = require_credentials(settings.test_email, settings.test_password)
    try:
        token = await login_api(
            str(settings.api_base_url),
            str(settings.base_url),
            email,
            password,
            max_response_time_ms=settings.default_response_time_ms * 5,
        )
    except Exception as exc:  # noqa: BLE001 — precondition failure → BLOCKED, not a test defect
        logger.error("Login API FAILED — blocking the run: {}", exc)
        pytest.skip(f"BLOCKED: shared SA API login failed — {blocked_reason(exc)}")
    logger.info("Login API complete - token cached (no re-login for the rest of the run)")
    yield token
    logger.log("FINISH", "Disconnect API - shared API session token released")


@pytest_asyncio.fixture
async def auth_client(settings: Settings, api_token: str) -> AsyncGenerator[AuthClient]:
    """Authenticated AuthClient — fresh instance per test, token from session."""

    client = AuthClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sa_partners_client(
    settings: Settings, api_token: str
) -> AsyncGenerator[SaPartnersClient]:
    """Authenticated SA Partners API client (sa-partners-api), token from session."""

    client = SaPartnersClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sa_deals_client(settings: Settings, api_token: str) -> AsyncGenerator[SaDealsClient]:
    """Authenticated SA Deals API client (sa-partners-api /v1/sa/deals), token from session."""

    client = SaDealsClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sa_commissions_client(
    settings: Settings, api_token: str
) -> AsyncGenerator[SaCommissionsClient]:
    """Authenticated SA Commissions API client (sa-partners-api /v1/sa/commissions)."""

    client = SaCommissionsClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sa_cleanup(settings: Settings) -> AsyncGenerator[SaCleanup]:
    """Deletes records a UI test created through the browser. Logs in LAZILY.

    Why not reuse ``sa_partners_client`` / ``api_token``:

    * ``api_token`` calls ``pytest.skip`` when the SA API login fails. That is right for
      an API test (no token = nothing to test) but wrong for a UI test, which needs only
      the UI login — staging answers ``/sign-in/credentials`` with 500
      ``MongoWriteConcernError`` often enough that coupling the two would make the whole
      UI suite hostage to an unrelated API outage. Here a failed login only disables
      cleanup (reported as a leak); the UI test still runs.
    * The login is deferred to the first cleanup call, i.e. teardown. stgsa's SA auth
      uses a rotating, single-use refresh cookie (see ``authenticated_page``), so an API
      session held open ALONGSIDE the browser session for the length of the test can
      rotate the session out from under the UI. Logging in only after the UI work is
      done keeps the two sessions from overlapping.

    Request ``created_resources`` AFTER this fixture so the cleanups run before the
    client is closed::

        async def test_x(sa_cleanup, make_page, created_resources):
            ...
            created_resources.add(lambda: sa_cleanup.delete_partner_by_name(company))
    """

    async def _login() -> SaPartnersClient | None:
        if not (settings.admin_email and settings.admin_password):
            logger.warning(
                "UI cleanup DISABLED: ADMIN_EMAIL/ADMIN_PASSWORD are not configured — "
                "records created through the UI will be left on staging."
            )
            return None
        try:
            token = await login_api(
                str(settings.api_base_url),
                str(settings.base_url),
                settings.admin_email,
                settings.admin_password,
                max_response_time_ms=settings.default_response_time_ms * 5,
            )
        except Exception as exc:  # noqa: BLE001 — cleanup is best-effort, never a blocker
            # Include the exception TYPE: httpx timeout errors stringify to "", so
            # blocked_reason() alone would render an empty, undebuggable reason.
            logger.warning(
                "UI cleanup DISABLED: SA API login failed ({}: {}). The test result is "
                "unaffected, but anything it created is left on staging. Sweep with: "
                "python -m utils.cleanup_staging",
                type(exc).__name__,
                blocked_reason(exc),
            )
            return None
        return SaPartnersClient(
            str(settings.api_base_url),
            token=token,
            # Cleanup is a setup-grade call, not the assertion under test: staging
            # mutations routinely take 10-25s, so a tight SLA would only add noise.
            max_response_time_ms=SETUP_RESPONSE_TIME_MS,
            app_origin=str(settings.base_url),
        )

    cleanup = SaCleanup(_login)
    try:
        yield cleanup
    finally:
        await cleanup.aclose()


@pytest.fixture
def test_user(fake: Faker) -> dict[str, str]:
    """Return a dict of generated user data for use as test input."""

    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "department": fake.job(),
    }


# ---------------------------------------------------------------------------
# Cleanup — track resources a test creates and remove them on teardown
# ---------------------------------------------------------------------------


class _CleanupRegistry:
    """Collects async teardown callbacks registered during a test."""

    def __init__(self) -> None:
        self.cleanups: list[Callable[[], Awaitable[Any]]] = []

    def add(self, cleanup: Callable[[], Awaitable[Any]]) -> None:
        """Register an async cleanup callback, e.g. ``lambda: client.delete(...)``."""
        self.cleanups.append(cleanup)

    def __len__(self) -> int:
        return len(self.cleanups)


@pytest_asyncio.fixture
async def created_resources() -> AsyncGenerator[_CleanupRegistry]:
    """Track resources a test creates and delete them on teardown (LIFO order).

    Register a cleanup for ANYTHING you create so it is removed even when the
    test fails::

        async def test_create_tenant(auth_client, created_resources):
            from utils.data_factory import make_tenant
            resp = await auth_client.post("/tenants", json=make_tenant())
            tenant_id = resp.json()["data"]["id"]
            created_resources.add(lambda: auth_client.delete(f"/tenants/{tenant_id}"))
            # ... assertions ...
        # teardown auto-deletes the tenant, pass OR fail.

    Cleanups run in reverse creation order; a failing cleanup is logged but never
    blocks the others or fails the test.
    """
    registry = _CleanupRegistry()
    yield registry
    for cleanup in reversed(registry.cleanups):
        try:
            await cleanup()
        except Exception as exc:  # noqa: BLE001 — cleanup must never break teardown
            logger.warning("Resource cleanup failed (non-blocking): {}", exc)
