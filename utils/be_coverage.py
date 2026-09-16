"""Map the backend's HTTP surface against this suite's API coverage.

Answers two questions that nothing else here can:

* Which backend endpoints does the automation suite actually exercise, and which does
  nobody test at all? (``python -m utils.be_coverage``)
* When the backend changes, which TCs should be re-run? (``utils/be_drift.py``, which
  builds on the extraction here.)

``make swagger`` covers a different axis: it detects CONTRACT drift (paths, params,
schemas) against a saved OpenAPI baseline. It cannot say whether an endpoint is tested,
and it cannot see a change that leaves the contract intact — which is most of them.

Needs a local clone of the backend repo; point ``BLAZEUP_BE_REPO`` at it, in
``config/blazeup/.env`` or as an environment variable. Run from THIS repo — the clone is
only input and is never written to.

Two extraction pitfalls, both measured on 2026-08-12, both easy to reintroduce:

1. Between a ``@Get``/``@Post``/... decorator and its handler sit any number of other
   decorators, several MULTI-LINE (``@ApiBody({ examples: { ... } })`` runs 40+ lines).
   A single regex paired 45 of 101 routes; the bracket-depth walk in ``_find_handler``
   pairs all 101. Anything that silently drops routes reports the gap as "covered".
2. Client methods reach the HTTP layer with a literal, an f-string over a constant, OR a
   bare constant (``self.get(_PARTNERS_PATH, ...)``). Reading only literals missed
   ``/v1/partner/auth/me`` entirely and under-counted QA coverage by a quarter.
"""

import argparse
import contextlib
import io
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLIENTS_DIR = PROJECT_ROOT / "api_clients"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs" / "blazeup"

# Every backend-facing tool writes here: a timestamped markdown log per run, the coverage
# map, and the raw jest output. Everything is dated rather than overwritten, so the folder
# is a HISTORY — the question you cannot answer afterwards is "when did that number move",
# and a single always-current file cannot answer it.
TOOL_LOG_DIR = DOCS_DIR / "tools" / "BE"

# The service this map covers. The backend repo is one microservice; QA client paths carry
# it as a prefix that backend routes do not.
SERVICE_PREFIX = "/sa-partners-api"

# Test fixture name -> the client module it is an instance of. Needed because a test only
# names the fixture (``sa_partners_client.approve_partner``), and method names repeat
# across clients (``list``, ``findById``), so the method name alone would mis-map.
FIXTURE_CLIENTS: dict[str, str] = {
    "sa_partners_client": "sa_partners_client.py",
    "sa_deals_client": "sa_deals_client.py",
    "sa_commissions_client": "sa_commissions_client.py",
    "auth_client": "auth_client.py",
    # every partner-portal session, however the test names it
    "portal": "partner_portal_client.py",
    "portal_a": "partner_portal_client.py",
    "portal_b": "partner_portal_client.py",
    "anon": "partner_portal_client.py",
    "refreshed": "partner_portal_client.py",
}


def rel(path: Path) -> str:
    """Repo-relative when it is, absolute otherwise.

    ``Path.relative_to`` raises outside the tree, and every use of it here is inside a
    message — so the plain call turns a helpful line into a ValueError. That happened
    twice before this helper existed.
    """
    with contextlib.suppress(ValueError):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


# ── Run logs ─────────────────────────────────────────────────────────────────


class _Tee(io.StringIO):
    """Collects everything written while still printing it live.

    Not ``redirect_stdout`` into a buffer: ``be_test_blame --run`` takes two minutes, and
    swallowing its progress line until the end looks like a hang.
    """

    def __init__(self, target) -> None:
        super().__init__()
        self._target = target

    def write(self, s: str) -> int:
        self._target.write(s)
        self._target.flush()
        return super().write(s)


