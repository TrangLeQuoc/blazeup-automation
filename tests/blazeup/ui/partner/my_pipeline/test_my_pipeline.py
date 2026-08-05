"""Partner Portal — My Pipeline (Deals) page (UI, Layer-B content).

Per-page CONTENT tests for the Deal Pipeline page (/deals). Navigation + shell
readiness come from PartnerShellPage; page-specific widgets are read via DealsPage.

    PARTNER_UI_MY_PIPELINE_014 — open my pipeline: all 6 stage tabs + their deal
                                 counts are visible (works with an empty pipeline).
"""

import pytest
from loguru import logger

from pages.blazeup.partner.deals_page import DealsPage
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_014(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_014: open My Pipeline — all deal stages and their counts are visible.

    Opens the Deals page via the shell, then asserts the pipeline shows all 6 stage
    tabs (All/Pending/Approved/Won/Lost/Expired) each with a numeric deal count, plus
    the pipeline summary and the Register CTA. Read-only: works with an empty
    pipeline (counts may be 0) — it verifies the stages RENDER, not any specific data.
    """
    shell = make_partner_page(PartnerShellPage)
    deals = make_partner_page(DealsPage)

    async with async_step("Setup: open the Deals page (My Pipeline) and let it settle"):
        await shell.open("deals")
        await shell.wait_ready("deals")  # marker "Deal Pipeline" in <main>; fast-fail on panel
        await deals.wait_list_settled()  # deals-list fetch done + spinner gone (stable page)

    async with async_step("[1/3] All 6 pipeline stage tabs are visible"):
        for stage in DealsPage.STAGES:
            tab = deals.stage_tab(stage)
            assert await tab.is_visible(), f"stage tab '{stage}' is not visible on the pipeline"
        logger.info("CHECK stages → OK (visible: {})", ", ".join(DealsPage.STAGES))

    async with async_step("[2/3] Every stage tab shows a numeric deal count"):
        counts: dict[str, int] = {}
        for stage in DealsPage.STAGES:
            count = await deals.stage_count(stage)
            assert count is not None, f"stage tab '{stage}' shows no numeric count"
            assert count >= 0, f"stage '{stage}' count must be >= 0, got {count}"
            counts[stage] = count
        logger.info("CHECK counts → OK ({})", counts)

    async with async_step("[3/3] Pipeline summary + Register CTA are visible"):
        assert await deals.summary().is_visible(), (
            "pipeline summary ('… deals in your pipeline') is not visible"
        )
        assert await deals.register_button().is_visible(), "'Register a deal' CTA is not visible"
        logger.info("CHECK controls → OK (summary + Register a deal visible)")

    logger.info("RESULT: My Pipeline shows all 6 stages with counts {}", counts)
