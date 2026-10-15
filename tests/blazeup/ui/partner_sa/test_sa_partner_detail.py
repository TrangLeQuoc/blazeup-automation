"""SA Partner Module — SA Partner Detail page (UI, stgsa SA Dashboard).

PARTNER_UI_SA_PARTNER_MODULE_013 — the SA-side Partner Detail page loads with its
tabs (Overview / Deals / Commission / Members), the partner-info + Tier & Performance
+ Territory Assignments sections, and — for the Pending partner it onboards — the
Approval-chain panel without the Partner-actions menu. Self-seeds a throwaway partner
via "Onboard Partner" (the Directory list is unreliable on staging).
"""

import pytest
from loguru import logger

from pages.blazeup.admin.partner_detail_page import PartnerDetailPage
from utils.data_factory import partner_name, unique_email
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_sa_partner_module_013(sa_cleanup, make_page, created_resources):
    """PARTNER_UI_SA_PARTNER_MODULE_013: the SA Partner Detail page loads.

    Onboards a throwaway partner, opens its detail, and confirms the detail chrome
    renders: the Overview/Deals/Commission/Members tabs, the Tier & Performance +
    Territory Assignments sections, the partner info (id + type + tier), and the header
    as a Pending partner shows it. Read-only load check (empty-safe).

    Header rule since the approval-chain redesign (confirmed 2026-10-15): the ⋮ "Partner
    actions" menu shows on a PENDING partner only to the SA assigned as its approver. The
    test logs in as the creating admin, which the chain never allows as approver — so the
    expected header is the Approval-chain panel ("0 / N approved") and NO ⋮. Until
    2026-10-14 this step asserted the ⋮ was visible, which belonged to the old
    "⋮ → Approve" flow.
    """
    detail = make_page(PartnerDetailPage)
    company = partner_name("Detail")
    email = unique_email()

    async with async_step("Setup: onboard a throwaway partner and open its detail"):
        await detail.open_directory()
        await detail.onboard_partner(company, email)
        # Register cleanup as soon as the record exists (before the assertions) so the
        # throwaway partner is removed even when a later step fails. The UI never exposes
        # the partner's `_id`, so cleanup resolves it from this unique company name.
        created_resources.add(lambda: sa_cleanup.delete_partner_by_name(company))
        await detail.open_partner(company)

    async with async_step("[1/3] The detail tabs render"):
        for name in PartnerDetailPage.TABS:
            assert await detail.tab(name).is_visible(), (
                f"partner-detail tab '{name}' must be visible"
            )
        logger.info("CHECK tabs → OK ({})", ", ".join(PartnerDetailPage.TABS))

    async with async_step("[2/3] The Overview sections + partner info render"):
        for name in PartnerDetailPage.SECTIONS:
            assert await detail.section(name).is_visible(), (
                f"partner-detail section '{name}' must be visible"
            )
        # Anchored to elements: "Channel" and the PAR- code render as their own text
        # nodes (probed live 2026-08-10), so an exact/regex match proves the field is
        # present rather than proving the word occurs somewhere in <main>.
        assert await detail.info_value(company).is_visible(), (
            "the partner company name must be shown on the detail"
        )
        assert await detail.info_value("Channel").is_visible(), (
            "the partner Type (Channel) must be shown"
        )
        assert await detail.partner_code().is_visible(), "the partner ID (PAR-…) must be shown"
        logger.info(
            "CHECK sections + info → OK ({} + partner info)", ", ".join(PartnerDetailPage.SECTIONS)
        )

    async with async_step(
        "[3/3] Pending partner: Approval chain shown, no Partner actions for a non-assigned SA"
    ):
        assert await detail.approval_chain_panel().is_visible(), (
            "a Pending partner's detail must show the Approval chain panel"
        )
        progress = await detail.approval_progress()
        assert progress is not None and progress[0] == 0 and progress[1] >= 1, (
            f"a freshly onboarded partner must read '0 / N approved' (N >= 1), got {progress}"
        )
        assert not await detail.actions_button().is_visible(), (
            "the 'Partner actions' menu must be hidden on a Pending partner for an SA who is "
            "not its assigned approver — and the creating admin never can be one"
        )
        logger.info(
            "CHECK header → OK (Approval chain {}/{} approved, no Partner actions)", *progress
        )

    logger.info("RESULT: SA Partner Detail loads with tabs, sections, info, and approval chain")
