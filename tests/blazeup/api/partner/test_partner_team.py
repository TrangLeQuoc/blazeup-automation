"""Partner Team directory API — the partner org managing its OWN members.

Maps to the test plan: PARTNER_API_PARTNER_TEAM_*. PRD §4.10 ("Partner Team Management +
Referral Links"), surface ``/sa-partners-api/v1/partner/directory/users``.

Not to be confused with the SA-side "Partner Directory" (PRD §5.1), where an SA operator
browses partner ORGANISATIONS — that is `PARTNER_UI_SA_PARTNER_MODULE_*`. The backend path
segment says `directory`; the feature is this org's own team list.

Every TC mints its own partner + portal session and deletes the partner on teardown, so no
test depends on another's data.
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_partner, make_prospect
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session, portal_client

# Never present on a team-member record — the invite response carries tempPassword by
# design (the admin has to pass it on), but nothing that LISTS or READS members may.
_SENSITIVE = ("password", "token", "secret", "credential", "tempPassword")

# From the OpenAPI spec 2026-09-16 (DirectoryInvitePartnerUserDto).
_ROLES = ("admin", "sales", "finance", "viewer")

# Rejected by the deals endpoint on 2026-09-17 with the full list in the 400 body.
_DEAL_STATUSES = ("registered", "approved", "in_progress", "won", "lost", "expired", "rejected")

# A well-formed ObjectId that does not exist.
_GHOST = "000000000000000000000000"

# The lockout fires on the 4th consecutive wrong password (measured 2026-09-17). The cap is
# a little higher so a threshold change shows up as a clear assertion rather than a hang.
_LOCKOUT_PROBE_MAX = 8


def _member_payload(role: str = "sales") -> dict:
    """Every field the DTO accepts except `password`, so each one can be asserted echoed."""
    p = make_partner()
    return {
        "email": f"team.{p['email']}",
        "firstName": "Team",
        "lastName": "Member",
        "role": role,
    }


def _envelope(resp) -> dict:
    """The `{statusCode, data, total?, message}` wrapper every endpoint here returns."""
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    assert "data" in body, f"envelope has no `data` key: {sorted(body)}"
    return body


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_001(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_001: partner team directory - invited member appears in list and detail.

    A partner admin invites a team member, reads the team list, then reads that member by
    id. Asserts every field sent is echoed back unchanged, the list is scoped to the caller's
    own partner, and no credential material leaks into the list.

    Precondition: an ACTIVE partner with a portal session (SA creates + approves, then the
    partner user logs in).
    """
    async with async_step("[1/6] Setup: mint an active partner + portal session"):
        portal, partner_id, session_user_id = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info(
            "SETUP: partner_id={} session_user_id={}",
            partner_id,
            session_user_id,
        )

    payload = _member_payload()
    logger.info(
        "SETUP: invite payload → email='{}', firstName='{}', lastName='{}', role='{}'",
        payload["email"],
        payload["firstName"],
        payload["lastName"],
        payload["role"],
    )

    async with async_step("[2/6] Invite a team member → 201 with the member record"):
        created = _envelope(await portal.invite_team_member(payload))["data"]
        member_id = created.get("userId")
        assert member_id, f"invite returned no userId: {sorted(created)}"
        logger.info("CHECK invite accepted → OK (userId={})", member_id)

    async with async_step("[3/6] Verify every field sent is echoed unchanged"):
        for field in ("email", "firstName", "lastName", "role"):
            assert created.get(field) == payload[field], (
                f"{field} was silently mutated: sent {payload[field]!r}, "
                f"stored {created.get(field)!r}"
            )
        assert created.get("partnerId") == partner_id, "member was attached to another partner"
        assert created.get("role") in _ROLES, f"role outside the spec enum: {created.get('role')!r}"
        assert isinstance(created.get("status"), str) and created["status"], "status missing"
        logger.info("CHECK all 4 fields echoed + partnerId/status → OK")

    async with async_step("[4/6] List the team → the invited member is present and typed"):
        listed = _envelope(await portal.list_team_members(params={"limit": 50}))
        rows = listed["data"]
        assert isinstance(rows, list), f"`data` must be a list, got {type(rows).__name__}"
        assert isinstance(listed.get("total"), int), "`total` must be an int"
        assert listed["total"] >= 2, (
            f"expected at least the session user + the invited member, got {listed['total']}"
        )
        row = next((r for r in rows if r.get("email") == payload["email"]), None)
        assert row is not None, f"invited member is absent from the list of {len(rows)}"
        for field in ("_id", "email", "role", "status", "firstName", "lastName"):
            assert field in row, f"list row is missing `{field}`: {sorted(row)}"
        logger.info("CHECK member listed with the required fields → OK (total={})", listed["total"])

    async with async_step("[5/6] Verify partner scoping and no credential leak in the list"):
        foreign = [r for r in rows if r.get("partnerId") != partner_id]
        assert not foreign, f"list leaked {len(foreign)} row(s) belonging to another partner"
        leaked = sorted(
            {k for r in rows for k in r if any(s.lower() in k.lower() for s in _SENSITIVE)}
        )
        assert not leaked, f"credential material exposed in the team list: {leaked}"
        logger.info("CHECK every row scoped to this partner, no credential field → OK")

    # The invite response and the list are both correct; reading ONE member is not.
    # Asking for the session user returns the invited member instead — the path param is
    # ignored (BUG-API-022). Asserting the member we asked for is the assertion this
    # endpoint exists to satisfy, so it stays and fails until BE fixes it.
    async with async_step("[6/6] Read the session user by id → must return THAT user"):
        fetched = _envelope(await portal.get_team_member(session_user_id))["data"]
        assert fetched.get("userId") == session_user_id, (
            f"GET /directory/users/{{userId}} ignored the path parameter: asked for "
            f"{session_user_id}, got {fetched.get('userId')} ({fetched.get('email')}). "
            "A ghost id and a malformed id return this same record with HTTP 200. Partner "
            "scoping still holds — another partner gets its own user, not this one — so it "
            "is wrong data, not a cross-partner leak. BUG-API-022, confirm with BE."
        )
        logger.info("CHECK member read back by id → OK")

    logger.info(
        "RESULT: invite → list → read-by-id verified for partner {} (member {})",
        partner_id,
        member_id,
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_002(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_002: partner team directory invalid input - rejected with the correct code.

    Negative counterpart of _001. Every required field missing, an invalid role enum, a bad
    email format, a ghost userId and a malformed userId. All cases run and failures are
    collected, so one broken rule does not hide the others.

    Duplicate-email is deliberately NOT here — a repeated create is its own TC
    (rule 8); see PARTNER_API_PARTNER_TEAM_00X in the plan.
    """
    async with async_step("[1/7] Setup: mint an active partner + portal session"):
        portal, partner_id, session_user_id = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner_id={}", partner_id)

    gaps: list[str] = []

    for idx, field in enumerate(("email", "firstName", "lastName"), start=2):
        async with async_step(f"[{idx}/7] Invite without `{field}` → expect 400"):
            bad = {k: v for k, v in _member_payload().items() if k != field}
            resp = await portal.invite_team_member(bad, expected_status=None)
            if resp.status_code != 400:
                gaps.append(
                    f"missing `{field}` was accepted with HTTP {resp.status_code} "
                    "(required by DirectoryInvitePartnerUserDto) — confirm with BE"
                )
            else:
                logger.info("CHECK missing `{}` → 400 → OK", field)

    async with async_step("[5/7] Invite with a role outside the enum → expect 400"):
        resp = await portal.invite_team_member(
            {**_member_payload(), "role": "wizard"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"role='wizard' accepted with HTTP {resp.status_code} — confirm with BE")
        else:
            logger.info("CHECK invalid role → 400 → OK")

    async with async_step("[6/7] Invite with a malformed email → expect 400"):
        resp = await portal.invite_team_member(
            {**_member_payload(), "email": "not-an-email"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(
                f"email='not-an-email' accepted with HTTP {resp.status_code} — confirm with BE"
            )
        else:
            logger.info("CHECK malformed email → 400 → OK")

    # A ghost id is self-proving here: the endpoint under test is the one that must report
    # "not found", so no separate GET at a source service is needed (rule 3 exception).
    async with async_step("[7/7] Read by ghost and malformed userId → expect 404 / 400"):
        ghost = "000000000000000000000000"
        resp = await portal.get_team_member(ghost, expected_status=None)
        if resp.status_code < 400:
            returned = (resp.json().get("data") or {}).get("userId")
            gaps.append(
                f"ghost userId {ghost} returned HTTP {resp.status_code} with userId="
                f"{returned} instead of 404 — the path parameter is ignored (BUG-API-022), "
                "so a caller reading a member it never asked for gets no error at all; "
                "confirm with BE"
            )
        else:
            logger.info("CHECK ghost userId → {} → OK", resp.status_code)

        resp = await portal.get_team_member("not-an-id", expected_status=None)
        if resp.status_code < 400:
            gaps.append(
                f"malformed userId 'not-an-id' returned HTTP {resp.status_code} instead of "
                "400 invalid-id (BUG-API-022) — confirm with BE"
            )
        else:
            logger.info("CHECK malformed userId → {} → OK", resp.status_code)

    assert not gaps, "Validation gaps on /v1/partner/directory/users:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: every invalid input refused with the correct code")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_003(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_PARTNER_TEAM_003: team member deals and commissions - own records, scoped.

    The two per-member rollups under a team member:
    ``GET /directory/users/{userId}/deals`` and ``/commissions``, both requiring a
    ``partnerId`` query. Asserts the envelope, that a registered deal is reachable, that the
    rollup DISCRIMINATES between members, and — the property that matters most — that another
    partner cannot read these rows even by passing this partner's id in the query.

    The commissions leg asserts the CONTRACT only, and an empty ledger is legitimate rather
    than a failure. Winning a deal does NOT earn a commission: since the v1 cutover the row
    accrues from the payment-gateway trigger (``PaymentEventsConsumer`` →
    ``CommissionAccrualService``) once the provisioned tenant's first payment succeeds,
    attributed by ``wonTenantId`` and anchored on ``goLiveAt``. Automation cannot make a real
    payment, so a non-empty ledger is out of reach here by design, not blocked by a defect.

    Precondition: an ACTIVE partner with a portal session, one invited member who registers
    nothing, and one deal registered by the session user.
    """
    async with async_step("[1/7] Setup: partner + portal session + a member + a deal"):
        portal, partner_id, session_user_id = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        member = _envelope(await portal.invite_team_member(_member_payload()))["data"]
        member_id = member["userId"]

        plan_id = await sa_deals_client.pick_billing_plan_id()
        deal = _envelope(await portal.register_deal(make_deal(None, plan_id, **make_prospect())))[
            "data"
        ]
        deal_id = deal.get("_id")
        assert deal_id, "precondition: the partner must be able to register a deal"
        logger.info(
            "SETUP: partner={} sessionUser={} member={} (registers nothing) deal={}",
            partner_id,
            session_user_id,
            member_id,
            deal_id,
        )

    async with async_step("[2/7] GET the session user's deals → envelope + the deal is there"):
        body = _envelope(await portal.get_team_member_deals(session_user_id, partner_id))
        rows = body["data"]
        assert isinstance(rows, list), f"`data` must be a list, got {type(rows).__name__}"
        assert isinstance(body.get("total"), int), "`total` must be an int"
        found = next((d for d in rows if d.get("_id") == deal_id), None)
        assert found is not None, f"the deal just registered is absent from {len(rows)} row(s)"
        logger.info("CHECK registered deal present → OK (total={})", body["total"])

    async with async_step("[3/7] Verify the deal row is well-formed and partner-scoped"):
        for field in ("_id", "partnerId", "dealType", "status", "prospectName"):
            assert field in found, f"deal row is missing `{field}`: {sorted(found)}"
        assert str(found["partnerId"]) == str(partner_id), "deal belongs to another partner"
        assert found["status"] in _DEAL_STATUSES, f"status outside the enum: {found['status']!r}"
        leaked = sorted(k for k in found if any(s.lower() in k.lower() for s in _SENSITIVE))
        assert not leaked, f"credential material exposed in a deal row: {leaked}"
        logger.info("CHECK deal row typed, scoped, no credential field → OK")

    async with async_step("[4/7] GET the member's commissions → valid envelope, empty is OK"):
        body = _envelope(await portal.get_team_member_commissions(member_id, partner_id))
        rows = body["data"]
        assert isinstance(rows, list), f"`data` must be a list, got {type(rows).__name__}"
        assert isinstance(body.get("total"), int), "`total` must be an int"
        # Empty is the expected state until the tenant's first payment accrues a commission
        # (see the docstring) — asserting "> 0" would make this TC fail for a reason that is
        # not a defect.
        logger.info("CHECK commissions envelope → OK (total={}, empty is valid)", body["total"])

    # The property worth the most here: a partnerId in the QUERY must not be able to widen
    # what the caller sees. It holds — verified 2026-09-17, partner B gets an empty list.
    async with async_step("[5/7] Another partner passing THIS partnerId must see nothing"):
        other_portal, other_pid, other_uid = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(other_pid))
        created_resources.add(other_portal.close)

        body = _envelope(await other_portal.get_team_member_deals(session_user_id, partner_id))
        assert body["data"] == [], (
            f"CROSS-PARTNER LEAK: partner {other_pid} passed partnerId={partner_id} in the query "
            f"and received {len(body['data'])} of its deals. The JWT must win over the query."
        )
        logger.info("CHECK cross-partner read refused (empty) → OK")

    async with async_step("[6/7] The rollup must DISCRIMINATE between members"):
        mine = _envelope(await portal.get_team_member_deals(session_user_id, partner_id))["data"]
        theirs = _envelope(await portal.get_team_member_deals(member_id, partner_id))["data"]
        assert [d.get("_id") for d in theirs] != [d.get("_id") for d in mine], (
            f"GET /directory/users/{{userId}}/deals ignores the path parameter: the member "
            f"{member_id} registered NO deals, yet asking for it returns the same "
            f"{len(theirs)} row(s) as the session user who registered them. A ghost userId "
            "returns them too. The deal record carries no registeredBy/createdBy field at all, "
            "so per-member attribution may not exist in the data model rather than the filter "
            "being broken. Partner scoping is intact (step 5). BUG-API-023, confirm with BE."
        )
        logger.info("CHECK per-member rollup discriminates → OK")

    async with async_step("[7/7] The partnerId query must not widen the result either"):
        foreign = _envelope(await portal.get_team_member_deals(session_user_id, other_pid))["data"]
        assert foreign == [], (
            f"passing partnerId={other_pid} (another partner) returned {len(foreign)} row(s) "
            "of THIS partner's deals — the query parameter is validated as a mongodb id and "
            "then ignored. Not a leak (the JWT still bounds it), but the parameter is a lie. "
            "BUG-API-023, confirm with BE."
        )
        logger.info("CHECK foreign partnerId returns nothing → OK")

    logger.info("RESULT: per-member rollups verified for partner {}", partner_id)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_004(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_004: team member deals/commissions invalid - correct rejection.

    Negative counterpart of _003: the required ``partnerId`` query missing, an invalid status
    enum, and ghost / malformed ids in both the path and the query. All cases run and failures
    are collected, so one broken rule does not hide the others.

    A ghost userId is self-proving here (rule 3 exception): the endpoint under test is the one
    that must report "not found", so no separate GET at a source service is needed.
    """
    async with async_step("[1/6] Setup: partner + portal session"):
        portal, partner_id, session_user_id = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={} sessionUser={}", partner_id, session_user_id)

    gaps: list[str] = []

    async with async_step("[2/6] Omit the REQUIRED partnerId query → expect 400"):
        legs = {
            "deals": portal.get_team_member_deals,
            "commissions": portal.get_team_member_commissions,
        }
        for leg, call in legs.items():
            # partner_id=None omits the parameter — the client builds the query, so this
            # negative stays behind a named method (no raw path in a test).
            resp = await call(session_user_id, None, expected_status=None)
            if resp.status_code != 400:
                gaps.append(f"{leg} without partnerId answered {resp.status_code}, expected 400")
            else:
                logger.info("CHECK {} without partnerId → 400 → OK", leg)

    async with async_step("[3/6] Invalid status enum → expect 400 naming the allowed values"):
        resp = await portal.get_team_member_deals(
            session_user_id, partner_id, params={"status": "bogus"}, expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"status='bogus' answered {resp.status_code}, expected 400")
        else:
            body = resp.text
            missing = [s for s in _DEAL_STATUSES if s not in body]
            if missing:
                gaps.append(f"the 400 for a bad status does not list {missing}")
            else:
                logger.info("CHECK invalid status → 400 listing every allowed value → OK")

    async with async_step("[4/6] Malformed partnerId → expect 400"):
        resp = await portal.get_team_member_deals(
            session_user_id, "not-an-id", expected_status=None
        )
        if resp.status_code != 400:
            gaps.append(f"partnerId='not-an-id' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed partnerId → 400 → OK")

    async with async_step("[5/6] Ghost and malformed userId → expect 404 / 400"):
        for label, uid, want in (("ghost", _GHOST, 404), ("malformed", "not-an-id", 400)):
            resp = await portal.get_team_member_deals(uid, partner_id, expected_status=None)
            if resp.status_code != want:
                n = len((resp.json().get("data") or []) if resp.status_code < 400 else [])
                gaps.append(
                    f"{label} userId answered {resp.status_code} with {n} row(s), expected "
                    f"{want} — the path parameter is ignored (BUG-API-023), so a member that "
                    "does not exist reads as one that simply has no records. This partner has "
                    "no deals, so nothing was disclosed here; _003 shows the same call "
                    "returning another member's deals when there ARE any. Confirm with BE"
                )
            else:
                logger.info("CHECK {} userId → {} → OK", label, want)

    async with async_step("[6/6] Ghost partnerId → expect 404, never this partner's rows"):
        resp = await portal.get_team_member_deals(session_user_id, _GHOST, expected_status=None)
        if resp.status_code < 400:
            n = len(resp.json().get("data") or [])
            gaps.append(
                f"a ghost partnerId answered {resp.status_code} with {n} row(s) instead of 404 "
                "— the query parameter is validated as a mongodb id and then ignored "
                "(BUG-API-023); confirm with BE"
            )
        else:
            logger.info("CHECK ghost partnerId → {} → OK", resp.status_code)

    assert not gaps, (
        "Validation gaps on /v1/partner/directory/users/{userId}/{deals,commissions}:\n  - "
        + "\n  - ".join(gaps)
    )
    logger.info("RESULT: every invalid input refused with the correct code")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_005(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_005: reset a member's password and unlock a locked member.

    Both actions are verified by their EFFECT on login, not by the 2xx alone: the invite's
    ``tempPassword`` is the member's real login password, so the suite can prove the old one
    stopped working and the new one works. No mailbox access is needed or implied.

    Lockout threshold measured 2026-09-17: the 4th consecutive wrong password is refused with
    "Too many failed login attempts. Try again in 30 minutes." — which is exactly why this TC
    uses a member it creates for itself.

    Precondition: an ACTIVE partner with a portal session and a THROWAWAY member. Never the
    shared portal account: locking or resetting that one breaks every other partner test for
    the next 30 minutes.
    """
    async with async_step("[1/8] Setup: partner + portal session + a throwaway member"):
        portal, partner_id, _session_user_id = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        member = _envelope(await portal.invite_team_member(_member_payload()))["data"]
        user_id, email, old_password = member["userId"], member["email"], member.get("tempPassword")
        assert old_password, "the invite must return a tempPassword to log in with"

        anon = portal_client(settings)
        created_resources.add(anon.close)
        logger.info("SETUP: throwaway member={} email={}", user_id, email)

    async with async_step("[2/8] Baseline: the member can log in with the invite password"):
        resp = await anon.login(email, old_password, expected_status=None)
        assert resp.status_code == 200, (
            f"precondition failed: a freshly invited member cannot log in (HTTP "
            f"{resp.status_code}) — the rest of this TC would prove nothing"
        )
        logger.info("CHECK invited member logs in → OK")

    async with async_step("[3/8] Reset the password → 200 with a NEW credential"):
        data = _envelope(await portal.reset_team_member_password(user_id))["data"]
        new_password = data.get("tempPassword")
        assert new_password, f"reset must return the new tempPassword: {sorted(data)}"
        assert new_password != old_password, "reset returned the SAME password — nothing changed"
        assert data.get("userId") == user_id, "reset answered about a different user"
        logger.info("CHECK reset returned a new credential → OK")

    async with async_step("[4/8] The OLD password must stop working"):
        resp = await anon.login(email, old_password, expected_status=None)
        assert resp.status_code == 401, (
            f"the old password still authenticates (HTTP {resp.status_code}) — the reset did "
            "not take effect, so the endpoint reports success it did not deliver"
        )
        logger.info("CHECK old password → 401 → OK")

    async with async_step("[5/8] The NEW password must work"):
        resp = await anon.login(email, new_password, expected_status=None)
        assert resp.status_code == 200, (
            f"the password returned by reset does not authenticate (HTTP {resp.status_code}) — "
            "the admin would hand the member a credential that does not work"
        )
        logger.info("CHECK new password → 200 → OK")

    async with async_step("[6/8] Lock the member out with wrong passwords"):
        locked = None
        for attempt in range(1, _LOCKOUT_PROBE_MAX + 1):
            resp = await anon.login(email, "WrongPassword!123", expected_status=None)
            if "too many failed" in resp.text.lower():
                locked = attempt
                break
        assert locked, (
            f"{_LOCKOUT_PROBE_MAX} wrong passwords did not lock the account — there is nothing "
            "for unlock to clear, and brute-force is unthrottled. Confirm with BE"
        )
        logger.info("CHECK locked after {} wrong attempt(s) → OK", locked)

    async with async_step("[7/8] The CORRECT password is refused while locked"):
        resp = await anon.login(email, new_password, expected_status=None)
        assert resp.status_code != 200, (
            "the correct password still logs in while the account is locked — the lockout is "
            "cosmetic"
        )
        logger.info("CHECK correct password refused while locked → {} → OK", resp.status_code)

    async with async_step("[8/8] Unlock → the member can log in again"):
        data = _envelope(await portal.unlock_team_member(user_id))["data"]
        assert data.get("userId") == user_id, "unlock answered about a different user"
        resp = await anon.login(email, new_password, expected_status=None)
        assert resp.status_code == 200, (
            f"unlock returned success but the member still cannot log in (HTTP "
            f"{resp.status_code}) — the lockout was not cleared"
        )
        logger.info("CHECK unlock cleared the lockout → OK")

    logger.info("RESULT: reset-password and unlock both verified by their effect on login")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_009(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_009: reset-password / unlock invalid target and repeat.

    Negative counterpart of _005: a ghost userId, a malformed one, and what a REPEAT does.

    Rule 8's 409-or-idempotent formula does not apply here — neither endpoint CREATES a
    resource, so a repeat is a mutating action whose correct behaviour has to be probed
    rather than assumed. Measured 2026-09-17: a second reset issues another new password
    (by design — the admin can re-issue), and unlocking an already-unlocked member is a no-op.

    Ghost ids are self-proving: the endpoint under test is the one that must report them.
    """
    async with async_step("[1/5] Setup: partner + portal session + a throwaway member"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        member = _envelope(await portal.invite_team_member(_member_payload()))["data"]
        user_id, email = member["userId"], member["email"]
        anon = portal_client(settings)
        created_resources.add(anon.close)
        logger.info("SETUP: throwaway member={}", user_id)

    gaps: list[str] = []

    async with async_step("[2/5] Ghost userId on both endpoints → must be refused"):
        for label, call in (
            ("reset-password", portal.reset_team_member_password),
            ("unlock", portal.unlock_team_member),
        ):
            resp = await call(_GHOST, expected_status=None)
            if resp.status_code < 400:
                gaps.append(f"{label} accepted a ghost userId with HTTP {resp.status_code}")
            elif "not found" not in resp.text.lower():
                gaps.append(f"{label} refused a ghost userId without saying not-found")
            else:
                # 400 rather than 404 is the service-wide ghost-id convention (the shared
                # Method.findById raises BadRequestException). Refusal is what matters here;
                # the status-code family is tracked separately, not re-filed per endpoint.
                logger.info("CHECK {} ghost userId → {} not-found → OK", label, resp.status_code)

    async with async_step("[3/5] Malformed userId on both endpoints → 400 invalid-id"):
        for label, call in (
            ("reset-password", portal.reset_team_member_password),
            ("unlock", portal.unlock_team_member),
        ):
            resp = await call("not-an-id", expected_status=None)
            if resp.status_code != 400:
                gaps.append(f"{label} answered {resp.status_code} for a malformed id, expected 400")
            else:
                logger.info("CHECK {} malformed userId → 400 → OK", label)

    async with async_step("[4/5] Repeat reset → a DIFFERENT password each time, both usable"):
        first = _envelope(await portal.reset_team_member_password(user_id))["data"]["tempPassword"]
        second = _envelope(await portal.reset_team_member_password(user_id))["data"]["tempPassword"]
        if first == second:
            gaps.append("two consecutive resets returned the SAME password — confirm with BE")
        else:
            resp = await anon.login(email, first, expected_status=None)
            if resp.status_code == 200:
                gaps.append(
                    "the password from the FIRST reset still works after a second reset — a "
                    "re-issued credential must supersede the previous one; confirm with BE"
                )
            else:
                logger.info("CHECK repeat reset supersedes the previous credential → OK")

    async with async_step("[5/5] Repeat unlock on a member that is not locked → no-op, no 5xx"):
        for n in (1, 2):
            resp = await portal.unlock_team_member(user_id, expected_status=None)
            if resp.status_code >= 500:
                gaps.append(f"unlock #{n} on an unlocked member returned {resp.status_code}")
            elif resp.status_code >= 400:
                gaps.append(
                    f"unlock #{n} on an unlocked member was refused with {resp.status_code}; "
                    "clearing nothing should be a no-op, not an error — confirm with BE"
                )
        if not gaps:
            logger.info("CHECK repeated unlock is a no-op → OK")

    assert not gaps, (
        "Gaps on /v1/partner/directory/users/{userId}/{reset-password,unlock}:\n  - "
        + "\n  - ".join(gaps)
    )
    logger.info("RESULT: invalid targets refused, repeat behaviour is as designed")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_008(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_008: invite the same email twice - rejected, no duplicate member.

    Rule 8 requires a POST that CREATES a resource to state what a repeat does. Probed on
    2026-09-16: the second invite answers **409 Conflict** with "A partner user with email
    ... already exists". This asserts that, and then proves the directory still holds exactly
    ONE member with that email — a 409 that still wrote a row would be the worse bug.

    Its own TC rather than a trailing step of _001: a duplicate failing there would paint the
    whole create path red and read like "invite is broken".
    """
    async with async_step("[1/4] Setup: mint an active partner + portal session"):
        portal, partner_id, _session_user_id = await mint_partner_session(
            sa_partners_client, settings
        )
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner_id={}", partner_id)

    payload = _member_payload()
    logger.info("SETUP: email to be invited twice → '{}'", payload["email"])

    async with async_step("[2/4] First invite → 201"):
        first = _envelope(await portal.invite_team_member(payload))["data"]
        assert first.get("userId"), "the first invite must create the member"
        logger.info("CHECK first invite created userId={} → OK", first["userId"])

    async with async_step("[3/4] Second invite, same email → expect 409 Conflict"):
        resp = await portal.invite_team_member(payload, expected_status=None)
        assert resp.status_code == 409, (
            f"a repeated invite answered HTTP {resp.status_code}, expected 409 Conflict. "
            "Either the duplicate rule changed or a second member was created — confirm "
            f"with BE. Body: {resp.text[:200]}"
        )
        logger.info("CHECK duplicate invite → 409 → OK")

    async with async_step("[4/4] Verify the directory still holds exactly ONE such member"):
        rows = _envelope(await portal.list_team_members(params={"limit": 50}))["data"]
        same = [r for r in rows if r.get("email") == payload["email"]]
        assert len(same) == 1, (
            f"expected exactly 1 member with {payload['email']}, found {len(same)} — "
            "the rejected invite still wrote a row"
        )
        logger.info("CHECK exactly one member with that email → OK")

    logger.info("RESULT: duplicate invite rejected with 409 and no second member created")
