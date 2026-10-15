"""SA Dashboard Partner Directory page object (/partners).

Content reads for the SA-side partner-management directory. Navigation + shell
readiness come from ``ShellPage`` (open("partners") + wait_ready("partners")); this
object reads the page-specific widgets (summary cards, filters, partner table).
"""

import re

from playwright.async_api import Locator

from locators.blazeup.admin.partner_directory_locators import PartnerDirectoryLocators
from pages.base_page import BasePage


class PartnerDirectoryPage(BasePage):
    """Reads the SA Partner Directory summary cards, filters, and partner table."""

    SUMMARY_CARDS = PartnerDirectoryLocators.SUMMARY_CARDS
    FILTERS = PartnerDirectoryLocators.FILTERS
    TABLE_HEADERS = PartnerDirectoryLocators.TABLE_HEADERS

    def _main(self) -> Locator:
        return self.page.locator("main")

    def breadcrumb(self) -> Locator:
        """Locator for the 'Directory' breadcrumb/tab label."""
        return self._main().get_by_text(PartnerDirectoryLocators.BREADCRUMB, exact=False).first

    def summary_card(self, label: str) -> Locator:
        """Locator for a summary stat card by its label (e.g. 'Total Partners')."""
        return self._main().get_by_text(label, exact=False).first

    def filter_control(self, name: str) -> Locator:
        """Locator for a filter dropdown, rendered as a <button> (e.g. 'Status').

        A filter with active selections prefixes their count to its label — the Directory
        opens with Status = Active, so the button reads "1 Status". An exact "Status" match
        missed it (TC 12060503, 2026-10-13/14). The pattern allows that count and nothing
        else, so it still cannot match an unrelated button that merely contains the word.
        """
        label = re.compile(rf"^\s*(?:\d+\s+)?{re.escape(name)}\s*$", re.IGNORECASE)
        return self._main().get_by_role("button", name=label).first

    def action_button(self, name: str) -> Locator:
        """Locator for a primary action button (e.g. 'Onboard Partner')."""
        return self._main().get_by_role("button", name=name, exact=False).first

    async def column_headers(self) -> list[str]:
        """Return the partner-table column header texts (upper-cased, in order)."""
        ths = self._main().locator("th")
        n = await ths.count()
        return [(await ths.nth(i).inner_text()).strip() for i in range(n)]

    async def data_row_count(self) -> int:
        """Return the number of partner data rows in the table body (0 when empty)."""
        return await self._main().locator("tbody tr").count()

    def empty_state(self) -> Locator:
        """Locator for the 'No Data Found' empty-state (shown when there are no partners)."""
        return (
            self._main().get_by_text(PartnerDirectoryLocators.EMPTY_STATE_TEXT, exact=False).first
        )
