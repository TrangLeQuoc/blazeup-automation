# Quản lý test data (Faker + cleanup)

Mục tiêu: mỗi test có dữ liệu **độc nhất** (chạy song song không đụng nhau) và
**tự dọn** sau khi xong (staging luôn sạch, kết quả ổn định).

## 2 công cụ

| Công cụ | File | Dùng để |
|---|---|---|
| **Factory** | `utils/data_factory.py` | Sinh payload độc nhất, có tag `QA-AUTO` |
| **Cleanup fixture** | `created_resources` (trong `pytest_support/fixtures.py`) | Đăng ký xóa resource → teardown tự gọi (kể cả khi test fail) |

## 1. Factory — sinh dữ liệu

```python
from utils.data_factory import make_user, make_tenant, make_deal

make_user()                       # tất cả field random + email độc nhất
make_user(department="Finance")   # override 1 field để assert
make_tenant()                     # name có prefix "QA-AUTO ..."
```
- `fake.unique.*` đảm bảo **không trùng** trong 1 lần chạy.
- Field human-readable mang prefix **`QA-AUTO`** → dễ nhận diện + dọn hàng loạt.
- Trả về `dict` thuần → truyền thẳng vào `client.post(..., json=...)`.

> Các field trong factory là **điểm khởi đầu hợp lý**, không phải schema backend
> chính thức. Khi API chốt contract, chỉnh field cho khớp.

## 2. Cleanup — tự xóa sau test

Fixture `created_resources`: đăng ký 1 callback xóa cho **mọi thứ bạn tạo**.
Teardown chạy các callback theo thứ tự **ngược** (LIFO), nuốt lỗi (chỉ log) để
một cleanup hỏng không chặn cái khác.

```python
import pytest
from utils.data_factory import make_tenant


@pytest.mark.api
@pytest.mark.regression
async def test_create_tenant_001(auth_client, created_resources):
    """TENANT_API_CREATE_001: tạo tenant mới qua API trả 201 + có id."""
    # ── Arrange + Act: tạo qua API (nhanh, ổn định hơn click UI) ──
    payload = make_tenant()
    resp = await auth_client.post("/tenants", json=payload, expected_status=201)
    tenant_id = resp.json()["data"]["id"]

    # ── Đăng ký dọn NGAY sau khi tạo (trước assert) để chắc chắn được xóa ──
    created_resources.add(lambda: auth_client.delete(f"/tenants/{tenant_id}"))

    # ── Assert ──
    assert tenant_id, "Tenant phải có id sau khi tạo"
    # → teardown tự xóa tenant này, dù test pass hay fail.
```

### Nguyên tắc vàng
1. **Đăng ký cleanup NGAY sau khi tạo** (trước các assert) — nếu assert fail giữa
   chừng, resource vẫn được dọn.
2. **Ưu tiên tạo/xóa qua API** trong setup/teardown (nhanh, ít flaky) — kể cả khi
   test chính là test UI.
3. **Không giả định data có sẵn** — test tự tạo cái nó cần (test isolation).

## 3. Test isolation (cô lập)
- Mỗi test sở hữu data riêng → chạy **bất kỳ thứ tự nào / song song / chạy lẻ** đều ra cùng kết quả.
- `authenticated_page` đã cho mỗi test 1 browser context riêng (không chia cookie).
- `created_resources` đảm bảo không để lại rác giữa các test.

## 4. Khi nào dùng
- Test **chỉ đọc/kiểm tra** (vd load trang) → **không cần** factory/cleanup.
- Test **CRUD** (tạo/sửa/xóa tenant, partner, deal, user...) → **bắt buộc** dùng cả hai.

## Checklist viết 1 test CRUD
- [ ] Dùng `make_*()` để sinh payload (đừng hard-code).
- [ ] Tạo resource qua API client (`auth_client.post(...)`).
- [ ] `created_resources.add(lambda: client.delete(...))` ngay sau khi tạo.
- [ ] Assert hành vi.
- [ ] (Không cần viết teardown thủ công — fixture lo.)
