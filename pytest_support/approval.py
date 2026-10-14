"""Approval-chain helper — pin ONE record to a single, non-creating approver.

Partners and deals both run through an approval chain, and the rule it exists to enforce
is that the SA who CREATED a record may not approve it (the same principle as not
approving your own pull request). Two things follow for automation:

* The tenant-wide "Required approvers" value is not ours to depend on. It is whatever the
  product wants (0, 1, 3 …), it changes without warning, and when it is raised with NO
  default approvers every new record arrives with an UNASSIGNED chain — approving or
  rejecting it is then refused with
  ``400 "Approval chain not assigned yet — an SA must assign the approvers first"``
  (observed on staging 2026-10-08 for deals and 2026-10-09 for partners, where that single
  setting failed or blocked 48 of 163 test cases).

* Setting a record's count to **0** would make the problem disappear — and that is exactly
  the loophole we are asking FE to close, because 0 turns the chain off and lets the
  CREATOR approve its own record. Automation must not rely on a defect it is reporting.

So: pin each record WE create to exactly ONE approver — the QA approver account, which is
never the creator. That satisfies the rule rather than bypassing it, and it is independent
of the global setting, so the suite survives 0, 1 or N without changes.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from loguru import logger

# One approver is the minimum that still enforces "the creator may not approve".
REQUIRED_APPROVERS = 1


@dataclass(frozen=True)
class ApproverLogin:
    """Outcome of the QA approver's (ADMIN2) session login.

    ``blocked_reason`` is non-empty when the approver cannot act this run — no ADMIN2_*
    configured, or its login failed after retries. ``token`` is then empty.
    """

    token: str = ""
    blocked_reason: str = ""


class BlockedApprover:
    """Stands in for the QA approver client when that account cannot act this run.

    The alternative — approving as the CREATOR — is always refused while the chain is on:
    the chain assignment answers 400 "The requester cannot be an approver on their own
    request" and the approve answers 403. Measured 2026-10-13 16:44: ONE ADMIN2 sign-in
    timeout made the old fallback do exactly that, and TC-2061602 failed with what looked
    like a BE defect. In a full run it would hit every test that approves.

    Any client method called on this object becomes a BLOCKED skip that names the real
    cause — and ONLY in tests that actually approve or reject. A test that never touches
    the approver is unaffected, which a skip at fixture level could not guarantee (every
    ``sa_partners_client`` user depends on the approver fixture). ``close`` stays a no-op
    so fixture teardown still runs.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def __getattr__(self, name: str):
        if name.startswith("__"):  # keep copy/pickle/introspection protocols honest
            raise AttributeError(name)
        reason = self.__dict__.get("reason", "the QA approver is unavailable")

        async def _blocked(*_args: Any, **_kwargs: Any):
            pytest.skip(f"BLOCKED: {reason}")

        return _blocked

    async def close(self) -> None:
        return None


async def assign_single_approver(
    set_approval_config: Callable[..., Awaitable[Any]],
    record_id: str,
    approver_id: str,
    *,
    label: str = "record",
) -> bool:
    """Pin one record's chain to ``REQUIRED_APPROVERS`` with ``approver_id`` as the approver.

    ``set_approval_config`` is the bound client method for the record type —
    ``SaPartnersClient.set_partner_approval_config`` or
    ``SaDealsClient.set_deal_approval_config`` — so this stays one helper for both.

    Returns True when the chain was assigned. A refusal is reported and swallowed rather
    than raised: the caller's own approve/reject is the assertion that matters, and this is
    setup. Never raises, so it is safe to call unconditionally.
    """
    if not approver_id:
        logger.warning(
            "No QA approver id — leaving the {} chain as it is. Approving will fail unless "
            "the chain is already assigned.",
            label,
        )
        return False
    try:
        response = await set_approval_config(
            record_id, required_approvers=REQUIRED_APPROVERS, approvers=[approver_id]
        )
    except Exception as exc:  # noqa: BLE001 — setup helper: report, never break the test here
        logger.warning("Could not assign the {} approval chain for {}: {}", label, record_id, exc)
        return False
    status = getattr(response, "status_code", None)
    if status is not None and status >= 400:
        logger.warning(
            "Assigning the {} approval chain for {} answered {}: {}",
            label,
            record_id,
            status,
            getattr(response, "text", "")[:160],
        )
        return False
    logger.info(
        "APPROVAL CHAIN {} {} → {} approver ({})", label, record_id, REQUIRED_APPROVERS, approver_id
    )
    return True
