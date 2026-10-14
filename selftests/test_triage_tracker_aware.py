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
    # The tracked bug's recorded evidence matches the group's signature (same cause
    # still reproducing) → KNOWN OPEN, not a signature-change.
    monkeypatch.setattr(
        bt,
        "load_tracker",
        lambda p: {12060201: bt.BugRow(12060201, "BUG-UI-009", "Open", _Group.evidence)},
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


def test_a_new_bug_is_proposed_not_written_by_default(monkeypatch, tmp_path):
    # Appending by default filled the tracker with rows nobody had agreed to
    # (BUG-UI-013…024, BUG-API-044 on 2026-10-08/09 — most passed again days later).
    # A run must PROPOSE; a human decides what gets raised.
    monkeypatch.delenv("BUG_TRACKER_AUTOWRITE", raising=False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(bt, "load_tracker", lambda p: {})
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: [])
    tracker = tmp_path / "tracker.xlsx"
    tracker.write_bytes(b"")  # exists, so only the opt-in can be what withholds the write
    appended: list = []
    monkeypatch.setattr(bt, "_append_rows", lambda path, rows: appended.extend(rows) or len(rows))

    res = bt.reconcile([_Group(["TC-2060999"])], passed_tc_ids=set(), tracker_path=tracker)

    assert len(res.new) == 1, "the defect must still be reported"
    assert not res.wrote_to_file, "nothing may be written without an explicit opt-in"
    assert appended == [], "no row may reach the tracker by default"
    assert "PROPOSED only" in bt.render(res), "the report must say it wrote nothing"


def test_autowrite_env_var_opts_back_in(monkeypatch, tmp_path):
    monkeypatch.setenv("BUG_TRACKER_AUTOWRITE", "1")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(bt, "load_tracker", lambda p: {})
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: [])
    tracker = tmp_path / "tracker.xlsx"
    tracker.write_bytes(b"")
    monkeypatch.setattr(bt, "_append_rows", lambda path, rows: len(rows))

    res = bt.reconcile([_Group(["TC-2060999"])], passed_tc_ids=set(), tracker_path=tracker)
    assert res.wrote_to_file, "BUG_TRACKER_AUTOWRITE=1 must restore appending"


def test_autowrite_is_still_refused_on_ci(monkeypatch, tmp_path):
    monkeypatch.setenv("BUG_TRACKER_AUTOWRITE", "1")
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(bt, "load_tracker", lambda p: {})
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: [])
    tracker = tmp_path / "tracker.xlsx"
    tracker.write_bytes(b"")
    monkeypatch.setattr(bt, "_append_rows", lambda path, rows: len(rows))

    res = bt.reconcile([_Group(["TC-2060999"])], passed_tc_ids=set(), tracker_path=tracker)
    assert not res.wrote_to_file, "CI must never write to the tracker, opt-in or not"


class _EvGroup:
    """An app_bug group with a caller-supplied evidence signature."""

    category = "app_bug"

    def __init__(self, tcs, evidence):
        self.tcs = tcs
        self.evidence = evidence


def test_reconcile_open_bug_signature_changed_is_flagged(monkeypatch, tmp_path):
    # BUG-API-027 is OPEN on TC 2061510, recorded as the pagination defect. This run
    # the same TC fails with a DIFFERENT signature (malformed id → 404): the bug's
    # original cause looks fixed and a NEW defect is now failing the same TC. It must
    # surface as `changed` — not silently rolled into KNOWN OPEN — and (suggest-only)
    # nothing is appended. This is the gap that let a cause-swap read as "old bug".
    monkeypatch.setattr(
        bt,
        "load_tracker",
        lambda p: {
            2061510: bt.BugRow(
                2061510, "BUG-API-027", "Open", "limit=0 answered 200 with 10 rows instead of 400"
            )
        },
    )
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: ["BUG-API-027"])
    res = bt.reconcile(
        [_EvGroup(["TC-2061510"], "a malformed attribution id answered 404, expected 400")],
        passed_tc_ids=set(),
        tracker_path=tmp_path / "t.xlsx",
        allow_write=False,
    )
    assert len(res.known_open) == 0, "a changed-signature failure must NOT report as KNOWN OPEN"
    assert len(res.new) == 0, "`changed` is suggest-only — nothing appended"
    assert len(res.changed) == 1, "the signature change must be flagged exactly once"
    assert res.changed[0]["bug_id"] == "BUG-API-027"
    assert res.changed[0]["tc_id"] == 2061510


