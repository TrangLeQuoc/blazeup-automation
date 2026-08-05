"""Partner Portal Deals page object (/deals — "Deal Pipeline").

Content actions/reads for the pipeline page. Navigation + shell readiness come from
``PartnerShellPage`` (open("deals") + wait_ready("deals")); this object reads the
page-specific widgets (stage tabs + counts, controls), mirroring how the admin side
pairs ShellPage with DashboardPage.
"""

import contextlib
import re

from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from locators.blazeup.partner.deals_locators import DealsLocators
from pages.base_page import BasePage


class DealsPage(BasePage):
    """Reads the Deal Pipeline stage tabs, counts, and primary controls."""

    STAGES = DealsLocators.STAGES

    async def wait_list_settled(self, timeout: int = 15_000) -> None:
        """Wait until the deals-list data has settled (fetch done, loading spinner gone).

        The page title + stage tabs render from the dashboard fetch, but the deals
        table keeps a loading spinner until its OWN fetch returns. Waiting for network
        idle + the spinner to disappear gives a stable page (final counts, clean
        screenshot/video) before assertions — otherwise the page reads mid-load.
        """
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        # If the spinner is present, wait for it to clear; hidden/absent both pass.
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.locator(DealsLocators.LIST_SPINNER).first.wait_for(
                state="hidden", timeout=5_000
            )

    def stage_tab(self, stage: str) -> Locator:
        """Locator for a pipeline stage tab (role=tab), e.g. 'All' / 'Won'."""
        return self.page.get_by_role("tab", name=stage, exact=False).first

    async def stage_count(self, stage: str) -> int | None:
        """Return the deal count shown on a stage tab (e.g. 'Won 0' → 0), or None."""
        text = await self.stage_tab(stage).inner_text()
        m = re.search(r"(\d[\d,]*)", text)
        return int(m.group(1).replace(",", "")) if m else None

    def register_button(self) -> Locator:
        """The 'Register a deal' CTA."""
        return self.page.locator(DealsLocators.REGISTER_BUTTON).first

    def summary(self) -> Locator:
        """The pipeline summary line ('N deals in your pipeline'), scoped to <main>."""
        return self.page.locator("main").get_by_text(DealsLocators.SUMMARY_TEXT).first
