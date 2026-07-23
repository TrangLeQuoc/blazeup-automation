"""Selectors for the Partner Portal (stgpartners.blazeup.ai) left-nav shell.

Like the SA Dashboard, the partner portal is a micro-frontend host: the sidebar
(<aside>) + top bar always render, while each section's content module is fetched
dynamically. So the stable surface to automate first is: navigate to a section,
then assert its content actually rendered (its page-title READY_MARKER visible in
<main>, no error panel).

Route map + markers discovered/validated against the LIVE staging DOM
(2026-07-23, logged in as the configured channel-partner user): the primary
sidebar has exactly 5 nav items. Their routes + rendered page titles are below.
Re-verify here if the portal nav changes.
"""


class PartnerShellLocators:
    """Partner Portal shell: sidebar nav links + global error/loading state."""

    # ── Error / loading state (MFE "Something went wrong" panel) ──────────────
    ERROR_PANEL = ":text('Something went wrong')"
    ERROR_DETAIL = ":text('Failed to fetch dynamically imported module')"

    # ── Main content region ───────────────────────────────────────────────────
    # The sidebar/top bar always render; to prove a *section* rendered we look for
    # its title text scoped to <main>, never the always-present chrome.
    MAIN = "main"

    # ── Sidebar (collapsed by default, icons only; expand to see labels) ──────
    # The trigger toggles a button whose accessible name is "Expand sidebar"
    # (collapsed) / "Collapse sidebar" (expanded).
    SIDEBAR = "aside"
    SIDEBAR_EXPAND_TRIGGER = "button[aria-label='Expand sidebar']"

    # ── Sidebar nav items + per-page READY_MARKER ─────────────────────────────
    # Key -> {label (sidebar text), route (path for goto), marker (page title in
    # <main> once the section rendered)}. All 5 verified rendering with no error
    # panel on 2026-07-23.
    #
    # NOTE on the plan wording: PARTNER_UI_PARTNER_PORTAL_SHELL_001's step text
    # names "My Pipeline / My Clients / Training", but the live portal's primary
    # nav is Dashboard / Deals / Commissions / Resources / My Apps. "My Pipeline"
    # maps to Deals (its page title is "Deal Pipeline"); "My Clients"/"Training"
    # are not top-level nav items (sub-sections / future). The test drives the
    # REAL nav, not the plan's assumed labels.
    SECTIONS: dict[str, dict[str, str]] = {
        "dashboard": {"label": "Dashboard", "route": "/dashboard", "marker": "Tier & Performance"},
        "deals": {"label": "Deals", "route": "/deals", "marker": "Deal Pipeline"},
        "commissions": {"label": "Commissions", "route": "/commissions", "marker": "Commissions"},
        "resources": {"label": "Resources", "route": "/resources", "marker": "Resources"},
        "apps": {"label": "My Apps", "route": "/apps", "marker": "My Apps"},
    }
