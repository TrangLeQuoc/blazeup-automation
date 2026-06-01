"""Central registry mapping numeric TC IDs to pytest nodes.  (AUTO-GENERATED — do not edit)

TC ID Encoding
--------------
New-style  :  {type}{module:02d}{section:02d}{seq:02d}
              type 1=UI / 0=API   module 01=PARTNER   section/feature 01-17
              UI IDs >= 1_000_000 * API IDs <= 999_999 -> no collision.

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
    1: TestCase(1, "demo", "api", "auth", "BlazeUp sign-in returns a bearer token.", "tests/api/test_auth_api.py", "test_tca01_login_returns_jwt_token", ['smoke'], "P1"),
    2: TestCase(2, "demo", "api", "auth", "BlazeUp sign-in with wrong password is rejected.", "tests/api/test_auth_api.py", "test_tca02_login_wrong_password_returns_401", [], "P2"),
    3: TestCase(3, "demo", "api", "auth", "GET /auth-api/current-user returns authenticated user information.", "tests/api/test_auth_api.py", "test_tca04_get_me_returns_user_info", ['smoke'], "P1"),
    4: TestCase(4, "demo", "api", "auth", "Calling a protected API without token returns 401.", "tests/api/test_auth_api.py", "test_tca05_api_without_token_returns_401", [], "P2"),
    5: TestCase(5, "demo", "api", "auth", "Calling protected API with invalid/expired token returns 401 or 403.", "tests/api/test_auth_api.py", "test_tca06_api_with_expired_token_returns_401_or_403", [], "P2"),
    6: TestCase(6, "demo", "ui", "login", "Login succeeds with valid credentials.", "tests/ui/test_login.py", "test_tc01_login_success_with_valid_credentials", ['smoke'], "P1"),
    7: TestCase(7, "demo", "ui", "login", "Login fails with wrong password and shows an error.", "tests/ui/test_login.py", "test_tc02_login_fails_with_wrong_password", [], "P2"),
    8: TestCase(8, "demo", "ui", "login", "Login fails for an email that does not exist.", "tests/ui/test_login.py", "test_tc03_login_fails_with_unknown_email", [], "P2"),
    9: TestCase(9, "demo", "ui", "login", "Logout clears the browser session.", "tests/ui/test_login.py", "test_tc05_logout_clears_session", [], "P2"),
    10101: TestCase(10101, "PARTNER_API_AUTH_ACCESS_CONTROL_001", "api", "partner", "Authenticate - Valid partner JWT - Partner-scoped request succeeds", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_001", ['smoke'], "P1"),
    10102: TestCase(10102, "PARTNER_API_AUTH_ACCESS_CONTROL_002", "api", "partner", "Reject - Tenant JWT on partner API - Request is unauthorized", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_002", [], "P1"),
    10103: TestCase(10103, "PARTNER_API_AUTH_ACCESS_CONTROL_003", "api", "partner", "Reject - Partner JWT accessing another partner - Request is forbidden", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_003", [], "P1"),
    10104: TestCase(10104, "PARTNER_API_AUTH_ACCESS_CONTROL_004", "api", "partner", "Enforce - Admin MFA policy - Protected action requires MFA", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_004", [], "P1"),
    10105: TestCase(10105, "PARTNER_API_AUTH_ACCESS_CONTROL_005", "api", "partner", "Guard - MSP accesses payroll data - Request is forbidden", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_005", [], "P1"),
    10106: TestCase(10106, "PARTNER_API_AUTH_ACCESS_CONTROL_006", "api", "partner", "Guard - MSP exports employee records - Request is forbidden", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_006", [], "P1"),
    10107: TestCase(10107, "PARTNER_API_AUTH_ACCESS_CONTROL_007", "api", "partner", "Refresh - Valid refresh token - New access token is issued without re-login", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_007", [], "P1"),
    10108: TestCase(10108, "PARTNER_API_AUTH_ACCESS_CONTROL_008", "api", "partner", "Logout - Active partner session - Refresh token is invalidated", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_008", [], "P1"),
    10109: TestCase(10109, "PARTNER_API_AUTH_ACCESS_CONTROL_009", "api", "partner", "Change password - Valid current credentials - Password updated and sessions revoked", "tests/api/Auth_Access_Control/test_partner_api_auth_access_control.py", "test_partner_api_auth_access_control_009", [], "P2"),
    1010101: TestCase(1010101, "PARTNER_UI_PARTNER_PORTAL_SHELL_001", "ui", "partner", "Navigate - Open main menu routes - Correct page content is shown", "tests/ui/partner_portal_shell/test_partner_ui_partner_portal_shell.py", "test_partner_ui_partner_portal_shell_001", [], "P1"),
    1010102: TestCase(1010102, "PARTNER_UI_PARTNER_PORTAL_SHELL_002", "ui", "partner", "Responsive - Partner portal mobile layout - Controls remain usable", "tests/ui/partner_portal_shell/test_partner_ui_partner_portal_shell.py", "test_partner_ui_partner_portal_shell_002", [], "P2"),
    1010103: TestCase(1010103, "PARTNER_UI_PARTNER_PORTAL_SHELL_003", "ui", "partner", "Switch - Dual account partner activates account switcher - Pack and Channel dashboards toggle correctly", "tests/ui/partner_portal_shell/test_partner_ui_partner_portal_shell.py", "test_partner_ui_partner_portal_shell_003", [], "P2"),
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
