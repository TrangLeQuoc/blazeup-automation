"""Partner Pipeline Management API — a partner's own deals list (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_PIPELINE_MANAGEMENT_*.

``GET /sa-partners-api/v1/partner/portal/deals`` (partner JWT) lists the partner's
OWN deals, filterable by status. Sessions are minted self-contained from the SA side
(`utils.partner_portal`). GET read-only → idempotency N/A.
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_prospect
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

_BASE = "/sa-partners-api/v1/partner/portal"


async def _register_own_deal(portal, sa_deals_client) -> str:
    plan_id = await sa_deals_client.pick_billing_plan_id()
    r = await portal.post(
        f"{_BASE}/deals",
        json=make_deal(None, plan_id, **make_prospect()),
        expected_status=(200, 201),
    )
    return (r.json().get("data") or {}).get("_id")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_pipeline_management_001(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_PIPELINE_MANAGEMENT_001: partner lists deals - only its OWN deals are returned.

    The partner registers a deal, then GET /partner/portal/deals returns it and every
    row is scoped to the partner (partnerId == own) — no cross-partner leakage.
    """
    async with async_step("Setup: mint a session + the partner registers a deal"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        deal_id = await _register_own_deal(portal, sa_deals_client)
        assert deal_id, "precondition: the partner must be able to register a deal"
        logger.info("SETUP: partner {} + deal {}", pid, deal_id)

    async with async_step("[1/2] GET own deals list"):
        resp = await portal.get(f"{_BASE}/deals", params={"limit": 20}, expected_status=200)
        deals = resp.json().get("data") or []
        assert isinstance(deals, list) and deals, "deals `data` must be a non-empty list"
        logger.info("CHECK list → OK ({} deal(s))", len(deals))

    async with async_step("[2/2] The registered deal appears + list scoped to own partner"):
        assert any((d.get("_id") or d.get("id")) == deal_id for d in deals), (
            "the registered deal must appear in the partner's own list"
        )
        assert all(str(d.get("partnerId")) == str(pid) for d in deals), (
            "list must contain ONLY the partner's own deals (no cross-partner leakage)"
        )
        logger.info("CHECK scoped → OK (all {} deal(s) belong to the partner)", len(deals))

    logger.info("RESULT: partner own-deals list verified (scoped)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_pipeline_management_002(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_PIPELINE_MANAGEMENT_002: partner lists deals with a status filter - filter applied.

    Filtering the own-deals list by ``status=registered`` returns only registered
    deals (and includes the freshly-registered one).
    """
    async with async_step("Setup: mint a session + the partner registers a deal"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        deal_id = await _register_own_deal(portal, sa_deals_client)
        assert deal_id, "precondition: deal must be registered"

    async with async_step("[1/1] Filter by status=registered"):
        resp = await portal.get(
            f"{_BASE}/deals", params={"limit": 20, "status": "registered"}, expected_status=200
        )
        deals = resp.json().get("data") or []
        assert deals, "status=registered must return the registered deal"
        assert all(d.get("status") == "registered" for d in deals), (
            "status filter must return only 'registered' deals"
        )
        assert any((d.get("_id") or d.get("id")) == deal_id for d in deals), (
            "the registered deal must appear under status=registered"
        )
        logger.info(
            "CHECK filter → OK (status=registered → {} deal(s), all registered)", len(deals)
        )

    logger.info("RESULT: partner deals status-filter verified")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_pipeline_management_011(sa_partners_client, settings, created_resources):
    """PARTNER_API_PIPELINE_MANAGEMENT_011: deals list invalid filter/pagination - graceful, never 5xx.

    Negative counterpart of _001/_002. An out-of-enum status and oversized limit must
    be handled gracefully (4xx where validated, never 5xx).
    """
    async with async_step("Setup: mint a partner-portal session"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))

    gaps: list[str] = []
    for idx, (label, params) in enumerate(
        [("bad status enum", {"status": "bogus"}), ("limit over max", {"limit": 999999})], start=1
    ):
        async with async_step(f"[{idx}/2] Invalid list: {label}"):
            r = await portal.get(f"{_BASE}/deals", params=params, expected_status=None)
            assert r.status_code < 500, f"{label} must not 5xx, got {r.status_code}"
            logger.info("CHECK {} → status {} (no 5xx)", label, r.status_code)
            if not (400 <= r.status_code < 500):
                logger.warning("OBSERVE {} → {} (not rejected — lenient)", label, r.status_code)

    assert not gaps
    logger.info("RESULT: partner deals invalid filter/pagination handled gracefully (never 5xx)")
