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

# Default TC IDs to execute when running `python -m runner.run_test` without arguments.
Execute_list_TC: list[str] = ["1001-1004"]

# TC IDs to skip when using the default execute list.
Skip_list_TC: list[str] = []


def parse_tc_range(tc_inputs: list[str]) -> list[int]:
    """Parse TC IDs from input, supporting ranges like '1001-1010' and individual IDs."""
    result = []
    for item in tc_inputs:
        if '-' in item:
            try:
                start, end = item.split('-')
                start_int = int(start)
                end_int = int(end)
                result.extend(range(start_int, end_int + 1))
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
        help="Override Execute_list_TC with a custom list of TC IDs. Supports ranges: 1001-1010 or individual: 1001 1002 1003",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        type=str,
        help="Skip these TC IDs. Supports ranges: 1001-1005 or individual: 1001 1003",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run Allure serve automatically after test execution.",
    )
    parser.add_argument("--list", action="store_true", help="List registered test cases.")
    parser.add_argument("--module", type=str, help="Run test cases from a module, for example: auth or login.")
    parser.add_argument("--type", choices=["api", "ui"], action="append", help="Run test cases by type.")
    parser.add_argument("--marker", type=str, help="Run test cases by pytest marker.")
    parser.add_argument("--debug-log", action="store_true", help="Write DEBUG level logs to the run log file.")
    args = parser.parse_args()

    if args.list:
        for tc_id, tc in sorted(TC_REGISTRY.items()):
            markers = f" [{', '.join(tc.markers)}]" if tc.markers else ""
            print(f"{tc_id}: {tc.type}/{tc.module} - {tc.title}{markers}")
        return 0

    default_execute_ids = parse_tc_range(Execute_list_TC)
    default_skip_ids = parse_tc_range(Skip_list_TC)

    if args.execute:
        execute_ids = parse_tc_range(args.execute)
    elif args.module:
        execute_ids = [tc.tc_id for tc in list_by_module(args.module)]
    elif args.type:
        execute_ids = [tc.tc_id for tc_type in args.type for tc in list_by_type(tc_type)]
    elif args.marker:
        execute_ids = [tc.tc_id for tc in list_by_marker(args.marker)]
    else:
        execute_ids = default_execute_ids

    skip_ids = parse_tc_range(args.skip) if args.skip else default_skip_ids
    selected_ids = [tc_id for tc_id in execute_ids if tc_id not in set(skip_ids)]

    if not selected_ids:
        print("No TC IDs to run. Update Execute_list_TC or pass --execute.")
        return 1

    return run_tc_ids(selected_ids, debug_log=args.debug_log, serve_allure=args.serve)


if __name__ == "__main__":
    sys.exit(main())
