"""Reconcile triaged failures against the Bug Tracker (docs/blazeup/Bug_Tracker.xlsx).

Deterministic — keyed by **Test Case ID**, never the LLM. For each real defect
(triage category ``app_bug`` — API or UI), decide:

* NEW        — the TC has no row yet → append one (local runs only).
* KNOWN OPEN — a row exists and is still open → just report the Bug ID.
* REOPEN     — a row exists but is Closed and the test failed again → report ⚠.

The mirror of REOPEN is reported too, keyed by the run's PASSED test-case ids:

* RESOLVED   — a row exists and is still open, but the TC PASSED this run → the
               defect is no longer reproducing → report ✅ and suggest closing it.
               Suggest-only: the tracker's Status is NEVER auto-changed (a single
               pass can be flaky/env — a human decides the close).

Nothing is written unless writing is explicitly asked for: run with
``BUG_TRACKER_AUTOWRITE=1`` (or pass ``allow_write=True``), and only on a **local** run
(``CI`` unset), and only to this separate file — never the test plan. By default a run
PROPOSES rows and a human raises the ones worth raising; appending by default produced a
tracker nobody had agreed to (twelve rows on 2026-10-08/09, most of which passed again
days later).
"""

import datetime
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKER = _PROJECT_ROOT / "docs" / "blazeup" / "Bug_Tracker.xlsx"
_SHEET = "Bug Tracker"
# Status stems that mean "no longer open". Matched by PREFIX (case-insensitive) so
# human variants all count: CLOSE / Closed / closing, Fix / Fixed, Resolve / Resolved,
# Verify / Verified, Done, Won't Fix / WontFix, Complete / Completed.
_CLOSED_STEMS = ("close", "fix", "resolv", "verif", "done", "wontfix", "won't", "complete")


def _is_closed(status: str | None) -> bool:
    """True when a tracker Status means the bug is no longer open (prefix match)."""
    s = (status or "").strip().lower()
    return any(s.startswith(stem) for stem in _CLOSED_STEMS)


@dataclass
class BugRow:
    tc_id: int
    bug_id: str
    status: str
    evidence: str = ""  # the assertion/evidence recorded when the bug was opened


@dataclass
class Reconciliation:
    new: list[dict] = field(default_factory=list)
    known_open: list[BugRow] = field(default_factory=list)
    reopen: list[BugRow] = field(default_factory=list)
    resolved: list[BugRow] = field(default_factory=list)
    # An open tracked bug whose TC still fails, but with a DIFFERENT failure
    # signature than the one recorded on the bug → the bug's original cause may be
    # fixed and a NEW defect is now failing the same TC. Suggest-only (review +
    # close-old + log-new); never auto-appended. Each item:
    #   {tc_id, bug_id, status, old_evidence, new_evidence}
    changed: list[dict] = field(default_factory=list)
    written: int = 0
    wrote_to_file: bool = False
    tracker: Path = DEFAULT_TRACKER


def _tc_int(tc: str) -> int | None:
    m = re.search(r"\d+", tc or "")
    return int(m.group()) if m else None


# Normalize a failure message to a stable signature (mongo ids / numbers / quoted
# values masked) so the SAME root cause collapses to one string. Mirrors
# ai_triage._signature — used to tell whether a re-failure is the SAME defect as a
# closed bug (→ reopen) or a DIFFERENT one (→ open a new bug).
_ID_RE = re.compile(r"\b[0-9a-fA-F]{24}\b")
_QUOTED_RE = re.compile(r"(['\"]).*?\1")
# Per-run fixture data must not reach the signature: tests mint a fresh plus-addressed
# mailbox (qa.auto+<name>-<hex>@mailinator.com) every run, so an assertion that quotes
# it would sign differently on every execution and read as a "signature change" when
# nothing about the defect moved. Collapse the whole address first.
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_NUM_RE = re.compile(r"\d+")


# Evidence stored on a tracker row. Big enough that the assertion tail (what `_sig`
# reads) survives for JSON-heavy messages; `_sig` caps its own output anyway.
_EVIDENCE_CHARS = 600


