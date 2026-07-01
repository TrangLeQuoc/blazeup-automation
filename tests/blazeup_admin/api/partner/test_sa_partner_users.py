"""SA Partner Users API — SA-side partner-portal user management (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_PARTNER_USERS_*.

``GET /sa-partners-api/v1/sa/partner-users`` lists portal users (envelope
``{statusCode, data[], total, message}``), optionally filtered by ``partnerId``.
No billing plan involved, so no sa-plans dependency.
"""

import pytest
from loguru import logger

from utils.data_factory import make_partner, make_partner_user, unique_email
from utils.log_helper import async_step

# A user must never expose credential material in the SA list (the invite response
# carries tempPassword for hand-off, but the list must not).
_SENSITIVE = ("password", "token", "secret", "pwd", "credential")

# A syntactically valid Mongo ObjectId that does not exist — for ghost-FK tests.
_GHOST_ID = "000000000000000000000000"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_001(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_USERS_001: SA lists portal users for a partner - users with roles, no secret leak.

    Contract on ``GET /sa-partners-api/v1/sa/partner-users?partnerId=``: returns HTTP
    200 with the envelope ``{statusCode, data[], total, message}``; the invited user
    appears carrying role + status; the list is scoped to the partner; and no
    sensitive field (password/tempPassword) is exposed.
    """
    async with async_step("Setup: create a partner + invite a portal user"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        uid = invited.data.get("userId")
        assert uid, "precondition: partner user must be invited"
        logger.info("SETUP: partner {} + user {}", partner.data.get("code"), uid)

    async with async_step("[1/3] GET partner-users filtered by partnerId"):
        resp = await sa_partners_client.list_partner_users(partner_id=pid, limit=20)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert isinstance(resp.data, list), "`data` must be a list"
        assert resp.message, "`message` should be present"
        logger.info("CHECK envelope → OK (total={}, returned={})", resp.total, len(resp.data))

    async with async_step(
        "[2/3] Invited user appears with role + status; list scoped to the partner"
    ):
        users = resp.data
        mine = next((u for u in users if (u.get("userId") or u.get("id")) == uid), None)
        assert mine, "invited user must appear in the partner's user list"
        assert isinstance(mine.get("role"), str) and mine.get("role"), "user must carry a role"
        assert isinstance(mine.get("status"), str) and mine.get("status"), (
            "user must carry a status"
        )
        assert mine.get("email"), "user must carry an email"
        assert all(str(u.get("partnerId")) == str(pid) for u in users), (
            "list must be scoped to the requested partner"
        )
        logger.info(
            "CHECK user → OK (role='{}', status='{}', scoped to partner)",
            mine.get("role"),
            mine.get("status"),
        )

    async with async_step("[3/3] No sensitive field is leaked (password/tempPassword)"):
        for u in users:
            leaked = [k for k in u if any(s in str(k).lower() for s in _SENSITIVE)]
            assert not leaked, f"partner-user list must not expose sensitive keys: {leaked}"
        logger.info("CHECK no-leak → OK (no password/tempPassword in the list)")

    logger.info(
        "RESULT: partner {} user list verified ({} user(s))",
        partner.data.get("code"),
        len(users),
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_011(sa_partners_client):
    """PARTNER_API_PARTNER_USERS_011: list partner-users invalid pagination/filter - graceful, never 5xx.

    Negative counterpart of _001. The server must NEVER 5xx on bad input. Validated
    cases are rejected with 4xx; a ghost (valid-but-nonexistent) partnerId returns
    200 empty.

    Observation (weak validation, confirm with BE): unlike the audit-log list,
    ``limit=0`` / non-numeric ``page`` / unknown ``sort`` are silently defaulted
    (HTTP 200) instead of rejected — logged here, not failed (they don't 5xx).
    """
    # Validated → must be 4xx (and never 5xx).
    robustness = [
        ("page=0", {"page": 0, "limit": 5}, "non-negative"),
        ("page=-1", {"page": -1, "limit": 5}, "non-negative"),
        ("limit over max", {"limit": 999999}, "must not exceed 100"),
        ("malformed partnerId", {"partnerId": "not-an-id", "limit": 5}, "mongodb id"),
    ]
    # Currently lenient (defaulted, 200) — observed, not asserted as 4xx.
    observations = [
        ("limit=0", {"limit": 0}),
        ("page non-numeric", {"page": "abc", "limit": 5}),
        ("unknown sort", {"limit": 5, "sort": "bogus"}),
    ]
    n_steps = len(robustness) + 2
    gaps: list[str] = []

    for idx, (label, params, hint) in enumerate(robustness, start=1):
        async with async_step(f"[{idx}/{n_steps}] Reject invalid: {label}"):
            r = await sa_partners_client.raw_list_partner_users(expected_status=None, **params)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    async with async_step(
        f"[{len(robustness) + 1}/{n_steps}] Ghost partnerId → 200 empty (graceful)"
    ):
        r = await sa_partners_client.raw_list_partner_users(
            partnerId="000000000000000000000000", limit=5
        )
        if r.status_code == 200 and len(r.json().get("data") or []) == 0:
            logger.info("CHECK ghost partnerId → OK (200 empty)")
        else:
            gaps.append(f"ghost partnerId: status={r.status_code}")
            logger.error("CHECK ghost partnerId → FAIL ({})", r.status_code)

    async with async_step(f"[{n_steps}/{n_steps}] Lenient-default params must still not 5xx"):
        for label, params in observations:
            r = await sa_partners_client.raw_list_partner_users(expected_status=None, **params)
            assert r.status_code < 500, f"{label} must not 5xx, got {r.status_code}"
            logger.info(
                "OBSERVE {} → status {} (lenient default, not rejected)", label, r.status_code
            )

    assert not gaps, "partner-users list negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info(
        "RESULT: invalid pagination/filter handled gracefully (4xx where validated, never 5xx)"
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_002(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_USERS_002: SA invites a partner-portal user - user created with role + hand-off credential.

    Contract on ``POST /sa-partners-api/v1/sa/partner-users``: a valid invite
    (partnerId + email + firstName + lastName + role) returns HTTP 201, persists the
    user with a server-assigned userId, echoes the submitted fields, and the user is
    retrievable in the partner's list.

    Note (TC↔BE): the plan describes an "email sent + PENDING user" model, but the BE
    creates an ACTIVE user and returns a ``tempPassword`` for SA hand-off — a
    different onboarding model. This test asserts the BE's actual contract; confirm
    with BE which model is intended.
    """
    async with async_step("Setup: create a partner"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        payload = make_partner_user(pid, role="sales")
        logger.info(
            "SETUP: partner {}; invite email='{}' role='{}'",
            partner.data.get("code"),
            payload["email"],
            payload["role"],
        )

    async with async_step("[1/4] Invite the portal user"):
        resp = await sa_partners_client.invite_partner_user(payload)
        uid = resp.data.get("userId")
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert uid, "invited user must have a server-assigned userId"
        logger.info("CHECK invited → OK (HTTP 201, userId={})", uid)

    async with async_step("[2/4] Every submitted field is stored (no silent mutation)"):
        for f in ("partnerId", "email", "firstName", "lastName", "role"):
            assert resp.data.get(f) == payload[f], (
                f"stored {f}={resp.data.get(f)!r} must match sent {payload[f]!r}"
            )
        logger.info("CHECK echo → OK (partnerId/email/firstName/lastName/role stored as sent)")

    async with async_step("[3/4] User is usable (active + temp credential for hand-off)"):
        # BE model: invite creates an ACTIVE user + a tempPassword (plan says 'pending' — see Note).
        assert resp.data.get("status") == "active", (
            f"invited user must be usable, got status={resp.data.get('status')!r}"
        )
        assert resp.data.get("tempPassword"), "invite must return a tempPassword for SA hand-off"
        logger.info("CHECK lifecycle → OK (status='active', tempPassword issued)")

    async with async_step("[4/4] User is retrievable in the partner's user list"):
        listed = await sa_partners_client.list_partner_users(partner_id=pid, limit=50)
        assert any((u.get("userId") or u.get("id")) == uid for u in listed.data), (
            "invited user must appear in the partner-users list"
        )
        logger.info("CHECK retrievable → OK (user appears in the partner-users list)")

    logger.info("RESULT: partner user {} invited (role='{}')", uid, payload["role"])


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_012(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_USERS_012: invite partner-user invalid/missing fields - rejected with 400.

    Negative counterpart of _002. Each invalid/incomplete payload must be rejected
    with 4xx + a descriptive message. The ghost partnerId is self-proving (the
    endpoint returns "Partner ... not found"). All cases run (failures collected).
    """
    async with async_step("Setup: create a partner (valid baseline)"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        base = make_partner_user(pid, role="admin")

    def without(field: str) -> dict:
        return {k: v for k, v in base.items() if k != field}

    cases = [
        ("missing email", without("email"), "email must be an email"),
        ("missing firstName", without("firstName"), "firstname"),
        ("missing lastName", without("lastName"), "lastname"),
        ("missing partnerId", without("partnerId"), "partnerid must be a mongodb id"),
        ("invalid role", {**base, "role": "bogus", "email": unique_email()}, "role must be one of"),
        ("invalid email", {**base, "email": "not-an-email"}, "email must be an email"),
        ("ghost partnerId", {**base, "partnerId": _GHOST_ID, "email": unique_email()}, "not found"),
        (
            "malformed partnerId",
            {**base, "partnerId": "not-an-id", "email": unique_email()},
            "mongodb id",
        ),
    ]
    gaps: list[str] = []
    for idx, (label, body, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject invalid invite: {label}"):
            r = await sa_partners_client.raw_invite_partner_user(body, expected_status=None)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "invite negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid invite attempts rejected", len(cases))


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.be_gap  # re-inviting the same email creates a 2nd user — confirm with BE
async def test_partner_api_partner_users_013(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_USERS_013: invite the same email twice - must not create a duplicate user.

    Idempotency/duplicate counterpart of _002. Inviting the SAME email to the SAME
    partner a second time must NOT create a second user — it should be idempotent
    (return the existing user) or rejected (409), since email is the login identity.

    GAP (verified 2026-06-25): the API returns 201 and creates a SECOND user with the
    same email (the partner ends up with two users sharing one login). Step [2/2]
    asserts a single user for that email and therefore FAILS until the BE de-dupes —
    confirm with BE (reject duplicate email or make invite idempotent).
    """
    async with async_step("Setup: create a partner + invite a user"):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        payload = make_partner_user(pid, role="sales")
        first = await sa_partners_client.invite_partner_user(payload)
        assert first.data.get("userId"), "precondition: first invite must create a user"
        logger.info(
            "SETUP: partner {} + user {} (email {})",
            pid,
            first.data.get("userId"),
            payload["email"],
        )

    async with async_step("[1/2] Re-invite the SAME email"):
        r = await sa_partners_client.raw_invite_partner_user(payload, expected_status=None)
        assert r.status_code in (200, 201, 409), (
            f"re-invite must be a defined outcome (idempotent 2xx or reject 409), got {r.status_code}"
        )
        logger.info("CHECK re-invite → status {}", r.status_code)

    async with async_step("[2/2] The partner must NOT end up with a duplicate-email user"):
        listed = await sa_partners_client.list_partner_users(partner_id=pid, limit=100)
        same = [u for u in listed.data if u.get("email") == payload["email"]]
        assert len(same) == 1, (
            f"re-inviting must not duplicate: expected 1 user for {payload['email']}, got {len(same)} "
            "— BE creates a second user on re-invite; confirm with BE (reject or idempotent)"
        )
        logger.info("CHECK no-duplicate → OK (exactly 1 user for the email)")

    logger.info("RESULT: invite idempotency checked (email {})", payload["email"])


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_003(sa_partners_client, created_resources):
    """PARTNER_API_PARTNER_USERS_003: SA resets a partner-portal user's password - fresh credential, repeatable.

    Contract on ``POST /sa-partners-api/v1/sa/partner-users/{userId}/reset-password``:
    returns HTTP 200 and issues a fresh ``tempPassword`` (different from the invite
    one). Reset is a repeatable mutating action — a second reset also succeeds.

    Note (TC↔BE): the plan says "a reset LINK is sent to the user", but the BE returns
    a new ``tempPassword`` for SA hand-off (temp-password model, same as invite).
    Confirm with BE which model is intended. Idempotency: reset is NOT a create —
    repeating it is a valid operation (each issues a fresh credential), so there is no
    duplicate-create idempotency TC.
    """
    async with async_step(
        "Setup: create a partner + invite a user (capture the invite credential)"
    ):
        partner = await sa_partners_client.create_partner(make_partner())
        pid = partner.partner_id
        if pid:
            created_resources.add(lambda: sa_partners_client.delete_partner(pid))
        assert pid, "precondition: partner must be created"
        invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
        uid = invited.data.get("userId")
        assert uid, "precondition: partner user must be invited"
        old_temp = invited.data.get("tempPassword")
        logger.info("SETUP: partner {} + user {}", partner.data.get("code"), uid)

    async with async_step("[1/3] Reset the user's password"):
        resp = await sa_partners_client.reset_partner_user_password(uid)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should confirm the reset"
        assert (resp.data.get("userId") or resp.data.get("id")) == uid, (
            "reset response must reference the same user"
        )
        logger.info("CHECK reset → OK (200, '{}')", resp.message)

    async with async_step("[2/3] A fresh credential is issued (differs from the invite one)"):
        new_temp = resp.data.get("tempPassword")
        assert new_temp, "reset must issue a tempPassword (hand-off credential)"
        if old_temp:
            assert new_temp != old_temp, "reset must issue a NEW password, not the previous one"
        logger.info("CHECK credential → OK (fresh tempPassword issued)")

    async with async_step("[3/3] Reset is repeatable (mutating action, not one-shot)"):
        again = await sa_partners_client.reset_partner_user_password(uid)
        assert again.status_code == 200, "a second reset must also succeed"
        logger.info("CHECK repeatable → OK (second reset also 200)")

    logger.info("RESULT: password reset for user {} (fresh credential, repeatable)", uid)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_014(sa_partners_client):
    """PARTNER_API_PARTNER_USERS_014: reset password with invalid id - rejected (4xx, never 5xx).

    Negative counterpart of _003. A non-existent (ghost) userId and a malformed id
    must be rejected with 4xx + a clear message — self-proving (the endpoint returns
    "not found" / "Invalid id"). All cases run (failures collected).
    """
    cases = [
        ("ghost userId", _GHOST_ID, "not found"),
        ("malformed userId", "not-an-id", "invalid id"),
    ]
    gaps: list[str] = []
    for idx, (label, uid, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject reset: {label}"):
            r = await sa_partners_client.raw_reset_partner_user_password(uid)
            try:
                msg = str(r.json().get("message") or "")
            except ValueError:
                msg = r.text[:120]
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "reset-password negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid reset-password attempts rejected (ghost/malformed id)")
