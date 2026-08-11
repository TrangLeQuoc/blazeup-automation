"""SA Partner Module — SA Partner Programme Analytics (UI, stgsa SA Dashboard).

Per-page CONTENT test for the SA-side Partner Programme Analytics dashboard
(/partners/analytics, PRD §7). Runs on the SA Dashboard (stgsa) via the super-admin
``make_page`` fixtures.

    PARTNER_UI_SA_PARTNER_MODULE_011 — the SA analytics dashboard: funnel + KPI + tier
                                       distribution + top-partners render and load cleanly.
"""

import pytest
from loguru import logger

from pages.blazeup.admin.partner_analytics_page import PartnerAnalyticsPage
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.be_gap  # BUG-UI-006: analytics query 400s ("limit must not exceed 100"). Confirm with BE.
async def test_partner_ui_sa_partner_module_011(make_page):
    """PARTNER_UI_SA_PARTNER_MODULE_011: the SA partner-programme analytics dashboard.

    Opens the SA Partner Programme Analytics dashboard and confirms it renders its
    shell — the summary KPI cards, the Deal Funnel stages, and the Tier Distribution /
    Top Partners sections — then that its data loaded with no backend error.

    Live status: the dashboard shell renders (KPIs + funnel + sections), but a
    paginated analytics query fails with "Server Error — Invalid pagination: limit
    must not exceed 100" (a backend defect). Steps [1-2] PASS (shell renders); step
    [3] FAILS with "confirm with BE" on the server error. This surfaces the real
    defect rather than faking a green.
    """
    analytics = make_page(PartnerAnalyticsPage)

    async with async_step("Setup: open the SA Partner Programme Analytics dashboard"):
        await analytics.open()
        await analytics.wait_ready()

    async with async_step("[1/3] Summary KPI cards + Deal Funnel stages render"):
        for label in PartnerAnalyticsPage.KPI_CARDS:
            assert await analytics.kpi_card(label).is_visible(), (
                f"analytics KPI card '{label}' must be visible"
            )
        for stage in PartnerAnalyticsPage.FUNNEL_STAGES:
            assert await analytics.funnel_stage(stage).is_visible(), (
                f"Deal Funnel stage '{stage}' must be visible"
            )
        logger.info(
            "CHECK KPIs + funnel → OK ({} | {})",
            ", ".join(PartnerAnalyticsPage.KPI_CARDS),
            ", ".join(PartnerAnalyticsPage.FUNNEL_STAGES),
        )

    async with async_step("[2/3] The Tier Distribution + Top Partners sections render"):
        for name in PartnerAnalyticsPage.SECTIONS:
            assert await analytics.section(name).is_visible(), (
                f"analytics section '{name}' must be visible"
            )
        logger.info("CHECK sections → OK ({})", ", ".join(PartnerAnalyticsPage.SECTIONS))

    async with async_step("[3/3] The analytics data loads without a server error"):
        await analytics.wait_data_settled()  # the queries are async — wait, don't race them
        err = await analytics.server_error_text()
        assert not err, (
            "the analytics dashboard must load its data, but a query fails with a backend "
            f"error: {err!r}. The dashboard shell renders but a paginated analytics query "
            "is rejected (limit must not exceed 100) — a backend defect. Confirm with BE."
        )
        logger.info("CHECK data loads → OK (no server error banner)")

    logger.info("RESULT: SA analytics dashboard shows funnel + KPIs + sections with data loaded")
