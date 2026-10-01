"""SA commission summary + detail — GET /v1/sa/commissions/{summary,:id} (sa-partners-api).

Maps to the test plan: PARTNER_API_COMMISSIONS_PAYOUTS_019 / _023. PRD §4.7, §5.6.

`summary` returns four SA-wide cents totals over every partner. `:id` returns one commission
row. Automation cannot create a commission — a row only accrues once the provisioned tenant's
first payment succeeds (G1) — so the detail route is reachable through its refusals only, and
the summary is asserted on its shape and internal consistency rather than on a specific figure.

That is not a weak test: a summary that returns the wrong TYPE, a negative total, or totals
that contradict each other is broken regardless of what the numbers happen to be, and those
are exactly the failures a zeroed staging ledger would otherwise hide.
"""

import pytest
from loguru import logger

from utils.log_helper import async_step

# Returned by the summary route — all four are cents, so all four are integers.
_TOTALS = (
    "totalEarnedCents",
    "totalPendingCents",
    "totalPaidCents",
    "clawbackExposureCents",
)
_SENSITIVE = ("password", "token", "secret", "credential")
_GHOST = "000000000000000000000000"


def _data(resp):
    body = resp.json()
    assert isinstance(body, dict), f"expected an object envelope, got {type(body).__name__}"
    assert "data" in body, f"envelope has no `data`: {sorted(body)}"
    return body["data"]


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_019(sa_commissions_client):
    """PARTNER_API_COMMISSIONS_PAYOUTS_019: SA commission summary - well-formed, self-consistent totals.

    GET /v1/sa/commissions/summary. Asserts the envelope, that all four totals are present and
    are integers (cents, never floats — a float here is a rounding bug waiting to happen), that
    none is negative, and that the totals do not contradict the ledger they summarise.

    The cross-check against GET /v1/sa/commissions is the part that would catch a genuinely
    wrong summary: if the ledger holds rows, the totals cannot all be zero.

    Read-only — no setup, no teardown.
    """
    async with async_step("[1/4] GET the summary → a valid envelope with all four totals"):
        resp = await sa_commissions_client.get_summary()
        data = _data(resp)
        assert isinstance(data, dict), f"`data` must be an object, got {type(data).__name__}"
        missing = [t for t in _TOTALS if t not in data]
        assert not missing, f"the summary is missing {missing}: {sorted(data)}"
        assert resp.json().get("message"), "the envelope should carry a `message`"
        logger.info("CHECK summary envelope → OK ({})", {k: data[k] for k in _TOTALS})

    async with async_step("[2/4] Every total is an integer number of cents, never negative"):
        for key in _TOTALS:
            value = data[key]
            assert isinstance(value, int) and not isinstance(value, bool), (
                f"{key} is {type(value).__name__} ({value!r}) — a cents total must be an int; "
                "a float would accumulate rounding error across the ledger"
            )
            assert value >= 0, (
                f"{key} is negative ({value}). Even clawback exposure is expressed as a "
                "positive magnitude, so a negative here is a sign error"
            )
        logger.info("CHECK all four totals int and >= 0 → OK")

    async with async_step("[3/4] No credential material on the summary"):
        leaked = sorted(k for k in data if any(s.lower() in k.lower() for s in _SENSITIVE))
        assert not leaked, f"credential material on the commission summary: {leaked}"
        logger.info("CHECK summary carries no credential field → OK")

    async with async_step("[4/4] The summary does not contradict the ledger it summarises"):
        ledger = await sa_commissions_client.list_commissions(limit=1)
        rows = ledger.total or 0
        if rows == 0:
            # Every total must then be zero: a figure with no rows behind it is invented.
            nonzero = {k: data[k] for k in _TOTALS if data[k] != 0}
            assert not nonzero, (
                f"the ledger holds 0 commissions but the summary reports {nonzero} — the totals "
                "are not derived from the rows"
            )
            logger.info("CHECK ledger empty and every total 0 → consistent → OK")
        else:
            assert any(data[k] > 0 for k in _TOTALS), (
                f"the ledger holds {rows} commission(s) but every total is 0 — the summary is "
                "not reading the ledger"
            )
            assert data["totalEarnedCents"] >= data["totalPaidCents"], (
                f"totalPaidCents ({data['totalPaidCents']}) exceeds totalEarnedCents "
                f"({data['totalEarnedCents']}) — more has been paid out than was ever earned"
            )
            logger.info("CHECK totals consistent with {} ledger row(s) → OK", rows)

    logger.info("RESULT: SA commission summary verified — typed, non-negative, ledger-consistent")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_commissions_payouts_023(sa_commissions_client):
    """PARTNER_API_COMMISSIONS_PAYOUTS_023: SA commission detail and filters invalid input - refused.

    Negative counterpart of _019, and where GET /v1/sa/commissions/{id} is covered. A
    commission cannot be created by automation (G1), so every case this route has is a
    refusal: an id that does not exist, an id that is not an id, and a filter value outside
    the spec. A well-formed id that simply matches nothing on the LIST is not an error and
    must answer 200 with an empty page.

    `summary` is also requested as a literal id to prove the route order is right — the
    `summary` path must never be swallowed by `:id`.

    Read-only. All cases run and failures are collected.
    """
    gaps: list[str] = []

    async with async_step("[1/4] A well-formed commission id that does not exist → 4xx"):
        resp = await sa_commissions_client.get_commission(_GHOST, expected_status=None)
        if resp.status_code == 200:
            gaps.append(f"a ghost commission id answered 200: {resp.text[:160]}")
        elif resp.status_code >= 500:
            gaps.append(
                f"a ghost commission id crashed the service ({resp.status_code}): "
                f"{resp.text[:160]}. A missing record is a refusal, not a server error"
            )
        else:
            logger.info("CHECK ghost commission id → {} → OK", resp.status_code)

    async with async_step("[2/4] An id that is not an id at all → 400"):
        resp = await sa_commissions_client.get_commission("not-an-id", expected_status=None)
        if resp.status_code != 400:
            gaps.append(f"a malformed commission id answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed commission id → 400 → OK")

    async with async_step("[3/4] `summary` must stay a route, not be read as an id"):
        # /summary is declared before /:id; if that order ever flips, this returns a
        # "not found" for an id literally called "summary" instead of the totals.
        resp = await sa_commissions_client.get_summary(expected_status=None)
        if resp.status_code != 200:
            gaps.append(
                f"GET /v1/sa/commissions/summary answered {resp.status_code} — the `summary` "
                "route is being matched by `:id` instead of its own handler"
            )
        elif "totalEarnedCents" not in resp.text:
            gaps.append(f"the summary route returned something else entirely: {resp.text[:160]}")
        else:
            logger.info("CHECK `summary` resolves to the summary route → OK")

    async with async_step("[4/4] Ledger filters: bad status → 400, ghost partnerId → 200 empty"):
        resp = await sa_commissions_client.raw_list_commissions(status="bogus")
        if resp.status_code != 400:
            gaps.append(f"status='bogus' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK status='bogus' → 400 → OK")

        resp = await sa_commissions_client.raw_list_commissions(partnerId="not-an-id")
        if resp.status_code != 400:
            gaps.append(f"partnerId='not-an-id' answered {resp.status_code}, expected 400")
        else:
            logger.info("CHECK malformed partnerId filter → 400 → OK")

        resp = await sa_commissions_client.raw_list_commissions(partnerId=_GHOST)
        if resp.status_code != 200:
            gaps.append(
                f"a ghost partnerId answered {resp.status_code}; a valid-format id with no "
                "matches is an empty result, not an error"
            )
        elif (n := (resp.json() or {}).get("total")) != 0:
            gaps.append(f"a ghost partnerId returned total={n} — the filter was ignored")
        else:
            logger.info("CHECK ghost partnerId → 200 empty → OK")

    assert not gaps, "Gaps on GET /v1/sa/commissions:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: commission detail and filters refuse every invalid input")
