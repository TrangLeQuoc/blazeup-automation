"""Partner Portal API — a partner's own-account read endpoints (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_PARTNER_PORTAL_*.

All endpoints are under ``/sa-partners-api/v1/partner/portal/*`` and require a
PARTNER JWT (not the SA token). The session is minted self-contained from the SA
side via ``utils.partner_portal.mint_partner_session`` (which also returns the
partner_id + user_id so the SA can seed own-scoped data). All read endpoints here
are GET (read-only → idempotency N/A). No billing plan → no sa-plans dependency
(except _002 deal-detail, which needs a registered deal — deferred while sa-plans
is down).
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_prospect, make_territory
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

_BASE = "/sa-partners-api/v1/partner/portal"
_SENSITIVE = ("password", "token", "secret", "pwd", "credential")
_GHOST_ID = "000000000000000000000000"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_001(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_001: partner gets its own account profile - details returned.

    GET /partner/portal/profile (partner JWT) returns the partner's own account
    (code/email/name/tier/status) with no sensitive field leaked. No params → no
    invalid-input negative; 401 auth belongs to Auth & Access Control. GET → no
    idempotency TC.
    """
    async with async_step("Setup: mint a partner-portal session"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        logger.info("SETUP: partner-portal session for partner {}", pid)

    async with async_step("[1/1] GET own profile"):
        resp = await portal.get(f"{_BASE}/profile", expected_status=200)
        d = resp.json().get("data") or {}
        assert isinstance(d, dict) and d, "profile `data` must be a non-empty object"
        assert (d.get("_id") or d.get("id")) == pid, (
            "profile must be the logged-in partner's account"
        )
        assert d.get("code"), "profile must include the partner code"
        assert d.get("email"), "profile must include the email"
        assert d.get("tier") and d.get("status"), "profile must include tier + status"
        leaked = [k for k in d if any(s in str(k).lower() for s in _SENSITIVE)]
        assert not leaked, f"profile must not leak sensitive keys: {leaked}"
        logger.info("CHECK profile → OK (code={}, tier={}, no leak)", d.get("code"), d.get("tier"))

    logger.info("RESULT: partner own-profile verified")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_004(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_004: partner gets its own commission summary - earned/pending/paid totals.

    GET /partner/portal/commissions/summary returns the cents totals
    (totalEarnedCents / totalPendingCents / totalPaidCents / clawbackExposureCents)
    as non-negative ints. No params → no invalid-input negative; GET → no idempotency.
    """
    async with async_step("Setup: mint a partner-portal session"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))

    async with async_step("[1/1] GET own commission summary"):
        resp = await portal.get(f"{_BASE}/commissions/summary", expected_status=200)
        d = resp.json().get("data") or {}
        assert isinstance(d, dict) and d, "summary `data` must be a non-empty object"
        for f in ("totalEarnedCents", "totalPendingCents", "totalPaidCents"):
            v = d.get(f)
            assert isinstance(v, int) and not isinstance(v, bool), f"{f} must be an int, got {v!r}"
            assert v >= 0, f"{f} must be non-negative, got {v}"
        logger.info(
            "CHECK summary → OK (earned={}, pending={}, paid={})",
            d.get("totalEarnedCents"),
            d.get("totalPendingCents"),
            d.get("totalPaidCents"),
        )

    logger.info("RESULT: partner commission summary verified")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_005(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_005: partner gets its own assigned territories - territory list returned.

    SA assigns a territory to the partner; GET /partner/portal/territories returns it
    scoped to the partner. No params → no invalid-input negative; GET → no idempotency.
    """
    async with async_step("Setup: mint a session + SA assigns a territory to the partner"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        terr = await sa_partners_client.assign_territory(make_territory(pid, countries=["DE"]))
        tid = terr.data.get("_id") or terr.data.get("id")
        if tid:
            created_resources.add(lambda: sa_partners_client.delete_territory(tid))
        logger.info("SETUP: partner {} + territory {}", pid, tid)

    async with async_step("[1/1] GET own territories"):
        resp = await portal.get(f"{_BASE}/territories", expected_status=200)
        terrs = resp.json().get("data") or []
        assert isinstance(terrs, list) and terrs, "territories `data` must be a non-empty list"
        mine = next((t for t in terrs if (t.get("_id") or t.get("id")) == tid), None)
        assert mine, "the assigned territory must appear in the partner's own list"
        assert all(str(t.get("partnerId")) == str(pid) for t in terrs), "list scoped to own partner"
        logger.info("CHECK territories → OK ({} row(s), scoped, assigned one present)", len(terrs))

    logger.info("RESULT: partner own-territories verified")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_006(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_006: partner gets its own tier commission rates - tier rates returned.

    GET /partner/portal/rates returns the tier-specific commission rates as a list.
    No params → no invalid-input negative; GET → no idempotency.
    """
    async with async_step("Setup: mint a partner-portal session"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))

    async with async_step("[1/1] GET own commission rates"):
        resp = await portal.get(f"{_BASE}/rates", expected_status=200)
        rates = resp.json().get("data")
        assert isinstance(rates, list), "rates `data` must be a list"
        if rates:
            for rate in rates:
                assert isinstance(rate, dict) and rate, "each rate must be a non-empty object"
            logger.info("CHECK rates → OK ({} tier rate(s) returned)", len(rates))
        else:
            logger.warning(
                "CHECK rates — empty for this tier (registered); endpoint returns a well-formed list"
            )

    logger.info("RESULT: partner tier commission rates verified ({} rate(s))", len(rates or []))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_003(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_003: partner gets its own certifications - active certs listed.

    SA grants a cert to the partner user; GET /partner/portal/certifications lists the
    partner's own certs with the right schema (certificationType/status/earnedAt). GET
    → no idempotency. Negative (invalid filter) is covered by _013.
    """
    cert_type = "sales_certified"
    async with async_step("Setup: mint a session + SA grants a cert to the partner user"):
        portal, pid, uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        await sa_partners_client.grant_certification(uid, certification_type=cert_type, score=90)
        logger.info("SETUP: partner {} user {} granted '{}'", pid, uid, cert_type)

    async with async_step("[1/2] GET own certifications"):
        resp = await portal.get(f"{_BASE}/certifications", expected_status=200)
        certs = resp.json().get("data") or []
        assert isinstance(certs, list) and certs, "certifications `data` must be a non-empty list"
        logger.info("CHECK list → OK ({} cert(s))", len(certs))

    async with async_step("[2/2] The granted cert appears with the right schema"):
        mine = next((c for c in certs if c.get("certificationType") == cert_type), None)
        assert mine, "the granted cert must appear in the partner's own list"
        assert mine.get("status"), "cert must carry a status"
        assert mine.get("earnedAt") and mine.get("expiresAt"), (
            "cert must carry earnedAt + expiresAt"
        )
        logger.info("CHECK cert → OK (type='{}', status='{}')", cert_type, mine.get("status"))

    logger.info("RESULT: partner own-certifications verified")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_013(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_013: own certifications with invalid filter - rejected (4xx, never 5xx).

    Negative counterpart of _003. Out-of-enum status / certificationType and oversized
    limit must be rejected with 4xx (never 5xx). All cases run (failures collected).
    """
    async with async_step("Setup: mint a partner-portal session"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))

    cases = [
        ("bad status enum", {"status": "bogus"}, "status must be one of"),
        (
            "bad certificationType enum",
            {"certificationType": "bogus"},
            "certificationtype must be one of",
        ),
        ("limit over max", {"limit": 999999}, "must not exceed"),
    ]
    gaps: list[str] = []
    for idx, (label, params, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid cert filter: {label}"):
            r = await portal.get(f"{_BASE}/certifications", params=params, expected_status=None)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "portal-certifications negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid portal-cert filters rejected (never 5xx)", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_002(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_PARTNER_PORTAL_002: partner retrieves its own deal by id - full record.

    The partner registers its own deal (POST /partner/portal/deals), then GET
    /partner/portal/deals/{id} returns the full record scoped to the partner.
    """
    async with async_step("Setup: mint a session + the partner registers a deal"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        plan_id = await sa_deals_client.pick_billing_plan_id()
        created = await portal.post(
            f"{_BASE}/deals",
            json=make_deal(None, plan_id, **make_prospect()),
            expected_status=(200, 201),
        )
        deal_id = (created.json().get("data") or {}).get("_id")
        assert deal_id, "precondition: the partner must be able to register a deal"
        logger.info("SETUP: partner {} + deal {}", pid, deal_id)

    async with async_step("[1/1] GET the own deal by id"):
        resp = await portal.get(f"{_BASE}/deals/{deal_id}", expected_status=200)
        d = resp.json().get("data") or {}
        assert (d.get("_id") or d.get("id")) == deal_id, "GET by id must return the same deal"
        assert str(d.get("partnerId")) == str(pid), "the deal must belong to the logged-in partner"
        for f in ("dealType", "prospectName", "status"):
            assert d.get(f), f"deal record must include {f}"
        logger.info("CHECK deal-detail → OK (own deal, status='{}')", d.get("status"))

    logger.info("RESULT: partner own deal-detail verified")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_012(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_012: get own deal with invalid id - rejected with the correct code.

    Negative counterpart of _002. A GHOST id (well-formed but non-existent) → 404
    'not found'; a MALFORMED id → 400 'invalid id'. All cases run (failures collected).

    Note: unlike the SA-side get-by-id endpoints (which return 400 for a ghost id — a
    known gap), THIS partner-portal endpoint correctly returns 404. This test pins that
    correct behavior so a regression toward 400 would be caught.
    """
    async with async_step("Setup: mint a partner-portal session"):
        portal, pid, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid))

    # (label, id, expected_status, message hint)
    cases = [
        ("ghost id (well-formed, absent)", _GHOST_ID, 404, "not found"),
        ("malformed id", "not-an-id", 400, "invalid id"),
    ]
    gaps: list[str] = []
    for idx, (label, did, want_status, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject get own deal: {label} → {want_status}"):
            r = await portal.get(f"{_BASE}/deals/{did}", expected_status=None)
            msg = str(r.json().get("message") or "")
            if r.status_code == want_status and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: expected {want_status}, got {r.status_code}, msg={msg!r}")
                logger.error(
                    "CHECK {} → FAIL (expected {}, got {}, msg={!r})",
                    label,
                    want_status,
                    r.status_code,
                    msg,
                )
    assert not gaps, "portal deal-detail negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid own-deal-by-id rejected (ghost 404 / malformed 400)")
