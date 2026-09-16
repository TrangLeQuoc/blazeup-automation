"""The extraction and join behind the backend coverage map.

Everything here feeds two decisions a human then acts on — "nobody tests this endpoint"
and "re-run these TCs" — so a parser that silently drops routes is worse than one that
crashes: a dropped route reports as *covered*.

Both bugs pinned below were real, measured 2026-08-12 while building the map:

* A single regex paired only 45 of 101 route decorators to their handler, because
  ``@ApiBody({ examples: { ... } })`` spans 40+ lines between the decorator and the method.
* The client-side reader saw only quoted path literals, so every
  ``self.get(_PARTNERS_PATH, ...)`` call was invisible and ``/v1/partner/auth/me`` was
  filed as untested by QA.

No backend clone and no network needed: the functions take source text, so the fixtures
below are hand-written TypeScript snippets.
"""

import re

import pytest

from utils import be_coverage
from utils.be_coverage import (
    QUADRANTS,
    Endpoint,
    extract_be_endpoints_from,
    extract_qa_calls,
    normalise,
)

# ── normalise ────────────────────────────────────────────────────────────────
# The join key. Both sides must reduce to the same string or every endpoint looks
# uncovered.


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # backend shape: no service prefix, :param
        ("/v1/sa/partners/:id/approve", "/v1/sa/partners/*/approve"),
        ("/v1/sa/partners", "/v1/sa/partners"),
        # client shape: service prefix, {param}
        ("/sa-partners-api/v1/sa/partners/{partner_id}/approve", "/v1/sa/partners/*/approve"),
        ("/sa-partners-api/v1/sa/partners", "/v1/sa/partners"),
        # several params, mixed styles — only the params collapse, the literal segments stay
        (
            "/v1/sa/partner-users/:userId/certifications/:type",
            "/v1/sa/partner-users/*/certifications/*",
        ),
        ("/sa-partners-api/v1/x/{a}/y/{b}", "/v1/x/*/y/*"),
        # tolerate stray slashes
        ("v1/sa/partners/", "/v1/sa/partners"),
    ],
)
def test_normalise(raw, expected):
    assert normalise(raw) == expected


def test_backend_and_client_forms_of_one_endpoint_agree():
    """The whole join rests on this."""
    be = normalise("/v1/sa/deals/:id/approve")
    qa = normalise("/sa-partners-api/v1/sa/deals/{deal_id}/approve")
    assert be == qa, f"{be!r} != {qa!r} — every endpoint would read as uncovered"


def test_a_different_endpoint_does_not_collide():
    assert normalise("/v1/sa/deals/:id/approve") != normalise("/v1/sa/deals/:id/reject")


# ── route -> handler pairing ─────────────────────────────────────────────────

SIMPLE = """
@Controller('v1/sa/partners')
export class PartnersSaController {
  @Post()
  async create(@Body() dto: CreatePartnerDto) {}

  @Get(':id')
  async findById(@Param('id') id: string) {}
}
"""

# The shape that broke the first parser: a multi-line decorator with nested objects
# sitting between the route decorator and the handler.
MULTILINE_DECORATOR = """
@Controller('v1/partner/portal')
export class BankAccountsController {
  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Add a payout account' })
  @ApiBody({
    type: AddBankAccountDto,
    examples: {
      usBankTransfer: {
        summary: 'US domestic',
        value: {
          label: 'Acme USD operating',
          countryCode: 'US',
        },
      },
    },
  })
  async addBankAccount(@Body() dto: AddBankAccountDto) {}
}
"""

WITH_COMMENTS = """
@Controller('v1/sa/deals')
export class DealsSaController {
  @Post(':id/approve')
  /**
   * Approve a registered deal.
   * @param id Deal identifier.
   */
  // a stray line comment too
  async approve(@Param('id') id: string) {}
}
"""


def _endpoints(source: str, specs: dict[str, str] | None = None) -> list[Endpoint]:
    eps, unpaired = extract_be_endpoints_from({"x.controller.ts": source}, specs or {})
    assert not unpaired, f"failed to pair a route to its handler: {unpaired}"
    return eps


