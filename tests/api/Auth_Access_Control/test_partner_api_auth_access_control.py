"""Partner API auth & access-control tests PARTNER_API_AUTH_ACCESS_CONTROL_001–009."""

import allure
import pytest

from api.auth_client import AuthClient
from api.partner_auth_client import PartnerAuthClient, PartnerLoginResponse
from config.settings import Settings
from utils.helpers import require_credentials
from utils.log_helper import async_step

pytestmark = [pytest.mark.api, pytest.mark.regression]


async def _partner_login(client: PartnerAuthClient, email: str, password: str) -> None:
    """Login and fail with a clear message when the endpoint is not implemented (404)."""
    resp = await client.raw_login({"email": email, "password": password}, expected_status=None)
    if resp.status_code == 404:
        pytest.fail(
            "NOT IMPLEMENTED (backend): POST /v1/partner/auth/login returned 404 — "
            "Partner Platform auth API has not been deployed to staging yet."
        )
    assert resp.status_code in {200, 201}, (
        f"partner login failed: POST /v1/partner/auth/login "
        f"returned {resp.status_code} — expected 200/201."
    )
    from api.partner_auth_client import PartnerLoginResponse
    data = PartnerLoginResponse.model_validate(resp.json())
    client.token = data.bearer_token
    client.refresh_token = data.refresh_token


