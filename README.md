# BlazeUp Automation Framework

pytest + Playwright async automation framework for the **BlazeUp Partner Platform** (SA/admin + partner actors under one `blazeup` domain, sharing one API gateway).

Covers both **HTTP API** (httpx + Pydantic) and **Browser UI** (Playwright async + Page Object Model) automation.

> **Full workflow, naming conventions, and troubleshooting** → **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)**

---

## Quick Start

### 1. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
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
│   └── blazeup/                          #   Partner Platform reference + test plan
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
│   │                                      #   - auth_state (session-scoped: login once)
│   │                                      #   - authenticated_page / make_page (UI tests)
│   │                                      #   - api_token (session-scoped)
│   │                                      #   - auth_client (API)
│   │                                      #   - created_resources (auto-cleanup)
│   └── hooks.py                          #   pytest_runtest_makereport hook
│
├── runner/                               #   Test execution & reporting
│   ├── run_test.py                       #   CLI entrypoint (modes, filters, repeat)
│   ├── test_runner.py                    #   Subprocess runner, summary, Excel export
│   ├── tc_registry.py                    #   AUTO-GENERATED: merged registry
│   └── blazeup/                          #   Domain entry points
│       ├── run_test.py                   #     Run tests
│       ├── registry.py                   #     Auto-generated TC registry
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
├── requirements.txt                      #   Python dependencies (to run tests)
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

# Sync TC registry (after adding new test functions)
python utils/sync_registry.py

# Lint the Excel test plan (well-formed + in sync with code; read-only)
python utils/validate_test_plan.py            # --strict = warnings fail too
```

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
| `authenticated_page` | function | UI test, already logged in |
| `page` | function | UI test without login (login tests) |
| `api_token` | session | API test, already have JWT token |
| `auth_client` | function | Authenticated API client (AuthClient) |
| `attendance_client` | function | Authenticated API client (AttendanceClient) |
| `make_page` | function | Factory: build an authenticated page object — `make_page(ShellPage)` |
| `created_resources` | function | Track created resources → auto-delete on teardown (CRUD tests) |
| `auth_state` | session | Pre-cached Playwright storage state (internal) |
| `fake` | session | Faker instance for dynamic data generation |
| `test_user` | function | Generated user data dict |

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

### Test suite — `test.yml` (manual)

Runs **on manual dispatch only** (no push/schedule trigger). Start it from
**Actions → BlazeUp Automation Tests → Run workflow** (works from the GitHub Mobile
app), choosing:

| Input | Options | Notes |
|-------|---------|-------|
| `mode` | `smoke` / `regression` / `normal` | Ignored when `execute` is set |
| `execute` | e.g. `2061001 2061002` or `2060201-2060220` | Specific TC IDs / ranges |
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

CI maps these secrets to the env vars `settings.py` reads (`API_BASE_URL` ←
`ADMIN_API_BASE_URL`; `ADMIN_*`/`PARTNER_*` as named):

| Secret | Purpose |
|--------|---------|
| `ADMIN_API_BASE_URL` | shared API gateway → `API_BASE_URL` |
| `ADMIN_BASE_URL` / `ADMIN_TEST_EMAIL` / `ADMIN_TEST_PASSWORD` | SA UI origin + login |
| `PARTNER_BASE_URL` / `PARTNER_TEST_EMAIL` / `PARTNER_TEST_PASSWORD` | Partner UI origin + login |
| `GROQ_API_KEY` | AI triage (Groq provider) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Telegram notifications |

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
