# BlazeUp Automation — User Guide

Complete reference for developers and QA engineers working on the BlazeUp automation framework.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Environment Setup](#2-environment-setup)
3. [Configuration Reference](#3-configuration-reference)
4. [Running Tests](#4-running-tests)
5. [TC Registry & ID System](#5-tc-registry--id-system)
6. [Adding New Test Cases](#6-adding-new-test-cases)
7. [Excel Report](#7-excel-report)
8. [Stability & Performance Testing](#8-stability--performance-testing)
9. [Results & Reports](#9-results--reports)
10. [Fixtures Reference](#10-fixtures-reference)
11. [Project Layers in Detail](#11-project-layers-in-detail)
12. [CI / CD Pipeline](#12-ci--cd-pipeline)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        runner/run_test.py                    │
│           CLI: modes, filters, repeat, Excel flag            │
└────────────────────────────┬─────────────────────────────────┘
                             │ calls
┌────────────────────────────▼─────────────────────────────────┐
│                     runner/test_runner.py                    │
│   builds pytest args · launches subprocess · parses JUnit   │
│   prints colour summary · generates Allure · writes Excel    │
└────────────────────────────┬─────────────────────────────────┘
                             │ pytest subprocess
┌────────────────────────────▼─────────────────────────────────┐
│                           pytest                             │
│  conftest.py → pytest_support/fixtures.py (fixtures/hooks)   │
│  tests/api/**   tests/ui/**                                  │
└───────────┬────────────────────────┬─────────────────────────┘
            │                        │
   ┌────────▼────────┐     ┌────────▼────────┐
   │   api/          │     │   pages/        │
   │  httpx clients  │     │  Playwright POM │
   │  Pydantic models│     │  async/await    │
   └─────────────────┘     └─────────────────┘
```

**Two test layers:**

| Layer | Tech | Location |
|-------|------|----------|
| API | `httpx` + `Pydantic` models | `api/` + `tests/api/` |
| UI | `Playwright` async + Page Object Model | `pages/` + `tests/ui/` |

**Key design decisions:**
- All tests are `async def` — powered by `pytest-asyncio` in `auto` mode.
- The custom runner (`run_test.py`) wraps pytest in a subprocess so it can parse JUnit XML and print a rich summary with colors and an Excel report.
- `tc_registry.py` is **auto-generated** by `sync_registry.py` — never hand-edit it.
- Sensitive data (passwords, tokens) is masked in logs by `base_client.py` and `log_helper.py`.

---

## 2. Environment Setup

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | 3.13 used in CI |
| Git | any | |
| Allure CLI | any | For viewing Allure dashboards |

Install Allure CLI:
- **Windows:** `scoop install allure`
- **macOS:** `brew install allure`
- **Linux:** see [allure docs](https://allurereport.org/docs/install/)

### Step-by-step

```powershell
# 1. Clone
git clone <repo-url>
cd blazeup_automation

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser
python -m playwright install chromium

# 5. Create your .env file
copy .env.example .env              # Windows
# cp .env.example .env              # macOS / Linux

# 6. Edit .env with real credentials (see Section 3)

# 7. Sync the TC registry
python utils/sync_registry.py

# 8. Verify everything works
python -m runner.run_test --list
```

---

## 3. Configuration Reference

All settings live in `.env` (never committed). `config/settings.py` loads them with Pydantic validation.

```env
# ── URLs ─────────────────────────────────────────────────────
BASE_URL=https://terralogic.blazeup.ai
# UI host — used as browser base_url and Referer/Origin header

API_BASE_URL=https://api.prod.blazeup.ai
# API host ONLY (no trailing slash, no service path)
# ✅ correct:  https://api.prod.blazeup.ai
# ❌ wrong:    https://api.prod.blazeup.ai/auth-api   ← service prefix added by client

# ── Credentials ──────────────────────────────────────────────
TEST_EMAIL=your-email@example.com
TEST_PASSWORD=your-password

# ── Browser ──────────────────────────────────────────────────
HEADLESS=true          # false = visible browser window (good for debugging)
BROWSER=chromium       # chromium | firefox | webkit
SLOW_MO=0              # ms delay between each Playwright action (0 = full speed)

# ── Viewport ─────────────────────────────────────────────────
VIEWPORT_WIDTH=1440
VIEWPORT_HEIGHT=900

# ── Timing ───────────────────────────────────────────────────
DEFAULT_RESPONSE_TIME_MS=30000
# Soft SLA for API responses. Slow responses log a WARNING but do NOT fail the test.
# Setup fixtures use 5× this value to avoid false failures on cold starts.
```

> **Tip:** Set `HEADLESS=false` and `SLOW_MO=500` while writing a new UI test to watch the browser in real time.

---

## 4. Running Tests

### 4.1 Custom runner (recommended)

```powershell
# Run default TCs (defined by DEFAULT_EXECUTE_IDS in run_test.py)
python -m runner.run_test

# Run specific TC IDs
python -m runner.run_test --execute 5
python -m runner.run_test --execute 1 2 3 10 11

# Run a range
python -m runner.run_test --execute 1-9
python -m runner.run_test --execute 1010101-1010103

# Mix IDs and ranges
python -m runner.run_test --execute 1-4 10 1010101
```

**Filter by metadata:**

```powershell
python -m runner.run_test --mode smoke          # @pytest.mark.smoke TCs
python -m runner.run_test --mode regression     # P1 priority TCs
python -m runner.run_test --type api            # all API TCs
python -m runner.run_test --type ui             # all UI TCs
python -m runner.run_test --module login        # TCs in module=login
python -m runner.run_test --module partner      # TCs in module=partner
python -m runner.run_test --priority P1         # filter by priority (stacks)
python -m runner.run_test --marker smoke        # filter by pytest marker
```

**Skip specific TCs:**

```powershell
python -m runner.run_test --execute 1-13 --skip 3 8
```

**Utility flags:**

```powershell
python -m runner.run_test --list               # list all registered TCs
python -m runner.run_test --dry-run            # show plan without running
python -m runner.run_test --debug-log          # write DEBUG-level logs to test.log
python -m runner.run_test --serve              # open Allure after run
python -m runner.run_test --no-excel-report    # skip Excel export for this run
```

### 4.2 Direct pytest (development & debugging)

Use direct pytest when writing a new test — faster feedback, no subprocess overhead:

```powershell
# Run a whole file
python -m pytest tests/api/test_auth_api.py -s

# Run a single function
python -m pytest tests/ui/test_login.py::test_tc01_login_success_with_valid_credentials -s

# Run all Partner Platform tests
python -m pytest tests/ui/partner_portal_shell/ -s

# Run smoke tests with pytest
python -m pytest -m smoke -s

# Stop on first failure
python -m pytest tests/ -x -s
```

> **Note:** Direct pytest writes artifacts to `reports/pytest-report.html` and `allure-results/` (root-level), not to a timestamped `results/run_*/` folder.

### 4.3 Defaults you can change in `run_test.py`

Open `runner/run_test.py` and edit these constants at the top — no CLI flags needed:

```python
# Which TCs to run when no --execute / --mode is passed
DEFAULT_EXECUTE_IDS: list[str] = ["1010101-1010103"]

# IDs to always skip (blacklist)
DEFAULT_SKIP_IDS: list[str] = []

# Export Excel report by default (True/False)
REPORT_EXCEL: bool = True
```

---

## 5. TC Registry & ID System

### 5.1 What is the registry?

`runner/tc_registry.py` is the **single source of truth** that maps a numeric TC ID to:
- the pytest node path (`test_path::test_func`)
- metadata (title, priority, type, module, markers)
- `tc_string` — the ID in `Partner_Platform_Test_Plan.xlsx`

It is **auto-generated** by `utils/sync_registry.py` — do not edit it manually.

### 5.2 ID ranges

| ID range | Type | Module | Source |
|----------|------|--------|--------|
| 1 – 4 | API | attendance | `tests/api/test_attendance_api.py` |
| 5 – 9 | API | auth | `tests/api/test_auth_api.py` |
| 10 – 13 | UI | login | `tests/ui/test_login.py` |
| 1 010 101 + | UI | partner | `tests/ui/partner_portal_shell/…` |

**Legacy TCs (1–13):** Assigned sequential IDs in file/line order. `tc_string = "demo"` — not linked to an Excel row.

**Partner Platform TCs:** Encoded IDs using the scheme below.

### 5.3 Partner Platform ID encoding

```
Format:  {type_bit}{module:02d}{section:02d}{seq:02d}

type_bit : 1 = UI   0 = API
module   : 01 = PARTNER
section  : 01 = PartnerPortalShell
           02 = Dashboard
           03 = Deals
           …  (see sync_registry.py → SECTION_MAP)
seq      : 01, 02, 03 …

Examples:
  1 01 01 01  =  1010101  →  PARTNER_UI_PARTNER_PORTAL_SHELL_001
  1 01 02 01  =  1010201  →  PARTNER_UI_DASHBOARD_001
  0 01 01 01  =   010101  →  PARTNER_API_AUTH_ACCESS_CONTROL_001
```

UI IDs are always ≥ 1 000 000. API IDs are always < 1 000 000. No collision possible.

### 5.4 Regenerating the registry

Run after adding, renaming, or deleting any test function:

```powershell
python utils/sync_registry.py
```

What it does:
1. Scans `tests/**/*.py` for functions matching `test_partner_{ui|api}_*_NNN`.
2. Looks up title and priority from `Partner_Platform_Test_Plan.xlsx`.
3. Scans legacy `test_tc*` / `test_tca*` functions and assigns sequential IDs.
4. Overwrites `runner/tc_registry.py`.

> CI also runs this and will fail the build if `tc_registry.py` is out of sync with the test files.

---

## 6. Adding New Test Cases

### 6.1 Naming convention

Follow this exact pattern so `sync_registry.py` auto-detects the function:

```
test_partner_{type}_{section}_{NNN}

type    : ui  or  api
section : snake_case of the Excel "Main Section" column
NNN     : 3-digit zero-padded sequence within the section (001, 002, …)
```

**Examples:**

| Excel TestcaseId | Function name |
|-----------------|---------------|
| `PARTNER_UI_PARTNER_PORTAL_SHELL_001` | `test_partner_ui_partner_portal_shell_001` |
| `PARTNER_UI_DASHBOARD_001` | `test_partner_ui_dashboard_001` |
| `PARTNER_API_AUTH_ACCESS_CONTROL_001` | `test_partner_api_auth_access_control_001` |

### 6.2 File structure

One file per **section** (not per TC). Multiple TCs live in the same file:

```text
tests/
└── ui/
    ├── partner_portal_shell/
    │   └── test_partner_ui_partner_portal_shell.py   ← 001, 002, 003 all here
    ├── dashboard/
    │   └── test_partner_ui_dashboard.py              ← 001, 002 here
    └── deals/
        └── test_partner_ui_deals.py
```

### 6.3 Step-by-step: add a new TC

**Step 1 — Write the test function**

```python
# tests/ui/dashboard/test_partner_ui_dashboard.py

import pytest
from pages.login_page import LoginPage
from pages.home_page import HomePage


async def test_partner_ui_dashboard_001(page):
    """PARTNER_UI_DASHBOARD_001: View - Partner shell loads - Dashboard is displayed."""
    # TODO: implement
    pass
```

> A function body of `pass` (no assertions, no exceptions) → **PASSED**.  
> `pytest.skip("reason")` → **SKIPPED**.  
> `assert False` / raise any exception → **FAILED**.

**Step 2 — Add locators (if needed)**

```python
# locator/dashboard_ui.py
class DashboardSelectors:
    KPI_WIDGET = "[data-testid='kpi-widget']"
    PIPELINE_SECTION = ".pipeline-snapshot"
```

**Step 3 — Add page actions (if needed)**

```python
# pages/dashboard_page.py
from pages.base_page import BasePage
from locator.dashboard_ui import DashboardSelectors

class DashboardPage(BasePage):
    async def expect_kpi_widget(self) -> None:
        await self.wait_for_element(DashboardSelectors.KPI_WIDGET, label="KPI Widget")
```

**Step 4 — Debug with direct pytest**

```powershell
python -m pytest tests/ui/dashboard/test_partner_ui_dashboard.py -s
```

**Step 5 — Sync the registry**

```powershell
python utils/sync_registry.py
```

The function `test_partner_ui_dashboard_001` is now in the registry with ID `1010201`.

**Step 6 — Run officially**

```powershell
python -m runner.run_test --execute 1010201
```

**Step 7 — Verify Excel report**

Open the generated `Partner_Platform_Test_Plan_result_*.xlsx` in the run folder.  
Find row `PARTNER_UI_DASHBOARD_001` → column **Auto** = `YES`, column **Automation Status** = `PASSED`.

### 6.4 Add markers (optional)

```python
import pytest

@pytest.mark.smoke
async def test_partner_ui_dashboard_001(page):
    ...
```

Available markers (defined in `pytest.ini`): `smoke`, `regression`, `ui`, `api`, `slow`.

After adding a marker, re-run `python utils/sync_registry.py` — the marker is stored in the registry.

### 6.5 Priority

Priority comes from the `Priority` column in `Partner_Platform_Test_Plan.xlsx`.  
`sync_registry.py` reads it automatically. If the TC has no Excel row yet, default is `P2`.

Override by setting a docstring-parsable priority or wait until the row exists in Excel.

---

## 7. Excel Report

After each run the framework copies `Partner_Platform_Test_Plan.xlsx` into the result folder and writes test outcomes.

### 7.1 What gets updated

| Excel column | Value written |
|---|---|
| **J — Auto** | `YES` (marks row as covered by automation) |
| **K — Automation Status** | `PASSED` / `FAILED` / `NOT_STARTED` |
| **H — Status** | Formula — auto-recomputes in Excel when you open the file |

Columns A–I and L onward are never touched.

### 7.2 Outcome mapping

| pytest result | Automation Status written |
|---|---|
| PASSED | `PASSED` |
| FAILED / ERROR | `FAILED` |
| SKIPPED / MISSING | `NOT_STARTED` |

### 7.3 Enable / disable

In `runner/run_test.py`:

```python
REPORT_EXCEL: bool = True   # True = export after every run (default)
                             # False = never export unless --excel-report passed
```

CLI overrides:

```powershell
python -m runner.run_test                    # uses REPORT_EXCEL default
python -m runner.run_test --excel-report     # force enable for this run
python -m runner.run_test --no-excel-report  # force disable for this run
```

### 7.4 Output file location

```text
results/run_YYYYMMDD_HHMMSS/
└── Partner_Platform_Test_Plan_result_YYYYMMDD_HHMMSS.xlsx
```

### 7.5 Only Partner Platform TCs are exported

Legacy TCs (IDs 1–13, `tc_string = "demo"`) have no Excel row and are skipped.  
Only TCs with a proper `tc_string` (e.g. `PARTNER_UI_DASHBOARD_001`) are written.

### 7.6 Add a new module / sheet

When a new Excel sheet is added (e.g. `Health System`), add it to **both** files:

```python
# utils/sync_registry.py  (line ~85)
EXCEL_SHEETS: dict[str, str] = {
    "Partner Platform": "PARTNER",
    "Health System":    "HEALTH",   # ← add here
}

# utils/excel_reporter.py  (line ~35)
MODULE_TO_SHEET: dict[str, str] = {
    "partner": "Partner Platform",
    "health":  "Health System",    # ← add here
}
```

Then run `python utils/sync_registry.py` to pick up the new module's TCs.

---

## 8. Stability & Performance Testing

Use `--repeat` to run the same TCs multiple times — useful for detecting flaky tests.

### 8.1 Repeat modes

| Mode | Order | Best for |
|------|-------|----------|
| `batch` (default) | `[1,2,3] × N` | System stability, detecting state leaks |
| `each` | `[1×N, 2×N, 3×N]` | Isolating a flaky single TC |

### 8.2 Examples

```powershell
# Run TC 10 five times in a row (flaky detection)
python -m runner.run_test --execute 10 --repeat 5 --repeat-mode each

# Run full suite 3 times (stability check)
python -m runner.run_test --execute 1-13 --repeat 3 --repeat-mode batch

# Stop after 2 total failures
python -m runner.run_test --execute 1-13 --repeat 5 --fail-fast-count 2
```

### 8.3 Stability summary

Multi-run produces a different table:

```
| TC      | P  | Type | Title           | Runs | Pass | Fail | Rate | Avg   | Stability |
|---------|----|------|-----------------|------|------|------|------|-------|-----------|
| 10      | P1 | ui   | Login succeeds  | 5    |  5   |  0   | 100% | 3.21s | STABLE    |
| 11      | P2 | ui   | Wrong password  | 5    |  4   |  1   |  80% | 2.87s | FLAKY     |
```

---

## 9. Results & Reports

### 9.1 Result folder structure

Every `python -m runner.run_test` run creates:

```text
results/run_YYYYMMDD_HHMMSS/
├── run_meta.json              # TC IDs, node IDs, mode, timestamp
├── report.html                # Self-contained pytest-html report
├── logs/
│   ├── test.log               # Full loguru log (all levels, TC-annotated)
│   └── junit.xml              # JUnit XML (parsed by the runner)
├── screenshots/               # PNG per test (failure = attached to Allure)
├── videos/                    # Playwright video recording per test
├── traces/                    # Playwright trace zip per test
├── allure-results/            # Raw JSON/XML for Allure
├── allure-report/             # Generated static Allure HTML (index.html)
└── Partner_Platform_Test_Plan_result_YYYYMMDD_HHMMSS.xlsx
```

### 9.2 Viewing reports

**pytest-html** (quickest):
Open `results/run_.../report.html` directly in a browser.

**Allure** (richest — steps, screenshots, timeline):
```powershell
# The runner prints this command after every run:
allure open "results/run_YYYYMMDD_HHMMSS/allure-report"

# Or serve the raw results directly:
allure serve "results/run_YYYYMMDD_HHMMSS/allure-results"
```

**Log file:**
```powershell
# Grep by TC ID
Select-String "TC-10" results\run_*\logs\test.log    # PowerShell
grep "TC-10" results/run_*/logs/test.log             # bash
```

**Playwright Trace Viewer** (step-by-step UI replay):
```powershell
python -m playwright show-trace "results/run_YYYYMMDD_HHMMSS/traces/test_tc01_login_success_with_valid_credentials.zip"
```

### 9.3 Artifacts from direct pytest

When running `python -m pytest ...` directly (not through the runner):

```text
reports/pytest-report.html    # from pytest.ini addopts
allure-results/               # root-level (overwritten each run)
```

---

## 10. Fixtures Reference

All fixtures are defined in `pytest_support/fixtures.py` and auto-discovered via `conftest.py`.

### Session-scoped (created once per test session)

| Fixture | Type | Description |
|---------|------|-------------|
| `settings` | `Settings` | Pydantic config loaded from `.env` |
| `result_dir` | `Path` | Timestamped run folder; configures loguru sinks |
| `test_data` | `dict` | Parsed `fixtures/test_data.yaml` |
| `fake` | `Faker` | Faker instance for generating test data |

### Function-scoped (created fresh per test)

| Fixture | Type | Description |
|---------|------|-------------|
| `browser_context` | `BrowserContext` | Playwright context with viewport + tracing |
| `page` | `Page` | Fresh Playwright page; takes screenshot on finish |
| `test_user` | `dict` | Generated user dict (`first_name`, `last_name`, `email`, `department`) |
| `api_token` | `str` | Fresh JWT via login API; uses 5× response-time limit |
| `auth_client` | `AuthClient` | Authenticated API client (auto-closed after test) |
| `attendance_client` | `AttendanceClient` | Authenticated attendance client (auto-closed) |
| `authenticated_page` | `Page` | Page already logged in through the UI |
| `tc_logger` *(autouse)* | — | Emits START / PASSED / FAILED banners; binds TC ID to logs |

### Usage examples

```python
# API test — use auth_client
async def test_tca04_get_me_returns_user_info(auth_client):
    response = await auth_client.me()
    assert response.email is not None

# UI test — use page (unauthenticated)
async def test_tc02_login_fails_with_wrong_password(page, settings, test_data):
    login = LoginPage(page, str(settings.base_url))
    await login.open()
    await login.login("bad@example.com", "wrong")
    error = await login.expect_error()
    assert "invalid" in error.lower()

# UI test — use authenticated_page (already logged in)
async def test_partner_ui_dashboard_001(authenticated_page, settings):
    dashboard = DashboardPage(authenticated_page, str(settings.base_url))
    await dashboard.expect_kpi_widget()
```

---

## 11. Project Layers in Detail

### 11.1 API clients (`api/`)

| File | Class | Key methods |
|------|-------|-------------|
| `base_client.py` | `BaseClient` | `request()`, `get()`, `post()` |
| `auth_client.py` | `AuthClient` | `login()`, `me()`, `raw_login()` |
| `attendance_client.py` | `AttendanceClient` | `status()`, `today()`, `raw_status()` |
| `expense_client.py` | `ExpenseClient` | expense endpoints |
| `user_client.py` | `UserClient` | user management endpoints |

`BaseClient` automatically:
- Adds `Authorization`, `Origin`, `Referer`, `X-PLATFORM` headers.
- Retries on `5xx` responses (up to 3 attempts with backoff).
- Logs `SLOW` warning if response exceeds `max_response_time_ms` (soft check — does NOT fail the test).
- Validates response against a Pydantic schema if `schema=` is passed.

### 11.2 Page Objects (`pages/`)

| File | Class | Key methods |
|------|-------|-------------|
| `base_page.py` | `BasePage` | `goto()`, `fill()`, `click()`, `wait_for_element()`, `get_text()` |
| `login_page.py` | `LoginPage` | `open()`, `login()`, `expect_error()` |
| `home_page.py` | `HomePage` | `expect_loaded()`, `logout()`, `clock_in()` |

`BasePage` automatically:
- Retries `click()` and `wait_for_element()` up to 3× on `TimeoutError`.
- Masks passwords in `fill()` log output.
- Provides readable error messages with selector labels.

### 11.3 Locators (`locator/`)

Pure selector constants — no logic. One file per page:

```python
# locator/login_ui.py
class LoginSelectors:
    IDENTIFIER_INPUT = "input[type='email'], input[type='text']"
    PASSWORD_INPUT   = "input[type='password']"
    PROCEED_BUTTON   = "button:has-text('Proceed'), button:has-text('Next')"
    LOGIN_BUTTON     = "button[type='submit']:has-text('Login')"
    ERROR_CONTAINERS = ".error-message, [role='alert'], .ant-form-item-explain-error"
```

When a UI changes (selector breaks), update only the locator file — no test changes needed.

### 11.4 Logging

Custom log levels in `utils/log_helper.py`:

| Level | Numeric | Color | Used for |
|-------|---------|-------|----------|
| `STEP` | 21 | Cyan | Test step actions |
| `START` | 22 | Blue | TC start banner |
| `PASSED` | 23 | Green | TC passed banner |
| `FAILED` | 24 | Red | TC failed banner |

Log format in terminal:
```
10:25:01 | START    | [TC-5] BlazeUp sign-in returns a bearer token.
10:25:01 | INFO     | POST /auth-api/login | 200 (342ms)
10:25:02 | PASSED   | [TC-5] PASSED (1.23s)
```

Log format in `test.log` file:
```
2026-05-26 10:25:01.342 | START    | TC-5      | fixtures.py:tc_logger:172  | [TC-5] BlazeUp sign-in returns a bearer token.
2026-05-26 10:25:01.684 | INFO     | TC-5      | base_client.py:request:89  | POST /auth-api/login | 200 (342ms)
2026-05-26 10:25:02.155 | PASSED   | TC-5      | fixtures.py:tc_logger:190  | [TC-5] PASSED (1.23s)
```

---

## 12. CI / CD Pipeline

File: `.github/workflows/test.yml`

### Jobs

| Job | Trigger | Command | Artifacts |
|-----|---------|---------|-----------|
| `smoke` | push to `main`/`develop`, manual dispatch | `pytest -m smoke` | `smoke-reports` |
| `regression` | nightly cron 02:00 UTC | `pytest -m regression` | `regression-reports` |

### Required GitHub secrets

| Secret | Value |
|--------|-------|
| `BASE_URL` | `https://terralogic.blazeup.ai` |
| `API_BASE_URL` | `https://api.prod.blazeup.ai` |
| `TEST_EMAIL` | test account email |
| `TEST_PASSWORD` | test account password |

### Registry validation step

CI runs `python utils/sync_registry.py` before tests and checks that `tc_registry.py` is unchanged. If any test file was added/removed without re-running the sync, the build fails with:

```
::error::tc_registry.py is out of sync. Run 'python utils/sync_registry.py' and commit.
```

**Fix:** run `python utils/sync_registry.py` locally and commit the updated `tc_registry.py`.

---

## 13. Troubleshooting

### pytest / import errors

**Problem:** `ModuleNotFoundError` when running pytest.  
**Fix:** Always run from the project root with the venv active:
```powershell
cd "C:\Users\trang.le\Desktop\New folder\blazeup_automation"
.venv\Scripts\Activate.ps1
python -m runner.run_test ...
```

---

**Problem:** `ModuleNotFoundError: No module named 'playwright'`  
**Fix:**
```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

---

**Problem:** `Executable doesn't exist` / browser not found.  
**Fix:**
```powershell
python -m playwright install chromium   # or firefox / webkit
```

---

### Credentials / login failures

**Problem:** All UI tests fail at login step.  
**Fix:** Check `.env` has correct `TEST_EMAIL` and `TEST_PASSWORD`. Test manually:
```powershell
python -c "
import asyncio
from config.settings import get_settings
from api.auth_client import AuthClient

async def check():
    s = get_settings()
    c = AuthClient(str(s.api_base_url))
    r = await c.login(s.test_email, s.test_password)
    print('Token:', r.bearer_token[:30], '...')
    await c.close()

asyncio.run(check())
"
```

---

### Registry out of sync

**Problem:** `TC ID X not found in registry`.  
**Fix:**
```powershell
python utils/sync_registry.py
```

**Problem:** `tc_registry.py is out of sync` in CI.  
**Fix:** Run sync locally and commit:
```powershell
python utils/sync_registry.py
git add runner/tc_registry.py
git commit -m "chore: sync tc_registry"
git push
```

---

### Flaky tests

**Problem:** Tests fail intermittently (timeout, slow response).

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `TimeoutError` on login | Slow page render | `login()` default is 60 s — usually enough |
| API tests slow | Server cold start | `api_token` fixture uses 5× SLA — warning only |
| Random failures | Concurrency / state | Use `--repeat 5 --repeat-mode each` to confirm flakiness |

Run stability check:
```powershell
python -m runner.run_test --execute 10 11 12 --repeat 5 --repeat-mode batch
```

---

### Allure not opening

**Problem:** `allure` command not found.  
**Fix:** Install Allure CLI and ensure it is on `PATH`:
```powershell
scoop install allure        # Windows
brew install allure         # macOS
```

**Problem:** Allure shows `0 test cases`.  
**Fix:** Use the exact path printed by the runner in the summary:
```
  Allure : results/run_20260526_113058/allure-report
           run: allure open "results/run_20260526_113058/allure-report"
```

---

### Excel report not generated

**Problem:** No `.xlsx` file in the result folder.  
**Causes:**
1. `REPORT_EXCEL = False` in `run_test.py` → change to `True` or pass `--excel-report`.
2. Only legacy TCs (IDs 1–13) were run → legacy TCs have no Excel row, nothing to write.
3. `Partner_Platform_Test_Plan.xlsx` not found at project root → ensure the file exists.

---

### Viewing a Playwright trace (step-by-step replay)

```powershell
python -m playwright show-trace "results\run_YYYYMMDD_HHMMSS\traces\<test_name>.zip"
```

This opens an interactive browser-based trace viewer showing every action, screenshot, and network request.

---

### Debug mode

```powershell
# Write DEBUG-level logs (includes all HTTP headers, body, response details)
python -m runner.run_test --execute 10 --debug-log

# Watch browser in slow motion
# In .env: HEADLESS=false  SLOW_MO=500
python -m runner.run_test --execute 10
```
