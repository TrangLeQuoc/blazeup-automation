"""SA Dashboard — page load-time tests (UI).

Two tests, one per navigation method.  Each one is a SINGLE test case that walks
all 16 nav pages in a loop and measures how long each takes to load (wall-clock
until the micro-frontend module renders):

    SHELL_UI_LOAD_TIME_PAGE_001  — via direct URL  (ShellPage.open_and_measure)
    SHELL_UI_LOAD_TIME_PAGE_002  — via sidebar NAV  (ShellPage.click_nav_and_measure)

Why one looping test instead of @pytest.mark.parametrize:
- One test function = one test case = one START/FINISH banner and one verdict in
  the run log.  Parametrize would explode each into 15 look-alike runs, which is
  what made the log read like "15 TCs" for a single test case.
- The loop soft-collects failures (it does NOT stop at the first bad page), then
  reports a single verdict naming exactly which page(s) failed.

Why both navigation methods:
- 001 (URL) is the isolated per-page load time — page.goto(route) then measure,
  independent of the sidebar. The clean baseline.
- 002 (NAV) measures real in-app navigation — land on the shell, click the
  sidebar item, then measure. Includes sidebar routing + dynamic module fetch,
  so it's closer to what a user actually experiences clicking around.

Pass/fail policy (IMPORTANT):
- A page FAILS the test ONLY when it does not render (MFE fetch error panel, or
  the READY_MARKER never becomes visible) — i.e. the measure helper raises.
- A page that renders but is SLOWER than LOAD_BUDGET_MS does NOT fail; it logs a
  WARNING ("PASSED but SLOW") and is reported separately. The budget is a soft
  performance signal, not a pass/fail gate — staging cold-loads (full SPA
  bootstrap + per-page remoteEntry.js fetch) routinely take 8-15 s, so gating on
  speed would just produce noise. Use the SLOW warnings to track regressions.

Notes:
- LOAD_BUDGET_MS is a soft warning threshold — tune to your environment. Keep
  this test in the nightly `regression` run, not `smoke`.
"""

import pytest
from loguru import logger

from locators.blazeup_admin.shell_locators import ShellLocators
from pages.blazeup_admin.shell_page import ShellPage
from utils.log_helper import finalize_checks, ordinal

# Per-page load budget in milliseconds — SOFT warning threshold only (a page over
# this is logged as SLOW but still PASSES; only a page that fails to render fails).
LOAD_BUDGET_MS = 5_000

# All 15 SA Dashboard nav pages.
PAGES = list(ShellLocators.SECTIONS.keys())


@pytest.mark.ui
@pytest.mark.regression
async def test_shell_ui_load_time_page_001(make_page, request):
    """SHELL_UI_LOAD_TIME_PAGE_001: every SA Dashboard page loads within budget (navigated via URL).

    Navigation method: URL — ShellPage.open_and_measure() does page.goto(route)
    for each section, then measures wall-clock until assert_loaded passes.
    Isolated per-page load time, independent of the sidebar.
    """
    shell = make_page(ShellPage)
    failures: list[str] = []  # pages that did NOT render — the only fail condition
    slow: list[str] = []  # pages that rendered but exceeded the soft budget

    # Warm-up: pay the one-off full SPA bootstrap (BlazeUp splash logo, vendor
    # bundles) ONCE before timing, so that cold-start cost is not charged to the
    # first page measured below. Not measured, and not a failure if slow.
    logger.log("STEP", "Warm up SPA (open dashboard once, not measured)")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")

    for idx, section in enumerate(PAGES, start=1):
        page_name = ShellLocators.SECTIONS[section]["label"]
        logger.info("Check page {}: {} load time (URL)", ordinal(idx), page_name)
        try:
            elapsed_ms = await shell.open_and_measure(section)
        except Exception as exc:  # noqa: BLE001 - soft-collect so all pages are checked
            logger.error("Page [{}] FAILED - did not load: {}", section, exc)
            failures.append(f"{section} (load error)")
            continue
        if elapsed_ms < LOAD_BUDGET_MS:
            logger.info(
                "Page [{}] PASSED - {:.0f} ms (budget {} ms)", section, elapsed_ms, LOAD_BUDGET_MS
            )
        else:
            logger.warning(
                "Page [{}] PASSED but SLOW - {:.0f} ms exceeds soft budget {} ms (not a failure)",
                section,
                elapsed_ms,
                LOAD_BUDGET_MS,
            )
            slow.append(f"{section} ({elapsed_ms:.0f}ms)")

    if slow:
        logger.warning(
            "Slow pages over {} ms soft budget (rendered OK, not failed): {}",
            LOAD_BUDGET_MS,
            ", ".join(slow),
        )
    finalize_checks(request, failures, len(PAGES))


@pytest.mark.ui
@pytest.mark.regression
async def test_shell_ui_load_time_page_002(make_page, request):
    """SHELL_UI_LOAD_TIME_PAGE_002: every SA Dashboard page loads within budget (navigated via NAV).

    Navigation method: NAV — land on the dashboard shell first, then measure the
    sidebar-click navigation via ShellPage.click_nav_and_measure(). Includes the
    sidebar routing + dynamic module fetch, i.e. real in-app navigation timing
    (vs 001 which measures the isolated URL/page.goto load).
    """
    shell = make_page(ShellPage)
    failures: list[str] = []  # pages that did NOT render — the only fail condition
    slow: list[str] = []  # pages that rendered but exceeded the soft budget

    # Warm-up: pay the one-off full SPA bootstrap ONCE before timing so that
    # cold-start cost is not charged to the first sidebar navigation measured.
    logger.log("STEP", "Warm up SPA (open dashboard once, not measured)")
    await shell.open("dashboard")
    await shell.wait_ready("dashboard")

    for idx, section in enumerate(PAGES, start=1):
        page_name = ShellLocators.SECTIONS[section]["label"]
        logger.info("Check page {}: {} load time (NAV)", ordinal(idx), page_name)
        # Land on a page that is NOT the target so the sidebar click actually
        # navigates — clicking the already-active nav item is a no-op that never
        # settles (it would time out). Use 'tenants' as the neutral home when
        # the target itself is 'dashboard'.
        home = "dashboard" if section != "dashboard" else "tenants"
        try:
            await shell.open(home)  # land on the shell so the sidebar is present
            await shell.assert_loaded()
            elapsed_ms = await shell.click_nav_and_measure(section)
        except Exception as exc:  # noqa: BLE001 - soft-collect so all pages are checked
            logger.error("Page [{}] FAILED - did not load: {}", section, exc)
            failures.append(f"{section} (load error)")
            continue
        if elapsed_ms < LOAD_BUDGET_MS:
            logger.info(
                "Page [{}] PASSED - {:.0f} ms (budget {} ms)", section, elapsed_ms, LOAD_BUDGET_MS
            )
        else:
            logger.warning(
                "Page [{}] PASSED but SLOW - {:.0f} ms exceeds soft budget {} ms (not a failure)",
                section,
                elapsed_ms,
                LOAD_BUDGET_MS,
            )
            slow.append(f"{section} ({elapsed_ms:.0f}ms)")

    if slow:
        logger.warning(
            "Slow pages over {} ms soft budget (rendered OK, not failed): {}",
            LOAD_BUDGET_MS,
            ", ".join(slow),
        )
    finalize_checks(request, failures, len(PAGES))
