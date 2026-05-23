#!/usr/bin/env python3
"""Core BlazeUp HRMS test execution helper."""

import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from loguru import logger

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None  # type: ignore[assignment]

try:
    from runner.tc_registry import TC_REGISTRY, TestCase, get_tc
except ModuleNotFoundError:
    from tc_registry import TC_REGISTRY, TestCase, get_tc

# ANSI color codes (used in print_summary and run_tc_ids)
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _bold(text: str) -> str:
    return f"{_BOLD}{text}{_RESET}"


def make_result_dir(base_dir: Path = Path('.')) -> Path:
    """Create results/run_YYYYMMDD_HHMMSS with report artifact subfolders."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = base_dir / "results" / f"run_{timestamp}"
    for subfolder in ["logs", "videos", "screenshots", "traces", "allure-results"]:
        (base / subfolder).mkdir(parents=True, exist_ok=True)
    return base


def build_pytest_args(tcs: list[TestCase], result_dir: Path, debug_log: bool = False) -> list[str]:
    """Build pytest CLI arguments for the selected test cases."""

    node_ids = [tc.node_id for tc in tcs]
    log_level = "DEBUG" if debug_log else "INFO"
    return [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-s",
        "--tb=short",
        *node_ids,
        f"--html={result_dir / 'report.html'}",
        "--self-contained-html",
        f"--alluredir={result_dir / 'allure-results'}",
        f"--log-file={result_dir / 'logs' / 'test.log'}",
        f"--log-file-level={log_level}",
        "--log-cli-level=INFO",
        "--log-disable=faker",
        "--log-disable=faker.factory",
        "--log-disable=asyncio",
        f"--junitxml={result_dir / 'logs' / 'junit.xml'}",
        "-p",
        "no:cacheprovider",
    ]


def resolve_tcs(tc_ids: list[int]) -> list[TestCase]:
    """Resolve requested test cases from numeric IDs."""

    if not TC_REGISTRY:
        logger.error("Test Registry is empty. Please run 'python utils/sync_registry.py' first!")
        return []

    selected: list[TestCase] = []
    for tc_id in tc_ids:
        try:
            selected.append(get_tc(tc_id))
        except KeyError:
            logger.warning("TC ID {} not found in registry. Try running sync_registry.py.", tc_id)
    return selected


def parse_junit_xml(junit_path: Path, tcs: list[TestCase]) -> list[dict[str, str]]:
    """Parse the generated junit XML and return status rows for each requested TC."""

    if not junit_path.exists():
        return [
            {
                "tc_id": str(tc.tc_id),
                "test_func": tc.test_func,
                "title": tc.title,
                "status": "UNKNOWN",
                "time": "0",
                "message": "JUnit XML not found",
            }
            for tc in tcs
        ]

    tree = ET.parse(junit_path)
    root = tree.getroot()
    testcases = root.findall(".//testcase")
    rows: list[dict[str, str]] = []

    for tc in tcs:
        expected_class = tc.test_path.replace("/", ".").replace("\\", ".").removesuffix(".py")
        matched = None
        for testcase in testcases:
            if testcase.attrib.get("name") == tc.test_func:
                classname = testcase.attrib.get("classname", "")
                if classname == expected_class or matched is None:
                    matched = testcase
                    if classname == expected_class:
                        break

        status = "MISSING"
        message = ""
        duration = matched.attrib.get("time", "0") if matched is not None else "0"
        if matched is not None:
            if matched.find("failure") is not None:
                status = "FAILED"
                message = matched.find("failure").text or ""
            elif matched.find("error") is not None:
                status = "ERROR"
                message = matched.find("error").text or ""
            elif matched.find("skipped") is not None:
                status = "SKIPPED"
                message = matched.find("skipped").attrib.get("message", "")
            else:
                status = "PASSED"

        rows.append(
            {
                "tc_id": str(tc.tc_id),
                "test_func": tc.test_func,
                "title": tc.title,
                "status": status,
                "time": duration,
                "message": message.strip().splitlines()[0] if message else "",
            }
        )
    return rows


def print_summary(summary_rows: list[dict[str, str]]) -> None:
    """Print a clean summary table for the selected test cases."""

    status_colors = {
        "PASSED": f"{_GREEN}PASSED{_RESET}",
        "FAILED": f"{_RED}FAILED{_RESET}",
        "ERROR": f"{_RED}ERROR{_RESET}",
        "SKIPPED": f"{_YELLOW}SKIPPED{_RESET}",
    }

    headers = [
        _bold("TC ID"), _bold("Status"), _bold("Time"), _bold("Title"), _bold("Message"),
    ]
    table_data = [
        [
            f"{_BLUE}{r['tc_id']}{_RESET}",
            status_colors.get(r["status"], r["status"]),
            f"{r['time']}s",
            r["title"],
            r["message"],
        ]
        for r in summary_rows
    ]

    print(f"\n{_bold('=== TEST EXECUTION SUMMARY ===')}")
    if tabulate is not None:
        print(tabulate(table_data, headers=headers, tablefmt="github"))
    else:
        for row in table_data:
            print(f"ID: {row[0]} | {row[1]} | {row[2]} | {row[3]}")


def serve_allure_report(allure_dir: Path, env: dict[str, str], cwd: Path) -> int:
    """Launch Allure serve on the generated allure-results folder."""

    if not allure_dir.exists():
        print(f"Allure data not found: {allure_dir}")
        return 1

    if shutil.which("allure") is None:
        print("Allure CLI is not installed or not on PATH. Install Allure and retry.")
        return 1

    print(f"Opening Allure report from {allure_dir}")
    result = subprocess.run(["allure", "serve", str(allure_dir)], env=env, cwd=cwd)
    return result.returncode


def run_tc_ids(tc_ids: list[int], debug_log: bool = False, serve_allure: bool = False) -> int:
    """Run the given test case IDs and return the pytest return code."""

    base_dir = Path(__file__).resolve().parents[1]
    tcs = resolve_tcs(tc_ids)
    if not tcs:
        print("No valid test cases selected. Use numeric TC IDs only.")
        return 1

    result_dir = make_result_dir(base_dir).resolve()
    metadata = {
        "run_at": datetime.now().isoformat(),
        "tc_ids": [tc.tc_id for tc in tcs],
        "node_ids": [tc.node_id for tc in tcs],
        "result_dir": str(result_dir),
    }
    (result_dir / "run_meta.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    env = os.environ.copy()
    env["BLAZEUP_RESULT_DIR"] = str(result_dir)
    env["BLAZEUP_LOG_LEVEL"] = "DEBUG" if debug_log else "INFO"
    pytest_args = build_pytest_args(tcs, result_dir, debug_log=debug_log)

    print(f"{_BLUE}{_bold('Starting BlazeUp Automation Run')}{_RESET}")
    print(f"Results: {result_dir}")
    print(f"Total:   {len(tcs)} test cases")
    for tc in tcs:
        print(f"   - TC {tc.tc_id}: {tc.title}")
    print("-" * 50)

    started = time.time()
    result = subprocess.run(pytest_args, env=env, cwd=base_dir)
    elapsed = time.time() - started

    junit_path = result_dir / "logs" / "junit.xml"
    summary_rows = parse_junit_xml(junit_path, tcs)
    print_summary(summary_rows)

    total = len(summary_rows)
    passed_ids = [r["tc_id"] for r in summary_rows if r["status"] == "PASSED"]
    failed_ids = [r["tc_id"] for r in summary_rows if r["status"] in ("FAILED", "ERROR")]
    skipped_ids = [r["tc_id"] for r in summary_rows if r["status"] == "SKIPPED"]

    print("\n" + "=" * 60)
    print(_bold("TEST EXECUTION RESULTS"))
    print(f"Total TCs Run: {_CYAN}{total}{_RESET}")
    if passed_ids:
        print(f"PASS {_GREEN}PASSED{_RESET} ({len(passed_ids)}): {', '.join(passed_ids)}")
    if failed_ids:
        print(f"FAIL {_RED}FAILED{_RESET} ({len(failed_ids)}): {', '.join(failed_ids)}")
    if skipped_ids:
        print(f"SKIP {_YELLOW}SKIPPED/BLOCKED{_RESET} ({len(skipped_ids)}): {', '.join(skipped_ids)}")

    print(f"\nDuration: {elapsed:.1f}s | Logs: {result_dir / 'logs' / 'test.log'}")
    print(f"Report: {result_dir / 'report.html'}")
    print(f"Allure: {result_dir / 'allure-results'}")
    print("=" * 60)

    if serve_allure:
        serve_returncode = serve_allure_report(result_dir / "allure-results", env, base_dir)
        if serve_returncode != 0:
            print("Allure serve failed. Please check the Allure CLI installation and try again.")

    return result.returncode


# ---------------------------------------------------------------------------
# Performance / stability runner
# ---------------------------------------------------------------------------

def _run_single_batch(
    batch_tcs: list[TestCase],
    base_dir: Path,
    debug_log: bool,
) -> tuple[Path, list[dict[str, str]]]:
    """Execute one pytest invocation for a batch and return (result_dir, rows)."""

    result_dir = make_result_dir(base_dir).resolve()
    env = os.environ.copy()
    env["BLAZEUP_RESULT_DIR"] = str(result_dir)
    env["BLAZEUP_LOG_LEVEL"] = "DEBUG" if debug_log else "INFO"

    pytest_args = build_pytest_args(batch_tcs, result_dir, debug_log=debug_log)
    # Suppress live output during performance runs; summary shown per-iteration
    subprocess.run(pytest_args, env=env, cwd=base_dir, capture_output=True)

    rows = parse_junit_xml(result_dir / "logs" / "junit.xml", batch_tcs)
    return result_dir, rows


def print_performance_summary(
    perf_results: dict[int, list[dict[str, str]]],
    tcs: list[TestCase],
    repeat: int,
    repeat_mode: str,
) -> None:
    """Print aggregated stability/performance table after all iterations."""

    print(f"\n{_bold('=== PERFORMANCE RUN SUMMARY ===')} "
          f"mode={repeat_mode}  iterations={repeat}")

    headers = [
        _bold("TC ID"), _bold("Title"), _bold("Pass"), _bold("Fail"),
        _bold("Pass Rate"), _bold("Avg Time"), _bold("Stability"),
    ]
    table_data = []

    for tc in tcs:
        runs = perf_results.get(tc.tc_id, [])
        if not runs:
            continue
        passes = sum(1 for r in runs if r["status"] == "PASSED")
        fails = sum(1 for r in runs if r["status"] in ("FAILED", "ERROR"))
        skips = sum(1 for r in runs if r["status"] == "SKIPPED")
        times = [float(r["time"]) for r in runs if r["time"] and r["status"] != "MISSING"]
        avg_time = f"{sum(times) / len(times):.2f}s" if times else "--"
        total = len(runs)
        pass_rate = passes / total * 100 if total else 0.0

        if fails == 0:
            stability = f"{_GREEN}✓ STABLE{_RESET}"
        elif passes == 0:
            stability = f"{_RED}✗ FAILING{_RESET}"
        else:
            stability = f"{_YELLOW}⚠ FLAKY{_RESET}"

        table_data.append([
            f"{_BLUE}{tc.tc_id}{_RESET}",
            tc.title[:45] + ("..." if len(tc.title) > 45 else ""),
            f"{_GREEN}{passes}{_RESET}",
            f"{_RED}{fails}{_RESET}" if fails else "0",
            f"{pass_rate:.0f}%",
            avg_time,
            stability,
        ])

    if tabulate is not None:
        print(tabulate(table_data, headers=headers, tablefmt="github"))
    else:
        for row in table_data:
            print("  |  ".join(str(c) for c in row))

    # Overall verdict
    all_runs = [r for runs in perf_results.values() for r in runs]
    total_pass = sum(1 for r in all_runs if r["status"] == "PASSED")
    total_fail = sum(1 for r in all_runs if r["status"] in ("FAILED", "ERROR"))
    flaky_tcs = [
        tc.tc_id for tc in tcs
        if perf_results.get(tc.tc_id)
        and any(r["status"] == "PASSED" for r in perf_results[tc.tc_id])
        and any(r["status"] in ("FAILED", "ERROR") for r in perf_results[tc.tc_id])
    ]

    print(f"\n  Total runs: {len(all_runs)} | "
          f"{_GREEN}Passed: {total_pass}{_RESET} | "
          f"{_RED}Failed: {total_fail}{_RESET}")
    if flaky_tcs:
        print(f"  {_YELLOW}Flaky TCs: {', '.join(str(i) for i in flaky_tcs)}{_RESET}")


def run_performance_plan(
    base_ids: list[int],
    repeat: int,
    repeat_mode: str,
    debug_log: bool = False,
    fail_fast_count: int = 0,
) -> int:
    """
    Run tests multiple times and produce a stability/performance report.

    repeat_mode='batch' -- run full list x N  ->  [1,2,3, 1,2,3, ...]
                          Good for: system stability, memory-leak detection.

    repeat_mode='each'  -- run each TC x N    ->  [1,1,1, 2,2,2, ...]
                          Good for: detecting flaky behaviour in one function.

    fail_fast_count     -- stop when this many total failures accumulate (0 = off).
    """
    base_dir = Path(__file__).resolve().parents[1]
    tcs = resolve_tcs(base_ids)
    if not tcs:
        print("No valid test cases selected.")
        return 1

    # Build batch list
    if repeat_mode == "each":
        batches: list[list[TestCase]] = []
        for tc in tcs:
            batches.extend([[tc]] * repeat)
    else:
        batches = [list(tcs)] * repeat

    total_batches = len(batches)
    perf_results: dict[int, list[dict[str, str]]] = {tc.tc_id: [] for tc in tcs}

    print(f"\n{_BLUE}{_bold('BlazeUp Performance Run')}{_RESET}")
    print(f"  Mode       : {repeat_mode}")
    print(f"  TCs        : {len(tcs)}")
    print(f"  Iterations : {repeat}")
    print(f"  Batches    : {total_batches}")
    if fail_fast_count:
        print(f"  Fail-fast  : stop after {fail_fast_count} failure(s)")
    print("-" * 60)

    total_failures = 0

    for idx, batch_tcs in enumerate(batches, start=1):
        # Progress label
        if repeat_mode == "each":
            tc = batch_tcs[0]
            run_num = (idx - 1) % repeat + 1
            label = f"TC {tc.tc_id}  run {run_num}/{repeat}"
        else:
            label = f"Iteration {idx}/{total_batches}"

        print(f"\n  [{label}]", end="  ", flush=True)

        _, rows = _run_single_batch(batch_tcs, base_dir, debug_log)

        # Print per-TC status on same line
        for row in rows:
            status_str = (
                f"{_GREEN}PASS{_RESET}" if row["status"] == "PASSED"
                else f"{_RED}FAIL{_RESET}" if row["status"] in ("FAILED", "ERROR")
                else f"{_YELLOW}SKIP{_RESET}"
            )
            print(f"TC{row['tc_id']}={status_str}({row['time']}s)", end="  ")
            perf_results[int(row["tc_id"])].append(row)
            if row["status"] in ("FAILED", "ERROR"):
                total_failures += 1

        print()  # newline after inline statuses

        # Fail-fast check
        if fail_fast_count and total_failures >= fail_fast_count:
            print(f"\n  {_YELLOW}Stopping: reached {total_failures} failure(s) "
                  f"(--fail-fast-count {fail_fast_count}){_RESET}")
            break

    print_performance_summary(perf_results, tcs, repeat, repeat_mode)

    any_failed = any(
        r["status"] in ("FAILED", "ERROR")
        for runs in perf_results.values()
        for r in runs
    )
    return 1 if any_failed else 0


# ---------------------------------------------------------------------------
# Direct invocation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]
    if not ids:
        # No IDs provided -- run every registered test case
        ids = sorted(TC_REGISTRY.keys())
    sys.exit(run_tc_ids(ids))
