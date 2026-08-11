"""Telling an expired SHARED partner session apart from a page that failed to render.

21 partner-portal TCs run off ONE cached login (the `partner_auth_state` fixture). To a
readiness wait, a dead session and a broken page look the same: the section marker never
appears. Without a signed-out check every one of those 21 sits out its full 90 s timeout
and then reports "did not render" — 21 x 90 s of misdirection from one root cause, with
the blame pointed at the page.

Measured 2026-08-11: the shared session was reused across 358 s in run_20260810_170831
(comfortably inside a normal token lifetime, and never yet observed failing — 0 of 359
recorded results show "did not render within"). The window grows with every partner TC
added, which is what this guards.

The decision lives in `PartnerShellLocators.is_login_url` — a pure string test — so this
runs in the selftest job, which does not install Playwright. The ordering inside
`wait_ready` is covered further down and skips when Playwright is absent.
"""

import asyncio

import pytest

from locators.blazeup.partner.partner_shell_locators import PartnerShellLocators as L

# ── is_login_url ─────────────────────────────────────────────────────────────

SIGNED_OUT = [
    "https://stgpartners.blazeup.ai/login",
    "https://stgpartners.blazeup.ai/login/",
    "https://stgpartners.blazeup.ai/login?redirect=%2Fdashboard",
    "https://stgpartners.blazeup.ai/login#expired",
    "/login",
]

STILL_SIGNED_IN = [
    "https://stgpartners.blazeup.ai/dashboard",
    "https://stgpartners.blazeup.ai/deals",
    "https://stgpartners.blazeup.ai/commissions",
    "https://stgpartners.blazeup.ai/directory",
    "https://stgpartners.blazeup.ai/resources",
    "https://stgpartners.blazeup.ai/apps",
    # Must NOT read as signed-out: the word appears, but not as the path.
    "https://stgpartners.blazeup.ai/deals?ref=login-flow",
    "https://stgpartners.blazeup.ai/logins",
    "https://stgpartners.blazeup.ai/settings/login-history",
]


@pytest.mark.parametrize("url", SIGNED_OUT)
def test_login_urls_are_recognised(url):
    assert L.is_login_url(url) is True, f"should read as signed-out: {url!r}"


@pytest.mark.parametrize("url", STILL_SIGNED_IN)
def test_section_urls_are_not_mistaken_for_login(url):
    assert L.is_login_url(url) is False, (
        f"must NOT read as signed-out — a false positive turns a slow page into a bogus "
        f"session error: {url!r}"
    )


@pytest.mark.parametrize("url", ["", None])
def test_missing_url_is_not_signed_out(url):
    """No URL yet (context just opened) is 'unknown', never 'signed out'."""
    assert L.is_login_url(url) is False


def test_every_declared_section_route_reads_as_signed_in():
    """Whatever routes SECTIONS grows to, none may trip the signed-out check."""
    offenders = [meta["route"] for meta in L.SECTIONS.values() if L.is_login_url(meta["route"])]
    assert not offenders, f"section route(s) mistaken for the login page: {offenders}"


# ── wait_ready ordering (needs Playwright; skipped in the selftest CI job) ───
# requirements-selftest.txt deliberately excludes Playwright to keep that job seconds
# fast, so these run locally only. The decision they depend on is already covered above.

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
