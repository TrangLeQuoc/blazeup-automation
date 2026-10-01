"""Partner self-service password reset — POST /v1/partner/auth/forgot-password.

Maps to the test plan: PARTNER_API_AUTH_ACCESS_CONTROL_010 / _011. PRD §9.1.

This endpoint was recorded "không build được — không đọc được inbox" on 2026-09-16. That was
wrong, and the source says why: `forgotPassword` rotates the password and only THEN mails it
(`partner-auth.service.ts:798` → `generateTempPassword` → `updateUserPassword`). The effect is
therefore observable without a mailbox — the old password stops working — exactly as
PARTNER_TEAM_005 proves the admin-driven reset.

Two further properties need no inbox either, and both are security properties rather than
conveniences:

* **No user enumeration.** A registered and an unknown email must be indistinguishable. The
  service returns early for an unknown or ineligible user — "silent no-op: no email, no write,
  no audit" — and the controller never branches on the outcome.
* **Rate limiting.** 5 per email and 20 per client IP in a 15-minute window.

⚠️ The IP budget is shared. This module spends ~9 calls per full run, so two back-to-back runs
fit inside 20 but a third within the same 15 minutes will start seeing 429s. _011 is written to
treat an early 429 as proof the limit exists rather than as a failure.
"""

import pytest
from loguru import logger

from utils.data_factory import make_partner_user, unique_email
from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session, partner_login, portal_client

