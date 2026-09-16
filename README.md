# BlazeUp Automation Framework

pytest + Playwright async automation framework for the **BlazeUp Partner Platform** (SA/admin + partner actors under one `blazeup` domain, sharing one API gateway).

Covers both **HTTP API** (httpx + Pydantic) and **Browser UI** (Playwright async + Page Object Model) automation.

> **Full workflow, naming conventions, and troubleshooting** → **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)**

---

## Quick Start

### 1. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.13 | [python.org](https://python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Allure CLI | optional | `scoop install allure` / `brew install allure` |

### 2. Clone & Setup

```bash
git clone <repo-url>
cd blazeup_automation

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
python -m playwright install chromium
```

One `.env` file drives everything. Copy the template and fill it in:

```bash
cp .env.example config/blazeup/.env
```

```bash
# config/blazeup/.env
API_BASE_URL=https://api.stg.blazeup.ai       # shared gateway (both actors)

# Admin / SuperAdmin actor (SA endpoints /v1/sa/*)
ADMIN_BASE_URL=https://stgsa.blazeup.ai
ADMIN_EMAIL=your-sa-user@example.com
ADMIN_PASSWORD=your-password

# Partner actor (partner endpoints /v1/partner/*) — optional
PARTNER_BASE_URL=https://stgpartners.blazeup.ai
PARTNER_EMAIL=your-partner-user@example.com
PARTNER_PASSWORD=your-password

HEADLESS=true
BROWSER=chromium
DEFAULT_RESPONSE_TIME_MS=30000
```

> **Note:** the SA/admin actor and the partner actor are distinguished by
> `ADMIN_*` / `PARTNER_*` keys — not separate files. The generic settings aliases
> (`settings.base_url` / `test_email` / `test_password`) resolve to the `ADMIN_*`
> values, since most setup + SA tests run as the admin actor.

**Never commit `.env` files** — they are listed in `.gitignore`.

### 4. Run Tests

```bash
# Run the smoke suite
python -m runner.blazeup.run_test --mode smoke

# Run specific TC IDs / ranges
python -m runner.blazeup.run_test --execute 2061001 2061002
python -m runner.blazeup.run_test --execute 2060201-2060220

# List all registered TCs
python -m runner.blazeup.run_test --list
```

---

## Project Structure