@contextlib.contextmanager
def logged_run(tool: str, argv: list[str] | None = None):
    """Run a tool, printing as usual, and archive the output as dated markdown.

    Named ``YYYYMMDD-HHMMSS_<tool>.md`` so the directory sorts chronologically. The
    command line is recorded in the file because the same tool run with different flags
    produces very different reports.
    """
    stamp = datetime.now()
    buffer = _Tee(sys.stdout)
    try:
        with contextlib.redirect_stdout(buffer):
            yield
    finally:
        TOOL_LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = TOOL_LOG_DIR / f"{stamp:%Y%m%d-%H%M%S}_{tool}.md"
        command = " ".join(["python", "-m", f"utils.{tool}", *(argv or [])]).strip()
        path.write_text(
            f"# {tool} — {stamp:%Y-%m-%d %H:%M:%S}\n\n"
            f"```\n{command}\n```\n\n"
            f"```\n{buffer.getvalue().rstrip()}\n```\n",
            encoding="utf-8",
        )
        print(f"\nlog -> {rel(path)}")


# ── Backend repo location ────────────────────────────────────────────────────


ENV_FILE = PROJECT_ROOT / "config" / "blazeup" / ".env"
ENV_KEY = "BLAZEUP_BE_REPO"


def _from_env_file(key: str) -> str | None:
    """Read one ``KEY=value`` out of config/blazeup/.env.

    Parsed here rather than through ``config.settings``: Settings validates the whole file
    and raises when a URL or credential is missing, so a coverage report — which needs no
    credentials at all — would fail for reasons unrelated to it.
    """
    if not ENV_FILE.is_file():
        return None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() == key:
            return value.strip().strip("\"'") or None
    return None


def be_repo() -> Path:
    """Path to the backend clone.

    ``BLAZEUP_BE_REPO`` from the environment wins, so a one-off run or CI can override;
    otherwise the same key from ``config/blazeup/.env``, which is where it belongs for
    day-to-day use (that file is gitignored, so the path stays per-machine).

    Never defaulted to a guessed path: a wrong path yields an empty endpoint list, which
    reads as "the backend has no routes" — a silent wrong answer instead of an error.
    """
    raw = os.getenv(ENV_KEY) or _from_env_file(ENV_KEY)
    if not raw:
        raise SystemExit(
            f"{ENV_KEY} is not set. Point it at a clone of\n"
            "  blazeupai/blazeup-microservice-sa-partners\n\n"
            f"Either add it to {rel(ENV_FILE)}:\n"
            f'  {ENV_KEY}="C:/Users/you/Desktop/blazeup/blazeup-microservice-sa-partners"\n\n'
            "or export it for one run:\n"
            f'  export {ENV_KEY}="/c/Users/you/Desktop/blazeup/'
            'blazeup-microservice-sa-partners"'
        )
    path = Path(raw)
    if not (path / "src").is_dir():
        raise SystemExit(f"{ENV_KEY}={path} has no src/ — is that the backend repo?")
    return path


