"""SA remediation: link a provisioned tenant to a stuck WON deal (service: sa-partners-api).

Maps to the test plan: PARTNER_API_DEAL_REGISTRATION_PIPELINE_037. PRD §7.5.

NEGATIVE ONLY, and deliberately so. `POST /v1/sa/deals/:id/link-tenant` exists to rescue a deal
whose tenant never came back from `ms-sa-tenants`, and its success path cannot be reached by
automation:

* Guard 3 calls `tenantExists()` against the real tenants collection, so a fabricated tenantId
  is always a 400 — there is no way to invent an acceptable one.
* Guard 7 allows a tenant to back only ONE won deal, so even a real tenant borrowed from
  staging would be consumed once and would corrupt an existing attribution.

So there is no positive counterpart to pair with (cf. rule 1): every case this route has is a
refusal, and each one is a guard that protects commission attribution. A deal wrongly linked to
the wrong tenant pays the wrong partner.

Every case runs against a deal this TC created itself, and nothing is ever successfully linked.
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_prospect
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

# NotEquals(PLATFORM_TENANT_ID) on the DTO — the platform's own tenant must never be linked.
_PLATFORM_TENANT = "blazeup-platform"
_GHOST_TENANT = "qa-auto-no-such-tenant"
_GHOST_DEAL = "000000000000000000000000"
_REASON = "QA-AUTO negative probe for the link-tenant guards; nothing is linked."


def _body(**overrides) -> dict:
    """A payload that is valid in SHAPE, so each case fails on the guard it targets."""
    payload = {
        "tenantId": _GHOST_TENANT,
        "goLiveAt": "2026-09-20T00:00:00.000Z",
        "reason": _REASON,
    }
    payload.update(overrides)
    return payload


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_deal_registration_pipeline_037(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_DEAL_REGISTRATION_PIPELINE_037: link-tenant guards - every invalid link refused.

    Walks the guards in the order the service applies them, each with a payload that is valid in
    every other respect so the refusal can only come from the guard under test: a deal that is
    not WON, a tenant that does not exist, the platform's own tenant, a `goLiveAt` outside its
    bounds, a `reason` below the minimum length, and a deal id that is not a deal.

    There is no positive case: a successful link needs a real, unclaimed, provisioned tenant,
    which automation cannot create (Guard 3) and must not borrow (Guard 7).

    Precondition: one partner with a REGISTERED deal (for the wrong-state case) and one with a
    WON deal (for the guards past it). All cases run and failures are collected.
    """
    async with async_step("[1/7] Setup: a registered deal and a won deal"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        plan_id = await sa_deals_client.pick_billing_plan_id()
        registered = (
            await portal.register_deal(make_deal(None, plan_id, **make_prospect()))
        ).json()
        registered_id = (registered.get("data") or {}).get("_id")
        assert registered_id, "precondition: the partner must be able to register a deal"

        won = (await portal.register_deal(make_deal(None, plan_id, **make_prospect()))).json()
        won_id = (won.get("data") or {}).get("_id")
        assert won_id, "precondition: a second deal is needed to drive to WON"
        await sa_deals_client.approve_deal(won_id, plan_id=plan_id)
        win_result = await sa_deals_client.win_deal(
            won_id,
            win_intake={
                "companyWebsite": "https://qa-auto-link-tenant.example.com",
                "industry": "Technology",
                "adminFirstName": "QA",
                "adminLastName": "LinkTenant",
                "adminEmail": "qa.auto+linktenant@mailinator.com",
                "companyName": "QA-AUTO LinkTenant Co",
                "tenantDomain": f"qa-auto-link-{won_id[-6:]}.example.com",
                "planId": plan_id,
                "billingCycle": "annual",
                "numberOfEmployee": 10,
                "region": "asia-southeast1",
                "country": "US",
                "actualAcvCents": 1_000_000,
            },
        )
        assert win_result.data.get("status") == "won", "precondition: the deal must reach WON"
        closed_at = win_result.data.get("closedAt")
        logger.info(
            "SETUP: partner={} registered={} won={} closedAt={}",
            partner_id,
            registered_id,
            won_id,
            closed_at,
        )

    gaps: list[str] = []

    async with async_step("[2/7] Guard 2: a deal that is not WON cannot be linked", soft=gaps):
        resp = await sa_deals_client.link_tenant(registered_id, _body(), expected_status=None)
        if resp.status_code < 400:
            gaps.append(
                f"linking a REGISTERED deal answered {resp.status_code} — only a won deal has a "
                "tenant to link, so this would attribute a client to a deal that never closed"
            )
        elif resp.status_code >= 500:
            gaps.append(f"linking a registered deal crashed the service ({resp.status_code})")
        else:
            logger.info("CHECK non-WON deal → {} → OK", resp.status_code)

    async with async_step("[3/7] Guard 3: a tenant that does not exist is refused", soft=gaps):
        resp = await sa_deals_client.link_tenant(won_id, _body(), expected_status=None)
        if resp.status_code < 400:
            gaps.append(
                f"a fabricated tenantId ({_GHOST_TENANT!r}) was ACCEPTED with "
                f"{resp.status_code} — the deal now points at a tenant that does not exist and "
                "its commission is attributed to nothing"
            )
        elif resp.status_code >= 500:
            gaps.append(f"a ghost tenantId crashed the service ({resp.status_code})")
        elif "not exist" not in resp.text.lower() and _GHOST_TENANT not in resp.text:
            gaps.append(
                f"the {resp.status_code} does not say the tenant is unknown: {resp.text[:160]}"
            )
        else:
            logger.info("CHECK ghost tenantId → {} → OK", resp.status_code)

    async with async_step(
        "[4/7] DTO: the platform tenant and a too-short reason are refused", soft=gaps
    ):
        resp = await sa_deals_client.link_tenant(
            won_id, _body(tenantId=_PLATFORM_TENANT), expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(
                f"tenantId={_PLATFORM_TENANT!r} answered {resp.status_code}, expected 400. The "
                "DTO carries @NotEquals(PLATFORM_TENANT_ID): linking the platform's own tenant "
                "to a partner deal would attribute BlazeUp itself as a partner's client"
            )
        else:
            logger.info("CHECK platform tenantId → 400 → OK")

        resp = await sa_deals_client.link_tenant(
            won_id, _body(reason="too short"), expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(
                f"a 9-character reason answered {resp.status_code}, expected 400 — the DTO "
                "requires 10-500 chars so a remediation always carries an auditable why"
            )
        else:
            logger.info("CHECK reason below the minimum length → 400 → OK")

    async with async_step("[5/7] Guard 6: goLiveAt must sit between closedAt and now", soft=gaps):
        for label, value in (
            ("in the future", "2099-01-01T00:00:00.000Z"),
            ("before closedAt", "2020-01-01T00:00:00.000Z"),
            ("not a date", "yesterday"),
        ):
            resp = await sa_deals_client.link_tenant(
                won_id, _body(goLiveAt=value), expected_status=None
            )
            if resp.status_code != 400:
                gaps.append(
                    f"goLiveAt {label} ({value}) answered {resp.status_code}, expected 400. "
                    "goLiveAt is the commission-eligibility anchor, so an out-of-bounds value "
                    "moves when the partner starts earning"
                )
            else:
                logger.info("CHECK goLiveAt {} → 400 → OK", label)

    async with async_step("[6/7] A deal id that is not a deal", soft=gaps):
        for label, deal_id in (("ghost", _GHOST_DEAL), ("malformed", "not-an-id")):
            resp = await sa_deals_client.link_tenant(deal_id, _body(), expected_status=None)
            if resp.status_code < 400:
                gaps.append(f"a {label} deal id answered {resp.status_code}, expected 4xx")
            elif resp.status_code >= 500:
                gaps.append(f"a {label} deal id crashed the service ({resp.status_code})")
            else:
                logger.info("CHECK {} deal id → {} → OK", label, resp.status_code)

    async with async_step("[7/7] Nothing was linked by any of the refused calls", soft=gaps):
        deal = (await sa_deals_client.get_deal(won_id)).data
        assert not deal.get("wonTenantId"), (
            f"the deal carries wonTenantId={deal.get('wonTenantId')!r} after only refused link "
            "attempts — one of them wrote despite answering an error"
        )
        assert deal.get("provisioningState") == "awaited", (
            f"provisioningState moved to {deal.get('provisioningState')!r}; a refused link must "
            "leave the deal exactly as it found it"
        )
        logger.info("CHECK deal untouched — no wonTenantId, still `awaited` → OK")

    assert not gaps, "Gaps on POST /v1/sa/deals/:id/link-tenant:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every link-tenant guard refuses correctly and writes nothing")
