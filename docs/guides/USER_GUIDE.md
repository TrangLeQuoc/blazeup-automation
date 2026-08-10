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
│            runner/blazeup/run_test.py                                 │
│   Entry point: scopes the run to the blazeup registry, sets defaults  │
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
│ conftest.py → fixtures.py (session: api_token, partner_auth_state)│
│ tests/{domain}/{api|ui}/{module}/**                               │
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

**One `blazeup` domain, two actors:**

SA/admin and partner are two actors inside one domain (they share one API gateway
and one test suite). The framework has:
- One `.env` (`config/blazeup/.env`) with `ADMIN_*` + `PARTNER_*` keys
- One TC registry (`runner/blazeup/registry.py`)
- One CLI entry point (`runner/blazeup/run_test.py`)

The shared runner merges all domain registries at runtime.

**Two test layers:**

| Layer | Tech | Location |
|-------|------|----------|
| API | `httpx` + `Pydantic` models | `api_clients/{domain}/{module}/` + `tests/{domain}/api/{module}/` |
| UI | `Playwright` async + Page Object Model | `pages/{domain}/` + `tests/{domain}/ui/{module}/` |

> **Module layer:** tests and API clients are grouped by module under the domain
> (e.g. `tests/blazeup/api/partner/`, `api_clients/blazeup/admin/partner/`).
> TC IDs come from the test **function name**, not the path — moving a test between
> folders never changes its ID (`sync_registry` scans recursively). Only shared
> infra stays at the domain root: `api_clients/{domain}/auth_client.py`,
> `api_clients/base_client.py`. Add a new module = new subfolder under each of
> `api_clients/{domain}/`, `tests/{domain}/api/` (and `ui/`).

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
| Python | 3.13 | pinned in all 3 CI workflows; Ruff targets `py313` |
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

# 5. Create your .env file  (it lives under config/blazeup/, NOT the repo root)
copy .env.example config/blazeup/.env      # Windows
# cp .env.example config/blazeup/.env      # macOS / Linux

# 6. Edit .env with real credentials (see Section 3)

# 7. Sync the TC registry
python utils/sync_registry.py

# 8. Verify everything works
python -m runner.run_test --list
```

---

## 3. Configuration Reference

One `.env` file drives everything: **`config/blazeup/.env`** (gitignored, never committed).
Copy the template and edit it:

```powershell
copy .env.example config/blazeup/.env
```

`config/settings.py` is the single authority — the table below is generated from it. Two
fields are **required**; a missing one makes `get_settings()` fail fast on the first test.

### The one .env file

```env
# ── Required ─────────────────────────────────────────────────────────────────
API_BASE_URL=https://api.stg.blazeup.ai      # shared gateway for BOTH actors
ADMIN_BASE_URL=https://stgsa.blazeup.ai      # SA/admin UI origin

# ── SA / admin actor ─────────────────────────────────────────────────────────
ADMIN_EMAIL=your-sa-user@example.com
ADMIN_PASSWORD=your-password

# ── Partner actor (only for partner-portal tests) ────────────────────────────
PARTNER_BASE_URL=https://stgpartners.blazeup.ai
PARTNER_EMAIL=your-partner-user@example.com
PARTNER_PASSWORD=your-password
PARTNER_TOTP_SECRET=                          # base32 setup key; the portal now has 2FA

# ── Browser / timing ─────────────────────────────────────────────────────────
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
DEFAULT_RESPONSE_TIME_MS=30000

# ── AI failure triage (optional) ─────────────────────────────────────────────
AI_PROVIDER=gemini
AI_MODEL=gemini-2.0-flash
GEMINI_API_KEY=
```

> **One domain, two actors.** There is no separate partner `.env`. SA/admin and partner
> share one API gateway and one suite; they are told apart by the `ADMIN_*` / `PARTNER_*`
> keys in this single file. The generic aliases `settings.base_url` / `test_email` /
> `test_password` resolve to the **`ADMIN_*`** values, since most setup runs as the SA actor.

### Settings reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `API_BASE_URL` | **yes** | — | API root, shared by both actors. Must NOT equal a UI origin — `settings.py` rejects that to catch pointing API calls at a UI server |
| `ADMIN_BASE_URL` | **yes** | — | SA UI origin; browser `base_url` + `Origin` header |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | no | `None` | SA login. Unset → SA tests skip as BLOCKED |
| `PARTNER_BASE_URL` | no | `None` | Partner-portal origin. Unset → partner UI tests skip as BLOCKED |
| `PARTNER_EMAIL` / `PARTNER_PASSWORD` | no | `None` | Partner-portal login |
| `PARTNER_TOTP_SECRET` | no | `None` | Base32 enrolment key for the portal's 2FA step (`pyotp` generates the code). Leave empty if the account has no 2FA |
| `HEADLESS` | no | `true` | `false` = visible browser |
| `BROWSER` | no | `chromium` | `chromium` / `firefox` / `webkit` |
| `SLOW_MO` | no | `0` | ms delay between Playwright actions |
| `DEFAULT_RESPONSE_TIME_MS` | no | `30000` | Per-call response-time SLA. A breach **fails** the call (setup calls raise it to 45 s instead of disabling it) |
| `VIEWPORT_WIDTH` / `VIEWPORT_HEIGHT` | no | `1440` / `900` | Browser viewport (the `mobile` marker overrides it to 375×812) |
| `AI_PROVIDER` | no | `gemini` | `gemini` / `groq` / `ollama` — only the selected provider's key is needed |
| `AI_MODEL` | no | `gemini-2.0-flash` | Model for `utils/ai_triage.py` |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | no | `None` | Key for the selected AI provider |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | Local Ollama endpoint |

> `DEFAULT_RESPONSE_TIME_MS` is a **hard** check, not a warning: exceeding it fails the
> call. It is deliberately generous, and the breach is deliberately **not** retried —
> see [Auto-retry of transient failures](#flaky-tests).

> **Tip:** `HEADLESS=false` + `SLOW_MO=500` while writing a new UI test, to watch the
> browser in real time.

---

## 4. Running Tests

### 4.1 Domain-specific runner (recommended)

**BlazeUp Admin (HRMS):**
```powershell
python -m runner.blazeup.run_test
python -m runner.blazeup.run_test --execute 1 2 3
python -m runner.blazeup.run_test --mode smoke
```

**BlazeUp Partner Platform:**
```powershell
python -m runner.blazeup.run_test
python -m runner.blazeup.run_test --execute 1010101 1010102
python -m runner.blazeup.run_test --mode regression
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

> **Note:** Direct pytest writes Allure data to `allure-results/` (root-level, overwritten each run), not to a timestamped `results/run_*/` folder. View with `allure serve allure-results`.

### 4.3 Defaults you can change in `run_test.py`

Open `runner/run_test.py` and edit these constants at the top — no CLI flags needed:

```python
# Which TCs to run when no --execute / --mode is passed.
# EMPTY = every registered TC (API + UI). This is the default and should stay that way.
DEFAULT_EXECUTE_IDS: list[str] = []

