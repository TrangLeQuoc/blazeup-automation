"""Partner Portal page object.  (SCAFFOLD — wire up the TODO methods)

Mirrors the pattern in ``pages/blazeup_admin/login_page.py``:
    locators/blazeup_partner/  → selectors (data)
    pages/blazeup_partner/     → actions  (this file)
    tests/blazeup_partner/ui/  → scenarios

Usage in a test::

    from pages.blazeup_partner.partner_portal_page import PartnerPortalPage

    async def test_partner_ui_dashboard_001(authenticated_page, settings):
        portal = PartnerPortalPage(authenticated_page, str(settings.base_url))
        await portal.open_dashboard()
        assert await portal.get_dashboard_title()  # non-empty
"""

from loguru import logger

from locators.blazeup_partner.partner_portal_locators import PartnerPortalLocators
from pages.base_page import BasePage


class PartnerPortalPage(BasePage):
    """Actions and assertions for the Partner Portal shell + dashboard."""

    async def open_dashboard(self) -> None:
        """Navigate to the Partner dashboard."""
        # TODO: confirm the real route (e.g. "/dashboard" or "/partner/dashboard").
        await self.goto("/dashboard")
        logger.log("STEP", "Opened Partner dashboard")

    async def get_dashboard_title(self) -> str:
        """Return the dashboard heading text."""
        return await self.get_text(PartnerPortalLocators.DASHBOARD_TITLE)

    async def get_total_deals_kpi(self) -> str:
        """Return the 'Total Deals' KPI value as text."""
        return await self.get_text(PartnerPortalLocators.KPI_TOTAL_DEALS)

    async def open_user_menu(self) -> None:
        """Open the top-right user menu in the portal shell."""
        await self.click(PartnerPortalLocators.USER_MENU, label="Partner user menu")
