"""Selectors for the home page."""


class HomeSelectors:
    """Home page selectors."""

    GREETING_CSS = (
        "[data-testid='greeting'], "
        "[data-testid='dashboard-greeting'], "
        "h1:has-text('Hi'), "
        "h1:has-text('Hello'), "
        "h1:has-text('Good'), "
        "h2:has-text('Good')"
    )
    GREETING_TEXT_PATTERN = r"^(Hi|Hello|Good morning|Good afternoon|Good evening)"
    DASHBOARD_READY_CSS = (
        "[data-testid='home-page'], "
        "[data-testid='dashboard'], "
        "[data-testid='quick-links']"
    )
    DASHBOARD_READY_TEXT_PATTERN = r"^(Quick Links|Celebrations|All Posts)"
    USER_MENU_BUTTON = (
        "[class*='container_avatar'], "
        "[class*='account'], "
        ".ant-avatar, "
        "button:has(.ant-avatar)"
    )
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
        "li:has-text('Logout'), "
        "[role='menuitem']:has-text('Logout'), "
        "[class*='menuItemLogout'], "
        "[data-testid='logout']"
    )
