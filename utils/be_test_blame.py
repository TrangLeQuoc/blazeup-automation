"""Why is this backend unit test red — who changed what, and did they update the test?

A jest failure says WHAT differs. It never says who introduced the difference, when, or
whether the same commit updated the other tests but missed this one. That answer is four
git commands away, and it changes what you report:

    "the auth test is broken"
    "commit 9188b27 (2026-07-27, Khoa Nguyen) added forgot-password to app.module.ts and
     updated 4 spec files but not app.module.spec.ts, which pins the whole route list with
     toEqual. Red for 16 days and merged anyway. The CODE is right — fix the test."

The chain, all read-only::

    jest --json                          the failing spec, the test name, the diff
      -> a string on ONE side of the diff only
      -> git log -S "<string>" -- src    which commit put it in the code
      -> git show --stat <commit>        did that commit touch the failing spec?
      -> git log -S "<string>" -- <spec> has the spec EVER known about it?

Usage::

    python -m utils.be_test_blame --json results.json   # analyse a saved run
    python -m utils.be_test_blame --run                 # run jest first (~2 min)
    python -m utils.be_test_blame --run modules/app     # run one spec, then analyse

``--json`` is the default mode on purpose: it keeps this tool read-only over the backend
clone. ``--run`` executes their test suite — it writes nothing to their repo, but it is no
longer just reading.

Limits, stated because a wrong blame is worse than none: this works when the diff contains
a distinctive STRING. Numeric-only failures (``expect(count).toBe(3)``), timeouts and
environment problems give it nothing to search for. In those cases it prints the four
commands rather than guessing.
"""

import argparse
import contextlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from utils.be_coverage import (
    TOOL_LOG_DIR,
    be_branch,
    be_head,
    be_repo,
    logged_run,
    rel,
    staleness_warning,
)


def stale_dependencies(repo: Path) -> list[tuple[str, str, str]]:
    """Packages pinned in ``package.json`` whose installed version differs.

    Returns ``(name, wanted, installed)``; *installed* is ``"(not installed)"`` when the
    package is absent. Empty list means nothing to report.

    Why this exists, measured 2026-09-16: a run reported **15 failed suites**, 14 of them
    "failed to run" on two TypeScript errors — ``BILLING_PLAN_EDITION.CUSTOM`` missing and
    ``BillingPlan.connectors`` renamed. It read as the backend being broken. It was not:
    ``package.json`` asked for ``@blazeupai/blazeup-global-common`` 1.0.275 while
    ``node_modules`` held 1.0.194, installed five weeks earlier. After ``npm install`` the
    same commit ran 1073 tests with a single real failure. Reporting that to the backend team
    as "your code does not compile" would have been wrong twice over.

    ``git pull`` moves the source but never ``node_modules``, so this drifts exactly when the
    staleness warning says everything is current.

    **Only exactly-pinned versions are compared.** A range (``^1.2.3``, ``~1.2``, ``*``,
    ``>=1.0``) is satisfied by many versions, so flagging a difference there would be noise on
    almost every dependency. The private ``@blazeupai/*`` packages — the ones that actually
    break the build — are pinned exactly, so the narrow check catches the real case with no
    false positives.
    """
    manifest = repo / "package.json"
    if not manifest.is_file():
        return []
    with contextlib.suppress(json.JSONDecodeError, OSError):
        pkg = json.loads(manifest.read_text(encoding="utf-8"))
        out: list[tuple[str, str, str]] = []
        for section in ("dependencies", "devDependencies"):
            for name, wanted in (pkg.get(section) or {}).items():
                if not _EXACT_VERSION.fullmatch(str(wanted)):
                    continue
                installed = repo / "node_modules" / Path(name) / "package.json"
                if not installed.is_file():
                    out.append((name, wanted, "(not installed)"))
                    continue
                with contextlib.suppress(json.JSONDecodeError, OSError):
                    have = json.loads(installed.read_text(encoding="utf-8")).get("version", "")
                    if have and have != wanted:
                        out.append((name, wanted, have))
        return sorted(out)
    return []


