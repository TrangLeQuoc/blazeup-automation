"""SA Deals API — deal registration & pipeline (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_DEAL_REGISTRATION_PIPELINE_*.

Registering a deal needs a partner (sa_partners_client) and a published billing
plan (picked via sa_deals_client.pick_billing_plan_id). The deal API has no
delete endpoint, so cleanup removes the parent partner; the QA-AUTO prospect name
keeps the deal identifiable on staging.
"""

import asyncio

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_partner, unique_email
from utils.log_helper import async_step

# A syntactically valid Mongo ObjectId that does not exist — for "not found" tests.
_GHOST_ID = "000000000000000000000000"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_001(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_001: register a partner deal - deal is created (registered).

    Happy-path deal registration on ``POST /sa-partners-api/v1/sa/deals``: a valid
    payload (partnerId + planId + dealType + prospect + ACV + close date) returns
    HTTP 201, persists the deal with a server-assigned id, starts it in
    ``status = "registered"`` with a protection window (``protectionExpiresAt``),
    and echoes the submitted fields. The registration is confirmed to persist via
    a follow-up GET.
    """
    async with async_step("Setup: create a partner + pick a published billing plan"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        payload = make_deal(pid, plan_id, dealType="referral")
        logger.info(
            "SETUP: partner {} + plan '{}'; prospect='{}'",
            partner.data.get("code"),
            plan_id,
            payload["prospectName"],
        )

    async with async_step("[1/5] Call API: POST /v1/sa/deals (register the deal)"):
        resp = await sa_deals_client.register_deal(payload)
        deal_id = resp.deal_id

    async with async_step("[2/5] Verify the deal is accepted + persisted"):
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should confirm the registration"
        assert deal_id, "registered deal must have a server-assigned id (_id)"
        logger.info("CHECK registered → OK (HTTP 201, id={}, message='{}')", deal_id, resp.message)

    async with async_step("[3/5] Verify EVERY submitted field is stored (no silent mutation)"):
        # echo-check all sent fields except the date (BE returns it as an ISO datetime)
        for field in (
            "partnerId",
            "dealType",
            "prospectName",
            "prospectEmail",
            "prospectPhone",
            "prospectCountry",
            "estimatedAcvCents",
            "planId",
            "notes",
        ):
            assert resp.data.get(field) == payload[field], (
                f"stored {field}={resp.data.get(field)!r} must match sent {payload[field]!r}"
            )
        # expectedCloseDate is normalized to an ISO datetime — assert the date part
        assert str(resp.data.get("expectedCloseDate", "")).startswith(
            payload["expectedCloseDate"]
        ), "stored expectedCloseDate must preserve the requested date"
        logger.info("CHECK echo → OK (all {} submitted fields stored as sent)", 10)

    async with async_step("[4/5] Verify lifecycle: status 'registered' + protection window opened"):
        assert resp.data.get("status") == "registered", (
            f"new deal must start 'registered', got {resp.data.get('status')!r}"
        )
        assert resp.data.get("protectionExpiresAt"), "registered deal must have a protection window"
        assert resp.data.get("conflictStatus") == "none", (
            f"a fresh deal must have conflictStatus 'none', got {resp.data.get('conflictStatus')!r}"
        )
        logger.info(
            "CHECK lifecycle → OK (status='registered', protectionExpiresAt set, no conflict)"
        )

    async with async_step("[5/5] Verify the deal is retrievable via GET /v1/sa/deals/{id}"):
        fetched = await sa_deals_client.get_deal(deal_id)
        assert fetched.deal_id == deal_id, "GET by id must return the same deal"
        assert fetched.data.get("status") == "registered", "fetched deal must be 'registered'"
        logger.info("CHECK retrievable → OK (GET by id returns the registered deal)")

    logger.info("RESULT: deal {} registered for partner {}", deal_id, partner.data.get("code"))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_002(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_002: register reseller deal - billing model 'reseller' is stored.

    Registers a deal with ``dealType="reseller"`` and verifies the reseller billing
    model is persisted (stored ``dealType == "reseller"``) plus the standard
    register contract (field echo + lifecycle), mirroring _001.

    Verified: a reseller deal stores no dedicated billing-model field beyond
    ``dealType`` — the deal record shape matches a referral deal, so
    ``dealType == "reseller"`` IS the stored billing model.
    """
    async with async_step("Setup: create a partner + pick a published billing plan"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        payload = make_deal(pid, plan_id, dealType="reseller")
        logger.info("SETUP: reseller deal payload ready (partner {})", partner.data.get("code"))

    async with async_step("[1/3] Register the reseller deal"):
        resp = await sa_deals_client.register_deal(payload)
        deal_id = resp.deal_id
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert deal_id, "registered deal must have a server-assigned id (_id)"
        logger.info("CHECK registered → OK (HTTP 201, id={})", deal_id)

    async with async_step("[2/3] Verify billing model 'reseller' is stored + fields echoed"):
        assert resp.data.get("dealType") == "reseller", (
            f"billing model must be stored as 'reseller', got {resp.data.get('dealType')!r}"
        )
        for field in (
            "partnerId",
            "prospectName",
            "prospectEmail",
            "prospectPhone",
            "prospectCountry",
            "estimatedAcvCents",
            "planId",
            "notes",
        ):
            assert resp.data.get(field) == payload[field], (
                f"stored {field}={resp.data.get(field)!r} must match sent {payload[field]!r}"
            )
        assert str(resp.data.get("expectedCloseDate", "")).startswith(
            payload["expectedCloseDate"]
        ), "stored expectedCloseDate must preserve the requested date"
        logger.info("CHECK reseller → OK (dealType='reseller' stored, all fields echoed)")

    async with async_step("[3/3] Verify lifecycle + retrievable (GET by id)"):
        assert resp.data.get("status") == "registered", (
            f"new deal must start 'registered', got {resp.data.get('status')!r}"
        )
        assert resp.data.get("protectionExpiresAt"), "registered deal must have a protection window"
        fetched = await sa_deals_client.get_deal(deal_id)
        assert fetched.data.get("dealType") == "reseller", (
            "fetched deal must keep dealType 'reseller'"
        )
        logger.info("CHECK lifecycle → OK (registered, protection set, reseller persisted)")

    logger.info(
        "RESULT: reseller deal {} registered for partner {}", deal_id, partner.data.get("code")
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_003(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_003: register co-sell deal - co-sell metadata is stored.

    Registers a deal with ``dealType="co_sell"`` and verifies the co-sell model is
    persisted (stored ``dealType == "co_sell"``) plus the standard register
    contract (field echo + lifecycle), mirroring _001/_002.

    Verified: at registration a co_sell deal stores no extra co-sell field beyond
    ``dealType`` — the record shape matches a referral deal, so ``dealType ==
    "co_sell"`` IS the stored co-sell metadata. The co-sell *split* (e.g. 70/30) is
    computed downstream and is covered by _011 (Calculate — currently a blocked
    job), out of scope here.
    """
    async with async_step("Setup: create a partner + pick a published billing plan"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        payload = make_deal(pid, plan_id, dealType="co_sell")
        logger.info("SETUP: co-sell deal payload ready (partner {})", partner.data.get("code"))

    async with async_step("[1/3] Register the co-sell deal"):
        resp = await sa_deals_client.register_deal(payload)
        deal_id = resp.deal_id
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert deal_id, "registered deal must have a server-assigned id (_id)"
        logger.info("CHECK registered → OK (HTTP 201, id={})", deal_id)

    async with async_step(
        "[2/3] Verify co-sell metadata (dealType='co_sell') stored + fields echoed"
    ):
        assert resp.data.get("dealType") == "co_sell", (
            f"co-sell metadata must be stored as dealType 'co_sell', got {resp.data.get('dealType')!r}"
        )
        for field in (
            "partnerId",
            "prospectName",
            "prospectEmail",
            "prospectPhone",
            "prospectCountry",
            "estimatedAcvCents",
            "planId",
            "notes",
        ):
            assert resp.data.get(field) == payload[field], (
                f"stored {field}={resp.data.get(field)!r} must match sent {payload[field]!r}"
            )
        assert str(resp.data.get("expectedCloseDate", "")).startswith(
            payload["expectedCloseDate"]
        ), "stored expectedCloseDate must preserve the requested date"
        logger.info("CHECK co-sell → OK (dealType='co_sell' stored, all fields echoed)")

    async with async_step("[3/3] Verify lifecycle + retrievable (GET by id)"):
        assert resp.data.get("status") == "registered", (
            f"new deal must start 'registered', got {resp.data.get('status')!r}"
        )
        assert resp.data.get("protectionExpiresAt"), "registered deal must have a protection window"
        fetched = await sa_deals_client.get_deal(deal_id)
        assert fetched.data.get("dealType") == "co_sell", (
            "fetched deal must keep dealType 'co_sell'"
        )
        logger.info("CHECK lifecycle → OK (registered, protection set, co_sell persisted)")

    logger.info(
        "RESULT: co-sell deal {} registered for partner {}", deal_id, partner.data.get("code")
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_004(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_004: register deal for an existing prospect - conflict raised.

    Deal protection: when a SECOND partner registers a deal for a prospect that a
    FIRST partner already registered (same prospect identity — name + email), the
    second deal is still accepted (201) but flagged for the deal-conflict queue:
    ``conflictStatus`` becomes "flagged" and ``conflictingDealId`` points at the
    first deal. (Same partner re-registering the same prospect is a hard 400
    duplicate instead — a separate behavior, not this TC.)
    """
    async with async_step("Setup: two partners + a shared prospect identity"):
        p1 = await sa_partners_client.create_partner(make_partner())
        p2 = await sa_partners_client.create_partner(make_partner())
        for p in (p1, p2):
            if p.partner_id:
                created_resources.add(
                    lambda pid=p.partner_id: sa_partners_client.delete_partner(pid)
                )
        assert p1.partner_id and p2.partner_id, "precondition: both partners must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        prospect = {
            "prospectName": make_partner()["name"] + " Prospect",  # unique shared name
            "prospectEmail": unique_email(),
        }
        logger.info(
            "SETUP: partners {} / {} + shared prospect '{}'",
            p1.data.get("code"),
            p2.data.get("code"),
            prospect["prospectName"],
        )

    async with async_step("[1/3] Partner 1 registers the deal first (no conflict)"):
        deal_a = await sa_deals_client.register_deal(make_deal(p1.partner_id, plan_id, **prospect))
        assert deal_a.data.get("conflictStatus") == "none", "first deal must have no conflict"
        logger.info("CHECK first deal → OK (id={}, conflictStatus='none')", deal_a.deal_id)

    async with async_step("[2/3] Partner 2 registers the SAME prospect → conflict flagged"):
        deal_b = await sa_deals_client.register_deal(make_deal(p2.partner_id, plan_id, **prospect))
        assert deal_b.deal_id, "second deal should still be created (flagged, not rejected)"
        assert deal_b.data.get("conflictStatus") == "flagged", (
            f"second deal must raise conflict, got conflictStatus={deal_b.data.get('conflictStatus')!r}"
        )
        assert deal_b.data.get("conflictingDealId") == deal_a.deal_id, (
            "conflictingDealId must point at the first registered deal"
        )
        logger.info(
            "CHECK conflict → OK (conflictStatus='flagged', conflictingDealId={})", deal_a.deal_id
        )

    async with async_step("[3/3] Verify the conflict persisted via GET /v1/sa/deals/{id}"):
        fetched = await sa_deals_client.get_deal(deal_b.deal_id)
        assert fetched.data.get("conflictStatus") == "flagged", "fetched deal must stay flagged"
        logger.info("CHECK persisted → OK (GET returns conflictStatus='flagged')")

    logger.info("RESULT: cross-partner same-prospect deal flagged as conflict")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_008(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_008: internal deal approve - approved + rate/rate-table version stamped.

    Approving a registered deal (POST /v1/sa/deals/{id}/approve) flips status
    registered → approved and stamps the reviewer (reviewedAt + reviewedBy).

    GAP this test surfaces: the plan also expects the commission ``rate`` + rate
    ``rateTableVersion`` to be stamped, but neither appears in the deal API
    response after approve (no rate field; no commission is created at approve
    either). Step [3/3] asserts they are present and therefore FAILS until the BE
    exposes them — confirm with BE whether the rate is stamped internally
    (not serialized), stamped at a different stage (e.g. deal win), or unimplemented.
    """
    async with async_step("Setup: create partner + register a deal (status 'registered')"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        registered = await sa_deals_client.register_deal(make_deal(pid, plan_id))
        deal_id = registered.deal_id
        assert registered.data.get("status") == "registered", (
            "precondition: deal must be registered"
        )
        logger.info("SETUP: deal {} registered for partner {}", deal_id, partner.data.get("code"))

    async with async_step("[1/3] Approve the registered deal"):
        resp = await sa_deals_client.approve_deal(deal_id, review_notes="QA-AUTO approve")
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.data.get("status") == "approved", (
            f"deal must become 'approved', got {resp.data.get('status')!r}"
        )
        logger.info("CHECK approved → OK (HTTP 201, status='approved')")

    async with async_step("[2/3] Verify the reviewer is stamped (reviewedAt + reviewedBy)"):
        assert resp.data.get("reviewedAt"), "approval must stamp `reviewedAt`"
        assert resp.data.get("reviewedBy"), "approval must stamp `reviewedBy`"
        logger.info(
            "CHECK reviewer → OK (reviewedBy='{}', reviewedAt set)", resp.data.get("reviewedBy")
        )

    async with async_step("[3/3] Verify rate + rate table version are stamped (per plan)"):
        rate = resp.data.get("rate") or resp.data.get("commissionRate")
        rate_table_version = resp.data.get("rateTableVersion")
        assert rate is not None and rate_table_version is not None, (
            f"approved deal must stamp rate + rateTableVersion, got rate={rate!r} "
            f"rateTableVersion={rate_table_version!r} — not present in the deal API response; "
            "confirm with BE (stamped internally / different stage / unimplemented)"
        )
        logger.info("CHECK rate → OK (rate={}, rateTableVersion={})", rate, rate_table_version)

    logger.info("RESULT: deal {} approved (reviewer stamped)", deal_id)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_009(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_009: resolve conflict - decision and reasoning are immutable.

    Resolving a flagged deal conflict (POST /v1/sa/deals/{id}/resolve-conflict)
    stamps the SA ``decision`` + ``reasoning`` (under ``conflictResolution``) and
    locks them: a second resolve is rejected (deal no longer FLAGGED), so the
    decision/reasoning cannot be changed — and a re-read confirms they are intact.
    """
    decision = "resolved_for_partner"
    reasoning = "QA-AUTO original reasoning — confirmed partner wins"

    async with async_step("Setup: create a flagged conflict (two partners, same prospect)"):
        p1 = await sa_partners_client.create_partner(make_partner())
        p2 = await sa_partners_client.create_partner(make_partner())
        for p in (p1, p2):
            if p.partner_id:
                created_resources.add(
                    lambda pid=p.partner_id: sa_partners_client.delete_partner(pid)
                )
        assert p1.partner_id and p2.partner_id, "precondition: both partners must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        prospect = {
            "prospectName": make_partner()["name"] + " Prospect",
            "prospectEmail": unique_email(),
        }
        await sa_deals_client.register_deal(make_deal(p1.partner_id, plan_id, **prospect))
        flagged = await sa_deals_client.register_deal(make_deal(p2.partner_id, plan_id, **prospect))
        assert flagged.data.get("conflictStatus") == "flagged", (
            "precondition: deal B must be flagged"
        )
        deal_id = flagged.deal_id
        logger.info("SETUP: deal {} is flagged (conflict)", deal_id)

    async with async_step("[1/3] Resolve the conflict — decision + reasoning are stamped"):
        resp = await sa_deals_client.resolve_conflict(
            deal_id, decision=decision, reasoning=reasoning
        )
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.data.get("conflictStatus") == decision, (
            f"conflictStatus must become {decision!r}, got {resp.data.get('conflictStatus')!r}"
        )
        res = resp.data.get("conflictResolution") or {}
        assert res.get("decision") == decision, "stamped decision must match"
        assert res.get("reasoning") == reasoning, "stamped reasoning must match"
        assert res.get("resolvedBy") and res.get("resolvedAt"), (
            "resolution must stamp resolvedBy/At"
        )
        logger.info(
            "CHECK resolved → OK (decision='{}', reasoning stamped, resolver recorded)", decision
        )

    async with async_step("[2/3] Immutability: a second resolve (different values) is rejected"):
        r = await sa_deals_client.raw_resolve_conflict(
            deal_id,
            decision="resolved_against_partner",
            reasoning="QA-AUTO CHANGED",
            expected_status=None,
        )
        assert 400 <= r.status_code < 500, f"re-resolve must be rejected, got {r.status_code}"
        assert "flagged" in str(r.json().get("message") or "").lower(), (
            "rejection should explain the deal is no longer in FLAGGED conflict state"
        )
        logger.info("CHECK immutable → OK (re-resolve rejected {})", r.status_code)

    async with async_step("[3/3] Re-read confirms decision + reasoning unchanged"):
        fetched = await sa_deals_client.get_deal(deal_id)
        res2 = fetched.data.get("conflictResolution") or {}
        assert res2.get("decision") == decision, (
            "decision must stay the original after a rejected re-resolve"
        )
        assert res2.get("reasoning") == reasoning, "reasoning must stay the original (immutable)"
        logger.info("CHECK persisted → OK (decision + reasoning still the original)")

    logger.info("RESULT: conflict resolved ({}) — decision + reasoning immutable", decision)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_010(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_010: deal approved event - published (CRM sync is downstream).

    Approving a deal emits a ``partner.deal.approved`` event (recorded in the SA
    audit log with the before/after status). That event is the trigger the CRM
    integration consumes to update the CRM owner + stage.

    Scope: this asserts the API-observable signal — the deal-approved event is
    published. The actual CRM owner/stage update happens in a downstream service
    (connectors / CRM Integration) and is out of scope here (covered by the CRM
    Integration TCs).
    """
    async with async_step("Setup: create partner + register a deal (status 'registered')"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        deal_id = (await sa_deals_client.register_deal(make_deal(pid, plan_id))).deal_id
        logger.info("SETUP: deal {} registered", deal_id)

    async with async_step("[1/2] Approve the deal"):
        resp = await sa_deals_client.approve_deal(deal_id)
        assert resp.data.get("status") == "approved", "deal must be approved"
        logger.info("CHECK approved → OK (status='approved')")

    async with async_step("[2/2] Verify a 'deal approved' event is published to the audit log"):
        found = None
        for attempt in range(1, 4):
            logs = await sa_partners_client.list_audit_logs(limit=50)
            found = next(
                (
                    e
                    for e in logs.data
                    if "deal" in str(e.get("action", "")).lower()
                    and "approv" in str(e.get("action", "")).lower()
                    and deal_id in str(e)
                ),
                None,
            )
            if found:
                break
            logger.info("deal-approved event not visible yet (attempt {}/3), retrying…", attempt)
            await asyncio.sleep(1)
        assert found, "no 'deal approved' event found in audit log for this deal"
        after = found.get("after") or {}
        assert after.get("status") == "approved", "event must record the approved transition"
        logger.info(
            "CHECK event → OK (action='{}', → approved). CRM owner/stage update is downstream.",
            found.get("action"),
        )

    logger.info(
        "RESULT: deal {} approved-event published (CRM sync downstream, out of scope)", deal_id
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_013(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_013: resolve conflict (prospect confirmation) - confirmed partner wins.

    When two partners register the same prospect, resolving the FLAGGED deal FOR
    its partner (decision=resolved_for_partner, citing the prospect's confirmation)
    makes that deal the winner (conflictStatus='resolved_for_partner') AND
    automatically flips the other (conflicting) deal to 'resolved_against_partner'
    — the loser. Both deals keep status 'registered'. The decision/reasoning
    immutability is covered by _009; negative resolve inputs by _029.
    """
    async with async_step("Setup: two partners register the SAME prospect (deal B flagged)"):
        p1 = await sa_partners_client.create_partner(make_partner())
        p2 = await sa_partners_client.create_partner(make_partner())
        for p in (p1, p2):
            if p.partner_id:
                created_resources.add(
                    lambda pid=p.partner_id: sa_partners_client.delete_partner(pid)
                )
        assert p1.partner_id and p2.partner_id, "precondition: both partners must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        prospect = {
            "prospectName": make_partner()["name"] + " Prospect",
            "prospectEmail": unique_email(),
        }
        deal_a = await sa_deals_client.register_deal(make_deal(p1.partner_id, plan_id, **prospect))
        deal_b = await sa_deals_client.register_deal(make_deal(p2.partner_id, plan_id, **prospect))
        assert deal_b.data.get("conflictStatus") == "flagged", (
            "precondition: deal B must be flagged"
        )
        logger.info(
            "SETUP: deal A {} (first) + deal B {} (flagged)", deal_a.deal_id, deal_b.deal_id
        )

    async with async_step("[1/3] Resolve the flagged deal FOR its partner (prospect confirmed)"):
        resp = await sa_deals_client.resolve_conflict(
            deal_b.deal_id,
            decision="resolved_for_partner",
            reasoning="Prospect confirmed this partner is the engaged reseller",
        )
        cs = resp.data.get("conflictStatus")
        assert cs == "resolved_for_partner", (
            f"confirmed partner must win, got conflictStatus={cs!r}"
        )
        assert isinstance(cs, str), "conflictStatus must be a string"
        assert isinstance(resp.data.get("conflictResolution"), dict), (
            "conflictResolution must be recorded"
        )
        logger.info("CHECK winner → OK (deal B conflictStatus='resolved_for_partner')")

    async with async_step("[2/3] The conflicting deal is auto-flipped to the loser"):
        loser = await sa_deals_client.get_deal(deal_a.deal_id)
        assert loser.data.get("conflictStatus") == "resolved_against_partner", (
            f"the other deal must lose, got {loser.data.get('conflictStatus')!r}"
        )
        logger.info("CHECK loser → OK (deal A conflictStatus='resolved_against_partner')")

    async with async_step("[3/3] Verify both outcomes persisted via GET"):
        winner = await sa_deals_client.get_deal(deal_b.deal_id)
        assert winner.data.get("conflictStatus") == "resolved_for_partner", "winner must persist"
        assert winner.data.get("status") == "registered", "winner keeps status 'registered'"
        logger.info(
            "CHECK persisted → OK (winner resolved_for_partner, loser resolved_against_partner)"
        )

    logger.info("RESULT: confirmed partner wins; conflicting deal flipped to loser")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_021(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_021: register deal invalid/missing fields - rejected with 400.

    Negative counterpart of _001 (register). Each invalid or incomplete payload
    must be rejected with 4xx + a descriptive message and create no deal. All
    cases run (failures collected) so one gap never hides the others.

    Known gap this test surfaces: a non-existent ``planId`` is currently accepted
    (HTTP 201) — the API does not validate planId against the plan catalog — so
    that case fails until the BE adds the check (confirm with BE). Any deal
    accidentally created is removed via the parent-partner cleanup.
    """
    async with async_step("Setup: create a partner + pick a published plan (valid baseline)"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        base = make_deal(pid, plan_id, dealType="referral")
        # Prove the fixture ids used in negative cases are genuinely absent, so the
        # "register must reject" assertions are trustworthy (not relying on a guess).
        ghost_plan = "no-such-plan-qa"
        absent_plan = await sa_deals_client.raw_get_billing_plan(ghost_plan)
        assert absent_plan.status_code >= 400, (
            f"test fixture invalid: planId '{ghost_plan}' unexpectedly exists in the catalog"
        )
        logger.info(
            "SETUP: baseline ready; verified ghost planId '{}' is absent (GET → {})",
            ghost_plan,
            absent_plan.status_code,
        )

    def without(field: str) -> dict:
        return {k: v for k, v in base.items() if k != field}

    # (label, payload, expected message hint)
    cases = [
        ("missing partnerId", without("partnerId"), "partner"),
        ("missing dealType", without("dealType"), "dealtype must be one of"),
        ("invalid dealType", {**base, "dealType": "wholesale"}, "dealtype must be one of"),
        ("missing prospectName", without("prospectName"), "prospectname"),
        ("missing prospectCountry", without("prospectCountry"), "prospectcountry"),
        ("invalid prospectEmail", {**base, "prospectEmail": "not-an-email"}, "must be an email"),
        ("missing estimatedAcvCents", without("estimatedAcvCents"), "estimatedacvcents"),
        ("negative ACV", {**base, "estimatedAcvCents": -100}, "must not be less than"),
        ("missing expectedCloseDate", without("expectedCloseDate"), "iso 8601"),
        ("bad date format", {**base, "expectedCloseDate": "31-12-2026"}, "iso 8601"),
        ("ghost partnerId", {**base, "partnerId": _GHOST_ID}, "not found"),
        ("ghost planId (verified absent above)", {**base, "planId": ghost_plan}, "plan"),
    ]
    gaps: list[str] = []
    for idx, (label, body, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid register: {label}"):
            r = await sa_deals_client.raw_register_deal(body)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "deal-register negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid register attempts rejected", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_028(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_028: approve invalid/illegal-state deal - rejected with a clear error.

    Negative counterpart of _008 (approve). Approving a non-existent id, a
    malformed id, or a deal that is not in an approvable state (already approved)
    must be rejected (4xx) with a descriptive message — never silently succeed.
    """
    async with async_step("Setup: create partner + register + approve a deal (now 'approved')"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        approved = await sa_deals_client.register_deal(make_deal(pid, plan_id))
        await sa_deals_client.approve_deal(approved.deal_id)
        logger.info("SETUP: deal {} is now approved", approved.deal_id)

    cases = [
        ("non-existent id", _GHOST_ID, "not found"),
        ("malformed id", "not-an-id", "invalid id"),
        ("already-approved deal", approved.deal_id, "cannot transition"),
    ]
    gaps: list[str] = []
    for idx, (label, deal_id, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject approve: {label}"):
            r = await sa_deals_client.raw_approve_deal(deal_id)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "deal-approve negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} illegal approve attempts rejected", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_029(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_029: resolve-conflict invalid input - rejected with a clear error.

    Negative counterpart of _009 (resolve conflict). Invalid input must be rejected
    (4xx) with a descriptive message: out-of-enum decision, missing decision,
    missing reasoning, a non-existent id, a malformed id, and resolving a deal that
    is not in a FLAGGED conflict state.
    """
    async with async_step("Setup: create a registered (non-flagged) deal as the target"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        deal = await sa_deals_client.register_deal(make_deal(pid, plan_id))
        did = deal.deal_id
        assert deal.data.get("conflictStatus") == "none", "precondition: deal must be non-flagged"
        logger.info("SETUP: non-flagged deal {} ready", did)

    # (label, target id, decision, reasoning, expected message hint)
    cases = [
        ("invalid decision enum", did, "whatever", "QA", "decision must be one of"),
        ("missing decision", did, None, "QA", "decision must be one of"),
        ("missing reasoning", did, "resolved_for_partner", None, "reasoning"),
        ("non-existent id", _GHOST_ID, "resolved_for_partner", "QA", "not found"),
        ("malformed id", "not-an-id", "resolved_for_partner", "QA", "invalid id"),
        ("non-flagged deal", did, "resolved_for_partner", "QA", "flagged"),
    ]
    gaps: list[str] = []
    for idx, (label, target, decision, reasoning, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject resolve-conflict: {label}"):
            r = await sa_deals_client.raw_resolve_conflict(
                target, decision=decision, reasoning=reasoning
            )
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "resolve-conflict negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid resolve-conflict attempts rejected", len(cases))
