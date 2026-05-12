"""Shared pytest fixtures for UI and API automation."""

import logging
import os
import sys
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from faker import Faker
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

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
    """Return the current run artifact directory."""

    for subfolder in ["logs", "videos", "screenshots", "traces", "allure-results"]:
        (RESULT_DIR / subfolder).mkdir(parents=True, exist_ok=True)
    log_level = os.getenv("BLAZEUP_LOG_LEVEL", "INFO")
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
        enqueue=True,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        RESULT_DIR / "logs" / "test.log",
        level=log_level,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
    return RESULT_DIR


@pytest.fixture(scope="session")
def test_data() -> dict[str, Any]:
    """Load YAML fixture test data."""

    return load_yaml(PROJECT_ROOT / "fixtures" / "test_data.yaml")


@pytest.fixture(scope="session")
def fake() -> Faker:
    """Return a Faker generator for dynamic test data."""

    return Faker()


@pytest.fixture(scope="session")
def browser_type_launch_args(settings: Settings) -> dict[str, Any]:
    """Customize pytest-playwright browser launch options."""

    return {
        "headless": settings.headless,
        "slow_mo": settings.slow_mo,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }


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
    client = AuthClient(str(settings.api_base_url), max_response_time_ms=settings.default_response_time_ms)
    try:
        response = await client.login(email, password)
        return response.bearer_token
    finally:
        await client.close()


@pytest_asyncio.fixture
async def auth_client(settings: Settings, api_token: str) -> AsyncGenerator[AuthClient, None]:
    """Return an authenticated AuthClient."""

    client = AuthClient(str(settings.api_base_url), token=api_token, max_response_time_ms=settings.default_response_time_ms)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def test_user(fake: Faker) -> AsyncGenerator[dict[str, str], None]:
    """Create test user data and reserve teardown point for future user API cleanup."""

    user = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "department": fake.job(),
    }
    logger.info("Prepared temporary user {}", user["email"])
    yield user
    logger.info("Temporary user cleanup hook completed for {}", user["email"])

