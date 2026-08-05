"""Locators for the SA Partner Programme Analytics page (/partners/analytics).

The SA-side partner-programme analytics dashboard (PRD §7). Verified against the live
staging DOM (stgsa, 2026-07-29, super-admin): summary KPI cards, a Deal Funnel, a
Tier Distribution breakdown, and a Top Partners by ARR table. NOTE: the page shows a
"Server Error — Invalid pagination: limit must not exceed 100" banner (a backend
defect on a paginated analytics query), so it renders its shell but a data query errors.
"""


class PartnerAnalyticsLocators:
    """SA Partner Programme Analytics: KPI cards + funnel + tier distribution + top partners."""

    ROUTE = "/partners/analytics"
    BREADCRUMB = "Analytics"

    # Summary KPI cards (each shows a $ / % / count value).
    KPI_CARDS = (
        "Total Partners",
        "Total ARR",
        "Avg Deal Size",
        "Win Rate",
        "Pending Payouts",
        "Clawback Exposure",
    )

    # Deal Funnel stages (in order).
    FUNNEL_STAGES = ("Registered", "Approved", "In Progress", "Won")

    # Named section panels.
    SECTIONS = ("Deal Funnel", "Tier Distribution", "Top Partners by ARR")

    # Backend-defect banner phrases that must NOT be visible when the page is healthy.
    SERVER_ERROR_TEXTS = ("Server Error", "Invalid pagination", "limit must not")
