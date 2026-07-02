"""Selectors for the SA Dashboard left-nav shell.

The sidebar renders reliably even when a section's micro-frontend fails to load,
so navigation + error-state detection can be automated now; per-section content
selectors are added later (once the deploy is fixed and real data shows up).

Fill in / verify the TODO values against the real DOM when available.
"""


class ShellLocators:
    """SA Dashboard shell: sidebar nav links + global error banner."""

    # ── Error / loading state (the "Something went wrong" panel in the shell) ──
    # Shown when a section's dynamically-imported module fails to load.
    ERROR_PANEL = ":text('Something went wrong')"
    ERROR_DETAIL = ":text('Failed to fetch dynamically imported module')"
    TRY_AGAIN_BUTTON = "button:has-text('Try again')"

    # ── Main content region ───────────────────────────────────────────────────
    # The sidebar (<aside>) and top bar (<header>) ALWAYS render, even when a
    # section's micro-frontend fails to load. To prove the *section* rendered we
    # look for its title text scoped to <main>, never the always-present chrome.
    MAIN = "main"

    # ── Sidebar collapse/expand ───────────────────────────────────────────────
    # The sidebar starts COLLAPSED (width ~48px, icons only). In that state the
    # nav labels are NOT rendered, so click-by-label navigation can't find them.
    # Expand it first via the trigger button. The trigger toggles its aria-label
    # between "Expand sidebar" (collapsed) and "Collapse sidebar" (expanded);
    # `data-state` on the <aside> reflects "collapsed" / "expanded".
    SIDEBAR = "aside[data-sidebar='sidebar']"
    SIDEBAR_TRIGGER = "[data-sidebar='trigger']"

    # ── Sidebar nav items + per-page READY_MARKER ─────────────────────────────
    # Key            -> {label, route, marker}
    #   label   : sidebar text used for click-by-text navigation (robust to route
    #             changes); verified against the real DOM.
    #   route   : path for direct goto().
    #   marker  : the page-title TEXT that appears in <main> once the section's
    #             micro-frontend has rendered — the page's READY_MARKER. Used as a
    #             POSITIVE readiness signal (vs the negative "no error panel"
    #             check): the page is considered loaded only when this text is
    #             visible inside <main>. Discovered/validated against the live
    #             staging DOM (see notes below).
    #
    # Notes from DOM discovery (staging, 2026-06-04):
    #   - dashboard route is /dashboard (NOT /sa-dashboard, which 404s).
    #   - marketplace / marketing_library / expense_library currently fail on
    #     staging ("Failed to fetch dynamically imported module"), so their marker
    #     is the best-guess page title (sidebar label) — to be re-verified once the
    #     deploy is healthy. Until then the READY_MARKER correctly fails for them.
    #   - statutory (/statutory) redirects to /statutory/payroll-rules; the default
    #     tab heading "Payroll Rules" is the rendered title.
    SECTIONS: dict[str, dict[str, str]] = {
        "dashboard": {"label": "Dashboard", "route": "/dashboard", "marker": "Dashboard"},
        "tenants": {"label": "Tenants", "route": "/tenants", "marker": "Tenant Management"},
        "billing": {"label": "Billing", "route": "/billing", "marker": "Billing Management"},
        "plans": {"label": "Plans", "route": "/plans", "marker": "Plans"},
        "partners": {"label": "Partners", "route": "/partners", "marker": "Partners"},
        "marketplace": {
            "label": "Marketplace",
            "route": "/marketplace-app",
            "marker": "Marketplace",
        },
        "audit_log": {"label": "Audit Log", "route": "/auditLog", "marker": "Audit Log"},
        "connectors": {"label": "Connectors", "route": "/connectors", "marker": "Connectors"},
        "platform_templates": {
            "label": "Platform Templates",
            "route": "/platform-templates",
            "marker": "Platform Templates",
        },
        "marketing_library": {
            "label": "Marketing Library",
            "route": "/marketing-library",
            "marker": "Marketing Library",
        },
        "expense_library": {
            "label": "Expense Library",
            "route": "/expense-library",
            "marker": "Expense Library",
        },
        "help_platform": {
            "label": "Help Platform",
            "route": "/help-platform",
            "marker": "Help Platform",
        },
        "statutory_reports": {
            "label": "Statutory Rules",
            "route": "/statutory",
            "marker": "Payroll Rules",
        },
        "compliance": {"label": "Compliance", "route": "/compliance", "marker": "Compliance"},
        "governance": {
            "label": "Governance",
            "route": "/governance",
            "marker": "Platform Governance",
        },
        # Added 2026-07-01 (live sidebar now has 16 items). The MFE currently fails
        # on staging ("Something went wrong"), so the marker is the best-guess page
        # title — re-verify once the deploy is healthy; until then READY_MARKER
        # correctly fails for it (fail-by-design).
        "user_groups_permissions": {
            "label": "User Groups & Permissions",
            "route": "/user-groups-permissions",
            "marker": "User Groups & Permissions",
        },
    }
