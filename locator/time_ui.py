"""Selectors for the time page."""


class TimeSelectors:
    """Time page selectors."""

    CLOCK_IN_BUTTON = "button:has-text('Clock In')"
    CLOCK_OUT_BUTTON = "button:has-text('Clock Out')"
    HISTORY_ROWS = "[data-testid='attendance-row'], table tbody tr"

