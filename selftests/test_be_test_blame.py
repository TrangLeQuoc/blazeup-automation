"""Turning a red backend unit test into "who changed what, and did they update the test".

A wrong blame is worse than none — it sends someone to the wrong commit and burns the
report's credibility. So the two judgement calls are pinned hard here:

* which string out of the diff to search git for. Pick a structural key like ``"path"``
  and ``git log -S`` matches half the history; pick nothing and the tool is useless.
* whether the commit that introduced it also updated the failing spec. That is the
  difference between "the code is wrong" and "the test is stale".

The git half runs against a real repository built in tmp_path, so the pickaxe search is
exercised for real rather than mocked.
"""

import os
import subprocess
from datetime import date

import pytest

from utils.be_test_blame import (
    Failure,
    assertion_kind,
    blame_token,
    distinguishing_tokens,
    parse_jest_json,
    summary,
)

# Trimmed from the real failure on 2026-08-12 — app.module.spec.ts pins the middleware
# exclusion list with toEqual, and the code gained one route the test never learned about.
REAL_MESSAGE = """Error: expect(received).toEqual(expected) // deep equality

- Expected  - 0
+ Received  + 4

@@ -3,10 +3,14 @@
      "method": 5,
      "path": "v1/partner/auth/login",
    },
    Object {
      "method": 5,
+     "path": "v1/partner/auth/forgot-password",
+   },
+   Object {
+     "method": 5,
      "path": "v1/partner/auth/refresh",
    },
    at Object.<anonymous> (modules/app.module.spec.ts:76:28)
"""


# ── reading jest --json ─────────────────────────────────────────────────────


def test_a_failing_assertion_is_extracted_with_its_location():
    data = {
        "testResults": [
            {
                "name": "/repo/src/modules/app.module.spec.ts",
                "assertionResults": [
                    {"status": "passed", "fullName": "fine", "failureMessages": []},
                    {
                        "status": "failed",
                        "fullName": "AppModule wires trace middleware",
                        "failureMessages": [REAL_MESSAGE],
                    },
                ],
            }
        ]
    }
    failures = parse_jest_json(data)
    assert len(failures) == 1, "passing assertions must not be reported"
    assert failures[0].spec == "modules/app.module.spec.ts"
    assert failures[0].line == 76
    assert failures[0].test == "AppModule wires trace middleware"


def test_no_failures_yields_nothing():
    data = {"testResults": [{"name": "x", "assertionResults": [{"status": "passed"}]}]}
    assert parse_jest_json(data) == []


# A suite that fails to LOAD reports no assertions at all — its error is on the suite.
# Reading only assertionResults under-counted silently: measured 2026-08-13, jest said 3
# failed suites while the report listed 1, because two specs died on
# "UNKNOWN: unknown error, open '...node_modules/...'". The totals block is what exposed it.
SUITE_DIED = {
    "testResults": [
        {
            "name": "/repo/src/modules/partner/__tests__/clients.partner.controller.spec.ts",
            "status": "failed",
            "assertionResults": [],
            "message": (
                "● Test suite failed to run\n\n"
                "    UNKNOWN: unknown error, open '/repo/node_modules/asynckit/index.js'"
            ),
        }
    ]
}


def test_a_suite_that_never_ran_is_still_reported():
    failures = parse_jest_json(SUITE_DIED)
    assert len(failures) == 1
    assert failures[0].suite_level is True
    assert "Test suite failed to run" in failures[0].message


def test_a_suite_level_failure_is_not_blamed_on_a_commit(tmp_path):
    """There is no diff, so hunting for a commit would point at an innocent change."""
    from utils.be_test_blame import render

    report = render(tmp_path, parse_jest_json(SUITE_DIED)[0], date(2026, 8, 13))
    assert "SUITE FAILED TO RUN" in report
    assert "Introduced" not in report, "must not name a commit it cannot know"
    assert "npx jest" in report, "should say how to reproduce it alone"


def test_a_failed_suite_with_a_failed_assertion_is_reported_once():
    """app.module.spec.ts is BOTH a failed suite and a failed assertion — not two entries."""
    data = {
        "testResults": [
            {
                "name": "/repo/src/modules/app.module.spec.ts",
                "status": "failed",
                "assertionResults": [
                    {
                        "status": "failed",
                        "fullName": "AppModule x",
                        "failureMessages": [REAL_MESSAGE],
                    }
                ],
                "message": "● AppModule › x",
            }
        ]
    }
    failures = parse_jest_json(data)
    assert len(failures) == 1
    assert failures[0].suite_level is False


