# Page Object / Locator / Fixture Conventions

Standard document for the UI automation layer. Follow these conventions exactly so that new code is
consistent and easy to maintain.

## Layering (3 separate tiers)

```
locators/<domain>/<x>_locators.py   →  DATA: contains selector strings only
pages/<domain>/<x>_page.py          →  BEHAVIOR: actions + assertions
tests/<domain>/ui/test_<x>.py       →  SCENARIO: calls the page object, asserts
```

Principle: **a test never hard-codes selectors** — selectors live only in
`locators/`. The test calls page object methods, and the page object uses locators.

## Naming conventions (MANDATORY)

| Type | File | Class | Example |
|---|---|---|---|
| Locator | `<x>_locators.py` | `<X>Locators` | `login_locators.py` → `LoginLocators` |
| Page object | `<x>_page.py` | `<X>Page(BasePage)` | `shell_page.py` → `ShellPage` |
| Test | `test_<x>.py` | function `test_<scope>_<feature>_NNN` | `test_shell_ui_page_loads_001` |

> Use the suffix **`Locators`** (not `Selectors`) to match the `locators/` directory
> and Playwright's original terminology (`Locator`).

## Locator — just data

```python
# locators/blazeup_admin/login_locators.py
class LoginLocators:
    """Login page locators."""
    IDENTIFIER_INPUT = "input[type='email'], input[name*='email' i]"
    PASSWORD_INPUT = "input[type='password']"
```
- Prefer stable hooks: `[data-testid=...]` > role/text > CSS class.
- Do not put logic here — string constants only.

## Page object — inherit from `BasePage`

```python
# pages/blazeup_admin/login_page.py
from locators.blazeup_admin.login_locators import LoginLocators
from pages.base_page import BasePage

class LoginPage(BasePage):
    async def login(self, email: str, password: str) -> None:
        await self.fill(LoginLocators.IDENTIFIER_INPUT, email, label="Email Input")
        await self.click(LoginLocators.PROCEED_BUTTON, label="Proceed")
```
- Always inherit from `BasePage(page, base_url)` to get `goto/click/fill/get_text` out of the box
  (which already include retry, STEP logging, password masking).
- Methods are **business actions** (`login`, `open_dashboard`), not raw Playwright operations.

## Creating a page object in a test — use `make_page`

An **already logged-in** page object (most cases):
```python
async def test_dashboard_ui_visible_001(make_page):
    shell = make_page(ShellPage)        # concise — no need to pass page + base_url
    dash  = make_page(DashboardPage)
    await shell.open("dashboard")
```

A **not-yet-logged-in** flow (e.g. the login page) — build it directly with the `page` fixture:
```python
async def test_login_invalid(page, settings):
    login = LoginPage(page, str(settings.base_url))
    await login.open()
```

## Main fixtures (defined in `pytest_support/fixtures.py`)

| Fixture | Scope | Use when |
|---|---|---|
| `settings` | session | Runtime configuration (URL, browser, credentials) |
| `page` | function | Page that is **not** logged in (login test / no auth needed) |
| `authenticated_page` | function | Page that **is** logged in (isolated context per test, login once per run) |
| `make_page` | function | Factory that builds an already-logged-in page object |
| `auth_state` | session | Log in via UI once, cache the storage state |
| `api_token` | session | API token shared across all API tests |
| `auth_client` / `attendance_client` | function | API client with the token already attached |
| `fake` / `test_user` | session/func | Generate dynamic test data (Faker) |

Rule: **log in only once per run** (session-scoped), but **one isolated context per test**
(no sharing of cookies/state between tests).

## Adding a new page/section — checklist
1. `locators/<domain>/<x>_locators.py` → class `<X>Locators` (selectors).
2. `pages/<domain>/<x>_page.py` → class `<X>Page(BasePage)` (actions).
3. `tests/<domain>/ui/test_<x>.py` → test calls `make_page(<X>Page)`.
4. Name the test `test_<scope>_<feature>_NNN` so `sync_registry` maps to the correct TC.
