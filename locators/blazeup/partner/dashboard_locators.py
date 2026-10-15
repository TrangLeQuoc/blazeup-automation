"""Locators for the Partner Portal Dashboard page (/dashboard).

The SOURCE OF TRUTH is the agreed Figma design (SuperAdmin file, node 10604-18631), not
whatever the live build shows today. The dashboard has been changing while FE implements
that design — 2026-10-13 it showed "Open pipeline (est. ACV)" / "Commission paid YTD" /
"Active Clients", 2026-10-14 "Total pipeline ACV" / "Commission paid YTD" / "Active
Tenants" — and chasing each interim build kept breaking the tests without saying anything
about the product. Asserting the design instead means a test fails for exactly as long as
the build differs from what the team agreed to ship.
"""


class DashboardLocators:
    """Dashboard: KPI cards + section panels."""

    # Page READY_MARKER (in <main>). The dashboard has no page title, so a section
    # heading stands in. "Pipeline Snapshot" exists in the design AND in every build seen
    # so far; the previous marker ("Tier & Performance") vanished from the live build, and
    # every dashboard TC then sat out the full 90 s readiness timeout on a page that had in
    # fact rendered fine. Readiness must not depend on a pending design gap.
    READY_MARKER = "Pipeline Snapshot"

    # Top KPI cards, labels exactly as in Figma. Each shows its value next to the label —
    # "USD 426K" / "USD 24,000.00" in the design, a bare number in interim builds.
    KPI_CARDS = ("Total pipeline ACV", "Commission YTD", "Active Tenants")

    # Section panels on the dashboard. "Performance" also matches the design's
    # "Tier & Performance" heading (substring match); the missing tier content is asserted
    # by PARTNER_UI_DASHBOARD_003 (BUG-UI-014), so it is not double-counted here.
    SECTIONS = (
        "Performance",
        "Territory Assignments",
        "Action Required",
        "Pipeline Snapshot",
    )
