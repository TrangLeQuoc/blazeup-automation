"""Pytest hooks used by the automation framework."""

from collections.abc import Generator
from typing import Any

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Generator[None, None, None]:
    """Expose test phase reports to async fixtures for screenshot-on-fail handling."""

    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

