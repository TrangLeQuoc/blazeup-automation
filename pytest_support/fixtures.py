"""Shared pytest fixtures for UI and API automation."""

import asyncio
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

import httpx
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
from pytest_support.approval import ApproverLogin, BlockedApprover, assign_single_approver
from pytest_support.seeding import seed_partner
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
    base_url: str | None = None,
    viewport: dict | None = None,
) -> tuple[Browser, BrowserContext]:
    """Launch a browser and create a context.

    Args:
        playwright_obj: The async_playwright instance.
        settings:       Runtime settings (browser type, viewport, etc.).
        result_dir:     Artifact directory for video recording.
        base_url:       Context base URL (defaults to the SA app).
        viewport:       Override the configured viewport (e.g. the 375×812 mobile size).

    No storage-state / sessionStorage seeding: every UI fixture logs in inside its own
    context. The partner portal's ``pp_refresh_token`` is single-use, so a captured session
    replayed into another context was refused (2026-10-09) — the parameters that carried it
    were removed with the snapshot mechanism.

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


@pytest_asyncio.fixture
async def partner_authenticated_page(
    request: pytest.FixtureRequest,
    settings: Settings,
    result_dir: Path,
) -> AsyncGenerator[Page]:
    """Pre-authenticated PARTNER-portal page — a FRESH login per test.

    Why not one cached login reused by every test (which is what this used to do): the
    portal keeps ``pp_refresh_token`` in sessionStorage and that token is SINGLE-USE. The
    context that logged in consumes it, so replaying the same snapshot into a second
    context is refused and every protected page bounces to /login. Measured 2026-10-09:
    the original context reached /deals while a freshly seeded one redirected to /login,
    and a full run lost 19 TCs to it at session age 0m00s. The SA side
    (``authenticated_page``) already re-logs in per test for the same reason.

    Tests marked ``@pytest.mark.mobile`` get a mobile-sized context (375×812) so the
    viewport AND the recorded video match — no need to resize at runtime (which would
    leave the video canvas at the desktop size with a grey dead margin).
    """
    partner_url = settings.partner_base_url
    if partner_url is None:
        pytest.skip("BLOCKED: PARTNER_BASE_URL not configured — cannot run partner UI tests")
    partner_url = str(partner_url)
    email, password = require_credentials(settings.partner_email, settings.partner_password)
    trace_name = request.node.name.replace("/", "_").replace("\\", "_")
    viewport = {"width": 375, "height": 812} if request.node.get_closest_marker("mobile") else None
    async with async_playwright() as playwright:
        browser, context = await _create_browser_context(
            playwright,
            settings,
            result_dir,
            base_url=partner_url,
            viewport=viewport,
        )
        page_obj = await context.new_page()
        request.node._playwright_page = page_obj
        try:
            try:
                await login_ui(
                    page_obj,
                    partner_url,
                    email,
                    password,
                    login_page_cls=PartnerLoginPage,
                    totp_secret=settings.partner_totp_secret,
                )
            except Exception as exc:  # noqa: BLE001 — precondition, not the feature under test
                logger.error("Login UI (partner) FAILED — blocking this test: {}", exc)
                pytest.skip(f"BLOCKED: partner UI login failed — {blocked_reason(exc)}")
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


# Sign-in is a POST, so base_client deliberately does not retry it (a retried create could
# double-create). Signing in creates nothing, so the approver login retries on its own —
# on transport errors, gateway 502/503/504 and an over-SLA response, i.e. the outages a
# second try can fix. Never on a 4xx: retrying a 401 would just hammer a wrong password.
_APPROVER_LOGIN_ATTEMPTS = 3


def _is_transport_error(exc: BaseException) -> bool:
    seen: BaseException | None = exc
    while seen is not None:
        if isinstance(seen, httpx.TransportError):
            return True
        seen = seen.__cause__ or seen.__context__
    return False


_GATEWAY_ERROR_RE = re.compile(r"\bgot 50[234]\b")


def _is_retryable_login_error(exc: BaseException) -> bool:
    """A failure a second sign-in attempt can plausibly fix (see the note above)."""
    text = str(exc)
    return (
        _is_transport_error(exc)
        or bool(_GATEWAY_ERROR_RE.search(text))
        or "exceeded limit" in text  # base_client's over-SLA assertion
    )


async def login_qa_approver(
    settings: Settings, *, login=login_api, sleep=asyncio.sleep
) -> ApproverLogin:
    """Log the QA approver (ADMIN2) in — retrying transport errors — or say why it can't.

    A plain function (``login`` / ``sleep`` injectable) so the retry and the classification
    are unit-tested without a network; the ``approver_login`` fixture only calls it.
    """
    if not (settings.admin2_email and settings.admin2_password):
        reason = (
            "no QA approver configured (ADMIN2_EMAIL / ADMIN2_PASSWORD) — the creator may "
            "not approve its own record"
        )
        logger.error("SA approver unavailable: {}", reason)
        return ApproverLogin(blocked_reason=reason)
    last_exc: BaseException | None = None
    for attempt in range(1, _APPROVER_LOGIN_ATTEMPTS + 1):
        try:
            token = await login(
                str(settings.api_base_url),
                str(settings.base_url),
                settings.admin2_email,
                settings.admin2_password,
                max_response_time_ms=settings.default_response_time_ms * 5,
            )
        except Exception as exc:  # noqa: BLE001 — classified below, never fatal to the run
            last_exc = exc
            retryable = _is_retryable_login_error(exc)
            logger.warning(
                "SA approver (ADMIN2) login attempt {}/{} failed ({}): {}",
                attempt,
                _APPROVER_LOGIN_ATTEMPTS,
                "retrying" if retryable else "not retryable",
                f"{type(exc).__name__}: {exc}",
            )
            if not retryable or attempt == _APPROVER_LOGIN_ATTEMPTS:
                break
            await sleep(2 * attempt)
            continue
        logger.info("Login API (approver) complete - ADMIN2 token cached for approvals")
        return ApproverLogin(token=token)
    # Type name first: an httpx timeout stringifies to "" and the old log line ended in a
    # bare colon, which named nothing.
    reason = "SA approver (ADMIN2) login failed — " + blocked_reason(
        RuntimeError(f"{type(last_exc).__name__}: {last_exc}")
    )
    logger.error("{} — tests that approve or reject will be BLOCKED", reason)
    return ApproverLogin(blocked_reason=reason)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def approver_login(settings: Settings) -> AsyncGenerator[ApproverLogin]:
    """Session login of the SECOND SA actor — the one that APPROVES what the first created.

    The approval chain forbids the REQUESTER from approving its own record (the same rule a
    code review encodes: the author does not approve their own PR). Seeding therefore
    creates with ``ADMIN_*`` and approves with ``ADMIN2_*``.

    There is NO fallback to the creating account any more. It used to fall back, and that
    can never work while the chain is on: on 2026-10-13 one ADMIN2 sign-in timeout made
    the creator the "approver", and the approve was refused with a 400/403 that read like a
    BE defect. Instead this reports WHY the approver is unavailable, and every test that
    actually approves turns BLOCKED with that reason (see ``BlockedApprover``).
    """
    result = await login_qa_approver(settings)
    yield result
    if result.token:
        logger.log("FINISH", "Disconnect API - approver session token released")


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def approver_api_token(approver_login: ApproverLogin) -> AsyncGenerator[str]:
    """The QA approver's token — empty when it is unavailable (see ``approver_login``)."""
    yield approver_login.token


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def approver_user_id(
    settings: Settings, approver_login: ApproverLogin
) -> AsyncGenerator[str]:
    """The QA approver's own user id, read from its token — never hard-coded.

    Needed because assigning an approval chain names the approver by id. Resolved once per
    session from ``GET /sa-auth-api/current-user``; an empty string when it cannot be read,
    which ``assign_single_approver`` reports rather than crashing the run.

    When the approver is unavailable this does NOT call current-user at all: with the old
    creator fallback that call returned the CREATOR's id, which was then assigned as the
    approver and refused by the BE.
    """
    if approver_login.blocked_reason:
        logger.warning("QA approver user id not resolved — {}", approver_login.blocked_reason)
        yield ""
        return
    client = AuthClient(
        str(settings.api_base_url),
        token=approver_login.token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    user_id = ""
    try:
        response = await client.get("/sa-auth-api/current-user", expected_status=None)
        if response.status_code < 400:
            body = response.json()
            data = body.get("data", body)
            user_id = str(data.get("_id") or data.get("id") or "")
    except Exception as exc:  # noqa: BLE001 — resolved lazily; absence is handled downstream
        logger.warning("Could not resolve the QA approver's user id: {}", exc)
    finally:
        await client.close()
    if user_id:
        logger.info("QA approver user id resolved: {}", user_id)
    else:
        logger.warning("QA approver user id is unknown — approval chains cannot be assigned")
    yield user_id


@pytest.fixture
def assign_qa_approver(
    approver_user_id: str,
    sa_partners_client: SaPartnersClient,
    sa_deals_client: SaDealsClient,
):
    """Reusable STEP: pin one record's approval chain to the QA approver (count = 1).

    Any test that has to get a partner or a deal approved calls this first, so the record
    carries exactly one approver who is NOT its creator::

        await assign_qa_approver(partner_id, kind="partner")
        await sa_approver_client.approve_partner(partner_id)   # approved by the QA account

        await assign_qa_approver(deal_id, kind="deal")

    Why it exists and why the count is 1 (never 0) is documented in
    ``pytest_support.approval``. Returns True when the chain was assigned.
    """

    async def _assign(record_id: str, *, kind: str = "partner") -> bool:
        setter = {
            "partner": sa_partners_client.set_partner_approval_config,
            "deal": sa_deals_client.set_deal_approval_config,
        }.get(kind)
        if setter is None:
            raise ValueError(f"kind must be 'partner' or 'deal', got {kind!r}")
        return await assign_single_approver(setter, record_id, approver_user_id, label=kind)

    return _assign


@pytest_asyncio.fixture
async def sa_approver_client(
    settings: Settings, approver_login: ApproverLogin
) -> AsyncGenerator[SaPartnersClient | BlockedApprover]:
    """SA Partners client bound to the APPROVER actor (see ``approver_login``).

    A ``BlockedApprover`` when that account is unavailable: approving through it marks the
    test BLOCKED with the reason, instead of failing it on the creator's refusal.
    """
    if approver_login.blocked_reason:
        yield BlockedApprover(approver_login.blocked_reason)
        return
    client = SaPartnersClient(
        str(settings.api_base_url),
        token=approver_login.token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


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
    settings: Settings,
    api_token: str,
    sa_approver_client: SaPartnersClient,
    approver_user_id: str,
) -> AsyncGenerator[SaPartnersClient]:
    """Authenticated SA Partners API client (sa-partners-api), token from session.

    Carries the QA approver alongside it, so ``approve_partner`` assigns the partner's
    chain to that account and lets IT approve — the creator may not approve its own
    partner. Every call site (seeding, ``provision_partner_user``, the approval TCs) gets
    this for free.
    """

    client = SaPartnersClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    client.approver_client = sa_approver_client
    client.approver_user_id = approver_user_id
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sa_deals_approver_client(
    settings: Settings, approver_login: ApproverLogin
) -> AsyncGenerator[SaDealsClient | BlockedApprover]:
    """SA Deals client bound to the QA APPROVER actor — it approves what the creator cannot.

    A ``BlockedApprover`` when that account is unavailable (see ``sa_approver_client``).
    """
    if approver_login.blocked_reason:
        yield BlockedApprover(approver_login.blocked_reason)
        return
    client = SaDealsClient(
        str(settings.api_base_url),
        token=approver_login.token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sa_deals_client(
    settings: Settings,
    api_token: str,
    sa_deals_approver_client: SaDealsClient,
    approver_user_id: str,
) -> AsyncGenerator[SaDealsClient]:
    """Authenticated SA Deals API client (sa-partners-api /v1/sa/deals), token from session.

    Carries the QA approver alongside it, so ``approve_deal`` / ``reject_deal`` can assign
    the deal's chain to that account and let IT make the call — the creator may not approve
    its own deal. Call sites stay unchanged.
    """

    client = SaDealsClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    client.approver_client = sa_deals_approver_client
    client.approver_user_id = approver_user_id
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


@pytest.fixture
def seeded_partner(
    sa_partners_client: SaPartnersClient,
    sa_approver_client: SaPartnersClient,
    approver_user_id: str,
    created_resources: _CleanupRegistry,
):
    """Create a partner with its cleanup ALREADY registered — impossible to forget.

    Requests ``sa_partners_client`` before ``created_resources`` on purpose: that sets the
    setup order, so at teardown the registered DELETEs run BEFORE the client closes.

    Thin wrapper over ``pytest_support.seeding.seed_partner``, where the rules and the
    reasoning live (that module is Playwright-free so the selftests cover it in CI)::

        partner = await seeded_partner()                    # pending
        active = await seeded_partner(approve=True)          # pending -> active
        custom = await seeded_partner(payload=make_partner(type="referral"))

    Returns the create response unchanged: call sites keep using ``partner.partner_id``
    and ``partner.data``.
    """

    async def _seed(*, approve: bool = False, payload: dict[str, Any] | None = None):
        return await seed_partner(
            sa_partners_client,
            created_resources.add,
            approve=approve,
            payload=payload,
            approver_client=sa_approver_client,
            approver_user_id=approver_user_id,
        )

    return _seed