def be_head(repo: Path | None = None) -> tuple[str, str]:
    """Return ``(short_sha, iso_date)`` of the backend clone's HEAD."""
    repo = repo or be_repo()
    out = subprocess.run(
        ["git", "log", "-1", "--format=%h|%ad", "--date=short"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    sha, _, date = (out.stdout or "|").strip().partition("|")
    return sha, date


def be_branch(repo: Path | None = None) -> str:
    repo = repo or be_repo()
    out = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return (out.stdout or "").strip()


def remote_lag(repo: Path | None = None, *, fetch: bool = False) -> tuple[int, str] | None:
    """How many commits the upstream branch has that the clone's ``HEAD`` does not.

    Returns ``(count, upstream_ref)``, or ``None`` when there is nothing to say — no
    upstream configured, detached HEAD, or already current.

    Every tool here reads **files on disk**, and those follow ``HEAD``. ``HEAD`` only moves
    on a pull, so an unpulled clone makes all four report on yesterday's source. ``be_drift``
    fails the dangerous way: it says *"nothing to re-run"* rather than erroring.

    Reads the remote-tracking ref as it already stands; *fetch* refreshes it first. It is
    deliberately never a pull — these tools promise not to write the clone, and a pull would
    move the user's ``HEAD`` behind their back. So this reports the problem and names the fix
    instead of applying it.
    """
    repo = repo or be_repo()

    def git(*args: str) -> tuple[int, str]:
        out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
        return out.returncode, (out.stdout or "").strip()

    code, upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if code or not upstream:
        return None  # no upstream, or detached — nothing to compare against

    if fetch:
        git("fetch", "--quiet")

    code, count = git("rev-list", "--count", f"HEAD..{upstream}")
    if code or not count.isdigit() or count == "0":
        return None
    return int(count), upstream


def staleness_warning(repo: Path | None = None, *, fetch: bool = False) -> str | None:
    """One line naming the lag and the fix, or ``None`` when the clone is current."""
    lag = remote_lag(repo, fetch=fetch)
    if not lag:
        return None
    count, upstream = lag
    plural = "commit" if count == 1 else "commits"
    return (
        f"WARNING: {upstream} has {count} {plural} this clone does not — "
        f"`git pull` it and re-run, or you are reading stale source"
    )


# ── Models ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Endpoint:
    """One backend route, plus whether a unit test names its handler."""

    method: str
    path: str
    handler: str
    controller: str  # relative to src/
    cls: str
    own_specs: tuple[str, ...] = ()
    specs: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str]:
        return self.method, normalise(self.path)

    @property
    def unit_tested(self) -> bool:
        return bool(self.specs)


@dataclass
class QaCall:
    """One HTTP call a client method makes."""

    method: str
    path: str
    client: str  # file name, e.g. sa_partners_client.py
    func: str  # the client method that makes the call

    @property
    def key(self) -> tuple[str, str]:
        return self.method, normalise(self.path)


@dataclass
class Coverage:
    """The joined picture."""

    endpoints: list[Endpoint]
    qa_calls: list[QaCall]
    quadrants: dict[str, list[Endpoint]] = field(default_factory=dict)
    endpoint_tcs: dict[tuple[str, str], list[str]] = field(default_factory=dict)


# ── Path shapes ─────────────────────────────────────────────────────────────


def normalise(path: str) -> str:
    """One shape for both sides: no service prefix, every path parameter as ``*``."""
    p = path[len(SERVICE_PREFIX) :] if path.startswith(SERVICE_PREFIX) else path
    p = re.sub(r":\w+", "*", p)  # backend  :id   -> *
    p = re.sub(r"\{[^}]+\}", "*", p)  # client   {id}  -> *
    return "/" + p.strip("/")


# ── Backend extraction ──────────────────────────────────────────────────────

_CTRL_RE = re.compile(r"@Controller\(\s*['\"]([^'\"]*)['\"]")
_CLASS_RE = re.compile(r"export\s+class\s+(\w+)")
_ROUTE_RE = re.compile(r"^\s*@(Get|Post|Patch|Put|Delete)\(\s*(?:['\"]([^'\"]*)['\"])?\s*\)")
_HANDLER_RE = re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:async\s+)?(\w+)\s*\(")
_NOT_A_HANDLER = {"if", "return", "for", "while", "switch", "catch", "constructor"}


def _depth(line: str) -> int:
    """Net bracket delta, ignoring brackets inside quotes."""
    out, quote, prev = 0, None, ""
    for ch in line:
        if quote:
            if ch == quote and prev != "\\":
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch in "([{":
            out += 1
        elif ch in ")]}":
            out -= 1
        prev = ch
    return out


def _find_handler(lines: list[str], start: int, decorator_end: int = 0) -> str | None:
    """The handler a route decorator on line *start* belongs to.

    Walks forward, consuming whole decorators however many lines they span (tracked by
    bracket depth) and skipping comments, then reads the first real signature. Returns
    None rather than guessing — callers count those, so a parser regression is visible.

    *decorator_end* is where the route decorator finishes on its own line, so the compact
    one-line form is handled too::

        @Get() async findAll() {}

    This service never writes it that way today (all 101 routes are on their own line), but
    it is valid NestJS and the parser must not silently drop such a route — a dropped route
    reports as *covered*.
    """
    tail = lines[start][decorator_end:] if decorator_end else ""
    if tail.strip() and not tail.lstrip().startswith(("@", "//")):
        m = _HANDLER_RE.match(tail)
        if m and m.group(1) not in _NOT_A_HANDLER:
            return m.group(1)

    depth, in_block_comment = 0, False
    for j in range(start + 1, min(start + 200, len(lines))):
        stripped = lines[j].strip()
        if in_block_comment:
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith("/*"):
            in_block_comment = "*/" not in stripped
            continue
        if not stripped or stripped.startswith("//"):
            continue
        if depth > 0:  # still inside a multi-line decorator
            depth += _depth(lines[j])
            continue
        if stripped.startswith("@"):
            depth += _depth(lines[j])
            continue
        m = _HANDLER_RE.match(lines[j])
        if m and m.group(1) not in _NOT_A_HANDLER:
            return m.group(1)
        return None
    return None


def extract_be_endpoints_from(
    controllers: dict[str, str], specs: dict[str, str]
) -> tuple[list[Endpoint], list[str]]:
    """Routes from in-memory sources. Both maps are ``{path relative to src/: text}``.

    Split out from ``extract_be_endpoints`` so a caller can pass file contents read at an
    older git revision (``git show <ref>:<path>``) and get comparable endpoints without
    checking anything out — that is how ``utils/be_drift.py`` tells a NEW route apart from
    a new file.

    A handler counts as unit-tested only when a spec that names its CONTROLLER CLASS also
    names the handler. Matching by file name instead under-reports: spec files are not
    named after their controllers (``partners.sa.controller.ts`` is tested by
    ``partners.controller.spec.ts``, ``lookup.partner.controller.ts`` by
    ``partner-lookup.controller.spec.ts``).
    """
    endpoints: list[Endpoint] = []
    unpaired: list[str] = []
    for rel in sorted(controllers):
        text = controllers[rel]
        lines = text.splitlines()
        cm = _CTRL_RE.search(text)
        prefix = (cm.group(1) if cm else "").strip("/")
        km = _CLASS_RE.search(text)
        cls = km.group(1) if km else Path(rel).stem
        own = tuple(
            sorted(s for s, body in specs.items() if re.search(rf"\b{re.escape(cls)}\b", body))
        )

        for i, line in enumerate(lines):
            rm = _ROUTE_RE.match(line)
            if not rm:
                continue
            handler = _find_handler(lines, i, decorator_end=rm.end())
            if not handler:
                unpaired.append(f"{rel}:{i + 1}: {line.strip()}")
                continue
            hits = tuple(s for s in own if re.search(rf"\b{re.escape(handler)}\b", specs[s]))
            sub = (rm.group(2) or "").strip("/")
            endpoints.append(
                Endpoint(
                    method=rm.group(1).upper(),
                    path="/" + "/".join(p for p in (prefix, sub) if p),
                    handler=handler,
                    controller=rel,
                    cls=cls,
                    own_specs=own,
                    specs=hits,
                )
            )
    return endpoints, unpaired


def extract_be_endpoints(repo: Path | None = None) -> tuple[list[Endpoint], list[str]]:
    """Every backend route in the working tree. Returns ``(endpoints, unpaired)``."""
    src = (repo or be_repo()) / "src"
    controllers = {
        p.relative_to(src).as_posix(): p.read_text(encoding="utf-8")
        for p in src.rglob("*.controller.ts")
        if not p.name.endswith(".spec.ts")
    }
    specs = {
        p.relative_to(src).as_posix(): p.read_text(encoding="utf-8") for p in src.rglob("*.spec.ts")
    }
    return extract_be_endpoints_from(controllers, specs)


# ── QA extraction ───────────────────────────────────────────────────────────

_CONST_RE = re.compile(r"^(_[A-Z][A-Z0-9_]*)\s*=\s*f?[\"']([^\"']+)[\"']", re.M)
_CLASS_CONST_RE = re.compile(r"^\s{4}([A-Z][A-Z0-9_]*)\s*=\s*f?[\"']([^\"']*)[\"']", re.M)
_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)", re.M)
# First argument: a quoted path OR a bare identifier (optionally self./Cls. prefixed).
_CALL_RE = re.compile(
    r"self\.(get|post|patch|put|delete)\(\s*\n?\s*"
    r"(?:(?P<q>f?)[\"'](?P<lit>[^\"']*)[\"']|(?P<ident>(?:self\.|[A-Za-z_]\w*\.)?[A-Za-z_]\w*))"
)