# IDs to always skip (blacklist)
DEFAULT_SKIP_IDS: list[str] = []

# Export Excel report by default (True/False)
REPORT_EXCEL: bool = True
```

> **Do not narrow the default here.** It used to hold an API-only range, so a plain
> run quietly skipped all 32 UI test cases and a green result meant "every API test
> passed" — a scope limit invisible in the output. Scope a run on the command line
> instead, where it is visible in the summary header:
>
> ```powershell
> python -m runner.blazeup.run_test --execute 2060101-2061211   # API only
> python -m runner.blazeup.run_test --type ui                   # UI only
> ```

---

## 5. TC Registry & ID System

### 5.1 What is the registry?

`runner/tc_registry.py` is the **single source of truth** that maps a numeric TC ID to:
- the pytest node path (`test_path::test_func`)
- metadata (title, priority, type, module, markers)
- `tc_string` — the ID in `Partner_Platform_Test_Plan.xlsx`

It is **auto-generated** by `utils/sync_registry.py` — do not edit it manually.

### 5.2 ID ranges

IDs are **derived from the function name**, never assigned sequentially — so the ranges
below are a consequence of the formula in §5.3, not a registry to maintain.

| ID shape | Type | Count today | Example |
|----------|------|-------------|---------|
| 7 digits, starts `2` | API (type digit `0` is dropped by `int()`) | 92 | `2060101` = `PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001` |
| 8 digits, starts `12` | UI | 32 | `12010101` = `SHELL_UI_LOAD_TIME_PAGE_001` |

Every TC in the registry today belongs to the `blazeup` domain (project digit `2`). The
demo/legacy `test_tc*` numbering the scanner still supports is no longer used by any test
— `sync_registry` reports `0 legacy TCs found`.

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
python utils/sync_registry.py                    # sync the blazeup registry
python utils/sync_registry.py --table            # just print the TC-ID reference table
```