def test_simple_controller():
    eps = _endpoints(SIMPLE)
    assert [(e.method, e.path, e.handler) for e in eps] == [
        ("POST", "/v1/sa/partners", "create"),
        ("GET", "/v1/sa/partners/:id", "findById"),
    ]


def test_multi_line_decorator_between_route_and_handler():
    """The 45-of-101 bug: nested decorator objects must not hide the handler."""
    eps = _endpoints(MULTILINE_DECORATOR)
    assert [(e.method, e.path, e.handler) for e in eps] == [
        ("POST", "/v1/partner/portal/bank-accounts".replace("/bank-accounts", ""), "addBankAccount")
    ]


def test_jsdoc_and_line_comments_are_skipped():
    eps = _endpoints(WITH_COMMENTS)
    assert [(e.method, e.path, e.handler) for e in eps] == [
        ("POST", "/v1/sa/deals/:id/approve", "approve")
    ]


def test_every_verb_is_recognised():
    src = """
@Controller('v1/x')
export class XController {
  @Get() async a() {}
  @Post() async b() {}
  @Patch() async c() {}
  @Put() async d() {}
  @Delete() async e() {}
}
"""
    assert {e.method for e in _endpoints(src)} == {"GET", "POST", "PATCH", "PUT", "DELETE"}


def test_an_unpairable_route_is_reported_not_dropped():
    """Silence here would report the route as covered. It must surface instead."""
    broken = """
@Controller('v1/x')
export class XController {
  @Get(':id')
   = notAMethodSignature
}
"""
    eps, unpaired = extract_be_endpoints_from({"x.controller.ts": broken}, {})
    assert eps == []
    assert len(unpaired) == 1 and "@Get(':id')" in unpaired[0]


# ── unit-test detection ──────────────────────────────────────────────────────
# The spec must be matched by the controller CLASS name: spec files are not named after
# their controllers (partners.sa.controller.ts is tested by partners.controller.spec.ts).


def test_handler_is_covered_when_its_controller_spec_names_it():
    specs = {"partners.controller.spec.ts": "describe('PartnersSaController', () => { create() })"}
    eps = _endpoints(SIMPLE, specs)
    by_handler = {e.handler: e for e in eps}
    assert by_handler["create"].unit_tested is True
    assert by_handler["findById"].unit_tested is False, "only `create` is named in the spec"


def test_a_spec_for_a_different_controller_does_not_count():
    """`create` is a common name — a spec for another class must not grant coverage."""
    specs = {"other.controller.spec.ts": "describe('OtherController', () => { create() })"}
    eps = _endpoints(SIMPLE, specs)
    assert all(e.unit_tested is False for e in eps)
    assert all(e.own_specs == () for e in eps)


def test_own_specs_records_which_spec_tests_the_class():
    specs = {"partners.controller.spec.ts": "PartnersSaController"}
    eps = _endpoints(SIMPLE, specs)
    assert eps[0].own_specs == ("partners.controller.spec.ts",)


# ── quadrant names ───────────────────────────────────────────────────────────


def test_quadrant_names_are_stable():
    """The report and the drift tool both key off these; renaming one breaks the other."""
    assert QUADRANTS == ("BOTH", "BE ONLY", "QA ONLY", "NEITHER")


# ── client path extraction ───────────────────────────────────────────────────
# The QA half of the join. Under-reading here reports a tested endpoint as untested.


def _clients(tmp_path, files: dict[str, str]):
    root = tmp_path / "api_clients"
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return extract_qa_calls(root)


def test_literal_f_string_and_bare_constant_are_all_read(tmp_path):
    """Three call shapes exist; reading only literals lost a quarter of QA coverage."""
    calls, unresolved = _clients(
        tmp_path,
        {
            "c.py": """
_BASE = "/svc-api/v1/things"

class C:
    async def list_all(self):
        return await self.get(_BASE)

    async def one(self, thing_id):
        return await self.get(f"{_BASE}/{thing_id}")

    async def literal(self):
        return await self.get("/svc-api/v1/other")
"""
        },
    )
    assert unresolved == []
    assert {(c.method, c.path) for c in calls} == {
        ("GET", "/svc-api/v1/things"),
        ("GET", "/svc-api/v1/things/*"),
        ("GET", "/svc-api/v1/other"),
    }


