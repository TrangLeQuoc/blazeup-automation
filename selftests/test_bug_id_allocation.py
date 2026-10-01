"""A new Bug ID must never collide with one already in the tracker.

Measured 2026-09-16: the tracker ended up with TWO `BUG-API-021` rows — the original (DELETE
partner is a soft delete, filed with **no** Test Case ID because no TC asserts it) and a
second one this module's own reconciliation appended for TC-2061401.

Cause: numbering read `load_tracker()`, which is keyed by Test Case ID and `continue`s past
any row without one. A bug filed against no TC is normal, so its number was invisible and got
handed out again. Numbering now reads the whole Bug ID column via `all_bug_ids()`.

The duplicate is quiet: both rows look fine on their own, and the `be_gap` traceability chain
(marker -> TEST_CASES docs -> tracker) still resolves, because it matches on the bug id and
finds *a* row. It only surfaces when someone follows the id and lands on the wrong defect.
"""

import openpyxl
import pytest

from utils.bug_tracker import (
    _SHEET,
    DEFAULT_TRACKER,
    _next_seq,
    all_bug_ids,
    load_tracker,
)


def make_tracker(tmp_path, rows):
    """A tracker sheet shaped like the real one: (bug_id, tc_id) pairs, tc_id may be None."""
    path = tmp_path / "Bug_Tracker.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = _SHEET
    ws.append(["Bug ID", "Test Case ID", "Test Case Name", "Status"])
    for bug_id, tc_id in rows:
        ws.append([bug_id, tc_id, "", "Open"])
    wb.save(path)
    return path


def test_a_bug_with_no_test_case_still_reserves_its_number(tmp_path):
    """The exact shape that caused the collision."""
    path = make_tracker(
        tmp_path,
        [("BUG-API-020", 2060234), ("BUG-API-021", None)],  # 021 filed against no TC
    )
    assert _next_seq(all_bug_ids(path), "API") == 21, (
        "numbering must see BUG-API-021 even though no TC points at it"
    )


def test_the_tc_keyed_view_is_the_one_that_cannot_see_it(tmp_path):
    """Pins the cause, so a future refactor back to load_tracker() fails here first."""
    path = make_tracker(tmp_path, [("BUG-API-020", 2060234), ("BUG-API-021", None)])
    keyed = load_tracker(path)
    assert 2060234 in keyed
    assert not [r for r in keyed.values() if r.bug_id == "BUG-API-021"], (
        "load_tracker is keyed by TC id — a TC-less row is absent BY DESIGN; "
        "that is why allocation must not read it"
    )


@pytest.mark.parametrize("section", ["API", "UI"])
def test_sections_are_numbered_independently(tmp_path, section):
    path = make_tracker(
        tmp_path,
        [("BUG-API-007", None), ("BUG-UI-003", None)],
    )
    assert _next_seq(all_bug_ids(path), section) == (7 if section == "API" else 3)


def test_an_empty_or_missing_tracker_starts_at_zero(tmp_path):
    assert all_bug_ids(tmp_path / "nope.xlsx") == []
    assert _next_seq([], "API") == 0


def test_the_real_tracker_has_no_duplicate_bug_ids():
    """The repo's own tracker — this is the assertion that was red on 2026-09-16."""
    ids = [b for b in all_bug_ids(DEFAULT_TRACKER) if b.upper().startswith("BUG-")]
    dupes = sorted({b for b in ids if ids.count(b) > 1})
    assert not dupes, (
        f"duplicate Bug ID(s) in {DEFAULT_TRACKER.name}: {dupes}. Two defects sharing an id "
        "means following one from a test message lands on the wrong bug."
    )
