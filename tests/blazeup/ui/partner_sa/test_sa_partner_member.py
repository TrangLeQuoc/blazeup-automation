"""SA Partner Module — add a portal user (member) to a partner (UI, stgsa).

PARTNER_UI_SA_PARTNER_MODULE_014 — from the SA Partner Detail → Members tab, an
SA adds a portal user to an active partner and the new user appears in the Portal
Users list with the Active status.

Scope note: the Members tab exposes only "Add User" (create) + per-row "Reset
Password". There is NO member deactivate/reactivate/suspend control on this build
(verified live 2026-08-03), so the deactivate/reactivate half of this feature is
not automatable — this TC covers the buildable positive path (add + verify).
"""

import uuid

import pytest
from loguru import logger

from locators.blazeup.admin.partner_detail_locators import PartnerDetailLocators
from pages.blazeup.admin.partner_detail_page import PartnerDetailPage
from pytest_support.seeding import seed_partner
from utils.data_factory import make_partner, unique_email
from utils.log_helper import async_step


def _throwaway_password() -> str:
    """A random staging-only password for a throwaway portal user (never logged)."""
    return "Qa!" + uuid.uuid4().hex[:12] + "9"


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_sa_partner_module_014(sa_partners_client, make_page, created_resources):
    """PARTNER_UI_SA_PARTNER_MODULE_014: add a portal user (member) to a partner.

    Seeds a throwaway partner already approved to Active, opens the Members tab
    (empty), adds a portal user, and confirms the new user appears as an Active
    row and the Portal Users count reflects it.

    The partner is created and approved through the API, by the QA approver
    (``seed_partner`` → approval library). Since the approval-chain redesign a Pending
    partner's "⋮ → Approve" is shown only to its ASSIGNED approver, and the creating
    admin can never be one — the old UI approve step timed out (BUG-UI-013, closed
    2026-10-15 as not a bug). Approval is a precondition here, not what is under test.
    """
    detail = make_page(PartnerDetailPage)
    company = "QA-AUTO Member " + unique_email().split("@")[0].split("+")[1]
    member_email = unique_email()

    async with async_step("Setup: seed an Active partner (API, QA approver) and open its detail"):
        # seed_partner registers the deletion at creation time; deleting the partner also
        # removes the portal user added below, so one cleanup covers both.
        await seed_partner(
            sa_partners_client,
            created_resources.add,
            approve=True,
            payload=make_partner(name=company),
        )
        await detail.open_partner(company, status="Active")
        logger.info("SETUP → partner {} is Active", company)

    async with async_step("[1/3] The Members tab shows the Portal Users list (empty)"):
        await detail.open_members()
        assert await detail.members_heading().is_visible(), (
            "the Members tab must show the 'Portal Users' list"
        )
        # The OR here is legitimate — the control is labelled differently when the list
        # is empty — but it is asserted on the BUTTONS, not on a scan of the page text.
        assert await detail.add_user_button().is_visible(), (
            "an Add-User control must exist (either 'Add User' or 'Add First User')"
        )
        logger.info("CHECK Members tab → OK (Portal Users list + Add control)")

    async with async_step("[2/3] Add a portal user"):
        result = await detail.add_portal_user(
            first="Qa", last="Auto", email=member_email, password=_throwaway_password()
        )
        assert PartnerDetailLocators.MEMBER_CREATED_TOAST in result, (
            "adding a portal user must confirm "
            f"'{PartnerDetailLocators.MEMBER_CREATED_TOAST}'; got: {result[:200]!r}"
        )
        logger.info("CHECK create → OK ({})", PartnerDetailLocators.MEMBER_CREATED_TOAST)

    async with async_step("[3/3] The new user appears as an Active row"):
        row = detail.member_row(member_email)
        assert await row.is_visible(), (
            f"the new portal user '{member_email}' must appear in the list"
        )
        row_text = " ".join((await row.inner_text()).split())
        assert "Active" in row_text, "the new portal user's status must be Active"
        heading = " ".join((await detail.members_heading().inner_text()).split())
        assert "(1)" in heading, (
            f"the Portal Users count must reflect the added user; heading reads {heading!r}"
        )
        logger.info("CHECK new member row → OK (Active, count=1)")

    logger.info("RESULT: SA added a portal user; it appears Active in the Portal Users list")