What it does:
1. Scans `tests/blazeup/**/*.py` for functions matching `test_partner_{ui|api}_*_NNN`.
2. Looks up title and priority from `docs/blazeup/Partner_Platform_Test_Plan.xlsx`
   (falls back to the function docstring + `P2` if no Excel file exists).
3. Scans legacy `test_tc*` / `test_tca*` functions and assigns sequential IDs.
4. Writes **one file per top-level module** under `runner/blazeup/registry_modules/`
   (`partner.py`, `shell.py`, …) so per-module PRs don't collide, plus the aggregator
   `runner/blazeup/registry.py` that globs + merges them.

`runner/tc_registry.py` then auto-merges every `runner/*/registry.py` into one central
`TC_REGISTRY` at import time. Filtering (`--module`, `--marker`, `--execute`) runs on the
merged registry — file layout doesn't affect how you select tests.

> CI also runs this and will fail the build if any `runner/blazeup/registry.py`
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

Available markers (defined in `pytest.ini`): `smoke`, `regression`, `ui`, `api`, `be_gap`, `mobile`.

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
| **K — Auto** | `YES` (marks row as covered by automation) |
| **L — Automation Status** | `PASSED` / `FAILED` / `BLOCKED` / `NOT_STARTED` |
| **I — Status** | Formula — auto-recomputes in Excel when you open the file (never written) |

Only columns **K** and **L** are written; everything else (incl. Manual Status in **J**) is left as-is. Column positions are configurable per domain — see §7.6.

### 7.2 Outcome mapping

| pytest result | Automation Status written |
|---|---|
| PASSED | `PASSED` |
| FAILED / ERROR | `FAILED` |
| BLOCKED (env/precondition down — login/service 5xx) | `BLOCKED` |
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

### 7.6 Add a new sheet (config-driven, no code change)

The reporter reads which sheets to write — and the column positions — from
`config/<domain>/config.yaml` (block `excel:`). To cover a new tab (e.g. `Tenant`),
add its name to `excel.sheets`; no code change:

```yaml
# config/blazeup/config.yaml
excel:
  sheets:
    - "Partner Platform"
    - "Tenant"            # ← add the new tab name
  col_tc_string: 3        # C: Test Case Name (lookup key)
  col_auto_flag: 11       # K: Auto
  col_auto_status: 12     # L: Automation Status
  data_start_row: 13      # first data row
```

The new tab must share the column layout above (Test Case Name in **C**, Auto in
**K**, Automation Status in **L**, data from **row 13**). The reporter matches each
TC by its name in column C and writes K + L; a sheet not present in the workbook is
skipped safely. Defaults (used when the block/key is absent) live in
`utils/excel_reporter.py`.

> If the new tab uses a *different* column layout, adjust `col_*` / `data_start_row`
> — but those apply to all listed sheets, so keep the layout consistent (or split
> into a separate domain/plan file).

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

