"""Shared authentication base — domain-agnostic login mechanics.

The *mechanics* of authentication (the ``{email, password}`` payload, the token
response model, the login/logout/me calls) are identical across BlazeUp domains;
only the *endpoints* differ. So the common logic lives here once, and each domain
ships a thin subclass that sets its own paths:

    api_clients/blazeup/admin/auth_client.py    → AuthClient(BaseAuthClient)
    api_clients/blazeup/partner/auth_client.py  → PartnerAuthClient(BaseAuthClient)

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
    # Two-factor challenge: when the account has 2FA, the login call returns
    # mfaRequired=true + a challengeToken (and NO token) instead of a bearer token.
    # The caller must then POST the TOTP code + challengeToken to MFA_VERIFY_PATH.
    mfa_required: bool = Field(
        default=False, validation_alias=AliasChoices("mfaRequired", "mfa_required")
    )
    challenge_token: str | None = Field(
        default=None, validation_alias=AliasChoices("challengeToken", "challenge_token")
    )
    mfa_method: str | None = Field(
        default=None, validation_alias=AliasChoices("method", "mfa_method")
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
    MFA_VERIFY_PATH: str = ""  # set by domains whose accounts use 2FA (TOTP)
    ME_PATH: str = ""

    async def login(
        self,
        email: str,
        password: str,
        expected_status: int | tuple[int, ...] = (200, 201),
        totp_secret: str | None = None,
    ) -> LoginResponse:
        """Login at this domain's ``LOGIN_PATH`` and return a validated token response.

        When the account has two-factor auth, the login call returns
        ``mfaRequired=true`` + a ``challengeToken`` instead of a token. If
        *totp_secret* (the base32 authenticator key) is provided, this completes the
        second factor: it generates the current TOTP code with pyotp and POSTs it +
        the challengeToken to ``MFA_VERIFY_PATH`` to obtain the bearer token. Accounts
        without 2FA return a token directly and are unaffected.
        """
        if not self.LOGIN_PATH:
            raise NotImplementedError(f"{type(self).__name__} must set LOGIN_PATH")
        response = await self.post(
            self.LOGIN_PATH,
            json={"email": email, "password": password},
            expected_status=expected_status,
            schema=LoginResponse,
        )
        if response.mfa_required and response.challenge_token:
            response = await self._complete_mfa(response.challenge_token, totp_secret)
        self.token = response.bearer_token
        return response

    async def _complete_mfa(self, challenge_token: str, totp_secret: str | None) -> LoginResponse:
        """Complete a TOTP 2FA challenge and return the token-bearing response."""
        if not totp_secret:
            raise ValueError(
                f"{type(self).__name__}: login requires 2FA (TOTP) but no totp_secret was "
                "provided. Set PARTNER_TOTP_SECRET in config/<domain>/.env."
            )
        if not self.MFA_VERIFY_PATH:
            raise NotImplementedError(
                f"{type(self).__name__} must set MFA_VERIFY_PATH to complete a 2FA login"
            )
        try:
            import pyotp
        except ImportError as exc:
            raise RuntimeError(
                "This account requires 2FA (TOTP) but the 'pyotp' package is not installed. "
                "Install dependencies with `pip install -r requirements.txt` (or `pip install pyotp`)."
            ) from exc

        code = pyotp.TOTP(totp_secret.replace(" ", "")).now()
        return await self.post(
            self.MFA_VERIFY_PATH,
            json={"challengeToken": challenge_token, "code": code},
            expected_status=(200, 201),
            schema=LoginResponse,
        )

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
