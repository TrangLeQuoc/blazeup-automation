"""Pytest hooks used by the automation framework."""

from collections.abc import Generator
from typing import Any

import pytest
from loguru import logger


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Generator[None, None, None]:
    """Expose test-phase reports to async fixtures and log failure details.

    Sets ``item.rep_<when>`` (setup / call / teardown) so fixtures can inspect
    the outcome during teardown (e.g. for screenshot-on-fail handling).

    For the *call* phase, also writes the full failure traceback at DEBUG level
    so it lands in the detailed log file without cluttering the terminal.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call" and report.failed and report.longrepr:
        longrepr_text = (
            report.longreprtext
            if hasattr(report, "longreprtext")
            else str(report.longrepr)
        )
        logger.debug(
            "Failure traceback for {}:\n{}",
            item.nodeid,
            longrepr_text,
        )
