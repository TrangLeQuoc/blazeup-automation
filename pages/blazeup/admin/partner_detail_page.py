"""SA-side Partner Detail page object (stgsa /partners/<id>).

Onboards a throwaway partner (self-seeding fixture — the Directory list is unreliable
on staging), opens its detail, and reads the tabs / sections / partner-actions menu.
"""

import contextlib
import time

from loguru import logger
from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from locators.blazeup.admin.partner_detail_locators import PartnerDetailLocators as L
from locators.blazeup.admin.shell_locators import ShellLocators
from pages.base_page import BasePage


class PartnerDetailPage(BasePage):
    """Actions + reads for the SA Partner Detail page (and the Onboard flow)."""

    TABS = L.TABS
    SECTIONS = L.SECTIONS

    def _main(self) -> Locator:
        return self.page.locator("main")

    async def _poll_main(self, minlen: int = 40, secs: int = 60) -> str:
        """Poll <main> until it has real content (staging cold-load safe)."""
        main = self._main()
        deadline = time.perf_counter() + secs
        while time.perf_counter() < deadline:
            if await main.count():
                t = " ".join((await main.inner_text()).split())
                if len(t) >= minlen and "Something went wrong" not in t:
                    return t
            await self.page.wait_for_timeout(1500)
        return " ".join((await main.inner_text()).split()) if await main.count() else ""

    async def open_directory(self) -> None:
        await self.goto("/partners")
        await self._poll_main(40, 60)

    async def onboard_partner(self, company: str, email: str, ready_timeout: int = 45_000) -> None:
        """Create a new partner via 'Onboard Partner' (it starts in Pending status).

        Waits for the 'Onboard Partner' CTA to be visible/actionable before clicking
        — the Directory shell can render before its action bar hydrates, so a bare
        click races the hydration and times out under slow cold-loads (the partner-
        detail setup flaky). ``ready_timeout`` is generous to absorb staging cold-loads.
        """
        main = self._main()
        logger.log("STEP", "Onboard partner [{}]", company)
        cta = main.get_by_role("button", name=L.ONBOARD_BUTTON, exact=False).first
        await cta.wait_for(state="visible", timeout=ready_timeout)
        await cta.click()
        # Wait for the FIELD, not for a guessed number of milliseconds: the form mounts
        # either in a dialog or inline, and on a cold staging load that takes far longer
        # than any fixed sleep we would be willing to pay on a fast one.
        await self.page.locator(L.ONBOARD_COMPANY).first.wait_for(
            state="visible", timeout=ready_timeout
        )
        dlg = self.page.locator("[role=dialog]").first
        scope = dlg if await dlg.count() else main
        await scope.locator(L.ONBOARD_COMPANY).fill(company)
        await scope.locator(L.ONBOARD_EMAIL).fill(email)
        await scope.get_by_role("button", name=L.ONBOARD_BUTTON, exact=True).first.click()
        await self._wait_onboard_settled()

    async def _wait_onboard_settled(self, timeout: int = 30_000) -> None:
        """Wait until the onboard request finished, however it finished.

        Two equally valid end states: the success toast shows, or the form closes.
        Polling for either is what makes this adapt — a fixed sleep is simultaneously
        too short on a slow staging write and pure waste on a fast one.
        """
        toast = self.page.get_by_text(L.ONBOARD_SUCCESS, exact=False).first
        field = self.page.locator(L.ONBOARD_COMPANY).first
        deadline = time.perf_counter() + timeout / 1000
        while time.perf_counter() < deadline:
            if await toast.count() and await toast.is_visible():
                return
            if not await field.count() or not await field.is_visible():
                return
            await self.page.wait_for_timeout(250)
        raise AssertionError(
            f"Onboard Partner did not settle within {timeout} ms "
            "(no success toast and the form is still open)."
        )

    async def open_partner(self, company: str, timeout: int = 60_000) -> None:
        """Open the just-onboarded partner's detail: back to the Directory, find its row, click it."""
        # After onboarding, the page is on the onboard form — go back to the Directory
        # and wait for the newly-created partner row to appear, then click it.
        await self.goto("/partners")
        await self._poll_main(40, 60)
        row = self._main().locator("tbody tr").filter(has_text=company).first
        await row.wait_for(state="visible", timeout=timeout)
        await row.click()
        await self.wait_detail_ready(timeout=timeout)

    async def wait_detail_ready(self, timeout: int = 60_000) -> None:
        """Wait until the detail rendered: the 'Members' tab is visible in <main>."""
        logger.log("STEP", "Wait partner-detail ready ('Members' tab)")
        # Tabs are Radix <button role="tab">, so match by the "tab" role (not "button").
        tab = self._main().get_by_role("tab", name="Members", exact=True).first
        error_loc = self.page.locator(ShellLocators.ERROR_PANEL).first
        deadline = time.perf_counter() + timeout / 1000
        while True:
            if await error_loc.is_visible():
                raise AssertionError(
                    "SA Partner Detail failed to load: the MFE error panel is visible."
                )
            if await tab.is_visible():
                return
            if time.perf_counter() >= deadline:
                raise AssertionError(
                    f"SA Partner Detail did not render within {timeout} ms "
                    "(the 'Members' tab never became visible)."
                )
            await self.page.wait_for_timeout(500)

    def tab(self, name: str) -> Locator:
        return self._main().get_by_role("tab", name=name, exact=True).first

    def section(self, name: str) -> Locator:
        return self._main().get_by_text(name, exact=False).first

    def actions_button(self) -> Locator:
        return self.page.get_by_role("button", name=L.ACTIONS_BUTTON, exact=False).first

    async def detail_text(self) -> str:
        return " ".join((await self._main().inner_text()).split())

    # ── Partner-actions workflow (Approve → Deactivate) ───────────────────────
    async def open_actions_menu(self, timeout: int = 15_000) -> None:
        """Open the 'Partner actions' kebab menu (Radix dropdown)."""
        await self.actions_button().click()
        # Radix portals the menu in asynchronously — wait for a real menu item to exist
        # instead of sleeping and hoping. The caller clicks one immediately after.
        await self.page.get_by_role("menuitem").first.wait_for(state="visible", timeout=timeout)

    def menu_item(self, name: str) -> Locator:
        return self.page.get_by_role("menuitem", name=name, exact=False).first

    async def approve_partner(self, timeout: int = 30_000) -> None:
        """Approve a Pending partner (one-click menu item → status becomes Active)."""
        logger.log("STEP", "Actions → Approve Partner")
        await self.open_actions_menu()
        await self.menu_item(L.ACTION_APPROVE).click()
        # Poll the header until the status flips to Active.
        deadline = time.perf_counter() + timeout / 1000
        while time.perf_counter() < deadline:
            if "Active" in await self.detail_text():
                return
            await self.page.wait_for_timeout(500)
        raise AssertionError("partner did not reach 'Active' after Approve within the timeout")

    async def deactivate_partner(self) -> str:
        """Confirm the Deactivate (suspend) action; return the resulting banner text.

        Opens Actions → Deactivate, then confirms the 'Deactivate Partner' dialog.
        Returns the <main> text after the request settles so the caller can assert
        on the success/error banner (the confirm dialog collects no 'reason').
        """
        logger.log("STEP", "Actions → Deactivate (confirm)")
        await self.open_actions_menu()
        await self.menu_item(L.ACTION_DEACTIVATE).click()
        # (No sleep here: the dialog wait below IS the wait for the menu item to act.)
        dlg = self.page.get_by_role("dialog").filter(has_text="Deactivate Partner").first
        await dlg.wait_for(state="visible", timeout=10_000)
        await dlg.get_by_role("button", name=L.ACTION_DEACTIVATE, exact=True).first.click()
        await self._wait_deactivate_outcome(dlg)
        return await self.detail_text()

    async def _wait_deactivate_outcome(self, dialog, timeout: int = 20_000) -> None:
        """Return as soon as the request resolved — EITHER way. Never raise.

        Two outcomes, and both have to end the wait:
          * accepted → the confirm dialog closes;
          * rejected → an error banner appears and the dialog STAYS open.

        Waiting only for the close is wrong on both counts: on the rejection path it
        burns the whole timeout, and by the time it gives up the error toast has
        auto-hidden — so the caller reads a page with no error on it and asserts
        something vaguer. That toast IS the evidence PARTNER_UI_SA_PARTNER_MODULE_015
        exists to capture (a be_gap TC whose value is the BE's rejection message).

        Tolerant on timeout for the same reason: the caller owns the assertion.
        """
        banner = self._main().get_by_text(L.ACTION_FAILED_BANNER, exact=False).first
        deadline = time.perf_counter() + timeout / 1000
        while time.perf_counter() < deadline:
            if await banner.count() and await banner.is_visible():
                return
            if not await dialog.count() or not await dialog.is_visible():
                return
            await self.page.wait_for_timeout(250)
        logger.warning("Deactivate produced neither a closed dialog nor an error banner")

    # ── Members tab (Portal Users) ────────────────────────────────────────────
    async def open_members(self, timeout: int = 20_000) -> None:
        """Switch to the Members tab and wait for the Portal Users list to render."""
        await self.tab("Members").click()
        await (
            self._main()
            .get_by_text(L.MEMBERS_HEADING, exact=False)
            .first.wait_for(state="visible", timeout=timeout)
        )

    async def add_portal_user(self, first: str, last: str, email: str, password: str) -> str:
        """Add a portal user via the Members tab; return the resulting <main> text.

        Opens the Add-User form ("Add User", or "Add First User" when the list is
        empty), fills first/last/email/password, submits, and dismisses the success
        panel via "Done" so the caller can assert the new row in the table. The
        password is filled directly (never logged).
        """
        logger.log("STEP", "Members → Add portal user [{}]", email)
        add = self.page.get_by_role("button", name=L.MEMBERS_ADD_USER, exact=True).first
        if not (await add.count() and await add.is_visible()):
            add = self.page.get_by_role("button", name=L.MEMBERS_ADD_FIRST_USER, exact=True).first
        await add.click()
        form = self.page.locator("form").filter(has_text=L.MEMBER_CREATE_BUTTON).first
        # Wait for the form itself; on a slow render the old 1s sleep let the fills
        # race the mount and fail on a field that did not exist yet.
        await form.wait_for(state="visible", timeout=20_000)
        await form.locator(L.MEMBER_FIRST_NAME).fill(first)
        await form.locator(L.MEMBER_LAST_NAME).fill(last)
        await form.locator(L.MEMBER_EMAIL).fill(email)
        logger.log("STEP", "Fill  [member password] = ***")
        await form.locator(L.MEMBER_PASSWORD).fill(password)
        await form.get_by_role("button", name=L.MEMBER_CREATE_BUTTON, exact=True).click()
        done = self.page.get_by_role("button", name=L.MEMBER_DONE_BUTTON, exact=True).first
        await self._wait_member_created(done)
        # Read AFTER the outcome is on screen — the caller asserts on this text, so a
        # premature read used to make a slow-but-successful create look like a failure.
        text = await self.detail_text()
        if await done.count() and await done.is_visible():
            await done.click()
            with contextlib.suppress(PlaywrightTimeoutError):
                await done.wait_for(state="hidden", timeout=15_000)
        # Dismissing the panel is NOT the same thing as the table having refreshed:
        # the caller asserts on the new row, so wait for that row — the actual end
        # state. (Waiting only for "Done" to detach made this flaky: the panel closes
        # before the list re-renders, and the assertion then ran against a stale table.)
        await self._wait_member_row(email)
        return text

    async def _wait_member_row(self, email: str, timeout: int = 20_000) -> None:
        """Wait for the newly added user's row to appear. Tolerant: the caller asserts."""
        row = self.member_row(email)
        deadline = time.perf_counter() + timeout / 1000
        while time.perf_counter() < deadline:
            if await row.count() and await row.is_visible():
                return
            await self.page.wait_for_timeout(250)
        logger.warning("Portal-user row for {} not listed after {} ms", email, timeout)

    async def _wait_member_created(self, done_button, timeout: int = 25_000) -> None:
        """Wait for the create-user request to land: success toast or the Done panel.

        Tolerant on timeout for the same reason as :meth:`_wait_dialog_dismissed` — the
        caller asserts on the resulting text and its message is the useful evidence.
        """
        toast = self.page.get_by_text(L.MEMBER_CREATED_TOAST, exact=False).first
        deadline = time.perf_counter() + timeout / 1000
        while time.perf_counter() < deadline:
            if await toast.count() and await toast.is_visible():
                return
            if await done_button.count() and await done_button.is_visible():
                return
            await self.page.wait_for_timeout(250)
        logger.warning("Create-portal-user did not confirm within {} ms — reading anyway", timeout)

    def member_row(self, email: str) -> Locator:
        return self._main().locator("tbody tr").filter(has_text=email).first