def _sig(text: str) -> str:
    core = (text or "").split(" -- ", 1)[-1]
    if "AssertionError:" in core:
        core = core.split("AssertionError:", 1)[-1]
    # Evidence can arrive clipped (the tracker column is capped), and a cut that lands
    # inside a quoted JSON value leaves an UNTERMINATED quote. _QUOTED_RE never matches
    # it, so the raw text would leak into the signature and the same failure would sign
    # differently clipped vs whole. Drop the dangling fragment. Only `"` is trimmed —
    # an odd `'` count is usually just an apostrophe in prose, not a broken quote.
    if core.count('"') % 2:
        core = core[: core.rfind('"')]
    s = _EMAIL_RE.sub("<email>", core.strip())
    s = _ID_RE.sub("<id>", s)
    s = _QUOTED_RE.sub("'<v>'", s)
    s = _NUM_RE.sub("<n>", s)
    return s.lower()[:120]


# `_sig` equality answers "is this byte-for-byte the same assertion", which a
# hand-written bug row never is: a human logs prose ("Validation gaps on …: ghost
# userId answered 200 …"), the runner logs the raw assertion. Worse, `_QUOTED_RE`
# collapses the whole quoted sentence to `'<v>'`, so such a row signs as
# `fail test_x (run <n>-<n>-<n>): '<v>'` — content-free, and therefore unequal to
# everything forever. Comparing the DISTINCTIVE WORDS of the two texts survives the
# rewording, because the same defect keeps naming the same things (ghost, malformed,
# userId, path parameter…). Measured on the three flagged rows of run_20261009_144113:
# a genuine cause swap scored 0.00, the reworded same cause 0.54.
_CAUSE_OVERLAP = 0.35
_CAUSE_MIN_SHARED = 3
_CAUSE_WORD_RE = re.compile(r"[a-z][a-z0-9_./{}-]{3,}")
# Vocabulary every failure contains, so it says nothing about the CAUSE. Without this
# the HTTP envelope alone (statusCode/message/error/timestamp) scored 0.44 between two
# unrelated 400s — close enough to the real match to make any threshold meaningless.
_CAUSE_STOPWORDS = frozenset(
    [
        "fail",
        "soft",
        "expected",
        "assertionerror",
        "status",
        "statuscode",
        "timestamp",
        "error",
        "message",
        "request",
        "response",
        "test",
        "run",
        "with",
        "that",
        "this",
        "the",
        "and",
        "must",
        "call",
        "step",
        "none",
        "from",
        "when",
        "then",
        "they",
        "into",
        "returned",
        "answered",
        "got",
        "bad",
        "found",
        "null",
        "true",
        "false",
        "data",
        "body",
    ]
)


def _cause_tokens(text: str) -> set[str]:
    core = (text or "").split(" -- ", 1)[-1].lower()
    # Strip the per-run values first, as `_sig` does, so "Partner PAR-123 not found" and
    # "Partner PAR-456 not found" share their words instead of differing on the id.
    core = _NUM_RE.sub("", _ID_RE.sub("", _EMAIL_RE.sub("", core)))
    return {w for w in _CAUSE_WORD_RE.findall(core) if w not in _CAUSE_STOPWORDS}


_PLACEHOLDER_RE = re.compile(r"<(?:n|v|id|email)>")
_STATUS_CODE_RE = re.compile(r"(?:\bgot|\bstatus \(|\bHTTP)\s*([1-5]\d\d)\b", re.IGNORECASE)


def _status_codes(text: str) -> tuple[str, ...]:
    """HTTP status codes an assertion names ("Expected status (201,), got 400" → 201, 400)."""
    return tuple(_STATUS_CODE_RE.findall(text or ""))


def _sig_has_content(sig: str) -> bool:
    """False when a signature is nothing but placeholders and assertion boilerplate.

    `_QUOTED_RE` turns every quoted JSON value into '<v>', so ANY
    ``Expected status (201,), got 400: {json}`` signs as the same skeleton whatever the
    body says. Two equal skeletons prove nothing. Measured run_20261013_103101: TC-2061602
    failed on "Approval chain not assigned yet" but signed identically to BUG-API-043's
    billingCycle 400, so triage reported KNOWN OPEN BUG-API-043 and hid the real failure.
    """
    words = _CAUSE_WORD_RE.findall(_PLACEHOLDER_RE.sub(" ", sig))
    return sum(1 for w in words if w not in _CAUSE_STOPWORDS) >= 2


