"""Partner Portal — Dashboard page (UI, Layer-B content).

Per-page CONTENT tests for the partner Dashboard (/dashboard). Navigation + shell
readiness come from PartnerShellPage; page-specific widgets via DashboardPage.

    PARTNER_UI_DASHBOARD_002 — dashboard KPI cards available: the actionable metric
                               cards render with a value (empty-safe).
"""

import re

import pytest
from loguru import logger

from pages.blazeup.partner.dashboard_page import DashboardPage
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.log_helper import async_step


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_dashboard_002(make_partner_page):
    """PARTNER_UI_DASHBOARD_002: dashboard KPI cards are available with actionable metrics.

    Opens the Dashboard via the shell, then asserts the KPI cards (Total pipeline
    ACV / Commission YTD / Active Tenants) each render with a metric value, plus the
    main dashboard sections. Read-only: works with empty data (values may be 0/USD 0)
    — it verifies the metric cards RENDER, not any specific figure.
    """
    shell = make_partner_page(PartnerShellPage)
    dash = make_partner_page(DashboardPage)

    async with async_step("Setup: open the Dashboard"):
        await shell.open("dashboard")
        await shell.wait_ready("dashboard")  # marker "Tier & Performance" in <main>

    async with async_step("[1/2] KPI cards render, each with a metric value"):
        values: dict[str, str] = {}
        for label in DashboardPage.KPI_CARDS:
            assert await dash.kpi_card(label).is_visible(), (
                f"KPI card '{label}' is not visible on the dashboard"
            )
            value = await dash.kpi_value(label)
            assert value, f"KPI card '{label}' must show a metric value, got {value!r}"
            values[label] = value
        logger.info("CHECK KPIs → OK ({})", values)

    async with async_step("[2/2] The main dashboard sections render"):
        for name in DashboardPage.SECTIONS:
            assert await dash.section(name).is_visible(), (
                f"dashboard section '{name}' is not visible"
            )
        logger.info("CHECK sections → OK (visible: {})", ", ".join(DashboardPage.SECTIONS))

    logger.info("RESULT: dashboard shows KPI cards with metrics + all main sections")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_dashboard_003(make_partner_page):
    """PARTNER_UI_DASHBOARD_003: the Tier Progress component shows progress to the next tier.

    Opens the Dashboard and asserts the Tier Progress panel shows the partner's current
    tier, the "Working towards <next tier>" progress copy, and the current T12M ARR.

    Plan-vs-live: the plan also lists a threshold target, a progress bar, and a
    remaining delta — this build does NOT render those (no role=progressbar element,
    no threshold/remaining text); it shows current tier + next-tier copy + ARR +
    deals/win-rate. The test asserts what the UI actually renders.
    """
    shell = make_partner_page(PartnerShellPage)
    dash = make_partner_page(DashboardPage)

    async with async_step("Setup: open the Dashboard"):
        await shell.open("dashboard")
        await shell.wait_ready("dashboard")

    async with async_step("[1/2] Tier Progress shows current tier + 'working towards' next tier"):
        panel = await dash.tier_panel_text()
        assert "Tier Progress" in panel, "the Tier Progress component must be present"
        assert re.search(r"\b(SELECT|ADVANCED|PREMIER)\b", panel), (
            f"the current tier must be shown, panel={panel[:80]!r}"
        )
        nxt = re.search(r"Working towards (\w+)", panel)
        assert nxt, "the next-tier progress copy ('Working towards <tier>') must be shown"
        assert "T12M ARR" in panel, "the current T12M ARR must be shown"
        logger.info("CHECK tier progress → OK (working towards {}; ARR shown)", nxt.group(1))

    async with async_step("[2/2] Progress metrics (deals + win rate) are shown"):
        assert re.search(r"\d+\s*Deals", panel), "deal count must be shown in tier progress"
        assert "Win rate" in panel, "win rate must be shown in tier progress"
        logger.info("CHECK metrics → OK (deals + win rate shown)")

    logger.info("RESULT: Tier Progress shows current tier, next-tier copy, ARR, and metrics")