def dependency_warning(repo: Path) -> str | None:
    """A block naming every drifted package and the fix, or ``None`` when they all match."""
    drift = stale_dependencies(repo)
    if not drift:
        return None
    lines = [
        f"WARNING: {len(drift)} pinned package(s) do not match package.json — "
        "jest will fail to compile, and that is NOT a backend defect:"
    ]
    lines += [f"  {name}  wants {wanted}, has {have}" for name, wanted, have in drift]
    # --ignore-scripts because this repo's postinstall and prepare are Unix-only shell
    # (`rm -rf`, `[ -f ... ]`) and abort npm on Windows after the packages are already in
    # place. Measured 2026-09-16.
    lines.append("  fix: cd <backend clone> && npm install --ignore-scripts")
    return "\n".join(lines)


# A version with no range syntax — "1.0.275" yes, "^1.0.275" / "~1.0" / "*" no.
_EXACT_VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")

# A quoted string inside a jest diff line.
_QUOTED = re.compile(r"[\"'`]([^\"'`]{2,})[\"'`]")
# "at Object.<anonymous> (modules/app.module.spec.ts:76:28)"
_STACK_LOC = re.compile(r"\(([^()]*\.spec\.ts):(\d+):\d+\)")
# "expect(received).toEqual(expected)"
_MATCHER = re.compile(r"expect\([^)]*\)\.(?:rejects\.|resolves\.)?(\w+)\(")
_TOO_GENERIC = re.compile(r"^\d+$|^(true|false|null|undefined)$", re.I)


@dataclass
class Failure:
    spec: str  # path as jest reports it
    test: str
    message: str
    line: int | None = None
    # True when the SUITE never ran (import error, file lock, timeout) rather than an
    # assertion failing. There is no diff to blame in that case, and the cause is usually
    # the environment, so the report must say so instead of hunting for a commit.
    suite_level: bool = False


@dataclass
class Blame:
    token: str
    commits: list[dict] = field(default_factory=list)  # sha/date/author/subject/files
    spec_ever_knew: bool = False


# ── jest output ─────────────────────────────────────────────────────────────


def parse_jest_json(data: dict) -> list[Failure]:
    """Everything red in a ``jest --json`` run — failing assertions AND suites that never ran.

    Reading only ``assertionResults`` under-reports, and silently: a suite that fails to
    LOAD has an empty list and puts its error in the suite's ``message``. Measured
    2026-08-13 — jest reported 3 failed suites while this returned 1 failure, because two
    specs died on ``UNKNOWN: unknown error, open '...node_modules/...'``. The summary block
    said 3 and the detail said 1, which is how the gap showed up.
    """
    out: list[Failure] = []
    for suite in data.get("testResults", []):
        spec = suite.get("name", "")
        failed_assertions = [
            a for a in suite.get("assertionResults", []) if a.get("status") == "failed"
        ]
        for assertion in failed_assertions:
            message = "\n".join(assertion.get("failureMessages") or [])
            loc = _STACK_LOC.search(message)
            out.append(
                Failure(
                    spec=loc.group(1) if loc else spec,
                    test=assertion.get("fullName") or assertion.get("title", ""),
                    message=message,
                    line=int(loc.group(2)) if loc else None,
                )
            )
        if suite.get("status") == "failed" and not failed_assertions:
            out.append(
                Failure(
                    spec=spec,
                    test="(the suite never ran)",
                    message=suite.get("message") or "",
                    suite_level=True,
                )
            )
    return out


