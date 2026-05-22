"""Pytest discovery entrypoint.

Keep this file thin so pytest can discover project fixtures and hooks while
the implementation stays organized under `pytest_support/`.
"""

from pytest_support.fixtures import (
    api_token,
    attendance_client,
    auth_client,
    authenticated_page,
    browser_context,
    fake,
    page,
    result_dir,
    settings,
    test_data,
    test_user,
)
from pytest_support.hooks import pytest_runtest_makereport

__all__ = [
    "api_token",
    "attendance_client",
    "auth_client",
    "authenticated_page",
    "browser_context",
    "fake",
    "page",
    "pytest_runtest_makereport",
    "result_dir",
    "settings",
    "test_data",
    "test_user",
]
