"""Shared pytest fixtures for UI and API automation."""

import logging
import os
import re
import sys
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from faker import Faker
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from api_clients.blazeup_admin.attendance_client import AttendanceClient
from api_clients.blazeup_admin.auth_client import AuthClient
from config.settings import Settings, get_settings
from utils.helpers import load_yaml, require_credentials
from utils.login_helpers import login_api, login_ui
from utils.screenshot_on_fail import attach_screenshot

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
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
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

def _parse_tc_id(node_name: str) -> str:
    """Return the registry TC ID string for a pytest node name.

    Looks up TC_REGISTRY by test_func — single source of truth, handles
    any numbering scheme (sequential demo IDs, structured Partner IDs, …).
    Falls back to regex extraction for tests not yet registered.
    """
    try:
        from runner.tc_registry import TC_REGISTRY
        for tc_id, tc in TC_REGISTRY.items():
            if tc.test_func == node_name:
                return str(tc_id)
    except ImportError:
        pass

    # Fallback: parse from function name (unregistered tests)
    m = re.search(r"test_tc(a?)(\d+)", node_name)
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
) -> AsyncGenerator[None, None]:
    """Autouse fixture: emits TC START/PASSED/FAILED banners and binds the
    TC ID to every log record produced during the test via loguru contextualize.
    """
    tc_id = _parse_tc_id(request.node.name)
    title = _parse_tc_title(request.node)
    start = time.perf_counter()

    with logger.contextualize(tc_id=f"TC-{tc_id}"):
        print("", file=sys.stderr, flush=True)
        logger.log("START", "[TC-{}] {}", tc_id, title)
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            rep_call = getattr(request.node, "rep_call", None)
            rep_setup = getattr(request.node, "rep_setup", None)

            failed = (rep_call is not None and rep_call.failed) or (
                rep_setup is not None and rep_setup.failed
            )
            skipped = rep_call is not None and rep_call.skipped

            if failed:
                logger.log("FAILED", "[TC-{}] FAILED ({:.2f}s)", tc_id, elapsed)
            elif skipped:
                logger.warning("[TC-{}] SKIPPED ({:.2f}s)", tc_id, elapsed)
            else:
                logger.log("PASSED", "[TC-{}] PASSED ({:.2f}s)", tc_id, elapsed)


