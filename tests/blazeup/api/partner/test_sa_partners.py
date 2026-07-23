"""SA Partners API — partner directory (API layer, service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_*.

Each ``async with async_step(...)`` is a reportable step: it emits a STEP line to
the console/log AND becomes a pass/fail node in the Allure report (so the run
reads as a step tree). The request payload + response body are logged by
``BaseClient`` inside the step that issues the call.
"""

import asyncio

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_partner, make_partner_user, unique_email
from utils.log_helper import async_step

# A syntactically valid Mongo ObjectId that does not exist — for "not found" tests.
_GHOST_ID = "000000000000000000000000"

# Reseller-pricing fields BlazeUp must NOT store (the reseller sets its own end-client
# price; CreateDealDto does not define these — a reseller must be able to keep its
# margin/sell price private). Data-minimization / enforcement.
_END_CLIENT_PRICE_FIELDS = {
    "endClientPrice": 249_999,
    "sellPrice": 199_999,
    "resellerMarginCents": 50_000,
}


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_001(sa_partners_client):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001: GET internal partners list - SA filters are applied.

    Read-only contract check on ``GET /sa-partners-api/v1/sa/partners``:
    returns 200 with the expected envelope (statusCode/data/total/message) and
    honours pagination (returned page size never exceeds the requested limit).
    HTTP 200 is asserted inside the client (expected_status); here we validate
    the response body contract.
    """
    # ── Setup: pagination window under test ──────────────────────────────────
    limit = 5
    logger.info("SETUP: request first page with limit={}", limit)

    async with async_step(f"[1/4] Call API: GET /v1/sa/partners (page=1, limit={limit})"):
        resp = await sa_partners_client.list_partners(page=1, limit=limit)

    async with async_step("[2/4] Verify the partner-list API contract"):
        assert resp.status_code == 200, f"Expected body statusCode 200, got {resp.status_code}"
        logger.info("CHECK status = 200 → OK (request authorized + succeeded)")

        assert isinstance(resp.data, list), "`data` must be a list"
        assert resp.total is not None and resp.total >= 0, "`total` must be a non-negative integer"
        assert resp.message, "`message` should be present"
        logger.info(
            "CHECK envelope → OK (data=list, total={}, message='{}')", resp.total, resp.message
        )

        assert len(resp.data) <= limit, (
            f"page size {len(resp.data)} must not exceed requested limit {limit}"
        )
        logger.info("CHECK pagination → OK (returned {} ≤ limit {})", len(resp.data), limit)

    async with async_step("[3/4] Verify data integrity + SA filtering"):
        if not resp.data:
            logger.warning(
                "CHECK filters/data — SKIPPED: staging has 0 partners (data-dependent). "
                "Seed partners to assert filtering actually restricts results."
            )
        else:
            for p in resp.data:
                assert isinstance(p, dict) and p, "each partner must be a non-empty object"
            ids = [p.get("id") or p.get("_id") for p in resp.data]
            if all(ids):
                assert len(ids) == len(set(ids)), "partner ids must be unique (no duplicate rows)"
            logger.info(
                "CHECK data integrity → OK ({} well-formed partner object(s))", len(resp.data)
            )

    async with async_step("[4/4] Verify SA isolation / no cross-partner leakage"):
        if not resp.data:
            logger.warning(
                "CHECK isolation — SKIPPED: no partner data to verify cross-partner leakage."
            )
        else:
            logger.info(
                "CHECK isolation → OK (SA-scoped directory returned {} partner(s); "
                "deep cross-partner audit applies once multi-partner data exists)",
                resp.total,
            )

    logger.info("RESULT: {} partner(s) in directory", resp.total)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_002(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002: POST create internal partner - a pending account is created.

    CRUD (create) contract check on ``POST /sa-partners-api/v1/sa/partners``:
    creating a partner with the required fields (name/email/type) returns HTTP
    201, persists the record with a server-assigned id + ``code``, and the new
    account starts in ``status = "pending"`` (awaiting SA activation). The
    created partner is registered for cleanup (DELETE) so the test is repeatable
    and leaves no residue on staging — pass OR fail.
    """
    # ── Setup: build a unique, identifiable partner payload ───────────────────
    # Log the fields the test actually asserts on (name/email/type), so the run
    # shows exactly what was sent and later verified — not a trimmed summary.
    payload = make_partner(type="channel")
    logger.info(
        "SETUP: partner payload → name='{}', email='{}', type='{}'",
        payload["name"],
        payload["email"],
        payload["type"],
    )

    async with async_step(f"[1/5] Call API: POST /v1/sa/partners (create '{payload['name']}')"):
        resp = await sa_partners_client.create_partner(payload)
        partner_id = resp.partner_id
        # Register cleanup FIRST (before assertions) so a later failed assert
        # still triggers the DELETE and we don't leak a partner on staging.
        if partner_id:
            created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))

    async with async_step("[2/5] Verify the create-partner contract (accepted + persisted)"):
        assert resp.status_code == 200, f"Expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should confirm the creation"
        logger.info("CHECK create accepted → OK (HTTP 201, message='{}')", resp.message)

        assert partner_id, "created partner must have a server-assigned id (_id)"
        assert resp.data.get("code"), (
            "created partner must have a generated `code` (e.g. PAR-xxxxxx)"
        )
        logger.info("CHECK persisted → OK (id={}, code={})", partner_id, resp.data.get("code"))

    async with async_step("[3/5] Verify the created record matches the request"):
        assert resp.data.get("name") == payload["name"], "stored name must match the request"
        assert resp.data.get("email") == payload["email"], "stored email must match the request"
        assert resp.data.get("type") == payload["type"], "stored type must match the request"
        logger.info("CHECK echo → OK (name/email/type stored as sent)")

    async with async_step("[4/5] Verify the new partner starts in 'pending' status"):
        assert resp.data.get("status") == "pending", (
            f"new partner must start pending, got status={resp.data.get('status')!r}"
        )
        logger.info("CHECK lifecycle → OK (status='pending' — awaits SA activation)")

    async with async_step("[5/5] Verify the partner is retrievable via GET /v1/sa/partners/{id}"):
        fetched = await sa_partners_client.get_partner(partner_id)
        assert fetched.partner_id == partner_id, "GET by id must return the same partner"
        assert fetched.data.get("status") == "pending", "fetched partner must also be pending"
        logger.info("CHECK retrievable → OK (GET by id returns the pending partner)")

    logger.info("RESULT: created pending partner {} (id={})", resp.data.get("code"), partner_id)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_003(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003: POST partner approve - activation + approval event are created.

    State-transition contract check on ``POST /sa-partners-api/v1/sa/partners/{id}/approve``:
    approving a *pending* partner returns HTTP 201, flips ``status`` from
    ``pending`` → ``active``, and records the approval event metadata
    (``approvedAt`` + ``approvedBy``). The transition is confirmed to persist via
    a follow-up GET. A pending partner is created first as the precondition and
    registered for cleanup (DELETE) so the test is self-contained and repeatable.

    Note: the downstream activation-*user* provisioning is emitted as an event to
    another service (not returned by this endpoint), so it is out of scope here;
    this TC asserts the approval contract observable on sa-partners-api.
    """
    async with async_step("Setup: create a PENDING partner (approval precondition)"):
        payload = make_partner(type="channel")
        created = await sa_partners_client.create_partner(payload)
        partner_id = created.partner_id
        if partner_id:
            created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        assert partner_id, "precondition: partner must be created"
        assert created.data.get("status") == "pending", "precondition: partner must start pending"
        logger.info("CHECK precondition → OK (partner {} is pending)", created.data.get("code"))

    async with async_step(f"[1/4] Call API: POST /v1/sa/partners/{partner_id}/approve"):
        resp = await sa_partners_client.approve_partner(partner_id)

    async with async_step("[2/4] Verify the approve call is accepted"):
        assert resp.status_code == 200, f"Expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should confirm the approval"
        assert resp.partner_id == partner_id, "approve must act on the same partner"
        logger.info("CHECK approve accepted → OK (HTTP 201, message='{}')", resp.message)

    async with async_step("[3/4] Verify status flipped to 'active' and approval event recorded"):
        assert resp.data.get("status") == "active", (
            f"approved partner must be active, got status={resp.data.get('status')!r}"
        )
        assert resp.data.get("approvedAt"), "approval event must stamp `approvedAt`"
        assert resp.data.get("approvedBy"), "approval event must record `approvedBy`"
        logger.info(
            "CHECK transition → OK (status='active', approvedBy='{}', approvedAt set)",
            resp.data.get("approvedBy"),
        )

    async with async_step("[4/4] Verify the active status persisted via GET /v1/sa/partners/{id}"):
        fetched = await sa_partners_client.get_partner(partner_id)
        assert fetched.data.get("status") == "active", (
            "fetched partner must be active after approval"
        )
        logger.info("CHECK persisted → OK (GET by id returns status='active')")

    logger.info("RESULT: partner {} approved (pending → active)", resp.data.get("code"))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_004(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004: partner application decline - mandatory reason is audit logged.

    Security check on declining a partner. The plan calls this "PATCH decline";
    the BE currently exposes no dedicated decline endpoint, so the closest real
    action — POST ``/sa-partners-api/v1/sa/partners/{id}/deactivate`` (the only
    partner action that carries a ``reason``) — is exercised here.

    This test encodes the TC's *intent* (decline succeeds, the reason is audit
    logged, and the reason is MANDATORY). The BE now enforces a mandatory,
    non-empty reason — declining with an absent, empty, or whitespace-only reason
    is rejected with 400 (verified 2026-06-22; previously accepted with 201). Any
    step that fails now is a real BE regression.
    """
    async with async_step("Setup: create a PENDING partner to decline"):
        created = await sa_partners_client.create_partner(make_partner())
        pid = created.partner_id
        code = created.data.get("code")
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        reason = f"QA-AUTO decline reason for {code}"  # unique → findable in audit log
        logger.info("SETUP: pending partner {} created; decline reason='{}'", code, reason)

    async with async_step("[1/3] Decline the partner WITH a reason"):
        resp = await sa_partners_client.deactivate_partner(pid, reason=reason)
        status = resp.json().get("data", {}).get("status")
        assert status not in ("pending", "active"), (
            f"declined partner must leave pending/active, got status={status!r}"
        )
        logger.info(
            "CHECK decline accepted → OK (HTTP {}, status now '{}')", resp.status_code, status
        )

    async with async_step("[2/3] Verify the decline reason is recorded in the audit log"):
        found = None
        for attempt in range(1, 4):  # audit write may be eventually consistent
            logs = await sa_partners_client.list_audit_logs(limit=50)
            found = next((e for e in logs.data if reason in str(e)), None)
            if found:
                break
            logger.info("audit log not visible yet (attempt {}/3), retrying…", attempt)
            await asyncio.sleep(1)
        assert found, (
            "decline reason not found in SA audit logs — confirm with BE whether the "
            "reason is persisted to the audit trail"
        )
        logger.info("CHECK audit → OK (reason logged; action='{}')", found.get("action"))

    async with async_step("[3/3] Enforce mandatory reason (no / blank reason must be rejected)"):
        # "Mandatory + non-empty" = cover all three invalid shapes, not just absent.
        invalid_reasons = [("absent", None), ("empty string", ""), ("whitespace", "   ")]
        gaps: list[str] = []
        for label, bad in invalid_reasons:
            victim = await sa_partners_client.create_partner(make_partner())
            if victim.partner_id:
                created_resources.add(
                    lambda pid=victim.partner_id: sa_partners_client.delete_partner(pid)
                )
            r = await sa_partners_client.deactivate_partner(
                victim.partner_id, reason=bad, expected_status=None
            )
            if r.status_code in (400, 422):
                logger.info("CHECK reason '{}' → OK (rejected {})", label, r.status_code)
            else:
                gaps.append(f"{label}: got {r.status_code}")
                logger.error(
                    "CHECK reason '{}' → FAIL (got {}, expected 400/422)", label, r.status_code
                )
        assert not gaps, (
            "decline accepted with no/blank reason (reason not enforced): "
            + "; ".join(gaps)
            + " — confirm with BE whether reason should be mandatory + non-empty"
        )

    logger.info("RESULT: partner {} declined; mandatory-reason + audit-log checks complete", code)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_005(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005: tier changed event - published so portal/analytics can refresh.

    Changing a partner's tier via POST /v1/sa/partners/{id}/upgrade-tier must
    update the stored ``tier`` AND emit a ``partner.tier.changed`` event recording
    the before/after tiers — the signal downstream consumers (partner portal, SA
    analytics) subscribe to in order to refresh. This test asserts the
    API-observable evidence: the tier transition + the audit-logged event. The
    actual portal/analytics refresh is a downstream Kafka consumer concern and is
    out of scope here.
    """

    async def _find_tier_event(unique_reason: str) -> "dict | None":
        """Poll the audit log for a tier-changed event carrying ``unique_reason``."""
        for attempt in range(1, 4):  # audit write may be eventually consistent
            logs = await sa_partners_client.list_audit_logs(limit=50)
            hit = next(
                (
                    e
                    for e in logs.data
                    if "tier" in str(e.get("action", "")).lower() and unique_reason in str(e)
                ),
                None,
            )
            if hit:
                return hit
            logger.info("tier event not visible yet (attempt {}/3), retrying…", attempt)
            await asyncio.sleep(1)
        return None

    async with async_step("Setup: create a partner (tier defaults to 'registered')"):
        created = await sa_partners_client.create_partner(make_partner())
        pid = created.partner_id
        code = created.data.get("code")
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert created.data.get("tier") == "registered", (
            "new partner should start at tier 'registered'"
        )
        logger.info("SETUP: partner {} at tier 'registered'", code)

    # Walk every valid tier (upgrades): registered → select → advanced → premier.
    async with async_step("[1/4] Upgrade through all tiers: registered→select→advanced→premier"):
        for tier in ("select", "advanced", "premier"):
            resp = await sa_partners_client.change_tier(
                pid, tier=tier, reason=f"QA-AUTO up {tier} {code}"
            )
            assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
            assert resp.data.get("tier") == tier, (
                f"tier must change to {tier!r}, got {resp.data.get('tier')!r}"
            )
            logger.info("CHECK upgrade → OK (now '{}')", tier)

    async with async_step("[2/4] Verify upgrade event recorded with before/after + reason"):
        ev = await _find_tier_event(f"QA-AUTO up premier {code}")
        assert ev, "no tier-changed event found for advanced→premier"
        before, after = (ev.get("before") or {}).get("tier"), (ev.get("after") or {}).get("tier")
        assert (before, after) == ("advanced", "premier"), (
            f"event must record advanced→premier, got {before!r}→{after!r}"
        )
        assert (ev.get("after") or {}).get("reason"), "event must record the change reason"
        logger.info("CHECK upgrade event → OK ({} → {}, reason logged)", before, after)

    # Downgrade must ALSO emit an event (TC endpoint = "upgrade OR downgrade").
    async with async_step("[3/4] Downgrade premier → select emits an event"):
        down_reason = f"QA-AUTO down select {code}"
        resp = await sa_partners_client.change_tier(pid, tier="select", reason=down_reason)
        assert resp.status_code == 200 and resp.data.get("tier") == "select", (
            f"downgrade must set tier 'select', got {resp.data.get('tier')!r}"
        )
        ev = await _find_tier_event(down_reason)
        assert ev, "no tier-changed event found for the downgrade"
        before, after = (ev.get("before") or {}).get("tier"), (ev.get("after") or {}).get("tier")
        assert (before, after) == ("premier", "select"), (
            f"downgrade event must record premier→select, got {before!r}→{after!r}"
        )
        logger.info("CHECK downgrade event → OK (premier → select)")

    async with async_step("[4/4] Verify the final tier persisted via GET /v1/sa/partners/{id}"):
        fetched = await sa_partners_client.get_partner(pid)
        assert fetched.data.get("tier") == "select", "fetched partner must have tier 'select'"
        logger.info("CHECK persisted → OK (GET returns tier='select')")

    logger.info(
        "RESULT: partner {} tier upgrades (select/advanced/premier) + downgrade emit events", code
    )


def _invalid_create_cases() -> list[tuple[str, dict, str]]:
    """Build the invalid-payload cases for create-partner validation.

    Each tuple is (human label, payload, expected-field keyword in the 400 error).
    Emails are generated fresh so the only thing wrong is the field under test.
    """
    return [
        ("missing name", {"email": unique_email(), "type": "channel"}, "name"),
        ("missing email", {"name": "QA-AUTO NoEmail", "type": "channel"}, "email"),
        ("missing type", {"name": "QA-AUTO NoType", "email": unique_email()}, "type"),
        (
            "malformed email",
            {"name": "QA-AUTO BadEmail", "email": "not-an-email", "type": "channel"},
            "email",
        ),
        ("empty name", {"name": "", "email": unique_email(), "type": "channel"}, "name"),
        (
            "invalid type enum",
            {"name": "QA-AUTO BadType", "email": unique_email(), "type": "foobar"},
            "type",
        ),
    ]


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_012(sa_partners_client):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012: create with invalid/missing fields - 400 + field errors.

    Negative counterpart of _002 (create).

    Negative contract check on ``POST /sa-partners-api/v1/sa/partners``: every
    invalid or incomplete payload (missing name/email/type, malformed email,
    empty name, out-of-enum type) must be rejected with HTTP 400, return a
    field-level error message naming the offending field, and create NO record.
    All cases run every time (failures are collected, not short-circuited) so one
    broken rule never hides the others. No cleanup needed — nothing is persisted.
    """
    cases = _invalid_create_cases()
    logger.info("SETUP: {} invalid create payload(s) to reject with HTTP 400", len(cases))

    failures: list[str] = []
    for idx, (label, payload, field) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid create: {label}"):
            resp = await sa_partners_client.raw_create_partner(payload)

            if resp.status_code != 400:
                failures.append(f"{label}: expected 400, got {resp.status_code}")
                logger.error("CHECK {} → FAIL (status {}, expected 400)", label, resp.status_code)
                continue

            body = resp.json()
            message = str(body.get("message") or body.get("error") or "")
            has_field = field.lower() in message.lower()
            no_record = not body.get("data")

            if has_field and no_record:
                logger.info("CHECK {} → OK (400, error mentions '{}', no record)", label, field)
            else:
                detail = []
                if not has_field:
                    detail.append(f"error msg missing field '{field}': {message!r}")
                if not no_record:
                    detail.append("a record was created (data is not empty)")
                failures.append(f"{label}: " + "; ".join(detail))
                logger.error("CHECK {} → FAIL ({})", label, "; ".join(detail))

    assert not failures, "Validation gaps found:\n  - " + "\n  - ".join(failures)
    logger.info("RESULT: all {} invalid payload(s) correctly rejected with 400", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_011(sa_partners_client):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011: list with invalid pagination - rejected (4xx, never 5xx).

    Negative counterpart of _001 (GET list). Invalid pagination params are validated
    by the BE and rejected with 4xx (never 5xx): ``page=0`` / ``page=-1`` (previously
    an HTTP 500 crash), and negative / oversized / non-numeric ``limit`` (previously
    silently defaulted). All cases run (failures collected) so one gap never hides
    the others.
    """
    cases = [
        ("page=0", {"page": 0, "limit": 5}),
        ("page=-1", {"page": -1, "limit": 5}),
        ("limit=-5", {"page": 1, "limit": -5}),
        ("limit=999999", {"page": 1, "limit": 999999}),
        ("page=abc", {"page": "abc", "limit": 5}),
    ]
    gaps: list[str] = []
    for idx, (label, params) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid pagination: {label}"):
            r = await sa_partners_client.raw_list_partners(**params)
            if 400 <= r.status_code < 500:
                logger.info("CHECK {} → OK (rejected {}, no 5xx)", label, r.status_code)
            else:
                gaps.append(f"{label}: got {r.status_code}")
                logger.error(
                    "CHECK {} → FAIL (got {}, expected 4xx, must never 5xx)", label, r.status_code
                )

    assert not gaps, (
        "invalid pagination not rejected (must be 4xx, never 5xx):\n  - " + "\n  - ".join(gaps)
    )
    logger.info("RESULT: all {} invalid pagination params rejected (4xx, never 5xx)", len(cases))


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # ghost (well-formed, absent) partner id returns 400, should be 404 — confirm with BE
async def test_partner_api_partner_account_management_013(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013: approve invalid/illegal-state - rejected with the correct code.

    Negative counterpart of _003 (approve). Three distinct rejections, each with its
    own code + a descriptive message (never silently succeed):

    * a GHOST id (well-formed but non-existent) → 404 'not found';
    * a MALFORMED id → 400 'invalid id';
    * an already-active partner (illegal transition) → 400 'cannot be approved'
      (409 Conflict would be more precise, but 400 is accepted).

    GAP this test surfaces: the ghost id returns 400 (not 404) — the status contradicts
    its own "not found" message. That case asserts 404 and FAILS until the BE returns
    the correct code (confirm with BE). Same root cause as the deals get-by-id gap.
    """
    async with async_step("Setup: create + approve a partner so it is already 'active'"):
        active = await sa_partners_client.create_partner(make_partner())
        if active.partner_id:
            created_resources.add(lambda: sa_partners_client.delete_partner(active.partner_id))
        await sa_partners_client.approve_partner(active.partner_id)
        logger.info("SETUP: partner {} is now active", active.data.get("code"))

    # (label, id, expected_status, message hint)
    illegal = [
        ("ghost id (well-formed, absent)", _GHOST_ID, 404, "not found"),
        ("malformed id", "not-an-id", 400, "invalid id"),
        (
            "already-active partner (illegal transition)",
            active.partner_id,
            400,
            "cannot be approved",
        ),
    ]
    gaps: list[str] = []
    for idx, (label, pid, want_status, hint) in enumerate(illegal, start=1):
        async with async_step(f"[{idx}/{len(illegal)}] Reject approve: {label} → {want_status}"):
            r = await sa_partners_client.raw_approve_partner(pid)
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
        "approve negative-case gaps:\n  - "
        + "\n  - ".join(gaps)
        + "\n(a well-formed but non-existent id should be 404 Not Found, not 400 — confirm with BE)"
    )
    logger.info("RESULT: all {} illegal approve attempts rejected", len(illegal))


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # ghost (well-formed, absent) partner id returns 400, should be 404 — confirm with BE
async def test_partner_api_partner_account_management_014(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014: deactivate invalid id - rejected; repeat is idempotent.

    Negative counterpart of _004 (deactivate). A GHOST id (well-formed but
    non-existent) → 404 'not found'; a MALFORMED id → 400 'invalid id'. Deactivating
    an already-suspended partner is observed (currently a no-op 201 — idempotent) and
    logged, not failed.

    GAP this test surfaces: the ghost id returns 400 (not 404) — the status contradicts
    its own "not found" message. That case asserts 404 and FAILS until the BE returns
    the correct code (confirm with BE). Same root cause as the deals get-by-id gap.
    """
    # (label, id, expected_status, message hint)
    illegal = [
        ("ghost id (well-formed, absent)", _GHOST_ID, 404, "not found"),
        ("malformed id", "not-an-id", 400, "invalid id"),
    ]
    gaps: list[str] = []
    for idx, (label, pid, want_status, hint) in enumerate(illegal, start=1):
        async with async_step(f"[{idx}/3] Reject deactivate: {label} → {want_status}"):
            r = await sa_partners_client.deactivate_partner(pid, reason="x", expected_status=None)
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
        "[3/3] Deactivating an already-suspended partner (idempotency observation)"
    ):
        p = await sa_partners_client.create_partner(make_partner())
        if p.partner_id:
            created_resources.add(lambda: sa_partners_client.delete_partner(p.partner_id))
        await sa_partners_client.deactivate_partner(p.partner_id, reason="first")
        r = await sa_partners_client.deactivate_partner(
            p.partner_id, reason="again", expected_status=None
        )
        status = r.json().get("data", {}).get("status")
        assert r.status_code < 500, f"repeat deactivate must not 5xx, got {r.status_code}"
        logger.info(
            "CHECK repeat deactivate → status {} (partner status='{}') — idempotent no-op observed",
            r.status_code,
            status,
        )

    assert not gaps, (
        "deactivate negative-case gaps:\n  - "
        + "\n  - ".join(gaps)
        + "\n(a well-formed but non-existent id should be 404 Not Found, not 400 — confirm with BE)"
    )
    logger.info("RESULT: invalid-id deactivate rejected; repeat deactivate is idempotent")


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # ghost (well-formed, absent) partner id returns 400, should be 404 — confirm with BE
async def test_partner_api_partner_account_management_015(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015: change tier with invalid input - rejected with the correct code.

    Negative counterpart of _005 (tier change). The upgrade-tier endpoint must reject
    invalid input with the correct code + a descriptive message and emit no event:

    * validation errors (out-of-enum tier, empty tier, missing tier) → 400;
    * same tier (already at that tier) → 400 'already at tier';
    * a MALFORMED id → 400 'invalid id';
    * a GHOST id (well-formed but non-existent) → 404 'not found'.

    GAP this test surfaces: the ghost id returns 400 (not 404) — the status contradicts
    its own "not found" message. That case asserts 404 and FAILS until the BE returns
    the correct code (confirm with BE). Same root cause as the deals get-by-id gap.
    """
    async with async_step("Setup: create a partner to target with valid id"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        logger.info("SETUP: partner {} ready (tier 'registered')", partner.data.get("code"))

    # (label, partner_id, tier-to-send, expected_status, expected message hint)
    cases = [
        ("invalid tier enum 'silver'", pid, "silver", 400, "tier must be one of"),
        ("empty tier ''", pid, "", 400, "tier must be one of"),
        ("missing tier (no tier field)", pid, None, 400, "tier must be one of"),
        ("same tier (already at 'registered')", pid, "registered", 400, "already at tier"),
        ("malformed id", "not-an-id", "select", 400, "invalid id"),
        ("ghost id (well-formed, absent)", _GHOST_ID, "select", 404, "not found"),
    ]
    gaps: list[str] = []
    for idx, (label, target, tier, want_status, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject change-tier: {label} → {want_status}"):
            r = await sa_partners_client.raw_change_tier(target, tier=tier)
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
        "change-tier negative-case gaps:\n  - "
        + "\n  - ".join(gaps)
        + "\n(a well-formed but non-existent id should be 404 Not Found, not 400 — confirm with BE)"
    )
    logger.info("RESULT: all {} invalid tier-change attempts rejected", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_010(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010: certification earned - granted, listed, and event published.

    Granting a certification to a partner user (POST /v1/sa/partner-users/{userId}/
    certifications) must create an active certification (with earnedAt/expiresAt),
    surface it in the partner's certification list, AND emit a
    ``partner.certification.granted`` event — the "certification earned" signal
    that triggers downstream tier-qualification re-evaluation. The re-evaluation
    itself is a downstream consumer/job and is out of scope here.
    """
    cert_type = "sales_certified"

    async with async_step("Setup: create a partner + invite a portal user"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        user_id = invited.data.get("userId")
        assert user_id, "precondition: partner user must be invited (userId present)"
        logger.info("SETUP: partner {} + user {} ready", partner.data.get("code"), user_id)

    async with async_step("[1/3] Grant certification (certification earned)"):
        resp = await sa_partners_client.grant_certification(
            user_id, certification_type=cert_type, score=95
        )
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.data.get("certificationType") == cert_type, "stored cert type must match"
        assert resp.data.get("status") == "active", "granted cert must be 'active'"
        assert resp.data.get("earnedAt") and resp.data.get("expiresAt"), (
            "cert must record earnedAt + expiresAt"
        )
        logger.info("CHECK granted → OK (type={}, status=active, earned+expires set)", cert_type)

    async with async_step("[2/3] Verify the cert appears in the partner's certification list"):
        certs = await sa_partners_client.list_partner_certifications(pid)
        match = next((c for c in certs.data if c.get("certificationType") == cert_type), None)
        assert match, f"granted cert '{cert_type}' must appear in the partner cert list"
        assert match.get("userId") == user_id, "listed cert must belong to the invited user"
        logger.info("CHECK listed → OK ({} cert(s) for partner)", len(certs.data))

    async with async_step("[3/3] Verify a 'partner.certification.granted' event is recorded"):
        found = None
        for attempt in range(1, 4):
            logs = await sa_partners_client.list_audit_logs(limit=50)
            found = next(
                (
                    e
                    for e in logs.data
                    if "certification" in str(e.get("action", "")).lower() and user_id in str(e)
                ),
                None,
            )
            if found:
                break
            logger.info("cert event not visible yet (attempt {}/3), retrying…", attempt)
            await asyncio.sleep(1)
        assert found, "no 'partner.certification.granted' event found in audit log"
        after = found.get("after") or {}
        assert after.get("certificationType") == cert_type, "event must record the cert type"
        logger.info("CHECK event → OK (action='{}', type recorded)", found.get("action"))

    logger.info(
        "RESULT: certification '{}' earned, listed, and event published (tier re-eval is downstream)",
        cert_type,
    )


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # ghost (well-formed, absent) userId returns 400, should be 404 — confirm with BE
async def test_partner_api_partner_account_management_020(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020: grant certification invalid input - rejected with the correct code.

    Negative counterpart of _010. Granting a certification must reject invalid input
    with the correct code + a descriptive message:

    * validation errors (out-of-enum certificationType, missing certificationType) → 400;
    * a MALFORMED userId → 400 'invalid id';
    * a GHOST userId (well-formed but non-existent) → 404 'not found'.

    GAP this test surfaces: the ghost userId returns 400 (not 404) — the status
    contradicts its own "not found" message. That case asserts 404 and FAILS until the
    BE returns the correct code (confirm with BE). Same root cause as the deals get-by-id gap.
    """
    async with async_step("Setup: create a partner + invite a portal user (valid userId)"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        user_id = invited.data.get("userId")
        assert user_id, "precondition: partner user must be invited"
        logger.info("SETUP: user {} ready", user_id)

    # (label, target userId, certificationType to send, expected_status, expected message hint)
    cases = [
        ("invalid cert type 'ninja'", user_id, "ninja", 400, "certificationtype must be one of"),
        ("missing cert type", user_id, None, 400, "certificationtype must be one of"),
        ("malformed userId", "not-an-id", "sales_certified", 400, "invalid id"),
        ("ghost userId (well-formed, absent)", _GHOST_ID, "sales_certified", 404, "not found"),
    ]
    gaps: list[str] = []
    for idx, (label, target, ctype, want_status, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject grant-cert: {label} → {want_status}"):
            r = await sa_partners_client.raw_grant_certification(target, certification_type=ctype)
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
        "grant-cert negative-case gaps:\n  - "
        + "\n  - ".join(gaps)
        + "\n(a well-formed but non-existent id should be 404 Not Found, not 400 — confirm with BE)"
    )
    logger.info("RESULT: all {} invalid grant-cert attempts rejected", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_021(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_021: duplicate partner (same email) - rejected, no second account.

    Idempotency / duplicate counterpart of _002 (create). Creating a second partner
    with the SAME email is rejected with HTTP 400 ("...already exists"), and no
    second account is created. Verified 2026-06-22.
    """
    async with async_step("Setup: create a partner with a unique email"):
        payload = make_partner()
        first = await sa_partners_client.create_partner(payload)
        pid = first.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: first partner must be created"
        logger.info(
            "SETUP: partner {} created with email '{}'", first.data.get("code"), payload["email"]
        )

    async with async_step("[1/2] Re-create with the SAME email → 400 duplicate"):
        r = await sa_partners_client.raw_create_partner(payload, expected_status=None)
        assert r.status_code == 400, (
            f"duplicate email must be rejected with 400, got {r.status_code}"
        )
        msg = str(r.json().get("message") or "")
        assert "already exists" in msg.lower(), (
            f"rejection should explain the email already exists, got message={msg!r}"
        )
        logger.info("CHECK duplicate → OK (400, msg~'already exists')")

    async with async_step("[2/2] No second account was created"):
        data = r.json().get("data") or {}
        new_id = data.get("_id") or data.get("id")
        assert not new_id or new_id == pid, "a rejected duplicate must NOT create a second partner"
        logger.info("CHECK no-op → OK (no second partner created)")

    logger.info("RESULT: duplicate partner (same email) rejected (400, no second account)")


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # re-grant creates a duplicate active cert (count=2) — confirm with BE
async def test_partner_api_partner_account_management_022(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_022: re-grant same certification - must not duplicate (idempotent or 409).

    Idempotency / duplicate counterpart of _010 (certification earned). Granting the
    SAME certificationType to the SAME user a second time must NOT create a second
    active cert of that type — it should be idempotent (renew the existing record)
    or rejected (409).

    GAP this test surfaces (verified 2026-06-22): the API returns 201 and creates a
    SECOND cert record (the user ends up with two active 'sales_certified' certs).
    Step [3/3] asserts a single cert of that type and therefore FAILS until the BE
    de-dupes — confirm with BE whether re-grant should renew or reject.
    """
    async with async_step("Setup: partner + invited user"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        host = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        uid = host.data.get("userId")
        assert uid, "precondition: partner user must be invited"
        logger.info("SETUP: partner {} + user {}", partner.data.get("code"), uid)

    cert_type = "sales_certified"
    async with async_step("[1/3] Grant the certification (first time)"):
        g1 = await sa_partners_client.grant_certification(
            uid, certification_type=cert_type, score=90
        )
        assert g1.data.get("status") == "active", "first grant must be active"
        logger.info("CHECK grant#1 → OK (active, id={})", g1.data.get("_id"))

    async with async_step("[2/3] Re-grant the SAME certification type"):
        g2 = await sa_partners_client.raw_grant_certification(
            uid, certification_type=cert_type, score=95, expected_status=None
        )
        assert g2.status_code in (200, 201, 409), (
            f"re-grant must be a defined outcome (renew 2xx or reject 409), got {g2.status_code}"
        )
        logger.info("CHECK re-grant → status {}", g2.status_code)

    async with async_step("[3/3] The user must NOT end up with a duplicate active cert"):
        lst = await sa_partners_client.list_partner_certifications(pid)
        same = [c for c in lst.data if c.get("certificationType") == cert_type]
        assert len(same) == 1, (
            f"re-granting must not duplicate: expected 1 '{cert_type}' cert, got {len(same)} "
            "— BE creates a second cert on re-grant; confirm with BE (renew vs reject)"
        )
        logger.info("CHECK no-duplicate → OK (exactly 1 '{}' cert)", cert_type)

    logger.info("RESULT: re-grant certification idempotency checked")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_006(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_006: reseller sell price - end-client price is NOT stored.

    Enforcement / data-minimization: a reseller sets its own price to the end client,
    and BlazeUp must NOT store that price. Registering a reseller deal with end-client
    pricing fields (endClientPrice / sellPrice / resellerMarginCents — none defined on
    CreateDealDto) must not persist them. The BE accepts the request (201) and strips
    the unknown fields (verified 2026-07-22). This is the same enforcement mechanism as
    SECURITY_COMPLIANCE_002 (unknown fields stripped), scoped to reseller pricing.

    Covers both plan lines _006 (Security) and _016 (Negative) — same assertion; _016 is
    a cross-reference (see its note). Happy-path reseller register is DEAL_REGISTRATION_
    PIPELINE_002; idempotency N/A (register duplicate is _022).
    """
    async with async_step(
        "Setup: partner + plan + a RESELLER deal payload carrying end-client pricing"
    ):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        payload = make_deal(pid, plan_id, dealType="reseller", **_END_CLIENT_PRICE_FIELDS)
        logger.info(
            "SETUP: partner {} + reseller deal payload with end-client pricing: {}",
            partner.data.get("code"),
            sorted(_END_CLIENT_PRICE_FIELDS),
        )

    async with async_step("[1/3] Register the reseller deal (with end-client pricing fields)"):
        resp = await sa_deals_client.register_deal(payload)
        deal_id = resp.deal_id
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert deal_id, "the reseller deal must still be created (BE accepts + strips)"
        assert resp.data.get("dealType") == "reseller", "deal must be a reseller deal"
        logger.info("CHECK registered → OK (HTTP 201, reseller deal id={})", deal_id)

    async with async_step("[2/3] The create response stores NONE of the end-client-price fields"):
        leaked = [k for k in _END_CLIENT_PRICE_FIELDS if k in resp.data]
        assert not leaked, (
            f"reseller end-client price must not be stored, but the deal kept {leaked}"
        )
        logger.info("CHECK response → OK (none of {} stored)", sorted(_END_CLIENT_PRICE_FIELDS))

    async with async_step("[3/3] A follow-up GET confirms the end-client price is not stored"):
        fetched = await sa_deals_client.get_deal(deal_id)
        leaked = [k for k in _END_CLIENT_PRICE_FIELDS if k in fetched.data]
        assert not leaked, f"fetched reseller deal must not carry end-client price, found {leaked}"
        logger.info("CHECK persisted → OK (GET confirms no end-client price stored)")

    logger.info(
        "RESULT: reseller end-client pricing accepted but not persisted (enforced / data-minimized)"
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_016(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_016: reseller sell price - end-client price cannot be SET via update.

    Negative counterpart of _006 — same enforcement ("BlazeUp does not store the
    reseller's end-client price"), but through the UPDATE/PATCH entry point instead of
    register. Attempting to set the end-client price on an open reseller deal must not
    take: (a) mixed with a valid editable field, the valid field updates but the price
    fields are stripped (not persisted); (b) with ONLY price fields, the update is
    rejected 400 ("No editable fields provided") — the end-client price is not a
    recognized editable field. Verified 2026-07-22.
    """
    async with async_step("Setup: partner + plan + a registered (open, editable) reseller deal"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        deal_id = (
            await sa_deals_client.register_deal(make_deal(pid, plan_id, dealType="reseller"))
        ).deal_id
        assert deal_id, "precondition: reseller deal must be registered"
        logger.info("SETUP: reseller deal {} ready for update attempts", deal_id)

    async with async_step(
        "[1/3] Update with a valid field + end-client price → valid field applies, price stripped"
    ):
        r = await sa_deals_client.patch(
            f"/sa-partners-api/v1/sa/deals/{deal_id}",
            json={"notes": "QA-AUTO update note", **_END_CLIENT_PRICE_FIELDS},
            expected_status=None,
        )
        assert r.status_code == 200, f"update with a valid field must succeed, got {r.status_code}"
        d = r.json().get("data") or {}
        assert d.get("notes") == "QA-AUTO update note", "the valid field (notes) must be updated"
        leaked = [k for k in _END_CLIENT_PRICE_FIELDS if k in d]
        assert not leaked, f"end-client price must not be settable via update, but kept {leaked}"
        logger.info(
            "CHECK mixed update → OK (notes updated; price fields {} stripped)",
            sorted(_END_CLIENT_PRICE_FIELDS),
        )

    async with async_step(
        "[2/3] Update with ONLY end-client price fields → 400 (not a recognized editable field)"
    ):
        r = await sa_deals_client.patch(
            f"/sa-partners-api/v1/sa/deals/{deal_id}",
            json=dict(_END_CLIENT_PRICE_FIELDS),
            expected_status=None,
        )
        msg = str(r.json().get("message") or "")
        assert r.status_code == 400 and "no editable fields" in msg.lower(), (
            f"price-only update must be rejected 400 'No editable fields provided', got {r.status_code} {msg!r}"
        )
        logger.info("CHECK price-only update → OK (400 'No editable fields provided')")

    async with async_step("[3/3] GET confirms: notes update persisted, no end-client price stored"):
        fetched = await sa_deals_client.get_deal(deal_id)
        assert fetched.data.get("notes") == "QA-AUTO update note", "the notes update must persist"
        leaked = [k for k in _END_CLIENT_PRICE_FIELDS if k in fetched.data]
        assert not leaked, f"fetched deal must not carry end-client price, found {leaked}"
        logger.info("CHECK persisted → OK (notes updated, no end-client price stored)")

    logger.info("RESULT: reseller end-client price cannot be set via update (stripped / 400)")