# Non-actionable "vanity" metrics that must NOT appear on the partner dashboard
# (matched as whole words / phrases, case-insensitive, against <main> text).
_VANITY_METRICS = (
    "page views",
    "profile views",
    "impressions",
    "followers",
    "bounce rate",
    "time on page",
    "click-through",
    "click through rate",
    "logins",
    "login count",
    "vanity",
)
# The actionable/decision-supporting anchors the dashboard MUST still highlight.
_ACTIONABLE_SECTIONS = ("Action Required", "Tier Progress", "Pipeline Snapshot")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_dashboard_007(make_partner_page):
    """PARTNER_UI_DASHBOARD_007 (negative): the dashboard hides vanity metrics.

    Guard test — per PRD §4.3 the first dashboard view shows ONLY actionable /
    decision-supporting values (pipeline ACV, commission, active tenants, tier
    progress, action items, pipeline snapshot) and must NOT surface non-actionable
    "vanity" metrics (page/profile views, impressions, followers, bounce rate,
    login counts, …). Asserts the actionable metric set + hierarchy are present AND
    no vanity metric leaks into <main>.
    """
    shell = make_partner_page(PartnerShellPage)
    dash = make_partner_page(DashboardPage)

    async with async_step("Setup: open the Dashboard"):
        await shell.open("dashboard")
        await shell.wait_ready("dashboard")
        main_text = " ".join((await shell.page.locator("main").inner_text()).split())

    async with async_step("[1/3] Only actionable/decision-supporting KPI metrics are shown"):
        for label in DashboardPage.KPI_CARDS:
            assert await dash.kpi_card(label).is_visible(), (
                f"the actionable KPI '{label}' must be shown"
            )
        logger.info("CHECK actionable KPIs → OK ({})", ", ".join(DashboardPage.KPI_CARDS))

    async with async_step("[2/3] No non-actionable vanity metrics are present"):
        leaked = [m for m in _VANITY_METRICS if re.search(rf"\b{re.escape(m)}\b", main_text, re.I)]
        assert not leaked, (
            f"vanity (non-actionable) metrics must not appear on the dashboard, found: {leaked}"
        )
        logger.info("CHECK vanity metrics → OK (none of {} present)", list(_VANITY_METRICS))

    async with async_step("[3/3] The page hierarchy still highlights the actionable sections"):
        for name in _ACTIONABLE_SECTIONS:
            assert await dash.section(name).is_visible(), (
                f"the actionable section '{name}' must still be highlighted"
            )
        logger.info("CHECK hierarchy → OK ({})", ", ".join(_ACTIONABLE_SECTIONS))

    logger.info("RESULT: dashboard shows only actionable metrics; vanity metrics are hidden")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.be_gap  # BUG-UI-007: tier-qualification math (ARR threshold / next-tier delta) not rendered
async def test_partner_ui_dashboard_005(make_partner_page):
    """PARTNER_UI_DASHBOARD_005: tier-qualification math (T12M ARR threshold + next-tier delta).

    Per the plan (PRD §2.1, §4.3), the Tier Progress component must surface the tier
    QUALIFICATION math: the current tier + current T12M ARR (already shown), PLUS the
    next-tier **T12M ARR threshold target**, the **remaining delta** to reach it, and a
    **progress bar** toward that threshold.

    Fail-by-design (be_gap): the live build renders only the current tier, the
    "Working towards <next tier>" copy, the current ARR, and deal/win-rate counts — it
    does NOT render any ARR threshold amount, any remaining-delta amount, or a progress
    bar (no role=progressbar). The threshold/delta assertions below FAIL with "confirm
    with BE" until the tier-qualification figures are exposed in the UI. This is the
    honest signal, not a faked green.
    """
    shell = make_partner_page(PartnerShellPage)
    dash = make_partner_page(DashboardPage)

    async with async_step("Setup: open the Dashboard and locate Tier Progress"):
        await shell.open("dashboard")
        await shell.wait_ready("dashboard")
        panel = await dash.tier_panel_text()
        assert "Tier Progress" in panel, "the Tier Progress component must be present"

    async with async_step("[1/3] Current tier + current T12M ARR are shown (baseline)"):
        assert re.search(r"\b(SELECT|ADVANCED|PREMIER)\b", panel), (
            f"the current tier must be shown, panel={panel[:80]!r}"
        )
        assert "T12M ARR" in panel, "the current T12M ARR must be shown"
        logger.info("CHECK baseline → OK (current tier + ARR shown)")

    async with async_step("[2/3] Next-tier T12M ARR threshold target + remaining delta are shown"):
        # Look for a dollar/ARR figure that represents the THRESHOLD or the DELTA to next tier,
        # e.g. "USD 250,000 to reach ADVANCED" / "USD 250,000 remaining" / "of USD 250,000".
        has_threshold = bool(
            re.search(r"(threshold|target|to reach|remaining|needed|away|of\s+USD)", panel, re.I)
        )
        assert has_threshold, (
            "the next-tier T12M ARR threshold target and remaining delta must be shown in Tier "
            f"Progress, but only current tier/ARR/deal-count are rendered (panel={panel[:160]!r}). "
            "Tier-qualification math (threshold + delta) is not surfaced in the UI — confirm with BE."
        )
        logger.info("CHECK threshold/delta → OK")

    async with async_step("[3/3] A progress bar toward the next-tier threshold is shown"):
        bars = await dash.tier_progressbar_count()
        assert bars > 0, (
            "a tier-qualification progress bar (progress toward the next-tier ARR threshold) must "
            "be rendered, but none is present (no role=progressbar / <progress> / progress element) "
            "— confirm with BE."
        )
        logger.info("CHECK progress bar → OK ({} bar(s))", bars)

    logger.info("RESULT: tier-qualification threshold + delta + progress bar are shown")


