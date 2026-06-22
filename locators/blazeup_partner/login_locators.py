"""Locators for the partner portal login page (stgpartners.blazeup.ai/login).

Single-step form (email + password + Sign in on one screen) — unlike the SA admin
two-step flow. Selectors are resilient (type/name/placeholder + button text) so
they survive minor markup changes; verify on the first UI run.
"""


class PartnerLoginLocators:
    """Partner portal login locators."""

    EMAIL_INPUT = "input[type='email'], input[name*='email' i], input[placeholder*='email' i]"
    PASSWORD_INPUT = (
        "input[type='password'], input[name*='password' i], input[placeholder*='password' i]"
    )
    SIGN_IN_BUTTON = (
        "button:text-is('Sign in'), "
        "button:text-is('Sign In'), "
        "button:text-is('Login'), "
        "button[type='submit']"
    )
    ERROR_CONTAINERS = (
        "[role='alert'], "
        ".error, "
        ".error-message, "
        ".invalid-feedback, "
        ".text-danger, "
        "[class*='error' i]"
    )