def test_reconcile_long_json_evidence_is_not_a_false_signature_change(monkeypatch, tmp_path):
    # Regression: reconcile used to clip the live evidence to 300 chars BEFORE signing it.
    # A cut landing inside a quoted JSON value leaves an unterminated quote, so the raw
    # text leaked into the signature and the SAME failure signed differently clipped vs
    # whole → a false "SIGNATURE CHANGED". Signatures must be taken untruncated.
    ev = (
        "FAIL | [1/4] Mark the approved deal as won (win intake incl. required "
        "adminPhoneNumber) -> status 'won' (321ms) -- AssertionError: Expected status "
        '(201,), got 400: {"statusCode":400,"message":"Tenant provisioning failed: '
        "[INVALID_PAYLOAD] intake.billingCycle: billingCycle must be one of the following "
        'values: MONTHLY, ANNUAL","error":"Tenant provisioning failed","timestamp":'
        '"2026-10-06T08:43:53.300Z","path":"/sa-partners-api/v1/sa/deals/abc/win"}'
    )
    assert len(ev) > 300, "the evidence must exceed the old clip point for this to bite"
    monkeypatch.setattr(
        bt, "load_tracker", lambda p: {2061602: bt.BugRow(2061602, "BUG-API-043", "Open", ev)}
    )
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: ["BUG-API-043"])
    res = bt.reconcile(
        [_EvGroup(["TC-2061602"], ev)],
        passed_tc_ids=set(),
        tracker_path=tmp_path / "t.xlsx",
        allow_write=False,
    )
    assert len(res.changed) == 0, "same evidence must never read as a signature change"
    assert {r.bug_id for r in res.known_open} == {"BUG-API-043"}


def test_sig_ignores_per_run_fixture_emails():
    # Tests mint a fresh plus-addressed mailbox every run. Two runs of the SAME defect
    # must sign identically — otherwise every run reads as a "signature change".
    a = "GET /directory/users/{userId} ignored the path parameter (qa.auto+aaron-aa31eed0b@mailinator.com)"
    b = "GET /directory/users/{userId} ignored the path parameter (team.qa.auto+michael-7d2c9e@mailinator.com)"
    assert bt._sig(a) == bt._sig(b), "a per-run email must not change the signature"
    assert "<email>" in bt._sig(a)


def test_sig_ignores_a_dangling_quote_from_clipping():
    # A clipped message ends mid-quote; the unterminated fragment must not leak into the
    # signature as raw text (it would make the signature unstable).
    whole = 'Expected 200, got 400: {"message":"boom happened here","path":"/v1/x"}'
    clipped = whole[:45]  # cuts inside the "message" value
    assert '"' in clipped and clipped.count('"') % 2, "fixture must leave a dangling quote"
    assert "boom" not in bt._sig(clipped), "raw clipped text must not leak into the signature"


def test_reconcile_open_bug_same_signature_stays_known_open(monkeypatch, tmp_path):
    # Same TC, SAME failure signature as recorded → unchanged behavior: KNOWN OPEN,
    # and NOT flagged as changed.
    ev = "a malformed attribution id answered 404, expected 400"
    monkeypatch.setattr(
        bt, "load_tracker", lambda p: {2061510: bt.BugRow(2061510, "BUG-API-027", "Open", ev)}
    )
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: ["BUG-API-027"])
    res = bt.reconcile(
        [_EvGroup(["TC-2061510"], ev)],
        passed_tc_ids=set(),
        tracker_path=tmp_path / "t.xlsx",
        allow_write=False,
    )
    assert len(res.changed) == 0, "an unchanged signature must not be flagged"
    assert {r.bug_id for r in res.known_open} == {"BUG-API-027"}


def test_group_keeps_each_members_own_evidence():
    # Two TCs share a group because their signatures match after normalization — the
    # step label and timing differ. The group must keep BOTH raw assertions, not just
    # the first member's.
    log = _log(
        "2026-01-01 00:00:00.000 | ERROR  | TC-2060218 | f.py:fn:1 | FAIL | [1/4] Mark won "
        "(368ms) -- AssertionError: Expected status (201,), got 400: billingCycle",
        "2026-01-01 00:00:00.000 | FAILED | TC-2060218 | f.py:fn:1 | [TC-2060218] FAILED (1.0s)",
        "2026-01-01 00:00:01.000 | ERROR  | TC-2060234 | f.py:fn:1 | FAIL | [8/8] Re-win "
        "(1565ms) -- AssertionError: Expected status (201,), got 400: billingCycle",
        "2026-01-01 00:00:01.000 | FAILED | TC-2060234 | f.py:fn:1 | [TC-2060234] FAILED (2.0s)",
    )
    groups = ai_triage.collect_fail_groups(log)
    g = next(g for g in groups if "TC-2060234" in g.tcs)
    assert g.count == 2, "same normalized signature → one group"
    assert "[8/8] Re-win" in g.evidence_for("TC-2060234"), "member keeps its OWN assertion"
    assert "[1/4] Mark won" in g.evidence_for("TC-2060218")
    assert "[1/4] Mark won" in g.evidence, "the representative stays the first member"


