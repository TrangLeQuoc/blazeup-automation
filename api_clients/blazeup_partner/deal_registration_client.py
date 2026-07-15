"""Deal Registration API client + schemas.

⚠️ SCAFFOLD — NOT WIRED YET. The `blazeup_partner` domain has no tests; the endpoint
paths below are placeholders. Calling any method raises NotImplementedError until
`_DEALS` is set to a real path. (Partner deals ARE tested today via the SA-minted
partner session under `blazeup_admin` — see `tests/blazeup_admin/api/partner/
test_sa_pipeline_management.py` + `utils/partner_portal.py`.) Fill this in only when
the `blazeup_partner` domain is built out.

Mirrors ``api_clients/blazeup_admin/auth_client.py``:
    api_clients/base_client.py            → BaseClient (get/post/put/patch/delete)
    api_clients/blazeup_partner/<this>    → endpoints + pydantic response schemas
    tests/blazeup_partner/api/            → scenarios

Usage in a test::

    from api_clients.blazeup_partner.deal_registration_client import DealRegistrationClient

    async def test_partner_api_deal_registration_001(settings, api_token):
        client = DealRegistrationClient(
            str(settings.api_base_url), token=api_token,
            app_origin=str(settings.base_url),
        )
        try:
            deals = await client.list_deals()
        finally:
            await client.close()
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from api_clients.base_client import BaseClient


class Deal(BaseModel):
    """A single registered deal.  (extra='allow' tolerates unknown fields.)"""

    model_config = ConfigDict(extra="allow")

    # TODO: align field names + aliases with the real API payload.
    id: str | int | None = None
    name: str | None = None
    stage: str | None = Field(default=None)


class DealRegistrationClient(BaseClient):
    """Client for Partner Deal Registration endpoints."""

    # ── Endpoints: replace TODO with the real paths ──────────────────────────
    # TODO: real path, e.g. "/sa-partners-api/v1/partner/portal/deals"
    _DEALS = "TODO-partner-deals-endpoint"

    def _endpoint(self) -> str:
        """Return the deals endpoint, or fail fast while this client is a scaffold."""
        path = self.__class__._DEALS
        if path.startswith("TODO"):
            raise NotImplementedError(
                "DealRegistrationClient is a SCAFFOLD — set `_DEALS` to the real partner-deals "
                "endpoint before use (probe the live OpenAPI / see the Partner Platform PRD)."
            )
        return path

    async def list_deals(self, expected_status: int = 200) -> list[dict[str, Any]]:
        """GET all deals registered by the current partner."""
        response = await self.get(self._endpoint(), expected_status=expected_status)
        payload = response.json()
        return payload.get("data", payload) if isinstance(payload, dict) else payload

    async def create_deal(
        self,
        body: dict[str, Any],
        expected_status: int | tuple[int, ...] = (200, 201),
    ) -> Deal:
        """POST a new deal registration; returns the validated Deal."""
        return await self.post(
            self._endpoint(), json=body, expected_status=expected_status, schema=Deal
        )

    async def update_deal(
        self,
        deal_id: str | int,
        body: dict[str, Any],
        expected_status: int = 200,
    ) -> Deal:
        """PATCH an existing deal (partial update)."""
        return await self.patch(
            f"{self._endpoint()}/{deal_id}", json=body, expected_status=expected_status, schema=Deal
        )

    async def delete_deal(self, deal_id: str | int, expected_status: int = 204) -> None:
        """DELETE a deal registration."""
        await self.delete(f"{self._endpoint()}/{deal_id}", expected_status=expected_status)
