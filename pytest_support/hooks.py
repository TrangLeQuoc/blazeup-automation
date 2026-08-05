"""Pytest hooks used by the automation framework."""

from collections.abc import Generator
from typing import Any

import pytest
from loguru import logger


def _suite_labels(test_path: str) -> tuple[str, str] | None:
    """Derive (parentSuite, suite) for the Allure hierarchy from a test file path.

    ``…/tests/<domain>/api/partner/test_x.py``  -> ("API", "partner")
    ``…/tests/<domain>/ui/partner/my_pipeline/…`` -> ("UI", "my_pipeline")
    ``…/tests/<domain>/ui/partner_sa/…``          -> ("UI", "partner_sa")

    parentSuite = API / UI (the layer folder); suite = the feature folder directly
    containing the test file. Returns ``None`` for paths outside api/ui so those
    keep Allure's default grouping.
    """
    parts = test_path.replace("\\", "/").split("/")
    for layer, label in (("api", "API"), ("ui", "UI")):
        if layer in parts:
            feature = parts[-2] if len(parts) >= 2 else label
            return label, feature
    return None


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Give Allure a consistent 2-level suite tree derived from the test path.

    Without this, Allure's default suite is the raw package path, so the flat
    ``api/partner`` folder shows as ONE suite while the per-feature ``ui/*``
    folders fan out into many — an asymmetric ``Suites`` tab. Setting explicit
    ``parentSuite`` (API/UI) + ``suite`` (feature) normalises both layers into
    ``API ▸ partner`` / ``UI ▸ my_pipeline`` / … while preserving per-feature detail.
    """
    try:
        import allure
    except ImportError:  # allure-pytest not installed → nothing to label
        return
    for item in items:
        labels = _suite_labels(str(getattr(item, "path", None) or item.fspath))
        if labels is None:
            continue
        parent, feature = labels
        item.add_marker(allure.label("parentSuite", parent))
        item.add_marker(allure.label("suite", feature))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Generator[None]:
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
            report.longreprtext if hasattr(report, "longreprtext") else str(report.longrepr)
        )
        logger.debug(
            "Failure traceback for {}:\n{}",
            item.nodeid,
            longrepr_text,
        )
