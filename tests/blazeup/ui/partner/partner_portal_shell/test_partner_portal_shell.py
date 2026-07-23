"""Partner Portal — shell all-pages load check (UI, shell-level).

PARTNER_UI_PARTNER_PORTAL_SHELL_001 walks every primary nav page of the partner
portal (stgpartners.blazeup.ai) via direct URL and asserts each page's content
module renders — its page-title READY_MARKER becomes visible in <main> and no MFE
error panel ("Something went wrong") appears.

One looping test = one test case = one START/FINISH banner + one verdict. The loop
soft-collects failures (does NOT stop at the first bad page), then reports a single
verdict naming exactly which page(s) failed.

Primary nav (verified live 2026-07-23): Dashboard, Deals, Commissions, Resources,
My Apps. The plan's step text named "My Pipeline / My Clients / Training", but the
live portal exposes Deals / Resources / My Apps instead ("My Pipeline" is the Deals
page, titled "Deal Pipeline"); the test drives the REAL nav — see
``PartnerShellLocators`` for the mapping note.
"""

import pytest
from loguru import logger

from locators.blazeup.partner.partner_shell_locators import PartnerShellLocators
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.log_helper import finalize_checks, ordinal

# All primary partner-portal nav pages.
PAGES = list(PartnerShellLocators.SECTIONS.keys())


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_partner_portal_shell_001(make_partner_page, request):
    """PARTNER_UI_PARTNER_PORTAL_SHELL_001: every primary nav page loads via URL (no MFE error).

    Navigation method: URL — PartnerShellPage.open() does page.goto(route) for each
    section, then wait_ready() asserts the section's READY_MARKER is visible in
    <main> (fast-fail on the MFE error panel). Covers the plan's "open main menu
    routes so that correct page content is shown".
    """
    shell = make_partner_page(PartnerShellPage)
    failures: list[str] = []

    # Warm-up: pay the one-off full SPA bootstrap (splash, vendor bundles) ONCE so
    # the first page in the loop isn't penalised by cold-start latency.
    logger.log("STEP", "Warm up SPA (open dashboard once)")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")

    for idx, section in enumerate(PAGES, start=1):
        page_name = PartnerShellLocators.SECTIONS[section]["label"]
        logger.info("Check page {}: {} loads (URL)", ordinal(idx), page_name)
        try:
            await shell.open(section)  # navigate by URL (page.goto)
            await shell.wait_ready(section)  # READY_MARKER in <main>; fast-fail on error panel
        except Exception as exc:  # noqa: BLE001 - soft-collect so all pages are checked
            logger.error("Page [{}] FAILED - {}", section, exc)
            failures.append(section)
            continue
        logger.info("Page [{}] PASSED", section)

    finalize_checks(request, failures, len(PAGES))
