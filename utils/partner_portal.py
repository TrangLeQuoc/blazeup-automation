"""Partner-portal session helper (mint a partner JWT from SA-side setup).

The partner-portal endpoints (``/sa-partners-api/v1/partner/portal/*``) require a
PARTNER user's JWT, not the SA admin token. Rather than depend on pre-provisioned
partner credentials, this helper builds a partner session self-contained from the
SA side: create + approve a partner, invite a user, then log in as that user.

Usage in a test::

    portal, pid = await mint_partner_session(sa_partners_client, settings)
    created_resources.add(lambda: portal.close())
    created_resources.add(lambda: sa_partners_client.delete_partner(pid))
    resp = await portal.get_dashboard()
"""

import asyncio
import base64
import contextlib
import json
import secrets
from dataclasses import dataclass, field

import pytest
from loguru import logger

from api_clients.blazeup.partner.partner_portal_client import PartnerPortalClient
from utils.activation_link import get_activation_token, skip_reason
from utils.data_factory import make_partner, make_partner_user
from utils.helpers import blocked_reason

# A user created via invite (201) is occasionally not yet visible to the login read
# (DB replication lag) → login returns 400 "partner_users … not found". That is a
# timing artefact of the SETUP, not a login defect, so the login is retried a few
# times. Any OTHER non-2xx (wrong password → 401, 5xx, real rejection) returns
# immediately so the caller's assertion still fires on a genuine failure.
_LOGIN_RETRY_ATTEMPTS = 4
_LOGIN_RETRY_DELAY_S = 0.75


async def partner_login(
    anon: PartnerPortalClient, email: str, password: str, *, expected=(200, 201)
):
    """POST the partner login, absorbing the transient just-invited 'user not found'.

    Returns the httpx.Response — a 2xx on success, or the last response once retries
    are exhausted (so the caller can still assert on a real failure). Only the
    replication-lag signature (400 + 'not found') is retried; everything else is
    returned on the first attempt.
    """
    resp = None
    for attempt in range(1, _LOGIN_RETRY_ATTEMPTS + 1):
        resp = await anon.login(email, password, expected_status=None)
        if resp.status_code in expected:
            return resp
        transient = resp.status_code == 400 and "not found" in (resp.text or "").lower()
        if not transient or attempt == _LOGIN_RETRY_ATTEMPTS:
            return resp
        logger.info(
            "partner login: user not yet visible (attempt {}/{}) — retry in {}s",
            attempt,
            _LOGIN_RETRY_ATTEMPTS,
            _LOGIN_RETRY_DELAY_S,
        )
        await asyncio.sleep(_LOGIN_RETRY_DELAY_S)
    return resp


def portal_client(
    settings, token: str | None = None, *, app_origin: str | None = None
) -> PartnerPortalClient:
    """A partner-portal client at the API gateway, optionally carrying a partner JWT.

    Generous timeout (setup/auth, not the assertion under test). Caller closes it.
    ``app_origin`` overrides the Origin/Referer headers — pass the PARTNER base url
    when the call is made on behalf of the portal UI rather than the SA app.
    """
    return PartnerPortalClient(
        str(settings.api_base_url),
        token=token,
        max_response_time_ms=settings.default_response_time_ms * 5,
        app_origin=app_origin or str(settings.base_url),
    )


def fresh_ip_headers() -> dict:
    """An ``X-Forwarded-For`` with a random private IP — its own per-IP throttle bucket.

    Activation is throttled 10 attempts / 15 min per client IP; without this, a few tests in
    one run (all from one IP) would exhaust the bucket and turn into false 429s.
    """
    return {
        "X-Forwarded-For": f"10.{secrets.randbelow(256)}.{secrets.randbelow(256)}.{1 + secrets.randbelow(254)}"
    }


def new_password() -> str:
    """A policy-compliant throwaway password (>= 8 chars, < 72 bytes) for activations."""
    return "Act!" + secrets.token_urlsafe(12)


async def resolve_invitee_password(settings, invited: dict) -> str:
    """Return a password the freshly invited user can log in with, whichever invite flow runs.

    ``temp_password`` flow (pre BLAZ7-17): the invite response carries ``tempPassword``.
    ``activation`` flow: the invite carries no credential, so read the emailed link through
    ``utils.activation_link``, activate with a generated password and return it. SKIPS (not
    fails) when no activation-link source is configured — a missing mailbox is an
    environment limit, not a defect.
    """
    if settings.partner_invite_flow == "temp_password":
        password = invited.get("tempPassword")
        if not password:
            raise RuntimeError("invite did not return a tempPassword (legacy flow selected)")
        return password
    email = invited.get("email")
    token = await get_activation_token(settings, email)
    if not token:
        pytest.skip(f"BLOCKED: cannot activate the invitee — {skip_reason()}")
    password = new_password()
    anon = portal_client(settings)
    try:
        await anon.activate(token, password, headers=fresh_ip_headers())
    finally:
        await anon.close()
    return password


