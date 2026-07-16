"""SA Dashboard — Dashboard page content (UI, Layer-B).

Per-page CONTENT tests for the Dashboard landing page (KPI cards, System Health,
Risk Signals). The generic "does the page load" check is NOT here — it lives once
for all 16 pages in test_page_loads.py (SHELL_UI_PAGE_LOADS_001).

Naming: each page is its own module, so content tests are DASHBOARD_UI_<FEATURE>_NNN
(here VISIBLE = key widgets render). This file is the template for the other 15
pages: each gets test_<page>.py with <PAGE>_UI_<FEATURE>_NNN tests, plus a
<page>_locators.py / <page>_page.py pair, created when real selectors exist.
"""

import pytest
from loguru import logger

from pages.blazeup.admin.dashboard_page import DashboardPage
from pages.blazeup.admin.shell_page import ShellPage

SECTION = "dashboard"


@pytest.mark.ui
@pytest.mark.regression
async def test_dashboard_ui_visible_001(make_page):
    """DASHBOARD_UI_VISIBLE_001: Dashboard shows KPI cards + System Health panel (navigated via URL).

    Navigation method: URL — ShellPage.open() does page.goto(route) for the
    Dashboard section.

    Layer-B content example. Navigate + assert_loaded via the shell, then read
    page-specific widgets via the per-section page object. Each element-visibility
    check logs a STEP (what is being checked) and an INFO PASSED/FAILED with the
    observed value, so the run log shows the verification clearly.
    """
    shell = make_page(ShellPage)
    await shell.open(SECTION)
    await shell.wait_ready(SECTION)  # wait past the splash until rendered; fast-fail if broken

    dash = make_page(DashboardPage)

    logger.log("STEP", "Check element [KPI cards] visible (expect >= 1)")
    kpi_count = await dash.kpi_card_count()
    assert kpi_count >= 1, "Expected at least one KPI card on the Dashboard"
    logger.info("element [KPI cards] PASSED - {} card(s) visible", kpi_count)

    logger.log("STEP", "Check element [System Health panel] visible")
    health_visible = await dash.is_system_health_visible()
    assert health_visible, "'System Health' panel not visible"
    logger.info("element [System Health panel] PASSED - visible")

    logger.log("STEP", "Check element [Risk Signals panel] visible")
    risk_visible = await dash.is_risk_signals_visible()
    assert risk_visible, "'Risk Signals' panel not visible"
    logger.info("element [Risk Signals panel] PASSED - visible")
