#!/usr/bin/env python3
"""Light wrapper to run BlazeUp HRMS tests by TC number.

Execution Modes (--mode):
  normal      Run TCs by explicit ID list (default)
  regression  Auto-select all P1 priority TCs
  smoke       Auto-select all smoke-marked TCs

Repeat Modes (--repeat N + --repeat-mode):
  batch       Run full list x N  ->  [1,2,3, 1,2,3, ...]  (system stability)
  each        Run each TC x N   ->  [1,1,1, 2,2,2, ...]  (flaky detection)

Examples:
  python -m runner.run_test --mode regression
  python -m runner.run_test --execute 1 2 3 --repeat 10 --repeat-mode each
  python -m runner.run_test --mode smoke --repeat 5 --repeat-mode batch
  python -m runner.run_test --execute 1001 1002 --repeat 20 --dry-run
  python -m runner.run_test --mode regression --priority P1 --type api
"""

import argparse
import sys
from pathlib import Path

try:
    from runner.tc_registry import (
        TC_REGISTRY,
        TestCase,
        list_by_marker,
        list_by_module,
        list_by_type,
    )
    from runner.test_runner import run_performance_plan, run_tc_ids
except ModuleNotFoundError:
    from tc_registry import TC_REGISTRY, TestCase, list_by_marker, list_by_module, list_by_type
    from test_runner import run_performance_plan, run_tc_ids

# ---------------------------------------------------------------------------
# Default run lists — edit these directly instead of passing CLI flags every time
# ---------------------------------------------------------------------------

# TC IDs to run when no --execute / --mode / --module / --marker is passed.
# Supports individual IDs and ranges, e.g. ["1", "4", "7-11", "1001-1005"]
# Leave empty [] to run ALL registered test cases.
# Note: Currently empty because all demo TCs have been removed. Real test cases
# will be added once test plans for each domain are finalized.
DEFAULT_EXECUTE_IDS: list[str] = []

# TC IDs to always skip (blacklist).
# Supports individual IDs and ranges, e.g. ["3", "1003"]
DEFAULT_SKIP_IDS: list[str] = []

# Set True to export results to a timestamped copy of Partner_Platform_Test_Plan.xlsx
# after every run.  Override from the CLI with --no-excel-report to skip for one run.
REPORT_EXCEL: bool = True

# Set True to run AI failure triage automatically when a run has failures,
# writing ai_triage.md into the result dir. Provider/model come from settings
# (AI_PROVIDER / AI_MODEL). Override from the CLI with --no-ai-triage.
REPORT_AI_TRIAGE: bool = True

# Test-plan workbook used for --excel-report.
#   None  -> auto-resolve per domain from BLAZEUP_DOMAIN:
#            docs/{domain}/Partner_Platform_Test_Plan.xlsx
#   Path  -> explicit override (domain runners patch this).
EXCEL_FILE: "Path | None" = None

