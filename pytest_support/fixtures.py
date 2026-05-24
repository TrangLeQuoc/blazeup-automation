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

from api.attendance_client import AttendanceClient
from api.auth_client import AuthClient
from config.settings import Settings, get_settings
from pages.home_page import HomePage
from pages.login_page import LoginPage
from utils.helpers import load_yaml, require_credentials
from utils.screenshot_on_fail import attach_screenshot

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = Path(os.getenv("BLAZEUP_RESULT_DIR", f"results/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"))

logging.getLogger("faker").setLevel(logging.WARNING)
logging.getLogger("faker.factory").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Return typed runtime settings."""

    return get_settings()


@pytest.fixture(scope="session")
def result_dir() -> Path:
    """Return the current run artifact directory and configure loguru sinks."""

    for subfolder in ["logs", "videos", "screenshots", "traces", "allure-results"]:
        (RESULT_DIR / subfolder).mkdir(parents=True, exist_ok=True)

    # Ensure custom log levels (STEP, START, PASSED, FAILED) are registered.
    import utils.log_helper  # noqa: F401 — side-effect import registers levels

    log_level = os.getenv("BLAZEUP_LOG_LEVEL", "INFO")
    logger.remove()

    # ── Terminal: compact & beautiful ────────────────────────────────────────
    # Shows only the time, coloured level badge, and message.
    # Level colours come from the loguru level definition (custom + built-in).
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
    # Includes timestamp (ms), TC ID (set via logger.contextualize), source
    # location, and full message.  Use: grep "TC-A01" results/.../test.log
    def _add_tc_id_default(record: dict) -> bool:
        record["extra"].setdefault("tc_id", "--")
        return True

    logger.add(
        RESULT_DIR / "logs" / "test.log",
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
    return RESULT_DIR


# ---------------------------------------------------------------------------
# TC-logger helpers
# ---------------------------------------------------------------------------

def _parse_tc_id(node_name: str) -> str:
    """Extract a short TC ID string from a pytest node name.

    Examples::

        test_tca01_login_returns_jwt  ->  'A01'
        test_tc01_login_success       ->  '1001'
        test_something_else           ->  '???'
    """
    m = re.search(r"test_tc(a?)(\d+)", node_name)
    if not m:
        return "???"
    if m.group(1):          # 'a' present -> API test  (tca01 -> A01)
        return f"A{int(m.group(2)):02d}"
    return str(1000 + int(m.group(2)))  # UI test  (tc01 -> 1001)


def _parse_tc_title(item: pytest.Item) -> str:
    """Return the first docstring line of the test function (strips TC prefix)."""
    fn = getattr(item, "function", None) or getattr(item, "obj", None)
    doc = (getattr(fn, "__doc__", None) or "").strip()
    if not doc:
        return item.name
    first_line = doc.split("\n")[0]
    # Strip "TC-A01: " or "TC01: " style prefix if present
    return first_line.split(": ", 1)[-1] if ": " in first_line else first_line


@pytest_asyncio.fixture(autouse=True)
async def tc_logger(
    request: pytest.FixtureRequest,
    result_dir: Path,
) -> AsyncGenerator[None, None]:
    """Autouse fixture: emits TC START/PASSED/FAILED banners and binds the
    TC ID to every log record produced during the test via loguru contextualize.

    Terminal output (compact):
        10:25:01 | START    | [TC-A01] Login returns JWT token
        10:25:01 | STEP     | Step 1: Login with valid credentials  [email='...']
        10:25:01 | INFO     | POST /auth-api/login | 200 (342ms)
        10:25:02 | PASSED   | [TC-A01] PASSED (1.23s)

    File output (detailed, grep-friendly):
        2026-05-24 10:25:01.342 | START    | TC-A01    | fixtures.py:tc_logger:95   | [TC-A01] Login returns JWT token
        2026-05-24 10:25:01.688 | INFO     | TC-A01    | base_client.py:request:78  | POST /auth-api/login | 200 (342ms)
        2026-05-24 10:25:02.155 | PASSED   | TC-A01    | fixtures.py:tc_logger:107  | [TC-A01] PASSED (1.23s)
    """
    tc_id = _parse_tc_id(request.node.name)
    title = _parse_tc_title(request.node)
    start = time.perf_counter()

    with logger.contextualize(tc_id=f"TC-{tc_id}"):
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


@pytest_asyncio.fixture
async def browser_context(
    request: pytest.FixtureRequest,
    settings: Settings,
    result_dir: Path,
) -> AsyncGenerator[BrowserContext, None]:
    """Create a browser context with the required viewport and tracing."""

    async with async_playwright() as playwright:
        browser_launcher = getattr(playwright, settings.browser)
        launch_options: dict[str, Any] = {
            "headless": settings.headless,
            "slow_mo": settings.slow_mo,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if settings.browser == "chromium":
            launch_options["channel"] = "chromium"
        browser: Browser = await browser_launcher.launch(**launch_options)
        context = await browser.new_context(
            viewport={"width": settings.viewport_width, "height": settings.viewport_height},
            base_url=str(settings.base_url),
            record_video_dir=str(result_dir / "videos"),
            record_video_size={"width": settings.viewport_width, "height": settings.viewport_height},
        )
        trace_name = request.node.name.replace("/", "_").replace("\\", "_")
        try:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)
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
    """Create a new page for each test."""

    page_obj = await browser_context.new_page()
    setattr(request.node, "_playwright_page", page_obj)
    yield page_obj
    if "ui" in request.node.keywords:
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
    await page_obj.close()


@pytest_asyncio.fixture
async def authenticated_page(page: Page, settings: Settings) -> Page:
    """Return a Playwright page already authenticated through the UI."""

    email, password = require_credentials(settings.test_email, settings.test_password)
    login_page = LoginPage(page, str(settings.base_url))
    await login_page.open()
    await login_page.login(email, password)
    await HomePage(page, str(settings.base_url)).expect_loaded()
    return page


@pytest_asyncio.fixture
async def api_token(settings: Settings) -> str:
    """Return a fresh JWT access token for each test."""

    email, password = require_credentials(settings.test_email, settings.test_password)
    client = AuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        response = await client.login(email, password)
        return response.bearer_token
    finally:
        await client.close()


@pytest_asyncio.fixture
async def auth_client(settings: Settings, api_token: str) -> AsyncGenerator[AuthClient, None]:
    """Return an authenticated AuthClient."""

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
    """Return an authenticated AttendanceClient."""

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
