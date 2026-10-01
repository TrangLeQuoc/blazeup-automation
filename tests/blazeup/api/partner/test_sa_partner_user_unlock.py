"""SA unlock of a partner user — POST /v1/sa/partner-users/:userId/unlock (sa-partners-api).

Maps to the test plan: PARTNER_API_PARTNER_USERS_015 / _016. PRD §5.1.

The SA-side twin of the portal's `/v1/partner/directory/users/:userId/unlock` (covered by
PARTNER_TEAM_005): that one lets a partner admin unlock someone in their own org, this one
lets SA unlock any partner user, and both clear the login AND MFA lockouts together.

Two things shape these TCs:

* **The response code proves nothing.** Measured 2026-09-24: calling unlock on a user who is
  not locked still answers 200. So _015 locks the account first and then shows the login
  works again — the effect, not the status code.
* **The threshold is undocumented.** §9.1 does not mention lockout and §5.1 does not mention
  unlock; 4 consecutive failures / 30 minutes is a MEASURED value, not a specified one, so the
  TC discovers it at run time instead of hard-coding it. Raised as OQ-28.

⚠️ Throwaway users only. Locking the shared portal account blocks every other partner test for
half an hour.
"""

import pytest
from loguru import logger

from utils.data_factory import make_partner_user
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session, partner_login, portal_client

