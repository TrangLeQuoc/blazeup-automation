"""TC registry — module `dashboard`. (AUTO-GENERATED — do not edit.)

One file per top-level module so per-module PRs don't collide. Merged into the
domain registry by runner/blazeup/registry.py.
"""

from runner.blazeup.registry_modules._base import TestCase

TC_REGISTRY: dict[int, TestCase] = {
    12020101: TestCase(12020101, "DASHBOARD_UI_VISIBLE_001", "ui", "dashboard", "Dashboard shows KPI cards + System Health panel (navigated via URL).", "tests/blazeup/ui/dashboard/test_dashboard.py", "test_dashboard_ui_visible_001", ['ui', 'regression'], "P2"),
}
