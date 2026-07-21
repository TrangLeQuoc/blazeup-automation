"""SA Territories API — SA-side partner territory assignment (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_TERRITORIES_*.

``POST /sa-partners-api/v1/sa/territories`` assigns a territory; GET lists / gets by
id; DELETE removes an assignment. No billing plan involved, so no sa-plans dependency.
"""

import pytest
from loguru import logger

from utils.data_factory import make_partner, make_territory
from utils.log_helper import async_step

# A syntactically valid Mongo ObjectId that does not exist — for ghost-FK tests.
_GHOST_ID = "000000000000000000000000"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_001(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_001: SA assigns a territory to a partner - saved with fields + effective dates.

    Contract on ``POST /sa-partners-api/v1/sa/territories``: a valid assignment
    (partnerId + label + countries + exclusivity + effective dates) returns HTTP 201,
    persists a server-assigned id, echoes the submitted fields (incl. the effective
    dates), and is retrievable via GET by id.
    """
    async with async_step("Setup: create a partner"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        payload = make_territory(pid, countries=["US", "CA"], exclusivityType="preferred")
        logger.info(
            "SETUP: partner {}; territory label='{}'", partner.data.get("code"), payload["label"]
        )

    async with async_step("[1/3] Assign the territory"):
        resp = await sa_partners_client.assign_territory(payload)
        tid = resp.data.get("_id") or resp.data.get("id")
        if tid:
            created_resources.add(lambda: sa_partners_client.delete_territory(tid))
        assert resp.status_code in (200, 201), (
            f"expected success statusCode, got {resp.status_code}"
        )
        assert tid, "assigned territory must have a server-assigned id"
        assert resp.message, "`message` should confirm the assignment"
        logger.info("CHECK assigned → OK (HTTP 201, id={})", tid)

    async with async_step("[2/3] Submitted fields stored (incl. effective dates)"):
        d = resp.data
        assert d.get("partnerId") == payload["partnerId"], "stored partnerId must match"
        assert d.get("label") == payload["label"], "stored label must match"
        assert d.get("countries") == payload["countries"], "stored countries must match"
        assert d.get("exclusivityType") == payload["exclusivityType"], (
            "stored exclusivityType must match"
        )
        assert str(d.get("exclusivityStartDate", "")).startswith(payload["exclusivityStartDate"]), (
            "effective start date must be preserved"
        )
        assert str(d.get("exclusivityEndDate", "")).startswith(payload["exclusivityEndDate"]), (
            "effective end date must be preserved"
        )
        logger.info("CHECK echo → OK (fields + effective dates stored as sent)")

    async with async_step("[3/3] Retrievable via GET by id"):
        fetched = await sa_partners_client.get_territory(tid)
        assert (fetched.data.get("_id") or fetched.data.get("id")) == tid, (
            "GET by id must return the same territory"
        )
        logger.info("CHECK retrievable → OK (GET by id returns the territory)")

    logger.info("RESULT: territory {} assigned to partner {}", tid, partner.data.get("code"))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_011(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_011: assign territory invalid/missing fields - rejected with 400.

    Negative counterpart of _001. Each invalid/incomplete payload must be rejected
    with 4xx + a descriptive message. The ghost partnerId is self-proving (the
    endpoint returns "Partner ... not found"). All cases run (failures collected).
    """
    async with async_step("Setup: create a partner (valid baseline)"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        base = make_territory(pid)

    def without(field: str) -> dict:
        return {k: v for k, v in base.items() if k != field}

    cases = [
        ("missing partnerId", without("partnerId"), "partnerid must be a mongodb id"),
        ("missing label", without("label"), "label"),
        ("missing countries", without("countries"), "countries"),
        (
            "invalid exclusivityType",
            {**base, "exclusivityType": "bogus"},
            "exclusivitytype must be one of",
        ),
        ("invalid country code", {**base, "countries": ["ZZ"]}, "iso31661"),
        ("bad start date", {**base, "exclusivityStartDate": "31-12-2026"}, "iso 8601"),
        ("ghost partnerId", {**base, "partnerId": _GHOST_ID}, "not found"),
        ("malformed partnerId", {**base, "partnerId": "not-an-id"}, "mongodb id"),
    ]
    gaps: list[str] = []
    for idx, (label, body, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid assign: {label}"):
            r = await sa_partners_client.raw_assign_territory(body, expected_status=None)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "territory-assign negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid territory-assign attempts rejected", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_012(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_012: exclusive territory conflict - a 2nd partner can't take a held exclusive country.

    Duplicate/conflict counterpart of _001 (assign). When one partner holds an
    EXCLUSIVE territory for a country, a DIFFERENT partner registering an exclusive
    territory for the same country is rejected (4xx "Exclusive territory conflict")
    and no territory is created. (Same-partner overlap is allowed by design.)
    """
    country = "IS"  # uncommon ISO code to minimise collisions with leftover data
    async with async_step("Setup: two partners"):
        p1 = await sa_partners_client.create_partner(make_partner())
        p2 = await sa_partners_client.create_partner(make_partner())
        for p in (p1, p2):
            if p.partner_id:
                created_resources.add(
                    lambda pid=p.partner_id: sa_partners_client.delete_partner(pid)
                )
        assert p1.partner_id and p2.partner_id, "precondition: both partners must be created"

    async with async_step(f"[1/3] Partner 1 takes an EXCLUSIVE territory on {country}"):
        first = await sa_partners_client.assign_territory(
            make_territory(p1.partner_id, countries=[country], exclusivityType="exclusive")
        )
        tid = first.data.get("_id") or first.data.get("id")
        if tid:
            created_resources.add(lambda: sa_partners_client.delete_territory(tid))
        assert tid, (
            f"precondition: partner 1 exclusive territory on {country} must be created (country free)"
        )
        logger.info("CHECK first → OK (exclusive {} assigned to partner 1)", country)

    async with async_step(f"[2/3] Partner 2 cannot take the SAME exclusive {country} → conflict"):
        r = await sa_partners_client.raw_assign_territory(
            make_territory(p2.partner_id, countries=[country], exclusivityType="exclusive"),
            expected_status=None,
        )
        assert 400 <= r.status_code < 500, (
            f"cross-partner exclusive overlap must be rejected, got {r.status_code}"
        )
        msg = str(r.json().get("message") or "")
        assert "exclusive" in msg.lower() and "conflict" in msg.lower(), (
            f"rejection should explain the exclusive conflict, got message={msg!r}"
        )
        logger.info("CHECK conflict → OK (400 'Exclusive territory conflict')")

    async with async_step("[3/3] No territory created for partner 2 on conflict"):
        data = r.json().get("data") or {}
        assert not (data.get("_id") or data.get("id")), (
            "a rejected exclusive overlap must NOT create a territory"
        )
        logger.info("CHECK no-op → OK (no territory created for partner 2)")

    logger.info("RESULT: cross-partner exclusive overlap on {} rejected", country)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_002(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_002: SA lists territories with filters - paginated, scoped, filterable.

    Contract on ``GET /sa-partners-api/v1/sa/territories``: returns 200 with the
    envelope; the assigned territory appears scoped to its partner with the right
    schema; and the exclusivityType filter returns only matching rows.
    """
    async with async_step("Setup: partner + an assigned territory"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        terr = await sa_partners_client.assign_territory(
            make_territory(pid, countries=["US"], exclusivityType="preferred")
        )
        tid = terr.data.get("_id") or terr.data.get("id")
        if tid:
            created_resources.add(lambda: sa_partners_client.delete_territory(tid))
        logger.info("SETUP: partner {} + territory {}", partner.data.get("code"), tid)

    async with async_step("[1/3] GET territories filtered by partnerId"):
        resp = await sa_partners_client.list_territories(partner_id=pid, limit=20)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert isinstance(resp.data, list), "`data` must be a list"
        # The territory list envelope is {statusCode, data, total} — no `message` field.
        assert resp.total is not None and resp.total >= 0, "`total` must be a non-negative integer"
        logger.info("CHECK envelope → OK (total={}, returned={})", resp.total, len(resp.data))

    async with async_step("[2/3] Assigned territory appears, scoped, with schema"):
        terrs = resp.data
        mine = next((t for t in terrs if (t.get("_id") or t.get("id")) == tid), None)
        assert mine, "assigned territory must appear in the list"
        assert mine.get("label"), "territory must carry a label"
        assert isinstance(mine.get("countries"), list) and mine.get("countries"), (
            "countries must be a list"
        )
        assert mine.get("exclusivityType"), "territory must carry an exclusivityType"
        assert all(str(t.get("partnerId")) == str(pid) for t in terrs), "list scoped to the partner"
        logger.info("CHECK list → OK (territory present, scoped, schema)")

    async with async_step("[3/3] exclusivityType filter returns only matching"):
        filtered = await sa_partners_client.list_territories(
            partner_id=pid, limit=20, exclusivityType="preferred"
        )
        assert all(t.get("exclusivityType") == "preferred" for t in filtered.data), (
            "exclusivityType filter must return only preferred territories"
        )
        logger.info("CHECK filter → OK (exclusivityType=preferred → {} row(s))", len(filtered.data))

    logger.info("RESULT: partner {} territory list verified", partner.data.get("code"))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_013(sa_partners_client):
    """PARTNER_API_TERRITORIES_013: list territories invalid filter/pagination - rejected (4xx, never 5xx).

    Negative counterpart of _002. Out-of-enum exclusivityType, invalid country,
    oversized limit, page=0, and a malformed partnerId must all be rejected with 4xx
    + a clear message (this endpoint validates strictly). All cases run.
    """
    cases = [
        ("bad exclusivityType", {"exclusivityType": "bogus"}, "exclusivitytype must be one of"),
        ("bad country", {"country": "ZZ"}, "iso31661"),
        ("limit over max", {"limit": 999999}, "must not exceed"),
        ("page=0", {"page": 0, "limit": 5}, "non-negative"),
        ("malformed partnerId", {"partnerId": "not-an-id"}, "mongodb id"),
    ]
    gaps: list[str] = []
    for idx, (label, params, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid list: {label}"):
            r = await sa_partners_client.raw_list_territories(expected_status=None, **params)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "territory-list negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid territory-list attempts rejected (never 5xx)", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_003(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_003: SA retrieves a single territory by id - full detail.

    Contract on ``GET /sa-partners-api/v1/sa/territories/{id}``: returns 200 with the
    full territory (id matches; partnerId/label/countries/exclusivityType present).
    """
    async with async_step("Setup: partner + an assigned territory"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        terr = await sa_partners_client.assign_territory(make_territory(pid, countries=["US"]))
        tid = terr.data.get("_id") or terr.data.get("id")
        if tid:
            created_resources.add(lambda: sa_partners_client.delete_territory(tid))
        assert tid, "precondition: territory must be created"
        logger.info("SETUP: territory {}", tid)

    async with async_step("[1/1] GET territory by id returns the full record"):
        resp = await sa_partners_client.get_territory(tid)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        d = resp.data
        assert (d.get("_id") or d.get("id")) == tid, "GET by id must return the same territory"
        for f in ("partnerId", "label", "countries", "exclusivityType"):
            assert d.get(f), f"territory must carry {f}"
        logger.info("CHECK by-id → OK (full territory returned)")

    logger.info("RESULT: territory {} retrieved by id", tid)


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # ghost (well-formed, absent) id returns 400, should be 404 — confirm with BE
async def test_partner_api_territories_014(sa_partners_client):
    """PARTNER_API_TERRITORIES_014: get territory with invalid id - rejected with the correct code.

    Negative counterpart of _003. Self-proving:

    * a GHOST id (well-formed but non-existent) → 404 'not found';
    * a MALFORMED id → 400 'invalid id'.

    GAP this test surfaces: the ghost id returns 400 (not 404) — the status contradicts
    its own "not found" message. That case asserts 404 and FAILS until the BE returns
    the correct code (confirm with BE). Same root cause as the deals get-by-id gap.
    """
    # (label, id, expected_status, message hint)
    cases = [
        ("ghost id (well-formed, absent)", _GHOST_ID, 404, "not found"),
        ("malformed id", "not-an-id", 400, "invalid id"),
    ]
    gaps: list[str] = []
    for idx, (label, tid, want_status, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject get-by-id: {label} → {want_status}"):
            r = await sa_partners_client.raw_get_territory(tid)
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

    assert not gaps, (
        "territory get-by-id negative gaps:\n  - "
        + "\n  - ".join(gaps)
        + "\n(a well-formed but non-existent id should be 404 Not Found, not 400 — confirm with BE)"
    )
    logger.info("RESULT: invalid territory get-by-id rejected (ghost/malformed)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_territories_004(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_004: SA removes a territory assignment - removed and no longer retrievable.

    Contract on ``DELETE /sa-partners-api/v1/sa/territories/{id}``: removing a
    territory returns HTTP 200 and the territory is no longer retrievable (GET by id
    → 4xx not-found).
    """
    async with async_step("Setup: partner + an assigned territory"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        terr = await sa_partners_client.assign_territory(make_territory(pid, countries=["US"]))
        tid = terr.data.get("_id") or terr.data.get("id")
        assert tid, "precondition: territory must be created"
        logger.info("SETUP: territory {}", tid)

    async with async_step("[1/2] Delete the territory"):
        r = await sa_partners_client.delete_territory(tid)
        assert r.status_code in (200, 204), f"delete must succeed, got {r.status_code}"
        logger.info("CHECK deleted → OK ({})", r.status_code)

    async with async_step("[2/2] The territory is no longer retrievable"):
        g = await sa_partners_client.raw_get_territory(tid)
        assert 400 <= g.status_code < 500, (
            f"a removed territory must not be retrievable, got {g.status_code}"
        )
        logger.info("CHECK gone → OK (GET by id → {})", g.status_code)

    logger.info("RESULT: territory {} removed", tid)


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # ghost / already-removed (well-formed, absent) id returns 400, should be 404 — confirm with BE
async def test_partner_api_territories_015(sa_partners_client, created_resources):
    """PARTNER_API_TERRITORIES_015: delete territory invalid/already-removed - rejected with the correct code.

    Negative counterpart of _004. A GHOST id (well-formed but non-existent) and an
    already-removed territory both target a resource that does not exist → 404
    'not found'; a MALFORMED id → 400 'invalid id'. The already-removed case documents
    delete's repeat behavior (mutating action, not a duplicate-create, so no separate
    idempotency TC).

    GAP this test surfaces: the not-found targets return 400 (not 404) — the status
    contradicts the "not found" message. Those cases assert 404 and FAIL until the BE
    returns the correct code (confirm with BE). Same root cause as the deals get-by-id gap.
    """
    async with async_step("Setup: partner + a territory to delete"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        terr = await sa_partners_client.assign_territory(make_territory(pid, countries=["US"]))
        tid = terr.data.get("_id") or terr.data.get("id")
        assert tid, "precondition: territory must be created"

    # (label, id, expected_status, message hint)
    cases = [
        ("ghost id (well-formed, absent)", _GHOST_ID, 404, "not found"),
        ("malformed id", "not-an-id", 400, "invalid id"),
    ]
    n_steps = len(cases) + 1
    gaps: list[str] = []
    for idx, (label, did, want_status, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{n_steps}] Reject delete: {label} → {want_status}"):
            r = await sa_partners_client.delete_territory(did, expected_status=None)
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

    async with async_step(
        f"[{n_steps}/{n_steps}] Re-delete an already-removed territory → 404 not found"
    ):
        await sa_partners_client.delete_territory(tid)
        r = await sa_partners_client.delete_territory(tid, expected_status=None)
        msg = str(r.json().get("message") or "")
        if r.status_code == 404 and "not found" in msg.lower():
            logger.info("CHECK already-removed → OK (404, no territory to delete)")
        else:
            gaps.append(f"already-removed: expected 404, got {r.status_code}, msg={msg!r}")
            logger.error(
                "CHECK already-removed → FAIL (expected 404, got {}, msg={!r})", r.status_code, msg
            )

    assert not gaps, (
        "territory-delete negative gaps:\n  - "
        + "\n  - ".join(gaps)
        + "\n(a well-formed but non-existent id should be 404 Not Found, not 400 — confirm with BE)"
    )
    logger.info("RESULT: all invalid/illegal territory-delete attempts rejected")
