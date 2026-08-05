"""Partner Portal Directory page object (/directory) — team members + invite.

The partner's own team management: reads the member table and drives the "Invite
User" dialog. Navigation + shell readiness come from ``PartnerShellPage``
(open("directory") + wait_ready("directory")).
"""

from loguru import logger
from playwright.async_api import Locator

from locators.blazeup.partner.directory_locators import PartnerDirectoryLocators as L
from pages.base_page import BasePage


class PartnerDirectoryPage(BasePage):
    """Reads the partner team-member table and drives the Invite User dialog."""

    TABLE_HEADERS = L.TABLE_HEADERS

    def _main(self) -> Locator:
        return self.page.locator("main")

    def dialog(self) -> Locator:
        return self.page.locator(L.DIALOG).first

    def invite_button(self) -> Locator:
        return self._main().get_by_role("button", name=L.INVITE_BUTTON, exact=False).first

    async def open_invite(self, timeout: int = 15_000) -> None:
        """Click 'Invite User' and wait for the dialog."""
        logger.log("STEP", "Open Invite User dialog")
        await self.invite_button().click()
        await self.dialog().wait_for(state="visible", timeout=timeout)

    async def fill_invite(self, email: str, first: str, last: str) -> None:
        """Fill the invite form's required fields (email + first/last name)."""
        dlg = self.dialog()
        await dlg.locator(L.EMAIL_INPUT).fill(email)
        await dlg.locator(L.FIRST_NAME_INPUT).fill(first)
        await dlg.locator(L.LAST_NAME_INPUT).fill(last)

    async def current_role(self) -> str:
        """Return the Role control's current selection (default 'Viewer'), best-effort."""
        combo = self.dialog().get_by_role("combobox").first
        if await combo.count():
            txt = (await combo.inner_text()).strip()
            return " ".join(txt.split())
        return ""

    async def send_invite(self) -> None:
        """Submit the invite (Send Invite)."""
        logger.log("STEP", "Click Send Invite")
        await self.dialog().get_by_role("button", name=L.SEND_BUTTON, exact=False).first.click()

    async def send_disabled(self) -> bool:
        """True when Send Invite is disabled (required fields not satisfied)."""
        btn = self.dialog().get_by_role("button", name=L.SEND_BUTTON, exact=False).first
        return await btn.is_disabled()

    def invited_confirmation(self) -> Locator:
        """The 'User invited' success dialog (shows the one-time temporary password)."""
        return self.page.get_by_text("User invited", exact=False).first

    async def close_credential(self) -> None:
        """Dismiss the credential ('User invited') dialog via its Done button."""
        logger.log("STEP", "Close credential dialog (Done)")
        await self.page.get_by_role("button", name="Done", exact=True).first.click()

    async def column_headers(self) -> list[str]:
        """Return the member-table column header texts."""
        ths = self._main().locator("th")
        n = await ths.count()
        return [(await ths.nth(i).inner_text()).strip() for i in range(n)]

    def member_row(self, email: str) -> Locator:
        """Locator for a member table row containing *email* (proves the invite persisted)."""
        return self._main().locator("tbody tr").filter(has_text=email).first

    async def member_count(self) -> int:
        """Return the number of member rows currently in the table."""
        return await self._main().locator("tbody tr").count()
