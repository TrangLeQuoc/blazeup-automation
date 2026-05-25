"""Authentication API tests TC-A01 to TC-A06."""

import pytest

from api.auth_client import AuthClient, UserInfo
from config.settings import Settings
from utils.helpers import require_credentials
from utils.log_helper import async_step

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.smoke
async def test_tca01_login_returns_jwt_token(settings: Settings, auth_client: AuthClient) -> None:
    """TC-A01: BlazeUp sign-in returns a bearer token."""

    email, password = require_credentials(settings.test_email, settings.test_password)

    async with async_step("Step 1: Login with valid credentials", email=email):
        response = await auth_client.login(email, password)

    async with async_step("Step 2: Verify bearer token is present"):
        assert response.bearer_token, "Login response did not contain a token"

    async with async_step("Step 3: Verify token format (JWT has 2 dots; opaque has 0)"):
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
        async with async_step("Step 1: Attempt login with wrong password", email=email):
            response = await client.raw_login({"email": email, "password": password}, expected_status=(400, 401))

        async with async_step("Step 2: Verify response status is 400 or 401"):
            assert response.status_code in {400, 401}
    finally:
        await client.close()


@pytest.mark.smoke
async def test_tca04_get_me_returns_user_info(auth_client: AuthClient) -> None:
    """TC-A04: GET /auth-api/current-user returns authenticated user information."""

    async with async_step("Step 1: Fetch current user info"):
        user = await auth_client.me()

    async with async_step("Step 2: Verify response is a UserInfo object with a non-empty id"):
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
        async with async_step("Step 1: Call protected endpoint without any token"):
            response = await client.get("/auth-api/current-user", expected_status=401)

        async with async_step("Step 2: Verify status code is 401"):
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
        async with async_step("Step 1: Call protected endpoint with an invalid/expired token"):
            response = await client.get("/auth-api/current-user", expected_status=(401, 403))

        async with async_step("Step 2: Verify status code is 401 or 403"):
            assert response.status_code in {401, 403}
    finally:
        await client.close()
