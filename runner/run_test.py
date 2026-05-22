#!/usr/bin/env python3
"""Light wrapper to run BlazeUp HRMS tests by TC number."""

import argparse
import sys

try:
    from runner.test_runner import run_tc_ids
    from runner.tc_registry import TC_REGISTRY, list_by_marker, list_by_module, list_by_type
except ModuleNotFoundError:
    from test_runner import run_tc_ids
    from tc_registry import TC_REGISTRY, list_by_marker, list_by_module, list_by_type

# Empty list = run all registered test cases when no filter flags are passed.
DEFAULT_EXECUTE_IDS: list[str] = []

# TC IDs to skip when using the default execute list.
DEFAULT_SKIP_IDS: list[str] = []


def parse_tc_range(tc_inputs: list[str]) -> list[int]:
    """Parse TC IDs from input, supporting ranges like '1001-1010' and individual IDs."""
    result = []
    for item in tc_inputs:
        if '-' in item:
            try:
                start, end = item.split('-')
                result.extend(range(int(start), int(end) + 1))
            except (ValueError, AttributeError):
                print(f"Warning: Invalid range format '{item}'. Expected format: 1001-1010")
        else:
            try:
                result.append(int(item))
            except ValueError:
                print(f"Warning: Invalid TC ID '{item}'. Expected numeric format.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run BlazeUp HRMS tests by TC ID")
    parser.add_argument(
        "--execute",
        nargs="+",
        type=str,
        help="TC IDs to run. Supports ranges (1001-1010) or individual IDs (1001 1002).",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        type=str,
        help="TC IDs to skip. Supports ranges (1001-1005) or individual IDs.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run Allure serve automatically after test execution.",
    )
    parser.add_argument("--list", action="store_true", help="List registered test cases.")
    parser.add_argument("--module", type=str, help="Run test cases from a module, e.g. auth or login.")
    parser.add_argument("--type", choices=["api", "ui"], action="append", help="Run test cases by type.")
    parser.add_argument("--marker", type=str, help="Run test cases by pytest marker.")
    parser.add_argument("--debug-log", action="store_true", help="Write DEBUG level logs to the run log file.")
    args = parser.parse_args()

    if args.list:
        for tc_id, tc in sorted(TC_REGISTRY.items()):
            markers = f" [{', '.join(tc.markers)}]" if tc.markers else ""
            print(f"{tc_id}: {tc.type}/{tc.module} - {tc.title}{markers}")
        return 0

    if args.execute:
        execute_ids = parse_tc_range(args.execute)
    elif args.module:
        execute_ids = [tc.tc_id for tc in list_by_module(args.module)]
    elif args.type:
        execute_ids = [tc.tc_id for tc_type in args.type for tc in list_by_type(tc_type)]
    elif args.marker:
        execute_ids = [tc.tc_id for tc in list_by_marker(args.marker)]
    else:
        # Default: run every registered test case
        execute_ids = sorted(TC_REGISTRY.keys())

    skip_ids = set(parse_tc_range(args.skip)) if args.skip else set(parse_tc_range(DEFAULT_SKIP_IDS))
    selected_ids = [tc_id for tc_id in execute_ids if tc_id not in skip_ids]

    if not selected_ids:
        print("No TC IDs to run. Use --list to see available test cases.")
        return 1

    return run_tc_ids(selected_ids, debug_log=args.debug_log, serve_allure=args.serve)


if __name__ == "__main__":
    sys.exit(main())
