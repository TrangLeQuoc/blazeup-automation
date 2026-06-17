# Tổ chức test (Test Taxonomy)

Cách phân loại, đặt tên, nhóm và viết test cho khung BlazeUp — để suite **không
bừa** khi lớn dần. Đọc cùng: [test-data.md](test-data.md) (factory + cleanup),
[add-domain.md](add-domain.md) (thêm domain mới).

> **Nguyên tắc vàng (đọc trước tất cả):**
> **1 test case = 1 hàm `test_…` = 1 dòng trong test plan.** Mỗi test **độc lập,
> tự setup, tự dọn**. Không test nào phụ thuộc thứ tự chạy của test khác.

---

## 1. Ba trục tổ chức

Mọi test được định vị bằng 3 trục, ánh xạ thẳng vào cấu trúc thư mục:

| Trục | Câu hỏi | Ví dụ |
|------|---------|-------|
| **Domain** | App nào? | `blazeup_admin` (SA Dashboard) · `blazeup_partner` (Partner Portal) |
| **Layer** | Tầng nào? | `api` (HTTP contract) · `ui` (browser) · `e2e` (luồng nghiệp vụ) |
| **Nhóm** | Thuộc về đâu? | API → theo **feature/resource** · UI → theo **page** |

```
tests/<domain>/
  api/      # nhóm theo RESOURCE/feature  → test_sa_partners.py, test_sa_deals.py
  ui/       # nhóm theo PAGE              → test_dashboard.py, test_tenants.py
  e2e/      # nhóm theo JOURNEY (nhiều bước, có state) → test_partner_onboarding.py
```

- **API gom theo feature/resource**, KHÔNG theo page (1 API phục vụ nhiều page).
- **UI gom theo page**, mỗi page 1 file.
- **`e2e/`** là chỗ DUY NHẤT cho kịch bản nhiều bước phụ thuộc nhau (xem §3).

---

## 2. Ba loại test — dùng loại nào khi nào

| Loại | Mục đích | Đặc tính | Để ở |
|------|----------|----------|------|
| **Atomic contract** | Kiểm 1 endpoint / 1 hành vi | Độc lập, tự setup+cleanup, chạy song song được | `api/`, `ui/` |
| **Negative / validation** | Input sai → bị từ chối đúng cách | Như atomic, nhưng assert lỗi (400/403/409…) | cạnh atomic, cùng feature |
| **E2E scenario** | Luồng nghiệp vụ end-to-end | Nhiều bước **chia sẻ state**, tuần tự | `e2e/` |

**Quy tắc quyết định:**

- Kiểm "API này trả đúng contract không?" → **atomic**.
- Kiểm "gửi rác có bị chặn không?" → **negative** (TC riêng, không nhét vào positive).
- Kiểm "partner đăng ký → SA duyệt → tạo deal → tính hoa hồng" (mỗi bước dùng kết
  quả bước trước) → **E2E** trong `e2e/`.

> ⚠️ **ĐỪNG** biến atomic API test thành chuỗi bước phụ thuộc nhau. Phụ thuộc ngầm
> = không chạy lẻ/song song được, 1 lỗi kéo theo "fail giả" hàng loạt, khó tìm
> nguồn lỗi. Đó chính là thứ làm suite bừa.

---

## 3. E2E scenario — khi nào & viết thế nào

Chỉ dùng khi các bước **thật sự phụ thuộc state** (record tạo ở bước 1 được bước 4
dùng). Vẫn là **1 hàm = 1 TC**, các bước là `async_step` (không tách thành nhiều
hàm phụ thuộc nhau).

```python
async def test_partner_onboarding_e2e(sa_partners_client, created_resources):
    async with async_step("[1/4] Đăng ký partner (pending)"):
        partner = await sa_partners_client.create_partner(make_partner())
        created_resources.add(lambda: sa_partners_client.delete_partner(partner.partner_id))
    async with async_step("[2/4] SA duyệt → active"):
        ...
    async with async_step("[3/4] Tạo deal cho partner"):
        ...
    async with async_step("[4/4] Kiểm hoa hồng được tính"):
        ...
```

Step nào fail thì step đó đỏ trong Allure → biết ngay chuỗi gãy ở đâu, mà test vẫn
là 1 đơn vị độc lập, tự dọn.

---

## 4. Đặt tên & TC ID

Tên hàm → TC ID do `utils/sync_registry.py` sinh tự động (viết hoa + tra module).

**Quy ước tên hàm:**
```
test_{feature}_{layer}_{section}_{seq}
        │         │        │        └─ số thứ tự 3 chữ số:  001, 002, …, 011
        │         │        └─ section/feature con trong module
        │         └─ api | ui
        └─ module (phải khai báo trong config/<domain>/config.yaml)
```
Ví dụ: `test_partner_api_partner_account_management_002`
→ `PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002` → ID `2060102`.

**Công thức ID:** `{type}{project}{module:02d}{section:02d}{seq:02d}`
- `type`: **1 = UI**, **0 = API**
- `project`: digit của domain (vd `blazeup_admin` = 2) — giữ ID khác nhau giữa các project dù trùng tên module
- module/section: 2 chữ số, lấy từ `config.yaml` (`modules.<NAME>.number` + `ui:`/`api:` section)

