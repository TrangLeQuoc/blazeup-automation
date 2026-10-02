"""SA tenant<->partner attribution ledger — GET /v1/sa/partner-attributions (sa-partners-api).

Maps to the test plan: PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_002 (PRD §7.1 provision
leg) / _012 / _013 (PRD §7.5 ledger).

The SA-wide counterpart of the partner portal's "My Clients". Same underlying collection, two
deliberately different scopes: the portal's `findByIdScoped(id, partnerId)` refuses a row that
is not the caller's, while this controller calls `findByIdScoped(id)` with no scope at all, so
an SA operator reads every partner's row. Proving that contrast is the point of _012 — it is
the same property CLIENT_HEALTH_MSP_010 proves from the other side.

A row is written only once a won deal's tenant is provisioned. The ledger TCs (_012/_013)
therefore READ rows that already exist and never create one; every id is discovered at run time
and nothing is written. The ONE exception is _002, which drives register→approve→win itself and
asserts the provisioning that *would* write such a row actually completes (it currently fails —
BUG-API-033 — and is the regression guard for when BE's provisioning worker runs on staging).
"""

import asyncio
import uuid

import pytest
from loguru import logger

from utils.data_factory import make_deal
from utils.log_helper import async_step

# Provisioning is async with no published SLA (BE: "indeterminate"); 117 deals sit 'overdue' on
# staging, so a generous bound still fails fast enough for CI while giving a healthy BE time to
# resolve. Revisit once BE confirms the expected provisioning completion time.
_PROVISION_POLL_TIMEOUT_S = 90
_PROVISION_POLL_INTERVAL_S = 10

# From partner-tenant-attribution.schema.ts — the spec's own enums, not guesses.
_STATUSES = ("active", "terminated")
_LIFECYCLE = ("active", "suspended", "churned")
# QueryAttributionsDto: partnerId (mongo id), status, clientLifecycleState, clientTenantId.
_REQUIRED_FIELDS = (
    "_id",
    "partnerId",
    "partnerName",
    "clientTenantId",
    "status",
    "clientLifecycleState",
    "source",
    "arrCents",
    "currency",
    "attachedAt",
)
_SENSITIVE = ("password", "token", "secret", "credential")
_GHOST = "000000000000000000000000"


