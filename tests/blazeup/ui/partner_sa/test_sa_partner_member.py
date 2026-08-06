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

from pages.blazeup.admin.partner_detail_page import PartnerDetailPage
from utils.data_factory import unique_email
from utils.log_helper import async_step


def _throwaway_password() -> str:
    """A random staging-only password for a throwaway portal user (never logged)."""
    return "Qa!" + uuid.uuid4().hex[:12] + "9"


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_sa_partner_module_014(sa_cleanup, make_page, created_resources):
    """PARTNER_UI_SA_PARTNER_MODULE_014: add a portal user (member) to a partner.

    Self-seeds a throwaway partner, approves it to Active, opens the Members tab
    (empty), adds a portal user, and confirms the new user appears as an Active
    row and the Portal Users count reflects it.
    """
    detail = make_page(PartnerDetailPage)
    company = "QA-AUTO Member " + unique_email().split("@")[0].split("+")[1]
    member_email = unique_email()

    async with async_step("Setup: onboard a throwaway partner and approve it to Active"):
        await detail.open_directory()
        await detail.onboard_partner(company, unique_email())
        # Register cleanup as soon as the record exists (before the assertions). Deleting
        # the partner also removes the portal user added below, so one cleanup covers both.
        created_resources.add(lambda: sa_cleanup.delete_partner_by_name(company))
        await detail.open_partner(company)
        await detail.approve_partner()
        logger.info("SETUP → partner {} is Active", company)

    async with async_step("[1/3] The Members tab shows the Portal Users list (empty)"):
        await detail.open_members()
        text = await detail.detail_text()
        assert "Portal Users" in text, "the Members tab must show the 'Portal Users' list"
        assert "Add User" in text or "Add First User" in text, "an Add-User control must exist"
        logger.info("CHECK Members tab → OK (Portal Users list + Add control)")

    async with async_step("[2/3] Add a portal user"):
        result = await detail.add_portal_user(
            first="Qa", last="Auto", email=member_email, password=_throwaway_password()
        )
        assert "created successfully" in result, (
            "adding a portal user must confirm 'Portal user created successfully'; "
            f"got: {result[:200]!r}"
        )
        logger.info("CHECK create → OK (Portal user created successfully)")

    async with async_step("[3/3] The new user appears as an Active row"):
        row = detail.member_row(member_email)
        assert await row.is_visible(), (
            f"the new portal user '{member_email}' must appear in the list"
        )
        row_text = " ".join((await row.inner_text()).split())
        assert "Active" in row_text, "the new portal user's status must be Active"
        assert "Portal Users (1)" in await detail.detail_text(), (
            "the Portal Users count must reflect the added user"
        )
        logger.info("CHECK new member row → OK (Active, count=1)")

    logger.info("RESULT: SA added a portal user; it appears Active in the Portal Users list")
