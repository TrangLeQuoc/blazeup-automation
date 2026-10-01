"""Partner portal lookups — plans, plans/:planId and countries (sa-partners-api).

Maps to the test plan: PARTNER_API_PARTNER_PORTAL_009 / _010. PRD §4.4.

The three catalogues the deal-registration wizard reads to populate its pickers. All reads,
no writes, no fixtures beyond a portal session — every key used is taken from a list response
at run time.

None of the three is enumerated in PRD §8.5; §4.4 (the wizard) is Confirmed but does not name
its lookups. Scope confirmed 2026-09-24: they implement an approved feature, so they belong
here rather than needing a feature of their own.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

# getPublishedPlans filters to exactly these — custom/bespoke editions are excluded.
_EDITIONS = ("starter", "pro", "enterprise")
_PUBLISHED = "published"
_REQUIRED_FIELDS = (
    "_id",
    "planId",
    "displayName",
    "edition",
    "billingCycle",
    "currency",
    "basePrice",
    "status",
)
_SENSITIVE = ("password", "token", "secret", "credential")
_GHOST = "000000000000000000000000"
# ISO 3166-1 lists ~250 entries; staging returned exactly 250 on 2026-09-24. The floor is set
# below that so a legitimate catalogue edit does not fail the TC, but a truncated list does.
_MIN_COUNTRIES = 200
_COUNTRY_FIELDS = ("_id", "name", "alpha2Code", "alpha3Code")


def _data(resp):
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    assert "data" in body, f"envelope has no `data`: {sorted(body)}"
    return body["data"]


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_009(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_009: partner reads the billing plan catalogue - published only.

    GET /portal/plans and GET /portal/plans/{id}. Asserts the envelope, that EVERY row is a
    published standard edition (the service filters to starter/pro/enterprise and excludes
    custom/bespoke, so a row outside that set means the filter regressed), the row schema, and
    that the detail route returns the same plan the list advertised.

    Precondition: an ACTIVE partner with a portal session. The catalogue must hold at least one
    plan — automation cannot publish one, so an empty catalogue fails the precondition loudly.
    """
    async with async_step("[1/7] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    async with async_step("[2/7] GET the catalogue → a valid, non-empty list"):
        plans = _data(await portal.list_plans())
        assert isinstance(plans, list), f"`data` must be a list, got {type(plans).__name__}"
        assert plans, (
            "the plan catalogue is empty — the deal-registration form would have nothing to "
            "offer. Automation cannot publish a plan, so this is an environment precondition"
        )
        logger.info("CHECK catalogue reachable → OK ({} plan(s))", len(plans))

    async with async_step("[3/7] Every plan is PUBLISHED and a standard edition"):
        for plan in plans:
            missing = [f for f in _REQUIRED_FIELDS if f not in plan]
            assert not missing, f"plan row is missing {missing}: {sorted(plan)}"
            assert plan["status"] == _PUBLISHED, (
                f"plan {plan.get('planId')!r} has status {plan['status']!r} — an unpublished "
                "plan must never reach the partner-facing picker"
            )
            assert plan["edition"] in _EDITIONS, (
                f"plan {plan.get('planId')!r} has edition {plan['edition']!r}, outside "
                f"{_EDITIONS}. Custom/bespoke editions are excluded by the service — this row "
                "means that filter regressed and a partner can see a bespoke plan"
            )
            leaked = sorted(k for k in plan if any(s.lower() in k.lower() for s in _SENSITIVE))
            assert not leaked, f"credential material on a plan row: {leaked}"
        logger.info(
            "CHECK all published, editions ⊆ {} → OK", sorted({p["edition"] for p in plans})
        )

    async with async_step("[4/7] Plan keys are unique — the picker cannot show a duplicate"):
        ids = [str(p["_id"]) for p in plans]
        slugs = [p["planId"] for p in plans]
        assert len(set(ids)) == len(ids), f"duplicate `_id` in the catalogue: {ids}"
        assert len(set(slugs)) == len(slugs), f"duplicate `planId` slug: {slugs}"
        logger.info("CHECK ids and slugs unique → OK")

    async with async_step("[5/7] The detail route returns the plan that was asked for"):
        wanted = plans[0]
        got = _data(await portal.get_plan(str(wanted["_id"])))
        assert str(got.get("_id")) == str(wanted["_id"]), (
            f"asked for plan {wanted['_id']} and received {got.get('_id')}"
        )
        for field in ("planId", "displayName", "edition", "billingCycle", "currency"):
            assert got.get(field) == wanted.get(field), (
                f"the detail route reports {field}={got.get(field)!r} but the list said "
                f"{wanted.get(field)!r} for the same plan"
            )
        assert got["status"] == _PUBLISHED, "the detail route returned an unpublished plan"
        logger.info("CHECK detail matches the list row → OK ({})", wanted.get("planId"))

    async with async_step("[6/7] The country lookup is complete and well-formed"):
        countries = _data(await portal.list_countries())
        assert isinstance(countries, list), f"`data` must be a list, got {type(countries).__name__}"
        assert len(countries) >= _MIN_COUNTRIES, (
            f"the country picker offers only {len(countries)} entries. There are ~250 ISO "
            f"3166-1 countries; a list this short means the lookup is truncated and partners "
            "cannot register a deal for the missing markets"
        )
        for row in countries:
            missing = [f for f in _COUNTRY_FIELDS if not row.get(f)]
            assert not missing, f"country row is missing/blank {missing}: {row}"
            assert len(row["alpha2Code"]) == 2, f"alpha2Code is not 2 chars: {row}"
            assert len(row["alpha3Code"]) == 3, f"alpha3Code is not 3 chars: {row}"
            assert row["_id"] == row["alpha2Code"], (
                f"`_id` ({row['_id']}) is not the alpha-2 code ({row['alpha2Code']}) — the "
                "picker uses _id as the value it submits, so the two must agree"
            )
        codes = [r["alpha2Code"] for r in countries]
        assert len(set(codes)) == len(codes), "duplicate alpha2Code in the country list"
        logger.info("CHECK {} countries, codes unique and well-formed → OK", len(countries))

    async with async_step("[7/7] The country `search` narrows without being case-sensitive"):
        for term in ("viet", "VIET", "Viet"):
            hits = _data(await portal.list_countries(params={"search": term}))
            assert hits, f"search={term!r} matched nothing, but 'Viet Nam' is in the list"
            assert all(term.lower() in r["name"].lower() for r in hits), (
                f"search={term!r} returned {[r['name'] for r in hits]} — a row whose name does "
                "not contain the term means the filter was ignored"
            )
            assert len(hits) < len(countries), f"search={term!r} did not narrow the list at all"
        logger.info("CHECK country search narrows, case-insensitive → OK")

    logger.info("RESULT: wizard lookups verified — plans published-only, countries complete")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_010(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_010: plan catalogue invalid key - correct rejection.

    Negative counterpart of _009. A key that does not exist must be refused with a 4xx that
    names what was not found, and a key that is not an id at all must be refused too — never a
    200 carrying some other plan, never a 5xx.

    The step that matters most is the CONTRACT one: the route is declared `plans/:planId` and
    its OpenAPI `@ApiParam` documents a kebab-case slug, so the row's own `planId` must work.
    It does not — see BUG-API-029.

    All cases run and failures are collected.
    """
    async with async_step("[1/5] Setup: portal session + one plan to borrow keys from"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        plans = _data(await portal.list_plans())
        assert plans, "precondition: the catalogue must hold at least one plan"
        sample = plans[0]
        logger.info(
            "SETUP: partner={} sample _id={} planId={!r}",
            partner_id,
            sample["_id"],
            sample.get("planId"),
        )

    gaps: list[str] = []

    async with async_step("[2/5] The documented `planId` slug must resolve the plan"):
        slug = sample.get("planId")
        resp = await portal.get_plan(str(slug), expected_status=None)
        if resp.status_code == 200:
            logger.info("CHECK planId slug resolves → 200 → OK")
        else:
            gaps.append(
                f"GET /portal/plans/{slug!r} answered {resp.status_code} ({resp.text[:120]}), but "
                f"that value is the `planId` of a plan the catalogue just returned. The route is "
                "declared `plans/:planId` and its @ApiParam documents a kebab-case slug "
                "('e.g. pro-annual'), yet the service queries { _id: planId } — so the parameter "
                "named planId is the only thing it will NOT accept. A client written from the "
                "OpenAPI spec always fails here. BUG-API-029, confirm with BE which side is wrong"
            )

    async with async_step("[3/5] A well-formed key that matches nothing → 404 naming it"):
        resp = await portal.get_plan(_GHOST, expected_status=None)
        if resp.status_code == 200:
            gaps.append(f"a ghost plan key answered 200 with a plan: {resp.text[:160]}")
        elif resp.status_code >= 500:
            gaps.append(f"a ghost plan key crashed the service ({resp.status_code})")
        elif _GHOST not in resp.text:
            gaps.append(f"the {resp.status_code} for a ghost plan key does not name the key")
        else:
            logger.info("CHECK ghost plan key → {} naming it → OK", resp.status_code)

    async with async_step("[4/5] A key that is not an id at all → 400, and never a 5xx"):
        # No path-traversal case here: `plans/../plans` is normalised to `plans` before the
        # request is even sent, so it would assert URL resolution rather than this endpoint.
        for bad in ("not-a-plan", "%20", "null"):
            resp = await portal.get_plan(bad, expected_status=None)
            if resp.status_code == 200:
                gaps.append(f"plan key {bad!r} answered 200: {resp.text[:140]}")
            elif resp.status_code >= 500:
                gaps.append(f"plan key {bad!r} crashed the service ({resp.status_code})")
            else:
                logger.info("CHECK plan key {!r} → {} → OK", bad, resp.status_code)

    async with async_step("[5/5] A country search that matches nothing → 200 empty, not an error"):
        resp = await portal.list_countries(
            params={"search": "QA-AUTO no such country"}, expected_status=None
        )
        if resp.status_code != 200:
            gaps.append(
                f"an unmatched country search answered {resp.status_code}; no match is an empty "
                "result, not an error — the picker would show a failure instead of 'no results'"
            )
        elif rows := _data(resp):
            gaps.append(
                f"an unmatched country search returned {len(rows)} row(s) "
                f"({[r.get('name') for r in rows[:3]]}) — the search term was ignored"
            )
        else:
            logger.info("CHECK unmatched country search → 200 empty → OK")

    assert not gaps, "Gaps on the wizard lookups:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid key refused; unmatched search is empty, not an error")
