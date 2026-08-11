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