# ---------------------------------------------------------------------------
# TC001 — Valid partner JWT → dashboard → 200
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Authenticate - Valid partner JWT - Partner-scoped request succeeds")
@pytest.mark.smoke
async def test_partner_api_auth_access_control_001(settings: Settings) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_001: Valid partner JWT gives 200 on dashboard."""

    email, password = require_credentials(settings.partner_email, settings.partner_password)
    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login as partner", email=email):
            await _partner_login(client, email, password)

        async with async_step("Step 2: GET /v1/partner/dashboard with valid partner JWT"):
            response = await client.dashboard(expected_status=None)

        async with async_step("Step 3: Verify response is 200"):
            assert response.status_code == 200, (
                f"BUG (backend): GET /v1/partner/dashboard"
                f" — expected: 200 (valid partner JWT should be accepted),"
                f" actual: {response.status_code}"
            )

        async with async_step("Step 4: Verify response body contains partner dashboard data"):
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            assert body, (
                "GET /v1/partner/dashboard returned 200 but an empty body — "
                "expected a JSON object with partner KPI data"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC002 — Tenant (SA) JWT on partner API → 401
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Reject - Tenant JWT on partner API - Request is unauthorized")
async def test_partner_api_auth_access_control_002(
    settings: Settings,
    api_token: str,
) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_002: SA/tenant JWT is rejected by the partner API."""

    # Use the SA bearer token (api_token fixture) directly — no partner login.
    client = PartnerAuthClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Call GET /v1/partner/dashboard using SA/tenant JWT"):
            response = await client.dashboard(expected_status=None)

        async with async_step("Step 2: Verify 401 — tenant JWT must be rejected"):
            assert response.status_code == 401, (
                f"BUG (backend): GET /v1/partner/dashboard"
                f" — expected: 401 (tenant JWT should not be accepted by partner API),"
                f" actual: {response.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC003 — Partner JWT accessing another partner's data → 403
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Reject - Partner JWT accessing another partner - Request is forbidden")
async def test_partner_api_auth_access_control_003(
    settings: Settings,
    test_data: dict,
) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_003: Partner A JWT cannot access Partner B's data."""

    email, password = require_credentials(settings.partner_email, settings.partner_password)
    other_partner_id = test_data["partner_users"]["secondary"]["partner_id"]
    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login as Partner A", email=email):
            await _partner_login(client, email, password)

        async with async_step(
            "Step 2: Attempt GET /v1/partner/{id}/dashboard with Partner A JWT",
            partner_id=other_partner_id,
        ):
            response = await client.partner_data(other_partner_id, expected_status=None)

        async with async_step("Step 3: Verify 403 — cross-partner access must be forbidden"):
            assert response.status_code == 403, (
                f"BUG (backend): GET /v1/partner/{other_partner_id}/dashboard"
                f" — expected: 403 (partner A JWT must not access partner B data),"
                f" actual: {response.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC004 — Admin MFA policy — protected action without MFA → 403 / 428
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Enforce - Admin MFA policy - Protected action requires MFA")
async def test_partner_api_auth_access_control_004(settings: Settings) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_004: MFA-protected admin action is rejected without OTP.

    NOTE: The exact endpoint path must be confirmed once the API contract is
    finalised (see PartnerAuthClient.mfa_protected_action).  The current path
    /v1/partner/admin/security/settings is a placeholder.
    Expected status: 403 Forbidden or 428 Precondition Required.
    """

    email, password = require_credentials(settings.partner_email, settings.partner_password)
    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login as partner admin", email=email):
            await _partner_login(client, email, password)

        async with async_step("Step 2: Call MFA-protected endpoint without an OTP token"):
            response = await client.mfa_protected_action(expected_status=None)

        async with async_step("Step 3: Verify 403 or 428 — MFA must be enforced"):
            assert response.status_code in {403, 428}, (
                f"BUG (backend): POST /v1/partner/admin/security/settings"
                f" — expected: 403 or 428 (MFA should be required for this action),"
                f" actual: {response.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC005 — MSP role accessing payroll data → 403
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Guard - MSP accesses payroll data - Request is forbidden")
async def test_partner_api_auth_access_control_005(
    settings: Settings,
    test_data: dict,
) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_005: MSP-role partner cannot access payroll data."""

    msp = test_data["partner_users"]["msp"]
    msp_email, msp_password = require_credentials(msp.get("email"), msp.get("password"))

    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login as MSP-role partner", email=msp_email):
            await _partner_login(client, msp_email, msp_password)

        async with async_step("Step 2: Attempt GET /v1/partner/payroll"):
            response = await client.payroll(expected_status=None)

        async with async_step("Step 3: Verify 403 — MSP must not access payroll"):
            assert response.status_code == 403, (
                f"BUG (backend): GET /v1/partner/payroll"
                f" — expected: 403 (MSP role should be denied access to payroll data),"
                f" actual: {response.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC006 — MSP role exporting employee records → 403
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Guard - MSP exports employee records - Request is forbidden")
async def test_partner_api_auth_access_control_006(
    settings: Settings,
    test_data: dict,
) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_006: MSP-role partner cannot export employee records."""

    msp = test_data["partner_users"]["msp"]
    msp_email, msp_password = require_credentials(msp.get("email"), msp.get("password"))

    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login as MSP-role partner", email=msp_email):
            await _partner_login(client, msp_email, msp_password)

        async with async_step("Step 2: Attempt GET /v1/partner/employees/export"):
            response = await client.export_employees(expected_status=None)

        async with async_step("Step 3: Verify 403 — MSP must not export employee records"):
            assert response.status_code == 403, (
                f"BUG (backend): GET /v1/partner/employees/export"
                f" — expected: 403 (MSP role should be denied employee record export),"
                f" actual: {response.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC007 — Token refresh: valid refresh → new access token; invalid → 401
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Refresh - Valid refresh token - New access token is issued without re-login")
async def test_partner_api_auth_access_control_007(settings: Settings) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_007: Valid refresh token yields a new access token."""

    email, password = require_credentials(settings.partner_email, settings.partner_password)
    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login to obtain access + refresh tokens", email=email):
            await _partner_login(client, email, password)
            assert client.refresh_token, (
                "POST /v1/partner/auth/login returned 200 but no refresh_token in body"
            )

        async with async_step("Step 2: POST /v1/partner/auth/refresh with valid refresh token"):
            response = await client.token_refresh(client.refresh_token, expected_status=None)

        async with async_step("Step 3: Verify 200 and new access_token in response"):
            assert response.status_code == 200, (
                f"BUG (backend): POST /v1/partner/auth/refresh"
                f" — expected: 200 (valid refresh token should issue a new access token),"
                f" actual: {response.status_code}"
            )
            body = response.json()
            new_token = body.get("access_token") or body.get("accessToken") or body.get("token")
            assert new_token, "POST /v1/partner/auth/refresh returned 200 but no access_token in body"

        async with async_step("Step 4: Use new access token — GET /v1/partner/dashboard → 200"):
            client.token = new_token
            dash = await client.dashboard(expected_status=None)
            assert dash.status_code == 200, (
                f"New access token from refresh is not accepted by dashboard: {dash.status_code}"
            )

        async with async_step("Step 5: POST /v1/partner/auth/refresh with invalid token → 401"):
            bad = await client.token_refresh("invalid.refresh.token", expected_status=None)
            assert bad.status_code == 401, (
                f"BUG (backend): POST /v1/partner/auth/refresh"
                f" — expected: 401 (invalid refresh token must be rejected),"
                f" actual: {bad.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC008 — Logout: active session → refresh token is invalidated
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Logout - Active partner session - Refresh token is invalidated")
async def test_partner_api_auth_access_control_008(
    settings: Settings,
) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_008: Logout invalidates the refresh token."""

    email, password = require_credentials(settings.partner_email, settings.partner_password)
    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        async with async_step("Step 1: Login to obtain an active session"):
            await _partner_login(client, email, password)
            refresh_token = client.refresh_token
            assert refresh_token, "Login did not return a refresh_token — check login response schema"

        async with async_step("Step 2: POST /v1/partner/auth/logout"):
            logout_resp = await client.logout(refresh_token, expected_status=None)
            assert logout_resp.status_code == 200, (
                f"BUG (backend): POST /v1/partner/auth/logout"
                f" — expected: 200, actual: {logout_resp.status_code}"
            )

        async with async_step("Step 3: Attempt POST /v1/partner/auth/refresh with invalidated token → 401"):
            refresh_resp = await client.token_refresh(refresh_token, expected_status=None)
            assert refresh_resp.status_code == 401, (
                f"BUG (backend): POST /v1/partner/auth/refresh after logout"
                f" — expected: 401 (refresh token must be invalidated after logout),"
                f" actual: {refresh_resp.status_code}"
            )
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# TC009 — Change password: updated password revokes all sessions (P2)
# ---------------------------------------------------------------------------

@allure.epic("BlazeUp Partner Platform")
@allure.feature("Auth & Access Control")
@allure.story("Change password - Valid current credentials - Password updated and sessions revoked")
async def test_partner_api_auth_access_control_009(
    settings: Settings,
) -> None:
    """PARTNER_API_AUTH_ACCESS_CONTROL_009: Change password invalidates old credentials.

    DESTRUCTIVE TEST — changes the partner password then restores it.
    The restore step runs in a finally block to ensure cleanup even on failure.
    """

    email, password = require_credentials(settings.partner_email, settings.partner_password)
    temp_password = "TempTest@Change999"

    client = PartnerAuthClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    password_changed = False
    try:
        async with async_step("Step 1: Login with current password"):
            await _partner_login(client, email, password)

        async with async_step("Step 2: POST /v1/partner/auth/change-password"):
            change_resp = await client.change_password(
                current_password=password,
                new_password=temp_password,
                expected_status=None,
            )
            assert change_resp.status_code == 200, (
                f"BUG (backend): POST /v1/partner/auth/change-password"
                f" — expected: 200, actual: {change_resp.status_code}"
            )
            password_changed = True

        async with async_step("Step 3: Attempt login with OLD password → 401"):
            old_resp = await client.raw_login(
                {"email": email, "password": password},
                expected_status=None,
            )
            assert old_resp.status_code == 401, (
                f"BUG (backend): POST /v1/partner/auth/login with old password after change"
                f" — expected: 401, actual: {old_resp.status_code}"
            )

        async with async_step("Step 4: Login with NEW password → 200"):
            new_resp = await client.raw_login(
                {"email": email, "password": temp_password},
                expected_status=None,
            )
            assert new_resp.status_code == 200, (
                f"BUG (backend): POST /v1/partner/auth/login with new password"
                f" — expected: 200, actual: {new_resp.status_code}"
            )

    finally:
        # Always restore the original password so subsequent test runs are not broken.
        if password_changed:
            async with async_step("Restore: revert password back to original"):
                restore = PartnerAuthClient(
                    str(settings.api_base_url),
                    max_response_time_ms=settings.default_response_time_ms * 5,
                    app_origin=str(settings.base_url),
                )
                try:
                    login_ok = await restore.raw_login(
                        {"email": email, "password": temp_password},
                        expected_status=None,
                    )
                    if login_ok.status_code == 200:
                        body = login_ok.json()
                        restore.token = (
                            body.get("access_token") or body.get("accessToken") or body.get("token")
                        )
                        await restore.change_password(
                            current_password=temp_password,
                            new_password=password,
                            expected_status=None,
                        )
                finally:
                    await restore.close()
        await client.close()
