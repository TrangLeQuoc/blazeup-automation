"""Partner Portal Deals page object (/deals — "Deal Pipeline").

Content actions/reads for the pipeline page. Navigation + shell readiness come from
``PartnerShellPage`` (open("deals") + wait_ready("deals")); this object reads the
page-specific widgets (stage tabs + counts, controls), mirroring how the admin side
pairs ShellPage with DashboardPage.
"""

import asyncio
import contextlib
import re

from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from locators.blazeup.partner.deals_locators import DealsLocators
from pages.base_page import BasePage


class DealsPage(BasePage):
    """Reads the Deal Pipeline stage tabs, counts, and primary controls."""

    STAGES = DealsLocators.STAGE_BUTTONS

    async def wait_list_settled(self, timeout: int = 15_000) -> None:
        """Wait until the deals-list data has settled (fetch done, loading spinner gone).

        The page title + stage tabs render from the dashboard fetch, but the deals
        table keeps a loading spinner until its OWN fetch returns. Waiting for network
        idle + the spinner to disappear gives a stable page (final counts, clean
        screenshot/video) before assertions — otherwise the page reads mid-load.
        """
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        # If the spinner is present, wait for it to clear; hidden/absent both pass.
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.locator(DealsLocators.LIST_SPINNER).first.wait_for(
                state="hidden", timeout=5_000
            )

    def register_button(self) -> Locator:
        """The 'Register a deal' CTA."""
        return self.page.locator(DealsLocators.REGISTER_BUTTON).first

    def summary(self) -> Locator:
        """The pipeline summary line ('N deals in your pipeline'), scoped to <main>."""
        return self.page.locator("main").get_by_text(DealsLocators.SUMMARY_TEXT).first

    # ── Deals table: list rows, columns, detail, filter, pagination ─────────────
    # Stage controls are BUTTONS now ("<Stage> <count>"), e.g. "Won 8" — not role=tab.

    def stage_button(self, stage: str) -> Locator:
        """A pipeline stage control button, matched by its 'Stage <count>' label."""
        return self.page.get_by_role(
            "button", name=re.compile(rf"^\s*{re.escape(stage)}\s+\d", re.I)
        ).first

    async def stage_button_count(self, stage: str) -> int | None:
        """The deal count shown on a stage button (e.g. 'Won 8' → 8), or None."""
        text = await self.stage_button(stage).inner_text()
        m = re.search(r"(\d[\d,]*)", text)
        return int(m.group(1).replace(",", "")) if m else None

    async def click_stage(self, stage: str) -> None:
        """Switch the list to a stage, then wait for the table to settle."""
        await self.click_on(self.stage_button(stage), f"Stage: {stage}")
        await self.wait_list_settled()

    def table(self) -> Locator:
        return self.page.locator(DealsLocators.TABLE).first

    def rows(self) -> Locator:
        """All data rows currently rendered in the deals table body."""
        return self.page.locator(DealsLocators.ROWS)

    def data_rows(self) -> Locator:
        """Only real deal rows (carry a 'D#...' Deal ID), excluding the empty-state row.

        An empty stage still renders one ``<tr>`` holding the 'No deals found' message,
        so ``rows()`` would count 1; this filters to rows that actually show a deal.
        """
        return self.rows().filter(has_text=re.compile(r"D#"))

    async def row_count(self) -> int:
        return await self.rows().count()

    async def data_row_count(self) -> int:
        return await self.data_rows().count()

    async def wait_empty_state(self, timeout: int = 8_000) -> bool:
        """Poll until the 'No deals found' empty-state is visible (True) or times out."""
        end = asyncio.get_event_loop().time() + timeout / 1000
        while True:
            with contextlib.suppress(PlaywrightTimeoutError):
                if await self.empty_state().is_visible():
                    return True
            if asyncio.get_event_loop().time() >= end:
                return False
            await self.page.wait_for_timeout(250)

    async def wait_row_count(self, expected: int, timeout: int = 8_000) -> bool:
        """Poll until the rendered row count equals ``expected`` (True) or times out.

        Stage switching and pagination re-render the table CLIENT-SIDE with no network
        spinner, so ``wait_list_settled`` can return before the new rows paint. Polling
        the row count is the reliable settle signal. Counts DEAL rows only — the
        'No deals found' row would otherwise read as one deal.

        Not proof on its own that a stage switch applied: if the previous view already
        showed ``expected`` rows this returns at once. Use ``wait_stage_applied`` for that.
        """
        end = asyncio.get_event_loop().time() + timeout / 1000
        while True:
            if await self.data_row_count() == expected:
                return True
            if asyncio.get_event_loop().time() >= end:
                return False
            await self.page.wait_for_timeout(250)

    async def wait_stage_applied(self, stage: str, expected: int, timeout: int = 8_000) -> bool:
        """Poll until the table shows exactly ``expected`` deal rows, ALL of ``stage``.

        A count match alone can come from the PREVIOUS view (the switch re-renders
        client-side with no spinner), so the statuses are checked too: only the new
        stage's rows can satisfy both at once.
        """
        want = stage.lower()
        end = asyncio.get_event_loop().time() + timeout / 1000
        while True:
            if await self.data_row_count() == expected:
                statuses = [(await self.row_status(i)).lower() for i in range(expected)]
                if all(want in st for st in statuses):
                    return True
            if asyncio.get_event_loop().time() >= end:
                return False
            await self.page.wait_for_timeout(250)

    async def wait_first_deal_changed(self, previous_id: str, timeout: int = 8_000) -> bool:
        """Poll until the first row's Deal ID differs from ``previous_id`` (after paging)."""
        end = asyncio.get_event_loop().time() + timeout / 1000
        while True:
            if (
                await self.data_row_count() > 0
                and (await self.row_cell(0, "DEAL ID")) != previous_id
            ):
                return True
            if asyncio.get_event_loop().time() >= end:
                return False
            await self.page.wait_for_timeout(250)

    async def column_headers(self) -> list[str]:
        """Visible column-header labels, left→right (trailing empty actions dropped)."""
        heads = self.table().get_by_role("columnheader")
        n = await heads.count()
        out: list[str] = []
        for i in range(n):
            txt = (await heads.nth(i).inner_text()).strip()
            if txt:
                out.append(txt)
        return out

    def _col_index(self, column: str) -> int:
        """0-based cell index for a known column name (from the live header order)."""
        return DealsLocators.COLUMNS.index(column)

    async def row_cell(self, row_index: int, column: str) -> str:
        """Text of one cell, addressed by row index + column name (e.g. 'STATUS')."""
        cells = self.rows().nth(row_index).get_by_role("cell")
        return (await cells.nth(self._col_index(column)).inner_text()).strip()

    async def row_status(self, row_index: int) -> str:
        return await self.row_cell(row_index, "STATUS")

    async def open_detail(self, row_index: int = 0, timeout: int = 10_000) -> None:
        """Click a deal row and wait for the Deal Detail drawer to open."""
        await self.click_on(self.rows().nth(row_index), f"Deal row #{row_index}")
        await self.detail_heading().wait_for(state="visible", timeout=timeout)

    def detail_heading(self) -> Locator:
        """The Deal Detail drawer's own heading (distinguishes it from the filter popover)."""
        return self.page.get_by_role("heading", name=DealsLocators.DETAIL_HEADING).first

    def detail_drawer(self) -> Locator:
        """The Deal Detail drawer dialog, scoped by its own 'Deal Detail' heading."""
        return self.page.get_by_role("dialog").filter(has=self.detail_heading())

    def detail_section(self, name: str) -> Locator:
        """A section heading inside the detail drawer, e.g. 'DEAL INFO' / 'COMPANY INFO'."""
        return self.page.get_by_text(name, exact=False).first

    def empty_state(self) -> Locator:
        """The 'No deals found' empty-state, scoped to <main>."""
        return self.page.locator("main").get_by_text(DealsLocators.EMPTY_STATE_TEXT).first

    async def open_filter(self, timeout: int = 8_000) -> Locator:
        """Open the Filter popover (radix) and return its container."""
        await self.click_on(self.page.locator(DealsLocators.FILTER_BUTTON).first, "Filter")
        popover = self.page.locator("[data-radix-popper-content-wrapper]").first
        await popover.wait_for(state="visible", timeout=timeout)
        return popover

    def page_input(self) -> Locator:
        """The numeric 'go to page' input in the pagination footer."""
        return self.page.locator(DealsLocators.PAGE_INPUT).first

    async def go_to_page(self, n: int) -> None:
        """Jump to a page number via the pagination input, then wait for settle."""
        inp = self.page_input()
        await self.fill_in(inp, str(n), "Go to page")
        await inp.press("Enter")
        await self.wait_list_settled()
