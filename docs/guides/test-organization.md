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
| `@pytest.mark.be_gap` | Gap BE đã biết, **cố ý đỏ** cho tới khi BE sửa (theo §6 rule 4) | TC mà bước kiểm chính fail vì BE thiếu logic |

> **Tách tín hiệu pass/fail:** TC gắn `be_gap` vẫn FAIL để báo gap (rule 4), nhưng
> **merge gate chạy `-m "not be_gap"`** để 100% xanh = không regression. Một job
> riêng chạy `-m be_gap` để theo dõi gap BE (được phép đỏ). Nhờ vậy "đỏ đã biết"
> không che "đỏ mới".

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

### Quy tắc bắt buộc khi viết TC

1. **Positive → kèm Negative.** Làm xong 1 TC positive thì làm luôn negative tương
   ứng (nếu nghiệp vụ có) — không để trống một phía.
2. **Phủ FULL param.** Mỗi TC tự rà hết:
   - *Positive:* gửi **mọi** field (required + optional) và **assert echoed** từng cái
     (bắt silent-mutation) + lifecycle/side-effects.
   - *Negative:* **mọi** required ở dạng missing, + invalid enum, + sai format
     (email/date), + boundary (âm/0/cực lớn), + FK không tồn tại.
   - Giá trị enum lấy từ **OpenAPI spec**; đừng đoán.
3. **Param là khóa ngoại (FK) → chứng minh "không tồn tại" TRONG test.** Nếu một
   param trỏ tới data của service khác (`planId`→sa-plans, `partnerId`→partners,
   `userId`→partner-users…), khi tạo data ghost cho negative phải **GET-by-id ở
   service nguồn và assert nó vắng mặt (4xx) NGAY trong test**, rồi mới dùng. Tuyệt
   đối không hard-code id rồi giả định. Nếu service nguồn báo "tồn tại" → fixture
   sai → fail rõ ("fixture invalid") thay vì cho kết quả sai lệch.
   - *Ngoại lệ:* nếu chính endpoint đang test đã trả "not found" cho ghost id
     (self-proving trong assert) thì không cần GET riêng (vd ghost `partnerId` khi
     register deal). Chỉ cần GET nguồn khi endpoint **không** tự báo (vd `planId`
     bị nhận 201 → phải chứng minh absence từ sa-plans).
4. **BE thiếu validation → fail thật + báo BE.** Không viết test xanh giả; để step
   đó FAIL kèm message "confirm with BE", và ghi gap vào Note của TC.
5. **Auth/Permission luôn có 3 TC cơ bản** (cho endpoint có bảo vệ):
   - Không có token → **401**
   - Sai role/permission → **403**
   - Token của entity khác cố truy cập tài nguyên không thuộc về mình → **403 hoặc 404**
   - *(Auth thường gom ở feature Auth & Access Control, không nhét vào từng TC chức năng — nhưng phải tồn tại.)*
6. **Mỗi TC tự chứa (self-contained):**
   - Setup fixture/data **trong chính TC** — không dùng data do TC khác tạo.
   - **Cleanup** sau khi chạy (`created_resources`), pass hay fail đều sạch.
   - Ghi rõ **precondition state** (vd "deal phải đang FLAGGED", "partner phải pending").
7. **Assert schema, không chỉ assert value:**
   - Kiểm **type** của field trả về (list/dict/int/str…), không chỉ giá trị.
   - Kiểm **sensitive field không bị lộ** trong response (password, token, secret…).
   - Kiểm **field bắt buộc luôn present** (id, status, code…).
8. **Duplicate/Idempotency cho mọi POST tạo resource:**
   - Gọi 2 lần payload giống nhau → **ghi rõ behavior mong đợi**: 409 (reject trùng)
     hay idempotent (no-op/trả lại cái cũ)? Assert đúng cái đó, đừng để mơ hồ.
   - **Là TC RIÊNG** (dòng riêng trong test plan, Test Type = `Negative`), đặt cạnh
     feature create — KHÔNG nhét thành step cuối của TC positive (gộp 2 mục đích →
     positive đỏ vì lý do duplicate, đọc log nhầm là "tạo hỏng"). Ngoại lệ DUY NHẤT:
     nếu gửi-lại là một bước thật trong kịch bản `e2e/` (vd user bấm gửi 2 lần do
     mạng) thì là `async_step`, không phải atomic.
9. **Cập nhật tài liệu test case sau khi làm xong.** Mỗi khi viết xong (hoặc sửa) 1 TC,
   phải cập nhật **cả 2 file** với nội dung TC tương ứng (description + steps có
   → Expected + overall + note; nếu là gap thì ghi rõ "confirm BE"):
   - `docs/blazeup_admin/PARTNER_TEST_CASES.md` (EN)
   - `docs/blazeup_admin/PARTNER_TEST_CASES_vi.md` (VI)
   - NOT_STARTED chỉ để tên; BLOCKED ghi lý do; PASSED/FAILED ghi đầy đủ. Giữ 2 file
     đồng bộ với code + test plan Excel.

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
