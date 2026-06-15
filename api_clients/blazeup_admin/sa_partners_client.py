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
