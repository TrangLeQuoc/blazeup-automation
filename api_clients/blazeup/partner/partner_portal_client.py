"""Partner Portal API client + auth endpoints (service: sa-partners-api).

The partner-portal surface (``/sa-partners-api/v1/partner/*``) needs a PARTNER
user's JWT, not the SA admin token. Sessions are minted SA-side by
``utils.partner_portal.mint_partner_session``, which returns one of these clients
already carrying the token.

Why this class exists: the paths used to be re-declared in four test modules under
three different names (``_BASE``, ``_PORTAL``, ``_DASHBOARD_PATH``) plus once inline in
a UI test, because there was no client for this surface — only an unwired scaffold.
Same value, five places. The paths now live here only, and tests call methods.

Every method forwards ``expected_status`` so the same method serves the positive case
(``expected_status=200``) and the negative one (``expected_status=None`` → return the
raw response and let the test assert the code). That is why there is no separate
``raw_*`` twin for each endpoint.

Usage in a test::

    portal, pid, uid = await mint_partner_session(sa_partners_client, settings)
    created_resources.add(lambda: portal.close())
    resp = await portal.get_dashboard()
    deals = await portal.list_deals(params={"limit": 20})
"""

from typing import Any

import httpx

from api_clients.base_client import BaseClient

# <api_base_url>/sa-partners-api/v1/partner/{portal,auth}/...
_PORTAL = "/sa-partners-api/v1/partner/portal"
_AUTH = "/sa-partners-api/v1/partner/auth"

_StatusArg = int | tuple[int, ...] | None


class PartnerPortalClient(BaseClient):
    """Client for the partner-portal + partner-auth endpoints (sa-partners-api)."""

    # Exposed for the ONE case that cannot use a method: a test proving a NON-partner
    # client (SA admin token) is rejected on a partner endpoint. It hits the path with
    # a different client class, so it needs the path — but still not a literal of its
    # own. See test_sa_auth_access_control.py (non-partner token → 401).
    AUTH_ME_PATH = f"{_AUTH}/me"

    # ── Portal: read-only pages ──────────────────────────────────────────────

    async def get_profile(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the logged-in partner's own profile."""
        return await self.get(f"{_PORTAL}/profile", expected_status=expected_status)

    async def get_dashboard(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the partner dashboard aggregate (tier, ARR, deal/win counts)."""
        return await self.get(f"{_PORTAL}/dashboard", expected_status=expected_status)

    async def get_commissions_summary(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the partner's own commission summary."""
        return await self.get(f"{_PORTAL}/commissions/summary", expected_status=expected_status)

    async def get_territories(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the territories assigned to the partner."""
        return await self.get(f"{_PORTAL}/territories", expected_status=expected_status)

    async def get_rates(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the commission rates visible to the partner."""
        return await self.get(f"{_PORTAL}/rates", expected_status=expected_status)

    async def get_certifications(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the partner's own certifications (``params`` for paging/filters)."""
        return await self.get(
            f"{_PORTAL}/certifications", params=params, expected_status=expected_status
        )

    async def check_domain(
        self, domain: str, *, expected_status: _StatusArg = 200
    ) -> httpx.Response:
        """GET whether a subdomain label is still available.

        ``data.available`` is False when another active deal already reserved it — the
        signal the register wizard turns into its inline conflict warning.
        """
        return await self.get(
            f"{_PORTAL}/check-domain", params={"domain": domain}, expected_status=expected_status
        )

    # ── Portal: the partner's own deals ──────────────────────────────────────

    async def register_deal(
        self, body: dict[str, Any], *, expected_status: _StatusArg = (200, 201)
    ) -> httpx.Response:
        """POST a new deal registration as the logged-in partner."""
        return await self.post(f"{_PORTAL}/deals", json=body, expected_status=expected_status)

    async def list_deals(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the partner's OWN deals (``params`` for paging / status filter)."""
        return await self.get(f"{_PORTAL}/deals", params=params, expected_status=expected_status)

    async def get_deal(self, deal_id: str, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET one of the partner's own deals by id (tenant-scoped by the BE)."""
        return await self.get(f"{_PORTAL}/deals/{deal_id}", expected_status=expected_status)

    # ── Partner auth ─────────────────────────────────────────────────────────

    async def me(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the identity behind the current token."""
        return await self.get(self.AUTH_ME_PATH, expected_status=expected_status)

    async def login(
        self, email: str, password: str, *, expected_status: _StatusArg = (200, 201)
    ) -> httpx.Response:
        """POST the partner login (``PartnerLoginDto``) → accessToken + refreshToken."""
        return await self.post(
            f"{_AUTH}/login",
            json={"email": email, "password": password},
            expected_status=expected_status,
        )

    async def refresh(
        self, refresh_token: str, *, expected_status: _StatusArg = 200
    ) -> httpx.Response:
        """POST a refresh token → a new access token."""
        return await self.post(
            f"{_AUTH}/refresh",
            json={"refreshToken": refresh_token},
            expected_status=expected_status,
        )

    async def logout(self, *, expected_status: _StatusArg = (200, 204)) -> httpx.Response:
        """POST logout — invalidates the session's refresh token."""
        return await self.post(f"{_AUTH}/logout", json={}, expected_status=expected_status)

    async def change_password(
        self,
        current_password: str,
        new_password: str,
        *,
        expected_status: _StatusArg = (200, 204),
    ) -> httpx.Response:
        """POST a password change for the logged-in partner user."""
        return await self.post(
            f"{_AUTH}/change-password",
            json={"currentPassword": current_password, "newPassword": new_password},
            expected_status=expected_status,
        )
