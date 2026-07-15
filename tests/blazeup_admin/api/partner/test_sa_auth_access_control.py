"""Partner Auth & Access Control API (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_AUTH_ACCESS_CONTROL_*.

The mandatory auth feature (test-organization §6 rule 5): a valid partner JWT
authorizes; a non-partner / missing token is rejected (401); refresh / logout /
change-password behave correctly. Sessions are minted self-contained from the SA
side via ``utils.partner_portal``. No billing plan → no sa-plans dependency.

Auth flows are not resource-creates → no duplicate-create idempotency TC; each TC
embeds its own negative aspect (rejection / invalidation).
"""

import pytest
from loguru import logger

from utils.data_factory import make_deal, make_prospect
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session, portal_client, provision_partner_user

_AUTH = "/sa-partners-api/v1/partner/auth"
_PORTAL = "/sa-partners-api/v1/partner/portal"
_NEW_PASSWORD = "QA-Auto-New-9!xZ"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_001(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_001: valid partner JWT - a partner-scoped request succeeds.

    A user logged in with a valid partner JWT can call a partner-scoped endpoint
    (GET /partner/auth/me) and receives HTTP 200 with their identity.
    """
    async with async_step("Setup: provision a partner user + log in"):
        creds = await provision_partner_user(sa_partners_client)
        created_resources.add(lambda: sa_partners_client.delete_partner(creds["partner_id"]))
        anon = portal_client(settings)
        created_resources.add(lambda: anon.close())
        login = await anon.post(
            f"{_AUTH}/login",
            json={"email": creds["email"], "password": creds["password"]},
            expected_status=(200, 201),
        )
        token = login.json().get("accessToken")
        assert token, "login must return an accessToken"
        portal = portal_client(settings, token)
        created_resources.add(lambda: portal.close())
        logger.info(
            "SETUP: [4] partner user logged in → partner JWT acquired (partner {})",
            creds["partner_id"],
        )

    async with async_step("[1/1] A partner-scoped request with the JWT succeeds"):
        resp = await portal.get(f"{_AUTH}/me", expected_status=200)
        body = resp.json()  # /me returns the identity at the top level (no `data` wrapper)
        assert body.get("userId") and body.get("email"), (
            "/me must return the authenticated identity"
        )
        logger.info("CHECK authorized → OK (200, identity userId={})", body.get("userId"))

    logger.info("RESULT: valid partner JWT authorizes partner-scoped requests")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_002(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_002: non-partner / missing token on the partner API - 401.

    The partner API rejects a request with no token and a request bearing a
    non-partner (SA admin) token — both with HTTP 401.
    """
    async with async_step("[1/2] No token → 401"):
        anon = portal_client(settings)
        created_resources.add(lambda: anon.close())
        r = await anon.get(f"{_AUTH}/me", expected_status=None)
        assert r.status_code == 401, f"a no-token request must be 401, got {r.status_code}"
        logger.info("CHECK no-token → OK (401)")

    async with async_step("[2/2] Non-partner (SA admin) token → 401"):
        r = await sa_partners_client.get(f"{_AUTH}/me", expected_status=None)
        assert r.status_code == 401, f"a non-partner token must be 401, got {r.status_code}"
        logger.info("CHECK non-partner token → OK (401)")

    logger.info("RESULT: partner API rejects missing / non-partner tokens (401)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_007(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_007: valid refresh token - a new access token is issued.

    Refreshing with a valid refreshToken returns a new accessToken (without re-login)
    that authorizes requests; an invalid refresh token is rejected (401).
    """
    async with async_step("Setup: provision + log in (capture access + refresh tokens)"):
        creds = await provision_partner_user(sa_partners_client)
        created_resources.add(lambda: sa_partners_client.delete_partner(creds["partner_id"]))
        anon = portal_client(settings)
        created_resources.add(lambda: anon.close())
        login = await anon.post(
            f"{_AUTH}/login",
            json={"email": creds["email"], "password": creds["password"]},
            expected_status=(200, 201),
        )
        body = login.json()
        access, refresh = body.get("accessToken"), body.get("refreshToken")
        assert access and refresh, "login must return access + refresh tokens"

    async with async_step("[1/3] Refresh → a new access token (different from the original)"):
        r = await anon.post(f"{_AUTH}/refresh", json={"refreshToken": refresh}, expected_status=200)
        new_access = r.json().get("accessToken")
        assert new_access, "refresh must return a new accessToken"
        assert new_access != access, "the refreshed access token must differ from the original"
        logger.info("CHECK refresh → OK (200, new access token issued)")

    async with async_step("[2/3] The new access token authorizes a request"):
        refreshed = portal_client(settings, new_access)
        created_resources.add(lambda: refreshed.close())
        me = await refreshed.get(f"{_AUTH}/me", expected_status=200)
        assert me.json().get("userId"), "the refreshed token must authorize /me"
        logger.info("CHECK new-token works → OK (200)")

    async with async_step("[3/3] An invalid refresh token is rejected (401)"):
        bad = await anon.post(
            f"{_AUTH}/refresh", json={"refreshToken": "not-a-valid-token"}, expected_status=None
        )
        assert bad.status_code == 401, (
            f"an invalid refresh token must be 401, got {bad.status_code}"
        )
        logger.info("CHECK invalid-refresh → OK (401)")

    logger.info("RESULT: refresh issues a working new access token; invalid refresh rejected")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_008(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_008: logout - the refresh token is invalidated.

    After logout, the previously valid refresh token can no longer mint a new access
    token (401) — the session is invalidated.
    """
    async with async_step("Setup: provision + log in (capture refresh token)"):
        creds = await provision_partner_user(sa_partners_client)
        created_resources.add(lambda: sa_partners_client.delete_partner(creds["partner_id"]))
        anon = portal_client(settings)
        created_resources.add(lambda: anon.close())
        login = await anon.post(
            f"{_AUTH}/login",
            json={"email": creds["email"], "password": creds["password"]},
            expected_status=(200, 201),
        )
        body = login.json()
        access, refresh = body.get("accessToken"), body.get("refreshToken")
        assert access and refresh, "login must return access + refresh tokens"
        portal = portal_client(settings, access)
        created_resources.add(lambda: portal.close())

    async with async_step("[1/2] Logout the active session"):
        r = await portal.post(f"{_AUTH}/logout", json={}, expected_status=(200, 204))
        logger.info("CHECK logout → OK ({})", r.status_code)

    async with async_step("[2/2] The refresh token is now invalidated (401)"):
        r = await anon.post(
            f"{_AUTH}/refresh", json={"refreshToken": refresh}, expected_status=None
        )
        assert r.status_code == 401, (
            f"refresh after logout must be rejected (401), got {r.status_code}"
        )
        logger.info("CHECK invalidated → OK (refresh after logout → 401)")

    logger.info("RESULT: logout invalidates the refresh token")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_009(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_009: change password - new credentials work, old fail.

    With a valid session, a wrong currentPassword is rejected; the correct
    currentPassword updates the password (204); afterwards the NEW password logs in
    and the OLD password is rejected (401).
    """
    async with async_step("Setup: provision + log in"):
        creds = await provision_partner_user(sa_partners_client)
        created_resources.add(lambda: sa_partners_client.delete_partner(creds["partner_id"]))
        anon = portal_client(settings)
        created_resources.add(lambda: anon.close())
        login = await anon.post(
            f"{_AUTH}/login",
            json={"email": creds["email"], "password": creds["password"]},
            expected_status=(200, 201),
        )
        portal = portal_client(settings, login.json().get("accessToken"))
        created_resources.add(lambda: portal.close())

    async with async_step("[1/4] Wrong currentPassword is rejected"):
        r = await portal.post(
            f"{_AUTH}/change-password",
            json={"currentPassword": "WrongPass-0!xZ", "newPassword": _NEW_PASSWORD},
            expected_status=None,
        )
        assert 400 <= r.status_code < 500, f"wrong currentPassword must be 4xx, got {r.status_code}"
        logger.info("CHECK wrong-current → OK ({})", r.status_code)

    async with async_step("[2/4] Correct currentPassword updates the password (204)"):
        r = await portal.post(
            f"{_AUTH}/change-password",
            json={"currentPassword": creds["password"], "newPassword": _NEW_PASSWORD},
            expected_status=(200, 204),
        )
        logger.info("CHECK change → OK ({})", r.status_code)

    async with async_step("[3/4] The NEW password logs in"):
        r = await anon.post(
            f"{_AUTH}/login",
            json={"email": creds["email"], "password": _NEW_PASSWORD},
            expected_status=None,
        )
        assert r.status_code in (200, 201) and r.json().get("accessToken"), (
            f"new password must log in, got {r.status_code}"
        )
        logger.info("CHECK new-password login → OK")

    async with async_step("[4/4] The OLD password is rejected (401)"):
        r = await anon.post(
            f"{_AUTH}/login",
            json={"email": creds["email"], "password": creds["password"]},
            expected_status=None,
        )
        assert r.status_code == 401, f"old password must be rejected (401), got {r.status_code}"
        logger.info("CHECK old-password rejected → OK (401)")

    logger.info("RESULT: change-password updates credentials (new works, old rejected)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_003(
    sa_partners_client, sa_deals_client, settings, created_resources
):
    """PARTNER_API_AUTH_ACCESS_CONTROL_003: cross-partner access - a partner cannot read another's deal.

    Partner A registers a deal; partner B (a separate session) requests A's deal by id
    via the partner portal and is refused (4xx) — A's deal is never exposed to B. This
    is the rule-5 cross-entity (tenant-isolation) auth case.
    """
    async with async_step("Setup: partner A registers a deal; partner B in a separate session"):
        portal_a, pid_a, _ = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal_a.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid_a))
        plan_id = await sa_deals_client.pick_billing_plan_id()
        created_a = await portal_a.post(
            f"{_PORTAL}/deals",
            json=make_deal(None, plan_id, **make_prospect()),
            expected_status=(200, 201),
        )
        a_deal_id = (created_a.json().get("data") or {}).get("_id")
        assert a_deal_id, "precondition: partner A must have a deal"

        portal_b, pid_b, _ = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: portal_b.close())
        created_resources.add(lambda: sa_partners_client.delete_partner(pid_b))
        logger.info("SETUP: A={} deal={} ; B={}", pid_a, a_deal_id, pid_b)

    async with async_step("[1/1] Partner B requests partner A's deal → refused, no leak"):
        r = await portal_b.get(f"{_PORTAL}/deals/{a_deal_id}", expected_status=None)
        assert 400 <= r.status_code < 500, (
            f"cross-partner deal access must be refused (4xx), got {r.status_code}"
        )
        data = r.json().get("data") or {}
        assert (data.get("_id") or data.get("id")) != a_deal_id, (
            "partner A's deal must NOT be exposed to partner B"
        )
        logger.info("CHECK cross-partner → OK ({} — A's deal not exposed to B)", r.status_code)

    logger.info("RESULT: a partner cannot access another partner's deal (tenant-isolated)")
