"""Locators for the SA Dashboard Partner Directory page (/partners).

The SA-side partner-management directory. Verified against the live staging DOM
(stgsa, 2026-07-29, super-admin user): a breadcrumb "Partners / Directory", 4
summary stat cards, Status/Tier filter controls + an "Onboard Partner" action, and
a partner table with an 8-column header and an empty-state when no partners exist.
"""


class PartnerDirectoryLocators:
    """SA Partner Directory: breadcrumb + summary cards + filters + partner table."""

    # Page-title READY_MARKER (in <main>) — the shell section marker is also "Partners".
    READY_MARKER = "Partners"
    BREADCRUMB = "Directory"

    # The 4 summary stat cards (each shows a count).
    SUMMARY_CARDS = ("Total Partners", "Active", "Pending Approval", "Premier Tier")

    # Filter controls (rendered as <button> dropdowns) + the primary action.
    FILTERS = ("Status", "Tier")
    ONBOARD_ACTION = "Onboard Partner"

    # Partner table column headers (<th>), in render order.
    TABLE_HEADERS = (
        "PARTNER",
        "TIER",
        "TYPE",
        "CONTACT",
        "TOTAL ARR",
        "OPEN DEALS",
        "STATUS",
        "JOINED",
    )

    # Empty-state shown when there are no partners yet.
    EMPTY_STATE_TEXT = "No Data Found"