**Allure** (steps, screenshots, timeline — the primary report):
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
allure-results/               # root-level (overwritten each run) — view with `allure serve allure-results`
```

---

## 10. Fixtures Reference

All fixtures are defined in `pytest_support/fixtures.py` and auto-discovered via `conftest.py`.

### Session-scoped (created once per test session)

| Fixture | Type | Description |
|---------|------|-------------|
| `settings` | `Settings` | Pydantic config loaded from `config/blazeup/.env` |
| `result_dir` | `Path` | Timestamped run folder; configures loguru sinks |
| `fake` | `Faker` | Faker instance for generating test data |
| `partner_auth_state` | `dict` | Partner-portal storage state from ONE login (incl. the 2FA step). Only the partner side caches a snapshot — see the note below |
| `api_token` | `str` | **Session-scoped**: One JWT per session; reused across all API tests. Avoids repeated login. |

### Function-scoped (created fresh per test)

| Fixture | Type | Description |
|---------|------|-------------|
| `browser_context` | `BrowserContext` | Unauthenticated Playwright context with viewport + tracing |
| `page` | `Page` | Fresh unauthenticated Playwright page; takes screenshot on finish |
| `test_user` | `dict` | Generated user dict (`first_name`, `last_name`, `email`, `department`) |
| `auth_client` | `AuthClient` | Authenticated API client (token from session `api_token`); auto-closed |
| `sa_partners_client` | `SaPartnersClient` | SA partner-module API client (token from session `api_token`); auto-closed |
| `sa_deals_client` | `SaDealsClient` | SA deals API client; auto-closed |
| `sa_commissions_client` | `SaCommissionsClient` | SA commissions API client; auto-closed |
| `sa_cleanup` | `SaCleanup` | Deletes records a UI test created. Logs in **lazily** and never blocks the test — see `utils/ui_cleanup.py` |
| `authenticated_page` | `Page` | SA page, **freshly logged in for every test** (not a cached snapshot — see the note below) |
| `partner_authenticated_page` | `Page` | Partner-portal page; fresh context per test, reusing the cached `partner_auth_state`. Honours the `mobile` marker (375×812) |
| `make_page` | factory | Build an SA page object without boilerplate: `make_page(ShellPage)` |
| `make_partner_page` | factory | Same, bound to the partner-portal origin |
| `created_resources` | registry | Track resources a test creates → auto-delete on teardown (LIFO), pass or fail |
| `tc_logger` *(autouse)* | — | Emits START / PASSED / FAILED / SKIPPED banners; binds the TC ID to every log line |

> **Why the two sides differ:** stgsa's SA auth uses a rotating, single-use refresh
> cookie — replaying one captured `storage_state` in a second context 401s and the SA
> micro-frontend never renders. So the SA side logs in fresh per test, while the partner
> portal (which does not rotate) shares one cached snapshot. See the docstrings in
> `pytest_support/fixtures.py`.

### Usage examples

```python
# API test — use auth_client
async def test_tca04_get_me_returns_user_info(auth_client):
    response = await auth_client.me()
    assert response.email is not None

# UI test — use page (unauthenticated)
async def test_tc02_login_fails_with_wrong_password(page, settings):
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
| `base_client.py` | `BaseClient` | `request()`, `get()`, `post()`, `put()`, `patch()`, `delete()` — retry on 5xx for idempotent methods only, response-time SLA, Pydantic schema validation, secret masking |
| `auth_base.py` | `BaseAuthClient` | `login()`, `logout()`, `me()` — shared login mechanics |
| `blazeup/admin/auth_client.py` | `AuthClient` | SA login + current-user (sa-auth-api) |
| `blazeup/admin/partner/sa_partners_client.py` | `SaPartnersClient` | `list_partners()`, `create_partner()`, `approve_partner()`, `deactivate_partner()`, `delete_partner()`, partner-users, certifications, territories, audit logs |
| `blazeup/admin/partner/sa_deals_client.py` | `SaDealsClient` | `register_deal()`, `approve_deal()`, `extend_protection()`, `win_deal()`, `lose_deal()`, `resolve_conflict()` |
| `blazeup/admin/partner/sa_commissions_client.py` | `SaCommissionsClient` | `list_commissions()`, `list_rate_table()`, `upsert_rate()` |
| `blazeup/partner/auth_client.py` | `PartnerAuthClient` | Partner-portal login (separate JWT issuer, TOTP) |
| `blazeup/partner/deal_registration_client.py` | `DealRegistrationClient` | Partner-side deal registration (**scaffold**) |

> Every write method has a `raw_*` twin (`raw_create_partner`, `raw_approve_deal`, …) that
> skips schema/status assertions, so negative tests can inspect a 400 body directly.

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
# locators/blazeup/admin/login_locators.py
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
| `mode` | `smoke` / `regression` / `normal` | Ignored when `execute` is filled in |
| `execute` | e.g. `2061001 2061002`, `2060201-2060220` | Specific TC IDs / ranges (wins over `mode`) |
| `excel` | checkbox | Export Excel report |
| `ai_triage` | checkbox | Run AI failure triage |

### Pipeline per run

```
tests → publish-report
```
The `tests` job maps secrets → runs `python -m runner.blazeup.run_test` → on failure
auto-generates `ai_triage.md` → uploads artifacts → sends a **Telegram** summary
(+ triage file). `publish-report` deploys an **Allure trend dashboard** to GitHub
Pages: `https://<owner>.github.io/<repo>/blazeup/`.

### Required GitHub secrets

