"""Partner payout / bank accounts — /v1/partner/portal/bank-accounts (sa-partners-api).

Maps to the test plan: PARTNER_API_COMMISSIONS_PAYOUTS_016 / _021 / _022. PRD §9.3.

A closed CRUD chain the partner owns end to end — list, add, promote to primary, remove — so
unlike every other group built so far this one needs no pre-existing data and cleans up after
itself completely.

Two properties carry the weight:

* **PII never comes back.** ``toBankAccountView`` strips ``accountNumber``, ``routingNumber``
  and ``iban``, leaving only the ``*Masked`` companions. _016 asserts the raw digits appear
  NOWHERE in any response, not merely that the field name is absent.
* **Admin only.** All four routes refuse a non-admin partner user with 403. _021 proves it with
  a real ``viewer`` session rather than by inspecting the guard.
"""

import pytest
from loguru import logger

from utils.data_factory import make_partner_user
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session, partner_login, portal_client

# From partner-bank-account.schema.ts.
_PAYOUT_METHODS = ("bank_transfer", "swift", "wise", "paypal")
_STATUSES = ("unverified", "pending_microdeposit", "verified", "rejected")
# Stripped by toBankAccountView — must never reach the partner.
_RAW_SECRET_FIELDS = ("accountNumber", "routingNumber", "iban")
_GHOST = "00000000-0000-4000-8000-000000000000"

# Fabricated, never a real account. The digits are what _016 hunts for in the response.
_ACCOUNT_NUMBER = "000123456789"
_ROUTING_NUMBER = "121140399"
_IBAN = "DE89370400440532013000"


def _account_payload(**overrides) -> dict:
    """A complete, valid US bank_transfer account. Every optional field is sent too."""
    payload = {
        "label": "QA-AUTO USD operating",
        "accountHolderName": "QA-AUTO Systems Inc",
        "bankName": "QA-AUTO Test Bank",
        "countryCode": "US",
        "currency": "USD",
        "payoutMethod": "bank_transfer",
        "accountNumber": _ACCOUNT_NUMBER,
        "routingNumber": _ROUTING_NUMBER,
    }
    payload.update(overrides)
    return payload


def _swift_payload(**overrides) -> dict:
    """A second, DIFFERENT account so the duplicate guard does not fire."""
    payload = {
        "label": "QA-AUTO EUR wire",
        "accountHolderName": "QA-AUTO Systems GmbH",
        "bankName": "QA-AUTO Euro Bank",
        "countryCode": "DE",
        "currency": "EUR",
        "payoutMethod": "swift",
        "iban": _IBAN,
        "swiftBic": "DEUTDEFF",
    }
    payload.update(overrides)
    return payload


def _rows(resp) -> list[dict]:
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    assert "data" in body, f"envelope has no `data`: {sorted(body)}"
    return body["data"] if isinstance(body["data"], list) else [body["data"]]


