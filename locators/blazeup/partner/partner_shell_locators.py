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

    # ── Content-level load error (data fetch failed) ──────────────────────────
    # DISTINCT from the MFE ERROR_PANEL: the section heading (READY_MARKER) still
    # renders while the page's DATA fails to load, showing a red banner like
    # "Failed to load your apps. Please refresh and try again." So marker-readiness
    # alone is NOT enough — a healthy page must ALSO show none of these phrases in
    # <main>. Kept to explicit failure phrasing (not the bare word "error") so a
    # valid empty-state (e.g. "0 apps submitted") is never mis-flagged.
    CONTENT_ERROR_TEXTS = (
        "Failed to load",
        "Please refresh and try again",
        "Something went wrong",
    )

    # ── Authorization / global failure phrases ────────────────────────────────
    # A THIRD list, deliberately separate from CONTENT_ERROR_TEXTS — they differ in
    # both WHAT they mean and WHERE they are checked:
    #   CONTENT_ERROR_TEXTS : a section's data fetch failed  -> checked inside <main>
    #                         (PartnerShellPage.assert_content_loaded)
    #   AUTH_ERROR_TEXTS    : the user is not allowed to see the page -> checked
    #                         PAGE-WIDE, because an auth banner renders outside <main>
    # Not merged on purpose: "Failed to load" on the dashboard is a data defect for
    # that page, while "403" is an access-control problem — different verdicts, and
    # merging would silently change what each existing test fails on. Both lists live
    # here so adding a phrase is one edit, in one place.
    AUTH_ERROR_TEXTS = (
        "Something went wrong",
        "not authorized",
        "Unauthorized",
        "403",
        "Access denied",
    )

    # ── Main content region ───────────────────────────────────────────────────
    # The sidebar/top bar always render; to prove a *section* rendered we look for
    # its title text scoped to <main>, never the always-present chrome.
    MAIN = "main"
    BODY = "body"

    # ── Sidebar (collapsed by default, icons only; expand to see labels) ──────
    # The trigger toggles a button whose accessible name is "Expand sidebar"
    # (collapsed) / "Collapse sidebar" (expanded).
    SIDEBAR = "aside"
    SIDEBAR_EXPAND_TRIGGER = "button[aria-label='Expand sidebar']"

    # ── Shell chrome (renders on every section, even a broken one) ────────────
    # Asserting on these proves the SHELL loaded; it says nothing about the section,
    # which is exactly why section readiness uses SECTIONS[...]["marker"] in <main>.
    BRAND_TEXT = "PARTNER PORTAL"
    PROFILE_BUTTON_NAME = "Open profile menu"

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
    # Live nav = 6 items (re-verified 2026-07-29): a "Directory" (team members) item
    # was added since the original 5-item snapshot.
    SECTIONS: dict[str, dict[str, str]] = {
        "dashboard": {"label": "Dashboard", "route": "/dashboard", "marker": "Tier & Performance"},
        "deals": {"label": "Deals", "route": "/deals", "marker": "Deal Pipeline"},
        "commissions": {"label": "Commissions", "route": "/commissions", "marker": "Commissions"},
        "directory": {"label": "Directory", "route": "/directory", "marker": "Directory"},
        "resources": {"label": "Resources", "route": "/resources", "marker": "Resources"},
        "apps": {"label": "My Apps", "route": "/apps", "marker": "My Apps"},
    }
