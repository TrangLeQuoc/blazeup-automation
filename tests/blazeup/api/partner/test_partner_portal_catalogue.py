"""Partner portal catalogue reads — modules + team certifications (service: sa-partners-api).

Maps to the test plan: PARTNER_API_PARTNER_PORTAL_007 / _008. PRD §4.8 (certifications) and
the module catalogue the deal wizard reads.

Two endpoints, one TC pair, because both are plain partner-scoped reads with the same envelope
and neither needs the other's setup.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

# From the 400 body when an unknown value is sent — the spec's own lists.
_CERT_STATUSES = ("active", "expired", "revoked")
_CERT_TYPE = "sales_certified"
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
async def test_partner_api_partner_portal_007(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_007: partner reads the module catalogue and its team's certs.

    GET /portal/modules and GET /portal/team/certifications. The certification leg is proven by
    effect: the team list is empty, SA grants a certification, and the same call then returns
    it — so the endpoint is shown to reflect state rather than to answer 200.

    Precondition: an ACTIVE partner with a portal session and no certifications yet.
    """
    async with async_step("[1/6] Setup: mint an active partner + portal session"):
        portal, partner_id, user_id = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={} sessionUser={}", partner_id, user_id)

    async with async_step("[2/6] GET the module catalogue → a valid, non-empty page"):
        body = _envelope(await portal.get_modules())
        rows = body["data"]
        assert body["total"] > 0, (
            "the module catalogue is empty — the deal wizard has nothing to offer"
        )
        for row in rows:
            for field in ("_id", "name"):
                assert row.get(field), f"module row is missing `{field}`: {row}"
        logger.info("CHECK module catalogue → OK (total={})", body["total"])

    async with async_step("[3/6] The `name` filter narrows to the matching module"):
        target = rows[0]["name"]
        body = _envelope(await portal.get_modules(params={"name": target}))
        wrong = [m.get("name") for m in body["data"] if m.get("name") != target]
        assert not wrong, f"name={target!r} also returned {sorted(set(wrong))}"
        assert body["data"], f"name={target!r} returned nothing although it came from the list"
        logger.info("CHECK name filter narrows → OK (name={!r})", target)

    async with async_step("[4/6] The team certification list starts empty"):
        body = _envelope(await portal.get_team_certifications())
        assert body["total"] == 0, (
            f"a freshly created partner already holds {body['total']} certification(s) — the "
            "grant in the next step would prove nothing"
        )
        logger.info("CHECK team certifications start empty → OK")

    async with async_step("[5/6] SA grants a certification → it appears in the team list"):
        await sa_partners_client.grant_certification(user_id, certification_type=_CERT_TYPE)
        body = _envelope(await portal.get_team_certifications())
        assert body["total"] == 1, f"after one grant the team list holds {body['total']} row(s)"
        cert = body["data"][0]
        for field in ("_id", "partnerId", "userId", "certificationType", "status", "earnedAt"):
            assert field in cert, f"certification row is missing `{field}`: {sorted(cert)}"
        assert cert["certificationType"] == _CERT_TYPE, "a different certification came back"
        assert cert["status"] in _CERT_STATUSES, f"status outside the enum: {cert['status']!r}"
        assert str(cert["partnerId"]) == str(partner_id), "the row belongs to another partner"
        leaked = sorted(k for k in cert if any(s.lower() in k.lower() for s in _SENSITIVE))
        assert not leaked, f"credential material exposed on a certification row: {leaked}"
        logger.info("CHECK granted certification appears, scoped and typed → OK")

    async with async_step("[6/6] Both certification filters narrow the result"):
        for param, value in (("status", cert["status"]), ("certificationType", _CERT_TYPE)):
            body = _envelope(await portal.get_team_certifications(params={param: value}))
            wrong = [c.get(param) for c in body["data"] if c.get(param) != value]
            assert not wrong, f"{param}={value!r} also returned {sorted(set(wrong))}"
            assert body["data"], f"{param}={value!r} returned nothing although a row matches"
            logger.info("CHECK {} filter narrows → OK", param)

    logger.info("RESULT: module catalogue and team certifications verified by effect")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_portal_008(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_PORTAL_008: portal catalogue invalid input - correct rejection.

    Negative counterpart of _007: values outside an enum, a filter that matches nothing, bad
    pagination, and the `groupByCategory` view.

    `groupByCategory=true` is a documented feature rather than an edge case, but it is asserted
    here because what it returns is unusable — see the note on BUG-API-026.

    All cases run and failures are collected.
    """
    async with async_step("[1/5] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    gaps: list[str] = []

    async with async_step("[2/5] Certification values outside an enum → 400", soft=gaps):
        for param, allowed in (("status", _CERT_STATUSES), ("certificationType", None)):
            resp = await portal.get_team_certifications(
                params={param: "bogus"}, expected_status=None
            )
            if resp.status_code != 400:
                gaps.append(f"{param}='bogus' answered {resp.status_code}, expected 400")
            elif allowed and (missing := [v for v in allowed if v not in resp.text]):
                gaps.append(f"the 400 for a bad {param} does not list {missing}")
            else:
                logger.info("CHECK {}='bogus' → 400 → OK", param)

    async with async_step("[3/5] A module name that matches nothing → 200, empty page", soft=gaps):
        resp = await portal.get_modules(
            params={"name": "QA-AUTO no such module"}, expected_status=None
        )
        if resp.status_code != 200:
            gaps.append(f"an unmatched module name answered {resp.status_code}, expected 200 empty")
        else:
            body = _envelope(resp)
            if body["data"]:
                gaps.append(
                    f"an unmatched module name returned {len(body['data'])} row(s) — the filter "
                    "was ignored"
                )
            else:
                logger.info("CHECK unmatched name → 200 empty → OK")

    async with async_step(
        "[4/5] Bad pagination on modules → 400, never the whole table", soft=gaps
    ):
        for params in ({"limit": -1}, {"limit": 0}, {"page": "abc"}):
            resp = await portal.get_modules(params=params, expected_status=None)
            if resp.status_code != 400:
                n = len((resp.json().get("data") or []) if resp.status_code < 400 else [])
                gaps.append(
                    f"modules {params} answered {resp.status_code} with {n} row(s) instead of "
                    "400. /v1/sa/deals refuses limit=-1, so the service knows how to validate "
                    "this — the portal catalogue simply does not. BUG-API-026, confirm with BE"
                )
            else:
                logger.info("CHECK modules {} → 400 → OK", params)

    async with async_step("[5/5] groupByCategory must return usable rows", soft=gaps):
        body = _envelope(await portal.get_modules(params={"groupByCategory": "true"}))
        broken = [m for m in body["data"] if str(m.get("_id")) == "undefined" or len(m) <= 1]
        if broken:
            gaps.append(
                f"groupByCategory=true returned {len(broken)} of {len(body['data'])} row(s) that "
                'are only {"_id": "undefined"} — no category name, no members, and the literal '
                'string "undefined" where an id belongs, which is a JavaScript value leaking '
                "into the response. The view is unusable. BUG-API-026, confirm with BE"
            )
        else:
            logger.info("CHECK groupByCategory returns usable rows → OK")

    assert not gaps, "Gaps on the portal catalogue reads:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid input refused, grouped view usable")