Secret names match the `.env` keys 1:1 (CI writes them straight to the environment):

| Secret | Purpose |
|--------|---------|
| `API_BASE_URL` | shared API gateway |
| `ADMIN_BASE_URL`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | SA UI origin + login |
| `PARTNER_BASE_URL`, `PARTNER_EMAIL`, `PARTNER_PASSWORD` | Partner UI origin + login |
| `GROQ_API_KEY` | AI triage (Groq) |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Telegram notifications |

> Store all of these as **Secrets** (not Variables) so credentials are masked in logs.

> Workflow permissions must allow **Read and write** (Settings → Actions → General)
> for the dashboard deploy.

### Registry validation step

CI runs `python utils/sync_registry.py` and checks `runner/*/registry.py` is unchanged.
If a test file was added/removed without re-syncing, the build fails:

```
::error::A runner/blazeup/registry.py is out of sync. Run 'python utils/sync_registry.py' and commit.
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
**Fix:** Check `config/blazeup/.env` has correct `ADMIN_EMAIL` / `ADMIN_PASSWORD` (and `PARTNER_*` if the failing test is a portal one). Test manually:
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

### "Environment is not usable — aborting before any test runs" (exit 6)

**Problem:** the run stops immediately with a `Preflight` table showing a FAIL row.

**Meaning:** the surface those tests need is unreachable *before* a single test starts —
a dead API gateway, a DNS failure, or a TLS certificate the browser refuses. Nothing ran,
so this is **not** a product regression.

The gate probes only what the selected TCs actually use, so an API-only run is never
blocked by a UI portal being down:

| Selection contains | Probed |
|---|---|
| any `api` TC | API gateway (httpx) |
| a partner-portal UI TC (`PARTNER_PORTAL_SHELL`, `MY_PIPELINE`, `COMMISSIONS`, `DASHBOARD`, `PARTNER_TEAM`) | `PARTNER_BASE_URL` **in Chromium** |
| any other UI TC | `ADMIN_BASE_URL` **in Chromium** |

UI origins are probed with Chromium, not httpx, on purpose: the two do not share a trust
store. On 2026-08-07 Python verified `stgpartners.blazeup.ai`'s certificate while Chromium
rejected it — an httpx probe would have reported the environment healthy and let 21 partner
UI TCs go BLOCKED one by one.

**Fix:** wait for the environment, then re-run. To run anyway (e.g. to reproduce the
failure yourself): `--no-preflight`.

> **Only one surface is down?** The gate is all-or-nothing: if the partner portal is
> unreachable it stops the whole run, including the API and SA UI tests that would pass.
> When that happens, re-run with `--no-preflight` — the tests bound to the dead surface
> report BLOCKED (their fixture fails fast) and everything else runs normally:
>
> ```powershell
> python -m runner.blazeup.run_test --no-preflight
> ```

> A single dead microservice does **not** abort the run — only a fault that would doom
> every test does. Use `make health` for the per-service picture.

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

#### Auto-retry of transient failures (off by default)

The runner can re-run a failed test, but **only** when the failure matches a whitelist of
transient signatures (`_RERUN_PATTERNS` in `runner/test_runner.py`) — a genuine assertion
failure is never retried.

```powershell
$env:BLAZEUP_UI_RERUNS = "2"    # 0 = disabled (the default)
$env:BLAZEUP_RERUN_DELAY = "3"  # seconds between attempts
```

Retried: Playwright timeouts · `did not render` (MFE cold load) · `Failed to fetch
dynamically imported module` · gateway `502/503/504` · `ECONNREFUSED` / `ECONNRESET` ·
httpx `ReadTimeout` / `ConnectTimeout` / `PoolTimeout` / `WriteTimeout`.

**Deliberately NOT retried — do not add it back:** the response-time SLA breach
(`response time … exceeded limit …`). Retrying it hides the very regression it exists to
catch — an *intermittently* slow endpoint would go green on a retry, and only a
permanently slow one would survive. The SLA is already generous (30 s normal, 45 s setup),
so a breach is a finding, not noise; `base_client` also logs a `SLOW:` warning on every one.

The 5xx patterns are anchored (`\b50[234]\b`) so they match `got 502:` but not digits that
merely happen to appear inside a mongo id (`…0158503`) or a duration (`5502ms`) — with the
bare substrings, real assertion failures carrying such ids were being retried.

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
