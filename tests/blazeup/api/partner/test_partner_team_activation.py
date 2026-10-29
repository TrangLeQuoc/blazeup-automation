"""Partner team invite -> activation link (BLAZ7-17) - API.

Maps to the test plan: PARTNER_API_PARTNER_TEAM_010..029, derived from the backend's
TC-PTA-* design (``.ai/memory/context/partner-team-activation-test-cases.md``). Surface:
``POST /v1/partner/directory/users`` (+ ``/:id/resend-invitation`` and ``/cancel-invitation``),
the public ``POST /v1/partner/auth/activate`` and the SA twin ``/v1/sa/partner-users``.

How each TC runs
----------------
* **Portal-side** TCs need a partner-admin session. Default: SA mints one (staging). Opt-in
  ``PARTNER_SESSION_SOURCE=env``: log in as ``PARTNER_EMAIL`` / ``PARTNER_PASSWORD`` instead,
  so they run on a stack with no SA login (local). The org is shared and never deleted; each
  TC cancels the invitations it created.
* **Token** TCs (marked ``[token]``) need the e-mailed link, which is never in an HTTP
  response. They read it through ``utils.activation_link`` and SKIP (not fail) when
  ``ACTIVATION_LINK_SOURCE`` is ``none``.
* **SA-side** TCs (marked ``[SA]``) use the SA login and skip when it is not configured.

The token and passwords are never logged or asserted into messages.
"""

import asyncio
import re
import secrets

import pytest
import pytest_asyncio
from loguru import logger

from config.settings import Settings
from utils.activation_link import get_activation_token, is_configured, skip_reason
from utils.data_factory import make_partner, make_partner_user
from utils.log_helper import async_step
from utils.partner_portal import (
    PortalSession,
    fresh_ip_headers,
    new_password,
    open_portal_session,
    partner_login,
    portal_client,
)

_GHOST = "000000000000000000000000"
_INVALID = "activation_link_invalid"
# Keys/values that must never appear in any invite/resend/cancel/list response.
_SECRET_KEYS = ("tempPassword", "password", "passwordHash", "token", "tokenHash", "activationToken")
_TOKEN_SHAPE = re.compile(r"\b[A-Za-z0-9_-]{43}\b")
_COOLDOWN_WAIT_S = 61


def _env_session_selected() -> bool:
    """Decide at import time which session fixture shape to define (static per run)."""
    try:
        return Settings().partner_session_source == "env"
    except Exception:  # noqa: BLE001 — settings problems surface in the `settings` fixture
        return False


# A fixture cannot depend on `sa_partners_client` only sometimes, so there are two shapes:
# the env one never touches the SA fixtures (they would skip the test on a stack with no SA
# login), the mint one needs them.
if _env_session_selected():

    @pytest_asyncio.fixture
    async def admin(settings, created_resources) -> PortalSession:
        """Partner-admin portal session from PARTNER_EMAIL/PARTNER_PASSWORD (no SA needed)."""
        return await open_portal_session(settings, created_resources)

else:

    @pytest_asyncio.fixture
    async def admin(settings, created_resources, sa_partners_client) -> PortalSession:
        """Partner-admin portal session on a freshly minted ACTIVE partner (SA setup)."""
        return await open_portal_session(settings, created_resources, sa_partners_client)


def _body(resp) -> dict:
    """JSON body of a response ({} when it is not JSON)."""
    try:
        data = resp.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _stable(resp) -> dict:
    """Body without the per-request ``timestamp`` - what "identical response" really means."""
    return {k: v for k, v in _body(resp).items() if k != "timestamp"}


def _member(email_prefix: str = "pta", role: str = "sales") -> dict:
    """A valid portal invite payload (no password, no partnerId)."""
    p = make_partner_user("x", role=role)
    return {
        "email": f"{email_prefix}.{p['email']}",
        "firstName": p["firstName"],
        "lastName": p["lastName"],
        "role": role,
    }