# ── the run totals ──────────────────────────────────────────────────────────
# `--run` invokes the same jest the `npm test` script does, over the same suite. Printing
# these totals is what makes running both unnecessary — without them you would still go
# back to `npm test` for the numbers, i.e. run 1052 tests twice.

FULL_RUN = {
    "numTotalTestSuites": 75,
    "numPassedTestSuites": 74,
    "numFailedTestSuites": 1,
    "numPendingTestSuites": 0,
    "numTotalTests": 1052,
    "numPassedTests": 1051,
    "numFailedTests": 1,
    "numPendingTests": 0,
    "startTime": 1_000_000,
    "testResults": [{"endTime": 1_131_409}],
}


def test_the_totals_match_what_npm_test_prints():
    out = summary(FULL_RUN)
    assert "Test Suites: 1 failed, 74 passed, 75 total" in out
    assert "Tests:       1 failed, 1051 passed, 1052 total" in out
    assert "Time:        131.4 s" in out


def test_an_all_green_run_omits_the_failed_count():
    green = {**FULL_RUN, "numFailedTestSuites": 0, "numFailedTests": 0}
    green |= {"numPassedTestSuites": 75, "numPassedTests": 1052}
    out = summary(green)
    assert "failed" not in out
    assert "Test Suites: 75 passed, 75 total" in out


def test_pending_tests_are_reported_when_present():
    out = summary({**FULL_RUN, "numPendingTests": 3})
    assert "3 pending" in out


def test_a_run_with_no_timing_says_so_instead_of_crashing():
    out = summary({"numTotalTests": 1, "numPassedTests": 1, "testResults": []})
    assert "Time:        ?" in out


# ── choosing the string to search for ───────────────────────────────────────


def test_the_value_that_moved_is_chosen_not_the_structure():
    """`"path"` and `"method"` also appear in the unchanged context — searching git for
    either would match nearly every commit. Only the value on one side is usable."""
    tokens = distinguishing_tokens(REAL_MESSAGE)
    assert tokens[0] == "v1/partner/auth/forgot-password"
    assert "path" not in tokens
    assert "method" not in tokens


def test_a_value_present_on_both_sides_is_not_a_difference():
    message = """
- Expected
+ Received
      "path": "v1/partner/auth/login",
+     "path": "v1/partner/auth/login",
"""
    assert "v1/partner/auth/login" not in distinguishing_tokens(message)


@pytest.mark.parametrize("noise", ["5", "12", "true", "null", "abc"])
def test_numbers_booleans_and_very_short_strings_are_not_candidates(noise):
    """Searching git for `5` or `true` returns the whole history."""
    message = f'- Expected\n+ Received\n+     "x": "{noise}",\n'
    assert noise not in distinguishing_tokens(message)


def test_a_diff_with_no_strings_yields_nothing():
    """expect(count).toBe(3) gives the pickaxe nothing — the caller must say so, not guess."""
    message = (
        "Error: expect(received).toBe(expected)\n\n- Expected  - 1\n+ Received  + 1\n- 3\n+ 4\n"
    )
    assert distinguishing_tokens(message) == []


def test_candidates_are_ordered_longest_first():
    """The longest distinct value is the most specific thing to search for."""
    message = '- Expected\n+ Received\n+ "abcd"\n+ "a-much-longer-token"\n'
    assert distinguishing_tokens(message) == ["a-much-longer-token", "abcd"]


# ── how the assertion is written ────────────────────────────────────────────


def test_a_whole_list_assertion_is_called_out():
    """Explains WHY one added route breaks it — the test pins the entire array."""
    kind = assertion_kind(REAL_MESSAGE, "    expect(excludedRoutes).toEqual([")
    assert "toEqual" in kind and "WHOLE list" in kind


def test_a_plain_assertion_is_just_named():
    assert assertion_kind(REAL_MESSAGE, "    expect(x).toEqual(y)") == "toEqual"


def test_an_unreadable_spec_line_still_names_the_matcher():
    assert assertion_kind(REAL_MESSAGE, None) == "toEqual"


# ── the git lookups ─────────────────────────────────────────────────────────


