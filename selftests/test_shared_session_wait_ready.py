"""`wait_ready` must report a dead SHARED partner session, not blame the page.

Split out of `test_shared_session_signal.py`: these need a page object and therefore
Playwright, and a module-level `importorskip` skips the ENTIRE file it appears in — keeping
both halves together took the Playwright-free half down with it in CI. The pure decision
they build on (`PartnerShellLocators.is_login_url`) still runs everywhere.

Why it matters: 21 partner-portal TCs run off ONE cached login. A dead session and a broken
page look identical to a readiness wait, so without the signed-out check every one of the 21
sits out its full 90 s and then reports "did not render" — 21 x 90 s of misdirection from a
single root cause, with the blame pointed at the page.
"""

import asyncio

import pytest

from locators.blazeup.partner.partner_shell_locators import PartnerShellLocators as L

# exc_type is explicit because pytest 9.1 stops treating a raising import as a skip by
# default. In the real CI job the package is simply absent (ModuleNotFoundError, a subclass
# of ImportError), so this covers both "not installed" and "installed but broken".
pytest.importorskip(
    "playwright",
    reason="pages/ needs Playwright; not in the selftest job",
    exc_type=ImportError,
)

# Imported for its side effect: it registers loguru's custom levels (STEP/START/...).
# 11 files under pages/ log at those levels and NONE of them import this module, so they
# rely on some earlier import having done it — true in a real run (conftest pulls it in),
# not true here. Without this line wait_ready raises ValueError: Level 'STEP' does not
# exist, which is a latent coupling worth knowing about rather than papering over.
import utils.log_helper  # noqa: E402, F401
from pages.blazeup.partner.partner_shell_page import PartnerShellPage  # noqa: E402


class _FakeLocator:
    def __init__(self, visible: bool) -> None:
        self._visible = visible

    @property
    def first(self):
        return self

    def get_by_text(self, *_args, **_kwargs):
        return self

    async def is_visible(self) -> bool:
        return self._visible


class _FakePage:
    """Just enough Page for wait_ready: a URL, two locators, and a sleep counter."""

    def __init__(self, url: str, *, marker: bool = False, error: bool = False) -> None:
        self.url = url
        self._marker = marker
        self._error = error
        self.polls = 0

    def locator(self, selector: str):
        return _FakeLocator(self._marker if selector == L.MAIN else self._error)

    async def wait_for_timeout(self, _ms: int) -> None:
        self.polls += 1


def _wait_ready(page: _FakePage, *, timeout: int = 50) -> None:
    shell = PartnerShellPage(page, "https://stgpartners.blazeup.ai")
    asyncio.run(shell.wait_ready("dashboard", timeout=timeout, poll_ms=1))


def test_signed_out_page_fails_immediately_with_the_session_reason():
    page = _FakePage("https://stgpartners.blazeup.ai/login?redirect=%2Fdashboard")
    with pytest.raises(AssertionError) as err:
        _wait_ready(page)
    message = str(err.value)
    assert "not authenticated" in message and "SHARED partner session" in message, message
    assert "did not render" not in message, "must not blame the page for a dead session"
    assert page.polls == 0, "a dead session must not wait out the timeout even once"


def test_ready_page_returns():
    page = _FakePage("https://stgpartners.blazeup.ai/dashboard", marker=True)
    _wait_ready(page)  # no raise


def test_mfe_error_panel_still_wins_over_the_timeout():
    page = _FakePage("https://stgpartners.blazeup.ai/dashboard", error=True)
    with pytest.raises(AssertionError, match="MFE error panel"):
        _wait_ready(page)


def test_slow_page_still_reports_did_not_render():
    """The original message must survive for its real case: signed in, nothing rendered."""
    page = _FakePage("https://stgpartners.blazeup.ai/dashboard")
    with pytest.raises(AssertionError, match="did not render"):
        _wait_ready(page)
    assert page.polls > 0, "a signed-in page must actually be given time to render"


def test_session_reason_is_reported_before_the_mfe_panel():
    """Both signals up: the session is the ROOT cause, so it must be the one reported."""
    page = _FakePage("https://stgpartners.blazeup.ai/login", error=True)
    with pytest.raises(AssertionError, match="not authenticated"):
        _wait_ready(page)
