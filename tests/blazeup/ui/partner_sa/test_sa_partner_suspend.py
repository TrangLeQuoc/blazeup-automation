"""SA Partner Module — suspend (deactivate) an active partner (UI, stgsa).

PARTNER_UI_SA_PARTNER_MODULE_015 — from the SA Partner Detail page, an active
partner is suspended via Partner actions → Deactivate. Expected: the partner
transitions out of Active (Suspended/Inactive) and portal access is revoked.

The "Deactivate Partner" dialog now has a required 'reason' textarea (FE fix for
BUG-UI-008, verified 2026-09-30); the page object fills it before confirming.
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
async def test_partner_ui_sa_partner_module_015(sa_cleanup, make_page, created_resources):
    """PARTNER_UI_SA_PARTNER_MODULE_015: suspend (deactivate) an active partner.

    Self-seeds a throwaway partner, approves it to Active, then deactivates it (with a
    reason) and asserts the partner is suspended (no longer Active) with no error banner.
    """
    detail = make_page(PartnerDetailPage)
    company = "QA-AUTO Suspend " + unique_email().split("@")[0].split("+")[1]
    email = unique_email()

    async with async_step("Setup: onboard a throwaway partner and approve it to Active"):
        await detail.open_directory()
        await detail.onboard_partner(company, email)
        # Register cleanup as soon as the record exists (before the assertions). This TC
        # can fail mid-way, so registering it late would leak the partner.
        created_resources.add(lambda: sa_cleanup.delete_partner_by_name(company))
        await detail.open_partner(company)
        await detail.approve_partner()
        status = await detail.status()
        assert status == "Active", f"precondition: partner must be Active, got {status!r}"
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
        # Read the status BADGE, not the page text. The previous check was
        #   "Active" not in banner or "Suspended" in banner or "Inactive" in banner
        # — three OR'd substring scans of all of <main>, so almost any page satisfied
        # one of them. ("Inactive" never renders on this build at all: verified live
        # 2026-08-10, so that third branch could not ever have been the reason it passed.)
        suspended = ("Suspended", "Inactive")
        status = await detail.wait_status(suspended)
        if status not in suspended:
            # Tell a stale badge (FE doesn't refetch) apart from a real no-op (BE didn't suspend).
            await detail.page.reload()
            await detail.wait_detail_ready()
            after_reload = await detail.status()
            assert after_reload not in suspended, (
                f"the partner IS suspended (badge reads {after_reload!r} after reload), but the "
                f"detail page kept showing {status!r} after Deactivate — the status badge is not "
                f"refreshed after the action. confirm with FE"
            )
        assert status in suspended, (
            f"the partner should no longer be Active after Deactivate — status badge "
            f"still reads {status!r} (also after reload). confirm with BE"
        )
        logger.info("RESULT: partner suspended via UI (status={})", status)
