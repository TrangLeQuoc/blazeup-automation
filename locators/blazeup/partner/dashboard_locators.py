"""Locators for the Partner Portal Dashboard page (/dashboard).

Verified against the live staging DOM (2026-07-28, channel-partner user). The
dashboard shows a row of KPI cards, a Tier & Performance panel, plus Territory
Assignments / Action Required / Pipeline Snapshot sections.
"""


class DashboardLocators:
    """Dashboard: KPI cards + section panels."""

    # Page-title READY_MARKER (in <main>).
    READY_MARKER = "Tier & Performance"

    # Top KPI cards — each shows a value ("USD 0" / a count) next to its label.
    KPI_CARDS = ("Total pipeline ACV", "Commission YTD", "Active Tenants")

    # Section panels on the dashboard.
    SECTIONS = (
        "Tier & Performance",
        "Territory Assignments",
        "Action Required",
        "Pipeline Snapshot",
    )