def _envelope(resp) -> dict:
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    for key in ("data", "total"):
        assert key in body, f"envelope has no `{key}`: {sorted(body)}"
    assert isinstance(body["data"], list), (
        f"`data` must be a list, got {type(body['data']).__name__}"
    )
    assert isinstance(body["total"], int), f"`total` must be an int, got {body['total']!r}"
    return body


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_tenant_provisioning_attribution_012(sa_partners_client):
    """PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_012: SA reads the attribution ledger - all partners, filters narrow.

    GET /v1/sa/partner-attributions and GET /v1/sa/partner-attributions/{id}. Asserts the
    envelope, the row schema, that the `partnerId` filter actually NARROWS (a filter accepted
    and then ignored is the failure mode this is written against — BUG-API-023 is exactly that
    on a sibling endpoint), and that the detail route returns the row that was asked for.

    The load-bearing assertion is the scope contrast: this SA route must return rows belonging
    to MORE THAN ONE partner, because the partner-portal twin returns only the caller's own.
    Together with CLIENT_HEALTH_MSP_010 that pins both halves of the boundary.

    Read-only: no setup, no teardown, nothing written. Precondition: the ledger holds at least
    one row — automation cannot create one, so an empty ledger fails the precondition loudly
    rather than passing on an empty set.
    """
    async with async_step("[1/6] GET the ledger → a valid, non-empty page"):
        body = _envelope(await sa_partners_client.list_attributions(params={"limit": 50}))
        rows = body["data"]
        assert rows, (
            "the attribution ledger is empty — this TC reads rows it cannot create, so there is "
            "nothing to assert. Not a defect in the endpoint: re-run once any partner has a "
            "provisioned client (see G1/G2 in ENDPOINT_BUILD_LIST.md)"
        )
        assert body.get("message"), "the envelope should carry a `message`"
        logger.info("CHECK ledger reachable → OK (total={}, page={})", body["total"], len(rows))

    async with async_step("[2/6] Every row is well-formed, typed, and leaks nothing"):
        for row in rows:
            missing = [f for f in _REQUIRED_FIELDS if f not in row]
            assert not missing, f"attribution row is missing {missing}: {sorted(row)}"
            assert row["status"] in _STATUSES, f"status outside the enum: {row['status']!r}"
            assert row["clientLifecycleState"] in _LIFECYCLE, (
                f"clientLifecycleState outside the enum: {row['clientLifecycleState']!r}"
            )
            assert isinstance(row["arrCents"], int), (
                f"arrCents must be an int, got {row['arrCents']!r}"
            )
            leaked = sorted(k for k in row if any(s.lower() in k.lower() for s in _SENSITIVE))
            assert not leaked, f"credential material exposed on an attribution row: {leaked}"
        logger.info("CHECK {} row(s) typed and clean → OK", len(rows))

    async with async_step("[3/6] The SA view spans MORE THAN ONE partner"):
        owners = {str(r["partnerId"]) for r in rows}
        assert len(owners) > 1, (
            f"every row on this page belongs to the same partner ({owners}). The SA ledger must "
            "not be partner-scoped — that scoping belongs to the portal twin. Either the scope "
            "leaked in from the portal route or staging happens to hold one partner's rows only; "
            "check `total` before reading this as a defect"
        )
        logger.info("CHECK SA view spans {} distinct partners → OK", len(owners))

    async with async_step("[4/6] The `partnerId` filter narrows to exactly that partner"):
        target = str(rows[0]["partnerId"])
        filtered = _envelope(
            await sa_partners_client.list_attributions(params={"partnerId": target, "limit": 50})
        )
        assert filtered["data"], f"partnerId={target} returned nothing although a row carries it"
        foreign = [r for r in filtered["data"] if str(r.get("partnerId")) != target]
        assert not foreign, (
            f"the partnerId filter was accepted and ignored: {len(foreign)} of "
            f"{len(filtered['data'])} rows belong to another partner"
        )
        assert filtered["total"] < body["total"] or len(owners) == 1, (
            f"filtering to one of {len(owners)} partners did not reduce the total "
            f"({filtered['total']} vs {body['total']}) — the filter is not narrowing"
        )
        logger.info(
            "CHECK partnerId filter narrows → OK ({} of {} rows)",
            filtered["total"],
            body["total"],
        )

    async with async_step("[5/6] The `status` filter returns only matching rows"):
        status = rows[0]["status"]
        by_status = _envelope(
            await sa_partners_client.list_attributions(params={"status": status, "limit": 50})
        )
        wrong = [r.get("status") for r in by_status["data"] if r.get("status") != status]
        assert not wrong, f"status={status!r} also returned rows with {sorted(set(wrong))}"
        logger.info("CHECK status filter → OK (status={})", status)

    async with async_step("[6/6] The detail route returns the row that was asked for"):
        wanted = rows[0]
        detail = (await sa_partners_client.get_attribution(str(wanted["_id"]))).json()
        got = detail.get("data") or {}
        assert str(got.get("_id")) == str(wanted["_id"]), (
            f"asked for attribution {wanted['_id']} and received {got.get('_id')} — the path "
            "parameter is being ignored (the failure mode of BUG-API-022 on a sibling route)"
        )
        assert str(got.get("partnerId")) == str(wanted["partnerId"]), (
            "the detail row names a different partner than the list row for the same id"
        )
        logger.info("CHECK detail route returns the requested row → OK ({})", wanted["_id"])

    logger.info("RESULT: SA attribution ledger verified — SA-wide, filters narrow, detail exact")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_tenant_provisioning_attribution_013(sa_partners_client):
    """PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_013: SA attribution ledger invalid input - correct rejection.

    Negative counterpart of _012. Values outside an enum and a malformed id must be refused
    with a 400 that names the problem; a well-formed id that simply matches nothing is NOT an
    error and must answer 200 with an empty page; nonsensical pagination must be refused rather
    than silently ignored.

    Read-only — no setup, no teardown. All cases run and failures are collected.
    """
    gaps: list[str] = []

    async with async_step(
        "[1/4] Values outside an enum → 400 naming the allowed values", soft=gaps
    ):
        for param, allowed in (("status", _STATUSES), ("clientLifecycleState", _LIFECYCLE)):
            resp = await sa_partners_client.list_attributions(
                params={param: "bogus"}, expected_status=None
            )
            if resp.status_code != 400:
                gaps.append(f"{param}='bogus' answered {resp.status_code}, expected 400")
            elif missing := [v for v in allowed if v not in resp.text]:
                gaps.append(f"the 400 for a bad {param} does not list {missing}")
            else:
                logger.info("CHECK {}='bogus' → 400 listing every allowed value → OK", param)

    async with async_step("[2/4] A malformed id → 400, on the filter and on the path", soft=gaps):
        resp = await sa_partners_client.list_attributions(
            params={"partnerId": "not-an-id"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"partnerId='not-an-id' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed partnerId filter → 400 → OK")

        detail = await sa_partners_client.get_attribution("not-an-id", expected_status=None)
        if detail.status_code != 400:
            gaps.append(f"a malformed attribution id answered {detail.status_code}, expected 400")
        else:
            logger.info("CHECK malformed attribution id → 400 → OK")

    async with async_step("[3/4] A well-formed id that matches nothing", soft=gaps):
        resp = await sa_partners_client.list_attributions(
            params={"partnerId": _GHOST}, expected_status=None
        )
        if resp.status_code != 200:
            gaps.append(
                f"a ghost partnerId answered {resp.status_code}; a valid-format id with no "
                "matches is an empty result, not an error"
            )
        elif (n := _envelope(resp)["total"]) != 0:
            gaps.append(f"a ghost partnerId returned {n} row(s) — the filter was ignored")
        else:
            logger.info("CHECK ghost partnerId → 200 empty → OK")

        detail = await sa_partners_client.get_attribution(_GHOST, expected_status=None)
        if detail.status_code == 200:
            gaps.append(f"a ghost attribution id answered 200: {detail.text[:160]}")
        elif detail.status_code >= 500:
            gaps.append(f"a ghost attribution id crashed the service ({detail.status_code})")
        else:
            logger.info("CHECK ghost attribution id → {} → OK", detail.status_code)

    async with async_step("[4/4] Nonsensical pagination must not dump the whole ledger", soft=gaps):
        for params in ({"limit": -1}, {"limit": 0}, {"page": "abc"}):
            r = await sa_partners_client.list_attributions(params=params, expected_status=None)
            if r.status_code == 200:
                n = len((r.json() or {}).get("data") or [])
                gaps.append(
                    f"{params} answered 200 with {n} row(s) instead of 400. limit=-1 IS refused "
                    "on this very endpoint, so the guard exists and simply misses these values. "
                    "Fourth endpoint with the same root cause after BUG-API-025 (/v1/sa/deals), "
                    "BUG-API-026 (/portal/modules) and BUG-API-027 (/portal/clients) — "
                    "BUG-API-028, one shared fix, confirm with BE"
                )
            elif r.status_code >= 500:
                gaps.append(f"{params} crashed the service ({r.status_code})")
            else:
                logger.info("CHECK {} → {} → OK", params, r.status_code)

    assert not gaps, "Gaps on GET /v1/sa/partner-attributions:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid filter and id refused, empty distinguished from an error")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_tenant_provisioning_attribution_002(sa_deals_client, seeded_partner):
    """PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_002: win an approved deal -> tenant provisioning completes.

    Provision leg of the close->provision->commission chain (PRD v1.8 §7.1). Scope
    is ONLY the provisioning outcome: a WON deal's tenant actually provisions —
    ``wonTenantId`` + ``goLiveAt`` get stamped and ``provisioningState`` reaches
    ``resolved`` within a bounded time. ``goLiveAt`` anchors the commission
    eligibility window, so this is the gate everything downstream depends on.

    NOT covered here: the commission leg (accrues later from
    ``payment.gateway.payment.succeeded``; stays blocked on _005/_006 behind
    ``COMMISSION_ACCRUAL_ENABLED`` + a payment event) and the win-endpoint
    negatives/idempotency (those belong to the deal-pipeline win TC, not to this
    outcome check).

    Currently FAILS by design — it reproduces BUG-API-033 (staging: 0 of the WON
    deals ever reach ``resolved``; ``wonTenantId``/``goLiveAt`` never stamped). It
    turns green the moment BE's provisioning worker runs on staging, so it is the
    regression guard for §7.1.
    """
    async with async_step(
        "Setup: partner + plan + register + approve a referral deal (status 'approved')"
    ):
        partner = await seeded_partner()
        pid = partner.partner_id
        plan_id = await sa_deals_client.pick_billing_plan_id()
        deal = await sa_deals_client.register_deal(make_deal(pid, plan_id, dealType="referral"))
        deal_id = deal.deal_id
        approved = await sa_deals_client.approve_deal(deal_id, plan_id=plan_id)
        assert approved.data.get("status") == "approved", "precondition: deal must be approved"
        logger.info("SETUP: deal {} approved (plan locked)", deal_id)

    async with async_step(
        "[1/4] Mark the approved deal as won (win intake incl. required adminPhoneNumber) -> status 'won'"
    ):
        suffix = uuid.uuid4().hex[:8]
        win_intake = {
            "companyWebsite": "https://qa-auto-provision.example.com",
            "industry": "Technology",
            "adminFirstName": "QA",
            "adminLastName": "Provision",
            "adminEmail": f"qa.auto+provision-{suffix}@mailinator.com",
            "companyName": f"QA-AUTO Provision Co {suffix}",
            "tenantDomain": f"qa-auto-provision-{suffix}.example.com",
            "planId": plan_id,
            "billingCycle": "annual",
            "numberOfEmployee": 42,
            "region": "asia-southeast1",
            "country": "US",
            "actualAcvCents": 7_500_000,
            # Required: the UI's "reuse prospect phone" fallback does not fire, so send it.
            "adminPhoneNumber": {"number": "4155550123", "countryCode": "+1"},
            "notes": "QA-AUTO provision-leg",
        }
        won = await sa_deals_client.win_deal(deal_id, win_intake=win_intake)
        assert won.data.get("status") == "won", (
            f"deal must become 'won', got {won.data.get('status')!r}"
        )
        logger.info(
            "CHECK won -> OK (provisioning kicked off; state={})",
            won.data.get("provisioningState"),
        )

    async with async_step(
        f"[2/4] Poll <={_PROVISION_POLL_TIMEOUT_S}s until provisioning completes "
        "(wonTenantId + goLiveAt stamped)"
    ):
        deadline = asyncio.get_event_loop().time() + _PROVISION_POLL_TIMEOUT_S
        d = won.data
        while True:
            d = (await sa_deals_client.get_deal(deal_id)).data
            if d.get("wonTenantId") and d.get("goLiveAt"):
                break
            if asyncio.get_event_loop().time() >= deadline:
                break
            await asyncio.sleep(_PROVISION_POLL_INTERVAL_S)
        logger.info(
            "POLL end: provisioningState={} wonTenantId={} goLiveAt={}",
            d.get("provisioningState"),
            d.get("wonTenantId"),
            d.get("goLiveAt"),
        )

    async with async_step(
        "[3/4] The WON deal has wonTenantId + goLiveAt stamped (attribution + commission-window anchor)"
    ):
        assert d.get("wonTenantId"), (
            f"wonTenantId not stamped after {_PROVISION_POLL_TIMEOUT_S}s — tenant never "
            "provisioned (BUG-API-033)"
        )
        assert d.get("goLiveAt"), (
            f"goLiveAt not stamped after {_PROVISION_POLL_TIMEOUT_S}s — commission eligibility "
            "window cannot start (BUG-API-033)"
        )
        logger.info(
            "CHECK stamped -> wonTenantId={} goLiveAt={}",
            d.get("wonTenantId"),
            d.get("goLiveAt"),
        )

    async with async_step(
        "[4/4] provisioningState reached 'resolved' (deal no longer awaiting/overdue)"
    ):
        assert d.get("provisioningState") == "resolved", (
            f"provisioningState={d.get('provisioningState')!r}, expected 'resolved' — "
            "provisioning did not complete (BUG-API-033)"
        )
        logger.info(
            "RESULT: provision leg complete — tenant provisioned, commission window can begin"
        )
