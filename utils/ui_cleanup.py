"""Cleanup helpers for resources a test creates through the BROWSER.

Why this module exists
---------------------
An API test knows the id of everything it creates — the create response carries
it — so it registers cleanup directly::

    resp = await sa_partners_client.create_partner(make_partner())
    created_resources.add(lambda: sa_partners_client.delete_partner(resp.partner_id))

A UI test cannot do that. The browser submits the form, and the page only shows a
human-readable code (``PAR-243212``), not the ``_id`` that ``DELETE
/v1/sa/partners/{id}`` needs. Without a way to resolve the id, UI tests registered
no cleanup at all and leaked a partner per run onto shared staging.

These helpers close the gap by resolving the id from the one value the test DOES
control: the unique name it typed into the form.

Loud by design
--------------
``created_resources`` swallows teardown exceptions (one failed cleanup must not
block the others), so a cleanup that quietly fails leaks forever and nobody
notices. Every helper here therefore logs a WARNING naming the record and the
reason it survived, so a leak shows up in the run log instead of only on staging.

Usage (register right after the UI creates the record, before the assertions)::

    async def test_x(sa_cleanup, make_page, created_resources):
        detail = make_page(PartnerDetailPage)
        await detail.onboard_partner(company, email)
        created_resources.add(lambda: sa_cleanup.delete_partner_by_name(company))

Why the API login is LAZY
-------------------------
``SaCleanup`` does not log in when the fixture is set up — it logs in the first
time a cleanup actually runs, which is during teardown, after the UI work is
finished. That is deliberate: stgsa's SA auth uses a rotating, single-use refresh
cookie (see the ``authenticated_page`` fixture), so holding an API session open
alongside the browser session for the duration of the test risks rotating the
session out from under the UI. Logging in only at teardown means the two sessions
never overlap while the test is exercising the UI.

Ordering rule: request ``created_resources`` AFTER ``sa_cleanup``. Pytest finalizes
fixtures in reverse setup order, so this way the cleanups run before ``sa_cleanup``
closes its HTTP client.
"""

import asyncio
from typing import Any

from loguru import logger

# A ``search`` hit returns a handful of rows; 20 is plenty to find the exact match.
_SEARCH_LIMIT = 20
# Retries absorb read-after-write lag and staging's intermittent 500s on this endpoint.
_RESOLVE_ATTEMPTS = 3
_RESOLVE_DELAY_S = 2


async def resolve_partner_id_by_name(client: Any, name: str) -> str | None:
    """Return the ``_id`` of the partner whose name is exactly *name*, else ``None``.

    Uses ``GET /v1/sa/partners?search=<name>``: the endpoint supports ``search`` and
    matches on the partner name (verified against staging 2026-08-06), so one request
    is normally enough.

    Retried a few times because two transient conditions must not be mistaken for
    "the record does not exist" — which would silently skip the delete:

    * read-after-write lag — a partner the UI just created is occasionally not yet
      visible to the list endpoint;
    * staging intermittently answers this endpoint with 500
      ``MongooseError: buffering timed out``.

    Deliberately does NOT fall back to paging the whole list: staging holds ~1.8k
    partners, so a scan costs ~19 requests and dumps ~60 KB of response body into the
    log per page — far more expensive and noisier than retrying a targeted search.

    Matching is EXACT on the name. The caller's name carries a uuid token, so an
    exact match cannot hit a sibling test's partner — a prefix match could.
    """
    for attempt in range(1, _RESOLVE_ATTEMPTS + 1):
        try:
            # expected_status=None: inspect the status here instead of raising, so a
            # transient 5xx becomes a retry rather than a failed teardown.
            response = await client.raw_list_partners(
                search=name, limit=_SEARCH_LIMIT, expected_status=None
            )
            if response.status_code == 200:
                match = _exact_match(response.json().get("data", []), name)
                if match:
                    return match
            else:
                logger.debug(
                    "partner search for {!r} returned HTTP {} (attempt {}/{})",
                    name,
                    response.status_code,
                    attempt,
                    _RESOLVE_ATTEMPTS,
                )
        except Exception as exc:  # noqa: BLE001 — retry, never break teardown
            logger.debug(
                "partner search for {!r} errored on attempt {}/{}: {}",
                name,
                attempt,
                _RESOLVE_ATTEMPTS,
                exc,
            )
        if attempt < _RESOLVE_ATTEMPTS:
            await asyncio.sleep(_RESOLVE_DELAY_S)
    return None


