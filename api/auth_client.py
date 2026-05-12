"""Authentication API client and response schemas."""

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api.base_client import BaseClient


class LoginResponse(BaseModel):
    """JWT login response."""

    model_config = ConfigDict(extra="allow")

    token: str | None = None
    access_token: str | None = Field(default=None, validation_alias=AliasChoices("accessToken", "access_token"))
    token_type: str | None = Field(default=None, validation_alias=AliasChoices("tokenType", "token_type"))

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

    id: str | int
    email: str | None = None
    name: str | None = None


class AuthClient(BaseClient):
    """Client for authentication endpoints."""

    async def login(self, email: str, password: str, expected_status: int = 200) -> LoginResponse:
        """Login and return a validated token response."""

        return await self.post(
            "/auth/login",
            json={"email": email, "password": password},
            expected_status=expected_status,
            schema=LoginResponse,
        )

    async def logout(self, expected_status: int = 200) -> None:
        """Revoke the current token."""

        await self.post("/auth/logout", expected_status=expected_status)

    async def me(self, expected_status: int = 200) -> UserInfo:
        """Return the current authenticated user."""

        return await self.get("/auth/me", expected_status=expected_status, schema=UserInfo)

    async def raw_login(self, payload: dict[str, Any], expected_status: int | tuple[int, ...]) -> Any:
        """Submit arbitrary login payloads for negative testing."""

        return await self.post("/auth/login", json=payload, expected_status=expected_status)
