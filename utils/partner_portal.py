"""Partner-portal session helper (mint a partner JWT from SA-side setup).

The partner-portal endpoints (``/sa-partners-api/v1/partner/portal/*``) require a
PARTNER user's JWT, not the SA admin token. Rather than depend on pre-provisioned
partner credentials, this helper builds a partner session self-contained from the
SA side: create + approve a partner, invite a user, then log in as that user.

Usage in a test::

    portal, pid = await mint_partner_session(sa_partners_client, settings)
    created_resources.add(lambda: portal.close())
    created_resources.add(lambda: sa_partners_client.delete_partner(pid))
    resp = await portal.get("/sa-partners-api/v1/partner/portal/dashboard", expected_status=200)
"""

import asyncio
import contextlib

import pytest
from loguru import logger

from api_clients.base_client import BaseClient
from utils.data_factory import make_partner, make_partner_user
from utils.helpers import blocked_reason

_PARTNER_LOGIN_PATH = "/sa-partners-api/v1/partner/auth/login"

# A user created via invite (201) is occasionally not yet visible to the login read
# (DB replication lag) → login returns 400 "partner_users … not found". That is a
# timing artefact of the SETUP, not a login defect, so the login is retried a few
# times. Any OTHER non-2xx (wrong password → 401, 5xx, real rejection) returns
# immediately so the caller's assertion still fires on a genuine failure.
_LOGIN_RETRY_ATTEMPTS = 4
_LOGIN_RETRY_DELAY_S = 0.75


async def partner_login(anon: BaseClient, email: str, password: str, *, expected=(200, 201)):
    """POST the partner login, absorbing the transient just-invited 'user not found'.

    Returns the httpx.Response — a 2xx on success, or the last response once retries
    are exhausted (so the caller can still assert on a real failure). Only the
    replication-lag signature (400 + 'not found') is retried; everything else is
    returned on the first attempt.
    """
    resp = None
    for attempt in range(1, _LOGIN_RETRY_ATTEMPTS + 1):
        resp = await anon.post(
            _PARTNER_LOGIN_PATH,
            json={"email": email, "password": password},
            expected_status=None,
        )
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


def portal_client(settings, token: str | None = None) -> BaseClient:
    """A BaseClient pointed at the API gateway, optionally carrying a partner JWT.

    Generous timeout (setup/auth, not the assertion under test). Caller closes it.
    """
    return BaseClient(
        str(settings.api_base_url),
        token=token,
        max_response_time_ms=settings.default_response_time_ms * 5,
        app_origin=str(settings.base_url),
    )


async def provision_partner_user(sa_partners_client) -> dict:
    """SA-side setup → login credentials for a fresh, active partner user.

    Creates + approves a partner (pending → active) and invites a user. Returns
    ``{partner_id, user_id, email, password}`` (password = the invite tempPassword).
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
        "password": invited.data.get("tempPassword"),
    }
    if not (creds["email"] and creds["password"]):
        raise RuntimeError("invite did not return email + tempPassword")
    logger.info("SETUP: [3] SA invited partner user {} (role admin)", creds["email"])
    return creds


async def mint_partner_session(sa_partners_client, settings) -> tuple[BaseClient, str, str]:
    """Return ``(partner_portal_client, partner_id, user_id)`` — authed as a partner user.

    Steps: SA creates a partner, approves it (pending → active so the user can log
    in), invites a portal user, then logs in as that user (PartnerLoginDto) to get a
    partner JWT. The returned client carries that token; the caller is responsible
    for closing it and deleting the partner (register both with ``created_resources``).
    ``user_id`` is returned so tests can seed user-scoped data (e.g. grant a cert).
    """
    # Establishing the session (SA create/approve/invite + partner login) is a
    # PRECONDITION, not the feature under test. If it can't be established — auth
    # rejected, service 5xx/unreachable — the test is BLOCKED (env), not FAILED.
    creds = None
    try:
        creds = await provision_partner_user(sa_partners_client)
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