```
blazeup_automation/
│
├── api_clients/                          # HTTP API clients (httpx + Pydantic)
│   ├── base_client.py                    #   Base: retry, timing, schema validation
│   ├── auth_base.py                      #   Shared login mechanics (BaseAuthClient)
│   └── blazeup/                          #   One domain, sub-split by actor surface
│       ├── admin/                        #   SA clients (/v1/sa/*)
│       │   ├── auth_client.py            #     SA login + current-user (sa-auth-api)
│       │   └── partner/                  #     SA-side partner-module clients
│       │       ├── sa_partners_client.py #       Partners, users, certs, territories, audit
│       │       └── sa_deals_client.py    #       Deal register / approve / pipeline
│       └── partner/                      #   Partner clients (/v1/partner/*)
│           ├── auth_client.py            #     Partner login (separate JWT issuer)
│           └── deal_registration_client.py  # Partner deal registration (SCAFFOLD)
│
├── config/                               # Settings
│   ├── settings.py                       #   Typed config from .env (Pydantic)
│   └── blazeup/
│       ├── config.yaml                   #   Modules, TC-ID numbering, services, excel map
│       └── .env                          #   API_BASE_URL + ADMIN_*/PARTNER_* credentials
│
├── docs/
│   ├── guides/                           #   Framework guides
│   │   ├── USER_GUIDE.md                 #     Full workflow & naming conventions
│   │   ├── add-domain.md                 #     Onboard a new test domain
│   │   ├── page-objects.md               #     Page object / locator / fixture conventions
│   │   ├── test-data.md                  #     Faker factories + cleanup conventions
│   │   └── test-organization.md          #     Test taxonomy: layers, naming, markers, e2e
│   ├── api-snapshots/blazeup/            #   Swagger baselines + CHANGELOG (drift detector)
│   │   └── be-commit.txt                 #     Backend commit this suite is reconciled to
│   └── blazeup/                          #   Partner Platform reference + test plan
│       ├── tools/BE/                     #     Dated output of the backend tools (see its README)
│       ├── Partner_Platform_Test_Plan.xlsx
│       ├── partner_product_backlog.vi.md
│       ├── partner_requirement.xlsx
│       └── partner-platform-prd-v1.8(.vi).md
│
├── locators/                             #   UI element selectors (Locators classes)
│   └── blazeup/
│       ├── admin/                        #   login / shell / dashboard locators
│       └── partner/                      #   partner-portal locators
│
├── pages/                                #   Page Object Model
│   ├── base_page.py                      #   Shared: goto, fill, click, wait_for_element
│   └── blazeup/
│       ├── admin/                        #   SA login (two-step) + shell + dashboard
│       └── partner/                      #   partner login + portal pages
│
├── pytest_support/
│   ├── fixtures.py                       #   All pytest fixtures
│   │                                      #   - authenticated_page / make_page (SA UI tests)
│   │                                      #   - partner_authenticated_page / make_partner_page (partner UI)
│   │                                      #   - api_token (session-scoped)
│   │                                      #   - auth_client / sa_*_client (API)
│   │                                      #   - created_resources (auto-cleanup)
│   └── hooks.py                          #   pytest_runtest_makereport hook
│
├── runner/                               #   Test execution & reporting
│   ├── run_test.py                       #   CLI entrypoint (modes, filters, repeat)
│   ├── test_runner.py                    #   Subprocess runner, summary, Excel export
│   ├── tc_registry.py                    #   AUTO-GENERATED: merged registry
│   └── blazeup/                          #   Domain entry points
│       ├── run_test.py                   #     Run tests
│       ├── registry.py                   #     Auto-gen: merges registry_modules/*
│       ├── registry_modules/             #     Auto-gen: one file per module (partner.py, …)
│       ├── health.py                     #     API service health-check
│       └── swagger_check.py              #     Swagger drift detector
│
├── tests/                                #   Test cases (layer / module)
│   └── blazeup/
│       ├── api/
│       │   └── partner/                  #   Partner module — one file per feature
│       │       └── test_sa_*.py          #     deals, partners, territories, certs, ...
│       └── ui/
│           ├── dashboard/                #   Dashboard module
│           └── shell/                    #   Shell module (page loads, load time)
│
├── utils/                                #   Shared utilities
│   ├── login_helpers.py                  #   Reusable: login_ui(), login_api()
│   ├── sync_registry.py                  #   Regenerates runner/*/registry.py from tests
│   ├── excel_reporter.py                 #   Exports results to Excel
│   ├── ai_triage.py                      #   AI failure triage → ai_triage.md
│   ├── data_factory.py                   #   Faker factories (make_user/tenant/partner/deal)
│   ├── helpers.py                        #   require_credentials
│   ├── log_helper.py                     #   Custom log levels: STEP, START, PASSED, FAILED
│   └── screenshot_on_fail.py             #   Allure screenshot attachment
│
├── .github/workflows/test.yml            #   CI: manual run + AI triage + dashboard + Telegram
├── conftest.py                           #   Pytest discovery entrypoint (imports fixtures)
├── pytest.ini                            #   Markers, asyncio mode, HTML/Allure paths
├── pyproject.toml                        #   Ruff lint + format config
├── .pre-commit-config.yaml               #   Local pre-commit hooks (ruff + registry sync)
├── requirements.txt                      #   Python dependencies (to run tests) — EDIT THIS
├── requirements.lock                      #   Generated: the 16 direct pins + 25 transitive
├── requirements-selftest.txt             #   Light set for selftests/ (no Playwright)
├── requirements-selftest.lock             #   Generated
├── requirements-dev.txt                  #   Dev tooling (ruff, pre-commit)
├── .gitignore                            #   Git ignore rules
├── .gitattributes                        #   Line ending & binary file rules
├── README.md                             #   ← you are here
└── .env.example                          #   Template (copy to config/blazeup/.env)
```

---

## Domain Architecture

One `blazeup` domain covers the whole Partner Platform. SA/admin and partner are
two **actors** inside it (not separate domains) — they share one API gateway and
one test suite; only the UI origin + credentials differ.

- **One registry** (`runner/blazeup/registry.py`, auto-generated by `utils/sync_registry.py`)
- **One CLI** (`python -m runner.blazeup.run_test`)
- **One `.env`** (`config/blazeup/.env`) with `ADMIN_*` + `PARTNER_*` keys

