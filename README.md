# BlazeUp HRMS Automation Framework

Automation framework for BlazeUp HRMS using Playwright async, pytest, API clients with httpx, pytest-html, Allure results, and a TC-based custom runner.

## Structure

```text
blazeup_automation/
├── api/                  # API clients and response schemas
├── config/               # Runtime settings loaded from .env
├── fixtures/             # Test data files
├── locator/              # UI locators grouped by page
├── pages/                # Page Object Model classes
├── pytest_support/       # Shared pytest fixtures and hooks
├── runner/               # TC registry and custom runner
│   ├── run_test.py
│   ├── test_runner.py
│   └── tc_registry.py
├── tests/                # API and UI test suites
├── utils/                # Helpers and registry sync utility
├── conftest.py           # Thin pytest discovery entrypoint
├── pytest.ini            # Pytest defaults, markers, and reporting
├── requirements.txt
└── USER_GUIDE.md
```

Generated artifacts are written to `results/`, `reports/`, and `allure-results/`. These folders are runtime output and should not be committed.

## Setup

```powershell
cd "C:\Users\trang.le\Desktop\New folder\blazeup_automation"
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
```

Update `.env` with valid credentials:

```env
BASE_URL=https://terralogic.blazeup.ai
API_BASE_URL=API_BASE_URL = https://api.prod.blazeup.ai
TEST_EMAIL=your-user@example.com
TEST_PASSWORD=your-password
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
```

Do not commit `.env`.

## Run Tests

Run by TC ID:

```powershell
python -m runner.run_test --execute 1001
python -m runner.run_test --execute 1001 1003 1005
python -m runner.run_test --execute 1001-1004
```

Run by marker, type, or module:

```powershell
python -m runner.run_test --marker smoke
python -m runner.run_test --type ui
python -m runner.run_test --type api
python -m runner.run_test --module login
```

List registered TCs:

```powershell
python -m runner.run_test --list
```

Run directly with pytest while developing or debugging a new test:

```powershell
python -m pytest tests/ui/test_login.py -s
python -m pytest tests/ui/test_login.py::test_tc01_login_success_with_valid_credentials -s
```

## Results

Each custom runner execution creates a timestamped folder:

```text
results/run_YYYYMMDD_HHMMSS/
├── run_meta.json
├── report.html
├── logs/test.log
├── screenshots/
├── videos/
├── traces/
└── allure-results/
```

Open a pytest HTML report directly from `results/run_.../report.html`, or serve Allure.

If your terminal is already inside `blazeup_automation`:

```powershell
allure serve results/run_YYYYMMDD_HHMMSS/allure-results
```

If your terminal is in the parent folder, for example `C:\Users\trang.le\Desktop\New folder`:

```powershell
allure serve ".\blazeup_automation\results\run_YYYYMMDD_HHMMSS\allure-results"
```

See [USER_GUIDE.md](USER_GUIDE.md) for the full workflow and troubleshooting notes.
