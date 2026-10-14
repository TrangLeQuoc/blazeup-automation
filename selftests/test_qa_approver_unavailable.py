"""When the QA approver (ADMIN2) cannot act, approving tests turn BLOCKED — never "fail".

Measured 2026-10-13 16:44: a single ADMIN2 sign-in timeout (POST, so base_client ran it
once with no retry) made the session fixture fall back to the CREATING account. Its id was
then assigned as the approver and the BE refused it — 400 "The requester cannot be an
approver on their own request", then 403 on the approve — so TC-2061602 failed with what
read like a BE defect. In a full run the same hiccup would have hit every approving test.

Guarded here:

1. ``login_qa_approver`` retries transport errors only (a 401 must not be hammered), and
   when it gives up it names the cause — the old log line ended in a bare colon.
2. ``BlockedApprover`` turns any approve/reject into a ``BLOCKED:`` skip, and only in the
   tests that actually approve; nothing ever falls back to the creator.

No network: login and sleep are injected, and the client is never allowed to send.
"""

import asyncio
from types import SimpleNamespace

import httpx
import pytest

from api_clients.blazeup.admin.partner.sa_deals_client import SaDealsClient
from api_clients.blazeup.admin.partner.sa_partners_client import SaPartnersClient
from pytest_support.approval import BlockedApprover
from pytest_support.fixtures import login_qa_approver
from pytest_support.seeding import seed_partner

_SKIPPED = pytest.skip.Exception


