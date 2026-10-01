"""SA partner update — PATCH /v1/sa/partners/:id (service: sa-partners-api).

Maps to the test plan: PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_023 / _024. PRD §8.5
(`PATCH /internal/partners/:id` in the requirement wording).

The endpoint every other partner TC depends on and none of them exercised: create, approve,
deactivate and change-tier were all covered, but the plain field update was not.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step

# UpdatePartnerDto, from the OpenAPI spec 2026-09-17. No field is required — a PATCH with an
# empty body is a legitimate no-op.
_TYPES = ("channel", "referral", "msp", "system_integrator")
_GHOST = "000000000000000000000000"

_SENSITIVE = ("password", "token", "secret", "credential")


def _data(resp) -> dict:
    body = resp.json()
    assert isinstance(body, dict) and "data" in body, f"unexpected envelope: {sorted(body)}"
    return body["data"]


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_023(sa_partners_client, seeded_partner):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_023: SA updates a partner - every field is stored.

    Sends every field UpdatePartnerDto accepts that can be asserted as a scalar, then reads
    the partner back to prove each one persisted rather than merely being echoed by the write
    response. Repeating the same PATCH must be idempotent — it is an update, not a create, so
    a second identical call must leave the record unchanged.

    Precondition: a partner exists (SA creates one inside this TC).
    """
    async with async_step("[1/5] Setup: SA creates a partner"):
        created = await seeded_partner()
        partner_id = created.partner_id
        assert partner_id, "precondition: the partner must be created"
        logger.info("SETUP: partner_id={}", partner_id)

    update = {
        "name": "QA-AUTO Updated Ltd",
        "legalName": "QA-AUTO Updated Legal Ltd",
        "website": "https://qa-auto-updated.example.com",
        "taxId": "QA-TAX-20260917",
        "internalNotes": "updated by PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_023",
        "type": "msp",
    }
    logger.info("SETUP: PATCH payload → {} field(s): {}", len(update), sorted(update))

    async with async_step("[2/5] PATCH the partner → 200 with the updated record"):
        patched = _data(await sa_partners_client.update_partner(partner_id, update))
        assert str(patched.get("_id")) == str(partner_id), "PATCH answered about another partner"
        logger.info("CHECK PATCH accepted → OK")

    async with async_step("[3/5] Read the partner back → every field persisted"):
        stored = _data(await sa_partners_client.raw_get_partner(partner_id, expected_status=200))
        for field, sent in update.items():
            assert stored.get(field) == sent, (
                f"{field} did not persist: sent {sent!r}, stored {stored.get(field)!r} "
                "— the write reported success it did not deliver"
            )
        assert stored.get("type") in _TYPES, f"type outside the enum: {stored.get('type')!r}"
        logger.info("CHECK all {} field(s) persisted after a follow-up GET → OK", len(update))

    async with async_step("[4/5] Verify the record is well-formed and leaks nothing"):
        for field in ("_id", "code", "email", "status", "tier"):
            assert field in stored, f"partner record is missing `{field}`: {sorted(stored)}"
        leaked = sorted(k for k in stored if any(s.lower() in k.lower() for s in _SENSITIVE))
        assert not leaked, f"credential material exposed on the partner record: {leaked}"
        logger.info("CHECK required fields present, no credential field → OK")

    async with async_step("[5/5] Repeat the same PATCH → idempotent, record unchanged"):
        again = _data(await sa_partners_client.update_partner(partner_id, update))
        for field, sent in update.items():
            assert again.get(field) == sent, (
                f"{field} changed on an identical repeat: {again.get(field)!r} != {sent!r}"
            )
        logger.info("CHECK repeat PATCH is idempotent → OK")

    logger.info("RESULT: partner update verified by read-back for {} field(s)", len(update))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_024(sa_partners_client, seeded_partner):
    """PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_024: SA partner update invalid - correct rejection.

    Negative counterpart of _023: a ghost id, a malformed id, an enum outside the spec, and an
    attempt to overwrite an identifier the DTO does not expose. An empty body is asserted as a
    legitimate no-op, not an error — UpdatePartnerDto declares no required field.

    All cases run and failures are collected. A ghost id is self-proving: this endpoint is the
    one that must report it.
    """
    async with async_step("[1/5] Setup: SA creates a partner"):
        partner_id = (await seeded_partner()).partner_id
        logger.info("SETUP: partner_id={}", partner_id)

    gaps: list[str] = []

    async with async_step("[2/5] Ghost and malformed id → must be refused"):
        for label, bad in (("ghost", _GHOST), ("malformed", "not-an-id")):
            resp = await sa_partners_client.update_partner(
                bad, {"name": "QA-AUTO nope"}, expected_status=None
            )
            if resp.status_code < 400:
                gaps.append(f"{label} id accepted with HTTP {resp.status_code}")
            else:
                logger.info("CHECK {} id → {} → OK", label, resp.status_code)

    async with async_step("[3/5] Enum outside the spec → 400 naming the allowed values"):
        resp = await sa_partners_client.update_partner(
            partner_id, {"type": "wizard"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"type='wizard' answered {resp.status_code}, expected 400")
        elif missing := [t for t in _TYPES if t not in resp.text]:
            gaps.append(f"the 400 for a bad type does not list {missing}")
        else:
            logger.info("CHECK invalid type → 400 listing every allowed value → OK")

    async with async_step("[4/5] An empty body is a no-op, not an error"):
        before = _data(await sa_partners_client.raw_get_partner(partner_id, expected_status=200))
        resp = await sa_partners_client.update_partner(partner_id, {}, expected_status=None)
        if resp.status_code >= 400:
            gaps.append(
                f"an empty PATCH was refused with {resp.status_code}; UpdatePartnerDto "
                "declares no required field, so it should be a no-op — confirm with BE"
            )
        else:
            after = _data(await sa_partners_client.raw_get_partner(partner_id, expected_status=200))
            if after.get("name") != before.get("name"):
                gaps.append("an empty PATCH changed the record")
            else:
                logger.info("CHECK empty body → no-op → OK")

    async with async_step("[5/5] A field the DTO does not expose must not be writable"):
        # One field at a time, so the report names the one that breaks rather than "the
        # payload". Sent together they returned 500 — see the 5xx branch below.
        for field, attempted in (("_id", _GHOST), ("code", "QA-HACKED"), ("status", "active")):
            resp = await sa_partners_client.update_partner(
                partner_id, {field: attempted}, expected_status=None
            )
            if resp.status_code >= 500:
                gaps.append(
                    f"PATCH with an undeclared field `{field}` answered HTTP "
                    f"{resp.status_code} — a field the DTO does not expose must be ignored or "
                    "refused with a 4xx, never crash the handler — and the body must not leak "
                    f"the storage engine's own error. Body: {resp.text[:150]}. "
                    "BUG-API-024, confirm with BE"
                )
            elif resp.status_code < 400:
                after = _data(
                    await sa_partners_client.raw_get_partner(partner_id, expected_status=200)
                )
                if str(after.get(field)) == attempted:
                    gaps.append(
                        f"`{field}` was overwritten through PATCH although UpdatePartnerDto "
                        "does not expose it. `status` in particular bypasses the approval FSM "
                        "(PRD §12.1 B3: SA Review -> Legal Countersign -> SA Final Approval) by "
                        "moving a PENDING partner straight to active without the approve "
                        "endpoint. BUG-API-024, confirm with BE"
                    )
                else:
                    logger.info("CHECK undeclared `{}` ignored → OK", field)
            else:
                logger.info("CHECK undeclared `{}` → {} → OK", field, resp.status_code)

    assert not gaps, "Gaps on PATCH /v1/sa/partners/{id}:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid update refused, identifiers not writable")
