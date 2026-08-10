"""TC identity: function name → TC string → numeric id.

`utils/sync_registry.py` decides which test functions become test cases and what id
each one gets. Nothing verifies its output today: if it silently stops recognising a
function, that TC just vanishes from the registry — `run_test` can no longer select
it, and the only symptom is a number in a report being smaller than you expected.

The strongest test here is the round-trip over the REAL registry: it turns all 124
committed test cases into assertions for free, so a change in the id formula or in
config.yaml cannot land unnoticed.
"""

import ast

import pytest

from runner.blazeup.registry import TC_REGISTRY
from utils.sync_registry import (
    _extract_markers,
    _func_name_to_tc_string,
    tc_id_from_string,
    tc_string_from_id,
)

_DOMAIN = "blazeup"


# ── The whole committed registry must survive a round trip ───────────────────


@pytest.mark.parametrize("tc_id", sorted(TC_REGISTRY))
def test_every_registered_tc_string_maps_back_to_its_id(tc_id):
    """tc_string → id must reproduce exactly the id stored in the registry."""
    tc = TC_REGISTRY[tc_id]
    assert tc_id_from_string(tc.tc_string, _DOMAIN) == tc_id, (
        f"{tc.tc_string} no longer maps to {tc_id} — the id formula or config.yaml "
        f"changed and the committed registry is now stale"
    )


@pytest.mark.parametrize("tc_id", sorted(TC_REGISTRY))
def test_every_registered_test_func_maps_back_to_its_tc_string(tc_id):
    """func name → tc_string must reproduce what the registry stored."""
    tc = TC_REGISTRY[tc_id]
    assert _func_name_to_tc_string(tc.test_func, _DOMAIN) == tc.tc_string, (
        f"{tc.test_func}() would no longer be recognised as {tc.tc_string} — "
        f"this TC would silently disappear from the registry"
    )


def test_registry_ids_are_unique():
    strings = [tc.tc_string for tc in TC_REGISTRY.values()]
    assert len(strings) == len(set(strings)), "two TCs share one TC string"


def test_registry_is_not_empty():
    """Guards the failure mode where a parsing bug empties the registry entirely."""
    assert len(TC_REGISTRY) > 100, f"registry collapsed to {len(TC_REGISTRY)} TCs"


# ── tc_id_from_string: the formula itself ────────────────────────────────────


def test_ui_id_keeps_the_leading_type_digit():
    # {type=1}{project=2}{module=06}{section=05}{seq=13}
    assert tc_id_from_string("PARTNER_UI_SA_PARTNER_MODULE_013", _DOMAIN) == 12060513


def test_api_id_starts_with_zero_so_it_renders_as_7_digits():
    # type=0 → the leading zero is dropped by int()
    assert tc_id_from_string("PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002", _DOMAIN) == 2060102


@pytest.mark.parametrize(
    "bad",
    [
        "TOO_SHORT",  # fewer than 4 parts
        "PARTNER_UI_MY_PIPELINE_abc",  # seq not numeric
        "PARTNER_UI_MY_PIPELINE_000",  # seq below range
        "PARTNER_UI_MY_PIPELINE_100",  # seq above range (max 99)
        "NOSUCHMODULE_UI_THING_001",  # module not in config.yaml
        "PARTNER_UI_NOSUCHSECTION_001",  # section not in config.yaml
    ],
)
def test_unmappable_tc_strings_return_zero(bad):
    assert tc_id_from_string(bad, _DOMAIN) == 0, f"{bad!r} must not produce an id"


def test_tc_string_from_id_reverses_a_known_id():
    assert tc_string_from_id(12060513) == "PARTNER_UI_SA_PARTNER_MODULE_13"


# ── _func_name_to_tc_string: which functions become TCs ──────────────────────


def test_valid_function_name_is_recognised():
    assert (
        _func_name_to_tc_string("test_partner_ui_my_pipeline_001", _DOMAIN)
        == "PARTNER_UI_MY_PIPELINE_001"
    )


@pytest.mark.parametrize(
    "name",
    [
        "helper_partner_ui_my_pipeline_001",  # not a test_ function
        "test_partner_ui_my_pipeline",  # no sequence number
        "test_partner_ui_my_pipeline_1",  # sequence must be 3 digits
        "test_partner_ui_my_pipeline_0001",  # 4 digits is not 3
        "test_nosuchmodule_ui_thing_001",  # module not registered for the domain
        "test_tca02_something_401",  # legacy naming must not be picked up
    ],
)
def test_non_conforming_names_are_not_turned_into_tcs(name):
    assert _func_name_to_tc_string(name, _DOMAIN) is None, (
        f"{name!r} must not be registered as a test case"
    )


# ── _extract_markers: markers drive smoke / regression / be_gap selection ─────


def _markers_of(source: str) -> list[str]:
    node = ast.parse(source).body[0]
    return _extract_markers(node)  # type: ignore[arg-type]


def test_markers_are_extracted_from_decorators():
    assert _markers_of("@pytest.mark.api\n@pytest.mark.regression\ndef test_x():\n    pass\n") == [
        "api",
        "regression",
    ]


def test_markers_work_on_async_tests():
    assert _markers_of("@pytest.mark.be_gap\nasync def test_x():\n    pass\n") == ["be_gap"]


def test_undecorated_test_has_no_markers():
    assert _markers_of("def test_x():\n    pass\n") == []


def test_non_pytest_decorators_are_ignored():
    assert _markers_of("@functools.cache\ndef test_x():\n    pass\n") == []
