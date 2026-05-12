"""Selectors for the home page."""


class HomeSelectors:
    """Home page selectors."""

    GREETING_CSS = (
        "[data-testid='greeting'], "
        "[data-testid='dashboard-greeting'], "
        "h1:has-text('Hi'), "
        "h1:has-text('Hello')"
    )
    GREETING_TEXT_PATTERN = r"^(Hi|Hello|Good morning|Good afternoon|Good evening)"
    LOCATION_DROPDOWN = (
        "select[name*='location' i], "
        "[role='combobox']:has-text('Location'), "
        "[data-testid='location-dropdown']"
    )
    CLOCK_IN_BUTTON = (
        "button:has-text('Clock In'), "
        "button:has-text('Check In'), "
        "[data-testid='clock-in']"
    )
    LOGOUT_BUTTON = (
        "button:has-text('Logout'), "
        "button:has-text('Log out'), "
        "a:has-text('Logout'), "
        "a:has-text('Log out'), "
        "[data-testid='logout']"
    )
