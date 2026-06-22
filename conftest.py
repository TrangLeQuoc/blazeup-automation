"""Pytest discovery entrypoint.

Keep this file thin so pytest can discover project fixtures and hooks while
the implementation stays organized under `pytest_support/`.
"""

from pytest_support.fixtures import (
    api_token,
    auth_client,
    auth_state,
    authenticated_page,
    browser_context,
    created_resources,
    fake,
    make_page,
    page,
    result_dir,
    sa_deals_client,
    sa_partners_client,
    settings,
    tc_logger,
    test_data,
    test_user,
)
from pytest_support.hooks import pytest_runtest_makereport

__all__ = [
    "api_token",
    "auth_client",
    "auth_state",
    "authenticated_page",
    "browser_context",
    "created_resources",
    "fake",
    "make_page",
    "page",
    "pytest_runtest_makereport",
    "result_dir",
    "sa_deals_client",
    "sa_partners_client",
    "settings",
    "tc_logger",
    "test_data",
    "test_user",
]