def summary(data: dict) -> str:
    """The run totals, in the shape ``npm test`` prints them.

    Included so ``--run`` fully replaces a separate ``npm test``: it invokes the same
    ``jest`` the ``test`` script does, over the same suite, and the only thing the JSON
    mode used to lose was this block. Running both was doing 1052 tests twice.
    """

    def line(label: str, passed: int, failed: int, pending: int, total: int) -> str:
        parts = [f"{passed} passed"]
        if failed:
            parts.insert(0, f"{failed} failed")
        if pending:
            parts.append(f"{pending} pending")
        return f"{label:<13}{', '.join(parts)}, {total} total"

    started = data.get("startTime")
    ended = max((s.get("endTime") or 0) for s in data.get("testResults") or [{}]) or None
    took = f"{(ended - started) / 1000:.1f} s" if started and ended else "?"

    return "\n".join(
        [
            line(
                "Test Suites:",
                data.get("numPassedTestSuites", 0),
                data.get("numFailedTestSuites", 0),
                data.get("numPendingTestSuites", 0),
                data.get("numTotalTestSuites", 0),
            ),
            line(
                "Tests:",
                data.get("numPassedTests", 0),
                data.get("numFailedTests", 0),
                data.get("numPendingTests", 0),
                data.get("numTotalTests", 0),
            ),
            f"{'Time:':<13}{took}",
        ]
    )


def distinguishing_tokens(message: str) -> list[str]:
    """Strings that appear on ONE side of the diff only, longest first.

    A jest diff marks changed lines with +/- and unchanged ones with a leading space. A
    string that also shows up in the unchanged context (``"path"``, ``"method"``) is
    structure, not the difference — searching git for it would match everything. What is
    left is the value that actually moved, which is what ``git log -S`` needs.
    """
    changed: set[str] = set()
    context: set[str] = set()
    for raw in message.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        bucket = changed if stripped[0] in "+-" else context
        bucket.update(_QUOTED.findall(stripped))

    candidates = {
        tok
        for tok in changed - context
        if len(tok) >= 4 and not _TOO_GENERIC.match(tok) and not tok.startswith("Expected")
    }
    return sorted(candidates, key=lambda t: (-len(t), t))


def assertion_kind(message: str, spec_line: str | None) -> str:
    """How the assertion is written — it explains why one added item breaks it."""
    m = _MATCHER.search(message)
    matcher = m.group(1) if m else "?"
    if spec_line and re.search(rf"{re.escape(matcher)}\(\s*\[", spec_line):
        return f"{matcher}([...]) — pins the WHOLE list, so any added item fails it"
    return matcher


# ── git ─────────────────────────────────────────────────────────────────────


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    return (out.stdout or "").strip()


def blame_token(repo: Path, token: str, spec_rel: str | None) -> Blame:
    """The three git lookups: who introduced it, what else they touched, did the spec know."""
    blame = Blame(token=token)
    shas = _git(repo, "log", "--format=%H", "-S", token, "--", "src").splitlines()
    for sha in shas[:5]:  # a token can legitimately arrive more than once
        meta = _git(repo, "log", "-1", "--format=%h|%ad|%an|%s", "--date=short", sha)
        short, _, rest = meta.partition("|")
        when, _, rest = rest.partition("|")
        who, _, subject = rest.partition("|")
        files = [
            line.split("\t")[-1]
            for line in _git(repo, "show", "--name-only", "--format=", sha).splitlines()
            if line.strip()
        ]
        blame.commits.append(
            {
                "sha": short,
                "date": when,
                "author": who,
                "subject": subject,
                "files": files,
                "specs": [f for f in files if f.endswith(".spec.ts")],
            }
        )
    if spec_rel:
        blame.spec_ever_knew = bool(
            _git(repo, "log", "--format=%h", "-S", token, "--", f"src/{spec_rel}")
        )
    return blame


def _days_since(iso: str, today: date) -> int | None:
    with contextlib.suppress(ValueError):
        return (today - date.fromisoformat(iso)).days
    return None


# ── report ──────────────────────────────────────────────────────────────────


