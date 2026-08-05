"""SA Partner Programme Analytics page object (/partners/analytics).

Content reads for the SA-side partner-programme analytics dashboard (PRD §7).
Navigates directly to /partners/analytics (a sub-route of the Partners area), waits
for the dashboard shell to render, and reads the KPI cards / funnel / tier
distribution / top-partners sections. Also exposes a check for the "Server Error /
Invalid pagination" backend-defect banner so a test can assert the data loaded.
"""

import contextlib
import time

from loguru import logger
from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from locators.blazeup.admin.partner_analytics_locators import PartnerAnalyticsLocators
from locators.blazeup.admin.shell_locators import ShellLocators
from pages.base_page import BasePage


class PartnerAnalyticsPage(BasePage):
    """Reads the SA Partner Programme Analytics KPI cards, funnel, and sections."""

    KPI_CARDS = PartnerAnalyticsLocators.KPI_CARDS
    FUNNEL_STAGES = PartnerAnalyticsLocators.FUNNEL_STAGES
    SECTIONS = PartnerAnalyticsLocators.SECTIONS

    def _main(self) -> Locator:
        return self.page.locator("main")

    async def open(self) -> None:
        """Navigate directly to the SA Partner Programme Analytics dashboard."""
        await self.goto(PartnerAnalyticsLocators.ROUTE)

    async def wait_ready(self, timeout: int = 90_000, poll_ms: int = 500) -> None:
        """Wait until the dashboard shell rendered: the 'Deal Funnel' section is visible.

        Fast-fails on the MFE error panel (broken deploy). The "Deal Funnel" heading is
        a stable element proving the dashboard mounted (distinct from a data-query
        error banner, which may still be present).
        """
        logger.log("STEP", "Wait ready [analytics] = 'Deal Funnel' section in <main>")
        funnel = self._main().get_by_text("Deal Funnel", exact=False).first
        error_loc = self.page.locator(ShellLocators.ERROR_PANEL).first
        deadline = time.perf_counter() + timeout / 1000
        while True:
            if await error_loc.is_visible():
                raise AssertionError(
                    "SA Partner Analytics failed to load: the MFE error panel "
                    "('Something went wrong') is visible. Deploy/MFE issue, not a test bug."
                )
            if await funnel.is_visible():
                return
            if time.perf_counter() >= deadline:
                raise AssertionError(
                    "SA Partner Analytics did not render within "
                    f"{timeout} ms: the 'Deal Funnel' section never became visible in <main>."
                )
            await self.page.wait_for_timeout(poll_ms)

    async def wait_data_settled(self, timeout: int = 20_000, settle_ms: int = 1_000) -> None:
        """Wait until the async analytics queries RESOLVED before asserting on them.

        ``wait_ready`` only proves the shell mounted; the KPI/funnel/tier data is
        fetched asynchronously and the 'Server Error / Invalid pagination' banner
        paints a moment later. Checking for the error right after the shell races
        that pending request and can read a FALSE 'no error' (the banner then shows
        in the video, on a "passing" run). Wait for network idle + a paint buffer.
        """
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        await self.page.wait_for_timeout(settle_ms)

    def kpi_card(self, label: str) -> Locator:
        """Locator for a KPI card by its label (e.g. 'Win Rate')."""
        return self._main().get_by_text(label, exact=False).first

    def funnel_stage(self, name: str) -> Locator:
        """Locator for a Deal Funnel stage label (e.g. 'Approved')."""
        return self._main().get_by_text(name, exact=False).first

    def section(self, name: str) -> Locator:
        """Locator for a named section heading (e.g. 'Tier Distribution')."""
        return self._main().get_by_text(name, exact=False).first

    async def server_error_text(self) -> str:
        """Return the visible backend-defect banner text, or '' if the data loaded cleanly.

        Looks for "Server Error" / "Invalid pagination" / "limit must not" in <main>. A
        non-empty return means an analytics data query failed — the dashboard shell
        rendered but its content is degraded (a backend defect, not a test bug).
        """
        text = " ".join((await self._main().inner_text()).split())
        for phrase in PartnerAnalyticsLocators.SERVER_ERROR_TEXTS:
            if phrase.lower() in text.lower():
                idx = text.lower().find(phrase.lower())
                return text[idx : idx + 70]
        return ""
