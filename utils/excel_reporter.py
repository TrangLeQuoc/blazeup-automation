"""Export automation test results back into a copy of the test-plan Excel workbook.

Usage (called from runner/test_runner.py when --excel-report is active):

    from utils.excel_reporter import write_excel_report

    out_path = write_excel_report(tc_summaries, result_dir, excel_path)
    # out_path is None when nothing to write (e.g. only legacy "demo" TCs were run)

Excel column mapping (Partner_Platform_Test_Plan.xlsx, "Partner Platform" sheet)
----------------------------------------------------------------------------------
Col C  (3)  TestcaseId         — lookup key  (e.g. PARTNER_UI_DASHBOARD_001)
Col H  (8)  Status             — formula, auto-recomputes in Excel — DO NOT WRITE
Col I  (9)  Manual Status      — not touched by automation
Col J  (10) Auto               — set to "YES" when automation covers the TC
Col K  (11) Automation Status  — written with PASSED / FAILED / NOT_STARTED

Status values accepted by the workbook formulas
------------------------------------------------
  PASSED  /  FAILED  /  IN_PROGRESS  /  BLOCKED  /  NOT_STARTED
"""

import shutil
from datetime import datetime
from pathlib import Path

import openpyxl
from loguru import logger

# ---------------------------------------------------------------------------
# Module → Excel sheet mapping.  Must mirror EXCEL_SHEETS in sync_registry.py.
# ---------------------------------------------------------------------------

MODULE_TO_SHEET: dict[str, str] = {
    "blazeup_partner": "Partner Platform",
    # "health": "Health System",   # uncomment when that sheet exists
}

# ---------------------------------------------------------------------------
# Column positions (1-based — used with ws.cell(row=r, column=c))
# ---------------------------------------------------------------------------

COL_TC_STRING = 3  # C: TestcaseId
COL_AUTO_FLAG = 10  # J: Auto  ("YES" / "NO")
COL_AUTO_STATUS = 11  # K: Automation Status

DATA_START_ROW = 13  # first row that contains test-case data

# ---------------------------------------------------------------------------
# pytest outcome → Excel automation status
# ---------------------------------------------------------------------------

_OUTCOME_MAP: dict[str, str] = {
    "PASSED": "PASSED",
    "FAILED": "FAILED",
    "ERROR": "FAILED",
    "BLOCKED": "BLOCKED",
    "SKIPPED": "NOT_STARTED",
    "MISSING": "NOT_STARTED",
    "UNKNOWN": "NOT_STARTED",
}


def _outcome_from_summary(s: dict) -> str:
    """Convert a tc_summary dict into an Excel automation status string."""
    if s["failed"] > 0:
        return "FAILED"
    if s.get("blocked", 0) > 0:
        return "BLOCKED"
    if s["passed"] > 0:
        return "PASSED"
    # skipped / missing
    return "NOT_STARTED"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def write_excel_report(
    tc_summaries: list[dict],
    result_dir: Path,
    excel_path: Path,
) -> "Path | None":
    """Copy *excel_path*, fill automation results, save to *result_dir*.

    Args:
        tc_summaries:  List of summary dicts produced by
                       ``_build_tc_summaries_from_rows()`` / ``_build_tc_summaries_from_perf()``.
                       Each dict has keys: tc_id, passed, failed, skipped, …
        result_dir:    Run result directory (e.g. results/run_20260526_113058).
                       The output file is written here.
        excel_path:    Source test-plan Excel file
                       (Partner_Platform_Test_Plan.xlsx at project root).

    Returns:
        Path to the generated ``.xlsx`` file, or ``None`` when nothing was
        written (no matchable TCs in the run, or source file missing).
    """
    if not excel_path.exists():
        logger.warning("Excel template not found: {} — skipping Excel report", excel_path)
        return None

    # ── Build tc_string → outcome lookup from summaries ───────────────────
    try:
        from runner.tc_registry import TC_REGISTRY
    except ModuleNotFoundError:
        from tc_registry import TC_REGISTRY  # type: ignore[no-redef]

    result_lookup: dict[str, str] = {}
    for s in tc_summaries:
        tc = TC_REGISTRY.get(s["tc_id"])
        if tc is None:
            continue
        if not tc.tc_string or tc.tc_string == "demo":
            # Legacy / demo TCs have no Excel row — skip
            continue
        result_lookup[tc.tc_string] = _outcome_from_summary(s)

    if not result_lookup:
        logger.debug("Excel report: no new-style TCs in this run — skipping")
        return None

    # ── Copy the workbook ──────────────────────────────────────────────────
    # Reuse the run dir's timestamp (run_YYYYMMDD_HHMMSS) so the Excel filename
    # matches the folder. Fall back to now() if the dir name isn't a run_* folder.
    run_name = result_dir.name
    timestamp = (
        run_name[len("run_") :]
        if run_name.startswith("run_")
        else datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    out_name = f"{excel_path.stem}_result_{timestamp}.xlsx"
    out_path = result_dir / out_name
    shutil.copy2(excel_path, out_path)

    # ── Open and update ────────────────────────────────────────────────────
    wb = openpyxl.load_workbook(out_path)
    updated = 0

    for module_name, sheet_name in MODULE_TO_SHEET.items():
        if sheet_name not in wb.sheetnames:
            logger.debug(
                "Sheet '{}' not in workbook — skipping module '{}'", sheet_name, module_name
            )
            continue

        ws = wb[sheet_name]
        for row_idx in range(DATA_START_ROW, ws.max_row + 1):
            tc_str = ws.cell(row=row_idx, column=COL_TC_STRING).value
            if not tc_str:
                continue
            tc_str = str(tc_str).strip()
            if tc_str not in result_lookup:
                continue

            outcome = result_lookup[tc_str]
            ws.cell(row=row_idx, column=COL_AUTO_FLAG).value = "YES"
            ws.cell(row=row_idx, column=COL_AUTO_STATUS).value = outcome
            logger.debug("  {} → Automation Status = {}", tc_str, outcome)
            updated += 1

    if updated == 0:
        # Nothing matched a workbook row — don't leave an unchanged copy behind.
        # Discard the file we copied and report nothing, even though Excel
        # reporting was requested (REPORT_EXCEL=True).
        wb.close()
        out_path.unlink(missing_ok=True)
        logger.warning(
            "Excel report: none of the {} tc_string(s) matched any row in the workbook "
            "- no result file written",
            len(result_lookup),
        )
        return None

    wb.save(out_path)
    logger.info("Excel report saved: {} ({} TC(s) updated)", out_path.name, updated)
    return out_path
