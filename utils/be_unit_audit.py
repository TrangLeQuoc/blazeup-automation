"""Are the backend's unit tests actually protecting anything?

``utils/be_coverage.py`` answers "does a unit test exist for this endpoint". That is not
the same as "is it any good", and the difference is not academic: the backend runs 1052
green unit tests and none of them notices the ghost-id 400-vs-404 defects this suite has
been reporting since July.

Four checks, all read from SOURCE ALONE — no Bug_Tracker lookup, so a brand-new API is
audited the same as an old one. Where a finding happens to match an open bug, that is
reported as extra evidence, never as the thing that makes it a finding.

    A  not-found answered with 400   REST says 404. Detected in the service, so it holds
                                     for endpoints nobody has filed a bug against yet.
    B  circular test                 mocks an exception, then asserts that exception.
                                     Green whichever behaviour is correct — protects nothing.
    C  spec with no error assertion   only the happy path is pinned; every 4xx/5xx path at
                                     the HTTP boundary is unverified at unit level.
    D  guard never exercised          the controller declares @UseGuards, the spec never
                                     names it, so the authorization path is untested.

None of these prove a test is WRONG — that needs a human with the PRD. They point at the
places worth a human's time, and they say why.

Usage::

    python -m utils.be_unit_audit            # full report
    python -m utils.be_unit_audit --check B  # one check
"""

import argparse
import contextlib
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from utils.be_coverage import be_branch, be_head, be_repo, logged_run, staleness_warning

# "not found" in any of the phrasings this codebase uses.
_NOT_FOUND = re.compile(r"not found|does not exist|no longer exists|not exist", re.I)

# A: the two ways this service answers "missing record" with a 400.
#   1. thrown outright
#   2. delegated to the shared Method helper, whose isThrow raises BadRequestException
_THROW_400 = re.compile(r"throw new BadRequestException\(\s*[`'\"]?([^`'\")]*)")
_IS_THROW = re.compile(r"isThrow:\s*true")

# B: inside one it(), an exception is mocked and then asserted.
_IT_BLOCK = re.compile(r"\bit(?:\.each\([^)]*\))?\s*\(\s*[`'\"](.+?)[`'\"]", re.S)
_MOCK_THROWS = re.compile(r"mockRejectedValue\(\s*new (\w+)")
_ASSERT_THROWS = re.compile(r"rejects\.toThrow\(\s*(?:new\s+)?(\w+)")
# A test whose NAME is about passing an exception on is not over-claiming when its body
# does exactly that — exempt it rather than report a test doing its stated job.
_PROPAGATION_INTENT = re.compile(r"propagat|delegat|forward|bubble|pass(?:es)? through", re.I)

# C: anything that pins a failure path.
_ERROR_ASSERT = re.compile(
    r"rejects|toThrow|Exception|toBe\((?:4\d\d|5\d\d)\)|Unauthorized|Forbidden|status\(4"
)

# D
_USE_GUARDS = re.compile(r"@UseGuards\(([^)]*)\)")


@dataclass
class Finding:
    check: str
    where: str  # file:line, relative to src/
    what: str
    why: str


# ── A. not-found answered with 400 ──────────────────────────────────────────


