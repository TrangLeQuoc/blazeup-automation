#!/usr/bin/env python3
"""Entry point: run the BlazeUp test suite.

Usage:
    python -m runner.blazeup.run_test
    python -m runner.blazeup.run_test --execute 1 2 3
    python -m runner.blazeup.run_test --mode smoke
    python -m runner.blazeup.run_test --mode regression
"""

import sys
from pathlib import Path

# Ensure project root is on path
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from runner.blazeup.registry import TC_REGISTRY  # noqa: E402

# ---------------------------------------------------------------------------
# SA domain defaults — edit these directly
# ---------------------------------------------------------------------------

# TC IDs to run when no --execute / --mode flag is passed.
# (empty until BlazeUp Admin test cases are added to the registry)
DEFAULT_EXECUTE_IDS: list[str] = ["2060101-2061211"]

# TC IDs to always skip
DEFAULT_SKIP_IDS: list[str] = []

# Export results to Excel after every run (the Partner Platform test plan).
REPORT_EXCEL: bool = True

# Run AI failure triage automatically when a run has failures (writes ai_triage.md).
REPORT_AI_TRIAGE: bool = True

# Test-plan workbook this suite reports into.
EXCEL_FILE = _PROJECT_ROOT / "docs" / "blazeup" / "Partner_Platform_Test_Plan.xlsx"

# ---------------------------------------------------------------------------
# Re-use the shared CLI from runner/run_test.py but scoped to SA registry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Scope the shared runner to SA-only TCs.  runner.run_test and
    # runner.test_runner each bind their own `TC_REGISTRY` name at import time,
    # so patching only runner.tc_registry would leave them pointing at the full
    # merged registry.  Patch every module that holds a reference.
    import importlib

    import runner.tc_registry as _shared_reg
    import runner.test_runner as _test_runner

    _shared_reg.TC_REGISTRY = TC_REGISTRY  # type: ignore[assignment]
    _test_runner.TC_REGISTRY = TC_REGISTRY  # type: ignore[assignment]

    _run_module = importlib.import_module("runner.run_test")
    _run_module.TC_REGISTRY = TC_REGISTRY  # type: ignore[assignment]
    _run_module.DEFAULT_EXECUTE_IDS = DEFAULT_EXECUTE_IDS
    _run_module.DEFAULT_SKIP_IDS = DEFAULT_SKIP_IDS
    _run_module.REPORT_EXCEL = REPORT_EXCEL
    _run_module.REPORT_AI_TRIAGE = REPORT_AI_TRIAGE
    _run_module.EXCEL_FILE = EXCEL_FILE
    sys.exit(_run_module.main())
