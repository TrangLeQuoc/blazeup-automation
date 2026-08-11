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

The decision lives in `PartnerShellLocators.is_login_url` — a pure string test — so it is
covered HERE, in the selftest job, which does not install Playwright. The ordering inside
`wait_ready` needs a page object and therefore Playwright, so it lives in
`test_shared_session_wait_ready.py`: a module-level `importorskip` skips the WHOLE file it
sits in, so keeping both halves together silently took these pure tests down with it in CI
(measured: 22 tests collected locally, 0 in CI).
"""

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
