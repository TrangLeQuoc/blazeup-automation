"""Shared authentication base — domain-agnostic login mechanics.

The *mechanics* of authentication (the ``{email, password}`` payload, the token
response model, the login/logout/me calls) are identical across BlazeUp domains;
only the *endpoints* differ. So the common logic lives here once, and each domain
ships a thin subclass that sets its own paths:

    api_clients/blazeup_admin/auth_client.py    → AuthClient(BaseAuthClient)
    api_clients/blazeup_partner/auth_client.py  → PartnerAuthClient(BaseAuthClient)

This keeps per-domain auth isolated (different API URL / endpoints per domain are
just config + a subclass) while avoiding duplicated login code.
"""

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api_clients.base_client import BaseClient


class LoginResponse(BaseModel):
    """JWT login response.

    Handles both envelope shapes: admin returns the token under ``data`` (BaseClient
    unwraps it when ``schema=`` is used), partner returns ``accessToken`` at the top
    level — either way ``access_token`` is populated.
    """

    model_config = ConfigDict(extra="allow")

    token: str | None = None
    access_token: str | None = Field(
        default=None, validation_alias=AliasChoices("accessToken", "access_token")
    )
    token_type: str | None = Field(
        default=None, validation_alias=AliasChoices("tokenType", "token_type")
    )

    @property
    def bearer_token(self) -> str:
        """Return whichever token field the API provides."""
        value = self.token or self.access_token
        if not value:
            raise ValueError("Login response did not contain token/accessToken")
        return value


class UserInfo(BaseModel):
    """Authenticated user payload."""

    model_config = ConfigDict(extra="allow")

    id: str | int = Field(validation_alias=AliasChoices("id", "_id"))
    email: str | None = None
    name: str | None = None


class BaseAuthClient(BaseClient):
    """Common auth flow. Subclasses set ``LOGIN_PATH`` (and ``ME_PATH`` if used)."""

    LOGIN_PATH: str = ""  # each domain's auth client must set this
    ME_PATH: str = ""

    async def login(
        self,
        email: str,
        password: str,
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> LoginResponse:
        """Login at this domain's ``LOGIN_PATH`` and return a validated token response."""
        if not self.LOGIN_PATH:
            raise NotImplementedError(f"{type(self).__name__} must set LOGIN_PATH")
        response = await self.post(
            self.LOGIN_PATH,
            json={"email": email, "password": password},
            expected_status=expected_status,
            schema=LoginResponse,
        )
        self.token = response.bearer_token
        return response

    async def logout(self, expected_status: int = 200) -> None:
        """Clear the bearer token for client-side logout tests."""
        self.token = None

    async def me(self, expected_status: int = 200) -> UserInfo:
        """Return the current authenticated user (uses this domain's ``ME_PATH``)."""
        if not self.ME_PATH:
            raise NotImplementedError(f"{type(self).__name__} must set ME_PATH to call me()")
        return await self.get(self.ME_PATH, expected_status=expected_status, schema=UserInfo)

    async def raw_login(
        self, payload: dict[str, Any], expected_status: int | tuple[int, ...] | None
    ) -> Any:
        """Submit arbitrary login payloads for negative testing (this domain's path)."""
        return await self.post(self.LOGIN_PATH, json=payload, expected_status=expected_status)