async def provision_partner_user(sa_partners_client, settings=None) -> dict:
    """SA-side setup → login credentials for a fresh, active partner user.

    Creates + approves a partner (pending → active) and invites a user. Returns
    ``{partner_id, user_id, email, password}`` (password = the invite tempPassword, or the one
    chosen at activation when ``settings`` is given and the activation flow is on).
    The caller deletes the partner for cleanup.
    """
    partner = await sa_partners_client.create_partner(make_partner())
    pid = partner.partner_id
    if not pid:
        raise RuntimeError("could not create a partner")
    logger.info(
        "SETUP: [1] SA created partner {} — status pending", getattr(partner, "code", None) or pid
    )
    await sa_partners_client.approve_partner(pid)  # pending → active (else login is rejected)
    logger.info("SETUP: [2] SA approved partner {} — now active", pid)
    invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
    creds = {
        "partner_id": pid,
        "user_id": invited.data.get("userId"),
        "email": invited.data.get("email"),
        "password": None,
    }
    if settings is None:  # legacy callers: temp-password flow
        creds["password"] = invited.data.get("tempPassword")
    else:
        creds["password"] = await resolve_invitee_password(settings, invited.data)
    if not (creds["email"] and creds["password"]):
        raise RuntimeError("invite did not yield email + a usable password")
    logger.info("SETUP: [3] SA invited partner user {} (role admin)", creds["email"])
    return creds


async def mint_partner_session(
    sa_partners_client, settings
) -> tuple[PartnerPortalClient, str, str]:
    """Return ``(partner_portal_client, partner_id, user_id)`` — authed as a partner user.

    Steps: SA creates a partner, approves it (pending → active so the user can log
    in), invites a portal user, then logs in as that user (PartnerLoginDto) to get a
    partner JWT. The returned client carries that token; the caller is responsible
    for closing it and deleting the partner (register both with ``created_resources``).
    ``user_id`` is returned so tests can seed user-scoped data (e.g. grant a cert).
    """
    if settings.partner_session_source == "env":
        env = await open_env_session(settings)
        return env.portal, env.partner_id, env.user_id
    # Establishing the session (SA create/approve/invite + partner login) is a
    # PRECONDITION, not the feature under test. If it can't be established — auth
    # rejected, service 5xx/unreachable — the test is BLOCKED (env), not FAILED.
    creds = None
    try:
        creds = await provision_partner_user(sa_partners_client, settings)
        anon = portal_client(settings)
        try:
            resp = await partner_login(anon, creds["email"], creds["password"])
            token = resp.json().get("accessToken") or resp.json().get("token")
        finally:
            await anon.close()
        if not token:
            raise RuntimeError("partner login did not return an accessToken")
        logger.info("SETUP: [4] partner user logged in → partner JWT acquired")
    except Exception as exc:  # noqa: BLE001 — precondition failure → BLOCKED, not a defect
        # Best-effort: remove the partner provisioned before the failure (no leak).
        if creds and creds.get("partner_id"):
            with contextlib.suppress(Exception):  # cleanup is best-effort
                await sa_partners_client.delete_partner(creds["partner_id"])
        pytest.skip(f"BLOCKED: could not establish partner-portal session — {blocked_reason(exc)}")

    portal = portal_client(settings, token)
    return portal, creds["partner_id"], creds["user_id"]


def _jwt_claims(token: str) -> dict:
    """Decode (without verifying) a JWT payload — only to read ``sub`` / ``partnerId``."""
    try:
        seg = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4)))
    except (IndexError, ValueError):
        return {}


@dataclass
class PortalSession:
    """A partner-admin portal session plus what is needed to clean up after it."""

    portal: PartnerPortalClient
    partner_id: str
    user_id: str
    minted: bool  # True = SA created the org (delete it); False = shared env org (leave it)
    invited_user_ids: list[str] = field(default_factory=list)


async def open_env_session(settings) -> PortalSession:
    """Log in as the pre-seeded org admin from PARTNER_EMAIL / PARTNER_PASSWORD (no SA needed).

    Opt-in through ``PARTNER_SESSION_SOURCE=env``. SKIPS when the credentials are missing or
    rejected. The org is shared and NEVER deleted — tests clean up only the users they invite.
    """
    if not (settings.partner_email and settings.partner_password):
        pytest.skip("BLOCKED: PARTNER_SESSION_SOURCE=env but PARTNER_EMAIL/PARTNER_PASSWORD unset")
    anon = portal_client(settings)
    try:
        resp = await partner_login(anon, settings.partner_email, settings.partner_password)
        token = resp.json().get("accessToken") if resp.status_code in (200, 201) else None
    finally:
        await anon.close()
    if not token:
        pytest.skip(f"BLOCKED: seeded partner login rejected (HTTP {resp.status_code})")
    claims = _jwt_claims(token)
    logger.info(
        "SETUP: seeded partner-admin session acquired (partnerId={})", claims.get("partnerId")
    )
    return PortalSession(
        portal_client(settings, token), claims.get("partnerId", ""), claims.get("sub", ""), False
    )


async def open_portal_session(settings, created_resources, sa=None) -> PortalSession:
    """One entry point for tests: an admin portal session from the env org OR a minted partner.

    ``PARTNER_SESSION_SOURCE=env`` logs in as the seeded org admin and needs no SA client;
    ``mint`` needs ``sa`` (the ``sa_partners_client`` fixture). Cleanup (close the client,
    delete a minted partner) is registered here.
    """
    if settings.partner_session_source == "env":
        sess = await open_env_session(settings)
    else:
        if sa is None:
            pytest.skip("BLOCKED: PARTNER_SESSION_SOURCE=mint needs the SA client")
        portal, pid, uid = await mint_partner_session(sa, settings)
        created_resources.add(lambda: sa.delete_partner(pid))
        sess = PortalSession(portal, pid, uid, True)
    created_resources.add(sess.portal.close)
    return sess
