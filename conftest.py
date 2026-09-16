"""Pytest discovery entrypoint.

Keep this file thin so pytest can discover project fixtures and hooks while
the implementation stays organized under `pytest_support/`.
"""

from pytest_support.fixtures import (
    api_token,
    auth_client,
    authenticated_page,
    browser_context,
    created_resources,
    fake,
    make_page,
    make_partner_page,
    page,
    partner_auth_state,
    partner_authenticated_page,
    partner_session_started_at,
    result_dir,
    sa_cleanup,
    sa_commissions_client,
    sa_deals_client,
    sa_partners_client,
    seeded_partner,
    settings,
    tc_logger,
    test_user,
)
from pytest_support.hooks import pytest_collection_modifyitems, pytest_runtest_makereport

__all__ = [
    "api_token",
    "auth_client",
    "authenticated_page",
    "browser_context",
    "created_resources",
    "fake",
    "make_page",
    "make_partner_page",
    "page",
    "partner_authenticated_page",
    "partner_auth_state",
    "partner_session_started_at",
    "pytest_collection_modifyitems",
    "pytest_runtest_makereport",
    "result_dir",
    "sa_cleanup",
    "sa_commissions_client",
    "sa_deals_client",
    "sa_partners_client",
    "seeded_partner",
    "settings",
    "tc_logger",
    "test_user",
]
