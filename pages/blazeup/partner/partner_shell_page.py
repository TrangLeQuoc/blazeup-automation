"""Partner Portal shell page object — sidebar navigation + load-state checks.

Mirrors ``pages/blazeup/admin/shell_page.py`` for the partner portal
(stgpartners.blazeup.ai). The portal is a micro-frontend host: the sidebar always
renders, each section's module is fetched dynamically and can fail. So the stable
surface to automate first is: navigate to a section, then assert it actually
rendered (READY_MARKER visible in <main>, fast-fail on the MFE error panel).

Usage::

    from pages.blazeup.partner.partner_shell_page import PartnerShellPage

    async def test_x(make_partner_page):
        shell = make_partner_page(PartnerShellPage)
        await shell.open("deals")
        await shell.wait_ready("deals")
"""

import contextlib
import time

from loguru import logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import expect

from locators.blazeup.partner.partner_shell_locators import PartnerShellLocators
from pages.base_page import BasePage


class PartnerShellPage(BasePage):
    """Actions for the Partner Portal sidebar shell."""

    SECTIONS = PartnerShellLocators.SECTIONS

    # -- navigation -----------------------------------------------------------

    async def open(self, section: str = "dashboard") -> None:
        """Navigate directly to a section by its route (default: Dashboard)."""
        meta = self._meta(section)
        await self.goto(meta["route"])

    async def ensure_sidebar_expanded(self, timeout: int = 10_000) -> None:
        """Expand the sidebar if collapsed (idempotent) so nav labels render.

        The portal sidebar defaults to COLLAPSED (icons only); in that state the
        nav labels aren't rendered, so click-by-label can't find them. Click the
        expand trigger only when it is present (i.e. currently collapsed).
        """
        trigger = self.page.locator(PartnerShellLocators.SIDEBAR_EXPAND_TRIGGER).first
        if await trigger.count() and await trigger.is_visible():
            logger.log("STEP", "Expand sidebar (was collapsed)")
            await trigger.click(timeout=timeout)
            await expect(trigger).to_have_count(0, timeout=timeout)

    async def click_nav(self, section: str) -> None:
        """Click a sidebar nav item by its key (expands the sidebar first)."""
        meta = self._meta(section)
        await self.ensure_sidebar_expanded()
        label = meta["label"]
        logger.log("STEP", "Click sidebar nav [{}]", label)
        link = self.page.get_by_role("link", name=label, exact=False).first
        await link.click(timeout=15_000)

    def nav_link(self, section: str):
        """Locator for a section's sidebar link, built from its declared route.

        Use this instead of writing ``aside a[href='/commissions']`` in a test: the
        route already lives in SECTIONS, so a route change is one edit here.
        Works while the sidebar is collapsed (the <a> is present, only its label is
        not) — unlike click_nav, which needs the labels expanded.
        """
        route = self._meta(section)["route"]
        return self.page.locator(f"{PartnerShellLocators.SIDEBAR} a[href='{route}']").first

    # -- shell chrome ---------------------------------------------------------
    # Present on every section, including a broken one. Proving the chrome rendered
    # is a different claim from proving a section rendered (marker_locator).

    def brand(self):
        """Locator for the portal brand text in the shell chrome."""
        return self.page.get_by_text(PartnerShellLocators.BRAND_TEXT, exact=False).first

    def profile_button(self):
        """Locator for the profile-menu control in the shell chrome."""
        return self.page.get_by_role("button", name=PartnerShellLocators.PROFILE_BUTTON_NAME).first

    # -- readiness marker -----------------------------------------------------

    def _meta(self, section: str) -> dict[str, str]:
        meta = self.SECTIONS.get(section)
        if meta is None:
            raise KeyError(
                f"Unknown Partner Portal section '{section}'. "
                f"Valid keys: {', '.join(self.SECTIONS)}"
            )
        return meta

    def marker_text(self, section: str) -> str:
        """Return the READY_MARKER text (page title) for a section."""
        return self._meta(section)["marker"]

    def marker_locator(self, section: str):
        """Locator for a section's READY_MARKER, scoped to <main>.

        Scoped to <main> on purpose: the sidebar + top bar always render (even on
        a failed module), so a page-title match outside <main> would give a false
        "loaded". Matching the title text inside <main> proves the section's own
        module rendered.
        """
        marker = self.marker_text(section)
        return self.page.locator(PartnerShellLocators.MAIN).get_by_text(marker, exact=True).first

    async def wait_ready(self, section: str, timeout: int = 90_000, poll_ms: int = 500) -> None:
        """Wait until a section is READY, distinguishing 'broken' from 'slow'.

        Polls two signals: the MFE error panel ("Something went wrong") → raise
        IMMEDIATELY (broken, no point waiting); and the section's READY_MARKER
        visible in <main> → return. Only if neither happens within *timeout* does
        it raise "did not render". The large timeout protects slow staging cold
        loads; a broken page is still reported in ~1-2 s because the error panel is
        polled every ``poll_ms``.
        """
        marker = self.marker_text(section)
        logger.log(
            "STEP",
            "Wait ready [{}] = marker '{}' in <main> (fast-fail on error panel)",
            section,
            marker,
        )
        marker_loc = self.marker_locator(section)
        error_loc = self.page.locator(PartnerShellLocators.ERROR_PANEL).first
        deadline = time.perf_counter() + timeout / 1000
        while True:
            if await error_loc.is_visible():
                raise AssertionError(
                    f"Partner Portal section '{section}' failed to load: the MFE error panel "
                    f"('Something went wrong') is visible. Deploy/MFE issue, not a test bug."
                )
            if await marker_loc.is_visible():
                return
            if time.perf_counter() >= deadline:
                raise AssertionError(
                    f"Partner Portal section '{section}' did not render within {timeout} ms: "
                    f"its page title '{marker}' never became visible in <main>."
                )
            await self.page.wait_for_timeout(poll_ms)

    async def assert_content_loaded(self, section: str, settle_timeout: int = 8_000) -> None:
        """After the shell is READY, assert the page's CONTENT loaded (no error banner).

        The READY_MARKER (page title) renders even when the section's data fetch
        fails, showing a banner like "Failed to load your apps." — so wait_ready
        (marker + no MFE panel) can pass on a page whose content is actually broken.
        This waits for the fetches to settle (network idle), then fails if any
        CONTENT_ERROR_TEXTS phrase is visible in <main>.
        """
        # a page that keeps polling never idles — check the banner anyway on timeout
        with contextlib.suppress(PlaywrightTimeoutError):
            await self.page.wait_for_load_state("networkidle", timeout=settle_timeout)
        text = (await self.page.locator(PartnerShellLocators.MAIN).inner_text()).lower()
        for phrase in PartnerShellLocators.CONTENT_ERROR_TEXTS:
            if phrase.lower() in text:
                raise AssertionError(
                    f"Partner Portal section '{section}' rendered its shell but the CONTENT "
                    f"failed to load: banner '{phrase}' is visible in <main>. Data-fetch/backend "
                    f"issue for this page — confirm with BE."
                )
        logger.log("STEP", "Content OK [{}] (no error banner)", section)

    # -- text snapshots + phrase checks ---------------------------------------

    async def main_text(self) -> str:
        """Whitespace-normalised text of <main> — the section's OWN content."""
        return " ".join((await self.page.locator(PartnerShellLocators.MAIN).inner_text()).split())

    async def page_text(self) -> str:
        """Whitespace-normalised text of the whole page, chrome included.

        Only for things that can render OUTSIDE <main> — a toast, for instance.
        Prefer main_text(): the chrome is always present, so a page-wide match can
        pass on a section that never rendered.
        """
        return " ".join((await self.page.locator(PartnerShellLocators.BODY).inner_text()).split())

    async def error_phrases_found(self, phrases=None) -> list[str]:
        """Return which of *phrases* are present anywhere on the page (default: auth).

        Page-wide on purpose — an authorization banner renders outside <main>. For a
        section's CONTENT load failure use assert_content_loaded() instead, which is
        scoped to <main> and carries the "confirm with BE" wording.
        """
        found = []
        for phrase in phrases if phrases is not None else PartnerShellLocators.AUTH_ERROR_TEXTS:
            if await self.page.get_by_text(phrase, exact=False).count():
                found.append(phrase)
        return found

    async def horizontal_overflow_px(self) -> int:
        """Return how many px the page content overflows the viewport horizontally.

        0 (or a tiny scrollbar allowance) = responsive/no horizontal scroll; a large
        positive value means the layout does not fit the viewport width (content is
        cut off / needs sideways scrolling) — a responsive-layout defect on mobile.
        """
        return await self.page.evaluate(
            "() => document.documentElement.scrollWidth - window.innerWidth"
        )

    async def visible_nav_link_count(self) -> int:
        """Return the number of sidebar/nav links currently visible (nav is usable)."""
        return await self.page.evaluate(
            "() => Array.from(document.querySelectorAll('aside a[href], nav a[href]'))"
            ".filter(a => a.offsetParent !== null).length"
        )

    async def nav_hrefs(self) -> list[str]:
        """Return all sidebar/nav hrefs (to check the partner nav set / no SA-only routes)."""
        return await self.page.evaluate(
            "() => Array.from(document.querySelectorAll('aside a[href], nav a[href]'))"
            ".map(a => a.getAttribute('href'))"
        )
