# Thêm một domain mới vào pipeline

Hướng dẫn thêm một domain test mới (ví dụ `blazeup_superadmin`) vào framework +
CI/CD. Thay `<domain>` = tên domain mới (snake_case, ví dụ `blazeup_superadmin`)
và `<DOMAIN>` = tên đó viết HOA (ví dụ `BLAZEUP_SUPERADMIN`).

> Mẫu có sẵn để copy: `blazeup_admin` (có test + Excel) và `blazeup_partner`
> (khung trống). Quy ước đặt tên đồng nhất là điều giúp CI "tự nhận" domain mới
> ở phần lớn các bước.

---

## A. Code trong repo

1. `runner/<domain>/` — copy **3 entry point** từ `runner/blazeup_admin/`, đổi
   `os.environ.setdefault("BLAZEUP_DOMAIN", "<domain>")` trong cả 3:
   - `run_test.py` — chạy test
   - `health.py` — health-check API service (engine dùng chung ở `utils/health_check.py`)
   - `swagger_check.py` — swagger drift detector (engine dùng chung ở `utils/swagger_check.py`)
   - thêm `__init__.py` (rỗng) nếu chưa có.
2. `runner/<domain>/registry.py` — sinh ra bằng `python utils/sync_registry.py`
   (đọc từ test plan Excel). KHÔNG sửa tay.
3. `tests/<domain>/` — test cases của domain.
4. `config/<domain>/.env` — để chạy LOCAL (gitignored, không commit):
   ```
   BASE_URL=...
   API_BASE_URL=...
   TEST_EMAIL=...
   TEST_PASSWORD=...
   ```
5. (Tùy chọn, nếu xuất Excel) `docs/<domain>/Partner_Platform_Test_Plan.xlsx`
   và đặt `REPORT_EXCEL = True` trong `runner/<domain>/run_test.py`.

Chạy thử local trước khi đụng CI:
```bash
python -m runner.<domain>.run_test --mode smoke   # chạy test
python -m runner.<domain>.health                  # kiểm service sống/chết
python -m runner.<domain>.swagger_check --save     # bắt baseline Swagger đầu tiên
```

> Lưu ý: trong `health.py` / `swagger_check.py`, chỉnh `EXTRA_SERVICES` nếu domain
> này cần giám sát service mà chưa có API client (vd `sa-partners-api`).

---

## B. Workflow `.github/workflows/test.yml` — sửa 4 chỗ

### 1) Thêm option vào input `domain`
```yaml
      domain:
        type: choice
        options:
          - blazeup_admin
          - blazeup_partner
          - <domain>          # ← thêm
          - all
```

### 2) Thêm vào danh sách matrix `all` (job `setup`)
```yaml
            all) DOMAINS='["blazeup_admin","blazeup_partner","<domain>"]' ;;
```

### 3) Thêm nhánh trong "Map domain secrets" (job `tests`)
```yaml
            <domain>)
              echo "BASE_URL=${{ secrets.<DOMAIN>_BASE_URL }}"           >> "$GITHUB_ENV"
              echo "API_BASE_URL=${{ secrets.<DOMAIN>_API_BASE_URL }}"   >> "$GITHUB_ENV"
              echo "TEST_EMAIL=${{ secrets.<DOMAIN>_TEST_EMAIL }}"       >> "$GITHUB_ENV"
              echo "TEST_PASSWORD=${{ secrets.<DOMAIN>_TEST_PASSWORD }}" >> "$GITHUB_ENV"
              ;;
```

### 4) Định tuyến Telegram (bước "Notify via Telegram")
Thêm 1 dòng env:
```yaml
          TELEGRAM_CHAT_ID_<DOMAIN>: ${{ secrets.TELEGRAM_CHAT_ID_<DOMAIN> }}
```
Và 1 nhánh `case`:
```yaml
            <domain>) CHAT_ID="${TELEGRAM_CHAT_ID_<DOMAIN>:-$TELEGRAM_CHAT_ID}" ;;
```

---

## C. GitHub Secrets cần thêm
Settings → Secrets and variables → Actions → **New repository secret**:

| Secret | Bắt buộc | Ghi chú |
|---|---|---|
| `<DOMAIN>_BASE_URL` | ✅ | URL web của domain |
| `<DOMAIN>_API_BASE_URL` | ✅ | URL API |
| `<DOMAIN>_TEST_EMAIL` | ✅ | Tài khoản test |
| `<DOMAIN>_TEST_PASSWORD` | ✅ | Mật khẩu test |
| `TELEGRAM_CHAT_ID_<DOMAIN>` | ⬜ | Channel riêng cho team. Bỏ trống → dùng channel chung `TELEGRAM_CHAT_ID` |

Lưu ý khi nhập secret: không để khoảng trắng / dòng trống ở cuối giá trị.

---

## D. Tự động — KHÔNG cần làm gì

| Tính năng | Hành vi với domain mới |
|---|---|
| Dashboard Allure + trend | Tự tạo `https://<owner>.github.io/<repo>/<domain>/` |
| AI triage (`ai_triage.md`) | Tự gen khi có test fail (flag `REPORT_AI_TRIAGE`) |
| Checkbox Excel / AI triage | Áp dụng chung cho mọi domain |
| Telegram | Có secret riêng → vào channel riêng; không → fallback channel chung |
| Health-check & Swagger drift | Engine dùng chung (`utils/`) — chỉ cần copy file mỏng ở mục A.1; tự quét service từ `api_clients/<domain>/` |

---

## Vì sao phải sửa tay 3 nhánh `case`?
GitHub Actions **không** cho tham chiếu secret bằng tên động lúc chạy
(không có `secrets[$domain]`). Vì bảo mật, secret chỉ truy cập được bằng **tên
literal** `${{ secrets.TÊN }}`. Do đó mỗi domain phải khai báo tường minh ở 3
nhánh `case` trên. Đây là giới hạn của nền tảng, không phải của framework.

---

## Checklist nhanh
- [ ] `runner/<domain>/` (run_test.py + health.py + swagger_check.py + __init__.py + registry.py)
- [ ] `tests/<domain>/`
- [ ] `config/<domain>/.env` (local) + chạy thử `--mode smoke`
- [ ] `python -m runner.<domain>.health` (kiểm service)
- [ ] `python -m runner.<domain>.swagger_check --save` (baseline Swagger)
- [ ] (tùy chọn) `docs/<domain>/...xlsx` + `REPORT_EXCEL = True`
- [ ] Workflow: input option, matrix `all`, Map domain secrets, Telegram route
- [ ] Secrets: `<DOMAIN>_BASE_URL` / `_API_BASE_URL` / `_TEST_EMAIL` / `_TEST_PASSWORD`
- [ ] (tùy chọn) `TELEGRAM_CHAT_ID_<DOMAIN>`
- [ ] Chạy `domain=<domain>` trên Actions để xác nhận xanh + dashboard + Telegram
