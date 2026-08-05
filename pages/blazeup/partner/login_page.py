"""Login page object for the partner portal (stgpartners.blazeup.ai).

Single-step login: email + password + Sign in on one screen (the SA admin login
is a two-step flow — hence a separate page object per domain). Same BasePage
helpers; only the flow + selectors differ.
"""

import contextlib
import re

from loguru import logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import expect

from locators.blazeup.partner.login_locators import PartnerLoginLocators
from pages.base_page import BasePage


class PartnerLoginPage(BasePage):
    """Actions + assertions for the partner portal login screen."""

    _ERROR_REGEX = re.compile(
        r"invalid|incorrect|not found|unauthorized|does not exist|wrong|not permitted",
        re.IGNORECASE,
    )

    async def open(self) -> None:
        """Open the partner login page."""
        await self.goto("/login")

    async def login(
        self,
        email: str,
        password: str,
        timeout: int = 60_000,
        totp_secret: str | None = None,
    ) -> None:
        """Submit credentials through the partner login form (+ TOTP 2FA if enabled).

        The portal added a two-factor step: after email+password it prompts for a
        6-digit authenticator code. When *totp_secret* (the base32 enrolment key) is
        provided, this generates the current code with pyotp and completes the step.
        When it is None, only email+password are submitted (pre-2FA behaviour / when
        the account has no 2FA), so existing flows are unaffected.
        """
        logger.info("Partner login with configured user {}", self._mask_email(email))
        await self.fill(
            PartnerLoginLocators.EMAIL_INPUT, email, label="Email Input", timeout=timeout
        )
        await self.fill(
            PartnerLoginLocators.PASSWORD_INPUT, password, label="Password Input", timeout=timeout
        )
        await self.click(
            PartnerLoginLocators.SIGN_IN_BUTTON, label="Sign in Button", timeout=timeout
        )
        if totp_secret:
            await self._complete_totp(totp_secret)

    async def _complete_totp(self, totp_secret: str, timeout: int = 20_000) -> None:
        """Fill the current TOTP code into the 2FA step, then submit.

        Waits briefly for the code input to appear (single one-time-code field OR
        6 single-char boxes). If it never appears, the account may not require 2FA on
        this login — log and return without failing.
        """
        try:
            import pyotp
        except ImportError as exc:
            raise RuntimeError(
                "The partner portal requires 2FA (TOTP) but the 'pyotp' package is not "
                "installed. Install dependencies with `pip install -r requirements.txt` "
                "(or `pip install pyotp`)."
            ) from exc

        code = pyotp.TOTP(totp_secret.replace(" ", "")).now()
        single = self.page.locator(PartnerLoginLocators.TOTP_SINGLE_INPUT).first
        boxes = self.page.locator(PartnerLoginLocators.TOTP_DIGIT_BOXES)
        try:
            await single.wait_for(state="visible", timeout=timeout)
        except Exception:
            if not await boxes.count():
                logger.info("Partner login: no 2FA code step detected — skipping TOTP")
                return
        logger.log("STEP", "Enter 2FA authenticator code (TOTP)")
        n_boxes = await boxes.count()
        if n_boxes >= len(code):
            for i, digit in enumerate(code):
                await boxes.nth(i).fill(digit)
        else:
            await single.fill(code)
        # Some builds auto-submit once the 6th digit is entered (the Verify button
        # goes disabled/aria-busy while it processes). Only click it when it is
        # actually enabled — otherwise the form is already submitting, so clicking a
        # busy button would hang. Best-effort: a missing/busy button is not an error.
        verify = self.page.locator(PartnerLoginLocators.TOTP_VERIFY_BUTTON).first
        with contextlib.suppress(PlaywrightTimeoutError):
            if await verify.count() and await verify.is_visible() and await verify.is_enabled():
                await verify.click(timeout=5_000)

    async def expect_error(self, timeout: int = 10_000) -> str:
        """Assert a login error is visible and return its text."""
        css_locator = self.page.locator(PartnerLoginLocators.ERROR_CONTAINERS).first
        text_locator = self.page.get_by_text(self._ERROR_REGEX).first
        combined = css_locator.or_(text_locator).first
        await expect(combined).to_be_visible(timeout=timeout)
        return " ".join((await combined.inner_text()).split())

    @staticmethod
    def _mask_email(email: str) -> str:
        if "@" not in email:
            return "***"
        prefix, domain = email.split("@", 1)
        return f"{prefix[:2]}***@{domain}"
