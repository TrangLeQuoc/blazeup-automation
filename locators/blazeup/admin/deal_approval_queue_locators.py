"""Locators for the SA Deal Approval Queue page (/partners/deals).

The SA-side deal-approval workspace (PRD §5.2). Re-verified against the live staging
DOM (stgsa, 2026-08-05, super-admin) after a redesign: a breadcrumb "Partners /
Deals", KPI cards, **status tabs rendered as custom <span> chips** (All / Pending /
Approved / In Progress / Won / Expired / Lost / Rejected — no button/tab role, so
fragile to match), a "Deal Type" + "Conflicts only" filter row, and a 9-column deals
table. NOTE: the deal list still fails to load — "Server Error / Invalid id: 'pro-v1'"
+ "No Data Found" (backend defect on the deal-list fetch), so the shell renders but no
deal rows load. Readiness/assertions key off the STABLE shell (filters + table header),
NOT the fragile <span> tab chips.
"""


class DealApprovalQueueLocators:
    """SA Deal Approval Queue: shell markers (filters + table) + error state."""

    ROUTE = "/partners/deals"
    # Breadcrumb / page marker in <main>.
    BREADCRUMB = "Deals"

    # Stable readiness marker: a filter button proves the queue shell mounted (the
    # status tabs are custom <span> chips with no stable role — do not key off them).
    READY_FILTER = "Deal Type"

    # Filter controls (rendered as <button>).
    FILTERS = ("Deal Type", "Conflicts only")

    # Deals table column headers (<th>), in render order (post-redesign).
    TABLE_HEADERS = (
        "DEAL ID",
        "DOMAIN",
        "COMPANY",
        "PARTNER",
        "ESTIMATED ACV",
        "DEAL TYPE",
        "PLAN",
        "STATUS",
        "ACTIONS",
    )

    # Backend-defect banner phrases that must NOT be visible when the queue is healthy.
    SERVER_ERROR_TEXTS = ("Server Error", "Invalid id")

    # Empty-state shown when a queue has no deals.
    EMPTY_STATE_TEXT = "No Data Found"