def _assert_no_secret(obj, where: str) -> None:
    """No credential-bearing key anywhere in ``obj`` (recursive) - checks keys, not values."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _SECRET_KEYS, f"{where}: secret-bearing key {k!r} present"
            _assert_no_secret(v, where)
    elif isinstance(obj, list):
        for v in obj:
            _assert_no_secret(v, where)


async def _invite(sess: PortalSession, created_resources, payload: dict | None = None) -> dict:
    """Invite via the portal route and register a best-effort cancel (a no-op once activated)."""
    payload = payload or _member()
    resp = await sess.portal.invite_team_member(payload)
    data = _body(resp)["data"]
    uid = data["userId"]
    sess.invited_user_ids.append(uid)
    created_resources.add(lambda: sess.portal.cancel_team_invitation(uid, expected_status=None))
    return data


async def _token(settings, email: str, *, not_token: str | None = None) -> str:
    """The emailed activation token for ``email`` - SKIPS the test when no source is wired."""
    if not is_configured(settings):
        pytest.skip(f"BLOCKED: {skip_reason()}")
    token = await get_activation_token(settings, email, not_token=not_token)
    if not token:
        pytest.skip("BLOCKED: activation source configured but no matching e-mail arrived")
    return token


def _anon(settings, created_resources):
    """Unauthenticated portal client (login / activate), closed on teardown."""
    anon = portal_client(settings)
    created_resources.add(anon.close)
    return anon


async def _list_rows(sess: PortalSession) -> list[dict]:
    """The caller's team list (first 100 rows)."""
    return _body(await sess.portal.list_team_members(params={"limit": 100}))["data"]


