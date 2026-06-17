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

    async def list_partner_certifications(
        self,
        partner_id: str,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> PartnerListResponse:
        """GET the certifications held across a partner's team."""
        response = await self.get(
            f"{_PARTNERS_PATH}/{partner_id}/certifications", expected_status=expected_status
        )
        return PartnerListResponse.model_validate(response.json())

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