def _spec_line(repo: Path, spec_rel: str, line: int | None) -> str | None:
    if not line:
        return None
    path = repo / "src" / spec_rel
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[line - 1] if 0 < line <= len(lines) else None


def render(repo: Path, failure: Failure, today: date) -> str:
    spec_rel = failure.spec.replace("\\", "/").split("src/")[-1].lstrip("/")
    out = [f"\n{spec_rel}", f"  {failure.test}", ""]

    if failure.suite_level:
        # No diff, so no commit to blame. Say what jest said and stop — guessing at a
        # commit here would send someone after a code change that is not the cause.
        reason = next(
            (line.strip() for line in failure.message.splitlines() if line.strip()),
            "no message",
        )
        detail = [line for line in failure.message.splitlines() if line.strip()][1:4]
        out += [f"  SUITE FAILED TO RUN — {reason}"]
        out += [f"      {line.strip()}" for line in detail]
        out += [
            "",
            "  Not an assertion: none of its tests ran, so its test count is missing from",
            "  the totals above. Usually the environment rather than the code —",
            "  a locked or missing file under node_modules, an import cycle, a timeout.",
            "  Re-run it on its own first:",
            f"    npx jest {spec_rel}",
            "",
        ]
        return "\n".join(out)

    tokens = distinguishing_tokens(failure.message)
    if not tokens:
        out += [
            "  No distinctive string in the diff — nothing to search git for.",
            "  Numeric-only failures, timeouts and environment problems land here.",
            "",
            "  Trace it by hand:",
            "    git log -S '<a string from the diff>' -- src",
            "    git show --stat <commit>",
            f"    git log -S '<same string>' -- src/{spec_rel}",
            "",
        ]
        return "\n".join(out)

    token = tokens[0]
    kind = assertion_kind(failure.message, _spec_line(repo, spec_rel, failure.line))
    out.append(f"  Difference : {token!r}   (on one side of the diff only)")
    out.append(f"  Assertion  : {kind}")
    if len(tokens) > 1:
        out.append(f"  (also considered: {', '.join(repr(t) for t in tokens[1:4])})")

    blame = blame_token(repo, token, spec_rel)
    if not blame.commits:
        out += [
            "",
            f"  No commit in src/ introduces {token!r} — the difference may come from a",
            "  shared package, config, or the test environment rather than this repo.",
            "",
        ]
        return "\n".join(out)

    out.append("")
    for c in blame.commits:
        touched_spec = spec_rel in [f.split("src/")[-1] for f in c["files"]]
        age = _days_since(c["date"], today)
        out.append(f"  Introduced : {c['sha']}  {c['date']}  {c['author']}")
        out.append(f"               {c['subject']}")
        out.append(
            f"  That commit: {len(c['files'])} file(s), {len(c['specs'])} of them spec files"
        )
        mark = "touched" if touched_spec else "did NOT touch"
        out.append(f"               {mark} {spec_rel}")
        if age is not None:
            out.append(f"  Red for    : {age} day(s) since {c['date']}")
    out.append(
        f"  This spec  : {'has' if blame.spec_ever_knew else 'has NEVER'} mentioned {token!r}"
    )

    first = blame.commits[0]
    if not blame.spec_ever_knew and first["specs"]:
        out += [
            "",
            "  Reading: the commit DID update other specs and missed this one, and this spec",
            "  has never known about the change. That points at the TEST being stale rather",
            "  than the code being wrong — confirm the behaviour is intended, then fix the test.",
        ]
    out += [
        "",
        "  Ask BE: does the PR pipeline run and BLOCK `npm test`? A test red this long that",
        "  still merged suggests it does not — the workflow lives in another repo, so this",
        "  tool cannot check it.",
        "",
    ]
    return "\n".join(out)


# ── CLI ─────────────────────────────────────────────────────────────────────


