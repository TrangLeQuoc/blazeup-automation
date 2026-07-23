"""SA Commissions API client + response schema (service: sa-partners-api).

SA-side commission ledger under ``/v1/sa/commissions`` — a read-only, paginated +
filterable list of partner commissions (plus per-id detail and write actions like
approve / clawback / dispute / mark-paid, not modelled here yet).

Maps to the Partner Platform test plan: PARTNER_API_COMMISSIONS_PAYOUTS_*.
"""

from typing import Any

import httpx
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api_clients.base_client import BaseClient

_COMMISSIONS_PATH = "/sa-partners-api/v1/sa/commissions"
_RATE_TABLE_PATH = "/sa-partners-api/v1/sa/rate-table"


class RateWriteResponse(BaseModel):
    """Envelope for the rate-table upsert: ``{statusCode, data:{...rate...}, message}``.

    ``data`` carries the persisted rate row (``_id``, tier, dealType, commissionType,
    ``rate``, ``clawbackWindowDays``, and ``previousRate`` — the prior value kept as a
    one-level version trail). HTTP is 201 while the body ``statusCode`` is 200.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    status_code: int | None = Field(
        default=None, validation_alias=AliasChoices("statusCode", "status_code")
    )
    data: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


class CommissionListResponse(BaseModel):
    """Envelope for the commission list: ``{statusCode, data[], total, message}``.

    ``data`` is a list of commission ledger entries. Validated as the envelope
    (BaseClient does not auto-unwrap here because we call ``get`` without ``schema=``).
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    status_code: int | None = Field(
        default=None, validation_alias=AliasChoices("statusCode", "status_code")
    )
    data: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None
    message: str | None = None


class SaCommissionsClient(BaseClient):
    """Client for SA-side commission ledger endpoints (sa-partners-api)."""

    async def list_commissions(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
        status: str | None = None,
        partner_id: str | None = None,
        deal_id: str | None = None,
        expected_status: int | tuple[int, ...] = 200,
    ) -> CommissionListResponse:
        """GET the commission ledger (paginated + filterable). Returns the envelope."""
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if status is not None:
            params["status"] = status
        if partner_id is not None:
            params["partnerId"] = partner_id
        if deal_id is not None:
            params["dealId"] = deal_id
        response = await self.get(
            _COMMISSIONS_PATH, params=params or None, expected_status=expected_status
        )
        return CommissionListResponse.model_validate(response.json())

    async def raw_list_commissions(
        self, *, expected_status: int | tuple[int, ...] | None = None, **params: Any
    ) -> httpx.Response:
        """Raw GET commissions for negative tests — returns the response unvalidated."""
        return await self.get(_COMMISSIONS_PATH, params=params, expected_status=expected_status)

    async def list_rate_table(
        self, *, expected_status: int | tuple[int, ...] = 200
    ) -> list[dict[str, Any]]:
        """GET the commission rate table — a list of rate rows (one per tier+dealType+commissionType)."""
        response = await self.get(_RATE_TABLE_PATH, expected_status=expected_status)
        return response.json().get("data") or []

    async def upsert_rate(
        self,
        *,
        tier: str,
        deal_type: str,
        commission_type: str,
        rate: float,
        clawback_window_days: int | None = None,
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> RateWriteResponse:
        """POST upsert a commission rate for a (tier, dealType, commissionType) combo.

        This is an **upsert-in-place** on an existing combo: the row's ``rate`` is
        replaced and the prior value is preserved under ``previousRate`` (a one-level
        version trail). There is no DELETE endpoint, so tests must only upsert an
        EXISTING combo and restore its original rate in teardown.
        """
        body: dict[str, Any] = {
            "tier": tier,
            "dealType": deal_type,
            "commissionType": commission_type,
            "rate": rate,
        }
        if clawback_window_days is not None:
            body["clawbackWindowDays"] = clawback_window_days
        response = await self.post(_RATE_TABLE_PATH, json=body, expected_status=expected_status)
        return RateWriteResponse.model_validate(response.json())

    async def raw_upsert_rate(
        self, body: dict[str, Any], *, expected_status: int | tuple[int, ...] | None = None
    ) -> httpx.Response:
        """Raw POST rate upsert for negative tests — returns the response unvalidated."""
        return await self.post(_RATE_TABLE_PATH, json=body, expected_status=expected_status)
