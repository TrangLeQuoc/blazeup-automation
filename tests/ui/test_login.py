"""Authentication UI tests TC01-TC05."""

import re

import allure
import pytest
from playwright.async_api import Page, expect

from config.settings import Settings
from pages.home_page import HomePage
from pages.login_page import LoginPage
from utils.helpers import require_credentials
from utils.log_helper import async_step

pytestmark = [pytest.mark.ui, pytest.mark.regression]


@allure.epic("BlazeUp HRMS")
@allure.feature("Authentication")
@allure.story("Login succeeds with valid credentials")
@pytest.mark.smoke
async def test_tc01_login_success_with_valid_credentials(page: Page, settings: Settings) -> None:
    """TC01: Login succeeds with valid credentials."""

    email, password = require_credentials(settings.test_email, settings.test_password)
    login_page = LoginPage(page, str(settings.base_url))
    home_page = HomePage(page, str(settings.base_url))

    async with async_step("Step 1: Open the login page"):
        await login_page.open()

    async with async_step("Step 2: Enter credentials and submit the login form", email=email):
        await login_page.login(email, password)

    async with async_step("Step 3: Verify successful redirect to the home page"):
        await home_page.expect_loaded()
        assert "/login" not in page.url


@allure.epic("BlazeUp HRMS")
@allure.feature("Authentication")
@allure.story("Login fails with wrong password")
async def test_tc02_login_fails_with_wrong_password(
    page: Page,
    settings: Settings,
    test_data: dict,
) -> None:
    """TC02: Login fails with wrong password and shows an error."""

    email = settings.test_email or test_data["invalid_users"]["wrong_password"]["email"]
    password = test_data["invalid_users"]["wrong_password"]["password"]
    login_page = LoginPage(page, str(settings.base_url))

    async with async_step("Step 1: Open the login page"):
        await login_page.open()

    async with async_step("Step 2: Submit login form with wrong password", email=email):
        await login_page.login(email, password)

    async with async_step("Step 3: Verify error message is shown"):
        try:
            error = await login_page.expect_error()
            assert error
        except AssertionError:
            raise AssertionError(
                f"BUG (backend): POST /sa-auth-api/sign-in/credentials"
                f" — expected: error message on UI for wrong password,"
                f" actual: no error rendered (server likely returned 5xx)"
            )


@allure.epic("BlazeUp HRMS")
@allure.feature("Authentication")
@allure.story("Login fails with unknown email")
async def test_tc03_login_fails_with_unknown_email(
    page: Page,
    settings: Settings,
    test_data: dict,
) -> None:
    """TC03: Login fails for an email that does not exist."""

    user = test_data["invalid_users"]["unknown_email"]
    login_page = LoginPage(page, str(settings.base_url))

    async with async_step("Step 1: Open the login page"):
        await login_page.open()

    async with async_step("Step 2: Submit login form with unknown email", email=user["email"]):
        await login_page.login(user["email"], user["password"])

    async with async_step("Step 3: Verify an error message is shown"):
        error = await login_page.expect_error()
        assert error


@allure.epic("BlazeUp HRMS")
@allure.feature("Authentication")
@allure.story("Logout clears browser session")
async def test_tc05_logout_clears_session(authenticated_page: Page, settings: Settings) -> None:
    """TC05: Logout clears the browser session."""

    home_page = HomePage(authenticated_page, str(settings.base_url))

    async with async_step("Step 1: Click the logout button"):
        await home_page.logout()

    async with async_step("Step 2: Verify redirect to the login/auth page"):
        await expect(authenticated_page).to_have_url(re.compile(r".*/(login|auth).*"), timeout=10_000)

    async with async_step("Step 3: Verify auth/session cookies are cleared"):
        cookies = await authenticated_page.context.cookies(str(settings.base_url))
        auth_cookies = [
            cookie for cookie in cookies
            if "token" in cookie["name"].lower() or "session" in cookie["name"].lower()
        ]
        assert not auth_cookies
