"""Deal-pipeline KPI stats — partner-portal and SA (service: sa-partners-api).

Maps to the test plan:
  * PARTNER_API_DASHBOARD_DATA_002 / _003        GET /v1/partner/portal/deals/stats  (PRD §4.3)
  * PARTNER_API_PIPELINE_MANAGEMENT_012 / _013   GET /v1/sa/deals/stats              (PRD §5.5)

One aggregate, two surfaces, and the difference between them is the point. Both return the
same counters; only the SA route may carry `byProvisioningState`. The service signature makes
that explicit — `stats(query, includeProvisioning = false)`, with "only the SA controller
passes true; the partner-portal stats surface must omit `byProvisioningState` entirely (§2.1)".

The published Swagger example shows the field on BOTH routes because they share one response
DTO, so reading the spec would tell you the opposite of the rule. Measured 2026-09-24: the
implementation is right and the example is misleading — which is exactly why _002 asserts the
absence rather than trusting either.

Neither endpoint appears in PRD §8.5; §4.3 and §5.5 are Confirmed features that do not name
their endpoints. Scope confirmed 2026-09-24.
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_prospect
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

_STATUSES = ("registered", "approved", "in_progress", "won", "lost", "expired", "rejected")
_TYPES = ("referral", "reseller", "co_sell", "admin_attach")
_PROVISIONING = ("awaited", "overdue", "resolved", "legacy_unknown")
_SCALARS = ("total", "openCount", "conflictedCount", "wonEstimatedAcvCents")
_CONFLICT_STATUSES = ("none", "flagged", "resolved_for_partner", "resolved_against_partner")
_GHOST = "000000000000000000000000"


def _data(resp) -> dict:
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    assert "data" in body, f"envelope has no `data`: {sorted(body)}"
    data = body["data"]
    assert isinstance(data, dict), f"`data` must be an object, got {type(data).__name__}"
    return data


def _assert_core_shape(data: dict, where: str) -> None:
    """The counters both surfaces share, zero-filled and correctly typed."""
    for key in _SCALARS:
        assert key in data, f"{where}: missing `{key}`: {sorted(data)}"
        value = data[key]
        assert isinstance(value, int) and not isinstance(value, bool), (
            f"{where}: {key} is {type(value).__name__} ({value!r}), must be an int"
        )
        assert value >= 0, f"{where}: {key} is negative ({value})"

    for bucket, members in (("byStatus", _STATUSES), ("byType", _TYPES)):
        assert bucket in data, f"{where}: missing `{bucket}`: {sorted(data)}"
        got = data[bucket]
        assert isinstance(got, dict), f"{where}: `{bucket}` must be an object"
        missing = [m for m in members if m not in got]
        assert not missing, (
            f"{where}: `{bucket}` is missing {missing}. The aggregate is documented as "
            "zero-filled, so an absent key is a defect — a dashboard reading it would render "
            "a blank instead of 0"
        )
        for member, count in got.items():
            assert isinstance(count, int) and not isinstance(count, bool), (
                f"{where}: {bucket}.{member} is {type(count).__name__} ({count!r})"
            )
            assert count >= 0, f"{where}: {bucket}.{member} is negative ({count})"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_dashboard_data_002(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_DASHBOARD_DATA_002: partner reads own pipeline KPIs - scoped, no SA-only fields.

    GET /v1/partner/portal/deals/stats. A fresh partner starts at zero across the board, then
    registers one deal and the counters must move by exactly one — that is what proves the
    aggregate is computed rather than stubbed, and it is reachable here because the partner
    owns the data it is counting.

    The other half is a leak check: `byProvisioningState` is SA-only (§2.1) and must not be on
    this surface, no matter what the shared Swagger example shows.

    Precondition: an ACTIVE partner with a portal session and no deals.
    """
    async with async_step("[1/5] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    async with async_step("[2/5] A partner with no deals reads a fully zero-filled aggregate"):
        before = _data(await portal.get_deal_stats())
        _assert_core_shape(before, "portal stats (empty partner)")
        assert before["total"] == 0, (
            f"a partner that has registered nothing reports total={before['total']} — the "
            "aggregate is not scoped to the caller"
        )
        assert all(v == 0 for v in before["byStatus"].values()), (
            f"byStatus is non-zero for a partner with no deals: {before['byStatus']}"
        )
        logger.info("CHECK empty partner → every counter 0, all buckets present → OK")

    async with async_step("[3/5] `byProvisioningState` must NOT be on the partner surface"):
        assert "byProvisioningState" not in before, (
            "the partner-portal stats surface returned `byProvisioningState` "
            f"({before.get('byProvisioningState')}). It is SA-only (AC-19/AC-20, §2.1): it "
            "exposes the internal provisioning watchdog — including how many tenants are "
            "OVERDUE — to the partner. The published Swagger example does show this field "
            "because both routes share one DTO, so the spec is not the authority here"
        )
        logger.info("CHECK byProvisioningState absent from the portal surface → OK")

    async with async_step("[4/5] Registering one deal moves the counters by exactly one"):
        plan_id = await sa_deals_client.pick_billing_plan_id()
        created = (await portal.register_deal(make_deal(None, plan_id, **make_prospect()))).json()
        deal = created.get("data") or {}
        status, deal_type = deal.get("status"), deal.get("dealType")
        assert deal.get("_id"), "precondition: the partner must be able to register a deal"

        after = _data(await portal.get_deal_stats())
        _assert_core_shape(after, "portal stats (one deal)")
        assert after["total"] == 1, f"after one registration total={after['total']}, expected 1"
        assert after["byStatus"][status] == 1, (
            f"the deal is {status!r} but byStatus[{status!r}]={after['byStatus'][status]} — the "
            "aggregate is not counting it"
        )
        assert after["byType"][deal_type] == 1, (
            f"byType[{deal_type!r}]={after['byType'][deal_type]}, expected 1"
        )
        assert sum(after["byStatus"].values()) == after["total"], (
            f"byStatus sums to {sum(after['byStatus'].values())} but total is {after['total']} "
            "— every deal must fall in exactly one status bucket"
        )
        logger.info("CHECK one deal → total 1, {} bucket 1, sums agree → OK", status)

    async with async_step("[5/5] The `status` filter narrows the aggregate"):
        matching = _data(await portal.get_deal_stats(params={"status": status}))
        assert matching["total"] == 1, f"status={status!r} reports total={matching['total']}"

        other = next(s for s in _STATUSES if s != status)
        empty = _data(await portal.get_deal_stats(params={"status": other}))
        assert empty["total"] == 0, (
            f"status={other!r} reports total={empty['total']} although the only deal is "
            f"{status!r} — the filter was accepted and ignored"
        )
        logger.info("CHECK status filter narrows → OK ({} → 1, {} → 0)", status, other)

    logger.info("RESULT: portal pipeline KPIs verified — scoped, counted, no SA-only field")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_dashboard_data_003(sa_partners_client, settings, created_resources):
    """PARTNER_API_DASHBOARD_DATA_003: partner pipeline KPIs invalid filter - correct rejection.

    Negative counterpart of _002. A status outside the enum must be refused with a 400 naming
    the allowed values, and a `search` term that matches nothing is a zeroed aggregate rather
    than an error — a dashboard must be able to tell "no results" from "request failed".

    All cases run and failures are collected.
    """
    async with async_step("[1/3] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    gaps: list[str] = []

    async with async_step(
        "[2/3] A status outside the enum → 400 listing the allowed values", soft=gaps
    ):
        resp = await portal.get_deal_stats(params={"status": "bogus"}, expected_status=None)
        if resp.status_code != 400:
            gaps.append(f"status='bogus' answered {resp.status_code}, expected 400")
        elif missing := [s for s in _STATUSES if s not in resp.text]:
            gaps.append(f"the 400 for a bad status does not list {missing}")
        else:
            logger.info("CHECK status='bogus' → 400 listing every status → OK")

    async with async_step(
        "[3/3] A search matching nothing → 200 zeroed, never an error", soft=gaps
    ):
        resp = await portal.get_deal_stats(
            params={"search": "QA-AUTO no such prospect"}, expected_status=None
        )
        if resp.status_code != 200:
            gaps.append(
                f"an unmatched search answered {resp.status_code}; no match is a zeroed "
                "aggregate, not an error"
            )
        else:
            data = _data(resp)
            if data["total"] != 0:
                gaps.append(f"an unmatched search reports total={data['total']} — search ignored")
            elif "byStatus" not in data:
                gaps.append("a zeroed aggregate dropped `byStatus` — it must stay zero-filled")
            else:
                logger.info("CHECK unmatched search → 200, zeroed, still filled → OK")

    assert not gaps, "Gaps on the portal deal stats:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid filters refused, empty result distinguished from an error")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_pipeline_management_012(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_PIPELINE_MANAGEMENT_012: SA reads pipeline KPIs across all partners.

    GET /v1/sa/deals/stats. The SA-wide twin of DASHBOARD_DATA_002: same counters plus
    `byProvisioningState`, which belongs HERE and only here.

    Two properties beyond the shape. First, the aggregate must agree with the list endpoint it
    summarises — `total` against `GET /v1/sa/deals`, which is what catches a stats query that
    drifts from the list query. Second, `partnerId` must narrow: an SA figure that ignores the
    filter would silently report platform-wide numbers on a single partner's page.

    Read-only apart from one deal registered to give the filter something to find.
    """
    async with async_step("[1/5] GET the SA aggregate → correctly shaped, SA-wide"):
        overall = _data(await sa_deals_client.get_deal_stats())
        _assert_core_shape(overall, "SA stats")
        assert overall["total"] > 0, (
            "the SA-wide aggregate reports 0 deals, but staging holds well over a thousand — "
            "the aggregate is not reading the collection"
        )
        logger.info("CHECK SA aggregate → OK (total={})", overall["total"])

    async with async_step("[2/5] `byProvisioningState` is present and zero-filled HERE"):
        assert "byProvisioningState" in overall, (
            "the SA aggregate is missing `byProvisioningState`. It is the only surface allowed "
            "to carry it (AC-19/AC-20), and it is how the provisioning watchdog backlog is read"
        )
        bucket = overall["byProvisioningState"]
        missing = [s for s in _PROVISIONING if s not in bucket]
        assert not missing, f"`byProvisioningState` is missing {missing}: {sorted(bucket)}"
        for state, count in bucket.items():
            assert isinstance(count, int) and count >= 0, (
                f"byProvisioningState.{state} is {count!r}"
            )
        logger.info("CHECK byProvisioningState present, zero-filled → OK ({})", bucket)

    async with async_step("[3/5] The aggregate agrees with the list it summarises"):
        listed = (await sa_deals_client.list_deals(params={"limit": 1})).json()
        assert listed.get("total") == overall["total"], (
            f"GET /v1/sa/deals reports total={listed.get('total')} but /deals/stats reports "
            f"{overall['total']}. Two views of one collection disagreeing means the stats match "
            "stage has drifted from the list query"
        )
        assert sum(overall["byStatus"].values()) == overall["total"], (
            f"byStatus sums to {sum(overall['byStatus'].values())}, total is {overall['total']}"
        )
        logger.info("CHECK stats total == list total == byStatus sum → OK")

    async with async_step("[4/5] Setup: a partner with exactly one known deal"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        plan_id = await sa_deals_client.pick_billing_plan_id()
        created = (await portal.register_deal(make_deal(None, plan_id, **make_prospect()))).json()
        deal = created.get("data") or {}
        assert deal.get("_id"), "precondition: the partner must be able to register a deal"
        logger.info("SETUP: partner={} one deal, status={}", partner_id, deal.get("status"))

    async with async_step("[5/5] `partnerId` narrows the aggregate to that partner alone"):
        scoped = _data(await sa_deals_client.get_deal_stats(params={"partnerId": partner_id}))
        _assert_core_shape(scoped, "SA stats (scoped)")
        assert scoped["total"] == 1, (
            f"partnerId={partner_id} reports total={scoped['total']} for a partner with exactly "
            f"one deal. If it equals the platform total ({overall['total']}) the filter is "
            "accepted and ignored, and every per-partner figure SA sees is wrong"
        )
        assert scoped["byStatus"][deal["status"]] == 1, (
            f"scoped byStatus[{deal['status']!r}]={scoped['byStatus'][deal['status']]}"
        )
        empty = _data(await sa_deals_client.get_deal_stats(params={"partnerId": _GHOST}))
        assert empty["total"] == 0, f"a ghost partnerId reports total={empty['total']}"
        logger.info("CHECK partnerId narrows → OK (1 of {}), ghost → 0", overall["total"])

    logger.info(
        "RESULT: SA pipeline KPIs verified — SA-wide, watchdog block present, filters narrow"
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_pipeline_management_013(sa_deals_client):
    """PARTNER_API_PIPELINE_MANAGEMENT_013: SA pipeline KPIs invalid filter - correct rejection.

    Negative counterpart of _012. Every filter this endpoint shares with the deal list must
    reject a value outside its enum, a malformed id must be refused, and a well-formed id that
    matches nothing must answer a zeroed aggregate rather than an error.

    Read-only — no setup, no teardown. All cases run and failures are collected.
    """
    gaps: list[str] = []

    async with async_step("[1/3] Every enum filter refuses a value outside the spec", soft=gaps):
        for param, allowed in (
            ("status", _STATUSES),
            ("dealType", _TYPES),
            ("conflictStatus", _CONFLICT_STATUSES),
            ("provisioningState", _PROVISIONING),
        ):
            resp = await sa_deals_client.get_deal_stats(
                params={param: "bogus"}, expected_status=None
            )
            if resp.status_code != 400:
                gaps.append(f"{param}='bogus' answered {resp.status_code}, expected 400")
            elif missing := [v for v in allowed if v not in resp.text]:
                gaps.append(f"the 400 for a bad {param} does not list {missing}")
            else:
                logger.info("CHECK {}='bogus' → 400 listing every value → OK", param)

    async with async_step("[2/3] A malformed partnerId → 400", soft=gaps):
        resp = await sa_deals_client.get_deal_stats(
            params={"partnerId": "not-an-id"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"partnerId='not-an-id' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed partnerId → 400 → OK")

    async with async_step("[3/3] A ghost partnerId → 200 zeroed, still fully filled", soft=gaps):
        resp = await sa_deals_client.get_deal_stats(
            params={"partnerId": _GHOST}, expected_status=None
        )
        if resp.status_code != 200:
            gaps.append(
                f"a ghost partnerId answered {resp.status_code}; a valid-format id with no "
                "matches is a zeroed aggregate, not an error"
            )
        else:
            data = _data(resp)
            if data["total"] != 0:
                gaps.append(f"a ghost partnerId reports total={data['total']} — filter ignored")
            elif any(b not in data for b in ("byStatus", "byType", "byProvisioningState")):
                gaps.append(
                    f"a zeroed SA aggregate dropped buckets: {sorted(data)}. Zero-filling must "
                    "survive an empty match, or a dashboard renders blanks instead of zeros"
                )
            else:
                logger.info("CHECK ghost partnerId → 200, zeroed, all buckets present → OK")

    assert not gaps, "Gaps on GET /v1/sa/deals/stats:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid filter refused, empty result distinguished from an error")
