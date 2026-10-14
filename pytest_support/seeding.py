"""Test-data seeding helpers — the setup that almost every SA-partner test repeats.

Deliberately kept OUT of ``pytest_support/fixtures.py``: that module imports Playwright,
and the framework selftests run without it. Living here means the seeding rules below are
covered by ``selftests/test_seeded_partner_fixture.py`` in CI, not only locally.

``fixtures.py`` wraps ``seed_partner`` as the ``seeded_partner`` fixture; tests use that.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from pytest_support.approval import assign_single_approver
from utils.data_factory import make_partner


async def seed_partner(
    sa_partners_client,
    register_cleanup: Callable[[Callable[[], Awaitable[Any]]], None],
    *,
    approve: bool = False,
    payload: dict[str, Any] | None = None,
    approver_client=None,
    approver_user_id: str = "",
):
    """Create a throwaway partner and register its deletion in one step.

    This setup was copy-pasted into 40 test bodies plus 17 near-variants (measured
    2026-08-11 across 6 API modules). The rule it encodes:

        the cleanup is registered AT SEED TIME — immediately after the create, before
        the test does anything else — so every later failure is still cleaned up.

    Registering later (at the end of a step, after the assertions) is the mistake, and it
    only shows up on the failure path, which is exactly when nobody is watching. Coupling
    the registration to the create makes it unskippable: there is no call site left that
    could seed a partner and forget.

    Note the ``if partner_id`` guard makes the position of the ``assert`` beside it
    irrelevant — with no id there is nothing to register either way. The rule is about
    seeding vs later, not about those two lines.

    Returns the create response unchanged, so call sites keep using
    ``partner.partner_id`` and ``partner.data``.

    This does NOT reduce what staging keeps: ``DELETE /v1/sa/partners/{id}`` only
    soft-deletes (BUG-API-021), so a full run still leaves ~75 records behind however
    faithfully cleanup runs. What it buys is ONE place to change when BE provides a real
    delete or a purge.
    """
    partner = await sa_partners_client.create_partner(payload or make_partner())
    partner_id = partner.partner_id
    # Bind the id as a default argument. Not strictly required here — each call gets its
    # own frame, so even a late-bound name would capture the right id — but it keeps the
    # lambda correct if this ever moves inside a loop, where late binding WOULD make every
    # cleanup target the last partner.
    if partner_id:
        register_cleanup(lambda pid=partner_id: sa_partners_client.delete_partner(pid))
    assert partner_id, "precondition: partner must be created"
    if approve:
        # Approving is deliberately NOT done by `sa_partners_client`: the chain forbids the
        # REQUESTER from approving its own record, so the creator is the one actor that may
        # be refused. `approver_client` is the QA approver (a different SA).
        approver = approver_client or sa_partners_client
        # Default to the QA approver id the fixture attached to the creator client. A call
        # site that passed only `approver_client` silently skipped the pin and the approve
        # was refused — "Approval chain not assigned yet" (TC-2061602, run_20261013_103101).
        # Taking the default here closes that gap for every call site, present and future.
        approver_user_id = approver_user_id or getattr(sa_partners_client, "approver_user_id", "")
        # Pin THIS partner to exactly one approver — the QA account — so the seed depends
        # neither on the tenant-wide "Required approvers" value nor on who is assigned by
        # default. See pytest_support.approval for why the count is 1 and never 0.
        await assign_single_approver(
            sa_partners_client.set_partner_approval_config,
            partner_id,
            approver_user_id,
            label="partner",
        )
        await approver.approve_partner(partner_id)  # pending -> active
    return partner
