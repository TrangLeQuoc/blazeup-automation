"""Selectors for the login page."""


class LoginSelectors:
    """Login page selectors."""

    IDENTIFIER_INPUT = (
        "input[type='email'], "
        "input[name*='email' i], "
        "input[name*='phone' i], "
        "input[placeholder*='email' i], "
        "input[placeholder*='phone' i]"
    )
    PASSWORD_INPUT = (
        "input[type='password'], "
        "input[name*='password' i], "
        "input[placeholder*='password' i]"
    )
    PROCEED_BUTTON = (
        "button:has-text('Proceed'), "
        "button:has-text('Continue'), "
        "button:has-text('Next')"
    )
    LOGIN_BUTTON = (
        "button:has-text('Login'), "
        "button:has-text('Log in'), "
        "button:has-text('Sign in')"
    )
    ERROR_CONTAINERS = (
        "[role='alert'], "
        ".error, "
        ".error-message, "
        ".invalid-feedback, "
        ".text-danger, "
        "[class*='error' i]"
    )

