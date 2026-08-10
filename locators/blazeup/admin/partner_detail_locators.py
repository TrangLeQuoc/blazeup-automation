"""Locators for the SA-side Partner Detail page (stgsa /partners/<id>).

Verified against the live staging DOM (2026-07-31, super-admin). Opened from the
Partners Directory (or created via "Onboard Partner"). The detail shows a header
with the partner name + status + a "Partner actions" menu, tabbed content
(Overview / Deals / Commission / Members), and Overview sections (partner info,
Tier & Performance, Territory Assignments).
"""


class PartnerDetailLocators:
    """SA Partner Detail: onboard flow + detail tabs/sections/actions."""

    # ── Onboard New Partner (from the Directory) ──────────────────────────────
    ONBOARD_BUTTON = "Onboard Partner"  # get_by_role button (opens the form + submits)
    ONBOARD_COMPANY = "input[placeholder*='Acme Partner' i]"
    ONBOARD_EMAIL = "input[placeholder*='contact@partner' i]"
    ONBOARD_SUCCESS = "Partner onboarded successfully"

    # ── Detail page ───────────────────────────────────────────────────────────
    ACTIONS_BUTTON = "Partner actions"  # get_by_role button (kebab menu, aria-label)
    TABS = ("Overview", "Deals", "Commission", "Members")
    SECTIONS = ("Tier & Performance", "Territory Assignments")

    # Status badge in the header. Probed live 2026-08-10 on an active and a suspended
    # partner: the badge is a standalone text node, so an EXACT match hits exactly one
    # element, and the losing values appear nowhere else on the page (an Active partner
    # has 0 occurrences of "Suspended" and vice versa). That is what makes
    # `PartnerDetailPage.status()` a real check instead of a substring scan of <main>.
    # "Inactive" was never observed on this build — kept only in case the FE adds it.
    STATUS_VALUES = ("Active", "Suspended", "Pending", "Inactive")

    # ── Partner actions (state-gated menu items) ──────────────────────────────
    # Pending → "Approve Partner"; Active → "Deactivate" (= suspend) + tier upgrades;
    # Deactivated → "Reactivate"/"Activate". Live label is "Deactivate", NOT "Suspend".
    ACTION_APPROVE = "Approve"
    ACTION_DEACTIVATE = "Deactivate"
    ACTION_REACTIVATE = "Reactivate"
    # Shown when the BE rejects the deactivate call (the FE sends no `reason`, which the
    # API requires — BUG-UI-008). The page object polls for this so the rejection path
    # ends as promptly as the success path, and the banner is read before it auto-hides.
    ACTION_FAILED_BANNER = "Failed to deactivate"

    # ── Members tab (Portal Users) — Add User flow ────────────────────────────
    # Columns: USER | ROLE | STATUS | LAST LOGIN | USER ID | (Reset Password).
    # The only per-row action live is "Reset Password" — there is NO member
    # deactivate/reactivate control on this build (verified 2026-08-03).
    MEMBERS_HEADING = "Portal Users"  # get_by_text; header shows "Portal Users (N)"
    MEMBERS_ADD_USER = "Add User"  # get_by_role button (also "Add First User" when empty)
    MEMBERS_ADD_FIRST_USER = "Add First User"
    MEMBER_FIRST_NAME = "input[placeholder='Jane']"
    MEMBER_LAST_NAME = "input[placeholder='Smith']"
    MEMBER_EMAIL = "input[placeholder='partner@company.com']"
    MEMBER_PASSWORD = "input[type=password]"
    MEMBER_CREATE_BUTTON = "Create Portal User"  # get_by_role button (submits the form)
    MEMBER_DONE_BUTTON = "Done"  # get_by_role button (dismisses the success panel)
    MEMBER_CREATED_TOAST = "Portal user created successfully"
