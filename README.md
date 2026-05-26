# BlazeUp Automation Framework

End-to-end automation framework for the **BlazeUp Partner Platform** (HRMS).  
Covers both **API** (httpx + Pydantic) and **UI** (Playwright async + Page Object Model) layers.

> Full workflow, naming conventions, and troubleshooting → **[USER_GUIDE.md](USER_GUIDE.md)**

---

## Quick Start

### 1. Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11 + | [python.org](https://python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Allure CLI | any | `scoop install allure` / `brew install allure` |

### 2. Clone & setup

```powershell
git clone <repo-url>
cd blazeup_automation

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Configure credentials

```powershell
copy .env.example .env
```

Edit `.env`:

```env
BASE_URL=https://terralogic.blazeup.ai
API_BASE_URL=https://api.prod.blazeup.ai
TEST_EMAIL=your-email@example.com
TEST_PASSWORD=your-password
HEADLESS=true
```

> **Never commit `.env`** — it is listed in `.gitignore`.

### 4. Sync the TC registry

```powershell
python utils/sync_registry.py
```

### 5. Run tests

```powershell
# Run default TCs (set in run_test.py → DEFAULT_EXECUTE_IDS)
python -m runner.run_test

# Run specific TC IDs
python -m runner.run_test --execute 1010101 1010102

# Run all smoke-marked TCs
python -m runner.run_test --mode smoke

# List all registered TCs
python -m runner.run_test --list
```

---

## Project Structure

```text
blazeup_automation/
│
├── api/                        # HTTP clients (httpx + Pydantic)
│   ├── base_client.py          #   Retry, timing, schema validation
│   ├── auth_client.py          #   Login, logout, /current-user
│   ├── attendance_client.py    #   Attendance status endpoints
│   ├── expense_client.py       #   Expense endpoints
│   └── user_client.py          #   User management endpoints
│
├── config/
│   └── settings.py             # Typed settings from .env (Pydantic)
│
├── fixtures/
│   └── test_data.yaml          # Static test data (invalid users, locations…)
│
├── locator/                    # UI selectors grouped by page
│   ├── login_ui.py
│   ├── home_ui.py
│   └── …
│
├── pages/                      # Page Object Model
│   ├── base_page.py            #   goto, fill, click, wait_for_element
│   ├── login_page.py           #   Two-step login flow
│   ├── home_page.py            #   Dashboard, clock-in, logout
│   └── …
│
├── pytest_support/
│   ├── fixtures.py             # All shared pytest fixtures
│   └── hooks.py                # pytest_runtest_makereport hook
│
├── runner/
│   ├── tc_registry.py          # AUTO-GENERATED — TC ID → test node map
│   ├── run_test.py             # CLI entrypoint (modes, filters, repeat)
│   └── test_runner.py          # Subprocess runner, summary, Excel export
│
├── tests/
│   ├── api/
│   │   ├── test_auth_api.py         # TCs 5-9  (auth endpoints)
│   │   └── test_attendance_api.py   # TCs 1-4  (attendance endpoints)
│   └── ui/
│       ├── test_login.py            # TCs 10-13 (login flow)
│       └── partner_portal_shell/
│           └── test_partner_ui_partner_portal_shell.py  # 1010101-1010103
│
├── utils/
│   ├── sync_registry.py        # Regenerates tc_registry.py from test files
│   ├── excel_reporter.py       # Writes results back to test-plan .xlsx
│   ├── helpers.py              # load_yaml, require_credentials
│   ├── log_helper.py           # Custom log levels: STEP, START, PASSED, FAILED
│   └── screenshot_on_fail.py   # Allure screenshot attachment
│
├── Partner_Platform_Test_Plan.xlsx   # Source of truth for TC metadata
├── conftest.py                       # Thin pytest discovery entrypoint
├── pytest.ini                        # Markers, asyncio mode, HTML/Allure paths
├── requirements.txt
├── Makefile                          # Shortcuts (requires make)
├── README.md                         # ← you are here
└── USER_GUIDE.md                     # Full workflow & reference
```

---

## Test IDs at a Glance

| Range | Layer | Module | Example |
|-------|-------|--------|---------|
| 1 – 4 | API | Attendance | `1` = requires-token |
| 5 – 9 | API | Auth | `5` = login-returns-JWT |
| 10 – 13 | UI | Login | `10` = login-success |
| 1 010 101 + | UI | Partner Platform | `1010101` = shell-navigate |

---

## Key Commands

```powershell
# Run by TC IDs or range
python -m runner.run_test --execute 5 6 7
python -m runner.run_test --execute 1010101-1010103

# Run by mode
python -m runner.run_test --mode smoke
python -m runner.run_test --mode regression

# Stability / flaky detection
python -m runner.run_test --execute 10 --repeat 5 --repeat-mode each

# Export results to Excel (on by default)
python -m runner.run_test                          # exports Excel
python -m runner.run_test --no-excel-report        # skip Excel

# Sync registry after adding new tests
python utils/sync_registry.py

# Direct pytest (development / debugging)
python -m pytest tests/ui/test_login.py -s
```

---

## Output Artifacts

Each run creates a timestamped folder:

```text
results/run_YYYYMMDD_HHMMSS/
├── report.html                          # pytest-html report
├── run_meta.json                        # TC IDs, timestamps, node IDs
├── logs/test.log                        # Full loguru log
├── screenshots/                         # Final + failure screenshots
├── videos/                              # Playwright video recordings
├── traces/                              # Playwright trace archives
├── allure-results/                      # Raw Allure data
├── allure-report/                       # Generated static Allure HTML
└── Partner_Platform_Test_Plan_result_YYYYMMDD_HHMMSS.xlsx  # Excel report
```

---

## CI / CD

GitHub Actions runs on every push to `main` / `develop` and on a nightly schedule:

| Job | Trigger | TCs |
|-----|---------|-----|
| `smoke` | push / manual | `@pytest.mark.smoke` |
| `regression` | nightly 02:00 UTC | `priority = P1` |

Secrets required: `BASE_URL`, `API_BASE_URL`, `TEST_EMAIL`, `TEST_PASSWORD`.

See `.github/workflows/test.yml` for full configuration.
