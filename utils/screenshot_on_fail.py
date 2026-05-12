"""Screenshot helper for failed Playwright tests."""

from pathlib import Path

import allure
from loguru import logger
from playwright.async_api import Page


async def attach_screenshot(page: Page, test_name: str, output_dir: str = "reports/screenshots") -> Path:
    """Capture a screenshot and attach it to Allure."""

    screenshot_dir = Path(output_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{test_name}.png"
    await page.screenshot(path=str(path), full_page=True)
    logger.info("Saved failure screenshot to {}", path)
    allure.attach.file(str(path), name="failure-screenshot", attachment_type=allure.attachment_type.PNG)
    return path

