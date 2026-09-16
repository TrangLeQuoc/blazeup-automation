"""What changed in the backend since last time, and which TCs to re-run because of it.

A backend deploy currently leaves two bad options: run all 124 TCs (~11 minutes) or run
none. This narrows it to the TCs whose endpoints are actually affected.

Measured evidence that the gap is real, not theoretical:

* ``POST /v1/partner/auth/forgot-password`` shipped 2026-07-27 and was still unknown to
  this suite 16 days later — absent from the TCs AND from the saved Swagger baseline.
* A closed bug left a ``be_gap`` marker in place for three weeks, keeping a passing TC
  outside the merge gate.

Run from THIS repo (it needs ``api_clients/`` and the TC registry to name the TCs); the
backend clone is only input and is never written to. Point ``BLAZEUP_BE_REPO`` at that
clone, in ``config/blazeup/.env`` or as an environment variable::

    python -m utils.be_drift              # diff the saved baseline against HEAD
    python -m utils.be_drift --save       # record HEAD as the new baseline
    python -m utils.be_drift --base <sha> # diff an explicit ref instead

``git pull`` the backend clone first, or there is nothing to diff.

The baseline is a file this repo owns, exactly like the Swagger baseline: the backend
exposes no ``/version`` endpoint and its deploy tag lives in a shared CI repo, so there is
no way to ask staging which commit it runs. ``record_baseline`` is the single place to
change if that ever becomes possible.
"""

