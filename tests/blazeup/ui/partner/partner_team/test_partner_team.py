"""Partner Portal — Directory / Team (UI).

PARTNER_UI_PARTNER_TEAM_001 — invite a team member: the Invite User dialog captures
                              email + name + role, sends the invite, and the new
                              member appears in the Directory with its role.

NO CLEANUP POSSIBLE (not an oversight): the invite creates a partner user inside the
SHARED partner org, and sa-partners-api exposes no delete for partner users — only
``POST /v1/sa/partner-users``, ``.../reset-password``, ``.../unlock`` and a DELETE for
*certifications* (verified against docs/api-snapshots/blazeup/sa-partners-api.endpoints.json).
Deleting the parent partner is not an option either; it is the real shared account the
whole partner-portal suite logs in with. So each run leaves one invited member behind —
the email is logged below so it can be found. Revisit when BE adds a remove/revoke
endpoint for partner users.
"""

import pytest
from loguru import logger

from pages.blazeup.partner.directory_page import PartnerDirectoryPage
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.data_factory import unique_email
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_partner_team_001(make_partner_page):
    """PARTNER_UI_PARTNER_TEAM_001: invite a partner team member (invitation sent with role).

    Opens the partner Directory, invites a new team member through the Invite User
    dialog (unique email + name, keeping the default Role), sends the invite, and
    confirms the new member appears in the member table with a role. Uses a globally
    unique email so re-runs never collide with an existing member.
    """
    shell = make_partner_page(PartnerShellPage)
    directory = make_partner_page(PartnerDirectoryPage)
    email = unique_email()

    async with async_step("Setup: open the partner Directory"):
        await shell.open("directory")
        await shell.wait_ready("directory")  # marker "Directory" in <main>

    async with async_step("[1/4] The member table + Invite User action render"):
        headers = await directory.column_headers()
        missing = [h for h in PartnerDirectoryPage.TABLE_HEADERS if h not in headers]
        assert not missing, f"member table is missing headers: {missing} (got {headers})"
        assert await directory.invite_button().is_visible(), "the 'Invite User' action must render"
        before = await directory.member_count()
        logger.info("CHECK directory → OK (headers {}, {} member(s))", headers, before)

    async with async_step("[2/4] The Invite dialog exposes email + name + a role selector"):
        await directory.open_invite()
        await directory.fill_invite(email, "QA", "AutoInvite")
        role = await directory.current_role()
        assert role, "the invite dialog must expose a Role selector"
        logger.info("CHECK invite form → OK (role={!r}, email={})", role, email)

    async with async_step(
        "[3/4] Send the invite → 'User invited' confirmation (one-time password)"
    ):
        await directory.send_invite()
        # Success = the "User invited" credential dialog (shows the one-time temp password).
        await directory.invited_confirmation().wait_for(state="visible", timeout=15_000)
        logger.info("CHECK send → OK ('User invited' confirmation shown for {})", email)
        await directory.close_credential()

    async with async_step("[4/4] The invited member appears in the Directory with its role"):
        row = directory.member_row(email)
        await row.wait_for(state="visible", timeout=15_000)
        row_text = " ".join((await row.inner_text()).split())
        assert email in row_text, f"the invited member row must show the email, got {row_text!r}"
        assert role.split()[0] in row_text or role in row_text, (
            f"the invited member row must show the role {role!r}, got {row_text!r}"
        )
        logger.info("CHECK member row → OK ({})", row_text)

    logger.warning(
        "CLEANUP LEAK (known, no endpoint): invited member {} stays in the shared partner "
        "org — sa-partners-api has no delete for partner users. See the module docstring.",
        email,
    )
    logger.info("RESULT: team member invited with role and now visible in the Directory")
