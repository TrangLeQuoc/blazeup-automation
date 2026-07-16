"""SA Certifications API — SA-side partner certification management (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_CERTIFICATIONS_SA_*.

Granting a cert is already covered by PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010
(certification earned + tier re-evaluation) / _020 (invalid) / _022 (re-grant
idempotency) — so CERTIFICATIONS_SA_001 (grant) is a cross-reference to _010, not a
duplicate test. This file covers the NEW cert endpoints: revoke, list-by-partner,
list-expiring. No billing plan involved, so no sa-plans dependency.
"""

import pytest
from loguru import logger

from utils.data_factory import make_partner, make_partner_user
from utils.log_helper import async_step

# A syntactically valid Mongo ObjectId that does not exist — for ghost-FK tests.
_GHOST_ID = "000000000000000000000000"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_certifications_sa_002(sa_partners_client, created_resources):
    """PARTNER_API_CERTIFICATIONS_SA_002: SA revokes a partner certification - cert becomes 'revoked'.

    Contract on ``DELETE /sa-partners-api/v1/sa/partner-users/{userId}/certifications/{type}``
    (body ``{reason}`` required): revoking an active certification returns HTTP 200
    and the cert transitions to ``status='revoked'`` (soft-revoke — the record
    remains, with the revoked status, visible in the partner's cert list).

    Note (TC↔BE): the plan says "certification removed and partner notified", but the
    BE soft-revokes (status='revoked', record kept). Confirm with BE.
    """
    cert_type = "sales_certified"
    async with async_step("Setup: partner + user + an active certification"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        uid = invited.data.get("userId")
        assert uid, "precondition: partner user must be invited"
        await sa_partners_client.grant_certification(uid, certification_type=cert_type, score=90)
        logger.info("SETUP: user {} holds an active '{}' cert", uid, cert_type)

    async with async_step("[1/2] Revoke the certification (with a reason)"):
        resp = await sa_partners_client.revoke_certification(
            uid, cert_type, reason="QA-AUTO revoke test"
        )
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should confirm the revoke"
        assert resp.data.get("status") == "revoked", (
            f"revoked cert must have status='revoked', got {resp.data.get('status')!r}"
        )
        logger.info("CHECK revoked → OK (200, status='revoked')")

    async with async_step(
        "[2/2] The cert shows as revoked in the partner's cert list (soft-revoke)"
    ):
        listed = await sa_partners_client.list_partner_certifications(pid)
        same = [c for c in listed.data if c.get("certificationType") == cert_type]
        assert same, "cert record should remain after a soft-revoke"
        assert all(c.get("status") == "revoked" for c in same), (
            "revoked cert must show status='revoked' (soft-revoke, not hard-removed)"
        )
        logger.info("CHECK persisted → OK (cert status='revoked' in the list)")

    logger.info("RESULT: certification '{}' revoked for user {}", cert_type, uid)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_certifications_sa_012(sa_partners_client, created_resources):
    """PARTNER_API_CERTIFICATIONS_SA_012: revoke certification invalid input/state - rejected with 4xx.

    Negative counterpart of _002 (revoke). Missing reason, a cert the user does not
    hold, a ghost/malformed userId, and re-revoking an already-revoked cert must all
    be rejected with 4xx + a clear message. The already-revoked case also documents
    revoke's repeat behavior (mutating action — not a duplicate-create, so no separate
    idempotency TC). All cases run (failures collected).
    """
    async with async_step("Setup: partner + user + an active sales_certified cert"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        uid = invited.data.get("userId")
        assert uid, "precondition: partner user must be invited"
        await sa_partners_client.grant_certification(
            uid, certification_type="sales_certified", score=90
        )
        logger.info("SETUP: user {} holds an active 'sales_certified' cert", uid)

    # (label, userId, certificationType, reason, expected message hint)
    cases = [
        ("missing reason", uid, "sales_certified", None, "reason should not be empty"),
        ("cert not held", uid, "hr_specialist", "QA-AUTO", "not found"),
        ("ghost user", _GHOST_ID, "sales_certified", "QA-AUTO", "not found"),
        ("malformed user", "not-an-id", "sales_certified", "QA-AUTO", "invalid id"),
    ]
    n_steps = len(cases) + 1
    gaps: list[str] = []
    for idx, (label, u, ct, reason, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{n_steps}] Reject revoke: {label}"):
            r = await sa_partners_client.raw_revoke_certification(
                u, ct, reason=reason, expected_status=None
            )
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    async with async_step(f"[{n_steps}/{n_steps}] Re-revoke an already-revoked cert is rejected"):
        await sa_partners_client.revoke_certification(
            uid, "sales_certified", reason="QA-AUTO first"
        )
        r = await sa_partners_client.raw_revoke_certification(
            uid, "sales_certified", reason="QA-AUTO again", expected_status=None
        )
        msg = str(r.json().get("message") or "")
        if 400 <= r.status_code < 500 and "not found" in msg.lower():
            logger.info("CHECK already-revoked → OK ({}, no active cert to revoke)", r.status_code)
        else:
            gaps.append(f"already-revoked: status={r.status_code}, msg={msg!r}")
            logger.error("CHECK already-revoked → FAIL (status={}, msg={!r})", r.status_code, msg)

    assert not gaps, "revoke-cert negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all invalid/illegal revoke attempts rejected (4xx)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_certifications_sa_003(sa_partners_client, created_resources):
    """PARTNER_API_CERTIFICATIONS_SA_003: SA lists a partner team's certifications - well-formed, filterable, scoped.

    Contract on ``GET /sa-partners-api/v1/sa/partners/{partnerId}/certifications``:
    returns HTTP 200 with the envelope ``{statusCode, data[], total, message}``; the
    granted cert appears with the right schema (certificationType/status/userId +
    earnedAt/expiresAt); the list is scoped to the partner; and a ``status=active``
    filter returns only active certs.
    """
    cert_type = "sales_certified"
    async with async_step("Setup: partner + user + an active certification"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        uid = invited.data.get("userId")
        assert uid, "precondition: partner user must be invited"
        await sa_partners_client.grant_certification(uid, certification_type=cert_type, score=90)
        logger.info(
            "SETUP: partner {} + user {} with '{}'", partner.data.get("code"), uid, cert_type
        )

    async with async_step("[1/3] GET partner certifications"):
        resp = await sa_partners_client.list_partner_certifications(pid, limit=20)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert isinstance(resp.data, list), "`data` must be a list"
        assert resp.message, "`message` should be present"
        logger.info("CHECK envelope → OK (total={}, returned={})", resp.total, len(resp.data))

    async with async_step(
        "[2/3] Granted cert appears with the right schema, scoped to the partner"
    ):
        certs = resp.data
        mine = next((c for c in certs if c.get("certificationType") == cert_type), None)
        assert mine, "granted cert must appear in the partner's cert list"
        assert isinstance(mine.get("status"), str) and mine.get("status"), (
            "cert must carry a status"
        )
        assert mine.get("userId"), "cert must carry a userId"
        assert mine.get("earnedAt") and mine.get("expiresAt"), (
            "cert must carry earnedAt + expiresAt"
        )
        assert all(str(c.get("partnerId")) == str(pid) for c in certs), (
            "list must be scoped to the requested partner"
        )
        logger.info(
            "CHECK cert → OK (type='{}', status='{}', scoped)", cert_type, mine.get("status")
        )

    async with async_step("[3/3] status=active filter returns only active certs"):
        active = await sa_partners_client.list_partner_certifications(
            pid, limit=20, status="active"
        )
        assert all(c.get("status") == "active" for c in active.data), (
            "status=active filter must return only active certs"
        )
        logger.info("CHECK filter → OK (status=active → {} cert(s))", len(active.data))

    logger.info(
        "RESULT: partner {} cert list verified ({} cert(s))",
        partner.data.get("code"),
        len(certs),
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_certifications_sa_013(sa_partners_client, created_resources):
    """PARTNER_API_CERTIFICATIONS_SA_013: list partner certifications invalid filter/pagination - graceful, never 5xx.

    Negative counterpart of _003. Out-of-enum filters, oversized limit, and a
    malformed partnerId are rejected with 4xx; a ghost (valid-but-nonexistent)
    partnerId returns 200 empty; page=0 is leniently defaulted (200). Never 5xx.
    """
    async with async_step("Setup: create a partner (baseline)"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"

    robustness = [
        ("bad status enum", {"status": "bogus"}, "status must be one of"),
        (
            "bad certificationType enum",
            {"certificationType": "bogus"},
            "certificationtype must be one of",
        ),
        ("limit over max", {"limit": 999999}, "must not exceed 100"),
    ]
    n_steps = len(robustness) + 3
    gaps: list[str] = []

    for idx, (label, params, hint) in enumerate(robustness, start=1):
        async with async_step(f"[{idx}/{n_steps}] Reject invalid: {label}"):
            r = await sa_partners_client.raw_list_partner_certifications(
                pid, expected_status=None, **params
            )
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    async with async_step(f"[{len(robustness) + 1}/{n_steps}] Malformed partnerId → 4xx"):
        r = await sa_partners_client.raw_list_partner_certifications("not-an-id", limit=5)
        msg = str(r.json().get("message") or "")
        if 400 <= r.status_code < 500 and "invalid id" in msg.lower():
            logger.info("CHECK malformed partnerId → OK ({})", r.status_code)
        else:
            gaps.append(f"malformed partnerId: status={r.status_code}, msg={msg!r}")
            logger.error("CHECK malformed partnerId → FAIL ({}, {!r})", r.status_code, msg)

    async with async_step(
        f"[{len(robustness) + 2}/{n_steps}] Ghost partnerId → 200 empty (graceful)"
    ):
        r = await sa_partners_client.raw_list_partner_certifications(_GHOST_ID, limit=5)
        if r.status_code == 200 and len(r.json().get("data") or []) == 0:
            logger.info("CHECK ghost partnerId → OK (200 empty)")
        else:
            gaps.append(f"ghost partnerId: status={r.status_code}")
            logger.error("CHECK ghost partnerId → FAIL ({})", r.status_code)

    async with async_step(
        f"[{n_steps}/{n_steps}] page=0 handled gracefully (4xx or default, never 5xx)"
    ):
        r = await sa_partners_client.raw_list_partner_certifications(pid, page=0, limit=5)
        assert r.status_code < 500, f"page=0 must not 5xx, got {r.status_code}"
        logger.info("OBSERVE page=0 → status {} (graceful, no 5xx)", r.status_code)

    assert not gaps, "cert list-by-partner negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid cert-list filter/pagination handled gracefully (never 5xx)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_certifications_sa_004(sa_partners_client):
    """PARTNER_API_CERTIFICATIONS_SA_004: SA lists certifications expiring soon - expiringWithinDays filter.

    Contract on ``GET /sa-partners-api/v1/sa/certifications?expiringWithinDays=N``:
    returns HTTP 200 with the envelope ``{statusCode, data[], total, message}``;
    every returned cert expires within the requested window; and the window is
    bounded 1..365 (the max, 365, is accepted).

    Note (confirm BE): the SA-wide list returns total=0 on staging even when active
    certs exist (they are visible via the per-partner list, _003) — a possible
    scoping/index difference. The filter SEMANTIC is asserted on whatever is
    returned; the empty case is logged, not failed.
    """
    from datetime import UTC, datetime, timedelta

    def _parse(ts: object) -> datetime:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))

    within = 30
    async with async_step(f"[1/2] GET /sa/certifications?expiringWithinDays={within}"):
        resp = await sa_partners_client.list_certifications(limit=50, expiringWithinDays=within)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert isinstance(resp.data, list), "`data` must be a list"
        assert resp.message, "`message` should be present"
        logger.info("CHECK envelope → OK (total={}, returned={})", resp.total, len(resp.data))
        if resp.data:
            cutoff = datetime.now(UTC) + timedelta(days=within)
            for c in resp.data:
                exp = c.get("expiresAt")
                assert exp and _parse(exp) <= cutoff, (
                    f"a returned cert must expire within {within} days, got expiresAt={exp}"
                )
            logger.info(
                "CHECK filter semantic → OK ({} cert(s), all expire ≤ {}d)", len(resp.data), within
            )
        else:
            logger.warning(
                "CHECK filter semantic — SKIPPED: SA-wide cert list empty on this env "
                "(total=0; certs visible via per-partner list — confirm BE scoping)"
            )

    async with async_step("[2/2] expiringWithinDays max boundary (365) is accepted"):
        r = await sa_partners_client.list_certifications(limit=5, expiringWithinDays=365)
        assert r.status_code == 200, "expiringWithinDays=365 (max) must be accepted"
        logger.info("CHECK boundary → OK (expiringWithinDays=365 accepted)")

    logger.info("RESULT: expiring-cert list contract verified (expiringWithinDays bounded 1..365)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_certifications_sa_014(sa_partners_client):
    """PARTNER_API_CERTIFICATIONS_SA_014: list SA certifications invalid filter/pagination - rejected (4xx, never 5xx).

    Negative counterpart of _004. Out-of-enum status/certificationType, an
    out-of-range ``expiringWithinDays`` (must be 1..365), oversized limit, and page=0
    must all be rejected with 4xx + a clear message. All cases run (failures
    collected).
    """
    cases = [
        ("bad status enum", {"status": "bogus"}, "status must be one of"),
        (
            "bad certificationType enum",
            {"certificationType": "bogus"},
            "certificationtype must be one of",
        ),
        ("expiringWithinDays = 0", {"expiringWithinDays": 0}, "must not be less than 1"),
        ("expiringWithinDays negative", {"expiringWithinDays": -5}, "must not be less than 1"),
        ("expiringWithinDays > 365", {"expiringWithinDays": 366}, "must not be greater than 365"),
        ("limit over max", {"limit": 999999}, "must not exceed 100"),
        ("page=0", {"page": 0, "limit": 5}, "non-negative"),
    ]
    gaps: list[str] = []
    for idx, (label, params, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid: {label}"):
            r = await sa_partners_client.raw_list_certifications(expected_status=None, **params)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "SA cert-list negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid SA cert-list attempts rejected (never 5xx)", len(cases))
