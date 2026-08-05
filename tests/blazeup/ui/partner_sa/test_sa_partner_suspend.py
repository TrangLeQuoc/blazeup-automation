"""SA Partner Module — suspend (deactivate) an active partner (UI, stgsa).

PARTNER_UI_SA_PARTNER_MODULE_015 — from the SA Partner Detail page, an active
partner is suspended via Partner actions → Deactivate. Expected: the partner
transitions out of Active (Suspended/Inactive) and portal access is revoked.

Fail-by-design (be_gap): the "Deactivate Partner" confirm dialog collects NO
'reason', but the deactivate API *requires* a non-empty reason string. The FE
sends the request without one, so the BE rejects it ("reason should not be
empty / must be a string / must be shorter than or equal to 2000 characters")
and the UI shows "Failed to deactivate partner / Server Error" while the partner
stays Active. No SA can suspend a partner through the UI. Confirm with BE.
"""

import pytest
from loguru import logger

from pages.blazeup.admin.partner_detail_page import PartnerDetailPage
from utils.data_factory import unique_email
from utils.log_helper import async_step

# Backend validation strings echoed in the failure banner (contract mismatch proof).
_BE_ERROR_MARKERS = ("Failed to deactivate", "Server Error", "reason should not be empty")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.be_gap  # Deactivate dialog sends no 'reason'; BE requires it -> suspend fails. Confirm with BE.
async def test_partner_ui_sa_partner_module_015(make_page):
    """PARTNER_UI_SA_PARTNER_MODULE_015: suspend (deactivate) an active partner.

    Self-seeds a throwaway partner, approves it to Active, then deactivates it and
    asserts the partner is suspended (no longer Active) with no error banner. Fails
    by design on the FE↔BE 'reason' contract gap (see module docstring).
    """
    detail = make_page(PartnerDetailPage)
    company = "QA-AUTO Suspend " + unique_email().split("@")[0].split("+")[1]
    email = unique_email()

    async with async_step("Setup: onboard a throwaway partner and approve it to Active"):
        await detail.open_directory()
        await detail.onboard_partner(company, email)
        await detail.open_partner(company)
        await detail.approve_partner()
        assert "Active" in await detail.detail_text(), "precondition: partner must be Active"
        logger.info("SETUP → partner {} is Active", company)

    async with async_step("[1/2] Deactivate (suspend) the active partner"):
        banner = await detail.deactivate_partner()
        logger.info("Deactivate result banner: {}", banner[:200])

    async with async_step("[2/2] The partner is suspended and no error is shown"):
        error = next((m for m in _BE_ERROR_MARKERS if m in banner), None)
        assert error is None, (
            "Deactivate failed — the BE rejected the request: "
            f"'{banner[: banner.find('Overview') if 'Overview' in banner else 200].strip()}'. "
            "The 'Deactivate Partner' confirm dialog collects no 'reason', but the "
            "deactivate API requires a non-empty reason string (reason should not be "
            "empty / must be a string / must be <= 2000 chars). No SA can suspend a "
            "partner via the UI. confirm with BE"
        )
        assert "Active" not in banner or "Suspended" in banner or "Inactive" in banner, (
            "the partner should no longer be Active after Deactivate (Suspended/Inactive). "
            "confirm with BE"
        )
        logger.info("RESULT: partner suspended via UI")
