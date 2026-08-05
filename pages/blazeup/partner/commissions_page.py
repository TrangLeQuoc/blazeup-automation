"""Partner Portal Commissions page object (/commissions).

Content reads for the commissions page. Navigation + shell readiness come from
``PartnerShellPage`` (open("commissions") + wait_ready("commissions")); this object
reads the page-specific widgets (summary cards, ledger tabs).
"""

import contextlib
import re

from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from locators.blazeup.partner.commissions_locators import CommissionsLocators
from pages.base_page import BasePage


class CommissionsPage(BasePage):
    """Reads the Commissions summary cards, ledger tabs, and table state."""

    SUMMARY_CARDS = CommissionsLocators.SUMMARY_CARDS
    TABS = CommissionsLocators.TABS

    async def wait_list_settled(self, timeout: int = 15_000) -> None:
        """Wait until the commissions data has settled (fetch done, spinner gone)."""
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.locator(CommissionsLocators.LIST_SPINNER).first.wait_for(
                state="hidden", timeout=5_000
            )

    def summary_card(self, label: str) -> Locator:
        """Locator for a summary stat card by its label (e.g. 'Total Earned')."""
        return self.page.locator("main").get_by_text(label, exact=False).first

    async def summary_amount(self, label: str) -> str:
        """Return the $ amount shown for a summary card label (e.g. '$0'), or ''.

        The cards render as "<Label> $<amount>" in <main> (e.g. "Total Earned $0"),
        so read the normalized main text and pull the $value right after the label.
        """
        text = " ".join((await self.page.locator("main").inner_text()).split())
        m = re.search(re.escape(label) + r"\s*(\$[\d,]+(?:\.\d+)?)", text)
        return m.group(1) if m else ""

    def tab(self, name: str) -> Locator:
        """Locator for a ledger status tab (rendered as a <button>), e.g. 'Paid'.

        exact=True so 'Paid' doesn't also match the 'Paid YTD' summary card, etc.
        """
        return self.page.locator("main").get_by_role("button", name=name, exact=True).first