def _same_cause(old_evidence: str, new_evidence: str) -> bool:
    """Is this run's failure the cause already recorded on the bug?

    An unknown (blank) recorded cause counts as the same: never cry "changed" over
    a row that was simply never filled in.
    """
    if not old_evidence:
        return True
    old_sig = _sig(old_evidence)
    # Equal signatures settle it only when they still say something — see _sig_has_content.
    if old_sig == _sig(new_evidence) and _sig_has_content(old_sig):
        return True
    old, new = _cause_tokens(old_evidence), _cause_tokens(new_evidence)
    if old == new:
        if old:
            return True  # the same words once per-run values are stripped
        # No distinctive word on either side ("Expected status (201,), got 400" vs "… got
        # 500"): two EMPTY sets are equal but prove nothing — the status codes are all that
        # is left to tell a 400 from a new 5xx.
        return _status_codes(old_evidence) == _status_codes(new_evidence)
    shared = old & new
    if len(shared) < _CAUSE_MIN_SHARED:
        return False
    return len(shared) / max(1, min(len(old), len(new))) >= _CAUSE_OVERLAP


# Most assertions read "Expected <X>, got <Y>" / "Expected <X> got <Y>" — split that
# into the tracker's Expected/Actual columns. When there is no such pattern (e.g. a UI
# content-load banner), Actual = the observed evidence and Expected is left blank for a
# human to fill (never fabricated).
_EXP_GOT_RE = re.compile(r"[Ee]xpected\s+(.+?)[,;]?\s+got\s+(.+)", re.DOTALL)


def _expected_actual(evidence: str) -> tuple[str, str]:
    ev = (evidence or "").strip()
    m = _EXP_GOT_RE.search(ev)
    if m:
        return m.group(1).strip()[:250], m.group(2).strip()[:250]
    return "", ev[:250]


def _registry_lookup() -> dict[int, object]:
    """Best-effort {tc_id: TestCase} from the code registry (empty on any failure)."""
    try:
        from runner.tc_registry import TC_REGISTRY

        return dict(TC_REGISTRY)
    except Exception:  # noqa: BLE001 — enrichment is optional; a stub row still works
        return {}


def _feature_from_tc_string(tc_string: str) -> str:
    """Derive the functional feature from a TC string.

    ``PARTNER_API_AUTH_ACCESS_CONTROL_003`` -> ``AUTH_ACCESS_CONTROL``.
    """
    m = re.match(r"^[A-Z0-9]+_(?:API|UI)_(.+)_\d+$", tc_string or "")
    return m.group(1) if m else ""


def load_tracker(path: Path) -> dict[int, BugRow]:
    """Return ``{tc_id: BugRow}`` keyed by Test Case ID (empty if no file/sheet)."""
    if not path.exists():
        return {}
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    if _SHEET not in wb.sheetnames:
        return {}
    ws = wb[_SHEET]
    hdr = {str(c.value).strip().lower(): i for i, c in enumerate(ws[1], 1) if c.value}
    ci_bug, ci_tc, ci_st = hdr.get("bug id"), hdr.get("test case id"), hdr.get("status")
    ci_ev = hdr.get("evidence / assertion") or hdr.get("summary")
    out: dict[int, BugRow] = {}
    if not (ci_bug and ci_tc and ci_st):
        return out
    for row in ws.iter_rows(min_row=2):
        tc = _tc_int(str(row[ci_tc - 1].value or ""))
        if tc is None:
            continue
        out[tc] = BugRow(
            tc_id=tc,
            bug_id=str(row[ci_bug - 1].value or "").strip(),
            status=str(row[ci_st - 1].value or "").strip(),
            evidence=(str(row[ci_ev - 1].value or "").strip() if ci_ev else ""),
        )
    return out


# ── Section-aware Bug IDs ─────────────────────────────────────────────────────
# The tracker is split into an **API** section and a **UI** section, each opened by
# a bold header row (col A == "API" / "UI", the other columns blank). Bug IDs are
# prefixed + numbered per section: BUG-API-001.. and BUG-UI-001.. . New bugs are
# inserted at the END of their own section so ids stay stable and the two lists
# never interleave.
_SECTIONS = ("API", "UI")