def _resolve(raw: str, consts: dict[str, str]) -> str:
    out = raw
    for _ in range(4):  # constants may reference constants
        before = out
        for name, value in consts.items():
            out = out.replace("{" + name + "}", value)
        if out == before:
            break
    return re.sub(r"\{[^}]+\}", "*", out)


def extract_qa_calls(clients_dir: Path | None = None) -> tuple[list[QaCall], list[str]]:
    """Every HTTP call the clients make. Returns ``(calls, unresolved)``."""
    clients_dir = clients_dir or CLIENTS_DIR
    files = sorted(clients_dir.rglob("*.py"))

    # auth_base.py calls self.LOGIN_PATH / self.ME_PATH — abstract constants each SUBCLASS
    # fills in. So one name legitimately has SEVERAL values:
    #     AuthClient.LOGIN_PATH        = /sa-auth-api/sign-in/credentials
    #     PartnerAuthClient.LOGIN_PATH = /sa-partners-api/v1/partner/auth/login
    # An earlier version kept one value per name in a flat map. Whichever file sorted last
    # won, so every base-class call was attributed to that service and the other showed
    # ZERO coverage — sa-auth-api read as untested when the SA login is exercised
    # constantly. Keep every value and emit one call per value: the base method really is
    # invoked on both subclasses.
    shared: dict[str, set[str]] = defaultdict(set)
    for path in files:
        text = path.read_text(encoding="utf-8")
        for name, value in _CONST_RE.findall(text) + _CLASS_CONST_RE.findall(text):
            if value:
                shared[name].add(value)

    calls: list[QaCall] = []
    unresolved: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        local: dict[str, str] = dict(_CONST_RE.findall(text))
        local.update(dict(_CLASS_CONST_RE.findall(text)))
        local = {k: v for k, v in local.items() if v}
        defs = [(m.start(), m.group(1)) for m in _DEF_RE.finditer(text)]

        for m in _CALL_RE.finditer(text):
            if m.group("lit") is not None:
                raw = m.group("lit")
                candidates = [_resolve(raw, local)]
            else:
                raw = m.group("ident")
                key = raw.split(".")[-1]
                if key in local:  # a file-local definition is unambiguous
                    values = {local[key]}
                elif key in shared:  # abstract constant: every subclass's value counts
                    values = shared[key]
                else:
                    unresolved.append(f"{path.name}: {raw}")
                    continue
                candidates = [_resolve(v, local) for v in sorted(values)]

            enclosing = ""
            for pos, name in defs:  # the last def that starts before this call
                if pos < m.start():
                    enclosing = name
                else:
                    break
            for resolved in candidates:
                if resolved.startswith("/"):
                    calls.append(
                        QaCall(
                            method=m.group(1).upper(),
                            path=resolved,
                            client=path.name,
                            func=enclosing,
                        )
                    )
    return calls, unresolved