# SA/tenant-only routes that must NOT appear in the partner portal nav.
_SA_ONLY_ROUTES = ("/tenants", "/billing", "/plans", "/partners", "/connectors", "/auditLog")
# Core partner routes that MUST be present.
_PARTNER_ROUTES = ("/dashboard", "/deals", "/commissions")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_dashboard_001(make_partner_page):
    """PARTNER_UI_DASHBOARD_001: the partner shell loads for a channel partner and shows the Dashboard.

    Logs in as the channel-partner user, navigates to the portal root, and confirms:
    the partner shell chrome (brand + nav + profile control) renders, the Dashboard is
    the active/default page, only partner navigation is exposed (no SA/tenant-only
    routes), and the dashboard content loads with no error/authorization banner.
    """
    shell = make_partner_page(PartnerShellPage)

    async with async_step("Setup: navigate to the portal root (should land on the Dashboard)"):
        await shell.goto("")  # portal root "/"
        await shell.wait_ready("dashboard")  # Dashboard is the default active page

    async with async_step("[1/3] Partner shell chrome renders (brand + nav + profile)"):
        assert await shell.page.get_by_text("PARTNER PORTAL", exact=False).first.is_visible(), (
            "the 'PARTNER PORTAL' brand must render in the shell"
        )
        assert await shell.visible_nav_link_count() >= 5, "the partner sidebar nav must render"
        assert await shell.page.get_by_role(
            "button", name="Open profile menu"
        ).first.is_visible(), "the profile control must render in the shell"
        logger.info("CHECK shell chrome → OK (brand + nav + profile)")

    async with async_step("[2/3] Only partner navigation is exposed (no SA/tenant-only routes)"):
        hrefs = await shell.nav_hrefs()
        leaked = [r for r in _SA_ONLY_ROUTES if r in hrefs]
        assert not leaked, f"SA/tenant-only routes must not appear in the partner nav: {leaked}"
        missing = [r for r in _PARTNER_ROUTES if r not in hrefs]
        assert not missing, f"core partner routes must be present, missing: {missing}"
        logger.info("CHECK nav → OK (partner routes present; no SA-only routes)")

    async with async_step("[3/3] Dashboard content loads with no error/authorization banner"):
        for bad in (
            "Something went wrong",
            "not authorized",
            "Unauthorized",
            "403",
            "Access denied",
        ):
            assert await shell.page.get_by_text(bad, exact=False).count() == 0, (
                f"no error/auth banner expected, found {bad!r}"
            )
        assert await shell.page.locator("main").get_by_text("Tier & Performance").first.is_visible()
        logger.info("CHECK dashboard content → OK (visible, no error/auth banner)")

    logger.info("RESULT: partner shell loads for the channel partner with the Dashboard active")