def _settings(**overrides):
    base = {
        "api_base_url": "http://api.invalid",
        "base_url": "http://sa.invalid",
        "admin2_email": "qa.approver@example.com",
        "admin2_password": "pw",
        "default_response_time_ms": 1000,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class _ScriptedLogin:
    """Fake login_api: raises the scripted exceptions in order, then returns a token."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    async def __call__(self, *_args, **_kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _login(fake, settings=None):
    naps: list[float] = []

    async def _sleep(seconds):
        naps.append(seconds)

    result = asyncio.run(login_qa_approver(settings or _settings(), login=fake, sleep=_sleep))
    return result, naps


# ── login: retry + classification ────────────────────────────────────────────


def test_a_transport_error_is_retried_and_the_login_then_succeeds():
    fake = _ScriptedLogin(httpx.ReadTimeout(""), httpx.ConnectError(""), "tok")
    result, naps = _login(fake)
    assert result.token == "tok" and not result.blocked_reason
    assert fake.calls == 3, "two transport errors, then the successful third attempt"
    assert len(naps) == 2, "a pause between attempts, none after the success"


def test_an_auth_rejection_is_not_retried():
    # Retrying a wrong password only hammers the account (and risks a lockout).
    fake = _ScriptedLogin(RuntimeError("Expected status (201,), got 401: Invalid credentials"))
    result, naps = _login(fake)
    assert fake.calls == 1 and naps == []
    assert not result.token
    assert "auth rejected" in result.blocked_reason


def test_exhausted_retries_block_with_a_reason_that_names_the_cause():
    fake = _ScriptedLogin(*[httpx.ReadTimeout("")] * 3)
    result, _ = _login(fake)
    assert fake.calls == 3
    assert not result.token
    # An httpx timeout stringifies to "" — the reason must still say what happened.
    assert "ReadTimeout" in result.blocked_reason
    assert "unreachable" in result.blocked_reason


def test_a_transport_error_wrapped_by_the_caller_is_still_retried():
    wrapped = RuntimeError("sign-in failed")
    wrapped.__cause__ = httpx.ReadTimeout("")
    fake = _ScriptedLogin(wrapped, "tok")
    result, _ = _login(fake)
    assert result.token == "tok" and fake.calls == 2


def test_missing_admin2_credentials_block_instead_of_using_the_creator():
    fake = _ScriptedLogin("never-called")
    result, _ = _login(fake, _settings(admin2_email="", admin2_password=""))
    assert fake.calls == 0
    assert not result.token
    assert "ADMIN2" in result.blocked_reason


# ── BlockedApprover: approving turns BLOCKED, nothing else changes ──────────


def test_approving_through_a_blocked_approver_is_a_blocked_skip():
    approver = BlockedApprover("SA approver (ADMIN2) login failed — service unreachable")
    with pytest.raises(_SKIPPED, match=r"^BLOCKED: SA approver \(ADMIN2\) login failed"):
        asyncio.run(approver.approve_partner("pid-1"))


def test_a_blocked_approver_still_closes_cleanly():
    # Fixture teardown calls close(); it must not skip or raise.
    asyncio.run(BlockedApprover("x").close())


def test_a_blocked_approver_does_not_fake_python_protocols():
    with pytest.raises(AttributeError):
        BlockedApprover("x").__deepcopy__  # noqa: B018 — the access itself is the test


def test_the_creator_client_delegates_the_approve_and_gets_blocked_not_refused():
    # The real client path every seeding call takes: approve_partner → approver.post.
    # With no QA approver id the pin is skipped, and the POST goes to the BlockedApprover
    # — never to the creator, whose approve the BE would refuse.
    async def _run():
        client = SaPartnersClient("http://127.0.0.1:9", token="creator")
        client.approver_client = BlockedApprover("no QA approver configured")
        client.approver_user_id = ""
        try:
            await client.approve_partner("pid-1")
        finally:
            await client.close()

    with pytest.raises(_SKIPPED, match="^BLOCKED: no QA approver configured"):
        asyncio.run(_run())


class _Creator:
    """Minimal creator client for seed_partner: records calls, never approves."""

    approver_user_id = ""

    def __init__(self):
        self.calls: list[str] = []

    async def create_partner(self, _payload):
        self.calls.append("create")
        return SimpleNamespace(partner_id="pid-1", data={})

    async def set_partner_approval_config(self, *_args, **_kwargs):
        self.calls.append("assign_chain")

    async def approve_partner(self, _partner_id):
        self.calls.append("approve")

    async def delete_partner(self, _partner_id):
        self.calls.append("delete")


def test_seeding_an_approved_partner_is_blocked_and_the_creator_never_approves():
    creator = _Creator()
    with pytest.raises(_SKIPPED, match="^BLOCKED: "):
        asyncio.run(
            seed_partner(
                creator,
                lambda _cleanup: None,
                approve=True,
                approver_client=BlockedApprover("SA approver (ADMIN2) login failed"),
            )
        )
    assert "approve" not in creator.calls, "the creator must never approve its own partner"
    assert "assign_chain" not in creator.calls, "no chain may be pinned without a QA approver id"


# ── both clients: the chain is pinned to the QA approver, or not touched — never 0 ──
#
# The pin logic lives in two clients, and the copies drifted: SaDealsClient fell back to
# requiredApprovers=0 when it had no approver id — the self-approval loophole automation
# must never rely on — while SaPartnersClient left the chain alone. Both are held to the
# same rule here.


def _chain_calls(client, setter_name):
    calls: list[tuple] = []

    async def _record(record_id, *, required_approvers, approvers):
        calls.append((record_id, required_approvers, tuple(approvers)))

    setattr(client, setter_name, _record)
    return calls


@pytest.mark.parametrize(
    ("client_cls", "setter", "approve", "kwargs"),
    [
        (SaPartnersClient, "set_partner_approval_config", "approve_partner", {}),
        # plan_id given: without it approve_deal first GETs the deal to look the plan up.
        (SaDealsClient, "set_deal_approval_config", "approve_deal", {"plan_id": "plan-1"}),
        (SaDealsClient, "set_deal_approval_config", "reject_deal", {}),
    ],
)
@pytest.mark.parametrize("approver_id", ["", "qa-approver-id"])
def test_no_client_ever_pins_a_chain_to_zero(client_cls, setter, approve, kwargs, approver_id):
    async def _run():
        client = client_cls("http://127.0.0.1:9", token="creator")
        calls = _chain_calls(client, setter)
        client.approver_user_id = approver_id
        client.approver_client = BlockedApprover("stop before any HTTP call")
        try:
            with pytest.raises(_SKIPPED):
                await getattr(client, approve)("rec-1", **kwargs)
        finally:
            await client.close()
        return calls

    calls = asyncio.run(_run())
    assert all(required != 0 for _, required, _ in calls), f"a chain was pinned to 0: {calls}"
    if approver_id:
        assert calls == [("rec-1", 1, ("qa-approver-id",))]
    else:
        assert calls == [], "with no QA approver id the chain must be left untouched"


@pytest.mark.parametrize(
    "first_failure",
    [
        RuntimeError('Expected status (201,), got 503: {"message":"Service Unavailable"}'),
        RuntimeError("Expected status (201,), got 502: Bad Gateway"),
        AssertionError("response time 9120ms exceeded limit 5000ms for POST sign-in"),
    ],
    ids=["503", "502", "over-SLA"],
)
def test_gateway_errors_and_slow_responses_are_retried(first_failure):
    # Review 2026-10-14: only transport errors were retried, so one gateway 503 on the
    # session-scoped sign-in turned every approving test in the run BLOCKED.
    fake = _ScriptedLogin(first_failure, "tok")
    result, naps = _login(fake)
    assert result.token == "tok" and fake.calls == 2 and len(naps) == 1


def test_a_client_error_other_than_401_is_not_retried_either():
    fake = _ScriptedLogin(RuntimeError("Expected status (201,), got 400: bad payload"))
    result, _ = _login(fake)
    assert fake.calls == 1 and not result.token