# ── TC mapping ──────────────────────────────────────────────────────────────


def extract_tc_client_calls(tests_dir: Path | None = None) -> dict[str, set[tuple[str, str]]]:
    """``{test_func: {(client_file, client_method), ...}}`` for every API test.

    Text-scanned rather than AST-walked so a test that builds a call inside a helper or a
    loop is still seen; the cost is that a method named in a comment counts too, which
    over-reports rather than under-reports.
    """
    tests_dir = tests_dir or TESTS_DIR
    fixtures = "|".join(re.escape(f) for f in FIXTURE_CLIENTS)
    call_re = re.compile(rf"\b({fixtures})\.(\w+)\(")
    func_re = re.compile(r"^\s*async def (test_\w+)", re.M)

    out: dict[str, set[tuple[str, str]]] = {}
    for path in sorted(tests_dir.rglob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        marks = [(m.start(), m.group(1)) for m in func_re.finditer(text)]
        if not marks:
            continue
        bounds = [
            (name, start, marks[i + 1][0] if i + 1 < len(marks) else len(text))
            for i, (start, name) in enumerate(marks)
        ]
        for name, start, end in bounds:
            hits = {(FIXTURE_CLIENTS[fix], meth) for fix, meth in call_re.findall(text[start:end])}
            if hits:
                out.setdefault(name, set()).update(hits)
    return out


def _tc_ids_by_func() -> dict[str, str]:
    """``{test_func: tc_id}`` from the registry; empty when it cannot be imported."""
    try:
        from runner.tc_registry import TC_REGISTRY
    except Exception:  # noqa: BLE001 — the map is a convenience, never a hard dependency
        return {}
    return {tc.test_func: str(tc_id) for tc_id, tc in TC_REGISTRY.items()}


# ── Join ────────────────────────────────────────────────────────────────────

QUADRANTS = ("BOTH", "BE ONLY", "QA ONLY", "NEITHER")


def build_coverage(repo: Path | None = None) -> Coverage:
    """Extract both sides, join them, and map each endpoint to the TCs that hit it."""
    endpoints, _unpaired = extract_be_endpoints(repo)
    qa_calls, _unresolved = extract_qa_calls()

    qa_keys = {c.key for c in qa_calls if c.path.startswith(SERVICE_PREFIX)}
    quadrants: dict[str, list[Endpoint]] = {q: [] for q in QUADRANTS}
    for ep in endpoints:
        has_api = ep.key in qa_keys
        if ep.unit_tested and has_api:
            quadrants["BOTH"].append(ep)
        elif ep.unit_tested:
            quadrants["BE ONLY"].append(ep)
        elif has_api:
            quadrants["QA ONLY"].append(ep)
        else:
            quadrants["NEITHER"].append(ep)

    # endpoint -> TC ids, via (client, method) -> endpoint
    method_endpoints: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for c in qa_calls:
        method_endpoints[(c.client, c.func)].add(c.key)

    tc_ids = _tc_ids_by_func()
    endpoint_tcs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for func, pairs in extract_tc_client_calls().items():
        label = tc_ids.get(func, func)
        for pair in pairs:
            for key in method_endpoints.get(pair, ()):
                endpoint_tcs[key].add(label)

    return Coverage(
        endpoints=endpoints,
        qa_calls=qa_calls,
        quadrants=quadrants,
        endpoint_tcs={k: sorted(v) for k, v in endpoint_tcs.items()},
    )


# ── Report ──────────────────────────────────────────────────────────────────

_BUCKETS: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "Commissions — money moves here",
        "HIGH",
        re.compile(r"/commissions"),
        "Approving, paying out, clawing back and disputing commission.",
    ),
    (
        "Bank accounts — payout details",
        "HIGH",
        re.compile(r"/bank-accounts"),
        "Account and routing numbers.",
    ),
    (
        "Security controls",
        "MEDIUM",
        re.compile(r"/mfa/disable|/unlock"),
        "Turning 2FA off and unlocking a locked-out account.",
    ),
    (
        "Reads / stats / lookups",
        "LOW",
        re.compile(r"/stats|/plans|/countries|link-tenant|assign-tenant"),
        "Read-only or wiring endpoints. Lower blast radius, still unproven.",
    ),
    (
        "Internal ops",
        "LOWEST",
        re.compile(r"/admin/migrations"),
        "One-off migration triggers. Operator-run, not customer-facing.",
    ),
]