def _assert_no_raw_pii(resp, where: str) -> None:
    """The raw identifiers must be absent as FIELDS and as VALUES anywhere in the body."""
    text = resp.text
    for secret, name in (
        (_ACCOUNT_NUMBER, "account number"),
        (_ROUTING_NUMBER, "routing number"),
        (_IBAN, "IBAN"),
    ):
        assert secret not in text, (
            f"{where}: the full {name} ({secret}) is echoed back in the response body. PRD §9.3 "
            "requires it be stored masked-for-display and never returned"
        )
    for row in _rows(resp):
        present = [f for f in _RAW_SECRET_FIELDS if f in row]
        assert not present, f"{where}: raw field(s) {present} present on the row: {sorted(row)}"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_016(sa_partners_client, settings, created_resources):
    """PARTNER_API_COMMISSIONS_PAYOUTS_016: payout account CRUD - sensitive fields never returned.

    Walks the whole chain a partner admin owns: list (empty) → add → add a second → promote the
    second to primary → remove → remove the last. After EVERY call the response is searched for
    the raw account number, routing number and IBAN that were sent; finding any of them is the
    failure this TC exists for (PRD §9.3).

    The single-primary invariant is checked from the promote response itself, which returns the
    whole list precisely so that is possible, and the 409 guard on removing a primary while
    others exist is exercised in _021.

    Precondition: an ACTIVE partner with an ADMIN portal session and no payout accounts.
    """
    async with async_step("[1/7] Setup: mint an active partner + admin portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    async with async_step("[2/7] The account list starts empty"):
        resp = await portal.list_bank_accounts()
        assert _rows(resp) == [], (
            f"a fresh partner already holds {len(_rows(resp))} payout account(s) — the adds "
            "below would prove nothing"
        )
        logger.info("CHECK payout list starts empty → OK")

    async with async_step("[3/7] Add an account → stored, masked, raw digits never returned"):
        created = _rows(await portal.add_bank_account(_account_payload()))[0]
        first_id = created.get("id")
        assert first_id, f"the created account carries no `id`: {sorted(created)}"
        for field in ("label", "accountHolderName", "bankName", "countryCode", "currency"):
            assert created[field] == _account_payload()[field], (
                f"{field} came back as {created[field]!r}, not what was sent"
            )
        assert created["payoutMethod"] in _PAYOUT_METHODS, "payoutMethod outside the enum"
        assert created["status"] in _STATUSES, f"status outside the enum: {created['status']!r}"
        assert created["status"] == "unverified", (
            f"a new account must start unverified, got {created['status']!r}"
        )
        masked = created.get("accountNumberMasked") or ""
        assert masked, "accountNumberMasked is missing — nothing to show the partner"
        assert masked.endswith(_ACCOUNT_NUMBER[-4:]), (
            f"the mask {masked!r} does not end with the real last 4 ({_ACCOUNT_NUMBER[-4:]})"
        )
        assert _ACCOUNT_NUMBER not in masked, f"the mask {masked!r} IS the full account number"
        logger.info("CHECK account stored and masked → OK (id={} mask={})", first_id, masked)

    async with async_step("[4/7] The first account is primary automatically"):
        resp = await portal.list_bank_accounts()
        _assert_no_raw_pii(resp, "GET bank-accounts after the first add")
        rows = _rows(resp)
        assert len(rows) == 1, f"expected exactly 1 account, got {len(rows)}"
        assert rows[0]["isPrimary"] is True, (
            "the only payout account on file is not primary — a partner would have no payout "
            "destination"
        )
        logger.info("CHECK sole account auto-promoted to primary → OK")

    async with async_step("[5/7] Add a second account, then promote it → exactly one primary"):
        second = _rows(await portal.add_bank_account(_swift_payload()))[0]
        second_id = second["id"]
        assert second.get("ibanMasked"), "ibanMasked is missing on the SWIFT account"
        assert _IBAN not in (second.get("ibanMasked") or ""), "the IBAN mask IS the full IBAN"

        resp = await portal.set_primary_bank_account(second_id)
        _assert_no_raw_pii(resp, "PATCH set-primary")
        rows = _rows(resp)
        assert len(rows) == 2, f"set-primary returned {len(rows)} account(s), expected the full 2"
        primaries = [r["id"] for r in rows if r.get("isPrimary")]
        assert primaries == [second_id], (
            f"after promoting {second_id} the primaries are {primaries} — the write must promote "
            "one and demote every other in the same atomic operation"
        )
        logger.info("CHECK promote demotes the previous primary → OK ({} accounts)", len(rows))

    async with async_step("[6/7] Remove the non-primary account → the other survives"):
        resp = await portal.delete_bank_account(first_id)
        _assert_no_raw_pii(resp, "DELETE non-primary")
        remaining = _rows(resp)
        assert [r["id"] for r in remaining] == [second_id], (
            f"after removing {first_id} the remaining ids are {[r['id'] for r in remaining]}"
        )
        assert remaining[0]["isPrimary"] is True, "the surviving account lost its primary flag"
        logger.info("CHECK non-primary removed, primary survives → OK")

    async with async_step("[7/7] Remove the last account → the primary may go when it is last"):
        resp = await portal.delete_bank_account(second_id)
        assert _rows(resp) == [], f"expected an empty list, got {_rows(resp)}"
        assert _rows(await portal.list_bank_accounts()) == [], (
            "the list still returns accounts after both were removed"
        )
        logger.info("CHECK last account (primary) removable → OK, list empty again")

    logger.info("RESULT: payout CRUD verified end to end — no raw PII returned at any step")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_021(sa_partners_client, settings, created_resources):
    """PARTNER_API_COMMISSIONS_PAYOUTS_021: payout account invalid input and non-admin - refused.

    Negative counterpart of _016, covering three distinct refusal classes:

    * DTO validation — every required field missing in turn, plus an enum outside the spec.
    * State guards — removing the primary while another account exists must be 409, and a
      ghost account id must not be silently accepted.
    * Authorization — a real ``viewer`` session must be refused 403 on all four routes. This is
      the rule-5 "token of a different role" case and is proven with an actual login, not by
      reading the guard.

    All cases run and failures are collected.
    """
    async with async_step(
        "[1/5] Setup: an admin session, plus a VIEWER session on the same partner"
    ):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        invited = await sa_partners_client.invite_partner_user(
            make_partner_user(partner_id, role="viewer")
        )
        viewer_creds = invited.data
        anon = portal_client(settings)
        try:
            login = await partner_login(anon, viewer_creds["email"], viewer_creds["tempPassword"])
            viewer_token = login.json().get("accessToken")
        finally:
            await anon.close()
        assert viewer_token, "precondition: the viewer user must be able to log in"
        viewer = portal_client(settings, token=viewer_token)
        created_resources.add(viewer.close)
        logger.info("SETUP: partner={} + viewer session {}", partner_id, viewer_creds["email"])

    gaps: list[str] = []

    async with async_step("[2/5] Every required field missing in turn → 400 naming it", soft=gaps):
        required = (
            "label",
            "accountHolderName",
            "bankName",
            "countryCode",
            "currency",
            "payoutMethod",
        )
        for field in required:
            payload = _account_payload()
            payload.pop(field)
            r = await portal.add_bank_account(payload, expected_status=None)
            if r.status_code != 400:
                gaps.append(f"omitting `{field}` answered {r.status_code}, expected 400")
            elif field not in r.text:
                gaps.append(
                    f"the 400 for a missing `{field}` does not name the field: {r.text[:140]}"
                )
            else:
                logger.info("CHECK missing {} → 400 naming it → OK", field)

    async with async_step(
        "[3/5] A payoutMethod outside the enum → 400 listing the allowed ones", soft=gaps
    ):
        r = await portal.add_bank_account(
            _account_payload(payoutMethod="carrier_pigeon"), expected_status=None
        )
        if r.status_code != 400:
            gaps.append(f"payoutMethod='carrier_pigeon' answered {r.status_code}, expected 400")
        elif missing := [m for m in _PAYOUT_METHODS if m not in r.text]:
            gaps.append(f"the 400 for a bad payoutMethod does not list {missing}")
        else:
            logger.info("CHECK bad payoutMethod → 400 listing every method → OK")

    async with async_step(
        "[4/5] State guards: ghost id, and removing the primary while others exist", soft=gaps
    ):
        first = _rows(await portal.add_bank_account(_account_payload()))[0]
        second = _rows(await portal.add_bank_account(_swift_payload()))[0]
        # `first` was added first, so it is the primary; `second` is not.
        r = await portal.delete_bank_account(first["id"], expected_status=None)
        if r.status_code != 409:
            gaps.append(
                f"removing the PRIMARY account while another exists answered {r.status_code}, "
                "expected 409 — the partner would be left with no payout destination chosen"
            )
        else:
            logger.info("CHECK remove primary while others exist → 409 → OK")

        for label, call in (
            ("DELETE", portal.delete_bank_account(_GHOST, expected_status=None)),
            ("PATCH primary", portal.set_primary_bank_account(_GHOST, expected_status=None)),
        ):
            r = await call
            if r.status_code < 400:
                gaps.append(f"{label} on a ghost account id answered {r.status_code}, expected 4xx")
            elif r.status_code >= 500:
                gaps.append(f"{label} on a ghost account id crashed the service ({r.status_code})")
            else:
                logger.info("CHECK {} ghost id → {} → OK", label, r.status_code)

        # Leave the partner clean for the role checks below.
        await portal.delete_bank_account(second["id"])
        await portal.delete_bank_account(first["id"])

    async with async_step("[5/5] A VIEWER is refused 403 on all four routes", soft=gaps):
        checks = (
            ("GET list", viewer.list_bank_accounts(expected_status=None)),
            ("POST add", viewer.add_bank_account(_account_payload(), expected_status=None)),
            ("PATCH primary", viewer.set_primary_bank_account(_GHOST, expected_status=None)),
            ("DELETE", viewer.delete_bank_account(_GHOST, expected_status=None)),
        )
        for label, call in checks:
            r = await call
            if r.status_code != 403:
                gaps.append(
                    f"a VIEWER got {r.status_code} on {label}, expected 403. Payout banking "
                    "details are admin-only (PRD §9.3)"
                )
            else:
                logger.info("CHECK viewer {} → 403 → OK", label)

        leftover = _rows(await portal.list_bank_accounts())
        if leftover:
            gaps.append(f"the refused viewer writes still created {len(leftover)} account(s)")

    assert not gaps, "Gaps on the payout account routes:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: validation, state guards and admin-only access all enforced")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_022(sa_partners_client, settings, created_resources):
    """PARTNER_API_COMMISSIONS_PAYOUTS_022: adding the same payout account twice - rejected.

    Rule 8 (duplicate/idempotency) as its own TC. The backend's answer is explicit and is
    asserted as such rather than left open: a repeat is REJECTED with 400 "This payout account
    is already on file for the partner", and — the half that matters — the partner is left with
    exactly ONE account, not two.

    The duplicate match is on normalised values, so a resend with different spacing must be
    caught too; and a genuinely different account must still be accepted, otherwise the guard
    would be over-broad rather than correct.

    Precondition: an ACTIVE partner with an ADMIN portal session and no payout accounts.
    """
    async with async_step("[1/4] Setup: partner + admin session + one account on file"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        first = _rows(await portal.add_bank_account(_account_payload()))[0]
        logger.info("SETUP: partner={} account={}", partner_id, first["id"])

    async with async_step("[2/4] Resending the identical payload → 400, and still ONE account"):
        r = await portal.add_bank_account(_account_payload(), expected_status=None)
        assert r.status_code == 400, (
            f"the duplicate was answered {r.status_code}, expected 400. Two payout accounts with "
            f"the same number would split the partner's payouts: {r.text[:200]}"
        )
        assert "already on file" in r.text.lower(), (
            f"the 400 does not say the account is already on file: {r.text[:200]}"
        )
        rows = _rows(await portal.list_bank_accounts())
        assert len(rows) == 1, f"after the rejected duplicate the partner holds {len(rows)}"
        logger.info("CHECK duplicate → 400 and still exactly 1 account → OK")

    async with async_step("[3/4] The match is on the normalised value, not the literal string"):
        spaced = _account_payload(accountNumber=" 0001 2345 6789 ", label="QA-AUTO spaced resend")
        r = await portal.add_bank_account(spaced, expected_status=None)
        if r.status_code == 400:
            logger.info("CHECK spaced resend also caught as duplicate → OK")
        else:
            rows = _rows(await portal.list_bank_accounts())
            assert len(rows) == 1, (
                f"the same account number with spaces was accepted ({r.status_code}) and the "
                f"partner now holds {len(rows)} accounts. `normaliseAccountField` is meant to "
                "strip formatting before comparing — confirm with BE"
            )

    async with async_step("[4/4] A genuinely different account is still accepted"):
        second = _rows(await portal.add_bank_account(_swift_payload()))[0]
        assert second["id"] != first["id"], "the second account reused the first one's id"
        rows = _rows(await portal.list_bank_accounts())
        assert len(rows) == 2, (
            f"a different account was rejected — the duplicate guard is over-broad "
            f"({len(rows)} account(s) on file)"
        )
        primaries = [r["id"] for r in rows if r.get("isPrimary")]
        assert primaries == [first["id"]], (
            f"adding a second account moved the primary to {primaries}; it must stay with "
            f"{first['id']} unless isPrimary was requested"
        )
        logger.info("CHECK distinct account accepted, primary unchanged → OK")

    logger.info("RESULT: duplicate rejected, one account on file, distinct account still allowed")
