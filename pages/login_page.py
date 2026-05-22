"""Login page object for the HRMS application."""

import re

from loguru import logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import expect

from pages.base_page import BasePage
from locator.login_ui import LoginSelectors


class LoginPage(BasePage):
    """Actions and assertions for authentication screens."""

    _ERROR_REGEX = re.compile(
        r"invalid|incorrect|not found|unauthorized|does not exist|wrong",
        re.IGNORECASE,
    )

    async def open(self) -> None:
        """Open the login page."""

        await self.goto("/login")

    async def login(self, email: str, password: str) -> None:
        """Submit credentials through BlazeUp's two-step login flow."""

        logger.info("Logging in with configured user {}", self._mask_email(email))
        await self.fill(LoginSelectors.IDENTIFIER_INPUT, email, label="Email/Phone Input")
        await self.click(LoginSelectors.PROCEED_BUTTON, label="Proceed Button")

        try:
            await self.wait_for_element(LoginSelectors.PASSWORD_INPUT, timeout=5_000, label="Password Input")
        except PlaywrightTimeoutError:
            logger.info("Password step did not appear; expecting identifier-level validation")
            return

        await self.fill(LoginSelectors.PASSWORD_INPUT, password, label="Password Input")
        await self.click(LoginSelectors.LOGIN_BUTTON, label="Login Button")

    async def expect_error(self, timeout: int = 10_000) -> str:
        """Assert that an authentication error is visible and return it."""

        css_locator = self.page.locator(LoginSelectors.ERROR_CONTAINERS).first
        text_locator = self.page.get_by_text(self._ERROR_REGEX).first

        # Combine both locators to wait for either one simultaneously
        combined_locator = css_locator.or_(text_locator).first

        logger.info("Waiting for error message...")
        await expect(combined_locator).to_be_visible(timeout=timeout)

        return " ".join((await combined_locator.inner_text()).split())

    @staticmethod
    def _mask_email(email: str) -> str:
        """Mask an email address for safe logging."""

        if "@" not in email:
            return "***"
        prefix, domain = email.split("@", 1)
        return f"{prefix[:2]}***@{domain}"
