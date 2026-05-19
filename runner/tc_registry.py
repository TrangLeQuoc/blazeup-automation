"""Central registry mapping BlazeUp HRMS test case numbers to pytest nodes. (AUTO-GENERATED)"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TestCase:
    """Metadata for a single automation test case."""

    tc_id: int
    type: Literal["api", "ui"]
    module: str
    title: str
    test_path: str
    test_func: str
    markers: list[str] = field(default_factory=list)
    priority: Literal["P1", "P2", "P3"] = "P2"

    @property
    def node_id(self) -> str:
        """Return the pytest node id for this test case."""
        return f"{self.test_path}::{self.test_func}"


TC_REGISTRY: dict[int, TestCase] = {
    1: TestCase(1, "api", "auth", "BlazeUp sign-in returns a bearer token.", "tests/api/test_auth_api.py", "test_tca01_login_returns_jwt_token", ['smoke'], "P1"),
    2: TestCase(2, "api", "auth", "BlazeUp sign-in with wrong password is rejected.", "tests/api/test_auth_api.py", "test_tca02_login_wrong_password_returns_401", [], "P2"),
    3: TestCase(3, "api", "auth", "POST /auth/logout returns 200 and revokes token.", "tests/api/test_auth_api.py", "test_tca03_logout_revokes_token", [], "P2"),
    4: TestCase(4, "api", "auth", "GET /auth-api/current-user returns authenticated user information.", "tests/api/test_auth_api.py", "test_tca04_get_me_returns_user_info", ['smoke'], "P1"),
    5: TestCase(5, "api", "auth", "Calling a protected API without token returns 401.", "tests/api/test_auth_api.py", "test_tca05_api_without_token_returns_401", [], "P2"),
    6: TestCase(6, "api", "auth", "Calling protected API with invalid/expired token returns 401 or 403.", "tests/api/test_auth_api.py", "test_tca06_api_with_expired_token_returns_401_or_403", [], "P2"),
    7: TestCase(7, "api", "attendance", "GET /time-api/attendances/status returns current work status.", "tests/api/test_attendance_api.py", "test_tca07_attendance_status_returns_status", ['smoke'], "P1"),
    8: TestCase(8, "api", "attendance", "Clocking in twice returns 409 Conflict.", "tests/api/test_attendance_api.py", "test_tca08_clock_in_twice_returns_409", [], "P2"),
    9: TestCase(9, "api", "attendance", "POST /attendance/clock-out returns duration.", "tests/api/test_attendance_api.py", "test_tca09_clock_out_returns_duration", [], "P2"),
    10: TestCase(10, "api", "attendance", "GET /attendance/history returns valid list format.", "tests/api/test_attendance_api.py", "test_tca10_attendance_history_returns_valid_list", [], "P2"),
    11: TestCase(11, "api", "attendance", "GET /time-api/attendances/status returns current status.", "tests/api/test_attendance_api.py", "test_tca11_today_attendance_returns_current_status", ['smoke'], "P1"),
    1001: TestCase(1001, "ui", "login", "Login succeeds with valid credentials.", "tests/ui/test_login.py", "test_tc01_login_success_with_valid_credentials", ['smoke'], "P1"),
    1002: TestCase(1002, "ui", "login", "Login fails with wrong password and shows an error.", "tests/ui/test_login.py", "test_tc02_login_fails_with_wrong_password", [], "P2"),
    1003: TestCase(1003, "ui", "login", "Login fails for an email that does not exist.", "tests/ui/test_login.py", "test_tc03_login_fails_with_unknown_email", [], "P2"),
    1004: TestCase(1004, "ui", "login", "User is redirected to the home page after login.", "tests/ui/test_login.py", "test_tc04_redirects_to_home_after_login", ['smoke'], "P1"),
    1005: TestCase(1005, "ui", "login", "Logout clears the browser session.", "tests/ui/test_login.py", "test_tc05_logout_clears_session", [], "P2"),
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
    """Return all test cases for a module."""

    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]
def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]
