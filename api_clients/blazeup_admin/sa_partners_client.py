"""SA Partners API client + response schemas (service: sa-partners-api).

Endpoints here are the SA-side partner management APIs documented in the
``sa-partners-api`` Swagger (e.g. ``GET /v1/sa/partners``). Authentication uses
the same SA bearer token as the rest of the admin domain.
"""

from typing import Any

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api_clients.base_client import BaseClient

# Full gateway path (service prefix + route). BaseClient strips the leading "/"
# and appends to api_base_url, so the final URL is
# <api_base_url>/sa-partners-api/v1/sa/partners.
_PARTNERS_PATH = "/sa-partners-api/v1/sa/partners"
_PARTNER_USERS_PATH = "/sa-partners-api/v1/sa/partner-users"
_CERTIFICATIONS_PATH = "/sa-partners-api/v1/sa/certifications"  # SA-wide cert list
_TERRITORIES_PATH = "/sa-partners-api/v1/sa/territories"


class PartnerListResponse(BaseModel):
    """Envelope returned by ``GET /v1/sa/partners``.

    Shape (observed): ``{"statusCode": 200, "data": [...], "total": N, "message": "..."}``.
    ``extra="allow"`` keeps the model forward-compatible if the API adds fields.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    status_code: int | None = Field(
        default=None, validation_alias=AliasChoices("statusCode", "status_code")
    )
    data: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None
    message: str | None = None


class PartnerWriteResponse(BaseModel):
    """Envelope returned by write endpoints (POST/PATCH/DELETE on partners).

    Shape (observed on create): ``{"statusCode": 200, "data": {...partner...},
    "message": "Partner created successfully"}``. Note the HTTP status is 201 on
    create while the *body* ``statusCode`` is 200 — assert the two separately.
    ``data`` carries the persisted record (``_id``, ``code`` e.g. "PAR-243212",
    ``status`` e.g. "pending", ``tier`` e.g. "registered", ...).
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    status_code: int | None = Field(
        default=None, validation_alias=AliasChoices("statusCode", "status_code")
    )
    data: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None

    @property
    def partner_id(self) -> "str | None":
        """The created/updated partner's id (the API uses ``_id``)."""
        return self.data.get("_id") or self.data.get("id")


