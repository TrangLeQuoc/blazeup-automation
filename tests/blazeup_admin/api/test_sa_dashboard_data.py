"""Partner Dashboard Data API — partner-portal dashboard KPIs (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_DASHBOARD_DATA_*.

``GET /sa-partners-api/v1/partner/portal/dashboard`` is a PARTNER-PORTAL endpoint
(needs a partner JWT, not the SA token). The session is minted self-contained from
the SA side via ``utils.partner_portal.mint_partner_session``. No billing plan
involved, so no sa-plans dependency.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

_DASHBOARD_PATH = "/sa-partners-api/v1/partner/portal/dashboard"
_SENSITIVE = ("password", "token", "secret", "pwd", "credential")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_dashboard_data_001(sa_partners_client, settings, created_resources):
    """PARTNER_API_DASHBOARD_DATA_001: partner dashboard stats - KPI schema is returned.

    Contract on ``GET /sa-partners-api/v1/partner/portal/dashboard`` (partner JWT):
    returns HTTP 200 with the envelope ``{statusCode, data{}, message}`` where ``data``
    carries the dashboard KPI sections (``partner`` with tier/status/openDealsCount,
    ``deals``, ``commissions``), leaking no sensitive field.

    Negative: the endpoint takes no params, so there is no invalid-input negative;
    the no-token / wrong-token 401 belongs to the Auth & Access Control feature.
    Idempotency: GET is read-only → N/A.
    """
    async with async_step(
        "Setup: mint a partner-portal session (create+approve partner, invite, login)"
    ):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        logger.info("SETUP: partner-portal session for partner {}", pid)

    async with async_step("[1/2] GET the partner dashboard"):
        resp = await portal.get(_DASHBOARD_PATH, expected_status=200)
        body = resp.json()
        assert body.get("statusCode") == 200, (
            f"expected body statusCode 200, got {body.get('statusCode')}"
        )
        data = body.get("data") or {}
        assert isinstance(data, dict) and data, "dashboard `data` must be a non-empty object"
        logger.info("CHECK envelope → OK (sections={})", sorted(data.keys()))

    async with async_step("[2/2] Verify the KPI schema (partner / deals / commissions) + no leak"):
        for section in ("partner", "deals", "commissions"):
            assert section in data, f"dashboard must include the '{section}' KPI section"
        p = data["partner"]
        assert isinstance(p, dict) and p, "partner KPI section must be an object"
        assert p.get("tier"), "partner KPI must include tier"
        assert p.get("status"), "partner KPI must include status"
        assert "openDealsCount" in p, "partner KPI must include openDealsCount"
        leaked = [k for k in p if any(s in str(k).lower() for s in _SENSITIVE)]
        assert not leaked, f"dashboard must not leak sensitive keys: {leaked}"
        logger.info(
            "CHECK KPI schema → OK (partner: tier='{}', status='{}', openDealsCount={}; deals/commissions present)",
            p.get("tier"),
            p.get("status"),
            p.get("openDealsCount"),
        )

    logger.info("RESULT: partner dashboard KPI schema verified")
