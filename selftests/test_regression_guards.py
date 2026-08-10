"""Locks in fixes that are easy to undo by accident.

Each block here corresponds to a bug that was live in this repo and would look
perfectly reasonable to "simplify" back. The comments say what breaks if you do.
"""

import asyncio
import re

import pytest

from runner.test_runner import _RERUN_PATTERNS
from utils import preflight as pf
from utils.ui_cleanup import delete_partner_by_name

# ── Auto-retry whitelist ─────────────────────────────────────────────────────
# pytest-rerunfailures does re.search(pattern, failure_repr) for each --only-rerun
# pattern. Two ways to get this wrong, both of which HIDE a real failure by making
# it green on the second attempt.

RETRYABLE = [
    "playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 60000ms exceeded.",
    "AssertionError: Expected status (200,), got 502: <html>Bad Gateway</html>",
    "AssertionError: Expected status (200,), got 503: Service Unavailable",
    "AssertionError: Expected status (200,), got 504: Gateway Timeout",
    "httpx.ReadTimeout",
    "httpx.PoolTimeout",
    "AssertionError: SA Partner Detail did not render within 60000 ms",
    "httpx.ConnectError: [Errno 111] ECONNREFUSED",
    "Failed to fetch dynamically imported module: https://stgsa/remoteEntry.js",
]

NOT_RETRYABLE = [
    # The response-time SLA breach. Retrying it defeats its purpose: an
    # INTERMITTENTLY slow endpoint would go green on attempt 2 and the perf
    # regression disappears. Do not add "exceeded limit" back to the whitelist.
    "AssertionError: response time 31000ms exceeded limit 30000ms for GET /v1/sa/partners",
    # Same, and it also proves the 5xx patterns stay anchored: "5502" contains "502".
    "AssertionError: response time 5502ms exceeded limit 30000ms for GET /v1/sa/partners",
    # A mongo id containing 503. With bare "503" in the whitelist this real
    # assertion failure was being retried.
    "AssertionError: re-granting must not duplicate (id=6a7450213cb2f122ed0158503)",
    "AssertionError: Expected status (404,), got 400: Partner 000.. not found",
    "AssertionError: the partner should no longer be Active after Deactivate",
]


def _would_retry(message: str) -> bool:
    return any(re.search(p, message) for p in _RERUN_PATTERNS)


@pytest.mark.parametrize("message", RETRYABLE)
def test_transient_failures_are_retried(message):
    assert _would_retry(message), f"should be retried: {message!r}"


@pytest.mark.parametrize("message", NOT_RETRYABLE)
def test_real_failures_are_never_retried(message):
    assert not _would_retry(message), f"retrying this hides a real failure: {message!r}"


def test_five_xx_patterns_stay_anchored():
    """A bare '502' substring also matches ids and durations — keep the \\b anchors."""
    assert any("50[234]" in p for p in _RERUN_PATTERNS), "the anchored 5xx pattern is gone"
    assert "502" not in _RERUN_PATTERNS, "bare '502' matches any digits; use the anchored form"


# ── Cleanup must not trust a 200 ─────────────────────────────────────────────
# DELETE /v1/sa/partners/{id} answers 200 "deleted successfully" but soft-deletes.
# Reporting success on the status code alone is how ~1.8k QA-AUTO partners piled up.


class _Resp:
    def __init__(self, status=200, text="{}"):
        self.status_code = status
        self.text = text

    def json(self):
        return {"data": self._data} if hasattr(self, "_data") else {"data": []}


class _FakeClient:
    """Minimal stand-in for SaPartnersClient."""

    def __init__(self, name, *, hard_delete=True, delete_status=200):
        self._rows = [{"_id": "abc123", "name": name}]
        self._hard = hard_delete
        self._delete_status = delete_status
        self.deletes = 0

    async def raw_list_partners(self, **kw):
        rows = self._rows
        resp = _Resp()
        resp._data = rows
        return resp

    async def delete_partner(self, pid, **kw):
        self.deletes += 1
        if self._hard and self._delete_status == 200:
            self._rows = []
        return _Resp(self._delete_status, "refused")


NAME = "QA-AUTO Something abc"


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch):
    """Zero the resolve back-off: these tests assert logic, not staging patience."""
    monkeypatch.setattr("utils.ui_cleanup._RESOLVE_DELAY_S", 0)


def test_hard_delete_reports_success():
    client = _FakeClient(NAME, hard_delete=True)
    assert asyncio.run(delete_partner_by_name(client, NAME)) is True
    assert client.deletes == 1


def test_soft_delete_is_reported_as_a_leak_despite_http_200():
    """The record is still listed after a 200 — that is NOT a successful cleanup."""
    client = _FakeClient(NAME, hard_delete=False)
    assert asyncio.run(delete_partner_by_name(client, NAME)) is False, (
        "a 200 with the record still present must not be reported as deleted"
    )


def test_refused_delete_is_reported_as_a_leak():
    client = _FakeClient(NAME, hard_delete=False, delete_status=500)
    assert asyncio.run(delete_partner_by_name(client, NAME)) is False


def test_missing_client_is_reported_as_a_leak_not_a_success():
    """Cleanup unavailable (API login down) must never look like a clean teardown."""
    assert asyncio.run(delete_partner_by_name(None, NAME)) is False


def test_unknown_name_never_deletes_anything():
    client = _FakeClient(NAME)
    assert asyncio.run(delete_partner_by_name(client, "QA-AUTO Not There")) is False
    assert client.deletes == 0, "must not delete a partner it could not positively identify"


# ── Preflight aborts only when EVERYTHING is down ────────────────────────────
# Aborting on a partial outage costs far more than it saves: measured on the real
# incident, 21 blocked TCs cost 10.8s while the healthy surfaces still produced 98
# real results.


def _fake_probes(monkeypatch, api_ok: bool, ui_ok: dict[str, bool]):
    async def fake_api(url):
        return {"name": "API gateway", "url": url, "ok": api_ok, "detail": "x"}

    async def fake_ui(origins, browser):
        return [{"name": n, "url": u, "ok": ui_ok[n], "detail": "x"} for n, u in origins.items()]

    monkeypatch.setattr(pf, "_probe_api", fake_api)
    monkeypatch.setattr(pf, "_probe_ui_origins", fake_ui)


def test_all_up_does_not_abort(monkeypatch):
    _fake_probes(monkeypatch, True, {"Partner portal": True})
    abort, failures = pf.run_preflight(
        api_base_url="https://api", ui_origins={"Partner portal": "https://p"}
    )
    assert abort is False
    assert failures == []


def test_partial_outage_reports_but_does_not_abort(monkeypatch):
    _fake_probes(monkeypatch, True, {"Partner portal": False})
    abort, failures = pf.run_preflight(
        api_base_url="https://api", ui_origins={"Partner portal": "https://p"}
    )
    assert abort is False, "one dead surface must not block the surfaces that still work"
    assert len(failures) == 1, "the dead surface must still be reported"


def test_total_outage_aborts(monkeypatch):
    _fake_probes(monkeypatch, False, {"Partner portal": False})
    abort, failures = pf.run_preflight(
        api_base_url="https://api", ui_origins={"Partner portal": "https://p"}
    )
    assert abort is True, "nothing can run — abort"
    assert len(failures) == 2


def test_nothing_to_probe_does_not_abort(monkeypatch):
    _fake_probes(monkeypatch, True, {})
    abort, failures = pf.run_preflight(api_base_url=None, ui_origins={})
    assert abort is False, "an empty probe list is not an outage"
    assert failures == []
