"""`seeded_partner` must create a partner AND register its deletion, every time.

Every SA-partner test starts with a throwaway partner; that setup was copy-pasted into 40
test bodies plus 17 near-variants. What matters is that the cleanup is registered at seed
time, so a failure anywhere later in the test still deletes the partner —
`test_a_failure_after_the_create_still_deletes_the_partner` is the point of the file.

Scope note, from proving these guards actually bite: two properties this file originally
claimed to protect turned out not to be real. Swapping the ``assert`` and the
``register_cleanup`` lines changes nothing (the ``if partner_id`` guard means there is
nothing to register when the assert would fire), and a late-bound closure would still
capture the right id (each call has its own frame). Both rewrites left the suite green, so
the tests asserting them were removed rather than left as decoration. What remains is
checked against a deliberate regression.

No network, no browser: ``pytest_support/seeding.py`` is Playwright-free precisely so
these run in the selftest CI job. ``fixtures.py`` only wraps it as a pytest fixture.
"""

import asyncio

import pytest

from pytest_support.seeding import seed_partner


class _CreateResponse:
    """Stand-in for SaPartnersClient's create response."""

    def __init__(self, partner_id: str | None, code: str = "QA-AUTO-1") -> None:
        self.partner_id = partner_id
        self.data = {"code": code, "status": "pending"}


class _FakeClient:
    """Records what the fixture asked of the client, in order."""

    def __init__(self, ids: list[str | None] | None = None) -> None:
        self._ids = list(ids or ["pid-1"])
        self.calls: list[tuple[str, object]] = []

    async def create_partner(self, payload):
        partner_id = self._ids.pop(0) if self._ids else None
        self.calls.append(("create", payload))
        return _CreateResponse(partner_id)

    async def approve_partner(self, partner_id):
        self.calls.append(("approve", partner_id))

    async def delete_partner(self, partner_id):
        self.calls.append(("delete", partner_id))


class _FakeRegistry:
    """Stand-in for _CleanupRegistry that can also RUN what was registered."""

    def __init__(self) -> None:
        self.cleanups: list = []

    def add(self, cleanup) -> None:
        self.cleanups.append(cleanup)

    async def run_all(self) -> None:
        for cleanup in reversed(self.cleanups):
            await cleanup()


def _seed(client, registry, **kwargs):
    """Seed once, the way the fixture does, and return the result."""
    return asyncio.run(seed_partner(client, registry.add, **kwargs))


# ── cleanup is registered at seed time ───────────────────────────────────────


def test_a_failure_after_the_create_still_deletes_the_partner():
    """The property that matters: teardown reaches the partner however the test ends.

    Simulates the real sequence — seed succeeds, the test then blows up — and checks the
    cleanup registered during seeding still targets that partner.
    """
    client = _FakeClient(ids=["pid-boom"])
    registry = _FakeRegistry()
    partner = _seed(client, registry)
    assert partner.partner_id == "pid-boom"
    # ... test body fails here; pytest still runs created_resources teardown ...
    asyncio.run(registry.run_all())
    assert ("delete", "pid-boom") in client.calls


def test_a_create_without_an_id_fails_loudly_and_registers_nothing():
    """No id means no partner to clean up — and the caller must not get a useless object."""
    client = _FakeClient(ids=[None])
    registry = _FakeRegistry()
    with pytest.raises(AssertionError, match="precondition: partner must be created"):
        _seed(client, registry)
    assert registry.cleanups == [], "nothing was created, so nothing may be registered"


# ── registration ─────────────────────────────────────────────────────────────


def test_one_cleanup_is_registered_per_partner():
    client = _FakeClient(ids=["pid-1"])
    registry = _FakeRegistry()
    _seed(client, registry)
    assert len(registry.cleanups) == 1


def test_two_partners_get_two_distinct_cleanups():
    """Seeding twice in one test (4 tests do) must delete both, not one of them twice.

    Covers the shape, not the closure style — see the module docstring on why a
    late-bound id would also work here.
    """
    client = _FakeClient(ids=["pid-a", "pid-b"])
    registry = _FakeRegistry()
    first = _seed(client, registry)
    second = _seed(client, registry)
    assert (first.partner_id, second.partner_id) == ("pid-a", "pid-b")

    asyncio.run(registry.run_all())
    deleted = [pid for kind, pid in client.calls if kind == "delete"]
    assert sorted(deleted) == ["pid-a", "pid-b"], (
        f"each partner must be deleted exactly once, got {deleted}"
    )


def test_the_returned_object_is_the_create_response_untouched():
    """Call sites use partner.partner_id and partner.data — do not wrap or reshape it."""
    client = _FakeClient(ids=["pid-1"])
    partner = _seed(client, _FakeRegistry())
    assert partner.partner_id == "pid-1"
    assert partner.data["code"] == "QA-AUTO-1"


# ── options ──────────────────────────────────────────────────────────────────


def test_default_does_not_approve():
    """A plain seeded partner stays `pending` — approving changes what is under test."""
    client = _FakeClient()
    _seed(client, _FakeRegistry())
    assert [kind for kind, _ in client.calls] == ["create"]


def test_approve_true_approves_after_creating():
    client = _FakeClient(ids=["pid-1"])
    _seed(client, _FakeRegistry(), approve=True)
    assert [kind for kind, _ in client.calls] == ["create", "approve"]
    assert ("approve", "pid-1") in client.calls


def test_default_payload_is_a_generated_partner():
    client = _FakeClient()
    _seed(client, _FakeRegistry())
    payload = next(arg for kind, arg in client.calls if kind == "create")
    assert isinstance(payload, dict) and payload, "must fall back to make_partner()"
    assert "email" in payload, f"generated payload looks wrong: {sorted(payload)}"


def test_an_explicit_payload_is_passed_through_unchanged():
    client = _FakeClient()
    mine = {"name": "QA-AUTO Specific", "email": "x@example.invalid"}
    _seed(client, _FakeRegistry(), payload=mine)
    assert next(arg for kind, arg in client.calls if kind == "create") is mine
