# Quy ước Page Object / Locator / Fixture

Tài liệu chuẩn cho lớp UI automation. Theo đúng các quy ước này để code mới nhất
quán và dễ bảo trì.

## Phân lớp (3 tầng tách biệt)

```
locators/<domain>/<x>_locators.py   →  DỮ LIỆU: chỉ chứa chuỗi selector
pages/<domain>/<x>_page.py          →  HÀNH VI: actions + assertions
tests/<domain>/ui/test_<x>.py       →  KỊCH BẢN: gọi page object, assert
```

Nguyên tắc: **test không bao giờ hard-code selector** — selector chỉ sống trong
`locators/`. Test gọi method của page object, page object dùng locator.

## Quy ước đặt tên (BẮT BUỘC)

| Loại | File | Class | Ví dụ |
|---|---|---|---|
| Locator | `<x>_locators.py` | `<X>Locators` | `login_locators.py` → `LoginLocators` |
| Page object | `<x>_page.py` | `<X>Page(BasePage)` | `shell_page.py` → `ShellPage` |
| Test | `test_<x>.py` | hàm `test_<scope>_<feature>_NNN` | `test_shell_ui_page_loads_001` |

> Dùng hậu tố **`Locators`** (không phải `Selectors`) cho khớp thư mục `locators/`
> và thuật ngữ gốc của Playwright (`Locator`).

## Locator — chỉ là dữ liệu

```python
# locators/blazeup_admin/login_locators.py
class LoginLocators:
    """Login page locators."""
    IDENTIFIER_INPUT = "input[type='email'], input[name*='email' i]"
    PASSWORD_INPUT = "input[type='password']"
```
- Ưu tiên hook ổn định: `[data-testid=...]` > role/text > CSS class.
- Không đặt logic ở đây — chỉ hằng chuỗi.

## Page object — kế thừa `BasePage`

```python
# pages/blazeup_admin/login_page.py
from locators.blazeup_admin.login_locators import LoginLocators
from pages.base_page import BasePage

class LoginPage(BasePage):
    async def login(self, email: str, password: str) -> None:
        await self.fill(LoginLocators.IDENTIFIER_INPUT, email, label="Email Input")
        await self.click(LoginLocators.PROCEED_BUTTON, label="Proceed")
```
- Luôn kế thừa `BasePage(page, base_url)` để có sẵn `goto/click/fill/get_text`
  (đã kèm retry, logging STEP, mask password).
- Method là **hành động nghiệp vụ** (`login`, `open_dashboard`), không phải thao
  tác Playwright thô.

## Tạo page object trong test — dùng `make_page`

Page object **đã đăng nhập** (đa số trường hợp):
```python
async def test_dashboard_ui_visible_001(make_page):
    shell = make_page(ShellPage)        # gọn — không cần truyền page + base_url
    dash  = make_page(DashboardPage)
    await shell.open("dashboard")
```

Luồng **chưa đăng nhập** (vd trang login) — dựng trực tiếp với fixture `page`:
```python
async def test_login_invalid(page, settings):
    login = LoginPage(page, str(settings.base_url))
    await login.open()
```

## Fixtures chính (định nghĩa ở `pytest_support/fixtures.py`)

| Fixture | Scope | Dùng khi |
|---|---|---|
| `settings` | session | Cấu hình runtime (URL, browser, credentials) |
| `page` | function | Trang **chưa** đăng nhập (test login / không cần auth) |
| `authenticated_page` | function | Trang **đã** đăng nhập (context cô lập mỗi test, login 1 lần/run) |
| `make_page` | function | Factory dựng page object đã đăng nhập |
| `auth_state` | session | Login UI 1 lần, cache storage state |
| `api_token` | session | Token API dùng chung cho mọi API test |
| `auth_client` / `attendance_client` | function | API client đã gắn token |
| `fake` / `test_user` | session/func | Sinh test data động (Faker) |

Quy tắc: **login chỉ 1 lần mỗi run** (session-scoped), nhưng **mỗi test 1 context
cô lập** (không chia sẻ cookie/state giữa các test).

## Thêm 1 trang/section mới — checklist
1. `locators/<domain>/<x>_locators.py` → class `<X>Locators` (selector).
2. `pages/<domain>/<x>_page.py` → class `<X>Page(BasePage)` (action).
3. `tests/<domain>/ui/test_<x>.py` → test gọi `make_page(<X>Page)`.
4. Đặt tên test `test_<scope>_<feature>_NNN` để `sync_registry` map đúng TC.
