"""Tests must not reach past the page objects into raw Playwright selectors.

The UI stack is three layers: `locators/` holds the selector strings, `pages/` turns
them into actions, `tests/` calls those actions. When a test skips a layer and does
`shell.page.locator("main")` or `page.get_by_role("button", name="Open profile menu")`
the selector ends up living in two layers, and the usual outcome is not a clean break:

* Measured 2026-08-11 — `test_dashboard.py` asserted the literal "Tier & Performance"
  while `partner_shell_locators.py` already declared it as the dashboard READY_MARKER.
  Renaming the heading fixes the page object, `wait_ready()` keeps working, and only
  the one hardcoded assertion goes red — so it reads as a product bug, and whoever
  investigates finds the page object already correct.
* Same file kept its own 5-phrase error list next to the locators' 3-phrase
  CONTENT_ERROR_TEXTS. Adding a phrase to either left the other blind.

WHAT IS ALLOWED: calling a selector on a locator the page object handed back —
`wiz.dialog().get_by_text("Referral")`, `summary.get_by_text(value)`. The ROOT comes
from the page object; only the expected text is in the test, and that text is what the
test is about. Six such calls exist on purpose.

WHAT IS BANNED: a selector call on a Page — `page.locator(...)`, `shell.page.get_by_*(...)`.
That is the layer skip, because a Page gives access to the whole document and the
selector has to be written from scratch.

NOT CHECKED HERE: hardcoded marker/route literals. Measured on the current suite, every
match was a comment, a network-URL check, or a deliberate expected-route set — a guard on
those would be all false positives, so it would just get muted.
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = PROJECT_ROOT / "tests"

# A selector call made on a Page: bare `page.` or an attribute access ending in `.page`
# (`shell.page.`, `self.page.`). Playwright's selector entry points only.
RAW_PAGE_SELECTOR_RE = re.compile(
    r"\b(?:page|\w+\.page)\.(?:locator|get_by_\w+|query_selector|query_selector_all)\("
)

# The API-side twin of the same rule: a service path literal ("/sa-partners-api/v1/...").
# Those belong to a client in api_clients/, which declares the path and exposes a method.
# Measured 2026-08-11 before the fix: the partner-portal prefix was declared in four test
# modules under three names (_BASE, _PORTAL, _DASHBOARD_PATH) plus once inline in a UI
# test, because no client existed for that surface — five copies of one string.
RAW_ENDPOINT_RE = re.compile(r"""['"](/[a-z][a-z0-9-]*-api/[^'"]*)['"]""")

# A bare HTTP verb on a client (`await portal.get(...)`) instead of a named method. After
# the endpoints moved into the clients there is exactly ONE legitimate case left: a test
# hitting a partner path with a NON-partner client to prove it is refused, which passes a
# declared constant. So the first argument must be a NAME, never a literal and never a
# keyword.
#
# This is not theoretical: rewriting the call sites, one line came out as
# `await portal.get(params={"limit": 20, ...})` — the method name dropped and the endpoint
# argument went missing. ruff passed, collection passed; it would only have failed against
# a live backend. Caught by reading the diff, which is not a control.
CLIENT_VERB_CALL_RE = re.compile(r"\bawait\s+\w+\.(?:get|post|patch|put|delete)\(")
_BAD_FIRST_ARG = (")", '"', "'", 'f"', "f'")  # no "" here: startswith("") is always True
_KEYWORD_FIRST_ARG_RE = re.compile(r"\w+\s*=[^=]")

TEST_FILES = sorted(TESTS_DIR.rglob("*.py"))


def test_the_scan_has_files_to_scan():
    """An empty file list would make the check below vacuously green."""
    assert TEST_FILES, f"no python files found under {TESTS_DIR}"


@pytest.mark.parametrize("path", TEST_FILES, ids=lambda p: p.name)
def test_no_raw_page_selectors_in_tests(path):
    offenders = [
        f"{path.relative_to(PROJECT_ROOT).as_posix()}:{n}: {line.strip()}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if RAW_PAGE_SELECTOR_RE.search(line)
    ]
    assert not offenders, (
        "a test called a Playwright selector directly on the Page, which puts the selector "
        "in the wrong layer — add a method to the page object (and the string to "
        "locators/) and call that instead:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("path", TEST_FILES, ids=lambda p: p.name)
def test_no_raw_endpoint_paths_in_tests(path):
    offenders = [
        f"{path.relative_to(PROJECT_ROOT).as_posix()}:{n}: {line.strip()}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if RAW_ENDPOINT_RE.search(line)
    ]
    assert not offenders, (
        "a test spelled out an API service path, which puts the endpoint in the wrong layer "
        "— declare it in the matching api_clients/ client and add a method (pass "
        "expected_status=None for the negative case) instead:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("path", TEST_FILES, ids=lambda p: p.name)
def test_client_verb_calls_pass_a_named_path(path):
    """`await client.get(...)` must take a declared path NAME as its first argument."""
    text = path.read_text(encoding="utf-8")
    offenders = []
    for match in CLIENT_VERB_CALL_RE.finditer(text):
        rest = text[match.end() :].lstrip()
        bad = not rest or rest.startswith(_BAD_FIRST_ARG) or bool(_KEYWORD_FIRST_ARG_RE.match(rest))
        if not bad:
            continue
        line_no = text.count("\n", 0, match.start()) + 1
        line = text.splitlines()[line_no - 1].strip()
        offenders.append(f"{path.relative_to(PROJECT_ROOT).as_posix()}:{line_no}: {line}")
    assert not offenders, (
        "a test called an HTTP verb on a client without a named endpoint — either the "
        "method name is missing (the endpoint argument silently became a keyword) or the "
        "path is a literal. Call the client's named method instead:\n  " + "\n  ".join(offenders)
    )