| Actor | UI origin | Endpoints | Credentials |
|-------|-----------|-----------|-------------|
| **Admin / SA** | `https://stgsa.blazeup.ai` | `/sa-partners-api/v1/sa/*` | `ADMIN_EMAIL` / `ADMIN_PASSWORD` |
| **Partner** | `https://stgpartners.blazeup.ai` | `/sa-partners-api/v1/partner/*` | `PARTNER_EMAIL` / `PARTNER_PASSWORD` |

> Partner-portal tests mint a throwaway partner from the SA side (create → approve →
> invite → log in), so they run as one self-contained test under the shared runner.
> Shared API gateway for both: `https://api.stg.blazeup.ai`.

---

## Test Numbering (TC IDs)

### New-Style (Structured)

For Partner Platform tests, TC IDs are auto-derived from function names:

```python
test_partner_ui_partner_portal_shell_001  →  TC 1010101
test_partner_ui_dashboard_001             →  TC 1010201
test_partner_api_auth_access_control_001  →  TC   10101  (API: no leading digit)
```

**Format**: `{type}{module:02d}{section:02d}{seq:02d}`
- **type**: 1=UI, 0=API
- **module**: 01=Partner, 02…=future domains
- **section**: 01-10 (UI), 01-17 (API) per module
- **seq**: 01-99 within section

**Stability**: IDs are stable — they're derived from the function name, not from test execution order.

---

## Key Commands

```bash
# Run tests
python -m runner.blazeup.run_test --list              # List all registered TCs
python -m runner.blazeup.run_test --dry-run           # Show execution plan
python -m runner.blazeup.run_test --mode smoke        # Run smoke-marked TCs
python -m runner.blazeup.run_test --mode regression   # Run P1 TCs
python -m runner.blazeup.run_test --execute 2061001   # Run a specific TC

# Direct pytest (for development)
python -m pytest tests/blazeup/ui/ -s -k test_partner_ui_partner_portal_shell_001
python -m pytest tests/ --co                          # Collect tests (show discovery)

# Skip the pre-run environment gate (it runs by default; exits 6 when staging is down)
python -m runner.blazeup.run_test --execute 2060101 --no-preflight

# Framework selftests (runner/registry logic + be_gap traceability; no staging, no browser, ~1s)
python -m pytest selftests/ -o addopts= --confcutdir=selftests -q

# Same selftests in a throwaway venv built from requirements-selftest.lock — what CI
# installs. Run before pushing a NEW selftest: your working env has the full
# requirements.txt, so a missing lock entry passes locally and only fails on push.
make selftest-ci

# Sync TC registry (after adding new test functions)
python utils/sync_registry.py

# Lint the Excel test plan (well-formed + in sync with code; read-only)
python utils/validate_test_plan.py            # --strict = warnings fail too
```

### Backend source cross-check

Needs a local clone of `blazeupai/blazeup-microservice-sa-partners` — no staging, no
secrets. Point `BLAZEUP_BE_REPO` at it, once, in `config/blazeup/.env`:

```
BLAZEUP_BE_REPO="C:/Users/you/Desktop/blazeup/blazeup-microservice-sa-partners"
```

An environment variable of the same name overrides it, for a one-off run or CI:

```bash
export BLAZEUP_BE_REPO="/c/Users/you/Desktop/blazeup/blazeup-microservice-sa-partners"
```

Leave it unset and nothing else changes — only these three commands use it.

| Command (no `make` on Windows) | What it answers |
|---|---|
| `make be-coverage`<br>`python -m utils.be_coverage` | Which of the backend's 101 endpoints have a BE unit test, a QA API test, both, or **neither** |
| `make be-drift`<br>`python -m utils.be_drift` | What changed in the backend since the recorded baseline → **which TCs to re-run**, plus any new endpoint with no TC |
| `make be-drift-save`<br>`python -m utils.be_drift --save` | Record the clone's HEAD as the new baseline, after reconciling a deploy |
| `make be-audit`<br>`python -m utils.be_unit_audit` | Are the backend's unit tests protecting anything? Four heuristics — not-found answered `400`, tests that assert what they stubbed, controller specs with no error path, guards no spec exercises |
| `python -m utils.be_test_blame --json <jest.json>` | Why is a backend unit test red: which commit introduced the difference, whether that commit updated the other specs but missed this one, and how long it has been red |

