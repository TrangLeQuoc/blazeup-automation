"""SA Dashboard shell page object — sidebar navigation + load-state checks.

Why a single "shell" object instead of one file per section:
the SA Dashboard is a micro-frontend host. The sidebar always renders, but each
section's content module is fetched dynamically and can fail (the "Something went
wrong / Failed to fetch dynamically imported module" panel). So the high-value,
stable surface to automate first is: navigate to a section, then assert it
actually loaded. Per-section page objects (TenantsPage, BillingPage, …) are added
later once the deploy is healthy and real selectors are visible.

Usage in a test::

    from pages.blazeup.admin.shell_page import ShellPage

    async def test_tc01_open_tenants(authenticated_page, settings):
        shell = ShellPage(authenticated_page, str(settings.base_url))
        await shell.open()                  # land on /sa-dashboard
        await shell.click_nav("tenants")    # click the sidebar item
        await shell.assert_loaded()         # fail fast if the MFE errored
"""

import time

from loguru import logger
from playwright.async_api import expect

from locators.blazeup.admin.shell_locators import ShellLocators
from pages.base_page import BasePage


class ShellPage(BasePage):
    """Actions for the SA Dashboard sidebar shell."""

    SECTIONS = ShellLocators.SECTIONS

    # -- navigation -----------------------------------------------------------

    async def open(self, section: str = "dashboard") -> None:
        """Navigate directly to a section by its route (default: Dashboard).

        Falls back to /sa-dashboard if the section's route is still a TODO.
        """
        route = self.SECTIONS.get(section, {}).get("route", "")
        if not route or route.startswith("TODO"):
            logger.warning("Route for section '{}' not set yet — opening /sa-dashboard", section)
            route = "/sa-dashboard"
        await self.goto(route)

    async def ensure_sidebar_expanded(self, timeout: int = 10_000) -> None:
        """Expand the sidebar if it is collapsed (idempotent).

        The SA Dashboard sidebar defaults to COLLAPSED (width ~48px, icons only),
        and in that state the nav *labels* are not rendered — so
        ``get_by_role("link", name=label)`` finds nothing and a click would time
        out. This clicks the collapse/expand trigger only when needed and waits
        until ``data-state`` becomes ``expanded``. A no-op when already expanded.
        """
        sidebar = self.page.locator(ShellLocators.SIDEBAR).first
        await sidebar.wait_for(state="attached", timeout=timeout)
        if await sidebar.get_attribute("data-state") == "expanded":
            return
        logger.log("STEP", "Expand sidebar (was collapsed)")
        await self.page.locator(ShellLocators.SIDEBAR_TRIGGER).first.click(timeout=timeout)
        await expect(sidebar).to_have_attribute("data-state", "expanded", timeout=timeout)

    async def click_nav(self, section: str) -> None:
        """Click a sidebar nav item by its key (e.g. 'tenants', 'billing').

        Expands the sidebar first (labels aren't rendered while collapsed), then
        clicks by visible label text, which is more stable than CSS classes.
        """
        meta = self.SECTIONS.get(section)
        if meta is None:
            raise KeyError(
                f"Unknown SA Dashboard section '{section}'. Valid keys: {', '.join(self.SECTIONS)}"
            )
        await self.ensure_sidebar_expanded()
        label = meta["label"]
        logger.log("STEP", "Click sidebar nav [{}]", label)
        link = self.page.get_by_role("link", name=label, exact=False).first
        await link.click(timeout=15_000)

    # -- readiness marker -----------------------------------------------------

    def marker_text(self, section: str) -> str:
        """Return the READY_MARKER text (page title) for a section."""
        meta = self.SECTIONS.get(section)
        if meta is None:
            raise KeyError(
                f"Unknown SA Dashboard section '{section}'. Valid keys: {', '.join(self.SECTIONS)}"
            )
        return meta["marker"]

    def marker_locator(self, section: str):
        """Locator for a section's READY_MARKER, scoped to <main>.

        Scoped to ``main`` on purpose: the sidebar + top bar always render (even
        on a failed micro-frontend), so a page-title match outside <main> would
        give a false "loaded". Matching the title text *inside* <main> proves the
        section's own module actually rendered.
        """
        marker = self.marker_text(section)
        return self.page.locator(ShellLocators.MAIN).get_by_text(marker, exact=True).first

    async def assert_ready(self, section: str, timeout: int = 30_000) -> None:
        """Assert a section actually rendered: its READY_MARKER is visible.

        Positive readiness check (complements the negative ``assert_loaded``):
        waits until the page-title text for *section* is visible inside <main>.
        Emits a STEP log naming the marker so the run log shows exactly what is
        being checked, and a clear AssertionError if it never appears.

        The default timeout is generous (30 s): on a cold page the first hard
        navigation must bootstrap the whole SPA (the BlazeUp splash logo) before
        the section module is even fetched, and staging cold loads routinely take
        8-15 s per page.
        """
        marker = self.marker_text(section)
        logger.log("STEP", "Check ready marker [{}] = '{}' visible in <main>", section, marker)
        await expect(
            self.marker_locator(section),
            f"SA Dashboard section '{section}' did not render: its page title "
            f"'{marker}' never became visible in <main> "
            f"(likely the section module failed to load).",
        ).to_be_visible(timeout=timeout)

    async def wait_ready(self, section: str, timeout: int = 90_000, poll_ms: int = 500) -> None:
        """Wait until a section is READY, distinguishing 'broken' from 'slow'.

        Polls two signals concurrently:
          * the MFE error panel ("Something went wrong") → raise IMMEDIATELY
            (the section is broken; no point waiting out the timeout), and
          * the section's READY_MARKER becoming visible in <main> → return.

        Only if neither happens within *timeout* does it raise "did not render".

        Why this instead of ``assert_loaded`` + ``assert_ready``: on slow staging
        a cold first load (full SPA bootstrap + remoteEntry.js fetch) can take
        20-30 s, while a broken page shows the error panel almost immediately.
        A single fixed timeout can't tell those apart — it would either fail slow
        pages or wait the full timeout on every broken page. This fast-fails the
        broken case and gives the slow-but-working case generous headroom.

        The timeout is deliberately large (90 s): a page that has NOT shown the
        error panel is "still loading", not "broken", and the policy is to fail
        only genuinely broken pages. Because the error panel is polled every
        ``poll_ms`` and raises immediately, a real failure is reported in ~1-2 s
        regardless of how large this timeout is — the big number only protects
        slow-but-working pages from a false "did not render" on the worst staging
        cold loads. Pair with a one-off warm-up (open any section once before a
        per-page loop) so the full SPA bootstrap is not charged to the first page.
        """
        marker = self.marker_text(section)
        logger.log(
            "STEP",
            "Wait ready [{}] = marker '{}' in <main> (fast-fail on error panel)",
            section,
            marker,
        )
        marker_loc = self.marker_locator(section)
        error_loc = self.page.locator(ShellLocators.ERROR_PANEL).first
        deadline = time.perf_counter() + timeout / 1000
        while True:
            if await error_loc.is_visible():
                raise AssertionError(
                    f"SA Dashboard section '{section}' failed to load: the MFE error "
                    f"panel ('Something went wrong') is visible. Deploy/MFE issue, not a test bug."
                )
            if await marker_loc.is_visible():
                return
            if time.perf_counter() >= deadline:
                raise AssertionError(
                    f"SA Dashboard section '{section}' did not render within {timeout} ms: "
                    f"its page title '{marker}' never became visible in <main>."
                )
            await self.page.wait_for_timeout(poll_ms)

    # -- load-state assertions ------------------------------------------------

    async def is_error_state(self) -> bool:
        """Return True if the 'Something went wrong' panel is visible."""
        panel = self.page.locator(ShellLocators.ERROR_PANEL).first
        return await panel.is_visible()

    async def assert_loaded(self, timeout: int = 15_000) -> None:
        """Assert the current section loaded (no module-fetch error panel).

        Raises AssertionError with a clear message when the SA Dashboard shows
        the 'Failed to fetch dynamically imported module' error — turning a
        flaky-deploy symptom into an explicit, debuggable test failure.
        """
        error_panel = self.page.locator(ShellLocators.ERROR_PANEL).first
        await expect(
            error_panel,
            "SA Dashboard failed to load the section module "
            "('Something went wrong'). Likely a deploy/MFE issue, not a test bug.",
        ).not_to_be_visible(timeout=timeout)

    async def retry_load(self) -> None:
        """Click the 'Try again' button on the error panel, if present."""
        await self.click(ShellLocators.TRY_AGAIN_BUTTON, label="Try again")

    # -- performance ----------------------------------------------------------

    async def open_and_measure(self, section: str, timeout: int = 90_000) -> float:
        """Navigate to a section and return its load time in milliseconds.

        Wall-clock from the start of navigation until the section's module has
        rendered (i.e. ``assert_loaded`` passes — no MFE error panel). This
        reflects the user-perceived load time for a micro-frontend, which the raw
        Navigation Timing API does not capture (the module is fetched after the
        initial document load).

        Raises AssertionError if the section errored (error panel) or never
        rendered its READY_MARKER, so a broken page is reported as a failure
        rather than a misleading timing.
        """
        start = time.perf_counter()
        await self.open(section)
        await self.wait_ready(
            section, timeout=timeout
        )  # fast-fail if broken, else wait until rendered
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("Load time via URL [{}] = {:.0f} ms", section, elapsed_ms)
        return elapsed_ms

    async def click_nav_and_measure(self, section: str, timeout: int = 90_000) -> float:
        """Navigate to a section via sidebar NAV click and return its load time (ms).

        Assumes the shell is already loaded (sidebar present). Wall-clock from the
        moment the sidebar item is clicked until the section's module has rendered
        (``assert_loaded`` passes). Unlike ``open_and_measure`` (URL/page.goto),
        this reflects in-app navigation: the timing includes the sidebar routing
        and the dynamic module fetch, closer to real user clicks.

        Raises AssertionError (via assert_loaded) if the section errored.
        """
        # Expand the sidebar BEFORE timing so the one-off expand cost is not
        # counted as page load time (click_nav below then finds it expanded).
        await self.ensure_sidebar_expanded()
        start = time.perf_counter()
        await self.click_nav(section)
        await self.wait_ready(
            section, timeout=timeout
        )  # fast-fail if broken, else wait until rendered
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("Load time via NAV [{}] = {:.0f} ms", section, elapsed_ms)
        return elapsed_ms
