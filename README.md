# BlazeUp Automation Framework

Multi-domain pytest + Playwright async automation framework for **BlazeUp Admin (HRMS)** and **BlazeUp Partner Platform**.

Covers both **HTTP API** (httpx + Pydantic) and **Browser UI** (Playwright async + Page Object Model) automation.

> **Full workflow, naming conventions, and troubleshooting** → **[USER_GUIDE.md](USER_GUIDE.md)**

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

### 3. Configure Credentials

Each domain has its own `.env` file:

```bash
# BlazeUp Admin (HRMS)
cat > config/blazeup_admin/.env <<EOF
BASE_URL=https://stgsa.blazeup.ai
API_BASE_URL=https://api.stg.blazeup.ai
TEST_EMAIL=your-email@example.com
TEST_PASSWORD=your-password
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
DEFAULT_RESPONSE_TIME_MS=2000
EOF

# BlazeUp Partner
cat > config/blazeup_partner/.env <<EOF
BASE_URL=https://partner.stgsa.blazeup.ai
API_BASE_URL=https://api.stg.blazeup.ai
PARTNER_EMAIL=your-email@example.com
PARTNER_PASSWORD=your-password
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
DEFAULT_RESPONSE_TIME_MS=2000
EOF
```

**Never commit `.env` files** — they are listed in `.gitignore`.

### 4. Run Tests

```bash
# Run BlazeUp Admin tests (currently empty, waiting for test plan)
python -m runner.blazeup_admin.run_test

# Run BlazeUp Partner tests (currently empty, waiting for test plan)
python -m runner.blazeup_partner.run_test

# Run specific test file
python -m pytest tests/blazeup_partner/ui/partner_portal_shell/test_*.py -s

# List all registered TCs (shared runner)
python -m runner.run_test --list
```

---

## Project Structure

```
blazeup_automation/
│
├── api_clients/                          # HTTP API clients (httpx + Pydantic)
│   ├── base_client.py                    #   Base: retry, timing, schema validation
│   ├── blazeup_admin/
│   │   ├── auth_client.py                #   Login, logout, /current-user
│   │   └── attendance_client.py          #   Attendance endpoints
│   └── blazeup_partner/                  #   (Currently empty, ready for Partner API)
│
├── config/                               # Domain-specific settings
│   ├── settings.py                       #   Typed config from .env (Pydantic)
│   ├── blazeup_admin/.env                #   Admin domain credentials & UI base URL
│   └── blazeup_partner/.env              #   Partner domain credentials & UI base URL
│
├── docs/
│   └── blazeup_admin/                    #   Reference docs, test plans, requirements
│       ├── Partner_Platform_Test_Plan.xlsx
│       ├── partner_requirement.xlsx
│       ├── partner-platform-prd-v1.8.md
│       └── partner-platform-prd-v1.8.vi.md
│
├── fixtures/
│   └── test_data.yaml                    #   Static test data (invalid users, etc.)
│
├── locators/                             #   UI element selectors (by page/domain)
│   ├── blazeup_admin/
│   │   └── login_ui.py                   #   Login page selectors
│   └── blazeup_partner/
│
├── pages/                                #   Page Object Model
│   ├── base_page.py                      #   Shared: goto, fill, click, wait_for_element
│   ├── blazeup_admin/
│   │   └── login_page.py                 #   Two-step login flow
│   └── blazeup_partner/
│
├── pytest_support/
│   ├── fixtures.py                       #   All pytest fixtures
│   │                                      #   - auth_state (session-scoped: login once)
│   │                                      #   - authenticated_page (UI tests)
│   │                                      #   - api_token (session-scoped)
│   │                                      #   - auth_client, attendance_client
│   └── hooks.py                          #   pytest_runtest_makereport hook
│
├── runner/                               #   Test execution & reporting
│   ├── run_test.py                       #   CLI entrypoint (modes, filters, repeat)
│   ├── test_runner.py                    #   Subprocess runner, summary, Excel export
│   ├── tc_registry.py                    #   AUTO-GENERATED: merged registry
│   ├── blazeup_admin/
│   │   ├── run_test.py                   #   Admin-only CLI (sets BLAZEUP_DOMAIN=blazeup_admin)
│   │   └── registry.py                   #   Auto-generated, domain-specific TCs
│   └── blazeup_partner/
│       ├── run_test.py                   #   Partner-only CLI (sets BLAZEUP_DOMAIN=blazeup_partner)
│       └── registry.py                   #   Auto-generated, domain-specific TCs
│
├── tests/                                #   Test cases (domain/layer structure)
│   ├── blazeup_admin/
│   │   ├── api/                          #   (Waiting for test plan)
│   │   └── ui/                           #   (Waiting for test plan)
│   └── blazeup_partner/
│       ├── api/                          #   (Waiting for test plan)
│       └── ui/                           #   (Waiting for test plan)
│
├── utils/                                #   Shared utilities
│   ├── login_helpers.py                  #   Reusable: login_ui(), login_api()
│   ├── sync_registry.py                  #   Regenerates runner/*/registry.py from tests
│   ├── excel_reporter.py                 #   Exports results to Excel
│   ├── helpers.py                        #   load_yaml, require_credentials
│   ├── log_helper.py                     #   Custom log levels: STEP, START, PASSED, FAILED
│   └── screenshot_on_fail.py             #   Allure screenshot attachment
│
├── conftest.py                           #   Pytest discovery entrypoint (imports fixtures)
├── pytest.ini                            #   Markers, asyncio mode, HTML/Allure paths
├── requirements.txt                      #   Python dependencies
├── .gitignore                            #   Git ignore rules
├── .gitattributes                        #   Line ending & binary file rules
├── README.md                             #   ← you are here
├── USER_GUIDE.md                         #   Full workflow & naming conventions
└── .env.example                          #   Template (copy to config/{domain}/.env)
```

