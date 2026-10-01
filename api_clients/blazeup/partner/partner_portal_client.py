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

# <api_base_url>/sa-partners-api/v1/partner/{portal,auth,directory}/...
_PORTAL = "/sa-partners-api/v1/partner/portal"
_AUTH = "/sa-partners-api/v1/partner/auth"
# The partner org's OWN team members (PRD §4.10 "Partner Team"). The backend calls the
# segment `directory`, which reads like the SA-side list of partner ORGANISATIONS (§5.1) —
# it is not that. This surface never leaves the calling partner.
_DIRECTORY = "/sa-partners-api/v1/partner/directory/users"

_StatusArg = int | tuple[int, ...] | None


def _query(partner_id: str | None, extra: dict | None) -> dict:
    """Build the query for the per-member rollups.

    ``partner_id=None`` OMITS the parameter rather than sending an empty one — that is the
    negative case (the backend answers 400 "partnerId must be a mongodb id"), and a test must
    be able to reach it through a named method. Sending ``partnerId=`` empty would exercise a
    different rule.
    """
    query = dict(extra or {})
    if partner_id is not None:
        query["partnerId"] = partner_id
    return query


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

    async def list_commissions(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the partner's own commission ledger. Only ``status`` filters, plus paging.

        The scope is taken from the JWT twice over — the controller passes ``partner.partnerId``
        both as the query filter and as the separate scope argument — so ``partnerId`` is not a
        parameter here and sending one cannot widen the result.

        The ledger is empty on staging and stays that way: a row only accrues after a
        provisioned tenant's first payment (G1), which automation cannot trigger.
        """
        return await self.get(
            f"{_PORTAL}/commissions", params=params, expected_status=expected_status
        )

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

    async def get_modules(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the module catalogue visible to the partner.

        Query params from the spec (2026-09-17): ``name``, ``groupByCategory``, plus
        ``page``/``limit``/``sort``. Measured the same day: ``name`` narrows correctly, but
        ``groupByCategory=true`` answers rows that are only ``{"_id": "undefined"}``, and no
        pagination value is validated at all. Tracked as BUG-API-026.
        """
        return await self.get(f"{_PORTAL}/modules", params=params, expected_status=expected_status)

    async def get_team_certifications(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET every certification held by the partner's team.

        The team-wide counterpart of :meth:`get_certifications`, which returns only the
        logged-in user's own. Filters: ``status`` (active|expired|revoked),
        ``certificationType``, ``expiringWithinDays``, plus paging.
        """
        return await self.get(
            f"{_PORTAL}/team/certifications", params=params, expected_status=expected_status
        )

    async def list_clients(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the partner's own post-close tenants — "My Clients" (PRD §4.6).

        Rows come from ``partner_tenant_attribution``, so the list is empty until a won deal's
        tenant is provisioned and attributed. ``partnerId`` is taken from the JWT and is NOT a
        query parameter — the backend comment is explicit that it "never comes from the query
        string", which is why there is no partner argument here to pass one.
        """
        return await self.get(f"{_PORTAL}/clients", params=params, expected_status=expected_status)

    async def get_client(
        self,
        attribution_id: str,
        *,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET one own client by ATTRIBUTION id (not a tenant id).

        Scoped by the JWT: an attribution belonging to another partner is refused with the
        SAME 400 ``Attribution {id} not found`` as an id that does not exist at all
        (``findByIdScoped``), so a caller cannot probe for foreign ids by message.
        """
        return await self.get(
            f"{_PORTAL}/clients/{attribution_id}", expected_status=expected_status
        )

    # ── Portal: payout / bank accounts (PRD §9.3, admin-only) ────────────────

    async def list_bank_accounts(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET the partner's own payout accounts, masked.

        Every route on this controller is ADMIN-ONLY — a non-admin partner user is refused
        with 403 "Only partner admins can ...". The rows come back through
        ``toBankAccountView``, which strips ``accountNumber``/``routingNumber``/``iban`` and
        leaves only their ``*Masked`` companions.
        """
        return await self.get(f"{_PORTAL}/bank-accounts", expected_status=expected_status)

    async def add_bank_account(
        self,
        payload: dict[str, Any],
        *,
        expected_status: _StatusArg = 201,
    ) -> httpx.Response:
        """POST a payout account onto the calling partner's own profile.

        Required: ``label``, ``accountHolderName``, ``bankName``, ``countryCode``,
        ``currency``, ``payoutMethod`` (bank_transfer|swift|wise|paypal). Then per method:
        ``accountNumber``+``routingNumber``, ``iban``+``swiftBic``, or ``providerRecipientId``.
        ``isPrimary`` is a hint only — the authoritative value is decided by the atomic write.

        Sending the same account twice is REJECTED with 400 "This payout account is already on
        file for the partner"; the match is on iban, providerRecipientId, or the
        accountNumber+routingNumber pair, each normalised first.
        """
        return await self.post(
            f"{_PORTAL}/bank-accounts", json=payload, expected_status=expected_status
        )

    async def set_primary_bank_account(
        self,
        account_id: str,
        *,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """PATCH one payout account to primary — promotes it and demotes the rest atomically.

        Returns the FULL account list (masked), not just the promoted one, so a caller can
        verify the single-primary invariant in the same response.
        """
        return await self.patch(
            f"{_PORTAL}/bank-accounts/{account_id}/primary", expected_status=expected_status
        )

    async def delete_bank_account(
        self,
        account_id: str,
        *,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """DELETE a payout account, returning the remaining ones (masked).

        Removing the PRIMARY is refused with 409 while other accounts exist — promote another
        one first. The primary may only be removed when it is the last account left.
        """
        return await self.delete(
            f"{_PORTAL}/bank-accounts/{account_id}", expected_status=expected_status
        )

    # ── Portal: lookup catalogues used by the deal-registration form ─────────

    async def list_plans(self, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET every PUBLISHED standard billing plan — the deal wizard's plan picker.

        Custom/bespoke editions are excluded by the service: only ``starter``, ``pro`` and
        ``enterprise`` with ``status = published`` are returned, sorted by edition then
        billing cycle. Takes no parameters.
        """
        return await self.get(f"{_PORTAL}/plans", expected_status=expected_status)

    async def get_plan(self, plan_key: str, *, expected_status: _StatusArg = 200) -> httpx.Response:
        """GET one published billing plan.

        The route is declared ``plans/:planId`` and its ``@ApiParam`` documents a kebab-case
        slug ("e.g. pro-annual"), but the service queries ``{ _id: planId }`` — measured
        2026-09-23: the mongo ``_id`` answers 200 while the row's own ``planId`` slug answers
        400 "Invalid id". The argument is named ``plan_key`` here rather than ``plan_id``
        precisely so no caller assumes which of the two it is. Tracked as BUG-API-029.
        """
        return await self.get(f"{_PORTAL}/plans/{plan_key}", expected_status=expected_status)

    async def list_countries(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the country lookup behind the deal-registration / win-deal country picker.

        250 ISO rows shaped ``{_id, name, alpha2Code, alpha3Code}`` where ``_id`` IS the
        alpha-2 code. The optional ``search`` query matches the name partially and
        case-insensitively; a term that matches nothing is a 200 with an empty list, not a 404.
        """
        return await self.get(
            f"{_PORTAL}/countries", params=params, expected_status=expected_status
        )

    async def get_deal_stats(
        self,
        *,
        params: dict[str, Any] | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the calling partner's OWN deal-pipeline KPIs. Filters: ``status``, ``search``.

        Deliberately a narrower payload than the SA twin: ``byProvisioningState`` is SA-only
        (AC-19/AC-20) and this surface "must omit it entirely" (§2.1). Confirmed by measurement
        2026-09-24 — the Swagger example shows the field because both routes share one DTO, but
        the portal response does not carry it.
        """
        return await self.get(
            f"{_PORTAL}/deals/stats", params=params, expected_status=expected_status
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

    async def forgot_password(
        self, email: str, *, expected_status: _StatusArg = (200, 201)
    ) -> httpx.Response:
        """POST a self-service password reset for a partner user.

        Answers the SAME generic message whatever happens — "If an account exists for that
        email, we've sent password-reset instructions." — so the response cannot be used to
        discover which emails are registered. The controller is written never to branch on the
        service outcome.

        For an ELIGIBLE user (user ACTIVE and partner ACTIVE) the password is rotated
        immediately and only then mailed, so the effect IS observable without an inbox: the old
        password stops authenticating. An ineligible or unknown email is a silent no-op — no
        mail, no write, no audit.

        ⚠️ Rate limited: 5 per email and **20 per client IP** in a 15-minute window, after which
        it answers 429. The IP budget is shared by every caller behind the same address, so a
        test must spend it deliberately.
        """
        return await self.post(
            f"{_AUTH}/forgot-password", json={"email": email}, expected_status=expected_status
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

    # ── Directory: the partner org's own team (PRD §4.10) ────────────────────

    async def list_team_members(
        self,
        *,
        params: dict | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the calling partner's team members. Accepts ``page``/``limit``/``sort``."""
        return await self.get(_DIRECTORY, params=params, expected_status=expected_status)

    async def invite_team_member(
        self,
        payload: dict,
        *,
        expected_status: _StatusArg = 201,
    ) -> httpx.Response:
        """POST an invite for a new team member.

        DTO (from the OpenAPI spec, 2026-09-16): ``email``, ``firstName``, ``lastName``
        required; ``role`` (``admin``/``sales``/``finance``/``viewer``) and ``password``
        optional. The 201 body carries ``tempPassword`` — the list endpoint must not.
        """
        return await self.post(_DIRECTORY, json=payload, expected_status=expected_status)

    async def get_team_member(
        self,
        user_id: str,
        *,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET one team member by id.

        Measured 2026-09-16: the backend ignores ``user_id`` entirely and answers with some
        member of the caller's own partner — a ghost id, a malformed id and another member's
        id all return 200 with the same record. Partner scoping still holds (another partner
        gets its OWN user back, never this one), so this is wrong data rather than a leak.
        Tracked as BUG-API-022.
        """
        return await self.get(f"{_DIRECTORY}/{user_id}", expected_status=expected_status)

    async def get_team_member_deals(
        self,
        user_id: str,
        partner_id: str | None,
        *,
        params: dict | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET the deals attributed to one team member. ``partnerId`` is a REQUIRED query.

        Measured 2026-09-17: neither parameter filters. ``userId`` and ``partnerId`` are both
        validated (a missing/malformed ``partnerId`` is a 400 "must be a mongodb id") and then
        ignored — a member who registered nothing returns the partner's deals, and so does a
        ghost id. Scoping is taken from the JWT and DOES hold: another partner passing this
        partnerId gets an empty list, never these deals. Tracked as BUG-API-023.
        """
        return await self.get(
            f"{_DIRECTORY}/{user_id}/deals",
            params=_query(partner_id, params),
            expected_status=expected_status,
        )

    async def get_team_member_commissions(
        self,
        user_id: str,
        partner_id: str | None,
        *,
        params: dict | None = None,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """GET one team member's commission rows. ``partnerId`` is a REQUIRED query.

        An empty ledger is legitimate. Winning a deal does NOT earn a commission: since the v1
        cutover the row accrues from the payment-gateway trigger once the provisioned tenant's
        first payment succeeds, attributed by ``wonTenantId`` and anchored on ``goLiveAt``.
        """
        return await self.get(
            f"{_DIRECTORY}/{user_id}/commissions",
            params=_query(partner_id, params),
            expected_status=expected_status,
        )

    async def reset_team_member_password(
        self,
        user_id: str,
        *,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """POST a password reset for a team member. Use a throwaway member, never a shared one."""
        return await self.post(
            f"{_DIRECTORY}/{user_id}/reset-password", expected_status=expected_status
        )

    async def unlock_team_member(
        self,
        user_id: str,
        *,
        expected_status: _StatusArg = 200,
    ) -> httpx.Response:
        """POST an unlock for a locked-out team member."""
        return await self.post(f"{_DIRECTORY}/{user_id}/unlock", expected_status=expected_status)
