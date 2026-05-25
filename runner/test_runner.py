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

from loguru import logger

try:
    from runner.tc_registry import TC_REGISTRY, TestCase, get_tc
except ModuleNotFoundError:
    from tc_registry import TC_REGISTRY, TestCase, get_tc

# ANSI color codes
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


def _bold(text: str) -> str:
    return f"{_BOLD}{text}{_RESET}"


# ---------------------------------------------------------------------------
# ANSI-aware table formatter
# ---------------------------------------------------------------------------

def _visible_len(s: str) -> int:
    """Return the number of *visible* characters (strips ANSI escape codes)."""
    return len(re.sub(r"\x1b\[[0-9;]*[mK]", "", s))


def _strip_ansi(s: str) -> str:
    """Return s with ANSI SGR codes AND OSC 8 hyperlinks removed (plain text).

    OSC 8 format:  ESC]8;;URL ESC\\ VISIBLE_TEXT ESC]8;; ESC\\
    The regex keeps VISIBLE_TEXT and discards the surrounding escape sequences.
    """
    # Remove ANSI SGR / erase codes  (e.g. \x1b[92m, \x1b[0m, \x1b[2K)
    s = re.sub(r"\x1b\[[0-9;]*[mK]", "", s)
    # Remove OSC 8 hyperlinks, preserving the visible link text
    s = re.sub(r"\x1b\]8;;[^\x1b]*\x1b\\(.*?)\x1b\]8;;\x1b\\", r"\1", s)
    return s


def _terminal_link(text: str, url: str) -> str:
    """Wrap *text* in an OSC 8 hyperlink escape sequence.

    Modern terminals (Windows Terminal, iTerm2, GNOME Terminal >=3.26) render
    this as a clickable hyperlink.  Terminals that don't understand OSC 8 show
    the raw text without escape sequences (safe fallback).
    """
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"


