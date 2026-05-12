"""Home page object for dashboard widgets and navigation."""

import re

from loguru import logger
from playwright.async_api import Locator, expect

from pages.base_page import BasePage
from locator.home_ui import HomeSelectors


class HomePage(BasePage):
    """Actions and assertions for the HRMS home dashboard."""

    async def expect_loaded(self) -> None:
        """Assert that the home dashboard is visible."""

        await expect(self._greeting_locator()).to_be_visible(timeout=15_000)

    async def greeting_text(self) -> str:
        """Return the dashboard greeting text."""

        text = await self._greeting_locator().inner_text(timeout=10_000)
        return " ".join(text.split())

    async def expect_celebrations_widget(self) -> None:
        """Verify celebrations widget and tabs are visible."""

        await expect(self.page.get_by_text("Celebrations", exact=False)).to_be_visible()
        for tab_name in ["All", "Birthdays", "Anniversaries"]:
            await expect(self.page.get_by_role("tab", name=tab_name)).to_be_visible()

    async def expect_attendance_status(self, expected: str) -> None:
        """Verify attendance widget status text."""

        await expect(self.page.get_by_text(expected, exact=False)).to_be_visible()

    async def select_location(self, location: str) -> None:
        """Select attendance location when the control is available."""

        logger.info("Selecting attendance location {}", location)
        dropdown = self.page.locator(HomeSelectors.LOCATION_DROPDOWN).first
        await expect(dropdown).to_be_visible(timeout=10_000)
        if await dropdown.evaluate("node => node.tagName.toLowerCase() === 'select'"):
            await dropdown.select_option(label=location)
        else:
            await dropdown.click()
            await self.page.get_by_role("option", name=location).click()

    async def clock_in(self, location: str = "Office") -> None:
        """Clock in from the attendance widget."""

        await self.select_location(location)
        await self.click(HomeSelectors.CLOCK_IN_BUTTON)

    async def logout(self) -> None:
        """Log out from the application."""

        await self.click(HomeSelectors.LOGOUT_BUTTON)

    def _greeting_locator(self) -> Locator:
        """Return a locator for the dashboard greeting."""

        css_locator = self.page.locator(HomeSelectors.GREETING_CSS).first
        text_locator = self.page.get_by_text(re.compile(HomeSelectors.GREETING_TEXT_PATTERN, re.IGNORECASE)).first
        return css_locator.or_(text_locator).first