`be_test_blame` defaults to reading a saved `jest --json` file so it stays read-only over
the clone; `--run` lets it run their suite first (~2 min, writes nothing to their repo).
It needs a distinctive **string** in the diff — numeric-only failures, timeouts and
environment problems give the `git log -S` search nothing, and it says so rather than
guessing.

Every run archives its output to `docs/blazeup/tools/BE/YYYYMMDD-HHMMSS_<tool>.md` — the
coverage map included, so nothing is overwritten and the folder shows how the numbers
moved. `docs/blazeup/tools/BE/README.md` documents each command's purpose, input and
output.

`be-audit` reads **source only** — no Bug_Tracker lookup — so a brand-new API is audited
the same as an old one. It explains a real puzzle: the backend runs 1052 green unit tests
and none of them notices the ghost-id `400`-vs-`404` defects this suite has reported since
July. None of its findings proves a test is *wrong*; that needs the PRD and a person.

Run them from **this** repo, not the backend clone — they are modules here and need
`api_clients/` + `runner/tc_registry` to name the TCs. The backend clone is only input,
and is never written to.

A full pass after a backend deploy:

```powershell
cd <the path in BLAZEUP_BE_REPO>; git pull   # HEAD only moves on a pull; all four read files
cd <this repo>; python -m utils.be_drift
# run the TC list it prints, then:
python -m utils.be_drift --save
```

Substitute your own paths. Pull first or `be_drift` prints `Nothing to re-run.` — a false
all-clear, since an unpulled clone has no changes to find. It warns when the clone is behind
its upstream; `--check-remote` adds a `git fetch` (~3 s) so that warning is current.

This is a different axis from `make swagger`. Swagger drift compares the live OpenAPI spec
to a saved baseline, so it sees **contract** changes (paths, params, schemas) — it cannot
see a change that leaves the contract intact, and it says nothing about what is tested.

Why a baseline file rather than asking the service: `sa-partners-api` exposes no `/version`
endpoint and its deploy tag lives in a shared CI repo, so there is no way to ask staging
which commit it runs. `docs/api-snapshots/blazeup/be-commit.txt` is our own bookmark —
same pattern as the Swagger baseline. `utils/be_drift.record_baseline` is the one place to
change if a `/version` endpoint ever appears.

**Known blind spot:** changes inside `@blazeupai/blazeup-global-common` and
`@blazeupai/hr-os-global-factory` live in other repos and are invisible to the import
graph. That is not academic — the shared `Method.findById` raising `BadRequestException`
for a missing document is the root cause behind the ghost-id 400-vs-404 bug family.
`be-drift` flags it when either package version is bumped, but cannot map it to endpoints.

---

## Authentication

The framework provides two reusable login mechanisms via `utils/login_helpers.py`:

### UI Login
```python
from utils.login_helpers import login_ui

async def test_example(authenticated_page):
    # Already logged in via fixture
    await authenticated_page.goto("/dashboard")
```

### API Login
```python
from utils.login_helpers import login_api

async def test_api_example(api_token):
    # Token obtained from fixture (session-scoped — reused across tests)
    async with AuthClient(..., token=api_token) as client:
        await client.list_users()
```

---

## Output Artifacts

Each test run creates a timestamped folder:

```
results/run_YYYYMMDD_HHMMSS/
├── run_meta.json                        # TC IDs, timestamps, node IDs
├── logs/test.log                        # Full loguru log (grep-friendly)
├── screenshots/                         # Final + failure screenshots
├── videos/                              # Playwright video recordings
├── traces/                              # Playwright trace archives (.zip)
├── allure-results/                      # Raw Allure data
└── allure-report/                       # Generated static Allure HTML
```

### View Results
```bash
# Allure report
allure serve results/run_*/allure-results

# Logs (grep-friendly format)
grep "TC-" results/run_*/logs/test.log
```

---

## Development

### Add a New Test

1. Write a test function in `tests/blazeup/{layer}/*.py`:
   ```python
   async def test_partner_ui_partner_portal_shell_002(authenticated_page):
       """Description of what this test does."""
       await authenticated_page.goto("/dashboard")
       ...
   ```

2. Run the sync script:
   ```bash
   python utils/sync_registry.py
   ```
   This auto-generates `runner/blazeup/registry.py` with the new TC ID.

3. Run the test:
   ```bash
   python -m runner.blazeup.run_test --execute <TC_ID>
   ```

