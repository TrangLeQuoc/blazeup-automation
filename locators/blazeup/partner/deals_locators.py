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

    # The 6 pipeline stage tabs (role="tab"); each tab's text is "<Stage> <count>".
    STAGES = ("All", "Pending", "Approved", "Won", "Lost", "Expired")

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