def _bucket(path: str) -> str:
    for name, _sev, rx, _why in _BUCKETS:
        if rx.search(path):
            return name
    return "Other"


def _table(rows: list[Endpoint], tcs: dict[tuple[str, str], list[str]]) -> str:
    out = ["| Method | Path | Handler | TCs |", "|---|---|---|---|"]
    for ep in sorted(rows, key=lambda e: (e.path, e.method)):
        hit = ", ".join(tcs.get(ep.key, [])) or "—"
        out.append(f"| `{ep.method}` | `{ep.path}` | `{ep.handler}` | {hit} |")
    return "\n".join(out)


def render_markdown(
    cov: Coverage,
    *,
    measured: str,
    unpaired: list[str] | None = None,
    unresolved: list[str] | None = None,
    stale: str | None = None,
) -> str:
    """The coverage-map body.

    *measured* is passed in so the caller owns the clock. *unpaired* and *unresolved* are
    the extraction losses; they belong IN the map rather than only on the console, because
    a route the parser dropped reads here as "covered" and the reader has no other way to
    know the numbers are short. *stale* is the same argument one level up: a map built from
    an unpulled clone is wrong for as long as the file exists, and the console line saying so
    scrolls away in a minute.
    """
    repo = be_repo()
    sha, be_date = be_head(repo)
    branch = be_branch(repo)
    n = {q: len(cov.quadrants.get(q, [])) for q in QUADRANTS}
    total = len(cov.endpoints)
    spec_files = len(list((repo / "src").rglob("*.spec.ts")))
    no_spec = sorted({ep.controller for ep in cov.endpoints if not ep.own_specs})
    lost = list(unpaired or [])
    unread = sorted(set(unresolved or []))

    md = f"""# Backend unit tests vs QA API tests — coverage map

Where the two suites overlap, where only one of them covers an endpoint, and where
**neither** does. Covers the `sa-partners-api` service only.

Generated by `python -m utils.be_coverage` — a snapshot, never edited by hand. Each run
writes a new dated file beside this one, so the folder shows how these numbers moved.

| | |
|---|---|
| Backend repo | `blazeupai/blazeup-microservice-sa-partners` |
| Branch / commit | `{branch}` @ `{sha}` ({be_date}) |
| Backend spec files | {spec_files} |
| Measured | {measured} |
| Routes parsed | {total}, {len(lost)} unpaired |
| Client paths | {len(cov.qa_calls)} resolved, {len(unread)} unresolved |
{
        ""
        if not stale
        else f"\n> **Read from an out-of-date clone.** {stale.removeprefix('WARNING: ')}\n"
        "> Every number below describes an older commit than the one the backend has shipped.\n"
    }{
        ""
        if not lost and not unread
        else "\n> **The numbers below are short.** Whatever the extractor dropped is missing "
        "from the counts, and a dropped route reads as *covered*. Details at the end.\n"
    }
---

## Result

Joined on endpoint (HTTP method + path). Backend exposes **{total} routes**.

| Quadrant | Endpoints | % | Meaning |
|---|---:|---:|---|
| **BOTH** | {n["BOTH"]} | {round(100 * n["BOTH"] / total)}% | unit test **and** QA API test |
| **BE ONLY** | {n["BE ONLY"]} | {
        round(100 * n["BE ONLY"] / total)
    }% | unit test only — the DB is mocked, so nothing proves it works wired up |
| **QA ONLY** | {n["QA ONLY"]} | {
        round(100 * n["QA ONLY"] / total)
    }% | **QA is the only safety net** |
| **NEITHER** | {n["NEITHER"]} | {
        round(100 * n["NEITHER"] / total)
    }% | **nobody tests the HTTP entry point** |

---

## What this measures — and what it does not

The signal is **controller-level**: does a spec that tests this controller class also name
this handler?

An endpoint in NEITHER does **not** mean its logic was never tested. Example:
`POST /v1/sa/commissions/:id/approve` has no controller spec, but the service spec
(`commissions.service.spec.ts`) holds tests for the logic underneath.

Say it precisely when raising this with BE:

> "No test exercises the **HTTP entry point** — so the guard, the DTO validation, the
> status code and the authorization path are unverified."

Not "this endpoint is untested" — that is refutable by pointing at the service spec.

---

## NEITHER — {n["NEITHER"]} endpoints nobody tests

"""
    by_bucket: dict[str, list[Endpoint]] = defaultdict(list)
    for ep in cov.quadrants.get("NEITHER", []):
        by_bucket[_bucket(ep.path)].append(ep)
    for name, sev, _rx, why in _BUCKETS:
        rows = by_bucket.get(name, [])
        if rows:
            md += f"### {name} — {sev} ({len(rows)})\n\n{why}\n\n"
            md += _table(rows, cov.endpoint_tcs) + "\n\n"
    if by_bucket.get("Other"):
        md += f"### Other ({len(by_bucket['Other'])})\n\n"
        md += _table(by_bucket["Other"], cov.endpoint_tcs) + "\n\n"

    md += f"""---

## QA ONLY — {n["QA ONLY"]} endpoints where QA is the only cover

Skipping or deleting one of these TCs leaves the endpoint with **no test at all**. Treat
this list as protected.

{_table(cov.quadrants.get("QA ONLY", []), cov.endpoint_tcs)}

---

## BE ONLY — {n["BE ONLY"]} endpoints, candidates for an API TC

Unit tests here mock the database. They prove the logic; they do not prove the guard, the
DTO validation, the status code or the authorization path survive being wired together.

{_table(cov.quadrants.get("BE ONLY", []), cov.endpoint_tcs)}

---

## BOTH — {n["BOTH"]} endpoints covered on both sides

{_table(cov.quadrants.get("BOTH", []), cov.endpoint_tcs)}

---

## Controllers with no dedicated spec file

{chr(10).join(f"- `{c}` — {sum(1 for e in cov.endpoints if e.controller == c)} endpoints" for c in no_spec)}

Spec files are **not** named after their controllers — `partners.sa.controller.ts` is
tested by `partners.controller.spec.ts`. This map joins on the controller **class name**;
joining on file name under-reports coverage.

---

## Limits

* Changes inside `@blazeupai/blazeup-global-common` and `@blazeupai/hr-os-global-factory`
  are invisible here — those live in other repos. That matters: the shared
  `Method.findById` is what raises `BadRequestException` for a missing document, the root
  cause behind the ghost-id 400-vs-404 bug family.
* Cron jobs and Kafka consumers have no HTTP surface, so they are out of scope.
* A TC listed against an endpoint means the test calls a client method that hits it — not
  that the TC's assertions are about that endpoint.
"""
    if lost or unread:
        md += "\n## Extraction losses\n\nEverything here is missing from the counts above.\n"
        if lost:
            md += f"\n**{len(lost)} route(s) the parser could not pair to a handler:**\n\n"
            md += "\n".join(f"- `{x}`" for x in lost[:20]) + "\n"
        if unread:
            md += f"\n**{len(unread)} client call(s) whose path could not be resolved:**\n\n"
            md += "\n".join(f"- `{x}`" for x in unread[:20]) + "\n"
    return md


