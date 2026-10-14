"""Locators for the Partner Portal Dashboard page (/dashboard).

Re-verified against the live staging dashboard 2026-10-13 (failure screenshots of
run_20261013_103101). The dashboard was REDESIGNED between 2026-10-09 and 2026-10-13:
the "Tier & Performance" panel is gone — replaced by a "Performance" panel (open
deals / closing soon / won deals / win rate) with NO tier-progress content — and all
three KPI cards were relabelled. Territory Assignments / Action Required / Pipeline
Snapshot survived unchanged.
"""


class DashboardLocators:
    """Dashboard: KPI cards + section panels."""

    # Page READY_MARKER (in <main>). The dashboard has no page title, so a section
    # heading stands in. "Pipeline Snapshot" is used because it SURVIVED the 2026-10
    # redesign unchanged; the previous marker ("Tier & Performance") did not, and every
    # dashboard TC then sat out the full 90 s readiness timeout on a page that had in
    # fact rendered fine.
    READY_MARKER = "Pipeline Snapshot"

    # Top KPI cards — each shows a value (a plain count/amount, no "USD" prefix since
    # the redesign) next to its label.
    KPI_CARDS = ("Open pipeline (est. ACV)", "Commission paid YTD", "Active Clients")

    # Section panels on the dashboard.
    SECTIONS = (
        "Performance",
        "Territory Assignments",
        "Action Required",
        "Pipeline Snapshot",
    )
