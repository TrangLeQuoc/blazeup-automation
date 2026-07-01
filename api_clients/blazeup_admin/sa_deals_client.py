"""SA Deals API client + response schemas (service: sa-partners-api).

SA-side deal-registration & pipeline endpoints under ``/v1/sa/deals``. Registering
a deal needs a ``planId`` from the billing-plan catalog (sa-plans-api), so a small
read-only helper to pick a published plan lives here too.

Maps to the Partner Platform test plan: PARTNER_API_DEAL_REGISTRATION_PIPELINE_*.
"""

from typing import Any

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api_clients.base_client import BaseClient

_DEALS_PATH = "/sa-partners-api/v1/sa/deals"
_BILLING_PLANS_PATH = "/sa-plans-api/v1/billing-plans"  # read-only catalog (sa-plans-api)


class DealWriteResponse(BaseModel):
    """Envelope for deal write endpoints: ``{statusCode, data:{...deal...}, message}``.

    ``data`` carries the persisted deal (``_id``, ``status`` e.g. "registered",
    ``dealType``, ``protectionExpiresAt``, ``conflictStatus``, ...). HTTP is 201
    on register while the body ``statusCode`` is 200 (same pattern as partners).
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    status_code: int | None = Field(
        default=None, validation_alias=AliasChoices("statusCode", "status_code")
    )
    data: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None

    @property
    def deal_id(self) -> "str | None":
        return self.data.get("_id") or self.data.get("id")


class SaDealsClient(BaseClient):
    """Client for SA-side deal-registration & pipeline endpoints (sa-partners-api)."""

    async def pick_billing_plan_id(self, *, expected_status: int | tuple[int, ...] = 200) -> str:
        """Return a published billing plan's id — needed to register a deal.

        Reads the billing-plan catalog (sa-plans-api). Prefers a ``published``
        plan; falls back to the first plan returned.
        """
        response = await self.get(
            _BILLING_PLANS_PATH, params={"limit": 20}, expected_status=expected_status
        )
        plans = response.json().get("data") or []
        if not plans:
            raise RuntimeError("no billing plans available to register a deal")
        published = next((p for p in plans if p.get("status") == "published"), plans[0])
        plan_id = published.get("planId") or published.get("_id")
        if not plan_id:
            raise RuntimeError(
                f"billing plan has no planId/_id to register a deal with: {published!r}"
            )
        return plan_id

    async def raw_get_billing_plan(
        self,
        plan_id: str,
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """GET a billing plan by id (sa-plans-api) — used to prove a planId is absent."""
        return await self.get(f"{_BILLING_PLANS_PATH}/{plan_id}", expected_status=expected_status)

    async def register_deal(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] = 201,
    ) -> DealWriteResponse:
        """POST register a new partner deal."""
        response = await self.post(_DEALS_PATH, json=payload, expected_status=expected_status)
        return DealWriteResponse.model_validate(response.json())

    async def raw_register_deal(
        self,
        payload: dict[str, Any],
        *,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST register for negative tests — no schema validation."""
        return await self.post(_DEALS_PATH, json=payload, expected_status=expected_status)

    async def get_deal(
        self,
        deal_id: str,
        *,
        expected_status: int | tuple[int, ...] = 200,
    ) -> DealWriteResponse:
        """GET a single deal by id."""
        response = await self.get(f"{_DEALS_PATH}/{deal_id}", expected_status=expected_status)
        return DealWriteResponse.model_validate(response.json())

    async def approve_deal(
        self,
        deal_id: str,
        *,
        review_notes: str | None = None,
        expected_status: int | tuple[int, ...] = 201,
    ) -> DealWriteResponse:
        """POST approve a registered deal (body ``ReviewDealDto{reviewNotes}``, optional).

        On success the deal transitions ``registered`` → ``approved`` and stamps
        ``reviewedAt`` + ``reviewedBy``. HTTP 201 / body statusCode 200.
        """
        body: dict[str, Any] = {} if review_notes is None else {"reviewNotes": review_notes}
        response = await self.post(
            f"{_DEALS_PATH}/{deal_id}/approve", json=body, expected_status=expected_status
        )
        return DealWriteResponse.model_validate(response.json())

    async def raw_approve_deal(
        self,
        deal_id: str,
        *,
        review_notes: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST approve for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {} if review_notes is None else {"reviewNotes": review_notes}
        return await self.post(
            f"{_DEALS_PATH}/{deal_id}/approve", json=body, expected_status=expected_status
        )

    async def extend_protection(
        self,
        deal_id: str,
        *,
        added_days: int,
        reasoning: str,
        expected_status: int | tuple[int, ...] = 201,
    ) -> DealWriteResponse:
        """POST manually extend a deal's protection window (SA action + reasoning).

        Body ``ExtendProtectionDto{addedDays, reasoning}`` (both required). On
        success the deal's ``protectionExpiresAt`` is pushed out by ``addedDays``.
        HTTP 201 / body statusCode 200 (same pattern as the other deal writes).
        """
        response = await self.post(
            f"{_DEALS_PATH}/{deal_id}/extend-protection",
            json={"addedDays": added_days, "reasoning": reasoning},
            expected_status=expected_status,
        )
        return DealWriteResponse.model_validate(response.json())

    async def raw_extend_protection(
        self,
        deal_id: str,
        *,
        added_days: int | None = None,
        reasoning: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST extend-protection for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {}
        if added_days is not None:
            body["addedDays"] = added_days
        if reasoning is not None:
            body["reasoning"] = reasoning
        return await self.post(
            f"{_DEALS_PATH}/{deal_id}/extend-protection", json=body, expected_status=expected_status
        )

    async def reject_deal(
        self,
        deal_id: str,
        *,
        review_notes: str | None = None,
        expected_status: int | tuple[int, ...] = 201,
    ) -> DealWriteResponse:
        """POST reject a registered deal (body ``ReviewDealDto{reviewNotes}``, optional).

        On success the deal transitions ``registered`` → ``rejected``. HTTP 201.
        """
        body: dict[str, Any] = {} if review_notes is None else {"reviewNotes": review_notes}
        response = await self.post(
            f"{_DEALS_PATH}/{deal_id}/reject", json=body, expected_status=expected_status
        )
        return DealWriteResponse.model_validate(response.json())

    async def raw_reject_deal(
        self,
        deal_id: str,
        *,
        review_notes: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST reject for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {} if review_notes is None else {"reviewNotes": review_notes}
        return await self.post(
            f"{_DEALS_PATH}/{deal_id}/reject", json=body, expected_status=expected_status
        )

    async def lose_deal(
        self,
        deal_id: str,
        *,
        notes: str | None = None,
        expected_status: int | tuple[int, ...] = 201,
    ) -> DealWriteResponse:
        """POST mark an APPROVED deal as lost (body ``LoseDealDto{notes}``, optional).

        Precondition: the deal must be ``approved`` (losing a ``registered`` deal is a
        400 illegal transition). On success ``status`` → ``lost``. HTTP 201.
        """
        body: dict[str, Any] = {} if notes is None else {"notes": notes}
        response = await self.post(
            f"{_DEALS_PATH}/{deal_id}/lose", json=body, expected_status=expected_status
        )
        return DealWriteResponse.model_validate(response.json())

    async def raw_lose_deal(
        self,
        deal_id: str,
        *,
        notes: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST lose for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {} if notes is None else {"notes": notes}
        return await self.post(
            f"{_DEALS_PATH}/{deal_id}/lose", json=body, expected_status=expected_status
        )

    async def resolve_conflict(
        self,
        deal_id: str,
        *,
        decision: str,
        reasoning: str,
        expected_status: int | tuple[int, ...] = 201,
    ) -> DealWriteResponse:
        """POST resolve a flagged deal conflict (``decision`` + ``reasoning`` required).

        ``decision`` ∈ resolved_for_partner / resolved_against_partner. On success
        ``conflictStatus`` becomes the decision and ``conflictResolution`` is stamped
        (decision, reasoning, resolvedBy, resolvedAt) — and is immutable thereafter.
        """
        response = await self.post(
            f"{_DEALS_PATH}/{deal_id}/resolve-conflict",
            json={"decision": decision, "reasoning": reasoning},
            expected_status=expected_status,
        )
        return DealWriteResponse.model_validate(response.json())

    async def raw_resolve_conflict(
        self,
        deal_id: str,
        *,
        decision: str | None = None,
        reasoning: str | None = None,
        expected_status: int | tuple[int, ...] | None = None,
    ) -> httpx.Response:
        """Raw POST resolve-conflict for negative tests — returns the response unvalidated."""
        body: dict[str, Any] = {}
        if decision is not None:
            body["decision"] = decision
        if reasoning is not None:
            body["reasoning"] = reasoning
        return await self.post(
            f"{_DEALS_PATH}/{deal_id}/resolve-conflict", json=body, expected_status=expected_status
        )
