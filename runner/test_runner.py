#!/usr/bin/env python3
"""Core BlazeUp test execution helper."""

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
    from tc_registry import TC_REGISTRY, TestCase, get_tc  # type: ignore[no-redef]

# Ensure project root is on sys.path so utils.* is importable regardless of
# how this file is invoked (python -m runner.run_test  vs  python runner/run_test.py)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from utils.excel_reporter import write_excel_report  # noqa: E402

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
            kw["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
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


def make_result_dir(base_dir: Path = Path(".")) -> Path:
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


# A test whose failure/skip message matches one of these is an ENVIRONMENT /
# precondition problem (shared login down, service 5xx, connection error) — it is
# reported as BLOCKED, not FAILED, so a down staging env never looks like a defect.
_BLOCKED_SIGNATURES = (
    "blocked:",  # explicit precondition skip from a fixture (shared login down)
    # Gateway/infra 5xx = service unavailable → env block. NOTE: 500 is deliberately
    # NOT here — a bare 500 is usually an APP BUG (service up, crashed on the request),
    # which must stay FAILED. Shared-login failures already carry the "blocked:" tag.
    "got 502",
    "got 503",
    "got 504",
    "bad gateway",
    "service unavailable",
    "gateway timeout",
    # Network unreachable / timeout → env block.
    "connecterror",
    "connecttimeout",
    "readtimeout",
    "connection refused",
    "max retries",
    "getaddrinfo",
)


def _is_blocked(message: str) -> bool:
    """True when a failure/skip message indicates an env/precondition block."""
    low = (message or "").lower()
    return any(sig in low for sig in _BLOCKED_SIGNATURES)


# Exit code for a run that had no real failures but was BLOCKED by the environment
# (login down, service 5xx). Distinct + non-zero so CI never reads a broken env as
# a clean pass, and distinct from pytest's own 1 (failures) / 5 (nothing collected).
_EXIT_BLOCKED = 3


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

        # Precondition/env failures (login down, 5xx, connection) → BLOCKED, not FAILED.
        if status in ("FAILED", "ERROR", "SKIPPED") and _is_blocked(message):
            status = "BLOCKED"

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
        result.append(
            {
                "tc_id": tc_id,
                "priority": tc.priority if tc else "--",
                "type": tc.type if tc else "--",
                "module": tc.module if tc else "--",
                "title": row["title"],
                "runs": 1,
                "passed": 1 if status == "PASSED" else 0,
                "failed": 1 if status in ("FAILED", "ERROR") else 0,
                "blocked": 1 if status == "BLOCKED" else 0,
                "skipped": 1 if status == "SKIPPED" else 0,
                "avg_time": float(row["time"] or 0),
                "last_msg": row["message"],
            }
        )
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
        passed = sum(1 for r in runs if r["status"] == "PASSED")
        failed = sum(1 for r in runs if r["status"] in ("FAILED", "ERROR"))
        blocked = sum(1 for r in runs if r["status"] == "BLOCKED")
        skipped = sum(1 for r in runs if r["status"] == "SKIPPED")
        times = [float(r["time"]) for r in runs if r.get("time") and r["status"] != "MISSING"]
        avg_t = sum(times) / len(times) if times else 0.0
        last_msg = next(
            (r["message"] for r in reversed(runs) if r["status"] in ("FAILED", "ERROR", "BLOCKED")),
            "",
        )
        result.append(
            {
                "tc_id": tc.tc_id,
                "priority": tc.priority,
                "type": tc.type,
                "module": tc.module,
                "title": tc.title,
                "runs": len(runs),
                "passed": passed,
                "failed": failed,
                "blocked": blocked,
                "skipped": skipped,
                "avg_time": avg_t,
                "last_msg": last_msg,
            }
        )
    return result


def _render_single_run_table(summaries: list[dict]) -> str:
    """Table for a single run: Status | Time | Failure (first line)."""
    _STATUS = {
        "pass": f"{_GREEN}PASS   {_RESET}",
        "fail": f"{_RED}FAIL   {_RESET}",
        "block": f"\033[95mBLOCK  {_RESET}",
        "skip": f"{_YELLOW}SKIP   {_RESET}",
        "missing": f"{_DIM}MISSING{_RESET}",
    }

    headers = [
        _bold("TC"),
        _bold("P"),
        _bold("Type"),
        _bold("Title"),
        _bold("Status"),
        _bold("Time"),
        _bold("Failure (first line)"),
    ]
    rows = []
    for s in summaries:
        if s["passed"]:
            key = "pass"
        elif s["failed"]:
            key = "fail"
        elif s.get("blocked"):
            key = "block"
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

        rows.append(
            [
                f"{_BLUE}{s['tc_id']}{_RESET}",
                s["priority"],
                s["type"],
                title,
                _STATUS[key],
                f"{s['avg_time']:.2f}s",
                msg,
            ]
        )
    return _fmt_table(rows, headers)


def _render_multi_run_table(summaries: list[dict]) -> str:
    """Table for multi-run: Runs | Pass | Fail | Rate | Avg Time | Stability."""
    headers = [
        _bold("TC"),
        _bold("P"),
        _bold("Type"),
        _bold("Title"),
        _bold("Runs"),
        _bold("Pass"),
        _bold("Fail"),
        _bold("Rate"),
        _bold("Avg"),
        _bold("Stability"),
    ]
    rows = []
    for s in summaries:
        runs = s["runs"]
        passed = s["passed"]
        failed = s["failed"]
        rate = f"{passed / runs * 100:.0f}%" if runs else "--"

        if passed == 0 and failed == 0 and s.get("blocked"):
            stability = "\033[95mBLOCKED\033[0m"
        elif failed == 0:
            stability = f"{_GREEN}STABLE {_RESET}"
        elif passed == 0:
            stability = f"{_RED}FAILING{_RESET}"
        else:
            stability = f"{_YELLOW}FLAKY  {_RESET}"

        title = s["title"]
        if len(title) > 42:
            title = title[:39] + "..."

        rows.append(
            [
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
            ]
        )
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
    excel_report_path: "Path | None" = None,
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
    total_tcs = len(tc_summaries)
    total_runs = sum(s["runs"] for s in tc_summaries)
    total_passed = sum(s["passed"] for s in tc_summaries)
    total_failed = sum(s["failed"] for s in tc_summaries)
    total_blocked = sum(s.get("blocked", 0) for s in tc_summaries)
    total_skipped = sum(s["skipped"] for s in tc_summaries)
    is_multi = repeat > 1

    out: list[str] = []  # collects every line before printing

    # ── Header ────────────────────────────────────────────────────────────────
    out.append(f"\n{_BOLD}{_BLUE}{'=' * W}{_RESET}")
    out.append(f"{_BOLD}  BlazeUp  --  Test Run Summary{_RESET}")
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
        flaky_ids = [str(s["tc_id"]) for s in tc_summaries if s["passed"] > 0 and s["failed"] > 0]
        failing_ids = [
            str(s["tc_id"]) for s in tc_summaries if s["passed"] == 0 and s["failed"] > 0
        ]
        out.append(
            f"  Total runs  : {total_runs}   "
            f"{_GREEN}Pass: {total_passed}{_RESET}   "
            f"{_RED}Fail: {total_failed}{_RESET}   "
            f"\033[95mBlock: {total_blocked}\033[0m   "
            f"{_YELLOW}Skip: {total_skipped}{_RESET}"
        )
        if flaky_ids:
            out.append(f"  {_YELLOW}Flaky  : TC {', '.join(flaky_ids)}{_RESET}")
        if failing_ids:
            out.append(f"  {_RED}Failing: TC {', '.join(failing_ids)}{_RESET}")
    else:
        fail_ids = [str(s["tc_id"]) for s in tc_summaries if s["failed"] > 0]
        blocked_ids = [str(s["tc_id"]) for s in tc_summaries if s.get("blocked", 0) > 0]
        skip_ids = [str(s["tc_id"]) for s in tc_summaries if s["skipped"] > 0]
        out.append(
            f"  Total : {total_tcs}   "
            f"{_GREEN}PASS: {total_passed}{_RESET}   "
            f"{_RED}FAIL: {total_failed}{_RESET}   "
            f"\033[95mBLOCK: {total_blocked}\033[0m   "
            f"{_YELLOW}SKIP: {total_skipped}{_RESET}"
        )
        if fail_ids:
            out.append(f"  {_RED}Failed : TC {', '.join(fail_ids)}{_RESET}")
        if blocked_ids:
            out.append(f"  \033[95mBlocked: TC {', '.join(blocked_ids)}\033[0m")
        if skip_ids:
            out.append(f"  {_YELLOW}Skipped: TC {', '.join(skip_ids)}{_RESET}")

    if result_dir is not None:
        log_path = result_dir / "logs" / "test.log"
        out.append(f"\n  Logs   : {_terminal_link(str(log_path), log_path.as_uri())}")

        if allure_html is not None:
            # Report generated — show the open command to copy-paste or click
            report_dir = allure_html.parent
            out.append(f"  Allure : {report_dir}")
            out.append(f'           {_DIM}run: allure open "{report_dir}"{_RESET}')
        else:
            # Allure CLI not available / results empty
            allure_results = result_dir / "allure-results"
            out.append(f"  Allure : {allure_results}")
            out.append(f'           {_DIM}run: allure serve "{allure_results}"{_RESET}')

        if excel_report_path is not None:
            out.append(
                f"  Excel  : {_terminal_link(str(excel_report_path), excel_report_path.as_uri())}"
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
    excel_report: bool = False,
    excel_path: "Path | None" = None,
    ai_triage: bool = False,
) -> int:
    """Run the given test case IDs and return the pytest return code.

    excel_path:  Test-plan workbook used when ``excel_report`` is True.
                 When None, it is auto-resolved per domain from the
                 BLAZEUP_DOMAIN env var: docs/{domain}/Partner_Platform_Test_Plan.xlsx.
    ai_triage:   When True and the run had failures, run AI triage on the log and
                 write ``ai_triage.md`` into the result dir. Provider/model come
                 from settings (AI_PROVIDER / AI_MODEL in .env or the environment).
    """

    base_dir = Path(__file__).resolve().parents[1]
    tcs = resolve_tcs(tc_ids)
    if not tcs:
        print("No valid test cases selected. Use numeric TC IDs only.")
        return 1

    result_dir = make_result_dir(base_dir).resolve()
    metadata = {
        "run_at": datetime.now().isoformat(),
        "mode": mode,
        "tc_ids": [tc.tc_id for tc in tcs],
        "node_ids": [tc.node_id for tc in tcs],
        "result_dir": str(result_dir),
    }
    (result_dir / "run_meta.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
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
    result = subprocess.run(pytest_args, env=env, cwd=base_dir)
    elapsed = time.time() - started

    summary_rows = parse_junit_xml(result_dir / "logs" / "junit.xml", tcs)
    tc_summaries = _build_tc_summaries_from_rows(summary_rows)
    total_blocked = sum(s.get("blocked", 0) for s in tc_summaries)

    # Generate static Allure HTML report (link shown in summary — Ctrl+Click to open).
    # shell=True makes this work on Windows where allure is a .bat/.cmd file.
    allure_html = _generate_allure_html(
        result_dir / "allure-results",
        result_dir / "allure-report",
    )

    # Optionally write results back to a copy of the test-plan Excel workbook.
    # Path precedence: explicit excel_path arg > BLAZEUP_DOMAIN auto-resolve.
    excel_report_path = None
    if excel_report:
        if excel_path is None:
            domain = os.environ.get("BLAZEUP_DOMAIN", "blazeup_admin")
            excel_path = base_dir / "docs" / domain / "Partner_Platform_Test_Plan.xlsx"
        excel_report_path = write_excel_report(tc_summaries, result_dir, excel_path)

    print_run_summary(
        tc_summaries,
        mode=mode,
        repeat=1,
        repeat_mode="batch",
        duration_s=elapsed,
        result_dir=result_dir,
        allure_html=allure_html,
        excel_report_path=excel_report_path,
    )

    # Optionally run AI triage when the run had failures. ai_triage itself is a
    # no-op if it finds no failures in the log, so this is safe to call broadly.
    # Wrapped so a triage/AI error never changes the test return code.
    if ai_triage and result.returncode not in (0, 5):
        print(f"\n{_BLUE}Running AI failure triage…{_RESET}")
        try:
            from utils.ai_triage import main as _triage_main

            _triage_main([str(result_dir)])
        except SystemExit as exc:  # bad-JSON path raises SystemExit
            print(f"AI triage could not complete: {exc}")
        except Exception as exc:  # noqa: BLE001 — never break the run
            print(f"AI triage failed (non-blocking): {exc}")

    if serve_allure:
        rc = serve_allure_report(result_dir / "allure-results", env, base_dir)
        if rc != 0:
            print("Allure serve failed. Check the Allure CLI installation and retry.")

    # A run with no real failures but BLOCKED TCs must not look like a clean pass.
    if result.returncode == 0 and total_blocked > 0:
        return _EXIT_BLOCKED
    return result.returncode


# ---------------------------------------------------------------------------
# Performance / stability runner
# ---------------------------------------------------------------------------


def _run_single_batch(
    batch_tcs: list[TestCase],
    base_dir: Path,
    debug_log: bool,
) -> tuple[Path, list[dict[str, str]]]:
    """Execute one pytest invocation for a batch and return (result_dir, rows).

    Output strategy during performance/repeat runs
    -----------------------------------------------
    Live pytest output is suppressed so the terminal stays clean (only the
    per-iteration status line TC5=PASS(0.32s) is printed).

    The captured stdout + stderr are written to
    ``result_dir/logs/pytest_output.txt`` so the full traceback and fixture
    errors are available for debugging when a batch fails — without having
    to rerun in non-repeat mode.
    """
    result_dir = make_result_dir(base_dir).resolve()
    env = os.environ.copy()
    env["BLAZEUP_RESULT_DIR"] = str(result_dir)
    env["BLAZEUP_LOG_LEVEL"] = "DEBUG" if debug_log else "INFO"

    pytest_args = build_pytest_args(batch_tcs, result_dir, debug_log=debug_log)

    # capture_output=True keeps the terminal clean during multi-iteration runs.
    proc = subprocess.run(pytest_args, env=env, cwd=base_dir, capture_output=True)

    # Persist the full pytest output so failures are debuggable after the run.
    # The file sits next to test.log; open it when a batch shows ERROR/FAIL.
    batch_log = result_dir / "logs" / "pytest_output.txt"
    try:
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
        batch_log.write_text(stdout + stderr, encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not write batch log to {}: {}", batch_log, exc)

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
            elif row["status"] == "BLOCKED":
                tag = "\033[95mBLOCK\033[0m"
            else:
                tag = f"{_YELLOW}SKIP{_RESET}"
            print(f"TC{row['tc_id']}={tag}({row['time']}s)", end="  ")
            perf_results[int(row["tc_id"])].append(row)
            # BLOCKED is an env/precondition state, not a test failure → does not
            # count toward total_failures (so it never trips --fail-fast-count).
            if row["status"] in ("FAILED", "ERROR"):
                total_failures += 1

        print()  # newline after inline statuses

        if fail_fast_count and total_failures >= fail_fast_count:
            print(
                f"\n  {_YELLOW}Stopping: reached {total_failures} failure(s) "
                f"(--fail-fast-count {fail_fast_count}){_RESET}"
            )
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
        r["status"] in ("FAILED", "ERROR") for runs in perf_results.values() for r in runs
    )
    any_blocked = any(r["status"] == "BLOCKED" for runs in perf_results.values() for r in runs)
    # Real failures win (exit 1). Otherwise a run that was BLOCKED by the env must
    # not look like a clean pass → exit _EXIT_BLOCKED, never 0.
    if any_failed:
        return 1
    if any_blocked:
        return _EXIT_BLOCKED
    return 0


# ---------------------------------------------------------------------------
# Direct invocation
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    def _parse_cli_ids(tokens: list[str]) -> list[int]:
        """Parse individual IDs and range notation (e.g. '10101-10109')."""
        out: list[int] = []
        for token in tokens:
            if "-" in token:
                try:
                    s, e = token.split("-", 1)
                    out.extend(range(int(s), int(e) + 1))
                except ValueError:
                    logger.warning("Invalid range token '{}' — skipped", token)
            else:
                try:
                    out.append(int(token))
                except ValueError:
                    logger.warning("Invalid TC ID '{}' — skipped", token)
        # Drop IDs that don't exist in the registry
        return [tc_id for tc_id in out if tc_id in TC_REGISTRY]

    raw_args = sys.argv[1:]

    if raw_args:
        ids = _parse_cli_ids(raw_args)
    else:
        # No CLI args — fall back to DEFAULT_EXECUTE_IDS defined in run_test.py.
        # Import lazily to avoid a circular-import issue at module level
        # (run_test.py imports run_tc_ids from this file).
        try:
            try:
                from runner.run_test import DEFAULT_EXECUTE_IDS as _defaults
            except ImportError:
                from run_test import DEFAULT_EXECUTE_IDS as _defaults  # type: ignore[no-redef]
            ids = _parse_cli_ids(_defaults) if _defaults else sorted(TC_REGISTRY.keys())
        except Exception:
            ids = sorted(TC_REGISTRY.keys())

    sys.exit(run_tc_ids(ids))