# The exact text the controller returns for every outcome (partner-auth.controller.ts:40).
_GENERIC = "If an account exists for that email, we've sent password-reset instructions."
# assertForgotQuota: 5 per email, 20 per IP, 15-minute window.
_MAX_PER_EMAIL = 5
_PROBE_CAP = _MAX_PER_EMAIL + 2


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_010(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_010: forgot-password rotates the credential - old one dies.

    Proven by effect, no mailbox needed: a throwaway user logs in, SA-side nothing is touched,
    the user requests a reset, and the password that worked a moment ago must stop working.
    That is the whole contract an inbox would otherwise be needed for.

    Also asserts the response is the fixed generic message and carries no credential material —
    a reset endpoint that echoed the new password would be worse than useless.

    Precondition: an ACTIVE partner and a THROWAWAY user on it. Spends ONE call against the
    per-IP rate budget.
    """
    async with async_step("[1/4] Setup: an active partner + a throwaway user"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        invited = await sa_partners_client.invite_partner_user(make_partner_user(partner_id))
        victim = invited.data
        email, old_password = victim.get("email"), victim.get("tempPassword")
        assert email and old_password, f"invite did not return usable creds: {victim}"

        anon = portal_client(settings)
        created_resources.add(anon.close)
        logger.info("SETUP: partner={} throwaway user={}", partner_id, email)

    async with async_step("[2/4] Baseline: the current password authenticates"):
        resp = await partner_login(anon, email, old_password)
        assert resp.status_code == 200, (
            f"the invited user cannot log in with its own tempPassword (HTTP "
            f"{resp.status_code}) — the fixture is broken, not the endpoint under test"
        )
        logger.info("CHECK baseline login → 200 → OK")

    async with async_step("[3/4] Request the reset → generic message, nothing leaked"):
        resp = await anon.forgot_password(email)
        body = resp.json()
        assert body.get("message") == _GENERIC, (
            f"expected the fixed generic message, got {body.get('message')!r}. Any wording that "
            "varies with the outcome turns this endpoint into a user-enumeration oracle"
        )
        # The generic message legitimately contains the word "password", so look for the
        # things that would actually be a leak: the new credential, or a session token.
        text = resp.text.lower()
        for secret in ("temppassword", "accesstoken", "refreshtoken", "newpassword"):
            assert secret not in text, (
                f"the reset response carries {secret!r} — the new credential must go to the "
                f"mailbox, never back to the caller: {resp.text[:200]}"
            )
        logger.info("CHECK reset accepted, generic message, nothing leaked → OK")

    async with async_step("[4/4] The OLD password must stop working — the effect"):
        resp = await partner_login(anon, email, old_password)
        assert resp.status_code != 200, (
            f"the old password still authenticates (HTTP {resp.status_code}) after a reset was "
            "requested. The credential was NOT rotated, so anyone who knew the old password "
            "keeps access even though the user was told a reset was sent — and the new password "
            "is in an inbox the user may never read"
        )
        logger.info("CHECK old password no longer authenticates → {} → OK", resp.status_code)

    logger.info("RESULT: forgot-password verified by effect — credential rotated, nothing leaked")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_auth_access_control_011(sa_partners_client, settings, created_resources):
    """PARTNER_API_AUTH_ACCESS_CONTROL_011: forgot-password does not leak accounts or allow sweeps.

    Negative counterpart of _010, and the security half of the endpoint:

    * An unknown email must be indistinguishable from a registered one — same status, same body.
      The service returns early for an unknown user and the controller never branches, so any
      observable difference is a user-enumeration oracle.
    * A malformed email must be refused by DTO validation.
    * The per-email rate limit must actually fire, or the endpoint is a password-reset flood
      tool against any address an attacker knows.

    Spends up to 8 calls against the per-IP budget of 20 per 15 minutes. An early 429 is treated
    as proof the limit exists, not as a failure.

    All cases run and failures are collected.
    """
    async with async_step("[1/4] Setup: an active partner + a throwaway user"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)

        invited = await sa_partners_client.invite_partner_user(make_partner_user(partner_id))
        known_email = invited.data.get("email")
        assert known_email, "invite did not return an email"
        anon = portal_client(settings)
        created_resources.add(anon.close)
        logger.info("SETUP: partner={} known user={}", partner_id, known_email)

    gaps: list[str] = []

    async with async_step("[2/4] A malformed email → 400 from DTO validation"):
        resp = await anon.forgot_password("not-an-email", expected_status=None)
        if resp.status_code != 400:
            gaps.append(f"email='not-an-email' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed email → 400 → OK")

    async with async_step("[3/4] An unknown email is indistinguishable from a registered one"):
        unknown = unique_email()
        known = await anon.forgot_password(known_email, expected_status=None)
        stranger = await anon.forgot_password(unknown, expected_status=None)
        if 429 in (known.status_code, stranger.status_code):
            gaps.append(
                "UNPROVEN: the per-IP rate limit (20 / 15 min) was already exhausted before this "
                "step, so the two responses could not be compared. Re-run in 15 minutes"
            )
        else:
            if known.status_code != stranger.status_code:
                gaps.append(
                    f"a registered email answers {known.status_code} but an unknown one answers "
                    f"{stranger.status_code} — the status code alone reveals which addresses "
                    "have accounts"
                )
            if known.json().get("message") != stranger.json().get("message"):
                gaps.append(
                    f"the messages differ — registered {known.json().get('message')!r} vs "
                    f"unknown {stranger.json().get('message')!r} — a user-enumeration oracle"
                )
            elif known.json().get("message") != _GENERIC:
                gaps.append(f"neither answer is the generic message: {known.text[:160]}")
            else:
                logger.info("CHECK known and unknown email indistinguishable → OK")

    async with async_step("[4/4] The per-email rate limit fires"):
        # Same throwaway address as step 3, which already spent 1 of its 5.
        limited_at = None
        for attempt in range(1, _PROBE_CAP + 1):
            resp = await anon.forgot_password(known_email, expected_status=None)
            if resp.status_code == 429:
                limited_at = attempt
                break
        if limited_at is None:
            gaps.append(
                f"{_PROBE_CAP} further reset requests for the same address were all accepted — "
                f"the documented limit is {_MAX_PER_EMAIL} per email per 15 minutes. Without it "
                "anyone can flood a known address with reset mail and rotate its password "
                "repeatedly. Confirm with BE"
            )
        else:
            logger.info("CHECK per-email rate limit → 429 after {} more → OK", limited_at)

    assert not gaps, "Gaps on forgot-password:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: no enumeration oracle, malformed input refused, rate limit enforced")
