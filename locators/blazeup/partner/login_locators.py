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
    # ── Two-factor (TOTP) step ────────────────────────────────────────────────
    # After email+password the portal shows a 6-digit authenticator-code step.
    # OTP inputs are commonly either a single one-time-code field or 6 single-char
    # boxes — the page object handles both. Selectors kept broad on purpose.
    TOTP_SINGLE_INPUT = (
        "input[autocomplete='one-time-code'], "
        "input[name*='otp' i], input[name*='code' i], "
        "input[placeholder*='code' i], input[inputmode='numeric']"
    )
    TOTP_DIGIT_BOXES = "input[maxlength='1']"
    TOTP_VERIFY_BUTTON = (
        "button:text-is('Verify'), "
        "button:text-is('Verify code'), "
        "button:text-is('Continue'), "
        "button:text-is('Submit'), "
        "button:text-is('Confirm'), "
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