import argparse
import contextlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from utils.be_coverage import (
    Endpoint,
    be_branch,
    be_head,
    be_repo,
    build_coverage,
    extract_be_endpoints_from,
    logged_run,
    rel,
    staleness_warning,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT_ROOT / "docs" / "api-snapshots" / "blazeup" / "be-commit.txt"

# A changed file rarely IS a controller; more often it is a service or helper the
# controller reaches through. Walk the import graph back this many hops before giving up.
# 3 covers controller -> service -> helper, which is how this codebase is layered.
MAX_IMPORT_HOPS = 3

# Above this many affected endpoints, listing individual TCs stops being useful — the
# change is broad and the whole area should be run.
WIDE_CHANGE_ENDPOINTS = 8

_IMPORT_RE = re.compile(r"""^\s*(?:import|export)\s[^'"]*from\s+['"](\.[^'"]+)['"]""", re.M)


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    return (out.stdout or "").strip()


# ── Baseline ────────────────────────────────────────────────────────────────


def read_baseline() -> str | None:
    """The commit this suite was last reconciled against, or None."""
    if not BASELINE.is_file():
        return None
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            return line
    return None


def record_baseline(repo: Path) -> str:
    """Write HEAD as the new baseline and return it."""
    sha, date = be_head(repo)
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(
        f"{sha}\n"
        f"# Backend commit this suite was last reconciled against.\n"
        f"# branch {be_branch(repo)} · committed {date} · recorded by utils/be_drift.py\n"
        f"# NOT necessarily what staging runs: the service exposes no /version endpoint,\n"
        f"# so this is our own bookmark. Update it after reconciling a deploy.\n",
        encoding="utf-8",
    )
    return sha


# ── Change -> endpoints ─────────────────────────────────────────────────────


def changed_files(repo: Path, base: str, head: str = "HEAD") -> list[str]:
    """Source files that differ between two refs, relative to src/."""
    raw = _git(repo, "diff", "--name-only", f"{base}..{head}", "--", "src")
    return sorted(line[4:] for line in raw.splitlines() if line.startswith("src/"))


def _import_graph(repo: Path) -> dict[str, set[str]]:
    """``{file: {files it imports}}`` over src/, relative paths resolved."""
    src = repo / "src"
    graph: dict[str, set[str]] = {}
    for path in src.rglob("*.ts"):
        if path.name.endswith(".spec.ts"):
            continue
        node = path.relative_to(src).as_posix()  # not `rel` — that name is the imported helper
        targets: set[str] = set()
        for spec in _IMPORT_RE.findall(path.read_text(encoding="utf-8")):
            resolved = (path.parent / spec).resolve()
            for candidate in (
                resolved.with_suffix(".ts"),
                resolved / "index.ts",
            ):
                with contextlib.suppress(ValueError):
                    if candidate.is_file():
                        targets.add(candidate.relative_to(src).as_posix())
                        break
        graph[node] = targets
    return graph


def controllers_touched(repo: Path, files: list[str]) -> dict[str, set[str]]:
    """``{controller: {changed files that reach it}}``.

    A changed file affects a controller when the controller imports it, directly or
    through up to ``MAX_IMPORT_HOPS`` intermediate modules. Reverse-walked from the
    controllers so an unrelated changed file simply never appears.
    """
    graph = _import_graph(repo)
    changed = set(files)
    hits: dict[str, set[str]] = defaultdict(set)

    for ctrl in (f for f in graph if f.endswith(".controller.ts")):
        seen: set[str] = set()
        frontier = {ctrl}
        for _hop in range(MAX_IMPORT_HOPS + 1):
            if not frontier:
                break
            for node in frontier:
                if node in changed:
                    hits[ctrl].add(node)
            seen |= frontier
            frontier = {t for node in frontier for t in graph.get(node, ())} - seen
    return hits


# ── New routes ──────────────────────────────────────────────────────────────


def endpoints_at(repo: Path, ref: str) -> list[Endpoint]:
    """Routes as they were at *ref*, read via ``git show`` — nothing is checked out.

    Reading the old tree matters: comparing against today's files only reveals new
    controller FILES, while the common case is a new route added to an existing
    controller. ``forgot-password`` (shipped 2026-07-27) was exactly that.
    """
    listing = _git(repo, "ls-tree", "-r", "--name-only", ref, "--", "src")
    paths = [p for p in listing.splitlines() if p.endswith(".ts")]
    controllers, specs = {}, {}
    for path in paths:
        inner = path[4:]  # drop "src/" — not `rel`, which is the imported helper
        if path.endswith(".spec.ts"):
            specs[inner] = _git(repo, "show", f"{ref}:{path}")
        elif path.endswith(".controller.ts"):
            controllers[inner] = _git(repo, "show", f"{ref}:{path}")
    if not controllers:
        return []
    return extract_be_endpoints_from(controllers, specs)[0]


def new_endpoints(repo: Path, base: str, current: list[Endpoint]) -> list[Endpoint]:
    """Routes present now that did not exist at *base*."""
    try:
        before = {ep.key for ep in endpoints_at(repo, base)}
    except Exception as exc:  # noqa: BLE001 — a bad ref must not hide the rest of the report
        print(f"  (could not read the tree at {base}: {exc} — skipping new-route detection)")
        return []
    if not before:
        return []
    return [ep for ep in current if ep.key not in before]


# ── Report ──────────────────────────────────────────────────────────────────


def _fmt(ep: Endpoint) -> str:
    return f"{ep.method:6} {ep.path}"


def report(base: str, head: str = "HEAD", *, check_remote: bool = False) -> int:
    """Print the drift report. Exit 0 always — this is information, not a gate."""
    repo = be_repo()
    sha, date = be_head(repo)
    print(f"\nBackend : {be_branch(repo)}  {base}  ->  {sha} ({date})")

    # Before the early return, not after: an unpulled clone has no changes to find, so the
    # "nothing to re-run" line below is exactly what a stale run prints. Of the four tools
    # this is the one that fails as a false all-clear rather than an error, and a warning
    # printed after that line would arrive too late to be read as qualifying it.
    stale = staleness_warning(repo, fetch=check_remote)
    if stale:
        print(stale)

    files = changed_files(repo, base, head)
    if not files:
        print("\nNo source changes since the baseline. Nothing to re-run.")
        if stale:
            print("  ^ and this clone is behind, so that is not evidence the backend is quiet.")
        return 0
    print(f"Changed : {len(files)} file(s) under src/")

    cov = build_coverage(repo)
    by_controller: dict[str, list[Endpoint]] = defaultdict(list)
    for ep in cov.endpoints:
        by_controller[ep.controller].append(ep)

    touched = controllers_touched(repo, files)
    affected: list[Endpoint] = [ep for ctrl in touched for ep in by_controller.get(ctrl, [])]

    new = new_endpoints(repo, base, cov.endpoints)

    if new:
        print(f"\nNEW ENDPOINTS ({len(new)})")
        for ep in sorted(new, key=lambda e: e.path):
            tcs = cov.endpoint_tcs.get(ep.key)
            mark = ", ".join(tcs) if tcs else "NO TC YET"
            print(f"  {_fmt(ep):58} {mark}")

    if not affected:
        print("\nNo endpoint reachable from the changed files. Cron/consumer/config only?")
        return 0

    wide = [
        c for c, _f in touched.items() if len(by_controller.get(c, [])) >= WIDE_CHANGE_ENDPOINTS
    ]
    tc_ids: set[str] = set()
    print(f"\nAFFECTED ENDPOINTS ({len(affected)})")
    for ep in sorted(affected, key=lambda e: (e.path, e.method)):
        tcs = cov.endpoint_tcs.get(ep.key, [])
        tc_ids.update(t for t in tcs if t.isdigit())
        print(f"  {_fmt(ep):58} {', '.join(tcs) if tcs else '— no TC'}")

    if wide:
        print("\nWIDE CHANGE — consider running the whole area rather than the listed TCs")
        for ctrl in sorted(wide):
            n = len(by_controller.get(ctrl, []))
            # Only name the indirect route in; "via <itself>" would say nothing.
            indirect = sorted(touched[ctrl] - {ctrl})
            via = f"  via {', '.join(indirect[:3])}" if indirect else "  (edited directly)"
            print(f"  {ctrl}  ({n} endpoints){via}")

    if tc_ids:
        ids = " ".join(sorted(tc_ids))
        print(f"\nRE-RUN ({len(tc_ids)} TC)\n  python -m runner.blazeup.run_test --execute {ids}")
    else:
        print("\nNo TC covers the affected endpoints — this change is untested here.")

    # Shared-library bumps are invisible to the import graph: those packages live in other
    # repos, and the ghost-id 400-vs-404 family originates in one of them.
    pkg = _git(repo, "diff", f"{base}..{head}", "--", "package.json")
    bumped = [
        line
        for line in pkg.splitlines()
        if line.startswith("+") and "@blazeupai/" in line and "blazeup-microservice" not in line
    ]
    if bumped:
        print("\nSHARED LIBRARY BUMPED — behaviour change here is NOT visible in this diff")
        for line in bumped:
            print(f"  {line.strip()}")

    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", help="backend ref to diff from (default: saved baseline)")
    ap.add_argument("--head", default="HEAD", help="backend ref to diff to (default: HEAD)")
    ap.add_argument("--save", action="store_true", help="record HEAD as the new baseline")
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
    if args.save:
        sha = record_baseline(repo)
        print(f"Baseline recorded: {sha}  ->  {rel(BASELINE)}")
        return 0

    base = args.base or read_baseline()
    if not base:
        print(
            f"No baseline yet ({rel(BASELINE)} missing).\n"
            "Record one against the commit currently deployed:\n"
            "  python -m utils.be_drift --save",
            file=sys.stderr,
        )
        return 2

    # --save just bookmarks a commit; only an actual drift report is worth archiving.
    flags = ["--base", base] if args.base else []
    if args.check_remote:
        flags.append("--check-remote")
    with logged_run("be_drift", flags):
        return report(base, args.head, check_remote=args.check_remote)


if __name__ == "__main__":
    raise SystemExit(main())