> Section đánh số **tăng dần theo lúc viết**, KHÔNG cần liền mạch theo nghĩa. Vd
> validation là `_011` đứng sau `_010` là bình thường — **lọc bằng marker/Test
> Type, đừng dựa vào số thứ tự** để phân nhóm.

Thêm test mới mà ID chưa nhận ra? → module/section phải có trong
`config/<domain>/config.yaml`, rồi chạy `python utils/sync_registry.py`.

---

## 5. Markers — phân loại để lọc khi chạy

Khai báo trong `pytest.ini`. Dùng marker để **lọc lúc chạy**, KHÔNG tách thành thư
mục riêng theo loại.

| Marker | Nghĩa | Khi nào gắn |
|--------|-------|-------------|
| `@pytest.mark.smoke` | Tập sống-còn, chạy nhanh mỗi commit | Vài TC chứng minh hệ thống "thở" |
| `@pytest.mark.regression` | Bộ đầy đủ, chạy trước release | Hầu hết TC |
| `@pytest.mark.api` | Test tầng HTTP | Mọi test trong `api/` |
| `@pytest.mark.ui` | Test trình duyệt | Mọi test trong `ui/` |
| `@pytest.mark.slow` | Chậm / E2E nhiều bước | E2E, job định kỳ |

```bash
python -m runner.<domain>.run_test --mode smoke        # chỉ smoke
python -m runner.<domain>.run_test --type api          # chỉ API
pytest -m "regression and not slow"                    # lọc trực tiếp
```

Quy ước gắn: **mỗi test ≥ 1 marker layer (`api`/`ui`) + 1 marker scope
(`smoke`/`regression`)**. `--strict-markers` bắt buộc marker phải khai báo trước.

---

## 6. Positive vs Negative

- **Positive**: đường đi đúng → kết quả đúng (vd tạo partner hợp lệ → 201, pending).
- **Negative**: input/điều kiện sai → bị từ chối **đúng cách** (vd thiếu field → 400 +
  message nêu field + KHÔNG tạo record).

Negative là **TC riêng** (dòng riêng trong test plan), không trộn vào positive. Đặt
cạnh feature tương ứng. Cột **Test Type** ghi rõ `Functional` / `Negative` /
`Security`.

---

## 7. Giải phẫu một test tốt

```python
@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_002(sa_partners_client, created_resources):
    """<TC ID>: <mô tả 1 dòng>.  <giải thích contract đang kiểm>."""
    # SETUP: dựng data độc nhất (factory) — log đúng field sẽ assert
    payload = make_partner(type="channel")
    logger.info("SETUP: payload → name='{}', email='{}'", payload["name"], payload["email"])

    async with async_step("[1/N] Gọi API ..."):
        resp = await sa_partners_client.create_partner(payload)
        created_resources.add(lambda: sa_partners_client.delete_partner(resp.partner_id))  # dọn TRƯỚC assert

    async with async_step("[2/N] Verify ..."):
        assert ...
        logger.info("CHECK ... → OK (...)")

    logger.info("RESULT: ...")
```

Thành phần bắt buộc:

| Phần | Vai trò |
|------|---------|
| **Docstring** | Dòng đầu = `<TC ID>: <mô tả>`; sau đó giải thích contract |
| **Marker** | layer + scope (§5) |
| **`SETUP:`** | dựng data (factory, [test-data.md](test-data.md)); log field sẽ assert |
| **`async_step("[n/N] …")`** | mỗi bước → 1 node Pass/Fail trong Allure ([log_helper](../../utils/log_helper.py)) |
| **`CHECK … → OK`** | mỗi assertion log 1 dòng → đọc như checklist |
| **`created_resources.add(...)`** | đăng ký cleanup **ngay sau khi tạo, trước assert** |
| **`RESULT:`** | kết quả cuối |

Request/response **tự được log + đính vào Allure step** bởi `BaseClient` — không cần
log payload thủ công.

---

## 8. Checklist chống bừa

Trước khi commit 1 test, tự hỏi:

- [ ] 1 hàm này = đúng 1 TC trong test plan? (không gộp 2 mục đích)
- [ ] Chạy **lẻ** được không? (không phụ thuộc test khác)
- [ ] Tự **dọn** data đã tạo? (`created_resources`)
- [ ] Data **độc nhất**? (factory `fake.unique`, prefix `QA-AUTO`)
- [ ] Có **marker** layer + scope?
- [ ] Tên hàm khớp convention → `sync_registry` ra đúng ID?
- [ ] Positive/negative tách đúng dòng test plan?
- [ ] Mỗi bước bọc `async_step`, mỗi assert có `CHECK`?

---

## 9. Khi nào tái cấu trúc

- **< 20 TC**: giữ phẳng theo `api/` `ui/`. Đừng tối ưu sớm.
- **20–50 TC**: tách file theo feature/page (đang làm). Chuẩn hóa marker.
- **> 50 TC**: cân nhắc thư mục con theo feature trong `api/`, tách `e2e/`, gom
  smoke-set rõ ràng. Lúc này có dữ liệu thật để quyết, không đoán.
