#!/usr/bin/env python3
"""Core BlazeUp HRMS test execution helper."""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Sequence

from loguru import logger

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None  # type: ignore[assignment]

try:
    from runner.tc_registry import TC_REGISTRY, TestCase, get_tc
except ModuleNotFoundError:
    from tc_registry import TC_REGISTRY, TestCase, get_tc


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
    args = [
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
    return args


def resolve_tcs(tc_ids: list[int]) -> list[TestCase]:
    """Resolve requested test cases from numeric IDs."""

    if not TC_REGISTRY:
        logger.error("Test Registry is empty. Please run 'python utils/sync_registry.py' first!")
        return []

    selected: list[TestCase] = []
    for tc_id in tc_ids:
        try:
            selected.append(get_tc(tc_id))
        except KeyError as exc:
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
                message = ""

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

    # ANSI escape codes for colors
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    status_colors = {
        "PASSED": f"{GREEN}PASSED{RESET}",
        "FAILED": f"{RED}FAILED{RESET}",
        "ERROR": f"{RED}ERROR{RESET}",
        "SKIPPED": f"{YELLOW}SKIPPED{RESET}",
    }

    headers = [f"{BOLD}TC ID{RESET}", f"{BOLD}Status{RESET}", f"{BOLD}Time{RESET}", f"{BOLD}Title{RESET}", f"{BOLD}Message{RESET}"]
    table_data = []
    for r in summary_rows:
        status = status_colors.get(r["status"], r["status"])
        table_data.append([f"{BLUE}{r['tc_id']}{RESET}", status, f"{r['time']}s", r["title"], r["message"]])

    print(f"\n{BOLD}=== TEST EXECUTION SUMMARY ==={RESET}")
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

    result_dir = make_result_dir(base_dir)
    result_dir = result_dir.resolve()
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

    print(f"\033[94m{bold('Starting BlazeUp Automation Run')}\033[0m")
    print(f"Results: {result_dir}")
    print(f"Total:   {len(tcs)} test cases")
    for tc in tcs:
        print(f"   - TC {tc.tc_id}: {tc.title}")
    print("-" * 50)

    started = time.time()
    # Run without capture_output to stream logs to terminal in real-time
    result = subprocess.run(pytest_args, env=env, cwd=base_dir)
    elapsed = time.time() - started

    junit_path = result_dir / "logs" / "junit.xml"
    summary_rows = parse_junit_xml(junit_path, tcs)
    print_summary(summary_rows)

    # Calculate detailed metrics
    total = len(summary_rows)
    passed_ids = [r["tc_id"] for r in summary_rows if r["status"] == "PASSED"]
    failed_ids = [r["tc_id"] for r in summary_rows if r["status"] in ("FAILED", "ERROR")]
    skipped_ids = [r["tc_id"] for r in summary_rows if r["status"] == "SKIPPED"]

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print("\n" + "=" * 60)
    print(f"{BOLD}TEST EXECUTION RESULTS{RESET}")
    print(f"Total TCs Run: {CYAN}{total}{RESET}")

    if passed_ids:
        print(f"PASS {GREEN}PASSED{RESET} ({len(passed_ids)}): {', '.join(passed_ids)}")
    if failed_ids:
        print(f"FAIL {RED}FAILED{RESET} ({len(failed_ids)}): {', '.join(failed_ids)}")
    if skipped_ids:
        print(f"SKIP {YELLOW}SKIPPED/BLOCKED{RESET} ({len(skipped_ids)}): {', '.join(skipped_ids)}")

    print(f"\nDuration: {elapsed:.1f}s | Logs: {result_dir / 'logs' / 'test.log'}")
    print(f"Report: {result_dir / 'report.html'}")
    print(f"Allure: {result_dir / 'allure-results'}")
    print("=" * 60)

    if serve_allure:
        serve_returncode = serve_allure_report(result_dir / "allure-results", env, base_dir)
        if serve_returncode != 0:
            print("Allure serve failed. Please check the Allure CLI installation and try again.")

    return result.returncode


def bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


if __name__ == "__main__":
    ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]
    if not ids:
        print("Usage: python -m runner.test_runner <tc_id> [<tc_id> ...]")
        sys.exit(1)
    sys.exit(run_tc_ids(ids))