def _run(repo, *args, author: tuple[str, str] = ("QA", "qa@example.invalid")):
    """Run git against *repo* with a fully controlled identity and no inherited git state.

    The identity goes through ``GIT_AUTHOR_*``/``GIT_COMMITTER_*`` rather than
    ``-c user.name=``, because git EXPORTS those variables to its hooks and an environment
    variable beats config. Measured 2026-09-16: this fixture passed when the suite was run by
    hand and failed the moment it ran from a pre-commit hook, with
    ``assert 'Le Quoc Trang' == 'Khoa Nguyen'`` — the real committer leaking into a fixture
    that thought it had set the author.

    ``GIT_DIR``/``GIT_INDEX_FILE``/``GIT_WORK_TREE`` are dropped for the same reason and a
    worse failure mode: a hook exports them too, and an inherited ``GIT_DIR`` would point
    these throwaway commands at the REAL repository regardless of ``cwd``.
    """
    name, email = author
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_AUTHOR_NAME=name,
        GIT_AUTHOR_EMAIL=email,
        GIT_COMMITTER_NAME=name,
        GIT_COMMITTER_EMAIL=email,
    )
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env)


@pytest.fixture
def repo(tmp_path):
    """A history shaped like the real one: a commit adds a value to code and updates SOME
    specs, but not the spec that pins it."""
    root = tmp_path / "backend"
    (root / "src" / "modules").mkdir(parents=True)
    _run(root, "init", "-q")

    code = root / "src" / "modules" / "app.module.ts"
    pinning_spec = root / "src" / "modules" / "app.module.spec.ts"
    other_spec = root / "src" / "modules" / "auth.service.spec.ts"

    code.write_text("routes = ['login', 'refresh']\n", encoding="utf-8")
    pinning_spec.write_text("expect(routes).toEqual(['login', 'refresh'])\n", encoding="utf-8")
    other_spec.write_text("it('logs in', () => {})\n", encoding="utf-8")
    _run(root, "add", "-A")
    _run(root, "commit", "-q", "-m", "initial", author=("Someone", "someone@example.invalid"))

    # the change: code gains the route, ONE spec is updated, the pinning spec is not
    code.write_text("routes = ['login', 'forgot-password', 'refresh']\n", encoding="utf-8")
    other_spec.write_text("it('logs in', () => {})\nit('forgot-password', () => {})\n", "utf-8")
    _run(root, "add", "-A")
    _run(
        root,
        "commit",
        "-q",
        "-m",
        "feat(auth): self-service forgot-password",
        author=("Khoa Nguyen", "khoa@example.invalid"),
    )
    return root


def test_the_commit_that_introduced_the_value_is_found(repo):
    blame = blame_token(repo, "forgot-password", "modules/app.module.spec.ts")
    assert len(blame.commits) == 1
    assert blame.commits[0]["author"] == "Khoa Nguyen"
    assert "forgot-password" in blame.commits[0]["subject"]


def test_the_files_that_commit_touched_are_recorded(repo):
    """Whether it updated OTHER specs is what separates 'stale test' from 'wrong code'."""
    blame = blame_token(repo, "forgot-password", "modules/app.module.spec.ts")
    files = blame.commits[0]["files"]
    assert "src/modules/app.module.ts" in files
    assert "src/modules/auth.service.spec.ts" in files
    assert "src/modules/app.module.spec.ts" not in files, "the pinning spec was missed"
    assert blame.commits[0]["specs"] == ["src/modules/auth.service.spec.ts"]


def test_a_spec_that_never_knew_is_reported_as_such(repo):
    """Distinguishes 'never added' from 'added then removed' — different people to talk to."""
    blame = blame_token(repo, "forgot-password", "modules/app.module.spec.ts")
    assert blame.spec_ever_knew is False


def test_a_spec_that_does_know_is_reported_as_such(repo):
    blame = blame_token(repo, "forgot-password", "modules/auth.service.spec.ts")
    assert blame.spec_ever_knew is True


def test_a_value_no_commit_introduced_yields_no_commits(repo):
    """Points at a shared package, config or the environment instead — never a wrong guess."""
    blame = blame_token(repo, "never-existed-anywhere", "modules/app.module.spec.ts")
    assert blame.commits == []


# ── end to end ──────────────────────────────────────────────────────────────


def test_the_report_names_the_commit_and_says_the_spec_was_missed(repo):
    from utils.be_test_blame import render

    failure = Failure(
        spec="modules/app.module.spec.ts",
        test="AppModule pins the route list",
        message=REAL_MESSAGE.replace("v1/partner/auth/forgot-password", "forgot-password"),
        line=1,
    )
    report = render(repo, failure, date(2026, 8, 12))
    assert "Khoa Nguyen" in report
    assert "did NOT touch modules/app.module.spec.ts" in report
    assert "has NEVER mentioned" in report
    assert "TEST being stale" in report