def main(argv: list[str] | None = None) -> int:
    """Write a dated coverage map; print the quadrant counts.

    Deliberately NOT wrapped in ``logged_run``: the map already contains everything the
    console prints and more, so a second archived file per run was pure duplication. The
    extraction losses moved INTO the map for the same reason — they were the one thing the
    console had that the map did not.
    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--check-remote",
        action="store_true",
        help="git fetch the clone first, so the staleness warning is current",
    )
    args = ap.parse_args(argv)

    # The other three tools already do this. This one got away with it until the staleness
    # warning became the first console line here to contain a non-ASCII character.
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(Exception):
            stream.reconfigure(encoding="utf-8")

    stamp = datetime.now()
    sha, be_date = be_head()
    print(f"\nBackend : {be_branch()} @ {sha} ({be_date})")
    stale = staleness_warning(fetch=args.check_remote)
    print(f"{stale}\n" if stale else "")

    endpoints, unpaired = extract_be_endpoints()
    _calls, unresolved = extract_qa_calls()
    cov = build_coverage()

    print(f"backend endpoints : {len(endpoints)}")
    if unpaired:
        print(f"  UNPAIRED routes : {len(unpaired)}  <-- parser lost these, counts are short")
    if unresolved:
        print(f"  unresolved client paths : {len(set(unresolved))}")
    for q in QUADRANTS:
        print(f"  {q:9} {len(cov.quadrants[q]):4}")

    # Dated, not a fixed BE_COVERAGE_MAP.md: an always-current file cannot answer
    # "when did that number move", which is the question that actually comes up.
    TOOL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = TOOL_LOG_DIR / f"{stamp:%Y%m%d-%H%M%S}_be_coverage_map.md"
    report.write_text(
        render_markdown(
            cov,
            measured=f"{stamp:%Y-%m-%d %H:%M:%S}",
            unpaired=unpaired,
            unresolved=unresolved,
            stale=stale,
        ),
        encoding="utf-8",
    )
    print(f"\nmap -> {rel(report)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