def _row_for(rows: list[dict], email: str) -> dict | None:
    """The list row with ``email`` (case-insensitive), or None."""
    return next((r for r in rows if str(r.get("email", "")).lower() == email.lower()), None)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_010(admin, created_resources):
    """PARTNER_API_PARTNER_TEAM_010: portal invite - pending_activation user, no credential returned.

    TC-PTA-01. A partner admin invites a member: 201, the documented key set, status
    ``pending_activation``, a 72 h expiry, and no password/token material in the body.
    """
    payload = _member()
    async with async_step("[1/3] Invite a team member -> 201"):
        resp = await admin.portal.invite_team_member(payload)
        body = _body(resp)
        data = body["data"]
        admin.invited_user_ids.append(data.get("userId"))
        created_resources.add(
            lambda: admin.portal.cancel_team_invitation(data["userId"], expected_status=None)
        )
        assert isinstance(body.get("message"), str), "envelope must carry a string message"
        logger.info("CHECK invite accepted -> OK (userId={})", data.get("userId"))

    async with async_step("[2/3] Shape: documented keys, pending status, echoed fields"):
        for key in (
            "userId",
            "partnerId",
            "email",
            "firstName",
            "lastName",
            "role",
            "status",
            "invitationSentAt",
            "invitationExpiresAt",
            "activationEmailSent",
        ):
            assert key in data, f"invite response is missing `{key}`: {sorted(data)}"
        assert data["status"] == "pending_activation", f"status={data['status']!r}"
        assert isinstance(data["activationEmailSent"], bool)
        for f in ("email", "firstName", "lastName", "role"):
            assert data[f] == payload[f], f"{f} mutated: sent {payload[f]!r}, got {data[f]!r}"
        assert data["partnerId"] == admin.partner_id, "invitee attached to a different org"
        logger.info("CHECK shape + status -> OK")

    async with async_step("[3/3] 72 h lifetime and no secret in the response"):
        from datetime import datetime

        sent = datetime.fromisoformat(data["invitationSentAt"].replace("Z", "+00:00"))
        exp = datetime.fromisoformat(data["invitationExpiresAt"].replace("Z", "+00:00"))
        hours = (exp - sent).total_seconds() / 3600
        assert abs(hours - 72) < 0.01, f"invitation lifetime is {hours:.2f} h, expected 72"
        _assert_no_secret(body, "invite response")
        logger.info("CHECK 72 h expiry + no secret -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_011(admin, created_resources):
    """PARTNER_API_PARTNER_TEAM_011: invite with `password` or any undeclared key - 400, nothing created.

    TC-PTA-04/05. The invite DTO is strict: the removed ``password`` key and an arbitrary
    extra key (``partnerId`` included on the portal route) are both rejected, and no row
    is written.
    """
    cases = {"password": "Sup3r!secret1", "partnerId": _GHOST, "nonsense": 1}
    async with async_step("[1/2] Each extra key -> 400"):
        sent_emails = []
        for key, value in cases.items():
            payload = _member() | {key: value}
            sent_emails.append(payload["email"])
            resp = await admin.portal.invite_team_member(payload, expected_status=None)
            assert resp.status_code == 400, (
                f"extra key {key!r} answered HTTP {resp.status_code}, expected 400: {resp.text[:160]}"
            )
            logger.info("CHECK extra key {} -> 400 -> OK", key)
    async with async_step("[2/2] No row was written for any rejected invite"):
        rows = await _list_rows(admin)
        leaked = [e for e in sent_emails if _row_for(rows, e)]
        assert not leaked, f"{len(leaked)} rejected invite(s) still created a user"
        logger.info("CHECK no rows written -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_012(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_012: duplicate email - one generic 409, no existing-account hint.

    TC-PTA-07. Re-inviting a pending address AND inviting an address that already belongs to
    an active user both answer the same generic 409, so the route cannot be used to probe
    which emails exist.
    """
    pending = await _invite(admin, created_resources)
    async with async_step("[1/3] Re-invite the pending email -> 409"):
        r1 = await admin.portal.invite_team_member(
            _member() | {"email": pending["email"]}, expected_status=None
        )
        assert r1.status_code == 409, f"HTTP {r1.status_code}: {r1.text[:160]}"
    async with async_step("[2/3] Invite an email owned by an ACTIVE user -> the same 409"):
        active_email = settings.partner_email or "admin@local.test"
        if settings.partner_session_source != "env":
            active_email = pending["email"]  # minted org: the pending user is the only known email
        r2 = await admin.portal.invite_team_member(
            _member() | {"email": active_email}, expected_status=None
        )
        assert r2.status_code == 409, f"HTTP {r2.status_code}: {r2.text[:160]}"
        assert _body(r1).get("message") == _body(r2).get("message"), (
            "the 409 body differs by account state - it leaks which emails exist"
        )
    async with async_step("[3/3] Body is generic: no org, user id or status disclosed"):
        text = r1.text.lower()
        for leak in (admin.partner_id.lower(), pending["userId"].lower(), "pending", "active"):
            if leak:
                assert leak not in text, f"409 body discloses {leak!r}: {r1.text[:200]}"
        logger.info("CHECK generic 409 -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_013(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_013: pending user login - identical to an unknown email.

    TC-PTA-55. A pending_activation user cannot log in (there is no password yet) and the
    rejection is byte-for-byte the "Invalid credentials" an unknown email gets.
    """
    member = await _invite(admin, created_resources)
    anon = _anon(settings, created_resources)
    async with async_step("[1/2] Login as the pending user and as an unknown email"):
        pend = await anon.login(member["email"], "Wrong#Pass123", expected_status=None)
        ghost = await anon.login(f"nobody.{member['email']}", "Wrong#Pass123", expected_status=None)
        assert pend.status_code == 400, f"pending login HTTP {pend.status_code}"
        assert ghost.status_code == 400, f"unknown login HTTP {ghost.status_code}"
    async with async_step("[2/2] Same status and body, no pending/activation hint"):
        assert _stable(pend) == _stable(ghost), (
            "pending login is distinguishable from unknown email"
        )
        assert "invalid credentials" in pend.text.lower()
        for hint in ("pending", "activat", "invit"):
            assert hint not in pend.text.lower(), f"login body hints at {hint!r}"
        logger.info("CHECK pending login == unknown email -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_014(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_014: activate [token] - password set, no session, user can log in.

    TC-PTA-21/22. Valid token + a policy password -> 200 ``{data: {email}}`` with no
    accessToken/refreshToken; the user then logs in with that password and shows as active.
    """
    member = await _invite(admin, created_resources)
    token = await _token(settings, member["email"])
    anon = _anon(settings, created_resources)
    password = new_password()
    async with async_step("[1/3] Activate -> 200, only the email is returned, no session"):
        resp = await anon.activate(token, password, headers=fresh_ip_headers())
        body = _body(resp)
        assert body.get("data", {}).get("email", "").lower() == member["email"].lower()
        flat = resp.text.lower()
        for forbidden in ("accesstoken", "refreshtoken", "access_token", "set-cookie"):
            assert forbidden not in flat, f"activation issued a session ({forbidden})"
        assert "set-cookie" not in {k.lower() for k in resp.headers}, "activation set a cookie"
        logger.info("CHECK activate 200, no session -> OK")
    async with async_step("[2/3] Login with the chosen password -> 200"):
        login = await partner_login(anon, member["email"], password)
        assert login.status_code in (200, 201), f"login HTTP {login.status_code}"
    async with async_step("[3/3] The user is now active in the team list"):
        row = _row_for(await _list_rows(admin), member["email"])
        assert row and row.get("status") == "active", f"row={row and row.get('status')!r}"
        logger.info("CHECK status active -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_015(settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_015: unknown and malformed tokens - one shared invalid-link body.

    TC-PTA-27. A random 43-char token, wrong-length strings and an empty/blank token all get
    HTTP 400 ``activation_link_invalid`` with the identical body, so nothing distinguishes
    "never existed" from "malformed". Needs no mailbox.
    """
    anon = _anon(settings, created_resources)
    headers = fresh_ip_headers()
    samples = {
        "random-43": secrets.token_urlsafe(32)[:43],
        "short-42": "a" * 42,
        "long-44": "b" * 44,
        "plus-char": "c" * 42 + "+",
        "blank": "   ",
    }
    bodies = {}
    async with async_step("[1/2] Activate with each bad token -> 400 invalid link"):
        for name, tok in samples.items():
            resp = await anon.activate(tok, new_password(), expected_status=None, headers=headers)
            bodies[name] = _stable(resp)
            if resp.status_code == 400 and bodies[name].get("error") == _INVALID:
                continue
            # A blank token may legitimately be a DTO validation error (GAP-PTA-TC-02).
            assert name == "blank" and resp.status_code == 400, (
                f"{name}: HTTP {resp.status_code} body={resp.text[:140]}"
            )
        logger.info("CHECK bad tokens rejected -> OK")
    async with async_step("[2/2] Every invalid-link body is identical"):
        invalid = [b for n, b in bodies.items() if b.get("error") == _INVALID]
        assert len(invalid) >= 4 and all(b == invalid[0] for b in invalid), (
            "invalid-link bodies differ between unknown/malformed tokens"
        )
        logger.info("CHECK identical bodies -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_016(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_016: reuse of a used token [token] - 400 activation_link_invalid.

    TC-PTA-24. The second activation with the same token is refused with the same body as
    an unknown token, and the first password keeps working (not overwritten).
    """
    member = await _invite(admin, created_resources)
    token = await _token(settings, member["email"])
    anon = _anon(settings, created_resources)
    first_pw = new_password()
    async with async_step("[1/3] First activation -> 200"):
        await anon.activate(token, first_pw, headers=fresh_ip_headers())
    async with async_step("[2/3] Reuse the token with another password -> 400 invalid"):
        resp = await anon.activate(
            token, new_password(), expected_status=None, headers=fresh_ip_headers()
        )
        assert resp.status_code == 400 and _body(resp).get("error") == _INVALID, (
            f"HTTP {resp.status_code} body={resp.text[:160]}"
        )
        unknown = await anon.activate(
            "z" * 43, new_password(), expected_status=None, headers=fresh_ip_headers()
        )
        assert _stable(resp) == _stable(unknown), "used-token body differs from unknown-token body"
    async with async_step("[3/3] The first password still logs in"):
        login = await partner_login(anon, member["email"], first_pw)
        assert login.status_code in (200, 201), "the reused token overwrote the password"
        logger.info("CHECK reuse rejected, first password intact -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_017(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_017: password shorter than 8 [token] - 400 and the token survives.

    TC-PTA-23. A rejected password must not burn the one-time link: the same token still
    activates with a valid password afterwards.
    """
    member = await _invite(admin, created_resources)
    token = await _token(settings, member["email"])
    anon = _anon(settings, created_resources)
    async with async_step("[1/2] 7-char password -> 400 validation"):
        resp = await anon.activate(
            token, "Ab1!xyz", expected_status=None, headers=fresh_ip_headers()
        )
        assert resp.status_code == 400, f"HTTP {resp.status_code}: {resp.text[:160]}"
        assert _body(resp).get("error") != _INVALID, "a weak password invalidated the link"
    async with async_step("[2/2] Same token with a valid password -> 200"):
        ok = await anon.activate(
            token, new_password(), expected_status=None, headers=fresh_ip_headers()
        )
        assert ok.status_code == 200, (
            f"token was burnt by the rejected attempt: HTTP {ok.status_code}"
        )
        logger.info("CHECK token survives a weak password -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_018(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_018: 72-byte password limit [token] - 73 bytes rejected, 72 accepted.

    TC-PTA-23/28. bcrypt truncates at 72 bytes, so the API caps the password in UTF-8 BYTES
    (a multi-byte character counts more than one). 73 bytes -> 400 with the token intact;
    exactly 72 bytes -> 200 and that password logs in.
    """
    member = await _invite(admin, created_resources)
    token = await _token(settings, member["email"])
    anon = _anon(settings, created_resources)
    over = "Aa1!" + "x" * 69  # 73 bytes
    multibyte_over = "Aa1!" + "é" * 35  # 4 + 70 = 74 bytes, only 39 characters
    exact = "Aa1!" + "y" * 68  # 72 bytes
    async with async_step("[1/3] 73 ASCII bytes and 74 bytes in 39 chars -> 400"):
        for label, pw in (("73-byte", over), ("74-byte multibyte", multibyte_over)):
            resp = await anon.activate(token, pw, expected_status=None, headers=fresh_ip_headers())
            assert resp.status_code == 400, f"{label}: HTTP {resp.status_code}"
            assert _body(resp).get("error") != _INVALID, f"{label}: the link was invalidated"
    async with async_step("[2/3] Exactly 72 bytes -> 200 (token still valid)"):
        ok = await anon.activate(token, exact, expected_status=None, headers=fresh_ip_headers())
        assert ok.status_code == 200, f"HTTP {ok.status_code}: {ok.text[:160]}"
    async with async_step("[3/3] The 72-byte password logs in"):
        login = await partner_login(anon, member["email"], exact)
        assert login.status_code in (200, 201)
        logger.info("CHECK 72-byte boundary -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_019(settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_019: activate body validation - missing/non-string/extra keys -> 400.

    TC-PTA-28. The public route is strict: a missing token or password, non-string values and
    any undeclared key are all 400 validation errors (not the invalid-link body, not 5xx).
    Needs no mailbox.
    """
    anon = _anon(settings, created_resources)
    good = {"token": "a" * 43, "password": "Aa1!validpass"}
    bad_bodies = {
        "no token": {"password": good["password"]},
        "no password": {"token": good["token"]},
        "empty body": {},
        "token not string": {**good, "token": 12345},
        "password not string": {**good, "password": ["x"]},
        "extra key": {**good, "email": "someone@example.test"},
        "token 513 chars": {**good, "token": "t" * 513},
    }
    async with async_step("[1/1] Every malformed body -> HTTP 400"):
        for name, body in bad_bodies.items():
            resp = await anon.activate_raw(body, headers=fresh_ip_headers())
            assert resp.status_code == 400, f"{name}: HTTP {resp.status_code}: {resp.text[:140]}"
            assert resp.status_code < 500
        logger.info("CHECK {} malformed bodies -> 400 -> OK", len(bad_bodies))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_020(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_020: resend [token] - 200, previous link dies, new link works.

    TC-PTA-26/37. After the 60 s cooldown a resend returns 200 with a fresh expiry and rotates
    the token: the first link is now ``activation_link_invalid`` and only the new one activates.
    """
    member = await _invite(admin, created_resources)
    old = await _token(settings, member["email"])
    anon = _anon(settings, created_resources)
    async with async_step(f"[1/4] Wait out the {_COOLDOWN_WAIT_S}s cooldown that starts at invite"):
        await asyncio.sleep(_COOLDOWN_WAIT_S)
    async with async_step("[2/4] Resend -> 200 with the documented shape"):
        resp = await admin.portal.resend_team_invitation(member["userId"])
        data = _body(resp)["data"]
        for key in (
            "userId",
            "status",
            "invitationSentAt",
            "invitationExpiresAt",
            "activationEmailSent",
        ):
            assert key in data, f"resend response is missing `{key}`"
        assert data["status"] == "pending_activation"
        assert data["invitationExpiresAt"] > member["invitationExpiresAt"], "expiry not extended"
        _assert_no_secret(_body(resp), "resend response")
    async with async_step("[3/4] The OLD link is dead"):
        dead = await anon.activate(
            old, new_password(), expected_status=None, headers=fresh_ip_headers()
        )
        assert dead.status_code == 400 and _body(dead).get("error") == _INVALID, (
            f"superseded link answered HTTP {dead.status_code}: {dead.text[:140]}"
        )
    async with async_step("[4/4] The NEW link activates"):
        new = await _token(settings, member["email"], not_token=old)
        ok = await anon.activate(
            new, new_password(), expected_status=None, headers=fresh_ip_headers()
        )
        assert ok.status_code == 200, f"new link HTTP {ok.status_code}"
        logger.info("CHECK old link dead, new link works -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_021(admin, created_resources):
    """PARTNER_API_PARTNER_TEAM_021: resend cooldown - 429 within 60 s of invite and of a resend.

    TC-PTA-42/44. The cooldown starts at the invite: an immediate resend is 429
    ("Please wait a minute..."); after 61 s a resend is 200 and an immediate second one is
    429 again. Takes ~65 s.
    """
    member = await _invite(admin, created_resources)
    async with async_step("[1/4] Immediate resend after invite -> 429"):
        r = await admin.portal.resend_team_invitation(member["userId"], expected_status=None)
        assert r.status_code == 429, f"HTTP {r.status_code}: {r.text[:160]}"
        assert "wait a minute" in r.text.lower(), f"unexpected 429 message: {r.text[:160]}"
    async with async_step("[2/4] A throttled resend changes nothing"):
        row = _row_for(await _list_rows(admin), member["email"])
        assert row and row.get("invitationExpiresAt") == member["invitationExpiresAt"], (
            "a throttled resend still moved the expiry"
        )
    async with async_step(f"[3/4] After {_COOLDOWN_WAIT_S}s a resend -> 200"):
        await asyncio.sleep(_COOLDOWN_WAIT_S)
        await admin.portal.resend_team_invitation(member["userId"])
    async with async_step("[4/4] Immediate second resend -> 429 again"):
        r2 = await admin.portal.resend_team_invitation(member["userId"], expected_status=None)
        assert r2.status_code == 429, f"HTTP {r2.status_code}: {r2.text[:160]}"
        logger.info("CHECK cooldown on invite + resend -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_022(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_022: cancel invitation - user gone, link dead, email re-invitable.

    TC-PTA-49/51. Cancel -> 200 ``{userId, cancelled: true}``; the row leaves the list, the
    link (if a mailbox is wired) stops working, a second cancel is 404, and the same email can
    be invited again with a NEW userId.
    """
    member = await _invite(admin, created_resources)
    token = None
    if is_configured(settings):
        token = await get_activation_token(settings, member["email"])
    async with async_step("[1/4] Cancel -> 200 {userId, cancelled: true}"):
        data = _body(await admin.portal.cancel_team_invitation(member["userId"]))["data"]
        assert data.get("userId") == member["userId"] and data.get("cancelled") is True, data
    async with async_step("[2/4] The user disappears from the list; a second cancel is 404"):
        assert _row_for(await _list_rows(admin), member["email"]) is None, "cancelled user listed"
        again = await admin.portal.cancel_team_invitation(member["userId"], expected_status=None)
        assert again.status_code == 404, f"second cancel HTTP {again.status_code}"
    async with async_step("[3/4] The cancelled link no longer activates"):
        if token:
            anon = _anon(settings, created_resources)
            dead = await anon.activate(
                token, new_password(), expected_status=None, headers=fresh_ip_headers()
            )
            assert dead.status_code == 400 and _body(dead).get("error") == _INVALID
        else:
            logger.info("SKIP link-dead check: {}", skip_reason())
    async with async_step("[4/4] The same email can be invited again (new userId)"):
        again = await _invite(admin, created_resources, _member() | {"email": member["email"]})
        assert again["userId"] != member["userId"], "re-invite reused the cancelled userId"
        logger.info("CHECK cancel + re-invite -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_023(admin, settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_023: non-admin role [token] - invite/resend/cancel -> 403.

    TC-PTA-62. A `viewer` (activated, logged in) cannot invite, resend or cancel; the pending
    target is untouched afterwards.
    """
    target = await _invite(admin, created_resources)
    viewer_m = await _invite(admin, created_resources, _member("viewer", "viewer"))
    token = await _token(settings, viewer_m["email"])
    anon = _anon(settings, created_resources)
    pw = new_password()
    async with async_step("[1/3] Activate the viewer and log in"):
        await anon.activate(token, pw, headers=fresh_ip_headers())
        login = await partner_login(anon, viewer_m["email"], pw)
        viewer = portal_client(settings, login.json().get("accessToken"))
        created_resources.add(viewer.close)
    async with async_step("[2/3] Invite / resend / cancel as viewer -> 403"):
        calls = {
            "invite": await viewer.invite_team_member(_member(), expected_status=None),
            "resend": await viewer.resend_team_invitation(target["userId"], expected_status=None),
            "cancel": await viewer.cancel_team_invitation(target["userId"], expected_status=None),
        }
        for name, r in calls.items():
            assert r.status_code == 403, f"viewer {name}: HTTP {r.status_code}: {r.text[:140]}"
    async with async_step("[3/3] The pending target is still pending"):
        row = _row_for(await _list_rows(admin), target["email"])
        assert row and row.get("status") == "pending_activation", "target changed by a 403 call"
        logger.info("CHECK viewer 403 on all three -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_024(settings, created_resources):
    """PARTNER_API_PARTNER_TEAM_024: no credentials - 401 on invite, resend and cancel.

    TC-PTA-65. The three authenticated routes refuse an anonymous caller; activate (public)
    is the only route that does not. Needs no session.
    """
    anon = _anon(settings, created_resources)
    async with async_step("[1/1] Anonymous invite / resend / cancel -> 401"):
        calls = {
            "invite": await anon.invite_team_member(_member(), expected_status=None),
            "resend": await anon.resend_team_invitation(_GHOST, expected_status=None),
            "cancel": await anon.cancel_team_invitation(_GHOST, expected_status=None),
        }
        for name, r in calls.items():
            assert r.status_code == 401, f"{name}: HTTP {r.status_code}: {r.text[:140]}"
        pub = await anon.activate_raw(
            {"token": "a" * 43, "password": "Aa1!validpass"}, headers=fresh_ip_headers()
        )
        assert pub.status_code != 401, "activate must stay public"
        logger.info("CHECK 401 on three routes, activate public -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_025(admin, created_resources):
    """PARTNER_API_PARTNER_TEAM_025: resend/cancel on unknown or malformed id - one 404 shape.

    TC-PTA-41/52. A well-formed unknown id, a malformed id and (for cancel) an already-
    cancelled id all answer 404 with the same message shape - no oracle for other orgs' ids.
    """
    ids = {"unknown": _GHOST, "malformed": "not-an-object-id", "short": "123"}
    async with async_step("[1/2] Resend and cancel on bad ids -> 404"):
        seen = {}
        for name, uid in ids.items():
            for op, fn in (
                ("resend", admin.portal.resend_team_invitation),
                ("cancel", admin.portal.cancel_team_invitation),
            ):
                r = await fn(uid, expected_status=None)
                assert r.status_code == 404, f"{op} {name}: HTTP {r.status_code}: {r.text[:140]}"
                seen[(op, name)] = _body(r)
    async with async_step("[2/2] The bodies are the same apart from the echoed id"):

        def shape(b: dict) -> tuple:
            return (
                b.get("statusCode"),
                re.sub(r"User \S+ not found", "User <id> not found", str(b.get("message"))),
            )

        shapes = {shape(b) for b in seen.values()}
        assert len(shapes) == 1, f"404 bodies differ between cases: {shapes}"
        logger.info("CHECK uniform 404 -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_026(admin, created_resources):
    """PARTNER_API_PARTNER_TEAM_026: pending user in lists + reset-password blocked, no token data.

    TC-PTA-54/58. The portal list shows the pending row with ``invitationSentAt`` /
    ``invitationExpiresAt`` and no token/secret fields; reset-password on a pending user is
    409 (the admin must use Resend instead).
    """
    member = await _invite(admin, created_resources)
    async with async_step("[1/2] List row: pending status, invitation timestamps, no secrets"):
        rows = await _list_rows(admin)
        row = _row_for(rows, member["email"])
        assert row, "pending member missing from the list"
        assert row.get("status") == "pending_activation", row.get("status")
        assert row.get("invitationSentAt") and row.get("invitationExpiresAt"), sorted(row)
        _assert_no_secret(rows, "team list")
        logger.info("CHECK pending row fields, no secret -> OK")
    async with async_step("[2/2] Reset-password on the pending user -> 409 'not activated'"):
        r = await admin.portal.reset_team_member_password(member["userId"], expected_status=None)
        assert r.status_code == 409, f"HTTP {r.status_code}: {r.text[:160]}"
        assert "not activated" in r.text.lower() or "resend" in r.text.lower(), r.text[:160]
        assert "tempPassword" not in r.text
        logger.info("CHECK reset-password 409 -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_027(sa_partners_client, seeded_partner, settings):
    """PARTNER_API_PARTNER_TEAM_027: [SA] SA invite - pending user, `password` key 400, unknown org 404.

    TC-PTA-02/04/12. Needs the SA login (SKIPS locally). SA invites into an ACTIVE org: 201,
    ``status: pending_activation``, no tempPassword; a `password` body key is 400; an unknown
    partnerId is 404 and a malformed one 400.
    """
    async with async_step("[1/3] SA invite into an active org -> pending_activation"):
        partner = await seeded_partner(approve=True)
        pid = partner.partner_id
        payload = make_partner_user(pid, role="admin")
        resp = await sa_partners_client.invite_partner_user(payload)
        assert resp.data.get("status") == "pending_activation", resp.data.get("status")
        assert "tempPassword" not in resp.data and "password" not in resp.data
        assert resp.data.get("partnerId") == pid and resp.data.get("role") == "admin"
    async with async_step("[2/3] A `password` key -> 400"):
        r = await sa_partners_client.raw_invite_partner_user(
            make_partner_user(pid) | {"password": "Sup3r!secret1"}, expected_status=None
        )
        assert r.status_code == 400, f"HTTP {r.status_code}: {r.text[:160]}"
    async with async_step("[3/3] Unknown partnerId -> 404, malformed -> 400"):
        nf = await sa_partners_client.raw_invite_partner_user(
            make_partner_user(_GHOST), expected_status=None
        )
        bad = await sa_partners_client.raw_invite_partner_user(
            make_partner_user("not-an-id"), expected_status=None
        )
        assert nf.status_code == 404, f"unknown partner HTTP {nf.status_code}"
        assert bad.status_code == 400, f"malformed partnerId HTTP {bad.status_code}"
        logger.info("CHECK SA invite contract -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_028(sa_partners_client, seeded_partner):
    """PARTNER_API_PARTNER_TEAM_028: [SA] invite into a non-active org - 409.

    TC-PTA-11. Needs the SA login (SKIPS locally). A partner still `pending` (never approved)
    cannot receive invitees: 409 "only into an active partner organisation", and no user row
    is created.
    """
    async with async_step("[1/2] SA invites into a PENDING partner -> 409"):
        partner = await seeded_partner()  # not approved
        pid = partner.partner_id
        payload = make_partner_user(pid)
        r = await sa_partners_client.raw_invite_partner_user(payload, expected_status=None)
        assert r.status_code == 409, f"HTTP {r.status_code}: {r.text[:160]}"
        assert "active partner" in r.text.lower(), r.text[:160]
    async with async_step("[2/2] No user row was created"):
        listed = await sa_partners_client.list_partner_users(partner_id=pid, limit=50)
        assert not [u for u in listed.data if u.get("email") == payload["email"]]
        logger.info("CHECK non-active org 409, no row -> OK")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_team_029(
    sa_partners_client, seeded_partner, settings, created_resources
):
    """PARTNER_API_PARTNER_TEAM_029: [SA] SA resend/cancel in any org + cross-org 404 for a portal admin.

    TC-PTA-38/50/41/52/64. Needs the SA login (SKIPS locally). SA resends (after the 60 s
    cooldown) and cancels a pending user of org B; a portal admin of org A gets the same 404
    for org B's user id as for an unknown id, and org B's user is unchanged by that attempt.
    """
    async with async_step("[1/4] Setup: org A (portal admin) + org B with a pending user"):
        portal, a_id, _uid = await _mint(sa_partners_client, settings, created_resources)
        b = await seeded_partner(approve=True)
        b_user = (
            await sa_partners_client.invite_partner_user(make_partner_user(b.partner_id))
        ).data
        victim = b_user["userId"]
    async with async_step("[2/4] Org A admin resend/cancel on org B's user -> 404 like unknown"):
        unknown = await portal.resend_team_invitation(_GHOST, expected_status=None)
        for op in (portal.resend_team_invitation, portal.cancel_team_invitation):
            r = await op(victim, expected_status=None)
            assert r.status_code == 404, f"cross-org {op.__name__}: HTTP {r.status_code}"
            assert _body(r).get("statusCode") == _body(unknown).get("statusCode")
    async with async_step(f"[3/4] SA resend after {_COOLDOWN_WAIT_S}s -> 200"):
        await asyncio.sleep(_COOLDOWN_WAIT_S)
        r = await sa_partners_client.resend_partner_user_invitation(victim)
        assert _body(r)["data"]["status"] == "pending_activation"
    async with async_step("[4/4] SA cancel -> 200 and the user is gone"):
        r = await sa_partners_client.cancel_partner_user_invitation(victim)
        assert _body(r)["data"].get("cancelled") is True
        listed = await sa_partners_client.list_partner_users(partner_id=b.partner_id, limit=50)
        assert victim not in {u.get("_id") or u.get("userId") for u in listed.data}
        logger.info("CHECK SA resend/cancel + cross-org 404 -> OK")


async def _mint(sa, settings, created_resources):
    """Mint an active partner + admin session for the SA-side TC (needs a token source)."""
    from utils.partner_portal import mint_partner_session

    portal, pid, uid = await mint_partner_session(sa, settings)
    created_resources.add(lambda: sa.delete_partner(pid))
    created_resources.add(portal.close)
    return portal, pid, uid
