"""SA Security & Compliance — audit-trail governance (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_SECURITY_COMPLIANCE_*.

Every SA action must write a well-formed, correlated audit entry. These tests drive a
real SA action and assert the resulting ``GET /v1/sa/audit-logs`` entry. No new client
is needed — the SA action + audit read both live on ``sa_partners_client``.
"""

import asyncio
import re

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_partner
from utils.log_helper import async_step

# Keys that must never appear on an audit entry (no credential material in the trail).
_SENSITIVE = ("password", "token", "secret", "pwd", "credential")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_security_compliance_001(sa_partners_client, created_resources):
    """PARTNER_API_SECURITY_COMPLIANCE_001: SA action is audited - entry carries actor, action, reasoning, correlation ID.

    Every SA action must write a well-formed, correlated audit entry. This performs a
    reason-carrying SA action (a tier change with a reason) and asserts the resulting
    audit-log entry captures the four governance fields the requirement names — actor,
    action, reasoning, and a correlation ID — plus a resource reference back to the
    acted-on entity, and leaks no sensitive field.
    """
    async with async_step("Setup: create a partner (the SA action target)"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        code = partner.data.get("code")
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        reason = f"QA-AUTO SECURITY_COMPLIANCE_001 tier-change reason for {code}"
        logger.info("SETUP: partner {} created; will change tier with reason='{}'", code, reason)

    async with async_step("[1/3] Perform a reason-carrying SA action (change tier with a reason)"):
        resp = await sa_partners_client.change_tier(pid, tier="select", reason=reason)
        assert resp.status_code == 200, f"tier change must succeed, got {resp.status_code}"
        assert resp.data.get("tier") == "select", "tier must change to 'select'"
        logger.info("CHECK action → OK (tier changed to 'select')")

    async with async_step(
        "[2/3] The action wrote an audit entry (find it, retry for eventual consistency)"
    ):
        entry = None
        for attempt in range(1, 4):
            logs = await sa_partners_client.list_audit_logs(limit=50)
            entry = next(
                (
                    e
                    for e in logs.data
                    if "tier" in str(e.get("action", "")).lower() and pid in str(e)
                ),
                None,
            )
            if entry:
                break
            logger.info("audit entry not visible yet (attempt {}/3), retrying…", attempt)
            await asyncio.sleep(1)
        assert entry, "the SA action must write an audit-log entry referencing the partner"
        logger.info("CHECK audited → OK (action='{}')", entry.get("action"))

    async with async_step(
        "[3/3] Entry carries actor + action + reasoning + correlationId (+ resource, no leak)"
    ):
        actor = entry.get("actor")
        assert isinstance(actor, dict) and actor.get("type"), (
            "entry must record the actor (with a type)"
        )
        assert isinstance(entry.get("action"), str) and entry.get("action"), (
            "entry must record the action"
        )
        cid = entry.get("correlationId")
        assert isinstance(cid, str) and cid, "entry must carry a correlationId"
        assert _UUID_RE.match(cid), f"correlationId must be a UUID, got {cid!r}"
        after = entry.get("after") or {}
        assert after.get("reason") == reason, (
            f"entry must record the action reasoning, got after.reason={after.get('reason')!r}"
        )
        resource = entry.get("resource") or {}
        assert str(resource.get("id")) == str(pid), (
            "entry resource must reference the acted-on partner"
        )
        leaked = [k for k in entry if any(s in str(k).lower() for s in _SENSITIVE)]
        assert not leaked, f"audit entry must not expose sensitive keys: {leaked}"
        logger.info(
            "CHECK governance → OK (actor.type='{}', action='{}', correlationId set, "
            "reasoning captured, resource→partner, no leak)",
            actor.get("type"),
            entry.get("action"),
        )

    logger.info("RESULT: SA action audited with actor/action/reasoning/correlationId")


# Unnecessary / sensitive PII fields the deal-registration DTO does NOT define — a
# data-minimization control must not persist them.
_UNNECESSARY_PII = {
    "prospectSsn": "123-45-6789",
    "prospectDateOfBirth": "1990-01-01",
    "prospectNationalId": "NID-999888777",
    "prospectPassportNumber": "X1234567",
}


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_security_compliance_002(
    sa_partners_client, sa_deals_client, created_resources
):
    """PARTNER_API_SECURITY_COMPLIANCE_002: prospect data minimization - unnecessary PII is not persisted.

    Data-minimization control: registering a deal with extra, unnecessary PII fields
    that the CreateDealDto does not define (SSN, date of birth, national id, passport)
    must NOT persist them. The BE accepts the request (201) and strips the unknown
    fields (verified 2026-07-22) — the "not persisted" branch of the requirement
    ("unnecessary PII is rejected OR not persisted"). This test asserts none of the
    injected PII fields survive on the stored deal (in the create response AND a
    follow-up GET). No invalid-input negative counterpart (this security check IS the
    unwanted-input scenario; the happy-path register is DEAL_REGISTRATION_PIPELINE_001).
    Idempotency N/A (duplicate register is _022).
    """
    async with async_step("Setup: partner + plan + a deal payload carrying unnecessary PII"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        plan_id = await sa_deals_client.pick_billing_plan_id()
        payload = make_deal(pid, plan_id, dealType="referral", **_UNNECESSARY_PII)
        logger.info(
            "SETUP: partner {} + deal payload with unnecessary PII: {}",
            partner.data.get("code"),
            sorted(_UNNECESSARY_PII),
        )

    async with async_step("[1/3] Register the deal (with the unnecessary PII fields)"):
        resp = await sa_deals_client.register_deal(payload)
        deal_id = resp.deal_id
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert deal_id, "the deal must still be created (BE accepts + strips, not rejects)"
        logger.info("CHECK registered → OK (HTTP 201, id={})", deal_id)

    async with async_step("[2/3] The create response persists NONE of the unnecessary PII fields"):
        leaked = [k for k in _UNNECESSARY_PII if k in resp.data]
        assert not leaked, (
            f"data-minimization: unnecessary PII must not be persisted, but the deal kept {leaked}"
        )
        logger.info("CHECK response → OK (none of {} persisted)", sorted(_UNNECESSARY_PII))

    async with async_step("[3/3] A follow-up GET confirms the PII is not stored"):
        fetched = await sa_deals_client.get_deal(deal_id)
        leaked = [k for k in _UNNECESSARY_PII if k in fetched.data]
        assert not leaked, (
            f"data-minimization: fetched deal must not carry unnecessary PII, found {leaked}"
        )
        logger.info("CHECK persisted → OK (GET confirms no unnecessary PII stored)")

    logger.info(
        "RESULT: data minimization verified — {} unnecessary PII field(s) accepted but not persisted",
        len(_UNNECESSARY_PII),
    )
