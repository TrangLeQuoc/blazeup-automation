"""Selectors for the home page."""


class HomeSelectors:
    """Home page selectors."""

    GREETING_CSS = (
        "[data-testid='greeting'], "
        "[data-testid='dashboard-greeting'], "
        "[data-testid='sa-greeting'], "
        "h1:has-text('Hi'), "
        "h1:has-text('Hello'), "
        "h1:has-text('Good'), "
        "h1:has-text('Welcome'), "
        "h2:has-text('Good'), "
        "h2:has-text('Welcome')"
    )
    GREETING_TEXT_PATTERN = r"^(Hi|Hello|Good morning|Good afternoon|Good evening|Welcome)"
    DASHBOARD_READY_CSS = (
        "[data-testid='home-page'], "
        "[data-testid='dashboard'], "
        "[data-testid='sa-dashboard'], "
        "[data-testid='quick-links'], "
        "[class*='dashboard'], "
        "[class*='sa-dashboard']"
    )
    # HRMS portal: Quick Links / Celebrations / All Posts
    # SA Dashboard (observed from screenshots): System Health / Recent Activity /
    #   Risk Signals / Active Tenants / Dashboard breadcrumb
    DASHBOARD_READY_TEXT_PATTERN = (
        r"^(Quick Links|Celebrations|All Posts"
        r"|Total Partners|Active Tenants|Active Dealers|Partners|Dashboard"
        r"|System Health|Recent Activity|Risk Signals)"
    )
    USER_MENU_BUTTON = (
        # Radix UI DropdownMenu.Trigger — SA Dashboard orange avatar circle.
        # Radix automatically sets aria-haspopup="menu" and data-state on the trigger.
        "button[aria-haspopup='menu'], "
        "button[aria-haspopup='true'], "
        # Data-testid based
        "[data-testid='user-menu'], "
        "[data-testid='avatar'], "
        "[data-testid*='profile'], "
        # Class-based — cover camelCase, kebab-case, BEM variants
        "[class*='userMenu'], "
        "[class*='user-menu'], "
        "[class*='UserMenu'], "
        "[class*='container_avatar'], "
        "[class*='avatar'], "
        "[class*='Avatar'], "
        "[class*='account'], "
        # Ant Design avatar
        ".ant-avatar, "
        "button:has(.ant-avatar), "
        # ARIA-labelled profile/account buttons
        "button[aria-label*='profile' i], "
        "button[aria-label*='user' i], "
        "button[aria-label*='account' i], "
        "button[aria-label*='menu' i], "
        # Last resort: last button inside the top header nav
        "header button:last-of-type, "
        "nav button:last-of-type"
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
        "button:has-text('Sign out'), "
        "a:has-text('Logout'), "
        "a:has-text('Log out'), "
        "a:has-text('Sign out'), "
        "li:has-text('Logout'), "
        "li:has-text('Log out'), "
        "li:has-text('Sign out'), "
        "[role='menuitem']:has-text('Logout'), "
        "[role='menuitem']:has-text('Log out'), "
        "[role='menuitem']:has-text('Sign out'), "
        "[class*='menuItemLogout'], "
        "[class*='logout'], "
        "[data-testid='logout'], "
        "[data-testid='sign-out']"
    )
