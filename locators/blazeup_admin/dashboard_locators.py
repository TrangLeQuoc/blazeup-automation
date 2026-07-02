"""Selectors for the SA Dashboard **Dashboard** page content.  (Layer-B example)

This is the per-section selector file that complements the shell:
    locators/blazeup_admin/shell_locators.py   → sidebar + error/load state (Layer-A)
    locators/blazeup_admin/dashboard_locators.py  → THIS page's widgets (Layer-B)

It is meant as a worked example of how to build out the remaining 15 pages:
create one ``<section>_locators.py`` per page, fill in stable selectors
(prefer ``[data-testid=...]`` / role+name over brittle CSS classes), then add
``test_sadash_ui_<section>_002+`` content tests.

The values below are BEST-GUESS from the dashboard screenshot (KPI cards,
"System Health", "Risk Signals"). Verify each against the real DOM and replace
text-based locators with data-testid hooks where the app provides them.
"""


class DashboardLocators:
    """Selectors for widgets on the SA Dashboard landing page."""

    # ── Page heading ─────────────────────────────────────────────────────────
    # The page title "Dashboard" (also the shell READY_MARKER). Scoped to <main>
    # so it never matches the sidebar's "Dashboard" nav link.
    PAGE_HEADING = "main >> text='Dashboard'"

    # ── KPI cards (top row) ──────────────────────────────────────────────────
    # Verified against the live DOM (2026-06-04): the app exposes NO data-testid
    # hooks. Each KPI card is a <div> whose label is a child
    #   <div class="... uppercase tracking-wider ...">ACTIVE TENANTS</div>
    # and whose value sits in a sibling (e.g. "$48.2K"). The uppercase+tracking
    # label class is the stable signature, so KPI_CARD counts the labels (one per
    # card). Scoped to <main> to exclude any chrome.
    KPI_CARD = "main div.uppercase.tracking-wider"  # one match per KPI card (10 on staging: 3+7)

    # KPI labels as they actually appear (UPPERCASE) on the dashboard.
    # KPI labels as they actually appear (UPPERCASE), verified against the live DOM
    # (2026-07-01). The dashboard now has TWO KPI rows: a finance row
    # (MRR / ARR / OUTSTANDING AR) then the ops row (7 cards). MRR + ARR therefore
    # appear TWICE — get_by_text(exact) on them matches 2 nodes; prefer the unique
    # labels ("OUTSTANDING AR", "ACTIVE TENANTS", ...) when reading a single card.
    KPI_LABELS: tuple[str, ...] = (
        "MRR",
        "ARR",
        "OUTSTANDING AR",
        "ACTIVE TENANTS",
        "NEW THIS MONTH",
        "CHURNED",
        "NPS",
        "NET REVENUE RET.",
    )

    # ── System Health panel ──────────────────────────────────────────────────
    SYSTEM_HEALTH_PANEL = "h3:has-text('System Health')"
    # A health row is OK when it shows this status text/icon.
    SYSTEM_HEALTH_OK = "text=/Operational|Healthy|OK/i"

    # ── Risk Signals panel ───────────────────────────────────────────────────
    RISK_SIGNALS_PANEL = "h3:has-text('Risk Signals')"

    # ── Recent Activity panel (new 2026-07-01) ───────────────────────────────
    RECENT_ACTIVITY_PANEL = "h3:has-text('Recent Activity')"
