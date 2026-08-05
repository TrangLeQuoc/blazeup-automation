"""Locators for the Partner Portal Directory page (/directory).

The partner's own team-members page: a member table (MEMBER / ROLE / STATUS / LAST
LOGIN) + an "Invite User" action that opens a dialog (Email / First / Last / Role /
optional temporary password → Send Invite). Verified against live staging DOM
(stgpartners, 2026-07-29, channel-partner user).
"""


class PartnerDirectoryLocators:
    """Partner Directory: member table + Invite User dialog."""

    READY_MARKER = "Directory"

    INVITE_BUTTON = "Invite User"

    # Invite dialog fields (verified names).
    DIALOG = "[role=dialog]"
    EMAIL_INPUT = "input[name='invite-email']"
    FIRST_NAME_INPUT = "input[name='given-name']"
    LAST_NAME_INPUT = "input[name='family-name']"
    PASSWORD_INPUT = "input[name='invite-password']"
    SEND_BUTTON = "Send Invite"

    # Member table.
    TABLE_HEADERS = ("MEMBER", "ROLE", "STATUS", "LAST LOGIN")
