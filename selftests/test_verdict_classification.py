"""The BLOCKED-vs-FAILED decision, and how a run is turned into a summary row.

Why this file matters most: `_is_blocked` decides whether a red test is reported as
an ENVIRONMENT problem or a DEFECT. A false positive here is the dangerous direction —
a genuine product bug gets filed as "staging was flaky" and nobody looks at it again.
The rules are plain substring matches, so they are easy to get subtly wrong (Gap 6
showed exactly that: a bare "503" pattern also matched a mongo id).
"""

import textwrap

import pytest

# Aliased: pytest would otherwise try to collect a class named Test* as a test class.
from runner.tc_registry import TestCase as _TC
from runner.test_runner import _error_type_label, _is_blocked, parse_junit_xml

# ── _is_blocked ──────────────────────────────────────────────────────────────
# Real messages this suite produces. The MUST-NOT list is the important half.

BLOCKED_MESSAGES = [
    "BLOCKED: shared partner UI login failed — precondition failed: ...",
    "BLOCKED: SA UI login failed — service unreachable",
    "AssertionError: Expected status (200,), got 502: <html>Bad Gateway</html>",
    "AssertionError: Expected status (200,), got 503: Service Unavailable",
    "AssertionError: Expected status (200,), got 504",
    "httpx.ConnectError: [Errno 111] Connection refused",
    "httpx.ReadTimeout",
    "httpx.ConnectTimeout",
    "socket.gaierror: [Errno 11001] getaddrinfo failed",
    "Max retries exceeded with url",
    "Service Unavailable",
    "Gateway Timeout",
]

NOT_BLOCKED_MESSAGES = [
    # A bare 500 is deliberately NOT a block: the service is up and crashed on the
    # request, which is an application bug. See the comment on _BLOCKED_SIGNATURES.
    "AssertionError: Expected status (200,), got 500: Internal Server Error",
    "AssertionError: Expected status (404,), got 400: Partner not found",
    "AssertionError: re-granting must not duplicate the certification",
    "AssertionError: the partner should no longer be Active after Deactivate",
    "AssertionError: response time 31000ms exceeded limit 30000ms for GET /v1/sa/partners",
    "playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 60000ms exceeded.",
]


@pytest.mark.parametrize("message", BLOCKED_MESSAGES)
def test_is_blocked_recognises_environment_failures(message):
    assert _is_blocked(message) is True, f"should be BLOCKED: {message!r}"


@pytest.mark.parametrize("message", NOT_BLOCKED_MESSAGES)
def test_is_blocked_does_not_swallow_real_defects(message):
    assert _is_blocked(message) is False, (
        f"must stay FAILED (reporting it as BLOCKED hides a defect): {message!r}"
    )


def test_is_blocked_is_case_insensitive():
    assert _is_blocked("blocked: shared login down")
    assert _is_blocked("BLOCKED: SHARED LOGIN DOWN")


def test_is_blocked_handles_empty_and_none():
    assert _is_blocked("") is False
    assert _is_blocked(None) is False  # type: ignore[arg-type]


# ── _error_type_label ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("status", "err_type", "message", "expected"),
    [
        ("BLOCKED", "whatever", "msg", "BLOCKED"),
        ("SKIPPED", "", "", "SKIP"),
        ("PASSED", "", "", ""),
        # A dotted type is reduced to the bare class name.
        ("FAILED", "playwright._impl._errors.TimeoutError", "", "TimeoutError"),
        ("FAILED", "AssertionError", "", "AssertionError"),
        # No type given → sniff it out of the message. httpx timeout names end in
        # "Timeout", not "Error", and used to be mislabelled "AssertionError".
        ("FAILED", "", "httpx.ReadTimeout: timed out", "ReadTimeout"),
        ("FAILED", "", "httpx.ConnectTimeout", "ConnectTimeout"),
        ("FAILED", "", "httpx.PoolTimeout: pool is full", "PoolTimeout"),
        # A bare "Timeout" is not a class name — needs a word part in front of it.
        ("FAILED", "", "Locator.wait_for: Timeout 60000ms exceeded", "AssertionError"),
        # Nothing to go on → default rather than an empty column.
        ("FAILED", "", "something went sideways", "AssertionError"),
    ],
)
def test_error_type_label(status, err_type, message, expected):
    assert _error_type_label(status, err_type, message) == expected


# ── parse_junit_xml ──────────────────────────────────────────────────────────

_TC_PASS = _TC(1, "X_API_Y_001", "api", "m", "t", "tests/x.py", "test_pass_one")
_TC_FAIL = _TC(2, "X_API_Y_002", "api", "m", "t", "tests/x.py", "test_fail_one")
_TC_BLOCK = _TC(3, "X_API_Y_003", "api", "m", "t", "tests/x.py", "test_block_one")

_JUNIT = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="3">
  <testcase classname="tests.x" name="test_pass_one" time="1.5"/>
  <testcase classname="tests.x" name="test_fail_one" time="2.0">
    <failure type="AssertionError" message="Expected status (404,), got 400">boom</failure>
  </testcase>
  <testcase classname="tests.x" name="test_block_one" time="0.7">
    <skipped type="pytest.skip" message="BLOCKED: shared partner UI login failed"/>
  </testcase>
</testsuite></testsuites>
"""


def _rows_by_tc(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text(textwrap.dedent(_JUNIT), encoding="utf-8")
    rows = parse_junit_xml(junit, [_TC_PASS, _TC_FAIL, _TC_BLOCK])
    return {row["tc_id"]: row for row in rows}


def test_parse_junit_reports_a_row_per_requested_tc(tmp_path):
    assert len(_rows_by_tc(tmp_path)) == 3


def test_parse_junit_marks_a_passing_test_pass(tmp_path):
    assert _rows_by_tc(tmp_path)["1"]["status"] == "PASSED"


def test_parse_junit_marks_a_real_assertion_failure_fail(tmp_path):
    row = _rows_by_tc(tmp_path)["2"]
    assert row["status"] == "FAILED", "an assertion failure must not be softened to BLOCK"


def test_parse_junit_marks_a_precondition_skip_block(tmp_path):
    row = _rows_by_tc(tmp_path)["3"]
    assert row["status"] == "BLOCKED", "a 'BLOCKED:' skip is an environment block, not a pass"


def test_parse_junit_missing_file_does_not_crash():
    """A crashed pytest leaves no XML — the runner must still report every TC."""
    from pathlib import Path

    rows = parse_junit_xml(Path("no/such/junit.xml"), [_TC_PASS, _TC_FAIL])
    assert len(rows) == 2
    assert all(row["status"] != "PASSED" for row in rows), (
        "no evidence of a pass must never be reported as a pass"
    )
