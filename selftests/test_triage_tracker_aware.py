"""Tracker-aware triage: a failing TC already in the Bug Tracker is a KNOWN defect.

Two changes are guarded here:

1. Classification (`ai_triage.collect_fail_groups`): a signature group with ANY tracked
   TC is upgraded to ``app_bug`` — even over ``flaky_slow`` (the register-wizard
   "Locator.click timeout" is a real bug, not a slow load) and ``unknown`` (an API
   assertion the log didn't surface). This ends the recurring "N flaky / M unknown"
   noise for failures that are already logged bugs.
2. Reconciliation (`bug_tracker.reconcile`): an untracked TC that shares a signature
   group with a tracked-open bug is COVERED by that bug — reported KNOWN OPEN, never
   appended as a duplicate. Groups are signature-based, so co-grouped == same defect.

No file/Playwright: the tracker is monkeypatched so these run in the selftest CI job.
"""

from utils import ai_triage
from utils import bug_tracker as bt


def _log(*lines: str) -> str:
    return "\n".join(lines)


def test_tracked_tc_upgrades_flaky_and_unknown_to_app_bug(monkeypatch):
    log = _log(
        "2026-01-01 00:00:00.000 | ERROR  | TC-12060201 | f.py:fn:1 | FAIL | [1/3] enter -- "
        "TimeoutError: Locator.click: Timeout 30000ms exceeded",
        "2026-01-01 00:00:00.000 | FAILED | TC-12060201 | f.py:fn:1 | [TC-12060201] FAILED (30.0s)",
        "2026-01-01 00:00:01.000 | FAILED | TC-2060124  | f.py:fn:1 | [TC-2060124] FAILED (4.0s)",
    )
    monkeypatch.setattr(ai_triage, "_tracked_tc_ids", lambda: {12060201, 2060124})
    cats = {tc: g.category for g in ai_triage.collect_fail_groups(log) for tc in g.tcs}
    assert cats["TC-12060201"] == "app_bug", "a tracked flaky-timeout TC must upgrade to app_bug"
    assert cats["TC-2060124"] == "app_bug", "a tracked no-evidence (unknown) TC must upgrade"


def test_untracked_flaky_stays_flaky(monkeypatch):
    log = _log(
        "2026-01-01 00:00:00.000 | ERROR  | TC-99999999 | f.py:fn:1 | did not render within 5000 ms",
        "2026-01-01 00:00:00.000 | FAILED | TC-99999999 | f.py:fn:1 | [TC-99999999] FAILED (5.0s)",
    )
    monkeypatch.setattr(ai_triage, "_tracked_tc_ids", lambda: set())
    cats = {tc: g.category for g in ai_triage.collect_fail_groups(log) for tc in g.tcs}
    assert cats["TC-99999999"] == "flaky_slow", "an untracked timeout stays flaky (unchanged)"


def test_env_auth_not_upgraded_even_when_tracked(monkeypatch):
    log = _log(
        "2026-01-01 00:00:00.000 | ERROR  | TC-2060124 | f.py:fn:1 | 502 Bad Gateway upstream",
        "2026-01-01 00:00:00.000 | FAILED | TC-2060124 | f.py:fn:1 | [TC-2060124] FAILED (1.0s)",
    )
    monkeypatch.setattr(ai_triage, "_tracked_tc_ids", lambda: {2060124})
    cats = {tc: g.category for g in ai_triage.collect_fail_groups(log) for tc in g.tcs}
    assert cats["TC-2060124"] == "env_auth", (
        "infra (couldn't-run) is not the tracked bug reproducing"
    )


class _Group:
    category = "app_bug"
    evidence = "TimeoutError: Locator.click waiting for get_by_role option"

    def __init__(self, tcs):
        self.tcs = tcs


def test_reconcile_covers_untracked_group_member(monkeypatch, tmp_path):
    # One group, two TCs: 12060201 is tracked-open (BUG-UI-009), 12060202 is not.
    # Both must report KNOWN OPEN under BUG-UI-009; nothing appended.
    monkeypatch.setattr(
        bt, "load_tracker", lambda p: {12060201: bt.BugRow(12060201, "BUG-UI-009", "Open", "ev")}
    )
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: ["BUG-UI-009"])
    res = bt.reconcile(
        [_Group(["TC-12060201", "TC-12060202"])],
        passed_tc_ids=set(),
        tracker_path=tmp_path / "tracker.xlsx",
        allow_write=False,
    )
    assert len(res.new) == 0, "an untracked TC covered by a co-grouped open bug must NOT append"
    assert {r.tc_id for r in res.known_open} == {12060201, 12060202}
    assert all(r.bug_id == "BUG-UI-009" for r in res.known_open)


def test_reconcile_appends_when_group_has_no_tracked_bug(monkeypatch, tmp_path):
    # No TC in the group is tracked → a genuinely new defect still gets appended.
    monkeypatch.setattr(bt, "load_tracker", lambda p: {})
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: [])
    res = bt.reconcile(
        [_Group(["TC-2060999"])],
        passed_tc_ids=set(),
        tracker_path=tmp_path / "tracker.xlsx",
        allow_write=False,
    )
    assert len(res.new) == 1, "a group with no tracked TC is a new defect → append"
    assert res.new[0]["Test Case ID"] == 2060999