### Fixtures Available

| Fixture | Scope | Use When |
|---------|-------|----------|
| `settings` | session | Access typed config (BASE_URL, API_BASE_URL, etc.) |
| `result_dir` | session | Run artifact dir (`results/run_*`) + configures loguru sinks |
| `tc_logger` | function (autouse) | Emits per-TC START/PASSED/FAILED banners + binds the TC id to logs |
| `fake` | session | Faker instance for dynamic data generation |
| `test_user` | function | Generated user data dict |
| `created_resources` | function | Track created resources → auto-delete on teardown (CRUD tests) |
| **SA / stgsa UI** | | |
| `authenticated_page` | function | SA (stgsa) UI test — fresh UI login per test |
| `make_page` | function | Factory: build an SA page object — `make_page(ShellPage)` |
| `page` | function | UI test WITHOUT login (login-flow tests) |
| `browser_context` | function | Unauthenticated browser context (used by `page`) |
| **Partner / stgpartners UI** | | |
| `partner_auth_state` | session | Partner-portal login once → cached storage state |
| `partner_authenticated_page` | function | Partner-portal (stgpartners) UI test, pre-authenticated |
| `make_partner_page` | function | Factory: build a partner page object — `make_partner_page(PartnerShellPage)` |
| **API** | | |
| `api_token` | session | SA API test, already have a JWT token |
| `auth_client` | function | Authenticated `AuthClient` (SA auth) |
| `sa_partners_client` | function | Authenticated `SaPartnersClient` (sa-partners-api) |
| `sa_deals_client` | function | Authenticated `SaDealsClient` (SA deals) |
| `sa_commissions_client` | function | Authenticated `SaCommissionsClient` (SA commissions) |

> Data factories live in `utils/data_factory.py` (`make_user`, `make_tenant`, …).
> See **[docs/guides/test-data.md](docs/guides/test-data.md)** and **[docs/guides/page-objects.md](docs/guides/page-objects.md)**.

---

## Troubleshooting

### Playwright browser not found
```bash
python -m playwright install chromium
```

### Settings fail to load
Settings read `config/blazeup/.env`. If a required field is missing, `get_settings()`
fails fast. Copy the template and fill it in: `cp .env.example config/blazeup/.env`.

### Tests timeout
Increase `DEFAULT_RESPONSE_TIME_MS` in `.env`:
```env
DEFAULT_RESPONSE_TIME_MS=30000   # 30 seconds
```

### Login fails
- Verify `ADMIN_EMAIL` / `ADMIN_PASSWORD` (and `PARTNER_*` if used) in `config/blazeup/.env`
- Check that `ADMIN_BASE_URL` / `API_BASE_URL` are correct

---

## CI / CD

Two workflows under `.github/workflows/`:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `test.yml` | **manual** (workflow_dispatch) | Runs the actual test suites against staging (needs secrets + a live backend) |
| `validate-test-plan.yml` | **automatic** on every push / PR | Lints the Excel test plan — fast, no secrets, no services |
| `selftest.yml` | **automatic** on push / PR touching `runner/`, `utils/`, `selftests/`, `tests/`, `docs/blazeup/` | Tests the framework's own logic (TC registry, PASS/FAIL/BLOCKED classification), the `be_gap` traceability chain (code marker ↔ test-case docs ↔ Bug_Tracker) the layer boundaries (no raw Playwright selectors or API paths in tests; every client method pinned to its endpoint) and the shared-partner-session signal — no secrets, no staging, no browser |

### Test suite — `test.yml` (manual)

Runs **on manual dispatch only** (no push/schedule trigger). Start it from
**Actions → BlazeUp Automation Tests → Run workflow** (works from the GitHub Mobile
app), choosing:

| Input | Options | Notes |
|-------|---------|-------|
| `mode` | `smoke` / `regression` / `normal` | Ignored when `execute` is set |
| `execute` | e.g. `2061001 2061002` or `2060201-2060220` | Specific TC IDs / ranges |
| `suite` | `gate` (default) / `be_gap` / `all` | `gate` drops the known-red `be_gap` TCs so a red job means a **regression**; `be_gap` runs only those and never fails the job |
| `excel` | checkbox | Export Excel report |
| `ai_triage` | checkbox | Run AI failure triage |

