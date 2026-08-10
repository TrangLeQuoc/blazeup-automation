"""TC selection: which test cases a command actually resolves to.

A selection bug is quiet by nature — the run goes green over a smaller set than you
think it covered. `--exclude-marker` (the be_gap gate) is the newest source of that
risk, so its semantics are pinned here.
"""

import pytest

from runner.blazeup.registry import TC_REGISTRY
from runner.run_test import _PARTNER_PORTAL_SECTIONS, parse_tc_range

# ── parse_tc_range ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (["1"], [1]),
        (["1", "5"], [1, 5]),
        (["1-3"], [1, 2, 3]),
        (["1-3", "7"], [1, 2, 3, 7]),
        (["2060201-2060203"], [2060201, 2060202, 2060203]),
        (["5-5"], [5]),
    ],
)
def test_parse_tc_range(given, expected):
    assert parse_tc_range(given) == expected


@pytest.mark.parametrize("bad", [["abc"], ["1-x"], ["-"], [""]])
def test_parse_tc_range_drops_garbage_instead_of_crashing(bad):
    """A typo must not take the whole run down — it is warned about and skipped."""
    assert parse_tc_range(bad) == []


def test_parse_tc_range_keeps_a_valid_id_next_to_a_bad_one():
    assert parse_tc_range(["7", "oops"]) == [7]


# ── be_gap exclusion (the merge gate) ────────────────────────────────────────
# Mirrors what main() does after resolving the selection.


def _exclude(tc_ids, markers):
    excluded = set(markers)
    return [
        tc_id
        for tc_id in tc_ids
        if not (TC_REGISTRY.get(tc_id) and excluded & set(TC_REGISTRY[tc_id].markers))
    ]


def _ids_with(marker):
    return [i for i, tc in TC_REGISTRY.items() if marker in tc.markers]


def test_be_gap_tcs_exist_to_be_excluded():
    """If this ever hits zero the gate is silently a no-op."""
    assert len(_ids_with("be_gap")) > 0


def test_excluding_be_gap_removes_exactly_the_marked_tcs():
    all_ids = sorted(TC_REGISTRY)
    kept = _exclude(all_ids, ["be_gap"])
    assert len(kept) == len(all_ids) - len(_ids_with("be_gap"))
    assert not any("be_gap" in TC_REGISTRY[i].markers for i in kept)


def test_exclusion_keeps_unmarked_tcs_untouched():
    plain = [i for i, tc in TC_REGISTRY.items() if "be_gap" not in tc.markers]
    assert _exclude(sorted(plain), ["be_gap"]) == sorted(plain)


def test_excluding_an_unused_marker_changes_nothing():
    all_ids = sorted(TC_REGISTRY)
    assert _exclude(all_ids, ["no_such_marker"]) == all_ids


# ── Preflight surface routing ────────────────────────────────────────────────
# Which origin a UI test needs is derived from its TC string. If a partner-portal
# section is missing from this list, preflight probes the wrong host and a real
# outage slips through.


def test_partner_portal_sections_match_real_tcs():
    """Every declared section must actually exist in the registry (no dead entries)."""
    for section in _PARTNER_PORTAL_SECTIONS:
        assert any(f"_UI_{section}_" in tc.tc_string for tc in TC_REGISTRY.values()), (
            f"section {section!r} matches no TC — stale entry in _PARTNER_PORTAL_SECTIONS"
        )


def test_every_ui_tc_routes_to_exactly_one_origin():
    """No UI TC may be unclassifiable: it is either portal or SA, never ambiguous."""
    for tc in TC_REGISTRY.values():
        if tc.type != "ui":
            continue
        hits = [s for s in _PARTNER_PORTAL_SECTIONS if f"_UI_{s}_" in tc.tc_string]
        assert len(hits) <= 1, f"{tc.tc_string} matches several portal sections: {hits}"