class SaPartnersClient(BaseClient):
    """Client for SA-side partner management endpoints (sa-partners-api)."""

    async def list_partners(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        expected_status: int | tuple[int, ...] = 200,
        **filters: Any,
    ) -> PartnerListResponse:
        """GET the SA partner list and return the validated envelope.

        Note: we do NOT pass ``schema=`` to ``get()`` because BaseClient would
        unwrap the ``data`` key and validate the inner list instead of the
        envelope — here we want the whole envelope, so we validate it ourselves.
        """
        params: dict[str, Any] = {"page": page, "limit": limit}
        params.update({k: v for k, v in filters.items() if v is not None})
        response = await self.get(_PARTNERS_PATH, params=params, expected_status=expected_status)
        return PartnerListResponse.model_validate(response.json())

    async def raw_list_partners(
        self, expected_status: int | tuple[int, ...] | None = None, **params: Any
    ) -> httpx.Response:
        """Raw GET for negative tests — arbitrary params, no schema validation."""
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.get(_PARTNERS_PATH, params=clean, expected_status=expected_status)

    async def create_partner(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] = 201,
    ) -> PartnerWriteResponse:
        """POST a new partner and return the validated write envelope.

        Defaults to asserting HTTP 201 (the create success code). As with the
        list endpoint we validate the envelope ourselves (no ``schema=``) so the
        wrapper keys (statusCode/data/message) are preserved.
        """
        response = await self.post(_PARTNERS_PATH, json=payload, expected_status=expected_status)
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_create_partner(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST for negative tests — arbitrary payload, no schema validation.

        On 400 the body is ``{"statusCode":400, "message":[...], "error":...}``
        (``message`` is a list of field errors), which doesn't fit the success
        envelope — callers inspect the raw response themselves.
        """
        return await self.post(_PARTNERS_PATH, json=payload, expected_status=expected_status)

    async def approve_partner(
        self,
        partner_id: str,
        *,
        expected_status: int | tuple[int, ...] = 201,
    ) -> PartnerWriteResponse:
        """POST approve a pending partner application (no request body).

        On success the partner transitions ``pending`` → ``active`` and the
        record gains ``approvedAt`` + ``approvedBy``. HTTP is 201 while the body
        ``statusCode`` is 200 (same pattern as create).
        """
        response = await self.post(
            f"{_PARTNERS_PATH}/{partner_id}/approve", json={}, expected_status=expected_status
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_approve_partner(
        self,
        partner_id: str,
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST approve for negative tests — returns the response unvalidated."""
        return await self.post(
            f"{_PARTNERS_PATH}/{partner_id}/approve", json={}, expected_status=expected_status
        )

    async def delete_partner(
        self,
        partner_id: str,
        *,
        expected_status: int | tuple[int, ...] = (200, 204),
    ) -> httpx.Response:
        """DELETE a partner by id — used for test cleanup."""
        return await self.delete(f"{_PARTNERS_PATH}/{partner_id}", expected_status=expected_status)

    async def get_partner(
        self,
        partner_id: str,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerWriteResponse:
        """GET a single partner by id (same envelope shape as create)."""
        response = await self.get(f"{_PARTNERS_PATH}/{partner_id}", expected_status=expected_status)
        return PartnerWriteResponse.model_validate(response.json())

    async def deactivate_partner(
        self,
        partner_id: str,
        *,
        reason: str | None = None,
        expected_status: int | tuple[int, ...] | None = 201,
    ) -> httpx.Response:
        """POST deactivate / decline a partner (``reason`` optional in the body).

        BE has no dedicated ``decline`` endpoint; declining/suspending a partner
        is done here. ``reason`` is sent only when provided so negative tests can
        probe whether the API enforces it. ``expected_status=None`` skips the
        status assertion (for negative cases that inspect the raw response).
        """
        body: dict[str, Any] = {} if reason is None else {"reason": reason}
        return await self.post(
            f"{_PARTNERS_PATH}/{partner_id}/deactivate",
            json=body,
            expected_status=expected_status,
        )

    async def change_tier(
        self,
        partner_id: str,
        *,
        tier: str,
        reason: str | None = None,
        expected_status: int | tuple[int, ...] = 201,
    ) -> PartnerWriteResponse:
        """POST upgrade/downgrade a partner tier (``tier`` ∈ registered/select/advanced/premier).

        On success the partner's ``tier`` changes and a ``partner.tier.changed``
        event is recorded (before/after tiers). HTTP 201 / body statusCode 200.
        """
        body: dict[str, Any] = {"tier": tier}
        if reason is not None:
            body["reason"] = reason
        response = await self.post(
            f"{_PARTNERS_PATH}/{partner_id}/upgrade-tier",
            json=body,
            expected_status=expected_status,
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_change_tier(
        self,
        partner_id: str,
        *,
        tier: str | None = None,
        reason: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST upgrade-tier for negative tests — omit ``tier`` to probe required-field handling.

        On 400 the body's ``message`` is a list of field errors, so callers
        inspect the raw response themselves (no envelope validation).
        """
        body: dict[str, Any] = {}
        if tier is not None:
            body["tier"] = tier
        if reason is not None:
            body["reason"] = reason
        return await self.post(
            f"{_PARTNERS_PATH}/{partner_id}/upgrade-tier",
            json=body,
            expected_status=expected_status,
        )

    async def list_partner_users(
        self,
        *,
        partner_id: str | None = None,
        page: int = 1,
        limit: int = 20,
        expected_status: int | tuple[int, ...] = 200,
        **filters: Any,
    ) -> PartnerListResponse:
        """GET the SA partner-portal users list (optionally filtered by ``partner_id``)."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if partner_id is not None:
            params["partnerId"] = partner_id
        params.update({k: v for k, v in filters.items() if v is not None})
        response = await self.get(
            _PARTNER_USERS_PATH, params=params, expected_status=expected_status
        )
        return PartnerListResponse.model_validate(response.json())

    async def raw_list_partner_users(
        self, expected_status: int | tuple[int, ...] | None = None, **params: Any
    ) -> httpx.Response:
        """Raw GET partner-users for negative tests — arbitrary params, no schema validation."""
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.get(_PARTNER_USERS_PATH, params=clean, expected_status=expected_status)

    async def invite_partner_user(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] = 201,
    ) -> PartnerWriteResponse:
        """POST invite a partner-portal user. Response ``data`` carries ``userId``."""
        response = await self.post(
            _PARTNER_USERS_PATH, json=payload, expected_status=expected_status
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_invite_partner_user(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST invite for negative/idempotency tests — arbitrary payload, no validation."""
        return await self.post(_PARTNER_USERS_PATH, json=payload, expected_status=expected_status)

    async def reset_partner_user_password(
        self,
        user_id: str,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerWriteResponse:
        """POST reset a partner-portal user's password — issues a fresh ``tempPassword``."""
        response = await self.post(
            f"{_PARTNER_USERS_PATH}/{user_id}/reset-password",
            json={},
            expected_status=expected_status,
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_reset_partner_user_password(
        self,
        user_id: str,
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST reset-password for negative tests — returns the response unvalidated."""
        return await self.post(
            f"{_PARTNER_USERS_PATH}/{user_id}/reset-password",
            json={},
            expected_status=expected_status,
        )

    async def grant_certification(
        self,
        user_id: str,
        *,
        certification_type: str,
        score: int | None = None,
        external_cert_id: str | None = None,
        expected_status: int | tuple[int, ...] = 201,
    ) -> PartnerWriteResponse:
        """POST grant/renew a certification to a partner user ("certification earned").

        ``certification_type`` ∈ sales_certified / hr_specialist / crm_specialist /
        implementation_certified. On success the cert is ``active`` with
        ``earnedAt`` + ``expiresAt`` and a ``partner.certification.granted`` event.
        """
        body: dict[str, Any] = {"certificationType": certification_type}
        if score is not None:
            body["score"] = score
        if external_cert_id is not None:
            body["externalCertId"] = external_cert_id
        response = await self.post(
            f"{_PARTNER_USERS_PATH}/{user_id}/certifications",
            json=body,
            expected_status=expected_status,
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_grant_certification(
        self,
        user_id: str,
        *,
        certification_type: str | None = None,
        score: int | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST grant-certification for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {}
        if certification_type is not None:
            body["certificationType"] = certification_type
        if score is not None:
            body["score"] = score
        return await self.post(
            f"{_PARTNER_USERS_PATH}/{user_id}/certifications",
            json=body,
            expected_status=expected_status,
        )

    async def revoke_certification(
        self,
        user_id: str,
        certification_type: str,
        *,
        reason: str,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerWriteResponse:
        """DELETE revoke a partner user's certification (body ``{reason}`` required).

        Soft-revoke: the cert stays on the record with ``status='revoked'``. HTTP 200.
        """
        response = await self.delete(
            f"{_PARTNER_USERS_PATH}/{user_id}/certifications/{certification_type}",
            json={"reason": reason},
            expected_status=expected_status,
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_revoke_certification(
        self,
        user_id: str,
        certification_type: str,
        *,
        reason: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw DELETE revoke-cert for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {} if reason is None else {"reason": reason}
        return await self.delete(
            f"{_PARTNER_USERS_PATH}/{user_id}/certifications/{certification_type}",
            json=body,
            expected_status=expected_status,
        )

    async def list_partner_certifications(
        self,
        partner_id: str,
        *,
        page: int = 1,
        limit: int = 20,
        expected_status: int | tuple[int, ...] = 200,
        **filters: Any,
    ) -> PartnerListResponse:
        """GET the certifications held across a partner's team (status/type/expiring filters)."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        params.update({k: v for k, v in filters.items() if v is not None})
        response = await self.get(
            f"{_PARTNERS_PATH}/{partner_id}/certifications",
            params=params,
            expected_status=expected_status,
        )
        return PartnerListResponse.model_validate(response.json())

    async def raw_list_partner_certifications(
        self,
        partner_id: str,
        expected_status: int | tuple[int, ...] | None = None,
        **params: Any,
    ) -> httpx.Response:
        """Raw GET partner certifications for negative tests — arbitrary params, no validation."""
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.get(
            f"{_PARTNERS_PATH}/{partner_id}/certifications",
            params=clean,
            expected_status=expected_status,
        )

    async def list_certifications(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        expected_status: int | tuple[int, ...] = 200,
        **filters: Any,
    ) -> PartnerListResponse:
        """GET the SA-wide certifications list (filters: status/certificationType/expiringWithinDays)."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        params.update({k: v for k, v in filters.items() if v is not None})
        response = await self.get(
            _CERTIFICATIONS_PATH, params=params, expected_status=expected_status
        )
        return PartnerListResponse.model_validate(response.json())

    async def raw_list_certifications(
        self, expected_status: int | tuple[int, ...] | None = None, **params: Any
    ) -> httpx.Response:
        """Raw GET SA-wide certifications for negative tests — arbitrary params, no validation."""
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.get(_CERTIFICATIONS_PATH, params=clean, expected_status=expected_status)

    async def assign_territory(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] = 201,
    ) -> PartnerWriteResponse:
        """POST assign a territory to a partner (``CreateTerritoryDto``). Response data carries ``_id``."""
        response = await self.post(_TERRITORIES_PATH, json=payload, expected_status=expected_status)
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_assign_territory(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST assign-territory for negative/conflict tests — no validation."""
        return await self.post(_TERRITORIES_PATH, json=payload, expected_status=expected_status)

    async def list_territories(
        self,
        *,
        partner_id: str | None = None,
        page: int = 1,
        limit: int = 20,
        expected_status: int | tuple[int, ...] = 200,
        **filters: Any,
    ) -> PartnerListResponse:
        """GET the SA territories list (filters: partnerId/country/exclusivityType)."""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if partner_id is not None:
            params["partnerId"] = partner_id
        params.update({k: v for k, v in filters.items() if v is not None})
        response = await self.get(_TERRITORIES_PATH, params=params, expected_status=expected_status)
        return PartnerListResponse.model_validate(response.json())

    async def raw_list_territories(
        self, expected_status: int | tuple[int, ...] | None = None, **params: Any
    ) -> httpx.Response:
        """Raw GET territories for negative tests — arbitrary params, no validation."""
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.get(_TERRITORIES_PATH, params=clean, expected_status=expected_status)

    async def get_territory(
        self,
        territory_id: str,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerWriteResponse:
        """GET a single territory by id."""
        response = await self.get(
            f"{_TERRITORIES_PATH}/{territory_id}", expected_status=expected_status
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_get_territory(
        self,
        territory_id: str,
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw GET territory by id for negative tests — returns the response unvalidated."""
        return await self.get(
            f"{_TERRITORIES_PATH}/{territory_id}", expected_status=expected_status
        )

    async def delete_territory(
        self,
        territory_id: str,
        *,
        expected_status: int | tuple[int, ...] | None = (200, 204),
    ) -> httpx.Response:
        """DELETE remove a territory assignment by id (also used for test cleanup)."""
        return await self.delete(
            f"{_TERRITORIES_PATH}/{territory_id}", expected_status=expected_status
        )

    async def list_audit_logs(
        self,
        *,
        limit: int = 20,
        expected_status: int | tuple[int, ...] = 200,
        **filters: Any,
    ) -> PartnerListResponse:
        """GET SA audit logs (same envelope as the partner list)."""
        params: dict[str, Any] = {"limit": limit}
        params.update({k: v for k, v in filters.items() if v is not None})
        response = await self.get(
            "/sa-partners-api/v1/sa/audit-logs", params=params, expected_status=expected_status
        )
        return PartnerListResponse.model_validate(response.json())

    async def raw_list_audit_logs(
        self, expected_status: int | tuple[int, ...] | None = None, **params: Any
    ) -> httpx.Response:
        """Raw GET audit-logs for negative tests — arbitrary params, no schema validation.

        On 400 the body's ``message`` is a list of field errors (doesn't fit the
        success envelope), so callers inspect the raw response themselves.
        """
        clean = {k: v for k, v in params.items() if v is not None}
        return await self.get(
            "/sa-partners-api/v1/sa/audit-logs", params=clean, expected_status=expected_status
        )

    async def get_audit_log_stats(
        self,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerWriteResponse:
        """GET SA audit-log KPI stats — 24h counters + chain integrity (data is an object)."""
        response = await self.get(
            "/sa-partners-api/v1/sa/audit-logs/stats", expected_status=expected_status
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def export_audit_logs(
        self,
        *,
        format: str | None = None,
        expected_status: int | tuple[int, ...] | None = 200,
        **filters: Any,
    ) -> httpx.Response:
        """GET export the SA audit log (``format`` csv|json, default csv).

        Returns the raw response: the body is a file (CSV text or a JSON array),
        NOT the standard envelope — callers inspect ``content-type`` + body. Omit
        ``format`` to exercise the server default; pass ``expected_status=None`` for
        negative cases (invalid format/filter) that inspect the raw error.
        """
        params = {k: v for k, v in {"format": format, **filters}.items() if v is not None}
        return await self.get(
            "/sa-partners-api/v1/sa/audit-logs/export",
            params=params,
            expected_status=expected_status,
        )

    async def get_audit_log(
        self,
        log_id: str,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerWriteResponse:
        """GET a single audit-log entry by id (envelope with the full entry in ``data``)."""
        response = await self.get(
            f"/sa-partners-api/v1/sa/audit-logs/{log_id}", expected_status=expected_status
        )
        return PartnerWriteResponse.model_validate(response.json())

    async def raw_get_audit_log(
        self,
        log_id: str,
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw GET audit-log by id for negative tests — returns the response unvalidated."""
        return await self.get(
            f"/sa-partners-api/v1/sa/audit-logs/{log_id}", expected_status=expected_status
        )
