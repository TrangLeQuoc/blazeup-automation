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

from api_clients.base_client import BaseClient
from utils.data_factory import make_partner, make_partner_user

_PARTNER_LOGIN_PATH = "/sa-partners-api/v1/partner/auth/login"


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
    await sa_partners_client.approve_partner(pid)  # pending → active (else login is rejected)
    invited = await sa_partners_client.invite_partner_user(make_partner_user(pid))
    creds = {
        "partner_id": pid,
        "user_id": invited.data.get("userId"),
        "email": invited.data.get("email"),
        "password": invited.data.get("tempPassword"),
    }
    if not (creds["email"] and creds["password"]):
        raise RuntimeError("invite did not return email + tempPassword")
    return creds


async def mint_partner_session(sa_partners_client, settings) -> tuple[BaseClient, str, str]:
    """Return ``(partner_portal_client, partner_id, user_id)`` — authed as a partner user.

    Steps: SA creates a partner, approves it (pending → active so the user can log
    in), invites a portal user, then logs in as that user (PartnerLoginDto) to get a
    partner JWT. The returned client carries that token; the caller is responsible
    for closing it and deleting the partner (register both with ``created_resources``).
    ``user_id`` is returned so tests can seed user-scoped data (e.g. grant a cert).
    """
    creds = await provision_partner_user(sa_partners_client)
    anon = portal_client(settings)
    try:
        resp = await anon.post(
            _PARTNER_LOGIN_PATH,
            json={"email": creds["email"], "password": creds["password"]},
            expected_status=(200, 201),
        )
        token = resp.json().get("accessToken") or resp.json().get("token")
    finally:
        await anon.close()
    if not token:
        raise RuntimeError("partner login did not return an accessToken")

    portal = portal_client(settings, token)
    return portal, creds["partner_id"], creds["user_id"]
