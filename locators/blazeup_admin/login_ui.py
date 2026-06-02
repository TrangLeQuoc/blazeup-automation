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
    # Use :text-is() (exact match) instead of :has-text() (partial match).
    # The SA Dashboard login page has both "Continue with Google" and "Continue"
    # buttons — :has-text('Continue') would match "Continue with Google" first,
    # triggering OAuth instead of advancing the email/password form.
    PROCEED_BUTTON = (
        "button:text-is('Proceed'), "
        "button:text-is('Continue'), "
        "button:text-is('Next')"
    )
    LOGIN_BUTTON = (
        "button:text-is('Login'), "
        "button:text-is('Log in'), "
        "button:text-is('Sign in'), "
        "button:text-is('Verify'), "
        "button:text-is('Continue')"
    )
    ERROR_CONTAINERS = (
        "[role='alert'], "
        ".error, "
        ".error-message, "
        ".invalid-feedback, "
        ".text-danger, "
        "[class*='error' i]"
    )

