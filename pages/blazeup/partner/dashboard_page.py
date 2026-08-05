"""Partner Portal Dashboard page object (/dashboard).

Content reads for the dashboard. Navigation + shell readiness come from
``PartnerShellPage`` (open("dashboard") + wait_ready("dashboard")); this object reads
the page-specific widgets (KPI cards, section panels).
"""

import re

from playwright.async_api import Locator

from locators.blazeup.partner.dashboard_locators import DashboardLocators
from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Reads the Dashboard KPI cards and section panels."""

    KPI_CARDS = DashboardLocators.KPI_CARDS
    SECTIONS = DashboardLocators.SECTIONS

    def kpi_card(self, label: str) -> Locator:
        """Locator for a KPI card by its label (e.g. 'Commission YTD')."""
        return self.page.locator("main").get_by_text(label, exact=False).first

    async def kpi_value(self, label: str) -> str:
        """Return the metric value shown with a KPI card (e.g. 'USD 0'), or ''.

        Cards render as "<value> <label>" in <main> (e.g. "USD 0 Total pipeline ACV"),
        so read the normalized main text and pull the value right before the label.
        """
        text = " ".join((await self.page.locator("main").inner_text()).split())
        m = re.search(r"(USD\s*[\d,]+(?:\.\d+)?|\b\d[\d,]*)\s*" + re.escape(label), text)
        return m.group(1) if m else ""

    def section(self, name: str) -> Locator:
        """Locator for a dashboard section heading (e.g. 'Pipeline Snapshot')."""
        return self.page.locator("main").get_by_text(name, exact=False).first

    async def tier_panel_text(self) -> str:
        """Return the 'Tier & Performance' panel text (up to the next section)."""
        text = " ".join((await self.page.locator("main").inner_text()).split())
        start = text.find("Tier & Performance")
        if start < 0:
            return ""
        end = text.find("Territory Assignments", start)
        return text[start:end] if end > start else text[start : start + 250]

    async def tier_progressbar_count(self) -> int:
        """Number of progress-bar elements rendered in <main> (tier qualification bar).

        The tier-qualification plan expects a progress bar toward the next-tier T12M
        ARR threshold. Counts ``role=progressbar`` / ``<progress>`` / ``progress``-class
        elements so a test can assert the bar is (or is not) rendered.
        """
        return await self.page.locator(
            "main [role='progressbar'], main progress, main [class*='progress']"
        ).count()
