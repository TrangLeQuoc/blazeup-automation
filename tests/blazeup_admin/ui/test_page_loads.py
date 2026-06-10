"""SA Dashboard — all-pages load check (UI, shell-level).

Two tests, one per navigation method.  Each one is a SINGLE test case that walks
all 15 nav pages in a loop and asserts every page's micro-frontend module loads
without the "Something went wrong / Failed to fetch dynamically imported module"
panel:

    SHELL_UI_PAGE_LOADS_001  — via direct URL  (page.goto on each route)
    SHELL_UI_PAGE_LOADS_002  — via sidebar NAV (click the nav item)

Why one looping test instead of @pytest.mark.parametrize:
- One test function = one test case = one START/FINISH banner and one verdict in
  the run log (not 15 look-alike runs).
- The loop soft-collects failures (does NOT stop at the first bad page), then
  reports a single verdict naming exactly which page(s) failed.

Why both navigation methods:
- 001 (URL) is the stable correctness canary — does each page render at all,
  independent of the sidebar. Runs on every push (smoke).
- 002 (NAV) additionally proves the sidebar links actually route correctly —
  closer to real user navigation, but depends on the sidebar DOM, so it runs in
  the nightly regression rather than smoke.
"""

import pytest
from loguru import logger

from locators.blazeup_admin.shell_locators import ShellLocators
from pages.blazeup_admin.shell_page import ShellPage
from utils.log_helper import finalize_checks, ordinal

# All 15 SA Dashboard nav pages.
PAGES = list(ShellLocators.SECTIONS.keys())


@pytest.mark.ui
@pytest.mark.smoke
async def test_shell_ui_page_loads_001(make_page, request):
    """SHELL_UI_PAGE_LOADS_001: every page loads via direct URL (no MFE fetch error).

    Navigation method: URL — ShellPage.open() does page.goto(route) for each
    section, then asserts no module-fetch error panel.
    """
    shell = make_page(ShellPage)
    failures: list[str] = []

    # Warm-up: pay the one-off full SPA bootstrap (splash logo, vendor bundles)
    # ONCE so the first page in the loop isn't penalised by cold-start latency.
    logger.log("STEP", "Warm up SPA (open dashboard once)")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")

    for idx, section in enumerate(PAGES, start=1):
        page_name = ShellLocators.SECTIONS[section]["label"]
        logger.info("Check page {}: {} loads (URL)", ordinal(idx), page_name)
        try:
            await shell.open(section)  # navigate by URL (page.goto)
            await shell.wait_ready(
                section
            )  # READY_MARKER visible in <main>; fast-fail on error panel
        except Exception as exc:  # noqa: BLE001 - soft-collect so all pages are checked
            logger.error("Page [{}] FAILED - {}", section, exc)
            failures.append(section)
            continue
        logger.info("Page [{}] PASSED", section)

    finalize_checks(request, failures, len(PAGES))


@pytest.mark.ui
@pytest.mark.regression
async def test_shell_ui_page_loads_002(make_page, request):
    """SHELL_UI_PAGE_LOADS_002: every page loads via sidebar NAV click (no MFE fetch error).

    Navigation method: NAV — land on the dashboard shell first, then click the
    sidebar item for each section (ShellPage.click_nav), then assert no
    module-fetch error panel. Proves the sidebar links route correctly.
    """
    shell = make_page(ShellPage)
    failures: list[str] = []

    # Warm-up: pay the one-off full SPA bootstrap ONCE so the first sidebar
    # navigation in the loop isn't penalised by cold-start latency.
    logger.log("STEP", "Warm up SPA (open dashboard once)")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")

    for idx, section in enumerate(PAGES, start=1):
        page_name = ShellLocators.SECTIONS[section]["label"]
        logger.info("Check page {}: {} loads (NAV)", ordinal(idx), page_name)
        # Land on a page that is NOT the target so the sidebar click actually
        # navigates — clicking the already-active nav item is a no-op that never
        # settles (it would time out). Use 'tenants' as the neutral home when
        # the target itself is 'dashboard'.
        home = "dashboard" if section != "dashboard" else "tenants"
        try:
            await shell.open(home)  # land on the shell so the sidebar is present
            await shell.wait_ready(home)
            await shell.click_nav(section)  # navigate by clicking the sidebar item
            await shell.wait_ready(
                section
            )  # READY_MARKER visible in <main>; fast-fail on error panel
        except Exception as exc:  # noqa: BLE001 - soft-collect so all pages are checked
            logger.error("Page [{}] FAILED - {}", section, exc)
            failures.append(section)
            continue
        logger.info("Page [{}] PASSED", section)

    finalize_checks(request, failures, len(PAGES))
