# BlazeUp HRMS Automation User Guide

This guide explains how to work with the BlazeUp HRMS automation framework after the project cleanup.

## 1. Architecture

The framework has two automation layers:

- UI tests use Playwright async with Page Object Model classes in `pages/`.
- API tests use httpx clients and Pydantic schemas in `api/`.

Core support folders:

- `locator/`: page-specific UI locators such as `login_ui.py`, `home_ui.py`, and `expense_ui.py`.
- `pytest_support/`: reusable pytest fixtures and hooks. Root `conftest.py` only imports this package so pytest can discover fixtures normally.
- `runner/`: custom TC runner, registry, and execution helpers.
- `fixtures/`: YAML test data.
- `utils/`: shared helpers, screenshot attachment, and registry sync.

## 2. Important Files

- `runner/tc_registry.py`: maps TC IDs to pytest node IDs.
- `runner/run_test.py`: CLI entrypoint for running tests by TC ID, marker, type, or module.
- `runner/test_runner.py`: builds pytest commands, creates result folders, and prints summaries.
- `conftest.py`: thin pytest discovery entrypoint.
- `pytest_support/fixtures.py`: browser, page, auth, API token, settings, and test data fixtures.
- `pytest_support/hooks.py`: pytest report hook used for screenshot status.
- `pytest.ini`: pytest defaults, markers, HTML report, Allure output, and async mode.
- `config/settings.py`: typed runtime settings loaded from `.env`.
- `.env.example`: safe template for local `.env`.

## 3. Environment Setup

From the project root:

```powershell
cd "C:\Users\trang.le\Desktop\New folder\blazeup_automation"
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
```

Set real values in `.env`:

```env
BASE_URL=https://terralogic.blazeup.ai
API_BASE_URL=https://api.prod.blazeup.ai
TEST_EMAIL=your-user@example.com
TEST_PASSWORD=your-password
HEADLESS=true
BROWSER=chromium
SLOW_MO=0
DEFAULT_RESPONSE_TIME_MS=30000
VIEWPORT_WIDTH=1440
VIEWPORT_HEIGHT=900
```

Never commit `.env`.

Keep `API_BASE_URL` as the host only, for example `https://api.prod.blazeup.ai`.
The API clients add service prefixes such as `/auth-api` and `/time-api` internally.

## 4. Running Tests

Use the custom runner for official TC execution:

```powershell
python -m runner.run_test --execute 1001
python -m runner.run_test --execute 1001 1003 1005
python -m runner.run_test --execute 1001-1004
```

Run by registry metadata:

```powershell
python -m runner.run_test --list
python -m runner.run_test --marker smoke
python -m runner.run_test --type ui
python -m runner.run_test --type api
python -m runner.run_test --module login
```

Skip specific IDs:

```powershell
python -m runner.run_test --execute 1001-1005 --skip 1003 1005
```

Open Allure after a run:

```powershell
python -m runner.run_test --execute 1001 --serve
```

Use direct pytest while developing or debugging a new test:

```powershell
python -m pytest tests/ui/test_login.py::test_tc01_login_success_with_valid_credentials -s
python -m pytest tests/api/test_auth_api.py -s
```

Recommended workflow for a new TC:

1. Add or update locators in `locator/`.
2. Add page/API actions in `pages/` or `api/`.
3. Write the pytest test in `tests/`.
4. Debug it directly with `python -m pytest ... -s`.
5. Sync or update `runner/tc_registry.py`.
6. Run officially with `python -m runner.run_test --execute <TC_ID>`.

## 5. Test Case Registry

Numbering convention:

- API TCs: `1` to `1000`
- UI TCs: `1001` to `2000`

Examples:

```text
1    -> tests/api/test_auth_api.py::test_tca01_login_returns_jwt_token
1001 -> tests/ui/test_login.py::test_tc01_login_success_with_valid_credentials
```

To regenerate the registry from implemented tests:

```powershell
python utils/sync_registry.py
```

The sync utility writes to `runner/tc_registry.py`.

## 6. Results

Every `python -m runner.run_test ...` execution creates:

```text
results/run_YYYYMMDD_HHMMSS/
├── run_meta.json
├── report.html
├── logs/
│   └── test.log
├── screenshots/
├── videos/
├── traces/
└── allure-results/
```

Artifacts:

- `report.html`: pytest-html report for the run.
- `run_meta.json`: selected TC IDs, pytest node IDs, timestamp, and result path.
- `logs/test.log`: execution logs.
- `screenshots/`: final and failure screenshots.
- `videos/`: Playwright videos.
- `traces/`: Playwright trace archives.
- `allure-results/`: raw Allure result files.

Direct pytest runs still use `pytest.ini` defaults and may write:

```text
reports/pytest-report.html
allure-results/
```

To open Allure from inside `blazeup_automation`:

```powershell
allure serve results/run_YYYYMMDD_HHMMSS/allure-results
```

To open Allure from the parent folder, for example `C:\Users\trang.le\Desktop\New folder`:

```powershell
allure serve ".\blazeup_automation\results\run_YYYYMMDD_HHMMSS\allure-results"
```

If Allure shows `0 test cases`, the path is usually pointing to the wrong folder or an empty `allure-results` directory. Use the exact path printed by the runner after `Allure:`.

## 7. Makefile Shortcuts

```powershell
make tc 1001
make smoke
make regression
make api
make ui
make list
make report
```

On Windows, these shortcuts require `make`. If `make` is unavailable, use the `python -m runner.run_test ...` commands directly.

## 8. Troubleshooting

If pytest is not recognized:

```powershell
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If Chromium is missing:

```powershell
python -m playwright install chromium
```

If a UI test fails and you need details:

```powershell
python -m runner.run_test --execute 1001 --debug-log
```

If imports fail after moving files, run commands from the project root:

```powershell
cd "C:\Users\trang.le\Desktop\New folder\blazeup_automation"
```

If Allure cannot open, install Allure CLI and ensure it is on `PATH`.