def run_jest(repo: Path, pattern: str | None, out_file: Path) -> None:
    """Run jest in the backend clone, writing JSON to OUR path — nothing lands in their repo.

    Captured as BYTES, never text. jest prints check marks, crosses and ANSI colour, and
    Python decodes a subprocess pipe with the console codepage — cp1252 on this machine —
    which raised UnicodeDecodeError from the reader thread mid-run. The traceback looked
    like a crash even though the report was fine, because the data arrives through
    ``--outputFile`` and never through stdout. Decoding is now deferred to the one place
    that needs it: explaining a jest that did not produce the file.
    """
    cmd = ["npx", "jest", "--json", f"--outputFile={out_file}"]
    if pattern:
        cmd.append(pattern)
    print(f"Running {' '.join(cmd[:3])} in {repo} — this takes a couple of minutes...")
    result = subprocess.run(cmd, cwd=repo, capture_output=True, check=False, shell=True)
    if not out_file.is_file():
        tail = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace")
        print(
            f"jest produced no output file (exit {result.returncode}).\n"
            f"{tail[-1500:]}\n"
            "Run `npm ci` in the backend clone if dependencies are missing.",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", type=Path, help="a jest --json output file to analyse")
    ap.add_argument(
        "--run",
        nargs="?",
        const="",
        metavar="PATTERN",
        help="run jest first (optionally for one spec pattern), then analyse",
    )
    ap.add_argument(
        "--check-remote",
        action="store_true",
        help="git fetch the clone first, so the staleness warning is current",
    )
    args = ap.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8")

    repo = be_repo()
    stale = staleness_warning(repo, fetch=args.check_remote)
    # Two different kinds of stale, and the second is the one that misleads. Out-of-date
    # SOURCE makes the report describe an older commit — wrong, but recognisably so. Out-of-
    # date DEPENDENCIES make suites fail to compile, which reads as a backend defect.
    deps = dependency_warning(repo)
    if args.run is not None:
        # Checked before jest rather than only in the report: jest takes minutes, and there is
        # no reason to spend them on source a pull is about to replace, or on a tree that
        # cannot compile. Goes to stderr, which ``logged_run`` does not capture — the report
        # prints both again below.
        if stale:
            print(f"\n{stale}", file=sys.stderr)
            print("  jest is about to spend minutes on that stale source.", file=sys.stderr)
        if deps:
            print(f"\n{deps}", file=sys.stderr)

    flags = []
    if args.run is not None:
        # The raw jest output lands beside the run logs rather than in results/: it is the
        # evidence behind the report, and keeping the two together means one folder holds
        # everything a reader needs to check a claim.
        TOOL_LOG_DIR.mkdir(parents=True, exist_ok=True)
        source = TOOL_LOG_DIR / "be-jest.json"
        flags = ["--run", args.run] if args.run else ["--run"]
        run_jest(repo, args.run or None, source)
    elif args.json:
        source = args.json
        flags = ["--json", str(args.json)]
    else:
        print(
            "Give it a jest run to analyse:\n"
            "  1. cd <backend clone> && npx jest --json --outputFile=jest.json\n"
            "     python -m utils.be_test_blame --json <backend clone>/jest.json\n"
            "  2. or let this tool run jest for you:\n"
            "     python -m utils.be_test_blame --run",
            file=sys.stderr,
        )
        return 2

    if not source.is_file():
        print(f"No jest output at {source}", file=sys.stderr)
        return 2

    with logged_run("be_test_blame", flags):
        data = json.loads(source.read_text(encoding="utf-8"))
        failures = parse_jest_json(data)
        sha, be_date = be_head(repo)
        print(f"\nBackend : {be_branch(repo)} @ {sha} ({be_date})")
        if stale:
            print(stale)
        if deps:
            print(deps)
        print(f"jest    : {rel(source)}\n")
        print(summary(data))
        if failures:
            today = date.today()
            for failure in failures:
                print(render(repo, failure, today))
        else:
            print("\nNothing to blame.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
