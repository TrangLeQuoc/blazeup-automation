"""Partner Portal — Commissions page (UI, Layer-B content).

Per-page CONTENT tests for the Commissions page (/commissions). Navigation + shell
readiness come from PartnerShellPage; page-specific widgets via CommissionsPage.

    PARTNER_UI_COMMISSIONS_002 — open Commissions: the earned/pending/paid summary
                                 totals + ledger tabs are visible (empty-safe).
"""

import pytest
from loguru import logger

from pages.blazeup.partner.commissions_page import CommissionsPage
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_commissions_002(make_partner_page):
    """PARTNER_UI_COMMISSIONS_002: Commissions page shows earned/pending/paid totals + ledger tabs.

    Opens the Commissions page via the shell, then asserts the 4 summary stat cards
    (Pending Payout / Paid YTD / Total Earned / Clawback Risk) each render with a $
    amount, and all ledger status tabs are present. Read-only: works with an empty
    ledger (amounts may be $0) — it verifies the page RENDERS its structure.
    """
    shell = make_partner_page(PartnerShellPage)
    comm = make_partner_page(CommissionsPage)

    async with async_step("Setup: open the Commissions page and let it settle"):
        await shell.open("commissions")
        await shell.wait_ready("commissions")  # marker "Commissions" in <main>
        await comm.wait_list_settled()

    async with async_step("[1/2] The 4 summary totals render, each with a $ amount"):
        amounts: dict[str, str] = {}
        for label in CommissionsPage.SUMMARY_CARDS:
            assert await comm.summary_card(label).is_visible(), (
                f"summary card '{label}' is not visible on the Commissions page"
            )
            amount = await comm.summary_amount(label)
            assert amount.startswith("$"), f"card '{label}' must show a $ amount, got {amount!r}"
            amounts[label] = amount
        logger.info("CHECK totals → OK ({})", amounts)

    async with async_step("[2/2] All ledger status tabs are visible"):
        for name in CommissionsPage.TABS:
            assert await comm.tab(name).is_visible(), f"ledger tab '{name}' is not visible"
        logger.info("CHECK tabs → OK (visible: {})", ", ".join(CommissionsPage.TABS))

    logger.info("RESULT: Commissions shows earned/pending/paid totals + all ledger tabs")