class _MultiGroup:
    """A group whose members failed with DIFFERENT raw assertions (same signature)."""

    category = "app_bug"
    evidence = "FAIL | [1/4] Mark won -- AssertionError: Expected status (201,), got 400"

    def __init__(self):
        self.tcs = ["TC-2060218", "TC-2060234"]
        self.evidence_by_tc = {
            "TC-2060218": self.evidence,
            "TC-2060234": "FAIL | [8/8] Re-win -- AssertionError: Expected status (201,), got 400",
        }


def test_reconcile_judges_each_tc_by_its_own_evidence(monkeypatch, tmp_path):
    # BUG-API-020 (TC-2060234) recorded the OLD cause; BUG-API-041 (TC-2060218) recorded
    # the cause still reproducing. Judging 2060234 by the group's representative (i.e.
    # 2060218's assertion) silently hid which assertion actually changed.
    monkeypatch.setattr(
        bt,
        "load_tracker",
        lambda p: {
            2060218: bt.BugRow(2060218, "BUG-API-041", "Open", _MultiGroup.evidence),
            2060234: bt.BugRow(2060234, "BUG-API-020", "Open", "missing companyWebsite → 201"),
        },
    )
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: ["BUG-API-020", "BUG-API-041"])
    res = bt.reconcile(
        [_MultiGroup()], passed_tc_ids=set(), tracker_path=tmp_path / "t.xlsx", allow_write=False
    )
    assert {r.bug_id for r in res.known_open} == {"BUG-API-041"}, "first member: cause unchanged"
    assert [c["bug_id"] for c in res.changed] == ["BUG-API-020"]
    assert "[8/8] Re-win" in res.changed[0]["new_evidence"], (
        "the reported 'now' must be THIS TC's assertion, not a co-grouped TC's"
    )


# The real row that made triage cry wolf: a hand-written bug logs PROSE, the runner
# logs the raw assertion. `_QUOTED_RE` collapses the quoted sentence to '<v>', so the
# recorded signature is content-free and can never match anything.
_PROSE_EVIDENCE = (
    "FAIL test_partner_api_partner_team_004 (run 2026-09-28): 'Validation gaps on "
    "/v1/partner/directory/users/{userId}/{deals,commissions}: ghost userId answered 200 "
    "with 0 rows, expected 404 - the path parameter is ignored (BUG-API-023); malformed "
    "userId answered 200 with 0 rows, expected 400.'"
)
_RAW_EVIDENCE = (
    "SOFT FAIL | [5/6] Ghost and malformed userId -> expect 404 / 400 (500ms) -- [5/6] ghost "
    "userId answered 200 with 0 row(s), expected 404 - the path parameter is ignored "
    "(BUG-API-023) | [5/6] malformed userId answered 200 with 0 row(s), expected 400"
)


def test_same_cause_survives_rewording():
    assert _PROSE_EVIDENCE != _RAW_EVIDENCE
    assert bt._sig(_PROSE_EVIDENCE) != bt._sig(_RAW_EVIDENCE), "exact signatures differ"
    assert bt._same_cause(_PROSE_EVIDENCE, _RAW_EVIDENCE), (
        "prose and the raw assertion describe ONE defect — must not be a cause swap"
    )


def test_same_cause_rejects_a_real_swap():
    old = "pipeline_034 [1-4/8]: missing companyWebsite/industry/adminFirstName each returned 201"
    new = (
        "FAIL | [8/8] Re-win an already-won deal -> 400 illegal transition (1565ms) -- "
        'AssertionError: Expected status (201,), got 400: {"statusCode":400,"message":'
        '"Tenant provisioning failed: intake.billingCycle must be MONTHLY, ANNUAL"}'
    )
    assert not bt._same_cause(old, new), "a genuinely different failure must still be flagged"


