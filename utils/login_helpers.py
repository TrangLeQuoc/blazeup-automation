"""Reusable login helpers — credential-agnostic.

These two functions are the single source of truth for how the framework
authenticates.  Fixtures in ``pytest_support/fixtures.py`` call them and
supply credentials from ``Settings``; individual tests can also call them
directly when they need custom credentials or mid-test re-authentication.

Usage in a test
---------------
.. code-block:: python

    from utils.login_helpers import login_ui, login_api

    # UI login (returns the same Page, now authenticated)
    async def test_something(page, settings):
        await login_ui(page, str(settings.base_url),
                       settings.test_email, settings.test_password)

    # API login (returns a bearer-token string)
    async def test_something_else(settings):
        token = await login_api(str(settings.api_base_url), str(settings.base_url),
                                settings.test_email, settings.test_password)
"""

import os
import re

from playwright.async_api import Page
from playwright.async_api import expect as pw_expect

from api_clients.auth_base import BaseAuthClient
from api_clients.blazeup_admin.auth_client import AuthClient
from api_clients.blazeup_partner.auth_client import PartnerAuthClient
from pages.base_page import BasePage
from pages.blazeup_admin.login_page import LoginPage
from pages.blazeup_partner.login_page import PartnerLoginPage

# Each domain owns its auth client (endpoints differ per domain). The shared login
# mechanics live in BaseAuthClient. Pick the client by BLAZEUP_DOMAIN.
AUTH_CLIENTS: dict[str, type[BaseAuthClient]] = {
    "blazeup_admin": AuthClient,
    "blazeup_partner": PartnerAuthClient,
}

# Each domain owns its login page object (different login flow + selectors).
# Admin = two-step (email → proceed → password); partner = single-step.
LOGIN_PAGES: dict[str, type[BasePage]] = {
    "blazeup_admin": LoginPage,
    "blazeup_partner": PartnerLoginPage,
}


def _auth_client_for_domain() -> type[BaseAuthClient]:
    """Resolve the domain's auth client class from BLAZEUP_DOMAIN (defaults to admin)."""
    return AUTH_CLIENTS.get(os.getenv("BLAZEUP_DOMAIN", "blazeup_admin"), AuthClient)


def _login_page_for_domain() -> type[BasePage]:
    """Resolve the domain's login page class from BLAZEUP_DOMAIN (defaults to admin)."""
    return LOGIN_PAGES.get(os.getenv("BLAZEUP_DOMAIN", "blazeup_admin"), LoginPage)


async def login_ui(
    page: Page,
    base_url: str,
    email: str,
    password: str,
    timeout: int = 30_000,
) -> Page:
    """Log in through the BlazeUp UI login page (domain-aware).

    Opens ``/login`` with the domain's login page object (admin = two-step,
    partner = single-step), submits *email*/*password*, then waits until the
    browser navigates away from the login page.

    Args:
        page:     A Playwright ``Page`` (may be blank or on any URL).
        base_url: Application root URL, e.g. ``"https://stgsa.blazeup.ai"``.
        email:    User e-mail address.
        password: User password.
        timeout:  Milliseconds to wait for the post-login redirect (default 30 s).

    Returns:
        The same ``Page`` object, now authenticated.

    Raises:
        AssertionError: If the browser is still on ``/login`` after *timeout*.
    """
    login_page = _login_page_for_domain()(page, base_url)
    await login_page.open()
    await login_page.login(email, password)
    await pw_expect(page).not_to_have_url(re.compile(r".*/login.*"), timeout=timeout)
    return page


async def login_api(
    api_base_url: str,
    app_origin: str,
    email: str,
    password: str,
    max_response_time_ms: int = 30_000,
    auth_cls: "type[BaseAuthClient] | None" = None,
) -> str:
    """Log in via the BlazeUp REST API and return a bearer token.

    Creates a short-lived ``AuthClient``, performs the sign-in call,
    closes the HTTP session, and returns the raw token string.

    Args:
        api_base_url:         API root URL, e.g. ``"https://api.stg.blazeup.ai"``.
        app_origin:           UI base URL sent as the HTTP ``Origin`` header.
        email:                User e-mail address.
        password:             User password.
        max_response_time_ms: Allowed response time for the login call in ms.
                              Fixtures pass ``settings.default_response_time_ms * 5``
                              because login is setup, not the assertion under test.

    Returns:
        Bearer token string (e.g. ``"eyJ..."``).

    Raises:
        ValueError: If the API response contains no token field.
        AssertionError: If the response time exceeds *max_response_time_ms*.
    """
    client = (auth_cls or _auth_client_for_domain())(
        api_base_url,
        max_response_time_ms=max_response_time_ms,
        app_origin=app_origin,
    )
    try:
        response = await client.login(email, password)
        return response.bearer_token
    finally:
        await client.close()