def test_the_calling_method_is_recorded(tmp_path):
    """The TC map joins through it: test -> client method -> endpoint."""
    calls, _ = _clients(
        tmp_path,
        {
            "c.py": """
class C:
    async def approve_thing(self, thing_id):
        return await self.post(f"/svc-api/v1/things/{thing_id}/approve")
"""
        },
    )
    assert [(c.func, c.path) for c in calls] == [("approve_thing", "/svc-api/v1/things/*/approve")]


def test_one_abstract_constant_with_two_subclass_values_yields_both(tmp_path):
    """A base class calls self.LOGIN_PATH; each subclass fills it with its own service.

    Keeping a single value per NAME let whichever file sorted last win, so every
    base-class call was attributed to that one service and the other reported ZERO
    coverage — sa-auth-api read as untested while the SA login runs in every session.
    """
    calls, unresolved = _clients(
        tmp_path,
        {
            "auth_base.py": """
class BaseAuthClient:
    LOGIN_PATH: str = ""

    async def login(self):
        return await self.post(self.LOGIN_PATH)
""",
            "admin/auth_client.py": """
class AuthClient(BaseAuthClient):
    LOGIN_PATH = "/sa-auth-api/sign-in/credentials"
""",
            "partner/auth_client.py": """
class PartnerAuthClient(BaseAuthClient):
    LOGIN_PATH = "/sa-partners-api/v1/partner/auth/login"
""",
        },
    )
    assert unresolved == []
    assert {c.path for c in calls} == {
        "/sa-auth-api/sign-in/credentials",
        "/sa-partners-api/v1/partner/auth/login",
    }, "both subclasses' paths must survive — the base method runs on both"


def test_a_file_local_constant_beats_the_package_wide_one(tmp_path):
    """A name defined in the calling file is unambiguous; do not fan it out."""
    calls, _ = _clients(
        tmp_path,
        {
            "a.py": """
class A:
    PATH = "/a-api/v1/thing"

    async def go(self):
        return await self.get(self.PATH)
""",
            "b.py": """
class B:
    PATH = "/b-api/v1/thing"
""",
        },
    )
    assert {c.path for c in calls} == {"/a-api/v1/thing"}


def test_an_unresolvable_name_is_reported_not_dropped(tmp_path):
    calls, unresolved = _clients(
        tmp_path,
        {
            "c.py": """
class C:
    async def go(self):
        return await self.get(self.MYSTERY_PATH)
"""
        },
    )
    assert calls == []
    assert len(unresolved) == 1 and "MYSTERY_PATH" in unresolved[0]


# ── run logs ─────────────────────────────────────────────────────────────────
# Every backend tool archives its output under docs/blazeup/tools/BE/. Two properties
# matter: the output still reaches the terminal live (a two-minute tool that prints
# nothing until it finishes reads as a hang), and the file records the exact command,
# because the same tool with different flags produces very different reports.