---

## Domain Architecture

This framework supports multiple test domains. Each domain has:

- **Independent test registry** (`runner/{domain}/registry.py`)
- **Domain-specific CLI** (`runner/{domain}/run_test.py`)
- **Domain-specific .env** (`config/{domain}/.env`)
- **Auto-discovery** via `utils/sync_registry.py`

### BlazeUp Admin (HRMS)
- **Base URL**: `https://stgsa.blazeup.ai`
- **API Base**: `https://api.stg.blazeup.ai`
- **Credentials**: `TEST_EMAIL`, `TEST_PASSWORD` from `config/blazeup_admin/.env`
- **Tests**: Currently being planned
- **CLI**: `python -m runner.blazeup_admin.run_test`

### BlazeUp Partner
- **Base URL**: `https://partner.stgsa.blazeup.ai`
- **API Base**: `https://api.stg.blazeup.ai`
- **Credentials**: `PARTNER_EMAIL`, `PARTNER_PASSWORD` from `config/blazeup_partner/.env`
- **Tests**: Currently being planned
- **CLI**: `python -m runner.blazeup_partner.run_test`

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
# Domain-specific runs
python -m runner.blazeup_admin.run_test              # Admin tests
python -m runner.blazeup_partner.run_test            # Partner tests

# Shared runner (runs all domains)
python -m runner.run_test --list                      # List all registered TCs
python -m runner.run_test --dry-run                   # Show execution plan
python -m runner.run_test --mode smoke                # Run smoke-marked TCs
python -m runner.run_test --mode regression           # Run P1 TCs

# Direct pytest (for development)
python -m pytest tests/blazeup_partner/ui/ -s -k test_partner_ui_partner_portal_shell_001
python -m pytest tests/ --co                          # Collect tests (show discovery)

# Sync TC registry (after adding new test functions)
python utils/sync_registry.py
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
├── report.html                          # pytest-html report
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

# HTML pytest report
open results/run_*/report.html

# Logs (grep-friendly format)
grep "TC-" results/run_*/logs/test.log
```

---

## Development

### Add a New Test

1. Write a test function in `tests/{domain}/{layer}/*.py`:
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
   This auto-generates `runner/{domain}/registry.py` with the new TC ID.

3. Run the test:
   ```bash
   python -m runner.{domain}.run_test --execute <TC_ID>
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
| `auth_state` | session | Pre-cached Playwright storage state (internal) |
| `test_data` | session | Static test data from `fixtures/test_data.yaml` |
| `fake` | session | Faker instance for dynamic data generation |
| `test_user` | function | Generated user data dict |

---

## Troubleshooting

### Playwright browser not found
```bash
python -m playwright install chromium
```

### Settings load wrong environment
Ensure `BLAZEUP_DOMAIN` is set BEFORE imports:
```bash
# ✅ Correct: domain set before config load
python -m runner.blazeup_admin.run_test

# ❌ Wrong: generic pytest, may load wrong .env
python -m pytest tests/blazeup_admin/...
```

### Tests timeout
Increase `DEFAULT_RESPONSE_TIME_MS` in `.env`:
```env
DEFAULT_RESPONSE_TIME_MS=30000   # 30 seconds
```

### Login fails
- Verify credentials in `config/{domain}/.env`
- Check that `BASE_URL` and `API_BASE_URL` are correct
- Ensure `LOGIN_TIMEOUT_MS` is not too short

---

## CI / CD

GitHub Actions workflows are in `.github/workflows/`:

| Workflow | Trigger | TCs |
|----------|---------|-----|
| `smoke.yml` | push, manual | `@pytest.mark.smoke` |
| `regression.yml` | nightly | `priority=P1` |

Requires secrets: `BASE_URL`, `API_BASE_URL`, `TEST_EMAIL`, `TEST_PASSWORD`, `PARTNER_EMAIL`, `PARTNER_PASSWORD`.

---

## License

Proprietary — BlazeUp Inc.
