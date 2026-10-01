"""Partner's own commission ledger — GET /portal/commissions (service: sa-partners-api).

Maps to the test plan: PARTNER_API_COMMISSIONS_PAYOUTS_020 / _024. PRD §4.7, §5.6.

There are NO commissions anywhere on staging — not for a fresh partner, not SA-wide — because a
row only accrues after a provisioned tenant's first payment (G1), which automation cannot
trigger. So the ledger's contents are out of reach and this pair says so plainly rather than
pretending otherwise.

What is still worth pinning, and would be just as broken with real data:

* Every value of the 8-member `status` enum is wired — a filter that 400s on a legitimate
  status is a defect the empty ledger does not hide.
* The list and its summary agree. An empty ledger with non-zero totals means the summary is
  not derived from the rows, and that check keeps working unchanged once commissions exist.
* `partnerId` is not a parameter on this route and cannot be smuggled in as one.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step
from utils.partner_portal import mint_partner_session

# partner-commission.schema.ts — the spec's own list, echoed back by the 400 on a bad value.
_STATUSES = (
    "earned",
    "accrued",
    "pending_approval",
    "approved",
    "paid",
    "disputed",
    "clawback",
    "cancelled",
)
_TOTALS = ("totalEarnedCents", "totalPendingCents", "totalPaidCents", "clawbackExposureCents")
_SENSITIVE = ("password", "token", "secret", "credential")
_GHOST = "000000000000000000000000"


def _envelope(resp) -> dict:
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    for key in ("data", "total"):
        assert key in body, f"envelope has no `{key}`: {sorted(body)}"
    assert isinstance(body["data"], list), (
        f"`data` must be a list, got {type(body['data']).__name__}"
    )
    assert isinstance(body["total"], int), f"`total` must be an int, got {body['total']!r}"
    return body


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_020(sa_partners_client, settings, created_resources):
    """PARTNER_API_COMMISSIONS_PAYOUTS_020: partner reads own commission ledger - scoped, consistent.

    GET /portal/commissions. An empty ledger is the correct answer for every partner on staging
    (G1), so the assertions are the ones that survive that: the envelope, that all eight status
    values are accepted, that the ledger agrees with its own summary, and that a `partnerId`
    smuggled into the query cannot widen a scope the JWT owns.

    Step 4 is the one that keeps its value once commissions exist — it compares two views of
    the same data rather than checking a constant.

    Precondition: an ACTIVE partner with a portal session.
    """
    async with async_step("[1/5] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    async with async_step("[2/5] GET the ledger → valid envelope; empty is the correct answer"):
        body = _envelope(await portal.list_commissions())
        rows = body["data"]
        assert body["total"] == len(rows) or body["total"] >= len(rows), (
            f"`total` ({body['total']}) is smaller than the page it returned ({len(rows)})"
        )
        assert body.get("message"), "the envelope should carry a `message`"
        for row in rows:
            leaked = sorted(k for k in row if any(s.lower() in k.lower() for s in _SENSITIVE))
            assert not leaked, f"credential material on a commission row: {leaked}"
        logger.info("CHECK ledger reachable → OK (total={})", body["total"])

    async with async_step("[3/5] Every status in the enum is accepted"):
        # The empty ledger cannot show that a filter NARROWS, but it can show that a legitimate
        # status is not rejected — which is what would break if the enum drifted from the schema.
        for status in _STATUSES:
            page = _envelope(await portal.list_commissions(params={"status": status}))
            wrong = [r.get("status") for r in page["data"] if r.get("status") != status]
            assert not wrong, f"status={status!r} also returned rows with {sorted(set(wrong))}"
        logger.info("CHECK all {} status values accepted → OK", len(_STATUSES))

    async with async_step("[4/5] The ledger and its summary tell the same story"):
        summary = (await portal.get_commissions_summary()).json().get("data") or {}
        missing = [t for t in _TOTALS if t not in summary]
        assert not missing, f"the summary is missing {missing}: {sorted(summary)}"
        if body["total"] == 0:
            nonzero = {k: summary[k] for k in _TOTALS if summary[k] != 0}
            assert not nonzero, (
                f"the partner's ledger is empty but its summary reports {nonzero} — the totals "
                "are not derived from the rows this partner actually owns"
            )
            logger.info("CHECK empty ledger ⇒ every summary total 0 → consistent → OK")
        else:
            assert any(summary[k] > 0 for k in _TOTALS), (
                f"the ledger holds {body['total']} row(s) but every summary total is 0"
            )
            logger.info("CHECK summary non-zero for a non-empty ledger → OK")

    async with async_step("[5/5] `partnerId` in the query cannot widen the scope"):
        # The controller takes partnerId from the JWT twice over and never from the query;
        # sending one must change nothing.
        widened = _envelope(await portal.list_commissions(params={"partnerId": _GHOST}))
        assert widened["total"] == body["total"], (
            f"passing partnerId={_GHOST} changed the total from {body['total']} to "
            f"{widened['total']} — the scope must come from the JWT, never the query string"
        )
        logger.info("CHECK query partnerId does not widen the scope → OK")

    logger.info("RESULT: own commission ledger verified — JWT-scoped and summary-consistent")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_024(sa_partners_client, settings, created_resources):
    """PARTNER_API_COMMISSIONS_PAYOUTS_024: own commission ledger invalid input - correct rejection.

    Negative counterpart of _020: a status outside the enum, and nonsensical pagination.

    All cases run and failures are collected.
    """
    async with async_step("[1/3] Setup: mint an active partner + portal session"):
        portal, partner_id, _uid = await mint_partner_session(sa_partners_client, settings)
        created_resources.add(lambda: sa_partners_client.delete_partner(partner_id))
        created_resources.add(portal.close)
        logger.info("SETUP: partner={}", partner_id)

    gaps: list[str] = []

    async with async_step("[2/3] A status outside the enum → 400 listing all eight values"):
        resp = await portal.list_commissions(params={"status": "bogus"}, expected_status=None)
        if resp.status_code != 400:
            gaps.append(f"status='bogus' answered {resp.status_code}, expected 400")
        elif missing := [s for s in _STATUSES if s not in resp.text]:
            gaps.append(f"the 400 for a bad status does not list {missing}")
        else:
            logger.info("CHECK status='bogus' → 400 listing every status → OK")

    async with async_step("[3/3] Nonsensical pagination must be refused"):
        for params in ({"limit": -1}, {"limit": 0}, {"page": "abc"}):
            r = await portal.list_commissions(params=params, expected_status=None)
            if r.status_code == 200:
                n = len((r.json() or {}).get("data") or [])
                gaps.append(
                    f"commissions {params} answered 200 with {n} row(s) instead of 400. "
                    "limit=-1 IS refused on this very endpoint, so the guard exists and simply "
                    "misses these values. FIFTH endpoint with the same root cause after "
                    "BUG-API-025 (/v1/sa/deals), 026 (/portal/modules), 027 (/portal/clients) "
                    "and 028 (/v1/sa/partner-attributions) — BUG-API-030, one shared fix"
                )
            elif r.status_code >= 500:
                gaps.append(f"commissions {params} crashed the service ({r.status_code})")
            else:
                logger.info("CHECK commissions {} → {} → OK", params, r.status_code)

    assert not gaps, "Gaps on GET /portal/commissions:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid status and page values refused")