def test_sig_distinguishes_different_json_messages():
    # Was an xfail (known gap) until run_20261013_103101 showed the cost: `_sig` collapses
    # every quoted JSON value to '<v>', so two 400s with different `message` bodies sign
    # identically. Equal-but-empty signatures now fall through to the word comparison.
    a = (
        "FAIL | [1/5] POST /v1/sa/partners -- AssertionError: Expected status (201,), got 400: "
        '{"statusCode":400,"message":"Partner code PAR-587434 already exists"}'
    )
    b = (
        "FAIL | [1/4] POST /v1/sa/deals/win -- AssertionError: Expected status (201,), got 400: "
        '{"statusCode":400,"message":"Tenant provisioning failed: intake.billingCycle"}'
    )
    assert bt._sig(a) == bt._sig(b), "precondition: the skeletons really are equal"
    assert not bt._same_cause(a, b), "different JSON messages are different causes"


def test_chain_not_assigned_is_not_reported_as_the_billing_cycle_bug():
    # The real pair from run_20261013_103101: TC-2061602 died in SETUP on the approval
    # chain, yet triage reported KNOWN OPEN BUG-API-043 (billingCycle) for it.
    bug_043 = (
        "FAIL | [1/4] Mark the approved deal as won -- AssertionError: Expected status (201,), "
        'got 400: {"statusCode":400,"message":"Tenant provisioning failed: [INVALID_PAYLOAD] '
        'intake.billingCycle: billingCycle must be one of the following values: MONTHLY, ANNUAL"}'
    )
    chain = (
        "FAIL | Setup: partner + plan + register + approve a referral deal (1219ms) -- "
        'AssertionError: Expected status (201,), got 400: {"statusCode":400,"message":'
        '"Approval chain not assigned yet — an SA must assign the approvers first"}'
    )
    assert not bt._same_cause(bug_043, chain)


def test_same_json_message_with_different_ids_is_still_the_same_cause():
    # The guard against the opposite mistake: once equal skeletons stop counting, two runs
    # of the SAME failure must still match even though the ids in the body differ.
    a = (
        "FAIL | x -- AssertionError: Expected status (200,), got 404: "
        '{"statusCode":404,"message":"Partner 6ac89b4461244224a0670f02 PAR-587434 not found"}'
    )
    b = (
        "FAIL | x -- AssertionError: Expected status (200,), got 404: "
        '{"statusCode":404,"message":"Partner 6acda867dbd1dbe3b1a55244 PAR-102938 not found"}'
    )
    assert bt._same_cause(a, b)


class _TwoBugGroup:
    """One cause group holding TWO tracked-open bugs — the case where 'the group's
    first open bug' names the wrong one."""

    category = "app_bug"
    evidence = "FAIL | [1/5] POST /v1/sa/partners -- Expected (201,), got 400: envelope"

    def __init__(self):
        self.tcs = ["TC-2060218", "TC-2060234", "TC-2061602"]
        self.evidence_by_tc = {
            "TC-2060218": self.evidence,
            "TC-2060234": "FAIL | [8/8] Re-win -- billingCycle must be MONTHLY, ANNUAL",
            "TC-2061602": "FAIL | [1/4] Win -- billingCycle must be MONTHLY, ANNUAL",
        }


def test_changed_names_the_bug_that_owns_the_new_cause(monkeypatch, tmp_path):
    monkeypatch.setattr(
        bt,
        "load_tracker",
        lambda p: {
            2060218: bt.BugRow(2060218, "BUG-API-041", "Open", _TwoBugGroup.evidence),
            2060234: bt.BugRow(2060234, "BUG-API-020", "Open", "missing companyWebsite → 201"),
            2061602: bt.BugRow(
                2061602, "BUG-API-043", "Open", "FAIL | [1/4] Win -- billingCycle MONTHLY, ANNUAL"
            ),
        },
    )
    monkeypatch.setattr(bt, "all_bug_ids", lambda p: ["BUG-API-020", "BUG-API-041", "BUG-API-043"])
    res = bt.reconcile(
        [_TwoBugGroup()], passed_tc_ids=set(), tracker_path=tmp_path / "t.xlsx", allow_write=False
    )
    changed = {c["bug_id"]: c for c in res.changed}
    assert set(changed) == {"BUG-API-020"}, "only the TC whose cause actually swapped"
    assert changed["BUG-API-020"]["cause_of"] == "BUG-API-043", (
        "the new cause belongs to BUG-API-043, not to the group's first open bug"
    )


def test_word_free_assertions_are_told_apart_by_status_code():
    # Review 2026-10-14: with no distinctive word on either side both token sets are empty,
    # and "equal" empty sets used to mean "same cause" — hiding a new 5xx behind an old 400.
    old = "FAIL | [1/2] Create -- AssertionError: Expected status (201,), got 400"
    assert not bt._same_cause(old, old.replace("got 400", "got 500"))
    assert bt._same_cause(old, old.replace("[1/2]", "[2/2]"))