def _is_ui(tc_id: int, tc_string: str = "") -> bool:
    """UI vs API classification for a test case (drives the Bug ID section)."""
    if "_UI_" in (tc_string or ""):
        return True
    if "_API_" in (tc_string or ""):
        return False
    # Fallback by id magnitude: UI ids are 8-digit and start with 1 (e.g. 12060515);
    # API ids are 7-digit and start with 2 (e.g. 2060234).
    return len(str(tc_id)) >= 8 and str(tc_id).startswith("1")


def _section_for(tc_id: int, tc_string: str = "") -> str:
    return "UI" if _is_ui(tc_id, tc_string) else "API"


def all_bug_ids(path: Path) -> list[str]:
    """Every Bug ID in the sheet, including rows that carry no Test Case ID.

    :func:`load_tracker` is keyed by TC id and therefore ``continue``s past any bug filed
    without one — which is a normal thing to file: BUG-API-021 records that DELETE partner
    is a soft delete, a defect no TC asserts. Allocating the next number from that dict
    handed out 021 a second time (measured 2026-09-16: two BUG-API-021 rows, one of them
    written by this module's own reconciliation). Numbering has to see the whole column.
    """
    if not path.exists():
        return []
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    if _SHEET not in wb.sheetnames:
        return []
    ws = wb[_SHEET]
    hdr = {str(c.value).strip().lower(): i for i, c in enumerate(ws[1], 1) if c.value}
    ci_bug = hdr.get("bug id")
    if not ci_bug:
        return []
    return [
        str(row[ci_bug - 1].value or "").strip()
        for row in ws.iter_rows(min_row=2)
        if str(row[ci_bug - 1].value or "").strip()
    ]


def _next_seq(bug_ids: list[str], section: str) -> int:
    """Highest existing sequence for BUG-<section>-NNN (0 if none).

    Takes the raw id list rather than the TC-keyed dict so a bug with no TC still reserves
    its number — see :func:`all_bug_ids`.
    """
    pat = re.compile(rf"BUG-{section}-0*(\d+)", re.IGNORECASE)
    mx = 0
    for bug_id in bug_ids:
        m = pat.match(bug_id or "")
        if m:
            mx = max(mx, int(m.group(1)))
    return mx


def _find_section_rows(ws) -> dict[str, int]:
    """{'API': header_row, 'UI': header_row} by scanning col A for the labels."""
    out: dict[str, int] = {}
    for r in range(1, ws.max_row + 1):
        label = str(ws.cell(r, 1).value or "").strip().upper()
        if label in _SECTIONS and (ws.cell(r, 2).value in (None, "")):
            out[label] = r
    return out


def _last_bug_row(ws, start: int, end: int) -> int:
    """Last row in (start, end) holding a Bug ID; else `start` (the section header)."""
    last = start
    for r in range(start + 1, end):
        if str(ws.cell(r, 1).value or "").upper().startswith("BUG-"):
            last = r
    return last


def _write_row(ws, idx: int, row: dict, hdr: dict[str, int]) -> None:
    for key, val in row.items():
        if key.startswith("_") or key not in hdr:  # skip transient hints (_section, …)
            continue
        cell = ws.cell(idx, hdr[key], val)
        # Test Case ID is a plain integer id, not a quantity — force the "0" number
        # format so it never renders with thousands separators (e.g. 12,060,102).
        if key == "Test Case ID":
            cell.number_format = "0"