def _exact_match(partners: list[dict[str, Any]], name: str) -> str | None:
    """Return the id of the partner in *partners* whose name equals *name*."""
    for partner in partners:
        if str(partner.get("name", "")) == name:
            return partner.get("_id") or partner.get("id")
    return None


class SaCleanup:
    """Deletes records a UI test created, logging in to the SA API only when needed.

    Built by the ``sa_cleanup`` fixture and used through ``created_resources``::

        created_resources.add(lambda: sa_cleanup.delete_partner_by_name(company))

    The login happens on the FIRST cleanup call (teardown), not at fixture setup —
    see the module docstring for why. A login failure disables cleanup for the rest
    of the test and is reported as a leak; it never fails the test.
    """

    def __init__(self, login: Any) -> None:
        """``login`` is an awaitable factory returning a client, or ``None`` on failure."""
        self._login = login
        self._client: Any | None = None
        self._attempted = False

    async def client(self) -> Any | None:
        """Return the SA client, logging in on first call. ``None`` when unavailable."""
        if not self._attempted:
            self._attempted = True
            self._client = await self._login()
        return self._client

    async def aclose(self) -> None:
        """Close the client if one was ever created."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def delete_partner_by_name(self, name: str) -> bool:
        """Delete the partner named *name*; see :func:`delete_partner_by_name`."""
        return await delete_partner_by_name(await self.client(), name)


async def delete_partner_by_name(client: Any | None, name: str) -> bool:
    """Delete the partner named *name*; return True when staging is left clean.

    Resolves the id (see :func:`resolve_partner_id_by_name`) and issues the
    DELETE. Deleting a partner also removes its portal users, so a test that
    added members only needs to clean up the parent partner.

    The return value means "staging is actually clean", NOT "the API said 200" —
    those are different on this backend. ``DELETE /v1/sa/partners/{id}`` answers
    ``200 {"message": "Partner deleted successfully"}`` but performs a SOFT delete:
    the record survives with ``status`` flipped to ``suspended`` and is still
    returned by ``GET /v1/sa/partners`` (probed on staging 2026-08-06). So this
    re-reads the record after the DELETE and only reports success when it is really
    gone. Without that check the log would claim a deletion that never happened —
    which is exactly how ~1.8k "cleaned up" partners accumulated on staging.

    Never raises — teardown must not turn a passing test red. Instead every
    outcome that leaves data behind is logged as a WARNING naming the partner, so
    the leak is visible in the run log:

    * client is None   → cleanup was unavailable this run (SA API login down)
    * id not resolved  → the record may still exist under a name we could not match
    * DELETE rejected  → the BE refused (a partner with deals cannot be deleted;
      the deal API has no delete endpoint, so the deal pins its parent)
    * DELETE soft-only → BE returned 200 but the record is still listed
    """
    if client is None:
        logger.warning(
            "CLEANUP LEAK: no SA API client this run — partner {!r} is left on staging. "
            "Sweep with: python -m utils.cleanup_staging",
            name,
        )
        return False

    partner_id = await resolve_partner_id_by_name(client, name)
    if partner_id is None:
        logger.warning(
            "CLEANUP LEAK: could not resolve a partner id for {!r} — if the record exists "
            "it is now orphaned on staging. Sweep with: python -m utils.cleanup_staging",
            name,
        )
        return False

    try:
        # expected_status=None so a refusal is reported here with its real body
        # instead of raising an AssertionError that created_resources would hide.
        response = await client.delete_partner(partner_id, expected_status=None)
    except Exception as exc:  # noqa: BLE001 — transport/timeout: report, never crash teardown
        logger.warning(
            "CLEANUP LEAK: DELETE partner {!r} (id={}) errored: {}", name, partner_id, exc
        )
        return False

    if response.status_code in (200, 204):
        # Trust the effect, not the status code — this endpoint soft-deletes.
        if await resolve_partner_id_by_name(client, name) is None:
            logger.info("CLEANUP: deleted partner {!r} (id={})", name, partner_id)
            return True
        logger.warning(
            "CLEANUP LEAK: DELETE partner {!r} (id={}) returned HTTP {} but the record is "
            "STILL listed — the endpoint soft-deletes (status → 'suspended') instead of "
            "removing it, so no test can actually clean up after itself. This is why "
            "QA-AUTO records accumulate on staging. Confirm with BE.",
            name,
            partner_id,
            response.status_code,
        )
        return False

    logger.warning(
        "CLEANUP LEAK: BE refused to delete partner {!r} (id={}) — HTTP {}: {}. "
        "A partner that already has deals cannot be removed (no deal delete endpoint).",
        name,
        partner_id,
        response.status_code,
        (response.text or "")[:200],
    )
    return False
