"""SA deal list — GET /v1/sa/deals (service: sa-partners-api).

Maps to the test plan: PARTNER_API_DEAL_REGISTRATION_PIPELINE_035 / _036. PRD §5.2, §8.5
(`GET /internal/deals` in the requirement wording).

The SA-wide view over EVERY partner's deals — 1405 rows on staging 2026-09-17. Nothing may be
assumed about the unfiltered page, so every assertion here either filters down to a deal this
TC registered, or checks a property that must hold for whatever rows come back.
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_prospect
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

# Returned in the 400 body when an unknown status is sent — the spec's own list.
_STATUSES = ("registered", "approved", "in_progress", "won", "lost", "expired", "rejected")
_DEAL_TYPES = ("referral", "reseller", "co_sell")
_GHOST = "000000000000000000000000"
_SENSITIVE = ("password", "token", "secret", "credential")


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
async def test_partner_api_deal_registration_pipeline_035(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_035: SA lists deals - filters narrow the result.

    Registers one deal, then proves each filter actually narrows: `partnerId` returns only that
    partner's rows, `status` and `dealType` return only matching rows, and `limit` caps the page
    without changing `total`. A filter that is accepted and then ignored is the failure mode
    this is written against — BUG-API-023 is exactly that on a sibling endpoint.

    Precondition: an ACTIVE partner with a portal session and one registered deal.
    """
    async with async_step("[1/7] Setup: an active partner registers one deal"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        plan_id = await sa_deals_client.pick_billing_plan_id()
        created = (await portal.register_deal(make_deal(None, plan_id, **make_prospect()))).json()
        deal = created.get("data") or {}
        deal_id = deal.get("_id")
        assert deal_id, "precondition: the partner must be able to register a deal"
        logger.info("SETUP: partner={} deal={} status={}", partner_id, deal_id, deal.get("status"))

    async with async_step("[2/7] GET the unfiltered list → a valid, non-empty page"):
        body = _envelope(await sa_deals_client.list_deals(params={"limit": 5}))
        assert body["total"] > 0, "the SA deal list is empty — the environment has no deals"
        assert len(body["data"]) <= 5, f"limit=5 returned {len(body['data'])} rows"
        logger.info("CHECK unfiltered list → OK (total={})", body["total"])

    async with async_step("[3/7] Filter by partnerId → only that partner, and our deal is there"):
        body = _envelope(
            await sa_deals_client.list_deals(params={"partnerId": partner_id, "limit": 50})
        )
        rows = body["data"]
        assert rows, f"partnerId={partner_id} returned nothing although it just registered a deal"
        foreign = [d for d in rows if str(d.get("partnerId")) != str(partner_id)]
        assert not foreign, (
            f"the partnerId filter was accepted and ignored: {len(foreign)} of {len(rows)} rows "
            "belong to another partner"
        )
        assert any(d.get("_id") == deal_id for d in rows), (
            "the registered deal is not in its own partner's list"
        )
        logger.info("CHECK partnerId filter narrows correctly → OK (n={})", len(rows))

    async with async_step("[4/7] Verify the deal row is well-formed and leaks nothing"):
        row = next(d for d in rows if d.get("_id") == deal_id)
        for field in ("_id", "partnerId", "dealType", "status", "prospectName", "createdAt"):
            assert field in row, f"deal row is missing `{field}`: {sorted(row)}"
        assert row["status"] in _STATUSES, f"status outside the enum: {row['status']!r}"
        assert row["dealType"] in _DEAL_TYPES, f"dealType outside the enum: {row['dealType']!r}"
        leaked = sorted(k for k in row if any(s.lower() in k.lower() for s in _SENSITIVE))
        assert not leaked, f"credential material exposed in a deal row: {leaked}"
        logger.info("CHECK deal row typed and clean → OK")

    async with async_step("[5/7] Filter by status → every row carries that status"):
        status = row["status"]
        body = _envelope(
            await sa_deals_client.list_deals(params={"partnerId": partner_id, "status": status})
        )
        wrong = [d.get("status") for d in body["data"] if d.get("status") != status]
        assert not wrong, f"status={status!r} returned rows with {sorted(set(wrong))}"
        logger.info("CHECK status filter → OK (status={})", status)

    async with async_step("[6/7] Filter by dealType → every row carries that type"):
        deal_type = row["dealType"]
        body = _envelope(
            await sa_deals_client.list_deals(
                params={"partnerId": partner_id, "dealType": deal_type}
            )
        )
        wrong = [d.get("dealType") for d in body["data"] if d.get("dealType") != deal_type]
        assert not wrong, f"dealType={deal_type!r} returned rows with {sorted(set(wrong))}"
        logger.info("CHECK dealType filter → OK (dealType={})", deal_type)

    async with async_step("[7/7] Pagination caps the page without changing the total"):
        full = _envelope(await sa_deals_client.list_deals(params={"limit": 50}))
        one = _envelope(await sa_deals_client.list_deals(params={"limit": 1}))
        assert len(one["data"]) == 1, f"limit=1 returned {len(one['data'])} rows"
        assert one["total"] == full["total"], (
            f"`total` changed with the page size: {one['total']} vs {full['total']} — it must "
            "count the whole result set, not the page"
        )
        logger.info("CHECK limit caps the page, total unchanged → OK (total={})", one["total"])

    logger.info("RESULT: SA deal list verified — every filter narrows, nothing leaks")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_036(sa_deals_client):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_036: SA deal list invalid filter - correct rejection.

    Negative counterpart of _035. A value outside an enum, a malformed id and bad pagination
    must be refused with a 4xx that names the problem; a well-formed id that simply matches
    nothing is NOT an error and must answer 200 with an empty page.

    Read-only — no setup, no teardown. All cases run and failures are collected.
    """
    gaps: list[str] = []

    async with async_step("[1/4] Values outside an enum → 400 naming the allowed values"):
        for param, allowed in (("status", _STATUSES), ("dealType", _DEAL_TYPES)):
            resp = await sa_deals_client.list_deals(params={param: "bogus"}, expected_status=None)
            if resp.status_code != 400:
                gaps.append(f"{param}='bogus' answered {resp.status_code}, expected 400")
            elif missing := [v for v in allowed if v not in resp.text]:
                gaps.append(f"the 400 for a bad {param} does not list {missing}")
            else:
                logger.info("CHECK {}='bogus' → 400 listing every allowed value → OK", param)

    async with async_step("[2/4] Malformed partnerId → 400"):
        resp = await sa_deals_client.list_deals(
            params={"partnerId": "not-an-id"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"partnerId='not-an-id' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed partnerId → 400 → OK")

    async with async_step("[3/4] Bad pagination → 400, never a silent default"):
        for params in ({"limit": -1}, {"limit": 0}, {"page": "abc"}):
            resp = await sa_deals_client.list_deals(params=params, expected_status=None)
            if resp.status_code != 400:
                n = len((resp.json().get("data") or []) if resp.status_code < 400 else [])
                gaps.append(
                    f"{params} answered {resp.status_code} with {n} row(s) instead of 400 — a "
                    "nonsensical page size must be refused, not quietly ignored. It is not "
                    "ignored down to a default either: the response carries the WHOLE table in "
                    "one page, so a caller can pull every deal in the system with one request. "
                    "limit=-1 IS refused with 400, so the validation exists and simply misses "
                    "these. BUG-API-025, confirm with BE"
                )
            else:
                logger.info("CHECK {} → 400 → OK", params)

    async with async_step("[4/4] A well-formed id that matches nothing → 200, empty page"):
        resp = await sa_deals_client.list_deals(params={"partnerId": _GHOST}, expected_status=None)
        if resp.status_code != 200:
            gaps.append(
                f"a ghost partnerId answered {resp.status_code}; a valid-format id with no "
                "matches is an empty result, not an error"
            )
        else:
            body = _envelope(resp)
            if body["total"] != 0 or body["data"]:
                gaps.append(
                    f"a ghost partnerId returned {body['total']} row(s) — the filter was ignored"
                )
            else:
                logger.info("CHECK ghost partnerId → 200 empty → OK")

    assert not gaps, "Gaps on GET /v1/sa/deals:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid filter refused, empty result distinguished from an error")
