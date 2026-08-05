"""SA Partner Module — SA Partner Detail page (UI, stgsa SA Dashboard).

PARTNER_UI_SA_PARTNER_MODULE_013 — the SA-side Partner Detail page loads with its
tabs (Overview / Deals / Commission / Members), the partner-info + Tier & Performance
+ Territory Assignments sections, and the Partner-actions control. Self-seeds a
throwaway partner via "Onboard Partner" (the Directory list is unreliable on staging).
"""

import pytest
from loguru import logger

from pages.blazeup.admin.partner_detail_page import PartnerDetailPage
from utils.data_factory import unique_email
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_sa_partner_module_013(make_page):
    """PARTNER_UI_SA_PARTNER_MODULE_013: the SA Partner Detail page loads.

    Onboards a throwaway partner, opens its detail, and confirms the detail chrome
    renders: the Overview/Deals/Commission/Members tabs, the Tier & Performance +
    Territory Assignments sections, the partner info (id + type + tier), and the
    Partner-actions control. Read-only load check (empty-safe).
    """
    detail = make_page(PartnerDetailPage)
    company = "QA-AUTO Detail " + unique_email().split("@")[0].split("+")[1]
    email = unique_email()

    async with async_step("Setup: onboard a throwaway partner and open its detail"):
        await detail.open_directory()
        await detail.onboard_partner(company, email)
        await detail.open_partner(company)

    async with async_step("[1/3] The detail tabs render"):
        for name in PartnerDetailPage.TABS:
            assert await detail.tab(name).is_visible(), (
                f"partner-detail tab '{name}' must be visible"
            )
        logger.info("CHECK tabs → OK ({})", ", ".join(PartnerDetailPage.TABS))

    async with async_step("[2/3] The Overview sections + partner info render"):
        text = await detail.detail_text()
        for name in PartnerDetailPage.SECTIONS:
            assert await detail.section(name).is_visible(), (
                f"partner-detail section '{name}' must be visible"
            )
        assert company in text, "the partner company name must be shown on the detail"
        assert "Channel" in text, "the partner Type (Channel) must be shown"
        assert "PAR-" in text, "the partner ID (PAR-…) must be shown"
        logger.info(
            "CHECK sections + info → OK ({} + partner info)", ", ".join(PartnerDetailPage.SECTIONS)
        )

    async with async_step("[3/3] The Partner-actions control renders"):
        assert await detail.actions_button().is_visible(), (
            "the 'Partner actions' control must be visible on the detail header"
        )
        logger.info("CHECK actions control → OK")

    logger.info("RESULT: SA Partner Detail loads with tabs, sections, info, and actions control")