def check_not_found_is_400(src: Path) -> list[Finding]:
    """Services that answer "missing record" with 400 rather than 404.

    Both shapes matter, and the second dominates: 3 sites throw BadRequestException
    directly, 29 delegate to ``Method.findById(..., { isThrow: true, message: '... not
    found' })`` in the shared ``@blazeupai`` package, which raises BadRequestException.
    A detector that only reads the literal throw misses 90% of the family.
    """
    out: list[Finding] = []
    for path in sorted(src.rglob("*.ts")):
        if path.name.endswith(".spec.ts"):
            continue
        rel = path.relative_to(src).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, start=1):
            m = _THROW_400.search(line)
            if m and _NOT_FOUND.search(m.group(1)):
                out.append(
                    Finding(
                        "A",
                        f"{rel}:{i}",
                        f"throw new BadRequestException({m.group(1).strip()!r})",
                        "a missing record is a 404; a 400 says the REQUEST was malformed",
                    )
                )
            elif _IS_THROW.search(line):
                # the message may sit on a neighbouring line of the same options object
                window = " ".join(lines[max(0, i - 3) : i + 3])
                msg = re.search(r"message:\s*[`'\"]?([^`'\",]*)", window)
                if msg and _NOT_FOUND.search(msg.group(1)):
                    out.append(
                        Finding(
                            "A",
                            f"{rel}:{i}",
                            f"isThrow: true, message: {msg.group(1).strip()!r}",
                            "the shared Method helper raises BadRequestException here, "
                            "so this reaches the client as 400 rather than 404",
                        )
                    )
    return out


# ── B. circular tests ───────────────────────────────────────────────────────


def check_circular_tests(src: Path) -> list[Finding]:
    """Tests whose NAME claims a rule but whose body only proves an exception passed through.

    ``mockRejectedValue(new BadRequestException(...))`` followed by
    ``rejects.toThrow(BadRequestException)`` asserts exactly what it stubbed. It stays
    green whether 400 or 404 is the correct answer, so it can neither catch the defect nor
    fail once the defect is fixed.

    Circularity alone is NOT the finding — for a controller, "does it swallow the
    service's exception?" is a fair question, and a test named ``should propagate ...`` is
    doing what it says. The finding is the MISMATCH. Compare, all three verified by hand
    on 2026-08-12:

        'should propagate NotFoundException from service'   name = propagation. Fine.
        'throws when email already exists'                  name = a duplicate-email rule;
                                                            body only stubs and re-checks.
        'rejects a ghost planId BEFORE creating the deal'    name also promises no deal was
                                                            created; body never asserts it.

    So a name that says propagate / delegate / forward / bubble is exempt.
    """
    out: list[Finding] = []
    for path in sorted(src.rglob("*.spec.ts")):
        rel = path.relative_to(src).as_posix()
        text = path.read_text(encoding="utf-8")
        starts = [(m.start(), m.group(1)) for m in _IT_BLOCK.finditer(text)]
        for idx, (pos, title) in enumerate(starts):
            if _PROPAGATION_INTENT.search(title):
                continue  # the name promises exactly what the body proves
            end = starts[idx + 1][0] if idx + 1 < len(starts) else len(text)
            block = text[pos:end]
            same = set(_MOCK_THROWS.findall(block)) & set(_ASSERT_THROWS.findall(block))
            if same:
                line = text.count("\n", 0, pos) + 1
                out.append(
                    Finding(
                        "B",
                        f"{rel}:{line}",
                        f"it({title!r}) mocks and asserts {', '.join(sorted(same))}",
                        "the name claims a rule; the body only proves the stubbed exception "
                        "was passed through — green whichever behaviour is correct",
                    )
                )
    return out


# ── C. specs with no error assertion ────────────────────────────────────────


def check_happy_path_only(src: Path) -> list[Finding]:
    """Controller specs that never pin a failure path.

    Measured 2026-08-12: 8 of 11 controller specs assert no error at all. In
    ``partner-auth.controller.spec.ts`` every one of the 11 tests is named "delegates X",
    i.e. it checks the controller forwards to the service and nothing else.

    That is a defensible split — NestJS error behaviour usually lives in the service — but
    for QA it is the point: the STATUS CODES, the guards and the validation at the HTTP
    boundary are unverified at unit level, so the API suite is their only cover.
    """
    out: list[Finding] = []
    for path in sorted(src.rglob("*controller*.spec.ts")):
        rel = path.relative_to(src).as_posix()
        text = path.read_text(encoding="utf-8")
        tests = len(_IT_BLOCK.findall(text))
        errors = len(_ERROR_ASSERT.findall(text))
        if tests and not errors:
            out.append(
                Finding(
                    "C",
                    rel,
                    f"{tests} test(s), 0 error assertions",
                    "no 4xx/5xx path pinned here — the API suite is the only cover",
                )
            )
    return out