Each run: `python -m runner.blazeup.run_test`, then on failure **AI-triages** the
log (`ai_triage.md`), publishes an **Allure trend dashboard** to GitHub Pages, and
sends a **Telegram** summary (+ triage file).

**Dashboard:** `https://<owner>.github.io/<repo>/blazeup/`.

### Test-plan validation — `validate-test-plan.yml` (automatic)

Runs on **every push / pull request** that touches the Excel plan, a generated
registry, or the validator itself. It reads the workbook + the committed TC registry
(only `openpyxl` needed — no secrets, no backend) and **fails the check** on a real
ERROR: bad enum, duplicate/mis-formatted `Test Case Name` id, a required cell left
empty, or an automated TC not flagged `Auto = YES`. Warnings don't fail the build.
To make it block merges: **Settings → Branch protection → require "Validate Test
Plan"**. Run it locally the same way: `python utils/validate_test_plan.py`.

### Required GitHub secrets

> Only `test.yml` needs secrets. `validate-test-plan.yml` needs none.

Secret names match the `.env` keys 1:1 (CI writes them straight to the environment):

| Secret | Purpose |
|--------|---------|
| `API_BASE_URL` | shared API gateway |
| `ADMIN_BASE_URL` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` | SA UI origin + login |
| `PARTNER_BASE_URL` / `PARTNER_EMAIL` / `PARTNER_PASSWORD` | Partner UI origin + login |
| `GROQ_API_KEY` | AI triage (Groq provider) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Telegram notifications |

> Store all of these as **Secrets** (not Variables) so credentials are masked in logs.

---

## Dependencies (locked)

`requirements.txt` is the file **you** edit — 16 direct pins with a comment on each.
The two `.lock` files are **generated** and hold the full resolved set (41 and 15
packages): the ~25 transitive dependencies that `requirements.txt` never mentions, and
that would otherwise install a different version on every CI run. A breaking release of
one of them (`pluggy`, `greenlet`, `anyio`, …) turns CI red on a day the diff is empty —
locking is what removes that failure mode.

CI installs the locks. After changing `requirements.txt`, regenerate and commit both:

```bash
make lock
# or, without make:
uv pip compile requirements.txt -o requirements.lock --python-platform linux --python-version 3.13 --no-header
uv pip compile requirements-selftest.txt -o requirements-selftest.lock --python-platform linux --python-version 3.13 --no-header
```

`--python-platform linux` matters: CI runs `ubuntu-latest`, so a lock resolved on
Windows without it can fail to install on the runner.

`requirements-selftest.txt` carries **no versions of its own** — it constrains against
`requirements.txt` (`-c requirements.txt`), so bumping a version in one place cannot
leave the selftest job pinned to the old one.

It is a **deliberately short list**, and that is also its trap: your working env has the
full `requirements.txt`, so a selftest importing something absent from this file passes
locally and fails on push. After adding a selftest that imports a new module, add the
package here, regenerate the lock, and verify with `make selftest-ci`.

---

## Code Quality (lint + format + pre-commit)

Ruff (lint + formatter) and pre-commit hooks keep the codebase consistent.

```bash
pip install -r requirements-dev.txt   # ruff + pre-commit
pre-commit install                     # enable git hooks (one-time per clone)

ruff check . --fix                     # lint + autofix
ruff format .                          # format
pre-commit run --all-files             # run all hooks manually
```

On every `git commit`, hooks auto-run `ruff` (lint + format), re-sync the TC
registry, and **lint the Excel test plan** (`validate-test-plan` — blocks the commit
on a real plan ERROR; read-only, never edits the `.xlsx`). If a hook modifies files,
the commit pauses so you can review + re-`git add`. Config lives in `pyproject.toml`
and `.pre-commit-config.yaml`.

---

## Documentation

| Doc | Topic |
|-----|-------|
| **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)** | Full workflow, runner flags, registry, reports |
| **[docs/guides/add-domain.md](docs/guides/add-domain.md)** | Onboard a new test domain |
| **[docs/guides/page-objects.md](docs/guides/page-objects.md)** | Page object / locator / fixture conventions |
| **[docs/guides/test-data.md](docs/guides/test-data.md)** | Faker factories + auto-cleanup |
| **[docs/guides/test-organization.md](docs/guides/test-organization.md)** | Test taxonomy: layers, naming, TC IDs, markers, atomic vs e2e |

---

## License

Proprietary — BlazeUp Inc.
