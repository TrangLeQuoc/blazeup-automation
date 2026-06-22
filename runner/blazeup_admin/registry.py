"""Central registry mapping numeric TC IDs to pytest nodes.  (AUTO-GENERATED — do not edit)

TC ID Encoding
--------------
New-style  :  {type}{project}{module:02d}{section:02d}{seq:02d}
              type 1=UI / 0=API   project 1=partner 2=admin
              module/section are per-domain. The project digit keeps IDs unique
              across projects even when they share a module name.

Legacy     :  1001-1999 = UI demo   1-99 = API demo   (BlazeUp HRMS test suite)

Traceability
------------
tc_string  links each registry entry back to the TestcaseId column in
Partner_Platform_Test_Plan.xlsx.  Empty string for legacy (HRMS) tests.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TestCase:
    """Metadata for a single automation test case."""

    tc_id:     int
    tc_string: str                        # Excel TestcaseId  e.g. PARTNER_UI_DASHBOARD_001
    type:      Literal["api", "ui"]
    module:    str
    title:     str
    test_path: str
    test_func: str
    markers:   list[str] = field(default_factory=list)
    priority:  Literal["P1", "P2", "P3"] = "P2"

    @property
    def node_id(self) -> str:
        return f"{self.test_path}::{self.test_func}"


TC_REGISTRY: dict[int, TestCase] = {
    2060101: TestCase(2060101, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001", "api", "partner", "GET internal partners list - SA filters are applied.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_001", ['api', 'regression'], "P2"),
    2060102: TestCase(2060102, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002", "api", "partner", "POST create internal partner - a pending account is created.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_002", ['api', 'regression'], "P2"),
    2060103: TestCase(2060103, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003", "api", "partner", "POST partner approve - activation + approval event are created.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_003", ['api', 'regression'], "P2"),
    2060104: TestCase(2060104, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004", "api", "partner", "partner application decline - mandatory reason is audit logged.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_004", ['api', 'regression'], "P2"),
    2060105: TestCase(2060105, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005", "api", "partner", "tier changed event - published so portal/analytics can refresh.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_005", ['api', 'regression'], "P2"),
    2060110: TestCase(2060110, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010", "api", "partner", "certification earned - granted, listed, and event published.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_010", ['api', 'regression'], "P2"),
    2060111: TestCase(2060111, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011", "api", "partner", "list with invalid pagination - graceful 4xx, never 5xx.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_011", ['api', 'regression'], "P2"),
    2060112: TestCase(2060112, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012", "api", "partner", "create with invalid/missing fields - 400 + field errors.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_012", ['api', 'regression'], "P2"),
    2060113: TestCase(2060113, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013", "api", "partner", "approve invalid/illegal-state - rejected with a clear error.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_013", ['api', 'regression'], "P2"),
    2060114: TestCase(2060114, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014", "api", "partner", "deactivate invalid id - rejected; repeat is idempotent.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_014", ['api', 'regression'], "P2"),
    2060115: TestCase(2060115, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015", "api", "partner", "change tier with invalid input - rejected with a clear error.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_015", ['api', 'regression'], "P2"),
    2060120: TestCase(2060120, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020", "api", "partner", "grant certification invalid input - rejected with a clear error.", "tests/blazeup_admin/api/test_sa_partners.py", "test_partner_api_partner_account_management_020", ['api', 'regression'], "P2"),
    2060201: TestCase(2060201, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_001", "api", "partner", "register a partner deal - deal is created (registered).", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_001", ['api', 'regression'], "P2"),
    2060202: TestCase(2060202, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_002", "api", "partner", "register reseller deal - billing model 'reseller' is stored.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_002", ['api', 'regression'], "P2"),
    2060203: TestCase(2060203, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_003", "api", "partner", "register co-sell deal - co-sell metadata is stored.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_003", ['api', 'regression'], "P2"),
    2060204: TestCase(2060204, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_004", "api", "partner", "register deal for an existing prospect - conflict raised.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_004", ['api', 'regression'], "P2"),
    2060208: TestCase(2060208, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_008", "api", "partner", "internal deal approve - approved + rate/rate-table version stamped.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_008", ['api', 'regression'], "P2"),
    2060209: TestCase(2060209, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_009", "api", "partner", "resolve conflict - decision and reasoning are immutable.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_009", ['api', 'regression'], "P2"),
    2060210: TestCase(2060210, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_010", "api", "partner", "deal approved event - published (CRM sync is downstream).", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_010", ['api', 'regression'], "P2"),
    2060213: TestCase(2060213, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_013", "api", "partner", "resolve conflict (prospect confirmation) - confirmed partner wins.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_013", ['api', 'regression'], "P2"),
    2060221: TestCase(2060221, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_021", "api", "partner", "register deal invalid/missing fields - rejected with 400.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_021", ['api', 'regression'], "P2"),
    2060228: TestCase(2060228, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_028", "api", "partner", "approve invalid/illegal-state deal - rejected with a clear error.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_028", ['api', 'regression'], "P2"),
    2060229: TestCase(2060229, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_029", "api", "partner", "resolve-conflict invalid input - rejected with a clear error.", "tests/blazeup_admin/api/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_029", ['api', 'regression'], "P2"),
    12010101: TestCase(12010101, "SHELL_UI_LOAD_TIME_PAGE_001", "ui", "shell", "every SA Dashboard page loads within budget (navigated via URL).", "tests/blazeup_admin/ui/test_load_time.py", "test_shell_ui_load_time_page_001", ['ui', 'regression'], "P2"),
    12010102: TestCase(12010102, "SHELL_UI_LOAD_TIME_PAGE_002", "ui", "shell", "every SA Dashboard page loads within budget (navigated via NAV).", "tests/blazeup_admin/ui/test_load_time.py", "test_shell_ui_load_time_page_002", ['ui', 'regression'], "P2"),
    12010201: TestCase(12010201, "SHELL_UI_PAGE_LOADS_001", "ui", "shell", "every page loads via direct URL (no MFE fetch error).", "tests/blazeup_admin/ui/test_page_loads.py", "test_shell_ui_page_loads_001", ['ui', 'smoke'], "P2"),
    12010202: TestCase(12010202, "SHELL_UI_PAGE_LOADS_002", "ui", "shell", "every page loads via sidebar NAV click (no MFE fetch error).", "tests/blazeup_admin/ui/test_page_loads.py", "test_shell_ui_page_loads_002", ['ui', 'regression'], "P2"),
    12020101: TestCase(12020101, "DASHBOARD_UI_VISIBLE_001", "ui", "dashboard", "Dashboard shows KPI cards + System Health panel (navigated via URL).", "tests/blazeup_admin/ui/test_dashboard.py", "test_dashboard_ui_visible_001", ['ui', 'regression'], "P2"),
}


def get_tc(tc_id: int) -> TestCase:
    if tc_id not in TC_REGISTRY:
        raise KeyError(f"TC {tc_id} does not exist in the registry")
    return TC_REGISTRY[tc_id]


def validate_registry() -> None:
    """Verify that all registered test functions exist (optional utility)."""
    for tc in TC_REGISTRY.values():
        path = Path(tc.test_path)
        if not path.exists():
            print(f"Warning: Test file {tc.test_path} missing for TC {tc.tc_id}")


def list_by_module(module: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]


def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]
