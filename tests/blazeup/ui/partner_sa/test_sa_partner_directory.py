"""SA Partner Module — Partner Directory page (UI, stgsa SA Dashboard).

Per-page CONTENT tests for the SA-side Partner Directory (/partners). Navigation +
shell readiness come from the SA ``ShellPage``; page-specific widgets via
``PartnerDirectoryPage``. Runs on the SA Dashboard (stgsa) via the ``make_page`` /
``authenticated_page`` (super-admin) fixtures — NOT the partner portal (stgpartners).

    PARTNER_UI_SA_PARTNER_MODULE_003 — the Partner Directory loads with its filters
                                       and partner table (empty-safe).
"""

import pytest
from loguru import logger

from pages.blazeup.admin.partner_directory_page import PartnerDirectoryPage
from pages.blazeup.admin.shell_page import ShellPage
from utils.log_helper import async_step

SECTION = "partners"


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_sa_partner_module_003(make_page):
    """PARTNER_UI_SA_PARTNER_MODULE_003: the SA Partner Directory loads (filters + rows).

    Opens the SA Dashboard "Partners" area and confirms the Partner Directory
    renders: the breadcrumb + summary stat cards, the Status/Tier filter controls +
    the "Onboard Partner" action, and the partner table with its full column header.
    Read-only + empty-safe: with no partners the table shows its "No Data Found"
    empty state (data rows appear here once partners exist) — it verifies the
    directory STRUCTURE renders, not any specific partner row.
    """
    shell = make_page(ShellPage)
    directory = make_page(PartnerDirectoryPage)

    async with async_step("Setup: open the SA Partner Directory"):
        await shell.open(SECTION)
        await shell.wait_ready(SECTION)  # marker "Partners" in <main>

    async with async_step("[1/3] The directory loads with its breadcrumb + summary cards"):
        assert await directory.breadcrumb().is_visible(), (
            "the 'Directory' breadcrumb must render on the Partners page"
        )
        for label in PartnerDirectoryPage.SUMMARY_CARDS:
            assert await directory.summary_card(label).is_visible(), (
                f"summary card '{label}' must be visible on the Partner Directory"
            )
        logger.info(
            "CHECK directory + summary → OK ({})", ", ".join(PartnerDirectoryPage.SUMMARY_CARDS)
        )

    async with async_step("[2/3] The filter controls + Onboard action are visible"):
        for name in PartnerDirectoryPage.FILTERS:
            assert await directory.filter_control(name).is_visible(), (
                f"filter control '{name}' must be visible on the Partner Directory"
            )
        assert await directory.action_button("Onboard Partner").is_visible(), (
            "the 'Onboard Partner' action must be visible"
        )
        logger.info(
            "CHECK filters → OK ({} + Onboard Partner)", ", ".join(PartnerDirectoryPage.FILTERS)
        )

    async with async_step(
        "[3/3] The partner table renders (full column header; rows when present)"
    ):
        headers = await directory.column_headers()
        missing = [h for h in PartnerDirectoryPage.TABLE_HEADERS if h not in headers]
        assert not missing, f"partner table is missing column headers: {missing} (got {headers})"
        rows = await directory.data_row_count()
        if rows == 0:
            assert await directory.empty_state().is_visible(), (
                "with no partners the table must show its 'No Data Found' empty state"
            )
            logger.info("CHECK table → OK (headers present; empty-state shown, 0 rows)")
        else:
            logger.info("CHECK table → OK (headers present; {} partner row(s) shown)", rows)

    logger.info("RESULT: SA Partner Directory loads with filters + partner table structure")