# ── D. guards never exercised ───────────────────────────────────────────────


def check_guards_untested(src: Path) -> list[Finding]:
    """Controllers whose declared guards are never named by a spec.

    A guard is the authorization boundary. If no spec mentions it, nothing proves an
    unauthenticated or wrong-role caller is actually refused.
    """
    specs = {p: p.read_text(encoding="utf-8") for p in src.rglob("*.spec.ts")}
    out: list[Finding] = []
    for ctrl in sorted(src.rglob("*.controller.ts")):
        if ctrl.name.endswith(".spec.ts"):
            continue
        text = ctrl.read_text(encoding="utf-8")
        guards = {
            g.strip() for match in _USE_GUARDS.findall(text) for g in match.split(",") if g.strip()
        }
        if not guards:
            continue
        cls = re.search(r"export\s+class\s+(\w+)", text)
        cls_name = cls.group(1) if cls else ctrl.stem
        own = [s for s, body in specs.items() if re.search(rf"\b{re.escape(cls_name)}\b", body)]
        untested = sorted(
            g for g in guards if not any(re.search(rf"\b{re.escape(g)}\b", specs[s]) for s in own)
        )
        if untested:
            out.append(
                Finding(
                    "D",
                    ctrl.relative_to(src).as_posix(),
                    f"declares {', '.join(untested)}; no spec for {cls_name} names them",
                    "the authorization path is unverified — nothing proves a wrong caller is refused",
                )
            )
    return out


CHECKS = {
    "A": ("not-found answered with 400 instead of 404", check_not_found_is_400),
    "B": ("circular test — mocks then asserts the same exception", check_circular_tests),
    "C": ("controller spec with no error assertion", check_happy_path_only),
    "D": ("guard declared but never exercised by a spec", check_guards_untested),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", choices=sorted(CHECKS), help="run one check only")
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
    src = repo / "src"
    flags = ["--check", args.check] if args.check else []
    if args.check_remote:
        flags.append("--check-remote")
    with logged_run("be_unit_audit", flags):
        _report(
            repo,
            src,
            [args.check] if args.check else sorted(CHECKS),
            check_remote=args.check_remote,
        )
    return 0


def _report(repo: Path, src: Path, selected: list[str], *, check_remote: bool = False) -> None:
    """The report itself, split out so ``logged_run`` can wrap exactly this output."""
    sha, date = be_head(repo)
    print(f"\nBackend : {be_branch(repo)} @ {sha} ({date})")
    if stale := staleness_warning(repo, fetch=check_remote):
        print(stale)
    print(f"Specs   : {len(list(src.rglob('*.spec.ts')))} files\n")

    grand = 0
    for key in selected:
        title, fn = CHECKS[key]
        findings = fn(src)
        grand += len(findings)
        print(f"{'=' * 78}\n[{key}] {title} — {len(findings)}\n{'=' * 78}")
        if not findings:
            print("  none\n")
            continue
        by_file: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            by_file[f.where.split(":")[0]].append(f)
        for file in sorted(by_file):
            print(f"\n  {file}")
            for f in by_file[file]:
                loc = f.where.split(":")
                at = f":{loc[1]}" if len(loc) > 1 else ""
                print(f"    {at:>7}  {f.what}")
            print(f"           -> {by_file[file][0].why}")
        print()

    print(f"{'=' * 78}\nTOTAL findings: {grand}")
    print(
        "\nThese point at places worth a human's time; none of them proves a test is wrong.\n"
        "Deciding that needs the PRD and a person."
    )


if __name__ == "__main__":
    raise SystemExit(main())
