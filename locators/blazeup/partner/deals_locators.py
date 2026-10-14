"""Locators for the Partner Portal Deals page (/deals — "Deal Pipeline").

Verified against the live staging DOM (2026-07-24, logged in as the channel-partner
user). The pipeline has 6 stage tabs rendered as ``button[role="tab"]`` (each shows
its name + a deal count), a summary line, a Register CTA, and a deals table with an
empty-state when there are no deals.
"""


class DealsLocators:
    """Deal Pipeline page: stage tabs + counts + primary controls."""

    # Page-title READY_MARKER (visible in <main> once the page rendered).
    READY_MARKER = "Deal Pipeline"

    # Primary controls.
    REGISTER_BUTTON = "button:has-text('Register a deal')"
    FILTER_BUTTON = "button:has-text('Filter')"

    # Pipeline summary line ("N deals in your pipeline") + empty-state.
    SUMMARY_TEXT = "deals in your pipeline"
    EMPTY_STATE_TEXT = "No deals found"

    # Loading spinner over the deals table while its data is still being fetched.
    # The title/stage tabs render first (from the dashboard fetch), so this spinner
    # must clear before the list is truly "ready" — a Tailwind ring spinner
    # (border-t-transparent + animate-spin).
    LIST_SPINNER = "[class*='animate-spin'], [class*='border-t-transparent']"

    # ── Deals table (list/detail) ──────────────────────────────────────────────
    # Verified live 2026-10-02 (partner "QA-AUTO Duncan PLC", 102 deals). After the
    # BE fix for the legacy-slug planId defect (was BUG: GET /portal/deals 400
    # "Invalid id: 'pro-v1'"), the list renders rows again.
    #
    # Stage controls are now rendered as BUTTONS (text "<Stage> <count>", e.g.
    # "Won 8"), and the set gained "In Progress" vs the older STAGES tuple.
    STAGE_BUTTONS = ("All", "Pending", "Approved", "In Progress", "Won", "Lost", "Expired")

    # The deals table + its parts (semantic roles are stable; class names are not).
    TABLE = "main table"
    ROWS = "main table tbody tr"
    # Column headers, left→right, as the live DOM renders them. The last header is an
    # empty actions column.
    COLUMNS = (
        "DEAL ID",
        "DOMAIN",
        "DEAL TYPE",
        "PLAN",
        "ESTIMATED ACV",
        "PROTECTION",
        "COMMISSION",
        "LAST UPDATED",
        "STATUS",
    )

    # Deal-detail drawer: a radix dialog opened by clicking a row; its own heading is
    # "Deal Detail" (distinguishes it from the Filter popover, also role=dialog).
    DETAIL_HEADING = "Deal Detail"
    DETAIL_SECTIONS = ("DEAL INFO", "COMPANY INFO")

    # Filter popover (radix): a builder with a field combobox (default "Deal Type")
    # and an "Add Filter" control.
    FILTER_ADD_BUTTON = "Add Filter"

    # Pagination: a numeric "go to page" input in <main> (102 deals / 20 per page).
    PAGE_INPUT = "main input[type='number']"
