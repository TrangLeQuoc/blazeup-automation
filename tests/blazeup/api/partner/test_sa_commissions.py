"""SA Commissions API — commission ledger (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_COMMISSIONS_PAYOUTS_*.

``GET /sa-partners-api/v1/sa/commissions`` is a read-only, paginated + filterable
ledger of partner commissions (envelope ``{statusCode, data[], total, message}``).
Read-only — these tests create nothing and need no cleanup. Commission rows are only
created downstream when a deal is *won* (win emits commission events), so on an env
with no won deals the ledger is legitimately empty; the list CONTRACT is still
asserted, and the per-row schema/filter checks WARN-skip on an empty dataset.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step

# Keys that must never appear on a commission entry (no credential material).
_SENSITIVE = ("password", "token", "secret", "pwd", "credential")
# Commission status enum (from the sa-partners-api OpenAPI spec).
_STATUS_ENUM = {
    "earned",
    "pending_approval",
    "approved",
    "paid",
    "disputed",
    "clawback",
    "cancelled",
}


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_002(sa_commissions_client):
    """PARTNER_API_COMMISSIONS_PAYOUTS_002: GET commission history - partner commission ledger is returned.

    Read-only contract on ``GET /sa-partners-api/v1/sa/commissions``: returns HTTP 200
    with the envelope ``{statusCode, data[], total, message}``, honours pagination
    (page size never exceeds the requested limit), each entry is well-formed with a
    valid status enum and leaks no sensitive field, and a ``status`` filter returns
    only matching rows. Ledger rows are created downstream on deal-win, so on an empty
    env the per-row schema/filter checks WARN-skip (the list contract still holds).
    """
    limit = 5
    async with async_step(f"[1/4] GET /v1/sa/commissions (page=1, limit={limit})"):
        resp = await sa_commissions_client.list_commissions(page=1, limit=limit)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert isinstance(resp.data, list), "`data` must be a list"
        assert resp.total is not None and resp.total >= 0, "`total` must be a non-negative integer"
        assert resp.message, "`message` should be present"
        logger.info("CHECK envelope → OK (total={}, returned={})", resp.total, len(resp.data))

    async with async_step("[2/4] Verify pagination (page size <= limit)"):
        assert len(resp.data) <= limit, (
            f"page size {len(resp.data)} must not exceed requested limit {limit}"
        )
        logger.info("CHECK pagination → OK ({} <= {})", len(resp.data), limit)

    if not resp.data:
        logger.warning(
            "CHECK schema/filter — SKIPPED: commission ledger is empty on this environment "
            "(no won deals → no commissions; the list contract above still holds)"
        )
        logger.info("RESULT: commission-ledger list contract verified (empty dataset)")
        return

    async with async_step("[3/4] Verify each entry's schema + no sensitive field leaked"):
        for e in resp.data:
            assert isinstance(e, dict) and e, "each commission entry must be a non-empty object"
            assert e.get("_id") or e.get("id"), "entry must carry an id"
            status = e.get("status")
            assert status in _STATUS_ENUM, f"entry status must be a valid enum, got {status!r}"
            leaked = [k for k in e if any(s in str(k).lower() for s in _SENSITIVE)]
            assert not leaked, f"commission entry must not expose sensitive keys: {leaked}"
        logger.info("CHECK schema → OK ({} entries well-formed, no sensitive leak)", len(resp.data))

    async with async_step("[4/4] Verify a status filter returns only matching entries"):
        status = resp.data[0].get("status")
        filtered = await sa_commissions_client.list_commissions(limit=20, status=status)
        assert all(x.get("status") == status for x in filtered.data), (
            f"status filter must return only '{status}' entries"
        )
        logger.info("CHECK filter → OK (status='{}' → {} matching)", status, len(filtered.data))

    logger.info(
        "RESULT: commission-ledger list verified (total={}, paginated, filterable)", resp.total
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_017(sa_commissions_client):
    """PARTNER_API_COMMISSIONS_PAYOUTS_017: list commissions invalid filter/pagination - rejected (4xx, never 5xx).

    Negative counterpart of _002. Out-of-enum status, a malformed partnerId, and
    invalid pagination (page 0 / negative, oversized limit) are rejected with 400 + a
    clear message; ``limit=0`` is leniently defaulted (200) — observed, not asserted as
    4xx (never 5xx). All cases run (failures collected) so one gap never hides others.
    """
    # (label, query params, expected_status, message hint) — None status = "observe, just no 5xx"
    cases = [
        ("bad status enum", {"status": "bogus", "limit": 5}, 400, "status must be one of"),
        ("malformed partnerId", {"partnerId": "not-an-id", "limit": 5}, 400, "mongodb id"),
        ("page=0", {"page": 0, "limit": 5}, 400, "non-negative"),
        ("page=-1", {"page": -1, "limit": 5}, 400, "non-negative"),
        ("limit over max", {"limit": 999999}, 400, "must not exceed 100"),
        ("limit=0 (lenient)", {"limit": 0}, None, None),
    ]
    gaps: list[str] = []
    for idx, (label, params, want_status, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid list: {label}"):
            r = await sa_commissions_client.raw_list_commissions(expected_status=None, **params)
            body = r.json()
            msg = str(body.get("message") or "")
            assert r.status_code < 500, f"{label} must never 5xx, got {r.status_code}"
            if want_status is None:
                logger.info(
                    "OBSERVE {} → status {} (lenient default, not rejected)", label, r.status_code
                )
                continue
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

    assert not gaps, "commission-list negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all invalid commission-list attempts rejected (4xx, never 5xx)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_006(sa_commissions_client, created_resources):
    """PARTNER_API_COMMISSIONS_PAYOUTS_006: upsert a commission rate - new rate stored, prior kept as a version.

    POST /v1/sa/rate-table upserts the rate for a (tier, dealType, commissionType)
    combo IN PLACE: the new rate replaces the old, the prior value is preserved under
    ``previousRate`` (a one-level version trail), and no duplicate row is created.
    There is no DELETE endpoint, so this test only upserts an EXISTING combo and
    RESTORES its original rate in teardown. Repeating the upsert is additive-in-place,
    not a new row (mutating action → no separate duplicate-create idempotency TC). The
    "cached" side (Redis invalidation) is internal / not API-observable (see _014).
    """
    async with async_step(
        "Setup: pick an existing rate-table combo + capture its original rate (restore in teardown)"
    ):
        rows = await sa_commissions_client.list_rate_table()
        assert rows, "precondition: rate table must have at least one row to upsert"
        row = rows[0]
        tier, dt, ct = row["tier"], row["dealType"], row["commissionType"]
        orig_rate = row["rate"]
        orig_claw = row.get("clawbackWindowDays")
        # Register restore FIRST so a later failed assert still puts the original rate back.
        created_resources.add(
            lambda: sa_commissions_client.upsert_rate(
                tier=tier,
                deal_type=dt,
                commission_type=ct,
                rate=orig_rate,
                clawback_window_days=orig_claw,
            )
        )
        new_rate = round(orig_rate + 0.01, 4) if orig_rate <= 0.98 else round(orig_rate - 0.01, 4)
        new_rate2 = round(orig_rate + 0.02, 4) if orig_rate <= 0.97 else round(orig_rate - 0.02, 4)
        logger.info(
            "SETUP: combo {}/{}/{} original rate={} → upsert {} then {} (restore on teardown)",
            tier,
            dt,
            ct,
            orig_rate,
            new_rate,
            new_rate2,
        )

    async with async_step("[1/4] Upsert the SAME combo with a new rate"):
        resp = await sa_commissions_client.upsert_rate(
            tier=tier,
            deal_type=dt,
            commission_type=ct,
            rate=new_rate,
            clawback_window_days=orig_claw,
        )
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should confirm the upsert"
        logger.info("CHECK upsert → OK (HTTP 201, message='{}')", resp.message)

    async with async_step(
        "[2/4] New rate stored + prior value kept under previousRate (version trail)"
    ):
        d = resp.data
        assert d.get("rate") == new_rate, f"stored rate must be {new_rate}, got {d.get('rate')!r}"
        assert (d.get("previousRate") or {}).get("rate") == orig_rate, (
            f"previousRate must capture the prior rate {orig_rate}, got {d.get('previousRate')!r}"
        )
        assert (
            d.get("tier") == tier and d.get("dealType") == dt and d.get("commissionType") == ct
        ), "the (tier, dealType, commissionType) combo must be unchanged"
        combo_id = d.get("_id")
        logger.info("CHECK stored+version → OK (rate={}, previousRate={})", new_rate, orig_rate)

    async with async_step(
        "[3/4] GET reflects the new rate + still exactly ONE row for the combo (in-place, no duplicate)"
    ):
        rows2 = await sa_commissions_client.list_rate_table()
        mine = [
            r
            for r in rows2
            if r["tier"] == tier and r["dealType"] == dt and r["commissionType"] == ct
        ]
        assert len(mine) == 1, (
            f"upsert must not duplicate the combo: expected 1 row, got {len(mine)}"
        )
        assert mine[0].get("rate") == new_rate, "GET must reflect the upserted rate"
        assert mine[0].get("_id") == combo_id, "same row id (updated in place, not a new row)"
        logger.info("CHECK persisted → OK (1 row, rate={}, same _id)", new_rate)

    async with async_step(
        "[4/4] Repeat upsert (2nd new rate) is in-place — no duplicate, previousRate advances"
    ):
        resp2 = await sa_commissions_client.upsert_rate(
            tier=tier,
            deal_type=dt,
            commission_type=ct,
            rate=new_rate2,
            clawback_window_days=orig_claw,
        )
        assert resp2.data.get("rate") == new_rate2, "second upsert must store the 2nd rate"
        assert (resp2.data.get("previousRate") or {}).get("rate") == new_rate, (
            "previousRate must advance to the 1st upsert value"
        )
        rows3 = await sa_commissions_client.list_rate_table()
        mine3 = [
            r
            for r in rows3
            if r["tier"] == tier and r["dealType"] == dt and r["commissionType"] == ct
        ]
        assert len(mine3) == 1, (
            "repeat upsert must stay a single row (mutating in-place, not a create)"
        )
        logger.info("CHECK repeat → OK (in-place, rate={}, still 1 row)", new_rate2)

    logger.info(
        "RESULT: rate-table upsert verified (in-place, versioned via previousRate); "
        "original rate restored in teardown"
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_018(sa_commissions_client):
    """PARTNER_API_COMMISSIONS_PAYOUTS_018: upsert commission rate invalid input - rejected with 400 (no write).

    Negative counterpart of _006. Out-of-enum tier/dealType/commissionType, missing
    required fields, and an out-of-range rate (rate must be 0..1) are each rejected
    with HTTP 400 + a field-level message BEFORE any write (so no combo is created or
    mutated — safe, no teardown). All cases run (failures collected).
    """
    base = {
        "tier": "registered",
        "dealType": "referral",
        "commissionType": "referral",
        "rate": 0.05,
        "clawbackWindowDays": 90,
    }

    def without(field: str) -> dict:
        return {k: v for k, v in base.items() if k != field}

    # (label, payload, expected message hint) — all expected 400, none persisted
    cases = [
        ("invalid tier enum", {**base, "tier": "platinum"}, "tier must be one of"),
        ("invalid dealType enum", {**base, "dealType": "wholesale"}, "dealtype must be one of"),
        (
            "invalid commissionType enum",
            {**base, "commissionType": "bogus"},
            "commissiontype must be one of",
        ),
        ("missing tier", without("tier"), "tier must be one of"),
        ("missing dealType", without("dealType"), "dealtype must be one of"),
        ("missing commissionType", without("commissionType"), "commissiontype must be one of"),
        ("missing rate", without("rate"), "rate must"),
        ("negative rate", {**base, "rate": -0.1}, "rate must not be less than 0"),
        ("rate over 1", {**base, "rate": 1.5}, "rate must not be greater than 1"),
        ("non-numeric rate", {**base, "rate": "abc"}, "rate must be a number"),
    ]
    gaps: list[str] = []
    for idx, (label, body, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid upsert: {label}"):
            r = await sa_commissions_client.raw_upsert_rate(body, expected_status=None)
            msg = str(r.json().get("message") or "")
            if r.status_code == 400 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK (400, msg~'{}')", label, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "rate-upsert negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid rate-upsert attempts rejected with 400", len(cases))
