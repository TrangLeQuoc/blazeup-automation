"""Partner Platform authentication and session API client."""

from typing import Any

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api.base_client import BaseClient


class PartnerLoginResponse(BaseModel):
    """Partner login/refresh token response."""

    model_config = ConfigDict(extra="allow")

    access_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("accessToken", "access_token", "token"),
    )
    refresh_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("refreshToken", "refresh_token"),
    )
    expires_at: str | int | None = Field(
        default=None,
        validation_alias=AliasChoices("expiresAt", "expires_at", "expiresIn", "expires_in"),
    )

    @property
    def bearer_token(self) -> str:
        """Return the access token or raise if absent."""
        value = self.access_token
        if not value:
            raise ValueError("Partner login response did not contain access_token")
        return value


class PartnerAuthClient(BaseClient):
    """Client for Partner Platform auth endpoints (/v1/partner/auth/*)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Cached after login() / token_refresh() — needed for logout and refresh TCs.
        self.refresh_token: str | None = None

    # ------------------------------------------------------------------
    # Auth lifecycle
    # ------------------------------------------------------------------

    async def login(
        self,
        email: str,
        password: str,
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> PartnerLoginResponse:
        """POST /v1/partner/auth/login — authenticate and cache access + refresh tokens."""
        response = await self.post(
            "/v1/partner/auth/login",
            json={"email": email, "password": password},
            expected_status=expected_status,
            schema=PartnerLoginResponse,
        )
        self.token = response.bearer_token
        self.refresh_token = response.refresh_token
        return response

    async def raw_login(
        self,
        payload: dict[str, Any],
        expected_status: int | tuple[int, ...] | None,
    ) -> httpx.Response:
        """POST /v1/partner/auth/login with arbitrary payload (negative tests)."""
        return await self.post(
            "/v1/partner/auth/login",
            json=payload,
            expected_status=expected_status,
        )

    async def token_refresh(
        self,
        refresh_token: str,
        expected_status: int | tuple[int, ...] | None = 200,
    ) -> httpx.Response:
        """POST /v1/partner/auth/refresh — exchange a refresh token for a new access token."""
        return await self.post(
            "/v1/partner/auth/refresh",
            json={"refresh_token": refresh_token},
            expected_status=expected_status,
        )

    async def logout(
        self,
        refresh_token: str,
        expected_status: int | tuple[int, ...] = 200,
    ) -> httpx.Response:
        """POST /v1/partner/auth/logout — invalidate the partner session."""
        return await self.post(
            "/v1/partner/auth/logout",
            json={"refresh_token": refresh_token},
            expected_status=expected_status,
        )

    async def change_password(
        self,
        current_password: str,
        new_password: str,
        expected_status: int | tuple[int, ...] | None = 200,
    ) -> httpx.Response:
        """POST /v1/partner/auth/change-password."""
        return await self.post(
            "/v1/partner/auth/change-password",
            json={"current_password": current_password, "new_password": new_password},
            expected_status=expected_status,
        )

    # ------------------------------------------------------------------
    # Partner-scoped resources
    # ------------------------------------------------------------------

    async def dashboard(
        self,
        expected_status: int | tuple[int, ...] | None = 200,
    ) -> httpx.Response:
        """GET /v1/partner/dashboard — partner-scoped KPI dashboard."""
        return await self.get("/v1/partner/dashboard", expected_status=expected_status)

    async def partner_data(
        self,
        partner_id: str,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """GET /v1/partner/{partnerId}/dashboard — explicit partner-scoped endpoint.

        Used in cross-partner isolation tests (TC003): Partner A's JWT should be
        rejected (403) when attempting to access Partner B's data via URL.
        """
        return await self.get(f"/v1/partner/{partner_id}/dashboard", expected_status=expected_status)

    # ------------------------------------------------------------------
    # Role-restricted resources (MSP guard tests TC005 / TC006)
    # ------------------------------------------------------------------

    async def payroll(
        self,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """GET /v1/partner/payroll — payroll data restricted to full-access partners.

        MSP-role partners should receive 403 Forbidden.
        Endpoint path should be confirmed against the finalized API contract.
        """
        return await self.get("/v1/partner/payroll", expected_status=expected_status)

    async def export_employees(
        self,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """GET /v1/partner/employees/export — employee record export restricted to full-access partners.

        MSP-role partners should receive 403 Forbidden.
        Endpoint path should be confirmed against the finalized API contract.
        """
        return await self.get("/v1/partner/employees/export", expected_status=expected_status)

    # ------------------------------------------------------------------
    # MFA-protected actions (TC004)
    # ------------------------------------------------------------------

    async def mfa_protected_action(
        self,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """POST /v1/partner/admin/security/settings — example MFA-protected admin endpoint.

        Called without a valid MFA OTP to verify the server enforces MFA policy
        (expected: 403 Forbidden or 428 Precondition Required).
        Endpoint path and required payload must be confirmed against the API contract.
        """
        return await self.post(
            "/v1/partner/admin/security/settings",
            json={},
            expected_status=expected_status,
        )