def test_output_is_both_printed_and_written(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(be_coverage, "TOOL_LOG_DIR", tmp_path / "BE")
    with be_coverage.logged_run("be_coverage"):
        print("backend endpoints : 101")

    printed = capsys.readouterr().out
    assert "backend endpoints : 101" in printed, "the terminal must still show the report"

    logs = list((tmp_path / "BE").glob("*_be_coverage.md"))
    assert len(logs) == 1
    assert "backend endpoints : 101" in logs[0].read_text(encoding="utf-8")


def test_the_log_records_the_command_line(tmp_path, monkeypatch):
    monkeypatch.setattr(be_coverage, "TOOL_LOG_DIR", tmp_path / "BE")
    with be_coverage.logged_run("be_unit_audit", ["--check", "A"]):
        print("findings")

    body = next((tmp_path / "BE").glob("*.md")).read_text(encoding="utf-8")
    assert "python -m utils.be_unit_audit --check A" in body


def test_the_file_name_sorts_chronologically(tmp_path, monkeypatch):
    """Named YYYYMMDD-HHMMSS_<tool> so `ls` is already in run order."""
    monkeypatch.setattr(be_coverage, "TOOL_LOG_DIR", tmp_path / "BE")
    with be_coverage.logged_run("be_coverage"):
        print("x")
    name = next((tmp_path / "BE").glob("*.md")).name
    assert re.fullmatch(r"\d{8}-\d{6}_be_coverage\.md", name), name


def test_a_crash_still_leaves_the_log(tmp_path, monkeypatch):
    """The output up to the failure is the most useful log there is — do not lose it."""
    monkeypatch.setattr(be_coverage, "TOOL_LOG_DIR", tmp_path / "BE")
    with pytest.raises(RuntimeError), be_coverage.logged_run("be_coverage"):
        print("got this far")
        raise RuntimeError("boom")

    body = next((tmp_path / "BE").glob("*.md")).read_text(encoding="utf-8")
    assert "got this far" in body


# ── locating the backend clone ───────────────────────────────────────────────
# A wrong or missing path must ERROR. Returning an empty endpoint list instead would read
# as "the backend has no routes", i.e. "everything is covered" — a silent wrong answer.


@pytest.fixture
def fake_be(tmp_path, monkeypatch):
    """A directory that looks like the backend repo, plus an empty .env by default."""
    repo = tmp_path / "backend"
    (repo / "src").mkdir(parents=True)
    env = tmp_path / ".env"
    env.write_text("API_BASE_URL=https://example.invalid\n", encoding="utf-8")
    monkeypatch.setattr(be_coverage, "ENV_FILE", env)
    monkeypatch.delenv(be_coverage.ENV_KEY, raising=False)
    return repo, env


def test_env_var_is_used(fake_be, monkeypatch):
    repo, _env = fake_be
    monkeypatch.setenv(be_coverage.ENV_KEY, str(repo))
    assert be_coverage.be_repo() == repo


def test_env_file_is_used_when_the_variable_is_absent(fake_be):
    repo, env = fake_be
    env.write_text(f'{be_coverage.ENV_KEY}="{repo}"\n', encoding="utf-8")
    assert be_coverage.be_repo() == repo


def test_env_var_wins_over_the_env_file(fake_be, tmp_path, monkeypatch):
    """So a one-off run or CI can override the per-machine path in .env."""
    repo, env = fake_be
    other = tmp_path / "other"
    (other / "src").mkdir(parents=True)
    env.write_text(f'{be_coverage.ENV_KEY}="{other}"\n', encoding="utf-8")
    monkeypatch.setenv(be_coverage.ENV_KEY, str(repo))
    assert be_coverage.be_repo() == repo


def test_a_commented_out_entry_does_not_count(fake_be):
    _repo, env = fake_be
    env.write_text(f"# {be_coverage.ENV_KEY}=/somewhere\n", encoding="utf-8")
    with pytest.raises(SystemExit, match=be_coverage.ENV_KEY):
        be_coverage.be_repo()


def test_an_empty_entry_does_not_count(fake_be):
    _repo, env = fake_be
    env.write_text(f"{be_coverage.ENV_KEY}=\n", encoding="utf-8")
    with pytest.raises(SystemExit, match=be_coverage.ENV_KEY):
        be_coverage.be_repo()


def test_nothing_set_explains_both_ways_to_set_it(fake_be):
    with pytest.raises(SystemExit) as err:
        be_coverage.be_repo()
    message = str(err.value)
    assert ".env" in message and "export" in message, message


def test_a_path_that_is_not_the_backend_repo_is_rejected(fake_be, tmp_path, monkeypatch):
    """The dangerous case: a real directory with no src/ would extract zero endpoints."""
    monkeypatch.setenv(be_coverage.ENV_KEY, str(tmp_path / "not-the-repo"))
    with pytest.raises(SystemExit, match="has no src/"):
        be_coverage.be_repo()