_BOLD = "\033[1m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_YELLOW = "\033[93m"
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Helper: build a human-readable mode label for the summary header
# ---------------------------------------------------------------------------


def _display_mode(args: argparse.Namespace) -> str:
    """Return a short human-readable label describing how TCs were selected.

    Examples::

        regression              -> "regression"
        regression + --priority -> "regression (priority=P1)"
        normal + --module auth  -> "normal (module=auth)"
        normal + --execute 1 2  -> "normal (ids=2 specified)"
    """
    base = args.mode  # "normal", "regression", "smoke"
    extras: list[str] = []
    if args.priority:
        extras.append(f"priority={args.priority}")
    if args.module:
        extras.append(f"module={args.module}")
    if getattr(args, "type", None):
        extras.append(f"type={'+'.join(args.type)}")
    if args.marker:
        extras.append(f"marker={args.marker}")
    if args.execute:
        extras.append(f"ids={len(args.execute)} specified")
    return f"{base} ({', '.join(extras)})" if extras else base


# ---------------------------------------------------------------------------
# Helper: ID parsing
# ---------------------------------------------------------------------------


def parse_tc_range(tc_inputs: list[str]) -> list[int]:
    """Parse TC IDs from input, supporting ranges like '1001-1010' and individual IDs."""
    result = []
    for item in tc_inputs:
        if "-" in item:
            try:
                start, end = item.split("-", 1)
                result.extend(range(int(start), int(end) + 1))
            except (ValueError, AttributeError):
                print(f"Warning: Invalid range format '{item}'. Expected: 1001-1010")
        else:
            try:
                result.append(int(item))
            except ValueError:
                print(f"Warning: Invalid TC ID '{item}'. Expected numeric format.")
    return result


# ---------------------------------------------------------------------------
# Helper: filtering
# ---------------------------------------------------------------------------


def filter_by_priority(tcs: list[TestCase], priority: str) -> list[TestCase]:
    """Return only TCs matching the given priority."""
    return [tc for tc in tcs if tc.priority == priority]


def _filter_to_registry(ids: list[int]) -> list[int]:
    """Keep only IDs that exist in the registry; silently drop the rest.

    This makes range notation like '1-1010' intuitive — you get whatever
    exists in that range without warnings for gaps.
    """
    return [tc_id for tc_id in ids if tc_id in TC_REGISTRY]


def resolve_base_ids(args: argparse.Namespace) -> list[int]:
    """Resolve the initial list of TC IDs from mode/execute/module/type/marker args."""

    # Explicit --execute: honour range notation, silently skip non-existent IDs
    if args.execute:
        return _filter_to_registry(parse_tc_range(args.execute))

    mode = args.mode

    if mode == "regression":
        return [tc.tc_id for tc in TC_REGISTRY.values() if tc.priority == "P1"]

    if mode == "smoke":
        return [tc.tc_id for tc in TC_REGISTRY.values() if "smoke" in tc.markers]

    # normal mode -- narrow down by secondary filters if present
    if args.module:
        return [tc.tc_id for tc in list_by_module(args.module)]
    if args.type:
        return [tc.tc_id for tc_type in args.type for tc in list_by_type(tc_type)]
    if args.marker:
        return [tc.tc_id for tc in list_by_marker(args.marker)]

    # Absolute default: use DEFAULT_EXECUTE_IDS if set, otherwise run every registered TC
    if DEFAULT_EXECUTE_IDS:
        return _filter_to_registry(parse_tc_range(DEFAULT_EXECUTE_IDS))
    return sorted(TC_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Helper: repeat strategy
# ---------------------------------------------------------------------------


def apply_repeat_strategy(base_ids: list[int], repeat: int, repeat_mode: str) -> list[list[int]]:
    """
    Build the list of *batches* to execute.

    Returns a list of batches where each batch is a list of TC IDs for one
    pytest invocation.

    batch  ->  [[1,2,3], [1,2,3], [1,2,3]]          N full-suite runs
    each   ->  [[1],[1],[1],[2],[2],[2]]              each TC x N before next
    """
    if repeat <= 1:
        return [base_ids]

    if repeat_mode == "each":
        batches: list[list[int]] = []
        for tc_id in base_ids:
            batches.extend([[tc_id]] * repeat)
        return batches

    # batch (default)
    return [list(base_ids)] * repeat


# ---------------------------------------------------------------------------
# Helper: dry-run display
# ---------------------------------------------------------------------------


def print_dry_run(base_ids: list[int], repeat: int, repeat_mode: str) -> None:
    """Print what would be executed without actually running any tests."""

    unique_ids = list(dict.fromkeys(base_ids))  # preserve order, deduplicate
    total_runs = len(base_ids) * repeat

    print(f"\n{_BLUE}{_BOLD}=== DRY RUN -- Execution Plan ==={_RESET}")
    print(f"  Mode           : {repeat_mode}")
    print(f"  Unique TCs     : {len(unique_ids)}")
    print(f"  Repeat         : {repeat}x")
    print(f"  Total TC runs  : {total_runs}")
    print()

    for tc_id in unique_ids:
        tc = TC_REGISTRY.get(tc_id)
        if tc:
            markers = f"  [{', '.join(tc.markers)}]" if tc.markers else ""
            print(
                f"  {_CYAN}TC {tc_id:>5}{_RESET}  [{tc.priority}]  {tc.type}/{tc.module}  {tc.title}{markers}"
            )
        else:
            print(f"  TC {tc_id:>5}  ⚠ NOT IN REGISTRY")

    if repeat > 1:
        batches = apply_repeat_strategy(base_ids, repeat, repeat_mode)
        preview_labels = [
            str(b[0]) if len(b) == 1 else f"[{','.join(str(i) for i in b)}]" for b in batches[:8]
        ]
        suffix = f"  ... (+{len(batches) - 8} more)" if len(batches) > 8 else ""
        print(f"\n  Batch order: {', '.join(preview_labels)}{suffix}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run BlazeUp HRMS tests by TC ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # ── Selection ──────────────────────────────────────────────────────────
    sel = parser.add_argument_group("selection")
    sel.add_argument(
        "--execute",
        nargs="+",
        type=str,
        help="Explicit TC IDs. Supports ranges (1001-1010) and individual IDs.",
    )
    sel.add_argument(
        "--skip", nargs="+", type=str, help="TC IDs to exclude. Supports ranges and individual IDs."
    )
    sel.add_argument(
        "--mode",
        choices=["normal", "regression", "smoke"],
        default="normal",
        help="normal=by ID, regression=P1 only, smoke=smoke-marked (default: normal)",
    )
    sel.add_argument(
        "--priority",
        choices=["P1", "P2", "P3"],
        help="Additional priority filter applied after mode/module/marker.",
    )
    sel.add_argument("--module", type=str, help="Run TCs from a module, e.g. auth or login.")
    sel.add_argument(
        "--type",
        choices=["api", "ui"],
        action="append",
        help="Filter by test type (may be repeated: --type api --type ui).",
    )
    sel.add_argument("--marker", type=str, help="Filter by pytest marker.")

    # ── Performance ────────────────────────────────────────────────────────
    perf = parser.add_argument_group("performance / stability")
    perf.add_argument(
        "--repeat", type=int, default=1, metavar="N", help="Run selected TCs N times (default: 1)."
    )
    perf.add_argument(
        "--repeat-mode",
        choices=["each", "batch"],
        default="batch",
        dest="repeat_mode",
        help="each=[TC1xN,TC2xN] (flaky), batch=[[TC1,TC2]xN] (stability)  (default: batch)",
    )
    perf.add_argument(
        "--fail-fast-count",
        type=int,
        default=0,
        metavar="N",
        dest="fail_fast_count",
        help="Abort after N total failures across all iterations (0 = disabled).",
    )

    # ── Output ─────────────────────────────────────────────────────────────
    out = parser.add_argument_group("output")
    out.add_argument("--list", action="store_true", help="List all registered TCs and exit.")
    out.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Show execution plan without running tests.",
    )
    out.add_argument("--serve", action="store_true", help="Open Allure report after execution.")
    out.add_argument(
        "--excel-report",
        action=argparse.BooleanOptionalAction,
        default=REPORT_EXCEL,
        dest="excel_report",
        help=f"Export results to a timestamped copy of Partner_Platform_Test_Plan.xlsx "
        f"(default: {REPORT_EXCEL}). Use --no-excel-report to skip for one run.",
    )
    out.add_argument(
        "--ai-triage",
        action=argparse.BooleanOptionalAction,
        default=REPORT_AI_TRIAGE,
        dest="ai_triage",
        help=f"Run AI failure triage and write ai_triage.md when the run has failures "
        f"(default: {REPORT_AI_TRIAGE}). Use --no-ai-triage to skip for one run.",
    )
    out.add_argument(
        "--debug-log", action="store_true", help="Write DEBUG-level logs to the run log file."
    )

    args = parser.parse_args()

    # ── --list ──────────────────────────────────────────────────────────────
    if args.list:
        for tc_id, tc in sorted(TC_REGISTRY.items()):
            markers = f"  [{', '.join(tc.markers)}]" if tc.markers else ""
            print(f"  {tc_id:>5}  [{tc.priority}]  {tc.type}/{tc.module}  {tc.title}{markers}")
        return 0

    # ── Resolve TC IDs ──────────────────────────────────────────────────────
    base_ids = resolve_base_ids(args)

    if args.priority:
        base_ids = [
            tc_id
            for tc_id in base_ids
            if TC_REGISTRY.get(tc_id) and TC_REGISTRY[tc_id].priority == args.priority
        ]

    skip_ids = (
        set(parse_tc_range(args.skip)) if args.skip else set(parse_tc_range(DEFAULT_SKIP_IDS))
    )
    base_ids = [tc_id for tc_id in base_ids if tc_id not in skip_ids]

    if not base_ids:
        print("No TC IDs matched the given filters. Use --list to see available test cases.")
        # Exit 5 = "nothing collected" (mirrors pytest's convention). CI treats
        # this as a non-failure so an empty domain/suite stays green instead of
        # looking like a real test failure.
        return 5

    repeat = max(1, args.repeat)
    mode = _display_mode(args)

    # ── --dry-run ───────────────────────────────────────────────────────────
    if args.dry_run:
        print_dry_run(base_ids, repeat, args.repeat_mode)
        return 0

    # ── Execute ─────────────────────────────────────────────────────────────
    if repeat > 1:
        return run_performance_plan(
            base_ids,
            repeat=repeat,
            repeat_mode=args.repeat_mode,
            mode=mode,
            debug_log=args.debug_log,
            fail_fast_count=args.fail_fast_count,
        )

    return run_tc_ids(
        base_ids,
        mode=mode,
        debug_log=args.debug_log,
        serve_allure=args.serve,
        excel_report=args.excel_report,
        excel_path=EXCEL_FILE,
        ai_triage=args.ai_triage,
    )


if __name__ == "__main__":
    sys.exit(main())