def _generate_allure_html(results_dir: Path, output_dir: Path) -> Path | None:
    """Generate a static Allure HTML report from *results_dir*.

    Runs ``allure generate <results_dir> -o <output_dir> --clean`` and
    returns the path to ``index.html`` on success.  Returns ``None`` when
    the results directory is empty or generation fails for any reason.

    Uses ``shell=True`` so Windows `.bat` / `.cmd` wrappers (the typical
    Allure install on Windows) are found without needing ``shutil.which()``.
    """
    if not results_dir.exists():
        return None
    try:
        if not any(results_dir.iterdir()):
            return None
    except OSError:
        return None
    try:
        subprocess.run(
            f'allure generate "{results_dir}" -o "{output_dir}" --clean',
            shell=True,
            capture_output=True,
            timeout=120,
        )
        index = output_dir / "index.html"
        return index if index.exists() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _launch_allure_browser(report_dir: Path) -> bool:
    """Open *report_dir* in the browser via ``allure open`` (detached process).

    ``allure open`` starts a lightweight HTTP server on a random local port
    and immediately opens the default browser at that address.  Running it
    detached means the test runner exits normally while the dashboard stays
    accessible in the background.

    Returns True when the subprocess was spawned successfully.
    """
    if not report_dir.exists():
        return False
    try:
        kw: dict = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if sys.platform == "win32":
            kw["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            kw["start_new_session"] = True
        subprocess.Popen(
            f'allure open "{report_dir}"',
            shell=True,
            **kw,
        )
        return True
    except OSError:
        return False


def _append_summary_to_log(lines: list[str], log_path: Path) -> None:
    """Append the ANSI-stripped summary block to an existing log file.

    The summary is wrapped in a dated header/footer so it's easy to locate
    at the bottom of the log with ``grep -A9999 'SUMMARY'``.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plain_lines = [_strip_ansi(ln) for ln in lines]
    try:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n# ===== TEST RUN SUMMARY  ({timestamp}) =====\n")
            fh.write("\n".join(plain_lines))
            fh.write("\n# ===== END OF SUMMARY =====\n")
    except OSError as exc:
        logger.warning("Could not write summary to {}: {}", log_path, exc)


def _fmt_table(rows: list[list], headers: list[str]) -> str:
    """Left-aligned pipe table that handles ANSI colour codes correctly.

    Standard ``tabulate`` counts escape sequences as visible characters,
    producing misaligned columns when cells contain colour codes.  This
    formatter strips codes only for *width measurement*, preserving colours
    in the rendered output.
    """
    str_rows = [[str(c) for c in row] for row in rows]
    ncols = len(headers)

    # Compute each column's required visible width
    widths = [_visible_len(h) for h in headers]
    for row in str_rows:
        for i in range(ncols):
            widths[i] = max(widths[i], _visible_len(row[i]) if i < len(row) else 0)

    def pad(cell: str, width: int) -> str:
        return cell + " " * (width - _visible_len(cell))

    divider = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt_row = lambda cells: "| " + " | ".join(pad(cells[i], widths[i]) for i in range(ncols)) + " |"  # noqa: E731

    lines = [divider, fmt_row(headers), divider]
    for row in str_rows:
        # Pad row to ncols in case of short rows
        padded = row + [""] * (ncols - len(row))
        lines.append(fmt_row(padded))
    lines.append(divider)
    return "\n".join(lines)


def make_result_dir(base_dir: Path = Path('.')) -> Path:
    """Create results/run_YYYYMMDD_HHMMSS with report artifact subfolders."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = base_dir / "results" / f"run_{timestamp}"
    for subfolder in ["logs", "videos", "screenshots", "traces", "allure-results"]:
        (base / subfolder).mkdir(parents=True, exist_ok=True)
    return base


def build_pytest_args(tcs: list[TestCase], result_dir: Path, debug_log: bool = False) -> list[str]:
    """Build pytest CLI arguments for the selected test cases.

    Logging strategy
    ----------------
    All terminal and file logging is handled exclusively by **loguru** (configured
    in pytest_support/fixtures.py::result_dir).  Pytest's built-in log-capture is
    kept only for failure tracebacks — NOT for live CLI display or duplicate file
    output.

    Removed intentionally:
      --log-cli-level   -> was causing '--- live log setup/call ---' banners and
                           duplicating httpx noise in the terminal.
      --log-file / --log-file-level -> was writing a second copy of logs into the
                           same test.log that loguru already owns, creating a
                           mixed-format file.
    """
    node_ids = [tc.node_id for tc in tcs]
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
        # Suppress noisy third-party loggers from pytest's internal capture
        # (these would appear in the '--- Captured log call ---' section on failure)
        "--log-disable=faker",
        "--log-disable=faker.factory",
        "--log-disable=asyncio",
        "--log-disable=httpx",
        "--log-disable=httpcore",
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


# ---------------------------------------------------------------------------
# Unified summary helpers
# ---------------------------------------------------------------------------

def _build_tc_summaries_from_rows(summary_rows: list[dict[str, str]]) -> list[dict]:
    """Convert single-run JUnit rows into the unified TC-summary dict format."""
    result: list[dict] = []
    for row in summary_rows:
        tc_id = int(row["tc_id"])
        tc = TC_REGISTRY.get(tc_id)
        status = row["status"]
        result.append({
            "tc_id":    tc_id,
            "priority": tc.priority if tc else "--",
            "type":     tc.type     if tc else "--",
            "module":   tc.module   if tc else "--",
            "title":    row["title"],
            "runs":     1,
            "passed":   1 if status == "PASSED" else 0,
            "failed":   1 if status in ("FAILED", "ERROR") else 0,
            "skipped":  1 if status == "SKIPPED" else 0,
            "avg_time": float(row["time"] or 0),
            "last_msg": row["message"],
        })
    return result


def _build_tc_summaries_from_perf(
    perf_results: dict[int, list[dict[str, str]]],
    tcs: list[TestCase],
) -> list[dict]:
    """Convert multi-run perf_results into the unified TC-summary dict format."""
    result: list[dict] = []
    for tc in tcs:
        runs = perf_results.get(tc.tc_id, [])
        if not runs:
            continue
        passed  = sum(1 for r in runs if r["status"] == "PASSED")
        failed  = sum(1 for r in runs if r["status"] in ("FAILED", "ERROR"))
        skipped = sum(1 for r in runs if r["status"] == "SKIPPED")
        times   = [float(r["time"]) for r in runs if r.get("time") and r["status"] != "MISSING"]
        avg_t   = sum(times) / len(times) if times else 0.0
        last_msg = next(
            (r["message"] for r in reversed(runs) if r["status"] in ("FAILED", "ERROR")),
            "",
        )
        result.append({
            "tc_id":    tc.tc_id,
            "priority": tc.priority,
            "type":     tc.type,
            "module":   tc.module,
            "title":    tc.title,
            "runs":     len(runs),
            "passed":   passed,
            "failed":   failed,
            "skipped":  skipped,
            "avg_time": avg_t,
            "last_msg": last_msg,
        })
    return result


def _render_single_run_table(summaries: list[dict]) -> str:
    """Table for a single run: Status | Time | Failure (first line)."""
    _STATUS = {
        "pass":    f"{_GREEN}PASS   {_RESET}",
        "fail":    f"{_RED}FAIL   {_RESET}",
        "skip":    f"{_YELLOW}SKIP   {_RESET}",
        "missing": f"{_DIM}MISSING{_RESET}",
    }

    headers = [
        _bold("TC"), _bold("P"), _bold("Type"),
        _bold("Title"),
        _bold("Status"), _bold("Time"), _bold("Failure (first line)"),
    ]
    rows = []
    for s in summaries:
        if s["passed"]:
            key = "pass"
        elif s["failed"]:
            key = "fail"
        elif s["skipped"]:
            key = "skip"
        else:
            key = "missing"

        title = s["title"]
        if len(title) > 42:
            title = title[:39] + "..."
        msg = s["last_msg"]
        if len(msg) > 45:
            msg = msg[:42] + "..."

        rows.append([
            f"{_BLUE}{s['tc_id']}{_RESET}",
            s["priority"],
            s["type"],
            title,
            _STATUS[key],
            f"{s['avg_time']:.2f}s",
            msg,
        ])
    return _fmt_table(rows, headers)


def _render_multi_run_table(summaries: list[dict]) -> str:
    """Table for multi-run: Runs | Pass | Fail | Rate | Avg Time | Stability."""
    headers = [
        _bold("TC"), _bold("P"), _bold("Type"),
        _bold("Title"),
        _bold("Runs"), _bold("Pass"), _bold("Fail"),
        _bold("Rate"), _bold("Avg"), _bold("Stability"),
    ]
    rows = []
    for s in summaries:
        runs   = s["runs"]
        passed = s["passed"]
        failed = s["failed"]
        rate   = f"{passed / runs * 100:.0f}%" if runs else "--"

        if failed == 0:
            stability = f"{_GREEN}STABLE {_RESET}"
        elif passed == 0:
            stability = f"{_RED}FAILING{_RESET}"
        else:
            stability = f"{_YELLOW}FLAKY  {_RESET}"

        title = s["title"]
        if len(title) > 42:
            title = title[:39] + "..."

        rows.append([
            f"{_BLUE}{s['tc_id']}{_RESET}",
            s["priority"],
            s["type"],
            title,
            str(runs),
            f"{_GREEN}{passed}{_RESET}",
            f"{_RED}{failed}{_RESET}" if failed else "0",
            rate,
            f"{s['avg_time']:.2f}s" if s["avg_time"] else "--",
            stability,
        ])
    return _fmt_table(rows, headers)


def print_run_summary(
    tc_summaries: list[dict],
    *,
    mode: str = "normal",
    repeat: int = 1,
    repeat_mode: str = "batch",
    duration_s: float = 0.0,
    result_dir: Path | None = None,
    allure_html: Path | None = None,
    allure_launched: bool = False,
) -> None:
    """Unified test-run summary for all execution modes.

    Single run  (repeat=1)  ->  Status | Time | Failure columns.
    Multi-run   (repeat>1)  ->  Runs | Pass | Fail | Rate | Avg | Stability.

    Output strategy
    ---------------
    All lines are first collected into a list so they can be:
    1. Printed to the terminal with ANSI colour codes and OSC 8 hyperlinks.
    2. Written to ``result_dir/logs/test.log`` with codes stripped (plain text).

    When *allure_launched* is True, the Allure row shows "Dashboard opened in
    browser automatically" — no clicking needed, the browser is already open.
    When *allure_html* exists but wasn't launched, shows a clickable path link.
    """
    W = 66  # separator width
    total_tcs     = len(tc_summaries)
    total_runs    = sum(s["runs"]    for s in tc_summaries)
    total_passed  = sum(s["passed"]  for s in tc_summaries)
    total_failed  = sum(s["failed"]  for s in tc_summaries)
    total_skipped = sum(s["skipped"] for s in tc_summaries)
    is_multi      = repeat > 1

    out: list[str] = []  # collects every line before printing

    # ── Header ────────────────────────────────────────────────────────────────
    out.append(f"\n{_BOLD}{_BLUE}{'=' * W}{_RESET}")
    out.append(f"{_BOLD}  BlazeUp HRMS  --  Test Run Summary{_RESET}")
    out.append(f"  Mode        : {_CYAN}{mode}{_RESET}")
    if is_multi:
        out.append(f"  Repeat      : {repeat}x  ({repeat_mode})")
        out.append(f"  Total TCs   : {total_tcs}   Total runs : {total_runs}")
    else:
        out.append(f"  Total TCs   : {total_tcs}")
    out.append(f"  Duration    : {duration_s:.1f}s")
    out.append(f"{_BOLD}{_BLUE}{'=' * W}{_RESET}")
    out.append("")

    # ── Table ─────────────────────────────────────────────────────────────────
    if is_multi:
        out.append(_render_multi_run_table(tc_summaries))
    else:
        out.append(_render_single_run_table(tc_summaries))

    # ── Footer ────────────────────────────────────────────────────────────────
    out.append("")
    if is_multi:
        flaky_ids   = [str(s["tc_id"]) for s in tc_summaries if s["passed"] > 0 and s["failed"] > 0]
        failing_ids = [str(s["tc_id"]) for s in tc_summaries if s["passed"] == 0 and s["failed"] > 0]
        out.append(
            f"  Total runs  : {total_runs}   "
            f"{_GREEN}Pass: {total_passed}{_RESET}   "
            f"{_RED}Fail: {total_failed}{_RESET}   "
            f"{_YELLOW}Skip: {total_skipped}{_RESET}"
        )
        if flaky_ids:
            out.append(f"  {_YELLOW}Flaky  : TC {', '.join(flaky_ids)}{_RESET}")
        if failing_ids:
            out.append(f"  {_RED}Failing: TC {', '.join(failing_ids)}{_RESET}")
    else:
        fail_ids = [str(s["tc_id"]) for s in tc_summaries if s["failed"]  > 0]
        skip_ids = [str(s["tc_id"]) for s in tc_summaries if s["skipped"] > 0]
        out.append(
            f"  Total : {total_tcs}   "
            f"{_GREEN}PASS: {total_passed}{_RESET}   "
            f"{_RED}FAIL: {total_failed}{_RESET}   "
            f"{_YELLOW}SKIP: {total_skipped}{_RESET}"
        )
        if fail_ids:
            out.append(f"  {_RED}Failed : TC {', '.join(fail_ids)}{_RESET}")
        if skip_ids:
            out.append(f"  {_YELLOW}Skipped: TC {', '.join(skip_ids)}{_RESET}")

    if result_dir is not None:
        log_path    = result_dir / "logs" / "test.log"
        report_path = result_dir / "report.html"
        out.append(f"\n  Logs   : {_terminal_link(str(log_path),    log_path.as_uri())}")
        out.append(f"  Report : {_terminal_link(str(report_path), report_path.as_uri())}")

        if allure_launched:
            # Dashboard auto-opened — no action needed from the user
            out.append(
                f"  Allure : {_GREEN}Dashboard opened in browser automatically{_RESET}"
            )
        elif allure_html is not None:
            # Generated but not launched (e.g. --serve not requested)
            allure_url = allure_html.as_uri()
            out.append(
                f"  Allure : {_terminal_link(str(allure_html.parent), allure_url)}"
                f"  {_DIM}(Ctrl+Click or run: allure open \"{allure_html.parent}\"){_RESET}"
            )
        else:
            # Allure CLI not available / results empty
            allure_results = result_dir / "allure-results"
            out.append(
                f"  Allure : {allure_results}"
                f"  {_DIM}(run: allure serve \"{allure_results}\"){_RESET}"
            )

    out.append(f"{_BOLD}{_BLUE}{'=' * W}{_RESET}")

    # ── Emit ──────────────────────────────────────────────────────────────────
    # 1. Terminal: print with colours
    for line in out:
        print(line)

    # 2. Log file: append plain-text (ANSI-stripped) copy
    if result_dir is not None:
        _append_summary_to_log(out, result_dir / "logs" / "test.log")


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


def run_tc_ids(
    tc_ids: list[int],
    mode: str = "normal",
    debug_log: bool = False,
    serve_allure: bool = False,
) -> int:
    """Run the given test case IDs and return the pytest return code."""

    base_dir = Path(__file__).resolve().parents[1]
    tcs = resolve_tcs(tc_ids)
    if not tcs:
        print("No valid test cases selected. Use numeric TC IDs only.")
        return 1

    result_dir = make_result_dir(base_dir).resolve()
    metadata = {
        "run_at":   datetime.now().isoformat(),
        "mode":     mode,
        "tc_ids":   [tc.tc_id for tc in tcs],
        "node_ids": [tc.node_id for tc in tcs],
        "result_dir": str(result_dir),
    }
    (result_dir / "run_meta.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    env = os.environ.copy()
    env["BLAZEUP_RESULT_DIR"] = str(result_dir)
    env["BLAZEUP_LOG_LEVEL"] = "DEBUG" if debug_log else "INFO"
    pytest_args = build_pytest_args(tcs, result_dir, debug_log=debug_log)

    print(f"\n{_BLUE}{_bold('BlazeUp Automation Run')}{_RESET}")
    print(f"  Mode    : {_CYAN}{mode}{_RESET}")
    print(f"  Results : {result_dir}")
    print(f"  TCs     : {len(tcs)}")
    for tc in tcs:
        print(f"            TC {tc.tc_id:>5}  [{tc.priority}]  {tc.title}")
    print("-" * 56)

    started = time.time()
    result  = subprocess.run(pytest_args, env=env, cwd=base_dir)
    elapsed = time.time() - started

    summary_rows = parse_junit_xml(result_dir / "logs" / "junit.xml", tcs)
    tc_summaries = _build_tc_summaries_from_rows(summary_rows)

    # Generate static Allure HTML then auto-open it in the browser.
    # shell=True makes this work on Windows where allure is a .bat/.cmd file.
    allure_html = _generate_allure_html(
        result_dir / "allure-results",
        result_dir / "allure-report",
    )

    # Launch the dashboard in the default browser (detached — runner exits normally).
    allure_launched = False
    if allure_html is not None:
        allure_launched = _launch_allure_browser(allure_html.parent)

    print_run_summary(
        tc_summaries,
        mode=mode,
        repeat=1,
        repeat_mode="batch",
        duration_s=elapsed,
        result_dir=result_dir,
        allure_html=allure_html,
        allure_launched=allure_launched,
    )

    if serve_allure:
        rc = serve_allure_report(result_dir / "allure-results", env, base_dir)
        if rc != 0:
            print("Allure serve failed. Check the Allure CLI installation and retry.")

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




def run_performance_plan(
    base_ids: list[int],
    repeat: int,
    repeat_mode: str,
    mode: str = "normal",
    debug_log: bool = False,
    fail_fast_count: int = 0,
) -> int:
    """Run tests multiple times and produce a stability/performance report.

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
    print(f"  Mode       : {_CYAN}{mode}{_RESET}")
    print(f"  Repeat     : {repeat}x  ({repeat_mode})")
    print(f"  TCs        : {len(tcs)}   Batches : {total_batches}")
    if fail_fast_count:
        print(f"  Fail-fast  : stop after {fail_fast_count} failure(s)")
    print("-" * 60)

    total_failures = 0
    wall_start = time.time()

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

        # Print per-TC inline status
        for row in rows:
            if row["status"] == "PASSED":
                tag = f"{_GREEN}PASS{_RESET}"
            elif row["status"] in ("FAILED", "ERROR"):
                tag = f"{_RED}FAIL{_RESET}"
            else:
                tag = f"{_YELLOW}SKIP{_RESET}"
            print(f"TC{row['tc_id']}={tag}({row['time']}s)", end="  ")
            perf_results[int(row["tc_id"])].append(row)
            if row["status"] in ("FAILED", "ERROR"):
                total_failures += 1

        print()  # newline after inline statuses

        if fail_fast_count and total_failures >= fail_fast_count:
            print(f"\n  {_YELLOW}Stopping: reached {total_failures} failure(s) "
                  f"(--fail-fast-count {fail_fast_count}){_RESET}")
            break

    elapsed = time.time() - wall_start
    tc_summaries = _build_tc_summaries_from_perf(perf_results, tcs)

    print_run_summary(
        tc_summaries,
        mode=mode,
        repeat=repeat,
        repeat_mode=repeat_mode,
        duration_s=elapsed,
    )

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
