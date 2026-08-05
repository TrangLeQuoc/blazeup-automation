"""SA Deal Approval Queue page object (/partners/deals).

Content reads for the SA-side deal-approval workspace (PRD §5.2). Navigates directly
to /partners/deals (a sub-route of the Partners area, not a top sidebar item), waits
for the queue shell to render (a stable filter button — the status tabs are custom
<span> chips), and reads the filters / deals table. Also exposes a check for the
"Server Error / Invalid id" backend-defect banner so a test can assert the queue
CONTENT loaded (not just its shell).
"""

import contextlib
import time

from loguru import logger
from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from locators.blazeup.admin.deal_approval_queue_locators import DealApprovalQueueLocators as L
from locators.blazeup.admin.shell_locators import ShellLocators
from pages.base_page import BasePage


class DealApprovalQueuePage(BasePage):
    """Reads the SA Deal Approval Queue filters, table, and error state."""

    FILTERS = L.FILTERS
    TABLE_HEADERS = L.TABLE_HEADERS

    def _main(self) -> Locator:
        return self.page.locator("main")

    async def open(self) -> None:
        """Navigate directly to the SA Deal Approval Queue (/partners/deals)."""
        await self.goto(L.ROUTE)

    async def wait_ready(self, timeout: int = 90_000, poll_ms: int = 500) -> None:
        """Wait until the queue shell rendered: the 'Deal Type' filter is visible.

        Keys off a STABLE filter button (not the redesigned status tabs, which are
        custom <span> chips with no reliable role/name). Fast-fails on the MFE error
        panel (broken deploy). The deal-list fetch may still error separately.
        """
        logger.log("STEP", "Wait ready [deal-queue] = '{}' filter in <main>", L.READY_FILTER)
        marker = self.filter_control(L.READY_FILTER)
        error_loc = self.page.locator(ShellLocators.ERROR_PANEL).first
        deadline = time.perf_counter() + timeout / 1000
        while True:
            if await error_loc.is_visible():
                raise AssertionError(
                    "SA Deal Approval Queue failed to load: the MFE error panel "
                    "('Something went wrong') is visible. Deploy/MFE issue, not a test bug."
                )
            if await marker.is_visible():
                return
            if time.perf_counter() >= deadline:
                raise AssertionError(
                    "SA Deal Approval Queue did not render within "
                    f"{timeout} ms: the '{L.READY_FILTER}' filter never became visible in <main>."
                )
            await self.page.wait_for_timeout(poll_ms)

    def filter_control(self, name: str) -> Locator:
        """Locator for a filter control, rendered as a <button> (e.g. 'Deal Type')."""
        return self._main().get_by_role("button", name=name, exact=False).first

    async def wait_deal_list_settled(self, timeout: int = 20_000, settle_ms: int = 1_000) -> None:
        """Wait until the async deal-list fetch RESOLVED before asserting on it.

        ``wait_ready`` only proves the shell mounted; the deal-list is fetched
        asynchronously and its result (rows, empty-state, or the 'Server Error /
        Invalid id' banner) paints a moment later. Checking for the error right
        after the shell races that pending request and can read a FALSE 'no error'
        (the banner then appears in the video, on a "passing" run). Wait for network
        idle + a short paint buffer so the deal-list's final state is on screen.
        """
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        await self.page.wait_for_timeout(settle_ms)  # let the rows/empty/error banner paint

    async def column_headers(self) -> list[str]:
        """Return the deals-table column header texts (in order)."""
        ths = self._main().locator("th")
        n = await ths.count()
        return [(await ths.nth(i).inner_text()).strip() for i in range(n)]

    async def data_row_count(self) -> int:
        """Return the number of deal rows in the current tab's table body."""
        return await self._main().locator("tbody tr").count()

    async def server_error_text(self) -> str:
        """Return the visible backend-defect banner text in <main>, or ''.

        Looks for the "Server Error" / "Invalid id" phrases in <main>. A non-empty
        return means the deal-list fetch failed — the queue shell rendered but its
        CONTENT is broken (a backend defect, not a test bug).
        """
        text = " ".join((await self._main().inner_text()).split())
        for phrase in L.SERVER_ERROR_TEXTS:
            if phrase.lower() in text.lower():
                idx = text.lower().find(phrase.lower())
                return text[idx : idx + 60]
        return ""
