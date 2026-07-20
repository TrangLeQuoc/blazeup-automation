"""TC registry — module `shell`. (AUTO-GENERATED — do not edit.)

One file per top-level module so per-module PRs don't collide. Merged into the
domain registry by runner/blazeup/registry.py.
"""

from runner.blazeup.registry_modules._base import TestCase

TC_REGISTRY: dict[int, TestCase] = {
    12010101: TestCase(12010101, "SHELL_UI_LOAD_TIME_PAGE_001", "ui", "shell", "every SA Dashboard page loads within budget (navigated via URL).", "tests/blazeup/ui/shell/test_load_time.py", "test_shell_ui_load_time_page_001", ['ui', 'regression'], "P2"),
    12010102: TestCase(12010102, "SHELL_UI_LOAD_TIME_PAGE_002", "ui", "shell", "every SA Dashboard page loads within budget (navigated via NAV).", "tests/blazeup/ui/shell/test_load_time.py", "test_shell_ui_load_time_page_002", ['ui', 'regression'], "P2"),
    12010201: TestCase(12010201, "SHELL_UI_PAGE_LOADS_001", "ui", "shell", "every page loads via direct URL (no MFE fetch error).", "tests/blazeup/ui/shell/test_page_loads.py", "test_shell_ui_page_loads_001", ['ui', 'smoke'], "P2"),
    12010202: TestCase(12010202, "SHELL_UI_PAGE_LOADS_002", "ui", "shell", "every page loads via sidebar NAV click (no MFE fetch error).", "tests/blazeup/ui/shell/test_page_loads.py", "test_shell_ui_page_loads_002", ['ui', 'regression'], "P2"),
}
