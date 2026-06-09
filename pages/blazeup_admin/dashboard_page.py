"""SA Dashboard **Dashboard** page object — content actions.  (Layer-B example)

Relationship to the shell object:
    ShellPage (page_locators.py)  -> navigate + assert the section
                                                module loaded (works for all 15).
    DashboardPage (this file)     -> read widgets ON the Dashboard
                                                page once it has loaded.

A Layer-B test typically does both::

    shell = ShellPage(authenticated_page, base_url)
    await shell.open("dashboard")
    await shell.assert_loaded()
    dash = DashboardPage(authenticated_page, base_url)
    assert await dash.kpi_card_count() >= 1

Use this file as the template for the other 14 pages: one
``<Section>Page`` per section, reading from its
``<section>_locators.py`` locator file.
"""

from loguru import logger
from playwright.async_api import expect

from locators.blazeup_admin.dashboard_locators import DashboardLocators
from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Read-only actions for the SA Dashboard landing page widgets."""

    async def assert_heading(self, timeout: int = 15_000) -> None:
        """Assert the Dashboard page heading is visible."""
        heading = self.page.locator(DashboardLocators.PAGE_HEADING).first
        await expect(heading).to_be_visible(timeout=timeout)

    async def kpi_card_count(self) -> int:
        """Return how many KPI cards are rendered on the page."""
        return await self.page.locator(DashboardLocators.KPI_CARD).count()

    async def get_kpi(self, label: str) -> str:
        """Return the value text of a KPI card identified by its visible label.

        ``KPI_CARD`` matches the label <div> (e.g. "MRR"); the value lives in a
        sibling within the same card container, so we step up to the parent card
        and strip the label text off its content (e.g. "MRR $48.2K ↑ +2.3%" →
        "$48.2K ↑ +2.3%").
        """
        logger.log("STEP", "Read KPI [{}]", label)
        label_el = self.page.locator(DashboardLocators.KPI_CARD).filter(has_text=label).first
        card = label_el.locator("xpath=..")
        text = " ".join((await card.inner_text(timeout=10_000)).split())
        return text[len(label):].strip() if text.startswith(label) else text

    async def is_system_health_visible(self) -> bool:
        """Return True if the 'System Health' panel is shown."""
        panel = self.page.locator(DashboardLocators.SYSTEM_HEALTH_PANEL).first
        return await panel.is_visible()

    async def is_risk_signals_visible(self) -> bool:
        """Return True if the 'Risk Signals' panel is shown."""
        panel = self.page.locator(DashboardLocators.RISK_SIGNALS_PANEL).first
        return await panel.is_visible()
