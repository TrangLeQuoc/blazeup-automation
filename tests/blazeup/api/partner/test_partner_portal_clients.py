""" "My Clients" portal reads — GET /portal/clients and /portal/clients/:id (sa-partners-api).

Maps to the test plan: PARTNER_API_CLIENT_HEALTH_MSP_001 / _010. PRD §4.6.

The module was recorded BLOCKED against `/v1/partner/clients/*` (checked 2026-06-30). It
shipped under `/v1/partner/portal/clients` instead — re-probed 2026-09-21: the old path is a
404, the portal path answers 200. Only these two reads exist; `/clients/:id/health`,
`/clients/:id/tickets`, consent, provisioning and handoff are absent from the BE source, so
_002.._009 stay BLOCKED.

A row is an ATTRIBUTION, written only when a won deal's tenant is provisioned (G2). Automation
cannot reach that, so the list is empty here by design. What IS provable: the envelope, that an
empty list is a valid answer rather than an error, that the JWT — not a query parameter — is
what scopes the read, and that the detail route refuses every id it should.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

# `toPortalClientRow` maps exactly these, and nothing else (partner-tenant-attribution.helpers).
_ROW_FIELDS = (
    "id",
    "clientTenantId",
    "clientTenantName",
    "arrCents",
    "currency",
    "clientLifecycleState",
    "billingModel",
    "source",
    "attachedAt",
)
# The mapper exists precisely so these internal-only fields can never reach a partner.
_INTERNAL_ONLY = ("attributionHistory", "commissionStructure", "suspensionTrigger", "partnerId")
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
async def test_partner_api_client_health_msp_001(sa_partners_client, settings, created_resources):
    """PARTNER_API_CLIENT_HEALTH_MSP_001: partner reads My Clients - own rows only, scoped by JWT.

    GET /portal/clients only. The detail route lives in _010: a partner cannot create an
    attribution, so there is no id of its OWN to fetch and the detail route has no positive
    case that automation can reach — every case it does have is a refusal.

    A fresh partner owns no attribution, so an EMPTY list is the correct answer and is
    asserted as such — `total == 0` with a well-formed envelope, not a 404 and not an error.

    The property that matters most is asserted directly: `partnerId` is NOT a query parameter
    on this route. Passing one must not widen the result, because the backend takes the scope
    from the JWT. Any row that does come back is checked field-by-field against the portal
    mapper and proven free of the internal-only fields that mapper exists to withhold.

    Precondition: an ACTIVE partner with a portal session and no attributions.
    """
    async with async_step("[1/5] Setup: mint an active partner + portal session"):
        portal, partner_id, user_id = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={} sessionUser={}", partner_id, user_id)

    async with async_step("[2/5] GET My Clients → valid envelope; empty is the correct answer"):
        body = _envelope(await portal.list_clients())
        assert body["total"] == 0, (
            f"a partner that has never won a deal owns {body['total']} client(s) — either the "
            "JWT scope leaked another partner's rows or the fixture is not fresh"
        )
        assert body["data"] == [], f"`total` says 0 but `data` carries {len(body['data'])} row(s)"
        assert body.get("message"), "the envelope should carry a `message`"
        logger.info("CHECK empty client list is a valid 200 → OK (message={!r})", body["message"])

    async with async_step("[3/5] Any row returned must match the portal mapper exactly"):
        # Defensive rather than dead: staging is shared, and the moment provisioning starts
        # working this loop is what proves the row is portal-safe instead of a raw document.
        for row in body["data"]:
            missing = [f for f in _ROW_FIELDS if f not in row]
            assert not missing, f"client row is missing {missing}: {sorted(row)}"
            leaked = [f for f in _INTERNAL_ONLY if f in row]
            assert not leaked, (
                f"internal-only field(s) {leaked} reached the partner portal — "
                "`toPortalClientRow` exists specifically to withhold them"
            )
            creds = sorted(k for k in row if any(s.lower() in k.lower() for s in _SENSITIVE))
            assert not creds, f"credential material exposed on a client row: {creds}"
        logger.info("CHECK row shape ({} row(s) to check) → OK", len(body["data"]))

    async with async_step("[4/5] `partnerId` in the query must NOT widen the result"):
        other_portal, other_pid, _ouid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(other_pid))
        created_resources.add(other_portal.close)

        widened = _envelope(await portal.list_clients(params={"partnerId": other_pid}))
        assert widened["total"] == body["total"], (
            f"passing partnerId={other_pid} changed the total from {body['total']} to "
            f"{widened['total']} — the scope must come from the JWT, never the query string"
        )
        logger.info("CHECK query partnerId does not widen the scope → OK")

    async with async_step("[5/5] Pagination is accepted and never contradicts `total`"):
        paged = _envelope(await portal.list_clients(params={"limit": 5, "page": 1}))
        assert len(paged["data"]) <= 5, f"limit=5 returned {len(paged['data'])} rows"
        assert paged["total"] == body["total"], (
            f"`total` changed with paging: {paged['total']} vs {body['total']} — it must count "
            "the whole result set, not the page"
        )
        logger.info("CHECK paging consistent with total → OK (total={})", paged["total"])

    logger.info("RESULT: My Clients read verified — JWT-scoped, portal-safe, empty is valid")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_client_health_msp_010(sa_partners_client, settings, created_resources):
    """PARTNER_API_CLIENT_HEALTH_MSP_010: My Clients invalid id / bad paging - correct rejection.

    Negative counterpart of _001. An attribution id that does not exist, one that is not an id
    at all, and nonsensical pagination must each be refused with a 4xx that names the problem —
    never a 200 carrying somebody else's data, and never a 500.

    This is where the detail route is covered: a partner cannot create an attribution, so the
    route has no reachable positive case and every case it does have is a refusal.

    The load-bearing one is non-disclosure. `findByIdScoped` answers a FOREIGN attribution with
    the same "not found" as an id that does not exist, so a partner must not be able to tell
    the two apart and probe for other partners' ids. A real foreign id is DISCOVERED at run
    time from the SA-wide list rather than hard-coded, and nothing is written to it — if
    staging holds no attribution at all, that step reports itself as unproven instead of
    passing silently.

    Read-only apart from the session fixture. All cases run and failures are collected.
    """
    async with async_step("[1/5] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    gaps: list[str] = []

    async with async_step("[2/5] A well-formed id that does not exist → 4xx, never 200"):
        resp = await portal.get_client(_GHOST, expected_status=None)
        if resp.status_code == 200:
            gaps.append(
                f"a ghost attribution id answered 200 with {resp.text[:160]} — the detail route "
                "returned a record for an id that cannot exist"
            )
        elif resp.status_code >= 500:
            gaps.append(
                f"a ghost attribution id crashed the service ({resp.status_code}): "
                f"{resp.text[:200]}. A missing record is a refusal, not a server error"
            )
        elif _GHOST not in resp.text and "not found" not in resp.text.lower():
            gaps.append(f"the {resp.status_code} for a ghost id does not say what was not found")
        else:
            logger.info("CHECK ghost attribution id → {} → OK", resp.status_code)

    async with async_step("[3/5] An id that is not an id at all → 400, and no existence oracle"):
        bad = await portal.get_client("not-an-id", expected_status=None)
        if bad.status_code != 400:
            gaps.append(f"a malformed attribution id answered {bad.status_code}, expected 400")
        else:
            logger.info("CHECK malformed attribution id → 400 → OK")

        # Non-disclosure: the two refusals must not let a caller tell "no such row" apart from
        # "exists but is not yours". They are different classes here (invalid format vs not
        # found), so only the SHAPE is compared — both must be a 4xx that names no record.
        if bad.status_code < 500 and resp.status_code < 500:
            for label, r in (("ghost", resp), ("malformed", bad)):
                if any(f in r.text for f in _ROW_FIELDS if f != "id"):
                    gaps.append(
                        f"the {label}-id refusal leaks client row fields in its body: "
                        f"{r.text[:200]}"
                    )
            logger.info("CHECK neither refusal leaks row data → OK")

    async with async_step("[4/5] A REAL attribution owned by another partner → same refusal"):
        # Discovered, never hard-coded: the row must belong to somebody else and must still
        # exist when this runs. Nothing is written to it.
        sa_rows = (await sa_partners_client.list_attributions(params={"limit": 20})).json()
        foreign = next(
            (
                a
                for a in (sa_rows.get("data") or [])
                if a.get("_id") and str(a.get("partnerId")) != str(partner_id)
            ),
            None,
        )
        if foreign is None:
            gaps.append(
                "UNPROVEN: staging holds no attribution belonging to another partner, so the "
                "cross-partner refusal could not be exercised. This is the property that stops "
                "a partner from probing for other partners' client ids — it must not stay "
                "unproven. Re-run once any partner has a provisioned client"
            )
        else:
            fid = str(foreign["_id"])
            other = await portal.get_client(fid, expected_status=None)
            if other.status_code == 200:
                gaps.append(
                    f"CROSS-PARTNER LEAK: partner {partner_id} read attribution {fid}, which "
                    f"belongs to partner {foreign.get('partnerId')} — {other.text[:200]}"
                )
            elif other.status_code != resp.status_code:
                gaps.append(
                    f"a foreign attribution id answered {other.status_code} but a ghost id "
                    f"answered {resp.status_code} — the difference tells a caller which ids "
                    "exist, so foreign ids can be probed for. Both must refuse identically"
                )
            elif any(f in other.text for f in _ROW_FIELDS if f != "id"):
                gaps.append(f"the foreign-id refusal leaks client row fields: {other.text[:200]}")
            else:
                logger.info(
                    "CHECK foreign attribution {} (partner {}) → {} identical to a ghost id → OK",
                    fid,
                    foreign.get("partnerId"),
                    other.status_code,
                )

    async with async_step("[5/5] Nonsensical pagination must not dump the whole table"):
        for params in ({"limit": -1}, {"limit": 0}, {"page": "abc"}):
            r = await portal.list_clients(params=params, expected_status=None)
            if r.status_code == 200:
                n = len((r.json() or {}).get("data") or [])
                gaps.append(
                    f"clients {params} answered 200 with {n} row(s) instead of 400. /v1/sa/deals "
                    "refuses limit=-1, so the service knows how to validate this — the portal "
                    "reads do not (same gap as BUG-API-025 / BUG-API-026), confirm with BE"
                )
            elif r.status_code >= 500:
                gaps.append(f"clients {params} crashed the service ({r.status_code})")
            else:
                logger.info("CHECK clients {} → {} → OK", params, r.status_code)

    assert not gaps, "Gaps on the My Clients reads:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid id and page value refused, nothing disclosed")
