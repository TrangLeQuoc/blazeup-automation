"""SA Partner Module — SA Deal Approval Queue (UI, stgsa SA Dashboard).

Per-page CONTENT tests for the SA-side Deal Approval Queue (/partners/deals, PRD
§5.2). Runs on the SA Dashboard (stgsa) via the super-admin ``make_page`` fixtures.

    PARTNER_UI_SA_PARTNER_MODULE_007 — the SA deal approval queue renders its shell
                                       and its deal list loads (no backend error).
"""

import pytest
from loguru import logger

from pages.blazeup.admin.deal_approval_queue_page import DealApprovalQueuePage
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.be_gap  # deal-list fetch 400s ("Invalid id: 'pro-v1'") — no rows load. Confirm with BE.
async def test_partner_ui_sa_partner_module_007(make_page):
    """PARTNER_UI_SA_PARTNER_MODULE_007: the SA deal approval queue loads its deals.

    Opens the SA Deal Approval Queue and confirms it renders its shell — the
    Deal Type + Conflicts-only filters and the deals table header — then that the
    queue actually LOADS its deals (no backend error).

    Live status: the queue shell renders, but the deal-list fetch fails with
    "Server Error / Invalid id: 'pro-v1'" (a backend defect) — so no deal rows load
    even though partners have open deals. Step [1] PASSES (shell/filters/header);
    step [2] FAILS with "confirm with BE" on the server error, surfacing the real
    defect rather than faking a green.
    """
    queue = make_page(DealApprovalQueuePage)

    async with async_step("Setup: open the SA Deal Approval Queue (/partners/deals)"):
        await queue.open()
        await queue.wait_ready()

    async with async_step("[1/2] The queue shell renders — filters + deals table header"):
        for name in DealApprovalQueuePage.FILTERS:
            assert await queue.filter_control(name).is_visible(), (
                f"filter control '{name}' must be visible on the deal approval queue"
            )
        headers = await queue.column_headers()
        missing = [h for h in DealApprovalQueuePage.TABLE_HEADERS if h not in headers]
        assert not missing, f"deals table is missing column headers: {missing} (got {headers})"
        logger.info(
            "CHECK shell → OK (filters: {} | headers: {})",
            ", ".join(DealApprovalQueuePage.FILTERS),
            ", ".join(DealApprovalQueuePage.TABLE_HEADERS),
        )

    async with async_step("[2/2] The deal list loads without a server error"):
        await queue.wait_deal_list_settled()  # the fetch is async — wait, don't race it
        err = await queue.server_error_text()
        assert not err, (
            "the deal approval queue must load its deals, but the deal-list fetch fails "
            f"with a backend error: {err!r}. The queue shell renders but no deals load "
            "(partners have open deals) — a backend defect on the SA deal-list API. Confirm with BE."
        )
        logger.info("CHECK deals load → OK (no server error)")

    logger.info("RESULT: SA deal approval queue renders and loads its deals")
