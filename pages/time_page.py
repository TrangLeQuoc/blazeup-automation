"""Time and attendance page object."""

from playwright.async_api import expect

from pages.base_page import BasePage
from locator.time_ui import TimeSelectors


class TimePage(BasePage):
    """Page object for dedicated Time module workflows."""

    async def open(self) -> None:
        """Open the Time module."""

        await self.goto("/time")

    async def clock_in(self) -> None:
        """Click the Clock In button."""

        await self.click(TimeSelectors.CLOCK_IN_BUTTON)

    async def clock_out(self) -> None:
        """Click the Clock Out button."""

        await self.click(TimeSelectors.CLOCK_OUT_BUTTON)

    async def expect_history_for_date(self, date_text: str) -> None:
        """Verify attendance history contains a specific date label."""

        await expect(self.page.get_by_text(date_text, exact=False)).to_be_visible()
