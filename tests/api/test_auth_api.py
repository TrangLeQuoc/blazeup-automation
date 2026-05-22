"""Authentication API tests TC-A01 to TC-A06."""

import pytest

from api.auth_client import AuthClient, UserInfo
from config.settings import Settings
from utils.helpers import require_credentials

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.smoke
async def test_tca01_login_returns_jwt_token(settings: Settings, auth_client: AuthClient) -> None:
    """TC-A01: BlazeUp sign-in returns a bearer token."""

    email, password = require_credentials(settings.test_email, settings.test_password)
    response = await auth_client.login(email, password)
    assert response.bearer_token, "Login response did not contain a token"
    # A JWT has exactly 2 dots; a plain opaque token has 0
    assert response.bearer_token.count(".") in {0, 2}, (
        f"Token format looks invalid: {response.bearer_token[:20]}..."
    )


async def test_tca02_login_wrong_password_returns_401(settings: Settings, test_data: dict) -> None:
    """TC-A02: BlazeUp sign-in with wrong password is rejected."""

    email = settings.test_email or test_data["invalid_users"]["wrong_password"]["email"]
    password = test_data["invalid_users"]["wrong_password"]["password"]
    client = AuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        response = await client.raw_login({"email": email, "password": password}, expected_status=(400, 401))
        assert response.status_code in {400, 401}
    finally:
        await client.close()


async def test_tca03_client_logout_clears_token_and_subsequent_request_is_rejected(
    settings: Settings,
    auth_client: AuthClient,
) -> None:
    """TC-A03: After client-side logout the bearer token is cleared and the next request returns 401.

    Note: This test covers *client-side* token clearing only.  It verifies that
    once the client's token field is set to None, protected endpoints reject the
    unauthenticated request.  Server-side token revocation (if the API supports a
    sign-out endpoint) should be covered by a separate test once that endpoint is
    confirmed.
    """

    await auth_client.logout()
    assert auth_client.token is None, "logout() should clear client.token"

    response = await auth_client.get("/auth-api/current-user", expected_status=(401, 403))
    assert response.status_code in {401, 403}, (
        f"Expected 401/403 after logout, got {response.status_code}"
    )


@pytest.mark.smoke
async def test_tca04_get_me_returns_user_info(auth_client: AuthClient) -> None:
    """TC-A04: GET /auth-api/current-user returns authenticated user information."""

    user = await auth_client.me()
    assert isinstance(user, UserInfo)
    assert user.id, "User id must be non-empty"


async def test_tca05_api_without_token_returns_401(settings: Settings) -> None:
    """TC-A05: Calling a protected API without token returns 401."""

    client = AuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        response = await client.get("/auth-api/current-user", expected_status=401)
        assert response.status_code == 401
    finally:
        await client.close()


async def test_tca06_api_with_expired_token_returns_401_or_403(settings: Settings) -> None:
    """TC-A06: Calling protected API with invalid/expired token returns 401 or 403."""

    client = AuthClient(
        str(settings.api_base_url),
        token="expired.jwt.token",
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        response = await client.get("/auth-api/current-user", expected_status=(401, 403))
        assert response.status_code in {401, 403}
    finally:
        await client.close()