# Cap on the discovery loop: high enough to find a threshold well above the measured 4,
# low enough that an unthrottled endpoint fails fast instead of hammering staging.
_LOCKOUT_PROBE_MAX = 8
_WRONG_PASSWORD = "QA-AUTO WrongPassword!123"
_GHOST = "000000000000000000000000"


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_015(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_USERS_015: SA unlocks a locked partner user - login works again.

    Proves the unlock by EFFECT, end to end: a throwaway user logs in, is locked out by
    repeated wrong passwords, is refused even with the CORRECT password while locked, and can
    log in again only after SA calls unlock. Asserting the 200 alone would pass against an
    endpoint that does nothing, because unlock answers 200 on an unlocked user too.

    The lockout threshold is discovered rather than assumed — it is not specified anywhere
    (OQ-28), so the TC reports the number it measured instead of pinning one.

    Precondition: an ACTIVE partner and a THROWAWAY user on it, never the shared account.
    """
    async with async_step(
        "[1/6] Setup: an active partner + a throwaway user with a known password"
    ):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        invited = await sa_partners_client.invite_partner_user(make_partner_user(partner_id))
        victim = invited.data
        email, password = victim.get("email"), victim.get("tempPassword")
        user_id = victim.get("userId")
        assert email and password and user_id, f"invite did not return usable creds: {victim}"

        anon = portal_client(settings)
        created_resources.add(anon.close)
        logger.info("SETUP: partner={} throwaway user={} ({})", partner_id, user_id, email)

    async with async_step("[2/6] Baseline: the throwaway user can log in"):
        resp = await partner_login(anon, email, password)
        assert resp.status_code == 200, (
            f"the invited user cannot log in with its own tempPassword (HTTP "
            f"{resp.status_code}) — the fixture is broken, not the endpoint under test"
        )
        logger.info("CHECK baseline login → 200 → OK")

    async with async_step("[3/6] Wrong passwords lock the account — measure the threshold"):
        locked_at = None
        for attempt in range(1, _LOCKOUT_PROBE_MAX + 1):
            resp = await partner_login(anon, email, _WRONG_PASSWORD)
            if "too many failed" in resp.text.lower():
                locked_at = attempt
                break
        assert locked_at, (
            f"{_LOCKOUT_PROBE_MAX} consecutive wrong passwords did not lock the account. There "
            "is then nothing for unlock to clear, and partner login is unthrottled against "
            "brute force. Confirm with BE — the policy is unspecified (OQ-28)"
        )
        logger.info("CHECK locked after {} wrong attempt(s) → OK", locked_at)

    async with async_step("[4/6] While locked, even the CORRECT password is refused"):
        resp = await partner_login(anon, email, password)
        assert resp.status_code != 200, (
            "the correct password still authenticates while the account is locked — the "
            "lockout is cosmetic and does not actually stop an attacker who then guesses right"
        )
        logger.info("CHECK correct password refused while locked → {} → OK", resp.status_code)

    async with async_step("[5/6] SA unlocks the user"):
        resp = await sa_partners_client.unlock_partner_user(user_id)
        body = resp.json()
        assert (body.get("data") or {}).get("userId") == user_id, (
            f"unlock answered about a different user: {body}"
        )
        assert body.get("message"), "the unlock response carries no `message`"
        logger.info("CHECK unlock accepted → OK ({})", body.get("message"))

    async with async_step("[6/6] The user can log in again — the effect, not the status code"):
        resp = await partner_login(anon, email, password)
        assert resp.status_code == 200, (
            f"unlock returned success but the user still cannot log in (HTTP "
            f"{resp.status_code}). The endpoint reported an outcome it did not deliver — this "
            "is the assertion the TC exists for, because unlock answers 200 even when it "
            "clears nothing"
        )
        logger.info("CHECK login works again after unlock → 200 → OK")

    logger.info(
        "RESULT: SA unlock verified by effect — locked at {} attempts, cleared, login restored",
        locked_at,
    )


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_users_016(sa_partners_client, settings, created_resources):
    """PARTNER_API_PARTNER_USERS_016: SA unlock invalid target and repeat call - correct handling.

    Negative counterpart of _015: a user id that does not exist, one that is not an id at all,
    and the repeat case.

    The repeat is the interesting one. Unlock is a mutating action rather than a create, so
    rule 8's 409-or-idempotent formula does not apply blindly — the question is what the BE
    intends when there is nothing to clear. Measured 2026-09-24: it answers 200. That is
    asserted as the documented behaviour, together with the property that matters more than
    the code — a redundant unlock must not leave the account in a worse state than it found it.

    All cases run and failures are collected.
    """
    async with async_step("[1/4] Setup: an active partner + a throwaway user"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        invited = await sa_partners_client.invite_partner_user(make_partner_user(partner_id))
        victim = invited.data
        email, password = victim.get("email"), victim.get("tempPassword")
        user_id = victim.get("userId")
        assert email and password and user_id, f"invite did not return usable creds: {victim}"
        anon = portal_client(settings)
        created_resources.add(anon.close)
        logger.info("SETUP: partner={} throwaway user={}", partner_id, user_id)

    gaps: list[str] = []

    async with async_step(
        "[2/4] A well-formed user id that does not exist → 4xx naming it", soft=gaps
    ):
        resp = await sa_partners_client.unlock_partner_user(_GHOST, expected_status=None)
        if resp.status_code < 400:
            gaps.append(
                f"unlocking a ghost user answered {resp.status_code} — a no-op success on an "
                "id that cannot exist hides typos from the SA operator"
            )
        elif resp.status_code >= 500:
            gaps.append(f"unlocking a ghost user crashed the service ({resp.status_code})")
        elif _GHOST not in resp.text and "not found" not in resp.text.lower():
            gaps.append(f"the {resp.status_code} does not say which user was not found")
        else:
            logger.info("CHECK ghost userId → {} naming it → OK", resp.status_code)

    async with async_step("[3/4] A user id that is not an id at all → 400", soft=gaps):
        resp = await sa_partners_client.unlock_partner_user("not-an-id", expected_status=None)
        if resp.status_code != 400:
            gaps.append(f"a malformed userId answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed userId → 400 → OK")

    async with async_step(
        "[4/4] Unlocking a user who is NOT locked is a harmless no-op", soft=gaps
    ):
        first = await sa_partners_client.unlock_partner_user(user_id, expected_status=None)
        if first.status_code != 200:
            gaps.append(
                f"unlocking a user who is not locked answered {first.status_code}; the measured "
                "behaviour is 200 (a no-op), so a different code here is a contract change"
            )
        second = await sa_partners_client.unlock_partner_user(user_id, expected_status=None)
        if second.status_code != first.status_code:
            gaps.append(
                f"two identical unlock calls answered differently ({first.status_code} then "
                f"{second.status_code}) — the operation is not idempotent"
            )
        # The property that matters more than the status code: a redundant unlock must not
        # damage an account that was fine to begin with.
        resp = await partner_login(anon, email, password)
        if resp.status_code != 200:
            gaps.append(
                f"after two redundant unlocks the user can no longer log in (HTTP "
                f"{resp.status_code}) — unlock altered an account that needed no change"
            )
        else:
            logger.info("CHECK redundant unlock → {} twice, login intact → OK", first.status_code)

    assert not gaps, "Gaps on SA unlock:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid targets refused, redundant unlock harmless and idempotent")
