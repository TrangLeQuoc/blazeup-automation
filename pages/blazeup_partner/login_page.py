"""Login page object for the partner portal (stgpartners.blazeup.ai).

Single-step login: email + password + Sign in on one screen (the SA admin login
is a two-step flow — hence a separate page object per domain). Same BasePage
helpers; only the flow + selectors differ.
"""

import re

from loguru import logger
from playwright.async_api import expect

from locators.blazeup_partner.login_locators import PartnerLoginLocators
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

    async def login(self, email: str, password: str, timeout: int = 60_000) -> None:
        """Submit credentials through the single-step partner login form."""
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