def _append_rows(path: Path, rows: list[dict]) -> int:
    """Insert each new bug at the end of its section (API above UI).

    Each row carries a transient ``_section`` ("API"/"UI"). Rows are inserted (not
    appended at the sheet bottom) so API bugs stay in the API block and UI bugs in
    the UI block; the Status dropdown + colour rules span a fixed range (H2:H500),
    so inserted rows inherit them automatically.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path)  # not data_only → preserve styles
    ws = wb[_SHEET]
    hdr = {str(c.value).strip(): i for i, c in enumerate(ws[1], 1) if c.value}
    written = 0
    for section in _SECTIONS:
        batch = [r for r in rows if r.get("_section") == section]
        for row in batch:
            secs = _find_section_rows(ws)  # recompute — earlier inserts shift rows
            if section in secs:
                end = secs["UI"] if section == "API" and "UI" in secs else ws.max_row + 1
                idx = _last_bug_row(ws, secs[section], end) + 1
                ws.insert_rows(idx)
            else:  # fallback: no section header found → append at the bottom
                idx = ws.max_row + 1
            _write_row(ws, idx, row, hdr)
            written += 1
    # Any rows without a recognised section (shouldn't happen) → bottom-append.
    for row in (r for r in rows if r.get("_section") not in _SECTIONS):
        _write_row(ws, ws.max_row + 1, row, hdr)
        written += 1
    wb.save(path)
    return written


def reconcile(
    groups,
    *,
    passed_tc_ids: set[int] | None = None,
    tracker_path: Path = DEFAULT_TRACKER,
    allow_write: bool | None = None,
):
    """Compare app_bug failures to the tracker and PROPOSE new rows.

    Nothing is written unless writing is asked for. Appending used to be the default on
    every local run, and the result was a tracker nobody had agreed to: twelve rows
    (BUG-UI-013…024, BUG-API-044) appeared from ordinary runs on 2026-10-08/09, and most
    of them passed again days later — noise that still had to be read, triaged and closed
    by hand. Whether a failure deserves a bug is a human call, so the default is now to
    report the proposal and let someone make it.

    Opt in with ``allow_write=True`` or by exporting ``BUG_TRACKER_AUTOWRITE=1``. Writing
    is refused on CI either way.

    ``passed_tc_ids`` (the run's PASSED test-case ids) drives the RESOLVED report:
    an open bug whose TC passed this run is no longer reproducing → suggest closing
    it. Detection is suggest-only — the tracker's Status is never auto-changed.
    """
    res = Reconciliation(tracker=tracker_path)
    existing = load_tracker(tracker_path)
    is_ci = bool(os.environ.get("CI"))
    if allow_write is None:
        opted_in = os.environ.get("BUG_TRACKER_AUTOWRITE", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        allow_write = opted_in and (not is_ci) and tracker_path.exists()

    seen: set[int] = set()
    # (tc_id, group, covering_row): covering_row is an OPEN tracker bug that already
    # covers this TC's signature group (via a co-grouped, already-tracked TC). Groups
    # are signature-based — every TC in a group failed for the SAME reason — so an
    # untracked TC that shares a group with a tracked-open bug is the SAME defect: it
    # is reported as KNOWN OPEN under that bug, never appended as a duplicate.
    # Each candidate carries the failing TC's OWN evidence. A group's `evidence` is
    # just its first member's; judging the other members by it compares a bug against
    # someone else's assertion (and so reports a bogus SIGNATURE CHANGED / KNOWN OPEN).
    candidates: list[tuple[int, object, BugRow | None, str]] = []
    for g in groups:
        if getattr(g, "category", "") != "app_bug":
            continue  # only real defects (API + UI) — skip env/flaky/deploy noise
        group_ev = getattr(g, "evidence", "") or ""
        ev_by_tc = {
            n: ev
            for tc, ev in (getattr(g, "evidence_by_tc", None) or {}).items()
            if (n := _tc_int(tc)) is not None
        }
        tcs_int = [n for tc in getattr(g, "tcs", []) if (n := _tc_int(tc)) is not None]
        covering = next(
            (existing[n] for n in tcs_int if n in existing and not _is_closed(existing[n].status)),
            None,
        )
        for n in tcs_int:
            if n not in seen:
                seen.add(n)
                candidates.append((n, g, covering, ev_by_tc.get(n) or group_ev))

    reg = _registry_lookup()
    # Per-section running sequence (API / UI numbered independently).
    seen_ids = all_bug_ids(tracker_path)
    next_seq = {s: _next_seq(seen_ids, s) for s in _SECTIONS}
    to_append: list[dict] = []

    def _build_entry(tc_id: int, evidence_full: str) -> dict:
        tc = reg.get(tc_id)  # enrich from the code registry when available
        name = getattr(tc, "tc_string", "") if tc else ""
        section = _section_for(tc_id, name)
        next_seq[section] += 1
        bug_id = f"BUG-{section}-{next_seq[section]:03d}"
        title = ((getattr(tc, "title", "") if tc else "") or "").strip()
        evidence = (evidence_full or "")[:_EVIDENCE_CHARS]
        expected, actual = _expected_actual(evidence)
        # Expected must never be blank. If the assertion had no "Expected … got …"
        # pattern (e.g. UI defects: overflow, "accepts invalid …"), fall back to the
        # TC title — it states the intended/correct behavior — then to the evidence.
        if not expected:
            expected = title or evidence[:200] or "(expected behavior — see Test Case Name)"
        return {
            "Bug ID": bug_id,
            "_section": section,  # transient hint for _append_rows (not a column)
            "Test Case ID": tc_id,
            "Test Case Name": name,
            "Module": getattr(tc, "module", "").capitalize() if tc else "",
            "Feature": _feature_from_tc_string(name),
            "Severity": "Major",
            "Priority": getattr(tc, "priority", "P2") if tc else "P2",
            "Status": "Open",
            "Reported By": "AI Triage",
            "Date Opened": datetime.date.today().isoformat(),
            "Summary": title or evidence[:200],
            "Expected": expected,
            "Actual": actual or evidence[:250],
            "Evidence / Assertion": evidence,
            "Notes": "",  # left blank by request — no auto-generated note text
        }

    def _cause_twin(tc_id: int, g: object, new_evidence: str) -> BugRow | None:
        """The OPEN bug in this TC's cause group whose recorded cause matches the
        failure seen now — i.e. the bug this failure actually belongs to.

        A group can hold several tracked bugs (a win-endpoint group held BUG-API-041
        and BUG-API-043 at once), so "the first open one" names the wrong bug half the
        time. Matching on the recorded cause names the right one.
        """
        for tc in getattr(g, "tcs", []):
            n = _tc_int(tc)
            if n is None or n == tc_id:
                continue
            r = existing.get(n)
            if (
                r
                and not _is_closed(r.status)
                and r.evidence
                and _same_cause(r.evidence, new_evidence)
            ):
                return r
        return None

    for tc_id, g, covering, cur_ev_full in sorted(candidates, key=lambda c: c[0]):
        row = existing.get(tc_id)
        # Prefer the co-grouped bug whose recorded cause actually matches this failure;
        # fall back to the group's first open bug only when none does.
        twin = _cause_twin(tc_id, g, cur_ev_full)
        covering = twin or covering
        # Signatures are compared on the UNTRUNCATED evidence: `_sig` already caps its
        # own output, and pre-clipping the input changes the signature (a cut inside a
        # quoted JSON value), which would report the SAME failure as "signature changed".
        # The clipped copy is only for storing/displaying.
        cur_ev = cur_ev_full[:_EVIDENCE_CHARS]
        if row is None and covering is not None:
            # Untracked TC, but a co-grouped TC is an open tracked bug (same signature)
            # → covered by that bug. Report KNOWN OPEN under it, don't append a duplicate.
            res.known_open.append(
                BugRow(tc_id=tc_id, bug_id=covering.bug_id, status=covering.status)
            )
        elif row is None:
            entry = _build_entry(tc_id, cur_ev_full)
            res.new.append(entry)
            to_append.append(entry)
        elif _is_closed(row.status) and covering is not None:
            # This TC's own bug is closed, but a co-grouped TC is an open bug of the
            # SAME signature → this run's failure is that open bug, not a reopen of the
            # closed one. Report KNOWN OPEN under the covering bug, don't append.
            res.known_open.append(
                BugRow(tc_id=tc_id, bug_id=covering.bug_id, status=covering.status)
            )
        elif _is_closed(row.status):
            # A closed bug is failing again. If the failure matches the recorded
            # evidence (same root cause) → REOPEN the same bug. If it's a DIFFERENT
            # failure (or the old evidence is unknown to compare) → treat SAME-cause
            # as reopen (conservative, no duplicate); only a clearly-different
            # signature opens a NEW bug distinct from the closed one.
            same_cause = _same_cause(row.evidence, cur_ev_full)
            if same_cause:
                res.reopen.append(row)
            else:
                entry = _build_entry(tc_id, cur_ev_full)
                entry["_distinct_from"] = row.bug_id  # transient hint for render (not a column)
                res.new.append(entry)
                to_append.append(entry)
        else:
            # Open tracked bug. Check the failure STILL matches the cause recorded on
            # it — same asymmetry the closed branch already uses, now applied to open
            # bugs so a "cause swap" within one TC is not silently rolled into KNOWN
            # OPEN. A soft-collect TC can have one sub-cause fixed and another appear
            # (e.g. BUG-API-027 pagination fixed, a new malformed-id defect now
            # failing the same TC): the signature differs, so flag it.
            same_cause = _same_cause(row.evidence, cur_ev_full)
            if same_cause:
                res.known_open.append(row)
            else:
                res.changed.append(
                    {
                        "tc_id": tc_id,
                        "bug_id": row.bug_id,
                        "status": row.status,
                        "old_evidence": row.evidence,
                        "new_evidence": cur_ev,
                        # The cause now failing this TC may already be a logged bug
                        # (another TC in the same cause group). Naming it turns "log
                        # the new cause" into "repoint this TC at BUG-X" — no reading
                        # of the raw log, no duplicate bug.
                        "cause_of": twin.bug_id if twin else "",
                        "cause_of_tc": twin.tc_id if twin else 0,
                    }
                )

    # RESOLVED (mirror of REOPEN): an open bug whose TC PASSED this run no longer
    # reproduces → suggest closing it. Skip any TC that also failed this run (a
    # fail can't coexist with a pass, but guard anyway — a fail always wins).
    for tc_id in sorted(passed_tc_ids or ()):
        if tc_id in seen:
            continue
        row = existing.get(tc_id)
        if row is not None and not _is_closed(row.status):
            res.resolved.append(row)

    if to_append and allow_write:
        res.written = _append_rows(tracker_path, to_append)
        res.wrote_to_file = True
    return res


def render(res: Reconciliation) -> str:
    """Human-readable reconciliation block (safe for console + markdown).

    Sections are ordered most-actionable first (NEW → REOPEN → KNOWN OPEN →
    RESOLVED); RESOLVED is a close-suggestion, so it sits last. Within each section
    rows are sorted by Bug ID so the list reads in order (BUG-API-001, 002, …).
    """
    lines = ["", "── Bug Tracker reconciliation ──"]
    if not (res.new or res.known_open or res.reopen or res.resolved or res.changed):
        lines.append("  No defects to track. ✅")
        return "\n".join(lines)
    for e in sorted(res.new, key=lambda e: e["Bug ID"]):
        tag = "added" if res.wrote_to_file else "would add (propose-only)"
        distinct = e.get("_distinct_from")
        extra = f"; NEW defect, different from closed {distinct}" if distinct else ""
        lines.append(f"  🆕 NEW         {e['Bug ID']}  (TC-{e['Test Case ID']}) — {tag}{extra}")
    for r in sorted(res.reopen, key=lambda r: r.bug_id):
        lines.append(
            f"  ⚠  REOPEN      {r.bug_id}  (TC-{r.tc_id}) — CLOSED but the SAME failure is "
            f"back → reopen"
        )
    for c in sorted(res.changed, key=lambda c: c["bug_id"]):
        lines.append(
            f"  ⚠  SIGNATURE CHANGED  {c['bug_id']}  (TC-{c['tc_id']}) — still failing, but with "
            "a DIFFERENT signature than its recorded cause → the original cause looks FIXED and a "
            "NEW defect is now failing this TC. Review: close the old bug if fixed + log the new "
            "cause (1 bug per distinct failure)."
        )
        if c.get("old_evidence"):
            lines.append(f"       was: {str(c['old_evidence'])[:140]}")
        lines.append(f"       now: {str(c['new_evidence'])[:140]}")
        if c.get("cause_of"):
            lines.append(
                f"       ↳ this new cause is already logged as {c['cause_of']} "
                f"(TC-{c['cause_of_tc']}) → repoint TC-{c['tc_id']} at it, do NOT open a duplicate"
            )
    for r in sorted(res.known_open, key=lambda r: r.bug_id):
        lines.append(f"  🔵 KNOWN OPEN  {r.bug_id}  (TC-{r.tc_id}) — already tracked, still open")
    for r in sorted(res.resolved, key=lambda r: r.bug_id):
        lines.append(
            f"  ✅ RESOLVED    {r.bug_id}  (TC-{r.tc_id}) — passed this run, no longer "
            f"failing → safe to CLOSE (status is '{r.status}')"
        )
    if res.new:
        if res.wrote_to_file:
            lines.append(f"  → {res.written} row(s) appended to {res.tracker.name}")
        else:
            lines.append(
                f"  → PROPOSED only — nothing was written to {res.tracker.name}. "
                "Raise the ones you agree with by hand, or re-run with "
                "BUG_TRACKER_AUTOWRITE=1 to append them."
            )
    return "\n".join(lines)
