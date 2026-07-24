"""Partner Portal — responsive / mobile layout (UI, shell-level).

PARTNER_UI_PARTNER_PORTAL_SHELL_002 opens the partner portal at a common mobile
viewport (375×812) and asserts the shell stays usable on every primary nav page:
the section renders (READY_MARKER), the sidebar nav stays reachable, and the layout
does NOT overflow horizontally (no content cut off / sideways scroll). Then it
exercises navigation by tapping a sidebar link at mobile width.

One looping test = one test case = one verdict. Failures are soft-collected (all
pages checked) then reported as a single verdict naming the bad page(s).

Kept separate from the content check (SHELL_001): this TC is about LAYOUT at mobile
width, not data-load — so it asserts overflow/nav, not the "Failed to load" banner.
"""

import pytest
from loguru import logger

from locators.blazeup.partner.partner_shell_locators import PartnerShellLocators
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.log_helper import finalize_checks, ordinal

PAGES = list(PartnerShellLocators.SECTIONS.keys())
MOBILE = {"width": 375, "height": 812}  # iPhone-X class, a common mobile width
OVERFLOW_TOL = 5  # px allowance for a scrollbar; more than this = layout doesn't fit


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_partner_portal_shell_002(
    partner_authenticated_page, make_partner_page, request
):
    """PARTNER_UI_PARTNER_PORTAL_SHELL_002: portal stays usable at mobile width (no h-overflow, nav reachable).

    Resizes the authenticated page to a mobile viewport, then per primary page
    asserts: shell renders (READY_MARKER), >=1 nav link visible, and horizontal
    overflow <= a scrollbar allowance. Finally taps a sidebar link to prove mobile
    navigation works.
    """
    await partner_authenticated_page.set_viewport_size(MOBILE)
    logger.log("STEP", "Set mobile viewport {}x{}", MOBILE["width"], MOBILE["height"])
    shell = make_partner_page(PartnerShellPage)
    failures: list[str] = []

    # Warm-up: pay the one-off SPA bootstrap once (mobile) so page 1 isn't penalised.
    logger.log("STEP", "Warm up SPA (open dashboard once, mobile)")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")

    for idx, section in enumerate(PAGES, start=1):
        page_name = PartnerShellLocators.SECTIONS[section]["label"]
        logger.info("Check page {}: {} usable at mobile width", ordinal(idx), page_name)
        try:
            await shell.open(section)
            await shell.wait_ready(section)  # shell rendered (marker in <main>)
            nav_count = await shell.visible_nav_link_count()
            assert nav_count >= 1, f"no sidebar nav link visible at mobile on '{section}'"
            overflow = await shell.horizontal_overflow_px()
            assert overflow <= OVERFLOW_TOL, (
                f"'{section}' overflows the mobile viewport by {overflow}px "
                f"(content does not fit 375px → responsive-layout defect; confirm with FE)"
            )
        except Exception as exc:  # noqa: BLE001 - soft-collect so all pages are checked
            logger.error("Page [{}] FAILED - {}", section, exc)
            failures.append(section)
            continue
        logger.info("Page [{}] PASSED (nav={}, overflow<= {}px)", section, nav_count, OVERFLOW_TOL)

    # Exercise navigation at mobile: tap a sidebar link and confirm it routes.
    logger.log("STEP", "Exercise mobile nav: tap sidebar link → 'commissions'")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")
    link = partner_authenticated_page.locator("aside a[href='/commissions']").first
    await link.click(timeout=15_000)
    await shell.wait_ready("commissions")
    logger.info("Mobile nav tap → 'commissions' routed and rendered")

    finalize_checks(request, failures, len(PAGES))