@pytest.fixture(scope="session")
def test_data() -> dict[str, Any]:
    """Load YAML fixture test data."""

    return load_yaml(PROJECT_ROOT / "fixtures" / "test_data.yaml")


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
) -> tuple[Browser, BrowserContext]:
    """Launch a browser and create a context.

    Args:
        playwright_obj: The async_playwright instance.
        settings:       Runtime settings (browser type, viewport, etc.).
        result_dir:     Artifact directory for video recording.
        storage_state:  Playwright storage state dict (cookies + localStorage).
                        Pass the value from the ``auth_state`` fixture to create
                        a pre-authenticated context without re-logging in.

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

    context_options: dict[str, Any] = {
        "viewport": {"width": settings.viewport_width, "height": settings.viewport_height},
        "base_url": str(settings.base_url),
        "record_video_dir": str(result_dir / "videos"),
        "record_video_size": {"width": settings.viewport_width, "height": settings.viewport_height},
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
        await attach_screenshot(page_obj, screenshot_name, output_dir=str(result_dir / "screenshots"))
    else:
        screenshot_path = result_dir / "screenshots" / f"{screenshot_name}.png"
        await page_obj.screenshot(path=str(screenshot_path), full_page=True)
        logger.info("Saved final screenshot to {}", screenshot_path)


# ---------------------------------------------------------------------------
# Unauthenticated browser fixtures  (login-page tests, non-auth scenarios)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def browser_context(
    request: pytest.FixtureRequest,
    settings: Settings,
    result_dir: Path,
) -> AsyncGenerator[BrowserContext, None]:
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
            await context.close()
            await browser.close()


@pytest_asyncio.fixture
async def page(
    request: pytest.FixtureRequest,
    browser_context: BrowserContext,
    result_dir: Path,
) -> AsyncGenerator[Page, None]:
    """Unauthenticated page — one fresh page per test."""

    page_obj = await browser_context.new_page()
    setattr(request.node, "_playwright_page", page_obj)
    yield page_obj
    if "ui" in request.node.keywords:
        await _save_page_artifacts(page_obj, request, result_dir)
    await page_obj.close()


# ---------------------------------------------------------------------------
# Auth — session-scoped  (login once for the entire test run)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def auth_state(settings: Settings) -> dict:
    """Log in once and cache the Playwright storage state (cookies + localStorage).

    Session-scoped: runs exactly once per test run regardless of how many tests
    request ``authenticated_page``.  The returned dict is injected into every
    new browser context via ``storage_state=``, so each test starts already
    authenticated without repeating the login flow.
    """
    async with async_playwright() as p:
        browser_launcher = getattr(p, settings.browser)
        browser = await browser_launcher.launch(headless=settings.headless)
        context = await browser.new_context(
            viewport={"width": settings.viewport_width, "height": settings.viewport_height},
            base_url=str(settings.base_url),
        )
        page_obj = await context.new_page()
        email, password = require_credentials(settings.test_email, settings.test_password)
        await login_ui(page_obj, str(settings.base_url), email, password)
        state = await context.storage_state()
        await context.close()
        await browser.close()

    logger.info("auth_state: session login complete — storage state cached for all UI tests")
    return state


@pytest_asyncio.fixture
async def authenticated_page(
    request: pytest.FixtureRequest,
    settings: Settings,
    auth_state: dict,
    result_dir: Path,
) -> AsyncGenerator[Page, None]:
    """Pre-authenticated page — fresh isolated context per test, login only once.

    Each test gets its own browser context (full isolation — no shared cookies
    between tests) but the context is pre-loaded with ``auth_state`` so the
    login page is never visited again after the first test in the session.

    Timeline:
        Session start  →  auth_state fixture logs in once, saves storage state
        Test 1  →  new context + storage_state injected  →  page is authenticated
        Test 2  →  new context + storage_state injected  →  page is authenticated
        ...
        Test N  →  new context + storage_state injected  →  page is authenticated
    """
    trace_name = request.node.name.replace("/", "_").replace("\\", "_")
    async with async_playwright() as playwright:
        browser, context = await _create_browser_context(
            playwright, settings, result_dir, storage_state=auth_state
        )
        page_obj = await context.new_page()
        setattr(request.node, "_playwright_page", page_obj)
        try:
            yield page_obj
        finally:
            await _save_page_artifacts(page_obj, request, result_dir)
            await context.tracing.stop(path=str(result_dir / "traces" / f"{trace_name}.zip"))
            await page_obj.close()
            await context.close()
            await browser.close()


@pytest_asyncio.fixture(scope="session")
async def api_token(settings: Settings) -> str:
    """JWT token valid for the entire test session.

    Session-scoped: one API login per run.  Tokens typically live for hours,
    so there is no need to re-authenticate before every test.

    Delegates to :func:`utils.login_helpers.login_api`.
    """
    email, password = require_credentials(settings.test_email, settings.test_password)
    return await login_api(
        str(settings.api_base_url),
        str(settings.base_url),
        email,
        password,
        max_response_time_ms=settings.default_response_time_ms * 5,
    )


@pytest_asyncio.fixture
async def auth_client(settings: Settings, api_token: str) -> AsyncGenerator[AuthClient, None]:
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
async def attendance_client(settings: Settings, api_token: str) -> AsyncGenerator[AttendanceClient, None]:
    """Authenticated AttendanceClient — fresh instance per test, token from session."""

    client = AttendanceClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    yield client
    await client.close()


@pytest.fixture
def test_user(fake: Faker) -> dict[str, str]:
    """Return a dict of generated user data for use as test input."""

    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "department": fake.job(),
    }
