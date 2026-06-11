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
    - [12b. Code Quality (lint + pre-commit)](#12b-code-quality-lint--format--pre-commit)
    - [12c. Test Data Management (Faker + cleanup)](#12c-test-data-management-faker--cleanup)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│            runner/{domain}/run_test.py                             │
│   Domain CLI: sets BLAZEUP_DOMAIN env var before any imports       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ delegates to
┌────────────────────────────▼────────────────────────────────────────┐
│                  runner/run_test.py  (shared)                      │
│        CLI: modes, filters, repeat, Excel flag                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │ calls
┌────────────────────────────▼────────────────────────────────────────┐
│                    runner/test_runner.py                           │
│  builds pytest args · subprocess · JUnit parse · Allure · Excel   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ pytest subprocess
┌────────────────────────────▼────────────────────────────────────────┐
│                          pytest                                    │
│ conftest.py → fixtures.py (auth_state session-scoped: login once) │
│ tests/{domain}/api/**  tests/{domain}/ui/**                       │
└────────┬──────────────────────────────────────┬────────────────────┘
         │                                      │
┌────────▼────────────────┐        ┌───────────▼─────────────────┐
│  api_clients/           │        │   pages/                    │
│  ├── base_client.py     │        │   ├── base_page.py          │
│  ├── {domain}/          │        │   ├── {domain}/             │
│  │   ├── auth_client    │        │   │   ├── login_page        │
│  │   └── ...            │        │   │   └── ...               │
│  └── httpx + Pydantic   │        │   └── Playwright async POM  │
└─────────────────────────┘        └─────────────────────────────┘
```

**Multi-domain support:**

Each domain (e.g. `blazeup_admin`, `blazeup_partner`) has:
- Its own `.env` file (`config/{domain}/.env`)
- Its own TC registry (`runner/{domain}/registry.py`)
- Its own CLI entry point (`runner/{domain}/run_test.py`)

The shared runner merges all domain registries at runtime.

**Two test layers:**

| Layer | Tech | Location |
|-------|------|----------|
| API | `httpx` + `Pydantic` models | `api_clients/` + `tests/{domain}/api/` |
| UI | `Playwright` async + Page Object Model | `pages/` + `tests/{domain}/ui/` |

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

Each domain has its own `.env` file: `config/{domain}/.env` (never committed).  
`config/settings.py` loads it based on the `BLAZEUP_DOMAIN` environment variable set by domain-specific run_test.py.

### BlazeUp Admin (.env)
```env
BASE_URL=https://stgsa.blazeup.ai
API_BASE_URL=https://api.stg.blazeup.ai
TEST_EMAIL=ceo@mailinator.com
TEST_PASSWORD=12345678@Tc
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
DEFAULT_RESPONSE_TIME_MS=2000
```

### BlazeUp Partner (.env)
```env
BASE_URL=https://partner.stgsa.blazeup.ai
API_BASE_URL=https://api.stg.blazeup.ai
TEST_EMAIL=ceo@mailinator.com
TEST_PASSWORD=12345678@Tc
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
DEFAULT_RESPONSE_TIME_MS=2000
```

> **All domains use the SAME env keys** (`TEST_EMAIL` / `TEST_PASSWORD`). Login
> fixtures read `settings.test_email` / `settings.test_password`, so adding a
> domain needs no fixture/test changes — only its own `config/<domain>/.env`.

### Settings reference

| Variable | Example | Purpose |
|----------|---------|---------|
| `BASE_URL` | `https://stgsa.blazeup.ai` | UI root; used as browser base_url & Origin header |
| `API_BASE_URL` | `https://api.stg.blazeup.ai` | API root (no trailing slash, no service path) |
| `TEST_EMAIL` | `ceo@mailinator.com` | Login email — **same key for every domain** |
| `TEST_PASSWORD` | `12345678@Tc` | Login password — **same key for every domain** |
| `HEADLESS` | `true` / `false` | false = visible browser (good for debugging) |
| `BROWSER` | `chromium` | chromium / firefox / webkit |
| `SLOW_MO` | `0` | ms delay between Playwright actions (0 = full speed) |
| `DEFAULT_RESPONSE_TIME_MS` | `2000` | Soft SLA for API responses (warning, not failure) |
| `VIEWPORT_WIDTH` | `1440` | Browser viewport width |
| `VIEWPORT_HEIGHT` | `900` | Browser viewport height |

> **Tip:** Set `HEADLESS=false` and `SLOW_MO=500` when writing new UI tests to watch the browser in real time.

> **Tip:** Set `HEADLESS=false` and `SLOW_MO=500` while writing a new UI test to watch the browser in real time.

---

## 4. Running Tests

### 4.1 Domain-specific runner (recommended)

**BlazeUp Admin (HRMS):**
```powershell
python -m runner.blazeup_admin.run_test
python -m runner.blazeup_admin.run_test --execute 1 2 3
python -m runner.blazeup_admin.run_test --mode smoke
```

**BlazeUp Partner Platform:**
```powershell
python -m runner.blazeup_partner.run_test
python -m runner.blazeup_partner.run_test --execute 1010101 1010102
python -m runner.blazeup_partner.run_test --mode regression
```

### 4.2 Shared runner (all domains)

```powershell
# Run ALL registered TCs from all domains
python -m runner.run_test

# Run specific TC IDs (mixed domains)
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
python utils/sync_registry.py                          # sync ALL domains
python utils/sync_registry.py --domain blazeup_admin   # sync only one domain's folder
python utils/sync_registry.py --domain blazeup_partner # sync only the partner folder
python utils/sync_registry.py --table                  # just print the TC-ID reference table
```

Use `--domain <name>` when you only touched your own domain's tests and don't want
to regenerate the other domain's registry. Without the flag, every domain found
under `tests/*/` is synced.

What it does (per domain):
1. Scans `tests/{domain}/**/*.py` for functions matching `test_partner_{ui|api}_*_NNN`.
2. Looks up title and priority from `docs/{domain}/Partner_Platform_Test_Plan.xlsx`
   (falls back to the function docstring + `P2` if no Excel file exists).
3. Scans legacy `test_tc*` / `test_tca*` functions and assigns sequential IDs.
4. Overwrites `runner/{domain}/registry.py`.

`runner/tc_registry.py` then auto-merges every `runner/*/registry.py` into one
central `TC_REGISTRY` at import time — so the merged total is the sum of all
domains (e.g. 2 admin + 2 partner = 4).

> CI also runs this and will fail the build if any `runner/{domain}/registry.py`
> is out of sync with the test files.

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
| `settings` | `Settings` | Pydantic config loaded from `config/{domain}/.env` |
| `result_dir` | `Path` | Timestamped run folder; configures loguru sinks |
| `test_data` | `dict` | Parsed `fixtures/test_data.yaml` |
| `fake` | `Faker` | Faker instance for generating test data |
| `auth_state` | `dict` | **NEW**: Playwright storage state (cookies + localStorage) cached from one login; injected into every `authenticated_page` context |
| `api_token` | `str` | **Session-scoped**: One JWT per session; reused across all API tests. Avoids repeated login. |

### Function-scoped (created fresh per test)

| Fixture | Type | Description |
|---------|------|-------------|
| `browser_context` | `BrowserContext` | Unauthenticated Playwright context with viewport + tracing |
| `page` | `Page` | Fresh unauthenticated Playwright page; takes screenshot on finish |
| `test_user` | `dict` | Generated user dict (`first_name`, `last_name`, `email`, `department`) |
| `auth_client` | `AuthClient` | Authenticated API client (token from session `api_token`); auto-closed |
| `attendance_client` | `AttendanceClient` | Authenticated attendance client (token from session `api_token`); auto-closed |
| `authenticated_page` | `Page` | Fresh isolated page context per test, pre-authenticated via `auth_state` storage injection (no per-test login) |
| `make_page` | factory | Build an authenticated page object without boilerplate: `make_page(ShellPage)` |
| `created_resources` | registry | Track resources a test creates → auto-delete on teardown (LIFO), pass or fail |
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

# UI test — use make_page (already logged in, no boilerplate)
async def test_partner_ui_dashboard_001(make_page):
    dashboard = make_page(DashboardPage)
    await dashboard.expect_kpi_widget()

# CRUD test — auto-cleanup created resources (pass OR fail)
async def test_create_tenant_001(auth_client, created_resources):
    from utils.data_factory import make_tenant
    resp = await auth_client.post("/tenants", json=make_tenant(), expected_status=201)
    tenant_id = resp.json()["data"]["id"]
    created_resources.add(lambda: auth_client.delete(f"/tenants/{tenant_id}"))
    assert tenant_id
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

### 11.3 Locators (`locators/<domain>/`)

Pure selector constants — no logic. One file per page. **Naming convention:**
file `<x>_locators.py`, class `<X>Locators` (see [page-objects.md](page-objects.md)).

```python
# locators/blazeup_admin/login_locators.py
class LoginLocators:
    IDENTIFIER_INPUT = "input[type='email'], input[type='text']"
    PASSWORD_INPUT   = "input[type='password']"
    PROCEED_BUTTON   = "button:text-is('Proceed'), button:text-is('Next')"
    LOGIN_BUTTON     = "button:text-is('Login'), button:text-is('Sign in')"
    ERROR_CONTAINERS = ".error-message, [role='alert'], [class*='error' i]"
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

File: `.github/workflows/test.yml`. **Manual dispatch only** — no push or schedule
trigger. Runs are started by hand (Actions → *BlazeUp Automation Tests* → *Run
workflow*), which also works from the GitHub Mobile app.

### Parameters (Jenkins-style "Build with Parameters")

| Input | Options | Notes |
|-------|---------|-------|
| `domain` | `blazeup_admin` / `blazeup_partner` / `all` | `all` fans out to parallel per-domain jobs |
| `mode` | `smoke` / `regression` / `normal` | Ignored when `execute` is filled in |
| `execute` | e.g. `12010101 12010102`, `1-10` | Specific TC IDs / ranges (wins over `mode`) |
| `excel` | checkbox | Export Excel report (per-domain `REPORT_EXCEL`) |
| `ai_triage` | checkbox | Run AI failure triage (per-domain `REPORT_AI_TRIAGE`) |

### Pipeline per run

```
setup (resolve params) → tests[matrix: domain] → publish-report[matrix: domain]
```
Each `tests` job: maps domain secrets → runs `python -m runner.<domain>.run_test`
→ on failure auto-generates `ai_triage.md` → uploads artifacts → sends a **Telegram**
summary (+ triage file). `publish-report` deploys an **Allure trend dashboard** to
GitHub Pages: `https://<owner>.github.io/<repo>/<domain>/`.

### Required GitHub secrets

| Secret | Purpose |
|--------|---------|
| `ADMIN_BASE_URL`, `ADMIN_API_BASE_URL`, `ADMIN_TEST_EMAIL`, `ADMIN_TEST_PASSWORD` | blazeup_admin |
| `PARTNER_BASE_URL`, `PARTNER_API_BASE_URL`, `PARTNER_TEST_EMAIL`, `PARTNER_TEST_PASSWORD` | blazeup_partner |
| `GROQ_API_KEY` | AI triage (Groq) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Telegram notifications (shared fallback) |
| `TELEGRAM_CHAT_ID_BLAZEUP_<DOMAIN>` | *(optional)* per-team channel routing |

> Workflow permissions must allow **Read and write** (Settings → Actions → General)
> for the dashboard deploy. Adding a domain → **[add-domain.md](add-domain.md)**.

### Registry validation step

CI runs `python utils/sync_registry.py` and checks `runner/*/registry.py` is unchanged.
If a test file was added/removed without re-syncing, the build fails:

```
::error::A runner/{domain}/registry.py is out of sync. Run 'python utils/sync_registry.py' and commit.
```

**Fix:** run `python utils/sync_registry.py` locally and commit the updated registry.
(The pre-commit hook does this for you automatically.)

---

## 12b. Code Quality (lint + format + pre-commit)

Ruff (lint + formatter) + pre-commit hooks keep the codebase consistent. Config in
`pyproject.toml` and `.pre-commit-config.yaml` (local hooks — work offline).

```powershell
pip install -r requirements-dev.txt   # ruff + pre-commit
pre-commit install                     # one-time per clone

ruff check . --fix                     # lint + autofix
ruff format .                          # format
pre-commit run --all-files             # run all hooks manually
```

On `git commit`, hooks auto-run ruff (lint + format) and re-sync the TC registry.
If a hook modifies files, the commit pauses → review + re-`git add` → commit again.

> Line endings are normalized to **LF** repo-wide (`.gitattributes` + ruff
> `line-ending = "lf"`); generated `registry.py` files are excluded from ruff via
> `force-exclude` so the formatter and `sync_registry` don't fight.

---

## 12c. Test Data Management (Faker + cleanup)

For CRUD tests, generate unique data and auto-clean it. See
**[test-data.md](test-data.md)**.

```python
from utils.data_factory import make_tenant   # unique, QA-AUTO tagged payloads

async def test_create_tenant_001(auth_client, created_resources):
    resp = await auth_client.post("/tenants", json=make_tenant(), expected_status=201)
    tenant_id = resp.json()["data"]["id"]
    created_resources.add(lambda: auth_client.delete(f"/tenants/{tenant_id}"))
    assert tenant_id   # tenant auto-deleted on teardown, pass or fail
```

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
