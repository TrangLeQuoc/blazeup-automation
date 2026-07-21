# Partner Platform — Kế hoạch Test (Automation)

> Sinh tự động từ test plan. TC NOT_STARTED chỉ hiện tên; BLOCKED hiện lý do block; PASSED/FAILED hiện đầy đủ mô tả, các bước (kèm expected mỗi bước), expected tổng, và ghi chú.

## 1. UI

### UI · COMMISSIONS

- PARTNER_UI_COMMISSIONS_001
- PARTNER_UI_COMMISSIONS_002
- PARTNER_UI_COMMISSIONS_003
- PARTNER_UI_COMMISSIONS_004
- PARTNER_UI_COMMISSIONS_005
- PARTNER_UI_COMMISSIONS_006
- PARTNER_UI_COMMISSIONS_007
- PARTNER_UI_COMMISSIONS_008
- PARTNER_UI_COMMISSIONS_009
- PARTNER_UI_COMMISSIONS_010
- PARTNER_UI_COMMISSIONS_011
### UI · DASHBOARD

- PARTNER_UI_DASHBOARD_001
- PARTNER_UI_DASHBOARD_002
- PARTNER_UI_DASHBOARD_003
- PARTNER_UI_DASHBOARD_004
- PARTNER_UI_DASHBOARD_005
- PARTNER_UI_DASHBOARD_006
- PARTNER_UI_DASHBOARD_007
- PARTNER_UI_DASHBOARD_008
- PARTNER_UI_DASHBOARD_009
### UI · MY_CLIENTS

- PARTNER_UI_MY_CLIENTS_001
- PARTNER_UI_MY_CLIENTS_002
- PARTNER_UI_MY_CLIENTS_003
- PARTNER_UI_MY_CLIENTS_004
- PARTNER_UI_MY_CLIENTS_005
- PARTNER_UI_MY_CLIENTS_006
- PARTNER_UI_MY_CLIENTS_007
- PARTNER_UI_MY_CLIENTS_008
- PARTNER_UI_MY_CLIENTS_009
- PARTNER_UI_MY_CLIENTS_010
- PARTNER_UI_MY_CLIENTS_011
- PARTNER_UI_MY_CLIENTS_012
- PARTNER_UI_MY_CLIENTS_013
### UI · MY_PIPELINE

- PARTNER_UI_MY_PIPELINE_001
- PARTNER_UI_MY_PIPELINE_002
- PARTNER_UI_MY_PIPELINE_003
- PARTNER_UI_MY_PIPELINE_004
- PARTNER_UI_MY_PIPELINE_005
- PARTNER_UI_MY_PIPELINE_006
- PARTNER_UI_MY_PIPELINE_007
- PARTNER_UI_MY_PIPELINE_008
- PARTNER_UI_MY_PIPELINE_009
- PARTNER_UI_MY_PIPELINE_010
- PARTNER_UI_MY_PIPELINE_011
- PARTNER_UI_MY_PIPELINE_012
- PARTNER_UI_MY_PIPELINE_013
- PARTNER_UI_MY_PIPELINE_014
- PARTNER_UI_MY_PIPELINE_015
- PARTNER_UI_MY_PIPELINE_016
- PARTNER_UI_MY_PIPELINE_017
- PARTNER_UI_MY_PIPELINE_018
- PARTNER_UI_MY_PIPELINE_019
- PARTNER_UI_MY_PIPELINE_020
- PARTNER_UI_MY_PIPELINE_021
- PARTNER_UI_MY_PIPELINE_022
- PARTNER_UI_MY_PIPELINE_023
- PARTNER_UI_MY_PIPELINE_024
- PARTNER_UI_MY_PIPELINE_025
- PARTNER_UI_MY_PIPELINE_026
- PARTNER_UI_MY_PIPELINE_027
- PARTNER_UI_MY_PIPELINE_028
- PARTNER_UI_MY_PIPELINE_029
- PARTNER_UI_MY_PIPELINE_030
- PARTNER_UI_MY_PIPELINE_031
- PARTNER_UI_MY_PIPELINE_032
- PARTNER_UI_MY_PIPELINE_033
### UI · PARTNER_PORTAL_SHELL

- PARTNER_UI_PARTNER_PORTAL_SHELL_001
- PARTNER_UI_PARTNER_PORTAL_SHELL_002
- PARTNER_UI_PARTNER_PORTAL_SHELL_003
### UI · PARTNER_TEAM

- PARTNER_UI_PARTNER_TEAM_001
- PARTNER_UI_PARTNER_TEAM_002
- PARTNER_UI_PARTNER_TEAM_003
### UI · RESOURCES

- PARTNER_UI_RESOURCES_001
- PARTNER_UI_RESOURCES_002
- PARTNER_UI_RESOURCES_003
- PARTNER_UI_RESOURCES_004
- PARTNER_UI_RESOURCES_005
### UI · SA_PARTNER_MODULE

- PARTNER_UI_SA_PARTNER_MODULE_001
- PARTNER_UI_SA_PARTNER_MODULE_002
- PARTNER_UI_SA_PARTNER_MODULE_003
- PARTNER_UI_SA_PARTNER_MODULE_004
- PARTNER_UI_SA_PARTNER_MODULE_005
- PARTNER_UI_SA_PARTNER_MODULE_006
- PARTNER_UI_SA_PARTNER_MODULE_007
- PARTNER_UI_SA_PARTNER_MODULE_008
- PARTNER_UI_SA_PARTNER_MODULE_009
- PARTNER_UI_SA_PARTNER_MODULE_010
- PARTNER_UI_SA_PARTNER_MODULE_011
- PARTNER_UI_SA_PARTNER_MODULE_012
### UI · SECURITY_COMPLIANCE

- PARTNER_UI_SECURITY_COMPLIANCE_001
- PARTNER_UI_SECURITY_COMPLIANCE_002
- PARTNER_UI_SECURITY_COMPLIANCE_003
- PARTNER_UI_SECURITY_COMPLIANCE_004
### UI · TRAINING

- PARTNER_UI_TRAINING_001
- PARTNER_UI_TRAINING_002
- PARTNER_UI_TRAINING_003

## 2. API

### API · AUTH_ACCESS_CONTROL

> Auth flow partner. Session được mint self-contained từ phía SA
> (`utils.partner_portal`). Endpoint auth (`/partner/auth/*`) trả token + `/me`
> identity ở TOP LEVEL (không có wrapper `data`). Không phải resource-create → không
> idempotency duplicate-create; mỗi TC tự gồm negative riêng (rejection/invalidation).

#### PARTNER_API_AUTH_ACCESS_CONTROL_001
**Mô tả test:** Partner JWT hợp lệ authorize một request scope-partner.
**Chuẩn bị (điều kiện tiên quyết):**
1. SA tạo một partner.
2. SA duyệt partner (pending → active).
3. SA mời một partner user (trả về email + tempPassword).
4. Login bằng user đó → lấy partner JWT.
**Các bước:**
1. GET /partner/auth/me với partner JWT.
   → Expected: 200, trả về identity (userId + email).
**Expected (tổng):** Một partner JWT hợp lệ authorize các request scope-partner.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_002
**Mô tả test:** Token non-partner / thiếu token trên partner API là unauthorized.
**Các bước:**
1. GET /partner/auth/me không có token → 401.
2. GET /partner/auth/me với một token non-partner (SA admin) → 401.
**Expected (tổng):** Token thiếu / non-partner bị từ chối (401).
**Ghi chú:** PASSED — verified 2026-06-25. (Dùng SA admin token để xấp xỉ "tenant JWT" — một token non-partner.) Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_003
**Mô tả test:** Cross-partner access — một partner JWT không đọc được deal của partner khác (tenant isolation).
**Chuẩn bị (điều kiện tiên quyết):**
1. Mint partner A (SA create → approve → invite → login) và đăng ký một deal cho A; lấy id.
2. Mint partner B (partner riêng, cùng flow mint từ SA).
**Các bước:**
1. Partner B gọi GET /partner/portal/deals/{A_deal_id}.
   → Expected: bị từ chối với **404** (ưu tiên — giấu sự tồn tại) hoặc **403** — không bao giờ 400 — và deal của A KHÔNG có trong body.
**Expected (tổng):** Một partner không truy cập được deal của partner khác — bị từ chối, không lộ dữ liệu.
**Ghi chú:** FAILED (by design / be_gap). Case cross-entity của rule-5. BE trả **400** cho cross-partner access, nhưng đúng ra phải **404** (ưu tiên, để giấu sự tồn tại của resource) hoặc **403** — 400 gán nhầm một request hợp lệ thành malformed. Test được siết để assert 403/404 + đánh dấu `be_gap` cho tới khi BE fix. Bản thân tenant isolation vẫn đúng (không lộ dữ liệu).

#### PARTNER_API_AUTH_ACCESS_CONTROL_004
**Ghi chú (NOT_STARTED):** Admin MFA policy enforcement — cần một flow MFA enroll/challenge. Chưa automate (assess các endpoint MFA: /partner/auth/mfa/*).

#### PARTNER_API_AUTH_ACCESS_CONTROL_005
**Ghi chú (NOT_STARTED):** Guard — MSP truy cập payroll data bị cấm. MSP/payroll guard; assess xem có API surface trong domain này không trước khi automate.

#### PARTNER_API_AUTH_ACCESS_CONTROL_006
**Ghi chú (NOT_STARTED):** Guard — MSP export employee records bị cấm. Như _005.

#### PARTNER_API_AUTH_ACCESS_CONTROL_007
**Mô tả test:** Refresh token hợp lệ cấp một access token mới (không cần re-login).
**Chuẩn bị (điều kiện tiên quyết):** SA create → approve → invite → login một partner user; lấy access + refresh token.
**Các bước:**
1. POST /partner/auth/refresh với refresh token đã lấy.
   → Expected: 200, một accessToken mới (khác cái ban đầu).
2. Access token mới authorize GET /partner/auth/me.
   → Expected: 200.
3. POST /partner/auth/refresh với một refresh token không hợp lệ.
   → Expected: 401.
**Expected (tổng):** Refresh cấp một access token mới hoạt động; refresh không hợp lệ bị từ chối.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_008
**Mô tả test:** Logout invalidate refresh token.
**Chuẩn bị (điều kiện tiên quyết):** SA create → approve → invite → login một partner user; lấy access + refresh token (session active).
**Các bước:**
1. POST /partner/auth/logout với access token.
   → Expected: 200/204.
2. POST /partner/auth/refresh với refresh token (đã bị invalidate).
   → Expected: 401.
**Expected (tổng):** Sau logout refresh token không thể cấp một access token nữa.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_009
**Mô tả test:** Change password cập nhật credential (mới hoạt động, cũ fail).
**Chuẩn bị (điều kiện tiên quyết):** SA create → approve → invite → login một partner user; lấy access token (session active).
**Các bước:**
1. POST /partner/auth/change-password với một currentPassword SAI.
   → Expected: 401 ("Current password is incorrect").
2. POST /partner/auth/change-password với currentPassword đúng.
   → Expected: 200/204.
3. Login bằng password MỚI.
   → Expected: 200/201 + accessToken.
4. Login bằng password CŨ.
   → Expected: 401.
**Expected (tổng):** Đổi password từ chối một current sai; credential mới hoạt động, cũ bị từ chối.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.
### API · DEAL_REGISTRATION_PIPELINE

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_001
**Mô tả test:** Happy-path đăng ký deal trên POST /v1/sa/deals — payload hợp lệ tạo một deal 'registered' với một cửa sổ bảo vệ.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một billing plan đã published; dựng payload deal (đủ field).
**Các bước:**
1. POST /v1/sa/deals với đủ field (partnerId, planId, dealType='referral', prospect*, ACV, closeDate, notes) → đăng ký deal.
   → Expected: request đã gửi.
2. Verify deal được chấp nhận + lưu.
   → Expected: HTTP 201 (envelope statusCode 200); message thành công; _id do server cấp.
3. Verify MỌI field gửi đi được lưu (không bị đổi ngầm).
   → Expected: mọi field được echo; expectedCloseDate giữ đúng ngày đã yêu cầu.
4. Verify lifecycle.
   → Expected: status 'registered', có protectionExpiresAt, conflictStatus 'none'.
5. GET /v1/sa/deals/{id} (persistence).
   → Expected: trả về đúng deal, status 'registered'.
**Teardown:** xóa partner cha (deal không có endpoint delete).
**Expected (tổng):** Deal được đăng ký với mọi field lưu chính xác, cửa sổ bảo vệ mở, truy xuất được.
**Ghi chú:** PASSED — echo-check full-param + lifecycle + persistence (rule-6).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_002
**Mô tả test:** Đăng ký một reseller deal — billing model 'reseller' được lưu.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một billing plan đã published; dựng payload deal với dealType='reseller'.
**Các bước:**
1. POST /v1/sa/deals (đăng ký reseller deal).
   → Expected: được chấp nhận (HTTP 201, envelope statusCode 200) + _id do server cấp.
2. Verify billing model được lưu + field echo.
   → Expected: dealType lưu == 'reseller'; mọi field khác echo nguyên vẹn; expectedCloseDate giữ đúng ngày.
3. Verify lifecycle + truy xuất được (GET /v1/sa/deals/{id}).
   → Expected: status 'registered', có protectionExpiresAt; deal fetch về giữ dealType 'reseller'.
**Teardown:** xóa partner cha.
**Expected (tổng):** Reseller deal đăng ký; dealType='reseller' CHÍNH LÀ billing model được lưu (không có field riêng).
**Ghi chú:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_003
**Mô tả test:** Đăng ký một co-sell deal — co-sell metadata được lưu.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một billing plan đã published; dựng payload deal với dealType='co_sell'.
**Các bước:**
1. POST /v1/sa/deals (đăng ký co-sell deal).
   → Expected: được chấp nhận (HTTP 201, envelope statusCode 200) + _id do server cấp.
2. Verify co-sell metadata được lưu + field echo.
   → Expected: dealType lưu == 'co_sell'; mọi field khác echo nguyên vẹn; expectedCloseDate giữ đúng ngày.
3. Verify lifecycle + truy xuất được (GET /v1/sa/deals/{id}).
   → Expected: status 'registered', có protectionExpiresAt; deal fetch về giữ dealType 'co_sell'.
**Teardown:** xóa partner cha.
**Expected (tổng):** Co-sell deal đăng ký; dealType='co_sell' CHÍNH LÀ metadata được lưu. Split 70/30 được tính downstream (_011, blocked) — ngoài phạm vi ở đây.
**Ghi chú:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_004
**Mô tả test:** Deal protection: một partner thứ hai đăng ký cùng prospect bị flag là conflict.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo hai partner; chọn một billing plan đã published; dựng một prospect identity chung (name + email) dùng cho cả hai.
**Các bước:**
1. Partner 1 đăng ký deal trước.
   → Expected: deal A được chấp nhận, conflictStatus 'none' (chưa có deal trước đó).
2. Partner 2 đăng ký CÙNG prospect.
   → Expected: HTTP 201 (deal B vẫn được tạo, không bị từ chối); conflictStatus 'flagged'; conflictingDealIds chứa id của deal A.
3. GET /v1/sa/deals/{id} trên deal B.
   → Expected: conflictStatus vẫn 'flagged' (đã lưu).
**Teardown:** xóa cả hai partner.
**Expected (tổng):** Deal cross-partner cùng prospect được tạo nhưng bị flag đối với deal đầu tiên (xếp hàng chờ giải quyết conflict).
**Ghi chú:** PASSED. Khác với CÙNG partner đăng ký lại cùng prospect → hard 400 duplicate (_022).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_005
**Mục đích:** CRON — protection hết hạn với activity gần đây → tự động gia hạn cửa sổ bảo vệ một lần.
**Ghi chú (BLOCKED):** Không có API surface. Đây là một job nền theo lịch (CRON) — auto-extension của protection kích hoạt theo timer của server khi một deal có activity gần đây sát lúc hết hạn. Không có endpoint để trigger theo yêu cầu và không có cách tua nhanh đồng hồ một cách deterministic từ test, nên hiệu ứng không quan sát được trong một lần chạy test. Xem lại nếu BE expose một hook "run job" thủ công / time-travel. (P1 / Critical trong plan.)

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_006
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_007
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_008
**Mô tả test:** Duyệt một deal đã registered (POST /v1/sa/deals/{id}/approve): status → approved, reviewer được đóng dấu; kỳ vọng có rate + rate-table version.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal; xác nhận status 'registered'.
**Các bước:**
1. Duyệt deal đã registered (reviewNotes='QA-AUTO approve').
   → Expected: được chấp nhận (HTTP 201, envelope statusCode 200); status 'approved'.
2. Verify reviewer được đóng dấu.
   → Expected: có reviewedAt + reviewedBy.
3. Verify rate + rate-table version được đóng dấu (theo plan).
   → Expected: có rate + rateTableVersion trong response. **Hiện FAIL** — cả hai đều không được expose.
**Teardown:** xóa partner cha.
**Expected (tổng):** Deal được duyệt + reviewer đóng dấu; việc đóng dấu rate / rate-table-version chờ BE.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap: rate/rateTableVersion KHÔNG có trong response của deal API và không có commission nào được tạo khi approve. Xác nhận với BE: đóng dấu nội bộ (không serialize) / stage khác (deal win) / chưa implement.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_009
**Mô tả test:** Giải quyết conflict của một deal bị flag (POST /v1/sa/deals/{id}/resolve-conflict): decision + reasoning được đóng dấu và bất biến.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo hai partner; cả hai đăng ký CÙNG prospect nên deal thứ hai (deal B) là 'flagged'.
**Các bước:**
1. Giải quyết conflict (decision='resolved_for_partner', reasoning) — decision + reasoning được đóng dấu.
   → Expected: HTTP 201 (envelope statusCode 200); conflictStatus='resolved_for_partner'; conflictResolution{decision, reasoning, resolvedBy, resolvedAt} được đóng dấu và khớp với cái đã gửi.
2. Bất biến: một resolve lần hai với decision/reasoning khác.
   → Expected: bị từ chối (4xx); message giải thích deal không còn ở trạng thái conflict FLAGGED.
3. Đọc lại GET /v1/sa/deals/{id}.
   → Expected: decision + reasoning vẫn là bản gốc (không đổi) — bất biến.
**Teardown:** xóa cả hai partner.
**Expected (tổng):** Conflict được giải quyết một lần; decision + reasoning là bất biến.
**Ghi chú:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_010
**Mô tả test:** Duyệt một deal phát ra một event partner.deal.approved (trigger CRM-sync).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal (status 'registered').
**Các bước:**
1. Duyệt deal.
   → Expected: status 'approved'.
2. Verify một event 'deal approved' được publish vào audit log (GET /v1/sa/audit-logs, retry tối đa 3× cho eventual consistency).
   → Expected: một event mà action đề cập deal + approve tham chiếu deal id này, và `after.status == 'approved'` (ghi lại transition registered→approved).
**Teardown:** xóa partner cha.
**Expected (tổng):** Event deal-approved được publish. Việc cập nhật owner/stage CRM là một service downstream (connectors/CRM Integration), ngoài phạm vi.
**Ghi chú:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_011
**Ghi chú (BLOCKED):** Chưa automate — trước đây bị gán nhầm PASSED/Auto=YES (false-green), sửa lại thành BLOCKED. Split co-sell 70/30 được tính DOWNSTREAM; tại thời điểm register deal record không mang field split (verify qua _003) và không có API để đọc split đã tính, nên không thể assert default 70/30. Cùng họ phụ thuộc với _012. Unblock khi BE expose split đã tính (hoặc một API tính-split).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_012
**Ghi chú (BLOCKED):** Phụ thuộc engine tính split co-sell (feature _011), vốn ở downstream và không expose thành API — không có endpoint để submit một override split co-sell, nên rule "override tại/dưới $100K ACV không được chấp nhận" không thể thực thi (threshold là TRÊN $100K ACV). Unblock khi BE expose API split-override.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_013
**Mô tả test:** Giải quyết deal FLAGGED CHO partner của nó (decision=resolved_for_partner, viện dẫn xác nhận của prospect) khiến deal đó thành winner và tự động lật deal conflict thành loser; cả hai giữ status 'registered'.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo hai partner; cả hai đăng ký CÙNG prospect (name+email) → deal A (đầu) + deal B (thứ hai, flagged).
**Các bước:**
1. Giải quyết deal B đã flag CHO partner của nó (decision='resolved_for_partner', reasoning viện dẫn xác nhận của prospect).
   → Expected: HTTP 201 (envelope statusCode 200); deal B conflictStatus='resolved_for_partner'; conflictResolution được ghi.
2. Kiểm tra deal conflict A (GET by id) — tự động lật thành loser.
   → Expected: deal A conflictStatus='resolved_against_partner'.
3. Đọc lại winner deal B (GET by id) — kết quả bền vững.
   → Expected: deal B vẫn 'resolved_for_partner' và status 'registered'.
**Teardown:** xóa cả hai partner.
**Expected (tổng):** partner được xác nhận thắng conflict và deal kia bị lật thành loser.
**Ghi chú:** PASSED. Tính bất biến của decision/reasoning được cover bởi _009; input resolve negative bởi _029.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_014
**Ghi chú (BLOCKED):** Không có API surface riêng. resolve-conflict (POST /v1/sa/deals/{id}/resolve-conflict) là một quyết định thủ công của SA (enum resolved_for_partner|resolved_against_partner); nó không nhận tín hiệu "prospect unreachable" và không áp dụng tiebreaker "first-registered-wins" tự động. Con đường thực thi duy nhất (SA thủ công resolve cho deal sớm hơn) về mặt cơ học giống hệt _013 → không có gì khác biệt để assert. Unblock nếu BE implement một tiebreaker tự động; ngược lại đã được _013 cover.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_015
**Ghi chú (BLOCKED):** Phụ thuộc hạ tầng tenant-provisioning + commission không tiếp cận được từ test domain này. Verify "không đăng ký → không attribution/commission" cần POST /internal/tenants/provision (internal-only), đọc tenant.attribution.partnerId == null, assert không có dòng partner_commissions, và xác nhận không có event blazeup.partner.commission.earned — không cái nào expose cho QA ở đây. Negative companion của PARTNER_API_006 (§3 Scenario I). Unblock khi endpoint provisioning + việc verify commission/event khả dụng.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_016
**Mô tả test:** SA gia hạn thủ công cửa sổ bảo vệ của một deal đã registered (POST /v1/sa/deals/{id}/extend-protection, body addedDays + reasoning).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan đã published; đăng ký một deal và lấy protectionExpiresAt hiện tại (expiry cũ).
**Các bước:**
1. SA gia hạn cửa sổ bảo vệ (addedDays=30 + reasoning).
   → Expected: được chấp nhận (HTTP 201, envelope statusCode 200); message xác nhận việc gia hạn.
2. Verify cửa sổ dời về sau đúng số ngày yêu cầu.
   → Expected: protectionExpiresAt mới > cũ; delta ĐÚNG BẰNG 30 ngày; deal vẫn 'registered'.
3. Verify cửa sổ mới bền vững (GET /v1/sa/deals/{id}).
   → Expected: protectionExpiresAt đã lưu == giá trị đã gia hạn.
**Teardown:** xóa partner cha.
**Expected (tổng):** Gia hạn thủ công của SA đẩy cửa sổ bảo vệ ra đúng số ngày yêu cầu.
**Ghi chú:** PASSED. Cửa sổ gia hạn đúng addedDays tính từ expiry CŨ (vd +30d: 2026-08-29 → 2026-09-28). Plan mô tả đây là một request partner xếp hàng, nhưng endpoint đã implement là một gia hạn TRỰC TIẾP của SA (áp dụng ngay) — xác nhận với BE xem có một flow request-partner xếp hàng riêng cũng được kỳ vọng không.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_017
**Ghi chú (BLOCKED):** Cần một đồng hồ 90 ngày mà staging không cung cấp được. "Đăng ký lại một prospect đã thua conflict được chấp nhận sau 90 ngày (khi chưa có close)" cần một deal thua conflict mà thời điểm thua đã 90+ ngày; createdAt/lostAt do server cấp và không thể backdate, và không có test clock/fast-forward. Negative companion ("từ chối đăng ký lại TRƯỚC 90 ngày") CÓ THỂ build ngay bây giờ như một TC riêng. Unblock khi BE cung cấp một test clock hoặc backdating.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_018
**Ghi chú (DEFERRED):** Win một deal (POST /v1/sa/deals/{id}/win). WinDealDto mang theo một thẻ thanh toán + chi tiết billing + provisioning tenant — gọi nó có side-effect nặng (provision một tenant, có thể chạm billing). Hoãn để tránh làm bẩn staging; build với một teardown chuyên dụng / một sandbox flag do BE cung cấp.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_019
**Mô tả test:** SA đánh dấu một deal đã approved là lost (POST /v1/sa/deals/{id}/lose). Lose yêu cầu deal phải 'approved' trước.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan; đăng ký một deal và approve nó (status 'approved').
**Các bước:**
1. Đánh dấu deal là lost (notes).
   → Expected: được chấp nhận (HTTP 201, envelope statusCode 200); status thành 'lost'.
2. Verify status lost bền vững (GET /v1/sa/deals/{id}).
   → Expected: deal fetch về status vẫn 'lost'.
**Teardown:** xóa partner cha.
**Expected (tổng):** Một deal approved chuyển sang 'lost' (thông báo partner là downstream, ngoài phạm vi).
**Ghi chú:** PASSED. Đối trọng negative/illegal-state là _032.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_020
**Mô tả test:** SA lấy một deal đơn theo id (GET /v1/sa/deals/{id}) — full record.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan; đăng ký một deal và lấy id.
**Các bước:**
1. GET deal theo id.
   → Expected: HTTP 200 (envelope statusCode 200); id trả về khớp deal yêu cầu.
2. Verify full record.
   → Expected: có đủ field bắt buộc (partnerId, dealType, prospectName, prospectCountry, estimatedAcvCents, status, protectionExpiresAt, conflictStatus); status 'registered'; không lộ field nhạy cảm nào (password/token/secret).
**Teardown:** xóa partner cha.
**Expected (tổng):** Get-by-id trả về full record đúng của deal, không lộ field nhạy cảm.
**Ghi chú:** PASSED. Đối trọng negative (ghost/malformed id) là _031.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_021
**Mô tả test:** Đối trọng negative của register (_001): mọi payload không hợp lệ/thiếu phải bị từ chối với 4xx + một message mô tả và không tạo deal nào. Tất cả case đều chạy (thu thập failure) để một gap không bao giờ che các gap khác.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan đã published (payload baseline hợp lệ). Chứng minh FK-absence (rule 3): GET ghost planId 'no-such-plan-qa' và assert nó trả 4xx (thực sự không tồn tại) trước khi dùng bên dưới.
**Các bước:** (mỗi case = một POST /v1/sa/deals với payload baseline bị mutate; kỳ vọng 4xx + gợi ý message)
1. Thiếu partnerId → 4xx, message đề cập "partner".
2. Thiếu dealType → "dealtype must be one of".
3. dealType không hợp lệ ('wholesale') → "dealtype must be one of".
4. Thiếu prospectName → "prospectname".
5. Thiếu prospectCountry → "prospectcountry".
6. prospectEmail không hợp lệ ('not-an-email') → "must be an email".
7. Thiếu estimatedAcvCents → "estimatedacvcents".
8. ACV âm (-100) → "must not be less than".
9. Thiếu expectedCloseDate → "iso 8601".
10. Định dạng ngày sai ('31-12-2026') → "iso 8601".
11. Ghost partnerId (000000000000000000000000) → "not found".
12. Ghost planId ('no-such-plan-qa', đã verify không tồn tại ở trên) → kỳ vọng bị từ chối "plan". **Hiện FAIL** — được chấp nhận (HTTP 201).
**Teardown:** xóa partner cha (gỡ mọi deal vô tình tạo bởi gap planId).
**Expected (tổng):** Mọi payload register không hợp lệ bị từ chối với một message rõ ràng và không tạo deal nào; planId nên được validate với catalog.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate). Gap (case 12): một planId không tồn tại được chấp nhận (201). sa-plans trả 4xx cho id đó, nhưng endpoint deals không validate planId cross-service. Xác nhận với BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_022
**Mô tả test:** Đối trọng idempotency/duplicate của _001: CÙNG partner đăng ký CÙNG prospect hai lần bị từ chối (không có deal thứ hai).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan đã published; dựng một prospect identity duy nhất dùng lại cho cả hai lần register.
**Các bước:**
1. Lần register đầu của partner thành công.
   → Expected: HTTP 201, id do server cấp, conflictStatus 'none'.
2. CÙNG partner đăng ký lại CÙNG prospect (name+email).
   → Expected: HTTP 400, message chứa "already exists".
3. Verify không có deal thứ hai được tạo (soi body response bị từ chối).
   → Expected: không có deal id (_id/id) trong body — hard reject, không phải path flagged.
**Teardown:** xóa partner cha.
**Expected (tổng):** Duplicate cùng-partner là một hard 400 reject; khác với _004 (một partner KHÁC → 201 + conflictStatus 'flagged').
**Ghi chú:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_028
**Mô tả test:** Đối trọng negative của _008 (approve): ba target approve bất hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng (không bao giờ thành công ngầm). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal và approve nó (status 'approved') để case illegal-transition có target.
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/approve)
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Deal đã approved (illegal transition) → **400** 'cannot transition' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
**Teardown:** xóa partner cha.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; illegal transition → 400/409. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với _031. Case 2 & 3 đúng. Xác nhận với BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_029
**Mô tả test:** Đối trọng negative của _009 (resolve-conflict): sáu input không hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal (status 'registered', conflictStatus 'none' — một target non-flagged).
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/resolve-conflict)
1. Enum decision không hợp lệ ('whatever') → **400** 'decision must be one of'.
2. Thiếu decision → **400** 'decision must be one of'.
3. Thiếu reasoning → **400** message đề cập "reasoning".
4. Malformed id ('not-an-id') → **400** 'invalid id'.
5. Deal non-flagged (illegal state) → **400** message đề cập "flagged" (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
6. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
**Teardown:** xóa partner cha.
**Expected (tổng):** Lỗi validation/format/state → 400; id không tồn tại → 404. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 6): một id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với _031. Case 1–5 đúng. Xác nhận với BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_030
**Mô tả test:** Đối trọng negative của _016 (extend-protection): tám input không hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. BE validate body TRƯỚC khi lookup deal, nên các case field tự chứng minh trên một ghost id (không cần deal thật). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** không có — các case nhắm trực tiếp vào một ghost/malformed id (validation body chạy trước; không phụ thuộc sa-plans).
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/extend-protection)
1. Thiếu addedDays → **400** message "addeddays".
2. Thiếu reasoning → **400** message "reasoning".
3. addedDays = 0 → **400** "less than 1".
4. addedDays âm → **400** "less than 1".
5. addedDays quá max (181) → **400** "greater than 180".
6. addedDays không phải số ('abc') → **400** message "addeddays".
7. Malformed id ('not-an-id') → **400** "invalid id".
8. Ghost deal id (body hợp lệ, đúng định dạng nhưng không tồn tại) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
**Expected (tổng):** Validation body / boundary / format / malformed → 400; id không tồn tại → 404. Không bao giờ 5xx. Ràng buộc spec: addedDays ∈ 1..180; reasoning bắt buộc + không rỗng.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 8): một id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với _031. Case 1–7 đúng. Xác nhận với BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_031
**Mô tả test:** Đối trọng negative của _020 (get-by-id): hai ngữ nghĩa từ chối riêng biệt — một malformed id là bad request (400), một ghost id là missing resource (404). Tự chứng minh; GET → không lo idempotency. Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/deals/{id}; kỳ vọng code + gợi ý message, không bao giờ 5xx)
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message đề cập "not found". **Hiện FAIL** — BE trả 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message đề cập "invalid id".
**Expected (tổng):** Một malformed id → 400; một id đúng định dạng nhưng không tồn tại → 404. Không bao giờ 5xx, không trả record.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một id đúng định dạng nhưng không tồn tại trả **400** với message "not found" — status mâu thuẫn message; REST đúng là **404 Not Found**. Case malformed-id (400) đúng. Xác nhận với BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_032
**Mô tả test:** Đối trọng negative của _019 (lose): ba target lose bất hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal (status 'registered', CHƯA approved — lose yêu cầu 'approved').
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/lose)
1. Deal registered (illegal transition — chưa approved) → **400** 'cannot transition' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận ở đây).
2. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
3. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Teardown:** xóa partner cha.
**Expected (tổng):** Illegal transition → 400/409; malformed id → 400; id không tồn tại → 404. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 2): một id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với _031. Case 1 & 3 đúng. Xác nhận với BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_033
**Mô tả test:** Đối trọng idempotency của _016 (extend-protection): một gia hạn lặp lại là CỘNG DỒN, không phải no-op hay cap.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan; đăng ký một deal và lấy protectionExpiresAt (exp0).
**Các bước:**
1. Gia hạn lần đầu (+30 ngày).
   → Expected: exp1 == exp0 + 30d.
2. Gia hạn lần hai (+30 ngày) — hành vi lặp.
   → Expected: HTTP 200; exp2 == exp1 + 30d (cộng dồn từ expiry hiện tại); deal vẫn 'registered'.
3. Verify tổng cửa sổ bền vững (GET /v1/sa/deals/{id}).
   → Expected: cửa sổ đã lưu == exp0 + 60d (2×addedDays).
**Teardown:** xóa partner cha.
**Expected (tổng):** extend-protection là một action mutating có tham số — lặp lại là cộng dồn theo thiết kế (không phải một no-op idempotent, không bị cap). Mỗi lần gọi cũng được ghi vào protectionExtensions[].
**Ghi chú:** PASSED. Probe theo rule 8 (mutating action ≠ POST-create): hành vi là cộng dồn (exp0 +30 → +30 = +60). BE đóng dấu mỗi lần gia hạn vào protectionExtensions[] (extendedBy/at, previous/newExpiresAt, addedDays, trigger, reasoning).

### API · DEAL_APPROVAL_QUEUE

#### PARTNER_API_DEAL_APPROVAL_QUEUE_001
**Mô tả test:** SA từ chối một deal đang xếp hàng (registered) từ approval queue (POST /v1/sa/deals/{id}/reject, body reviewNotes).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; chọn một plan; đăng ký một deal (status 'registered' = xếp hàng chờ review).
**Các bước:**
1. Từ chối deal với một lý do (reviewNotes).
   → Expected: được chấp nhận (HTTP 201, envelope statusCode 200); status thành 'rejected'.
2. Verify việc từ chối bền vững (GET /v1/sa/deals/{id}).
   → Expected: deal fetch về status vẫn 'rejected'.
**Teardown:** xóa partner cha.
**Expected (tổng):** Một deal registered bị từ chối và giữ nguyên rejected.
**Ghi chú:** PASSED. Đối trọng negative/illegal-state là _011.

#### PARTNER_API_DEAL_APPROVAL_QUEUE_011
**Mô tả test:** Đối trọng negative của _001 (reject): ba target reject bất hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal và reject nó (status 'rejected') để case illegal-transition có target.
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/reject)
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Deal đã rejected (illegal transition) → **400** 'cannot transition' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
**Teardown:** xóa partner cha.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; illegal transition → 400/409. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với _031. Case 2 & 3 đúng. Xác nhận với BE.

### API · DEAL_COLLABORATION

#### PARTNER_API_DEAL_COLLABORATION_001
**Ghi chú (BLOCKED):** Không có API collaboration/notes-thread. Một deal chỉ mang một chuỗi `notes` phẳng duy nhất (set khi register / qua deal update) — không có endpoint comment/activity-thread để thêm, list, hay quy attribution cho các entry collaboration. Re-scope với BE: nếu "collaboration" chỉ là field notes phẳng, nó đã được cover bởi các TC register/update; ngược lại các endpoint chưa tồn tại.

#### PARTNER_API_DEAL_COLLABORATION_002
**Ghi chú (BLOCKED):** Không có API document/attachment trên deal. Không có endpoint để upload, list, hay download document của deal. Build khi BE expose một surface deal-documents.

### API · PIPELINE_MANAGEMENT

#### PARTNER_API_PIPELINE_MANAGEMENT_001
**Mô tả test:** Một partner list các deal của mình (GET /partner/portal/deals) — chỉ trả về deal của CHÍNH nó (scoped).
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal (SA create → approve → invite partner user → login lấy partner JWT); partner đăng ký một deal qua portal.
**Các bước:**
1. GET danh sách deal của chính partner (GET /partner/portal/deals?limit=20).
   → Expected: HTTP 200; `data` là một list không rỗng.
2. Verify deal đã đăng ký xuất hiện VÀ list được scope theo caller.
   → Expected: id deal đã đăng ký có trong list VÀ mọi row có partnerId == partner của caller (không rò rỉ cross-partner).
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** List deal của chính mình được scope đúng theo partner đã auth.
**Ghi chú:** PASSED. Đối trọng negative (filter/pagination không hợp lệ) là _011.

#### PARTNER_API_PIPELINE_MANAGEMENT_002
**Mô tả test:** Một partner lọc danh sách deal của mình theo status (GET /partner/portal/deals?status=registered).
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal; partner đăng ký một deal (status 'registered').
**Các bước:**
1. Lọc list deal của chính mình theo status=registered (GET /partner/portal/deals?limit=20&status=registered).
   → Expected: HTTP 200; không rỗng; mọi deal trả về có status 'registered' VÀ deal vừa đăng ký được bao gồm.
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Filter status được áp dụng đúng.
**Ghi chú:** PASSED. Enum deal-status hợp lệ: registered, approved, in_progress, won, lost, expired, rejected.

#### PARTNER_API_PIPELINE_MANAGEMENT_011
**Mô tả test:** Đối trọng negative của _001/_002: một filter không hợp lệ / pagination quá cỡ được BE validate và từ chối với 4xx + một message rõ ràng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal.
**Các bước:** (mỗi case = một GET /partner/portal/deals với một query không hợp lệ)
1. status=bogus (ngoài enum) → **400**, message đề cập "status".
2. limit=999999 (quá max) → **400**, message đề cập "limit".
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Filter/pagination không hợp lệ bị từ chối (4xx), không bao giờ 5xx.
**Ghi chú:** PASSED. BE validate cả hai (trả 400) — không lỏng.
### API · TENANT_PROVISIONING_ATTRIBUTION

> Ghi chú: các id TC của section này gom nhiều feature (close→provision→commission→attribution). Theo quyết định của user, giữ nguyên cách gom hiện tại; một số row thực sự thuộc về co-sell / commissions / CRM.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_001
**Ghi chú (BLOCKED):** Endpoint accept/lock split co-sell POST /v1/partner/deals/:id/cosell-split-accept không có trong dev build. (Gom nhầm — thực ra là một case co-sell.) Unblock khi BE ship nó.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_002
**Ghi chú (BLOCKED):** Phụ thuộc flow win/close deal (DEAL_018, deferred) + các surface tenant-provisioning & commission/event downstream không tiếp cận được từ domain này. Unblock khi win chạy an toàn được + các surface đó được expose.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_003
**Ghi chú (BLOCKED):** Phụ thuộc win/close + billing/invoice downstream ("reseller close → invoice nhắm reseller"). Unblock khi win + verify billing khả dụng.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_004
**Ghi chú (BLOCKED):** Phụ thuộc win/close + một tenant đã pre-provision + line-item billing downstream. Unblock khi expansion-close + verify billing được expose.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_005
**Ghi chú (BLOCKED):** Engine tính commission ở downstream không có API để đọc commission đã tính ("expansion NN → full rate"). Cùng họ với COMMISSIONS_PAYOUTS_001. Unblock khi BE expose commission đã tính.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_006
**Ghi chú (BLOCKED):** Như _005 — tính commission ở downstream, không có API đọc ("expansion EN → rate thấp hơn"). Unblock khi BE expose commission đã tính.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_007
**Ghi chú (BLOCKED):** Phụ thuộc flow deal-win (DEAL_018, deferred) + một CRM connector downstream để verify "deal won → CRM close won với tenant id". Unblock khi win chạy an toàn được.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_008
**Ghi chú (BLOCKED):** Cần một tenant đã provision (post-win) để soi các field partner vĩnh viễn trong tenant.attribution — surface downstream không tiếp cận được ở đây. Unblock khi surface đọc tenant/attribution được expose.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_009
**Ghi chú (BLOCKED):** Không có API expose cho một SA override tenant-attribution với two-eye (dual) approval + history. Unblock khi BE expose endpoint attribution-override.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_010
**Ghi chú (BLOCKED):** Endpoint lock-after-accept split co-sell POST /v1/partner/deals/:id/cosell-split-accept không có trong dev build. Cùng endpoint với _001. Unblock khi BE ship nó.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_011
**Ghi chú (redundant):** "expectedCloseDate không hợp lệ → 400" đã được cover bởi DEAL_REGISTRATION_PIPELINE_021 (step 2e). Không blocked; không có coverage riêng nếu build standalone.
### API · REFERRAL_ATTRIBUTION

#### PARTNER_API_REFERRAL_ATTRIBUTION_001
**Ghi chú (BLOCKED):** Endpoint referral-attribution (GET/POST /v1/partner/referral-links) vắng khỏi spec đã deploy (xác nhận 2026-06-30: 0 referral path); TTL Redis 30 ngày cũng cần điều khiển đồng hồ. Unblock khi BE ship API referral-links + một test clock.

#### PARTNER_API_REFERRAL_ATTRIBUTION_002
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — endpoint referral attribution chưa có trong dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_003
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — endpoint referral attribution chưa có trong dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_004
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — endpoint referral attribution chưa có trong dev build

### API · CLIENT_HEALTH_MSP

> Tất cả BLOCKED — module My Clients / Client Health / MSP (`/v1/partner/clients/*`) vắng khỏi spec đã deploy (xác nhận 2026-06-30: sa-partners-api = 68 path, 0 path /client*). Unblock khi BE ship module.

#### PARTNER_API_CLIENT_HEALTH_MSP_001
**Ghi chú (BLOCKED):** GET /v1/partner/clients (My Clients — tenant post-close) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_002
**Ghi chú (BLOCKED):** GET /v1/partner/clients/:tenantId/health (metric usage/renewal/ticket) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_003
**Ghi chú (BLOCKED):** GET /v1/partner/clients/:tenantId/tickets (không có MSP consent → chỉ count + severity) chưa implement. Cặp với _004.

#### PARTNER_API_CLIENT_HEALTH_MSP_004
**Ghi chú (BLOCKED):** GET /v1/partner/clients/:tenantId/tickets (có MSP consent → full nội dung ticket) chưa implement. Cặp với _003.

#### PARTNER_API_CLIENT_HEALTH_MSP_005
**Ghi chú (BLOCKED):** PATCH MSP consent dưới /v1/partner/clients/* (revoke → dừng truy cập nội dung ngay lập tức) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_006
**Ghi chú (BLOCKED):** POST MSP tenant provision dưới /v1/partner/clients/* (tạo một tenant partner_managed) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_007
**Ghi chú (BLOCKED):** MSP handoff/transfer dưới /v1/partner/clients/* (giữ history cũ + phát event) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_008
**Ghi chú (BLOCKED):** MSP tier qualification (tổng ARR quản lý) dưới /v1/partner/clients/* chưa implement; cũng là một calc downstream.

#### PARTNER_API_CLIENT_HEALTH_MSP_009
**Ghi chú (BLOCKED):** Audit grant/revoke MSP consent dưới /v1/partner/clients/* (event với actor + timestamp, đổi truy cập ngay lập tức) chưa implement.
### API · COMMISSIONS_PAYOUTS

> Spec (xác nhận 2026-06-30): endpoint commission ĐÃ CÓ (/v1/sa/commissions + /approve /mark-paid /dispute /clawback, /v1/partner/portal/commissions + /summary /dispute, /v1/sa/rate-table). VẮNG: waiver, spiff, approve-payout, payout/banking. Hầu hết TC lifecycle vẫn cần một commission record, vốn chỉ được tạo bởi win pipeline đã deferred (DEAL_018). Chỉ _002 và _006 build được ngay bây giờ.

#### PARTNER_API_COMMISSIONS_PAYOUTS_001
**Ghi chú (BLOCKED):** Tính commission downstream ("renewal EE → rate thấp nhất"); cần pipeline win→commission (deferred) và không có API để đọc rate đã tính. Unblock khi một commission có thể được tạo + rate của nó đọc được.

#### PARTNER_API_COMMISSIONS_PAYOUTS_002
**Ghi chú (NOT_STARTED — build được ngay):** GET /v1/partner/portal/commissions (ledger/history commission) đã có; có thể assert schema list + partner scoping (pass ngay cả khi rỗng). Ứng viên build kế tiếp. Khác với PARTNER_PORTAL_004 (commissions/summary, PASSED).

#### PARTNER_API_COMMISSIONS_PAYOUTS_003
**Ghi chú (BLOCKED, positive):** POST /v1/partner/portal/commissions/{id}/dispute đã có, nhưng dispute cần một commission {id} thật (win pipeline deferred). Negative (dispute một ghost id → 4xx) build được ngay bây giờ. Unblock khi một commission record có thể được tạo.

#### PARTNER_API_COMMISSIONS_PAYOUTS_004
**Ghi chú (BLOCKED):** Waiver product-failure POST /v1/partner/commissions/:id/waiver vắng khỏi spec (2026-06-30). Unblock khi BE ship endpoint waiver.

#### PARTNER_API_COMMISSIONS_PAYOUTS_005
**Ghi chú (BLOCKED):** Endpoint quyết định waiver / event final-outcome vắng (không có waiver path, 2026-06-30). Cặp với _004/_012.

#### PARTNER_API_COMMISSIONS_PAYOUTS_006
**Ghi chú (NOT_STARTED — build được ngay):** Endpoint rate-table tồn tại dưới dạng POST /v1/sa/rate-table (TC ghi PUT /internal/commission/rates — method PUT→POST, path đổi tên). Có thể tạo một version mới + assert nó bền vững. Phía "cached" (Redis invalidation) là internal/không quan sát được qua API (xem _014).

#### PARTNER_API_COMMISSIONS_PAYOUTS_007
**Ghi chú (BLOCKED):** "approve over threshold" hai người duyệt cần /v1/sa/commissions/{id}/approve-payout (dual approval), vắng khỏi spec — chỉ có một POST /{id}/approve đơn. Cũng cần một commission record.

#### PARTNER_API_COMMISSIONS_PAYOUTS_008
**Ghi chú (BLOCKED):** Endpoint referral-attribution vắng (0 referral path, 2026-06-30) + TTL 40 ngày cần điều khiển đồng hồ. Cùng gốc với REFERRAL_ATTRIBUTION_003.

#### PARTNER_API_COMMISSIONS_PAYOUTS_009
**Ghi chú (BLOCKED):** Endpoint referral-link vắng (0 referral path, 2026-06-30). "Signup qua referral-link → notification + trigger commission" cần referral path.

#### PARTNER_API_COMMISSIONS_PAYOUTS_010
**Ghi chú (BLOCKED):** POST /v1/sa/commissions/{id}/clawback đã có, nhưng một clawback cần một commission tồn tại (win pipeline deferred) + điều khiển timing 12 tháng.

#### PARTNER_API_COMMISSIONS_PAYOUTS_011
**Ghi chú (BLOCKED):** Cần một reseller commission record + một churn event (cả hai downstream/không khả dụng) để assert "reseller churn → KHÔNG clawback".

#### PARTNER_API_COMMISSIONS_PAYOUTS_012
**Ghi chú (BLOCKED):** Endpoint SLA/quyết định waiver + ledger-credit vắng (không có waiver path, 2026-06-30). Cặp với _004/_005.

#### PARTNER_API_COMMISSIONS_PAYOUTS_013
**Ghi chú (BLOCKED):** Programme SPIFF POST /internal/commission/spiff vắng khỏi spec (0 spiff path, 2026-06-30).

#### PARTNER_API_COMMISSIONS_PAYOUTS_014
**Ghi chú (BLOCKED):** POST /v1/sa/rate-table đã có (bản update), nhưng "rate cache Redis bị invalidate" là một side-effect internal không có API để quan sát. Re-scope thành "update bền vững + phản ánh ở lần đọc kế tiếp" (chồng với _006), hoặc giữ blocked cho assertion cache-invalidation theo nghĩa đen.

#### PARTNER_API_COMMISSIONS_PAYOUTS_015
**Ghi chú (BLOCKED):** "Ledger của pack vs channel partner giữ tách biệt" cần commission tồn tại cho cả hai loại partner (win pipeline deferred). Endpoint list đã có; dữ liệu thì chưa.

#### PARTNER_API_COMMISSIONS_PAYOUTS_016
**Ghi chú (BLOCKED):** "Chi tiết banking payout mã hóa at-rest" (CSFLE) là một thuộc tính lưu trữ internal không có API để xác nhận; không có endpoint payout/banking trong khu vực commissions (banking nằm trên partner.payoutAccounts). Verify qua review DB/infra, không qua API.
### API · PARTNER_ACCOUNT_MANAGEMENT

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001
**Mô tả test:** Kiểm tra contract read-only trên GET /v1/sa/partners: trả 200 với envelope (statusCode/data/total/message) và tuân thủ pagination.
**Chuẩn bị (điều kiện tiên quyết):** SA client đã auth; request trang đầu với limit=5.
**Các bước:**
1. GET /v1/sa/partners?page=1&limit=5.
   → Expected: request đã gửi (HTTP 200 được assert trong client).
2. Verify contract của partner-list API.
   → Expected: statusCode 200; `data` là một list; `total` ≥ 0; có `message`; page size trả về ≤ limit yêu cầu (5).
3. Verify tính toàn vẹn dữ liệu + SA filtering (phụ thuộc dữ liệu).
   → Expected: mỗi partner là một object không rỗng với một id duy nhất; WARN-skip nếu staging có 0 partner.
4. Verify SA isolation / không rò rỉ cross-partner.
   → Expected: chỉ directory scope-SA; WARN-skip khi không có dữ liệu (audit cross-partner sâu áp dụng khi đã có dữ liệu multi-partner).
**Expected (tổng):** Partner list trả về một envelope paginated hợp lệ, scope-SA.
**Ghi chú:** PASSED. Step 3–4 phụ thuộc dữ liệu (staging thường có 0 partner seed → WARN-skip); đối trọng negative pagination là _011.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002
**Mô tả test:** CRUD create trên POST /v1/sa/partners với name/email/type bắt buộc.
**Chuẩn bị (điều kiện tiên quyết):** dựng một payload partner duy nhất (name/email/type='channel'); cleanup (DELETE) được đăng ký ngay sau khi tạo.
**Các bước:**
1. POST /v1/sa/partners (tạo partner).
   → Expected: request đã gửi.
2. Verify contract create-partner (được chấp nhận + lưu).
   → Expected: HTTP 201 (envelope statusCode 200); message thành công; _id do server cấp và một `code` được sinh (PAR-xxxxxx).
3. Verify record đã tạo khớp request.
   → Expected: name/email/type lưu == đã gửi (không bị đổi ngầm).
4. Verify partner mới bắt đầu ở status 'pending'.
   → Expected: status == 'pending' (chờ SA kích hoạt).
5. Verify partner truy xuất được (GET /v1/sa/partners/{id}).
   → Expected: trả về đúng partner, vẫn 'pending'.
**Teardown:** xóa partner đã tạo.
**Expected (tổng):** Partner pending được tạo, lưu, truy xuất được.
**Ghi chú:** PASSED. Đối trọng negative (field không hợp lệ) là _012; duplicate (cùng email) là _021.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003
**Mô tả test:** State transition trên POST /v1/sa/partners/{id}/approve: pending -> active với event approval.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner PENDING (assert nó bắt đầu 'pending').
**Các bước:**
1. POST /v1/sa/partners/{id}/approve.
   → Expected: request đã gửi.
2. Verify call approve được chấp nhận.
   → Expected: HTTP 201 (envelope statusCode 200); message thành công; tác động lên cùng partner id.
3. Verify status lật sang 'active' và event approval được ghi.
   → Expected: status 'active'; có approvedAt; có approvedBy.
4. Verify status active bền vững (GET /v1/sa/partners/{id}).
   → Expected: partner fetch về status 'active'.
**Teardown:** xóa partner.
**Expected (tổng):** Partner pending được approve sang active với metadata approval; user activation downstream là event-driven (ngoài phạm vi). Đối trọng negative/illegal-state là _013.
**Ghi chú:** PASSED.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004
**Mô tả test:** Decline/suspend một partner qua POST /v1/sa/partners/{id}/deactivate (action partner duy nhất mang một reason); reason bắt buộc và được audit-log.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner PENDING; dựng một decline reason duy nhất (tìm được trong audit log).
**Các bước:**
1. Decline partner CÓ một reason.
   → Expected: được chấp nhận; status rời pending/active (→ 'suspended').
2. Verify decline reason được ghi trong audit log (GET /v1/sa/audit-logs, retry tối đa 3× cho eventual consistency).
   → Expected: một audit entry chứa reason duy nhất.
3. Enforce reason bắt buộc: decline ba partner mới với reason absent / rỗng / chỉ toàn whitespace.
   → Expected: mỗi cái bị từ chối với 400/422 (reason bắt buộc + không rỗng).
**Teardown:** xóa các partner đã tạo.
**Expected (tổng):** Decline hoạt động, reason được audit-log, và một reason bắt buộc không rỗng được enforce.
**Ghi chú:** PASSED. Plan gọi đây là "PATCH decline"; BE không expose endpoint decline chuyên dụng, nên POST /deactivate (mang reason) được thực thi. BE enforce reason bắt buộc không rỗng (từng là một gap đã biết, đã được BE fix). Đối trọng negative-id là _014.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005
**Mô tả test:** Tier change trên POST /v1/sa/partners/{id}/upgrade-tier cập nhật tier lưu VÀ phát một event partner.tier.changed (before/after) — tín hiệu refresh portal/analytics. Cover cả upgrade và downgrade.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner (assert tier mặc định 'registered').
**Các bước:**
1. Upgrade qua tất cả tier: registered→select→advanced→premier (ba call upgrade-tier, mỗi cái với một reason).
   → Expected: mỗi cái HTTP 200; tier lưu thành select, rồi advanced, rồi premier.
2. Verify event upgrade được ghi với before/after + reason.
   → Expected: một event partner.tier.changed cho advanced→premier (before='advanced', after='premier') mang reason thay đổi.
3. Downgrade premier→select phát một event.
   → Expected: HTTP 200, tier 'select'; một event partner.tier.changed ghi before='premier', after='select'.
4. Verify tier cuối bền vững (GET /v1/sa/partners/{id}).
   → Expected: tier fetch về == 'select'.
**Teardown:** xóa partner.
**Expected (tổng):** Tier change (lên và xuống) cập nhật tier lưu và publish một event before/after; refresh portal/analytics là một consumer downstream (ngoài phạm vi).
**Ghi chú:** PASSED. Đối trọng negative (tier không hợp lệ / cùng tier / id sai) là _015.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_006
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] Đã tìm trong OpenAPI spec của tất cả 11 platform service (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 field cho giá reseller/end-client (chỉ có basePrice/totalPrice trong plan/billing, không liên quan). Không có endpoint hay field để gửi/lưu một giá end-client → data-model mà TC này mô tả chưa được implement trong bất kỳ API hiện tại nào. Xác nhận với product/BE: service nào sở hữu, hay đây là một feature PRD tương lai (§2.2/§7.2/§11)? Chưa automate được cho tới khi model tồn tại.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_007
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Đây là một JOB nền theo lịch (tính lại tier hàng quý), không phải một API endpoint. Không có endpoint manual-trigger trong bất kỳ service nào để gọi nó theo yêu cầu, nên không thể thực thi qua API automation. Thuộc về unit/integration test của BE (hoặc cần một endpoint trigger QA-only). Lưu ý: thay đổi tier thủ công ĐƯỢC cover bởi _005 (POST /upgrade-tier); TC này cụ thể là job hàng quý tự động. Xác nhận với BE xem có thể expose một endpoint trigger không.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_008
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Phụ thuộc job tính-tier hàng quý (_007): rule "grace quarter khi downgrade" (partner giữ benefit tier hiện tại trong grace period) được áp dụng bởi job theo lịch đó, không phải một endpoint gọi được. Không có API để set đồng hồ/quý hay trigger việc đánh giá grace → không automate được qua API. Lãnh địa unit/integration test của BE. Xác nhận với BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_009
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] Không có endpoint hay field cho việc phân bổ PSM (Partner Success Manager) hay ngưỡng ARR trong bất kỳ spec của 11 service nào (chỉ có carryForwardPolicy không liên quan trong setting-api). Rule "$1.5M ARR → PSM chuyên trách" là một calculation không expose qua API → chưa automate được. Xác nhận với product/BE logic này nằm ở đâu (có thể là một job/calc internal).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010
**Mô tả test:** Grant một certification (POST /v1/sa/partner-users/{userId}/certifications) = certification earned; phát partner.certification.granted.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một portal user (lấy userId).
**Các bước:**
1. Grant certification (sales_certified, score=95) — certification earned.
   → Expected: HTTP 200 (envelope statusCode 200); status 'active'; có earnedAt + expiresAt; certificationType echo.
2. Verify cert xuất hiện trong cert list của partner (GET /v1/sa/partners/{partnerId}/certifications).
   → Expected: cert đã grant xuất hiện và thuộc về user đã mời.
3. Verify một event 'partner.certification.granted' được ghi (GET /v1/sa/audit-logs, retry tối đa 3×).
   → Expected: một event ghi cert type cho user đó.
**Teardown:** xóa partner cha.
**Expected (tổng):** Certification earned, listed, và event published; re-evaluate tier là downstream (ngoài phạm vi).
**Ghi chú:** PASSED. Đối trọng negative (input không hợp lệ) là _020; re-grant duplicate là _022.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011
**Mô tả test:** Đối trọng negative của _001 (GET list): pagination không hợp lệ được BE validate và từ chối với 4xx (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/partners với pagination không hợp lệ)
1. page=0 → **4xx** (bị từ chối), không bao giờ 5xx.
2. page=-1 → **4xx** (bị từ chối), không bao giờ 5xx.
3. limit=-5 → **4xx** (bị từ chối), không bao giờ 5xx.
4. limit=999999 (quá max) → **4xx** (bị từ chối), không bao giờ 5xx.
5. page=abc (không phải số) → **4xx** (bị từ chối), không bao giờ 5xx.
**Expected (tổng):** Mọi param pagination không hợp lệ bị từ chối với 4xx và không bao giờ crash endpoint (5xx).
**Ghi chú:** PASSED. BE trả 400 cho tất cả (page=0/-1 trước đây là một HTTP 500 crash — đã được BE fix). Siết từ "chỉ never-5xx" thành assert 4xx giờ khi BE đã validate.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012
**Mô tả test:** Đối trọng negative của _002 (create): mọi payload không hợp lệ/thiếu bị từ chối với 400 + một field-level error nêu tên field vi phạm, và tạo KHÔNG record. Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một POST /v1/sa/partners với field đang test bị hỏng)
1. Thiếu name → **400**, error đề cập "name", không record.
2. Thiếu email → **400**, error đề cập "email", không record.
3. Thiếu type → **400**, error đề cập "type", không record.
4. Email malformed ('not-an-email') → **400**, error đề cập "email", không record.
5. Name rỗng ('') → **400**, error đề cập "name", không record.
6. Enum type không hợp lệ ('foobar') → **400**, error đề cập "type", không record.
**Expected (tổng):** Mọi payload create không hợp lệ bị từ chối với 400, một message field-level, và không record được lưu.
**Ghi chú:** PASSED.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013
**Mô tả test:** Đối trọng negative của _003 (approve): ba target approve bất hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo + approve một partner nên nó đã 'active' (target cho case illegal-transition).
**Các bước:** (mỗi case = một POST /v1/sa/partners/{id}/approve)
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Partner đã active (illegal transition) → **400** 'cannot be approved' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
**Teardown:** xóa partner.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; illegal transition → 400/409. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một partner id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 2 & 3 đúng. Xác nhận với BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014
**Mô tả test:** Đối trọng negative của _004 (deactivate): id không hợp lệ bị từ chối với code đúng; một deactivate lặp lại là idempotent. Tất cả case invalid-id đều chạy (thu thập failure).
**Các bước:** (case 1–2 = POST /v1/sa/partners/{id}/deactivate trên một id sai)
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Idempotency: tạo một partner, deactivate nó, rồi deactivate lại.
   → Expected: không bao giờ 5xx; giữ 'suspended' (idempotent no-op, hiện tại 201).
**Teardown:** xóa các partner đã tạo.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; deactivate lặp lại là một idempotent no-op (không bao giờ 5xx).
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một partner id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 2 và quan sát idempotency đúng. Xác nhận với BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015
**Mô tả test:** Đối trọng negative của _005 (tier change): sáu input không hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng (không phát event). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner (tier 'registered') làm target valid-id.
**Các bước:** (mỗi case = một POST /v1/sa/partners/{id}/upgrade-tier)
1. Enum tier không hợp lệ ('silver') → **400** 'tier must be one of'.
2. Tier rỗng ('') → **400** 'tier must be one of'.
3. Thiếu tier (không field) → **400** 'tier must be one of'.
4. Cùng tier (đã ở 'registered') → **400** 'already at tier'.
5. Malformed id ('not-an-id') → **400** 'invalid id'.
6. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
**Teardown:** xóa partner.
**Expected (tổng):** Validation / same-tier / malformed → 400; id không tồn tại → 404. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 6): một partner id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 1–5 đúng. Xác nhận với BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_016
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] Đã tìm trong OpenAPI spec của tất cả 11 platform service (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 field cho giá reseller/end-client (chỉ có basePrice/totalPrice trong plan/billing, không liên quan). Không có endpoint hay field để gửi/lưu một giá end-client → data-model mà TC này mô tả chưa được implement trong bất kỳ API hiện tại nào. Xác nhận với product/BE: service nào sở hữu, hay đây là một feature PRD tương lai (§2.2/§7.2/§11)? Chưa automate được cho tới khi model tồn tại.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_017
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Đây là một JOB nền theo lịch (tính lại tier hàng quý), không phải một API endpoint. Không có endpoint manual-trigger trong bất kỳ service nào để gọi nó theo yêu cầu, nên không thể thực thi qua API automation. Thuộc về unit/integration test của BE (hoặc cần một endpoint trigger QA-only). Lưu ý: thay đổi tier thủ công ĐƯỢC cover bởi _005 (POST /upgrade-tier); TC này cụ thể là job hàng quý tự động. Xác nhận với BE xem có thể expose một endpoint trigger không.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_018
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Phụ thuộc job tính-tier hàng quý (_007): rule "grace quarter khi downgrade" (partner giữ benefit tier hiện tại trong grace period) được áp dụng bởi job theo lịch đó, không phải một endpoint gọi được. Không có API để set đồng hồ/quý hay trigger việc đánh giá grace → không automate được qua API. Lãnh địa unit/integration test của BE. Xác nhận với BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_019
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] Không có endpoint hay field cho việc phân bổ PSM (Partner Success Manager) hay ngưỡng ARR trong bất kỳ spec của 11 service nào (chỉ có carryForwardPolicy không liên quan trong setting-api). Rule "$1.5M ARR → PSM chuyên trách" là một calculation không expose qua API → chưa automate được. Xác nhận với product/BE logic này nằm ở đâu (có thể là một job/calc internal).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020
**Mô tả test:** Đối trọng negative của _010 (grant certification): bốn input không hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một portal user (lấy userId hợp lệ).
**Các bước:** (mỗi case = một POST /v1/sa/partner-users/{userId}/certifications)
1. Cert type không hợp lệ ('ninja') → **400** 'certificationType must be one of'.
2. Thiếu cert type → **400** 'certificationType must be one of'.
3. Malformed userId ('not-an-id') → **400** 'invalid id'.
4. Ghost userId (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400 ("User 000… not found").
**Teardown:** xóa partner cha.
**Expected (tổng):** Validation / malformed → 400; userId không tồn tại → 404. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 4): một userId đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 1–3 đúng. Xác nhận với BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_021
**Mô tả test:** Đối trọng idempotency/duplicate của _002 (create): tạo một partner với cùng email hai lần bị từ chối (không có account thứ hai).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner với một email duy nhất (payload được dùng lại cho lần thử duplicate).
**Các bước:**
1. Tạo lại với CÙNG email → 400 duplicate.
   → Expected: HTTP 400, message chứa "already exists".
2. Verify không có account thứ hai được tạo (soi body response bị từ chối).
   → Expected: không có partner id mới (hoặc cùng id) — không có account duplicate.
**Teardown:** xóa partner đã tạo.
**Expected (tổng):** Duplicate cùng-email là một hard 400 reject; không có partner account duplicate.
**Ghi chú:** PASSED.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_022
**Mô tả test:** Đối trọng idempotency/duplicate của _010 (certification earned): re-grant cùng loại certification cho cùng user không được tạo một duplicate (renew hoặc 409).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một portal user (lấy userId).
**Các bước:**
1. Grant 'sales_certified' (lần đầu).
   → Expected: cert 'active'.
2. Re-grant CÙNG loại certification.
   → Expected: một outcome xác định — renew (2xx) hoặc reject (409).
3. Verify user KHÔNG kết thúc với một active cert duplicate cùng loại (list các certification của partner).
   → Expected: đúng 1 cert 'sales_certified'. **Hiện FAIL** — list hiện 2.
**Teardown:** xóa partner cha.
**Expected (tổng):** Re-grant không được duplicate một active cert cùng loại.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker BUG-001). Gap: re-grant trả 201 và tạo một active cert THỨ HAI (list hiện 2). BE nên renew hoặc reject (409). Xác nhận với BE.

### API · PARTNER_USERS

#### PARTNER_API_PARTNER_USERS_001
**Mô tả test:** SA list các portal user của một partner: GET /sa-partners-api/v1/sa/partner-users?partnerId= trả về danh sách user với role.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một portal user (lấy userId).
**Các bước:**
1. GET partner-users lọc theo partnerId (limit=20).
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}.
2. Verify user đã mời xuất hiện với role + status, và list được scope.
   → Expected: user hiện diện với role + status + email; mọi row có partnerId == partner yêu cầu.
3. Verify không lộ field nhạy cảm.
   → Expected: không có key password/token/secret/tempPassword trong bất kỳ row nào (invite mang tempPassword; list thì không được).
**Teardown:** xóa partner cha.
**Expected (tổng):** Danh sách user scope-partner với role/status, không lộ credential.
**Ghi chú:** PASSED. Đối trọng negative (pagination/filter không hợp lệ) là _011.

#### PARTNER_API_PARTNER_USERS_002
**Mô tả test:** SA mời một partner-portal user: POST /sa-partners-api/v1/sa/partner-users tạo user với một role.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; dựng một payload invite (partnerId + email + firstName + lastName + role='sales').
**Các bước:**
1. Mời portal user.
   → Expected: HTTP 201 (envelope statusCode 200); userId do server cấp.
2. Verify mọi field gửi đi được lưu (không bị đổi ngầm).
   → Expected: partnerId/email/firstName/lastName/role echo đúng như đã gửi.
3. Verify user usable (active + credential tạm cho hand-off).
   → Expected: status 'active' + một tempPassword được cấp.
4. Verify user truy xuất được trong list của partner.
   → Expected: user xuất hiện trong GET partner-users?partnerId.
**Teardown:** xóa partner cha.
**Expected (tổng):** Invite tạo một partner-portal user usable với role đã chọn.
**Ghi chú:** PASSED. TC↔BE: plan ghi "email sent + user PENDING", nhưng BE tạo một user ACTIVE + trả tempPassword (onboarding temp-password) — xác nhận với BE model nào được kỳ vọng. Đối trọng negative (field không hợp lệ) là _012; duplicate (cùng email) là _013.

#### PARTNER_API_PARTNER_USERS_003
**Mô tả test:** SA reset password của một partner-portal user: POST /sa-partners-api/v1/sa/partner-users/{userId}/reset-password cấp một credential mới.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một user (lấy tempPassword của invite làm baseline).
**Các bước:**
1. Reset password của user.
   → Expected: HTTP 200; message xác nhận; response tham chiếu cùng userId.
2. Verify một credential mới được cấp.
   → Expected: một tempPassword mới, khác cái của invite.
3. Verify reset lặp lại được (mutating action, không phải one-shot).
   → Expected: một reset thứ hai cũng trả 200.
**Teardown:** xóa partner cha.
**Expected (tổng):** Reset cấp một credential hand-off mới và là một mutating action lặp lại được.
**Ghi chú:** PASSED. TC↔BE: plan ghi "reset LINK sent", nhưng BE trả một tempPassword mới (model temp-password) — xác nhận với BE. Idempotency: reset không phải create — lặp lại là hợp lệ, nên không có TC duplicate-create. Đối trọng negative (id không hợp lệ) là _014.

#### PARTNER_API_PARTNER_USERS_011
**Mô tả test:** Đối trọng negative của _001 (list partner-users): pagination/filter không hợp lệ được xử lý với code đúng — case đã validate 4xx, một ghost filter 200-empty, param lỏng default gracefully — không bao giờ 5xx. Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/partner-users với param đang test)
1. page=0 → **400** 'skip must be a non-negative integer'.
2. page=-1 → **400** 'skip must be a non-negative integer'.
3. limit quá max (999999) → **400** 'limit must not exceed 100'.
4. Malformed partnerId ('not-an-id') → **400** 'partnerId must be a mongodb id'.
5. Ghost partnerId (đúng định dạng nhưng không tồn tại, dùng như một FILTER) → **200** với một list rỗng (một filter không khớp gì, không phải 404).
6. Param lỏng (limit=0 / page không phải số / sort không xác định) → **200** (default ngầm), vẫn không bao giờ 5xx.
**Expected (tổng):** Input không hợp lệ đã validate → 4xx; một ghost filter → 200-empty; param lỏng default gracefully; không bao giờ 5xx.
**Ghi chú:** PASSED. Ghi chú WEAK-VALIDATION cần xác nhận với BE: khác với audit-log list (400 các cái này), limit=0 / page không phải số / sort không xác định bị default ngầm (200) thay vì reject. (Ghost partnerId ở đây là một query FILTER → 200-empty là đúng, khác với một ghost PATH id → 404.)

#### PARTNER_API_PARTNER_USERS_012
**Mô tả test:** Đối trọng negative của _002 (invite): tám payload không hợp lệ/thiếu, mỗi cái bị từ chối với 400 + một message mô tả. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner (payload invite baseline hợp lệ, role='admin').
**Các bước:** (mỗi case = một POST /v1/sa/partner-users với field đang test bị hỏng)
1. Thiếu email → **400** 'email must be an email'.
2. Thiếu firstName → **400** message đề cập "firstname".
3. Thiếu lastName → **400** message đề cập "lastname".
4. Thiếu partnerId → **400** 'partnerId must be a mongodb id'.
5. Enum role không hợp lệ ('bogus') → **400** 'role must be one of'.
6. Email không hợp lệ ('not-an-email') → **400** 'email must be an email'.
7. Ghost partnerId (đúng định dạng nhưng không tồn tại, gửi như một BODY FK) → **400** 'Partner … not found'.
8. Malformed partnerId ('not-an-id') → **400** 'mongodb id'.
**Teardown:** xóa partner cha.
**Expected (tổng):** Mọi payload invite không hợp lệ bị từ chối với 400 + một message field/rõ ràng; không tạo user.
**Ghi chú:** PASSED. Case 7 (ghost partnerId) là một foreign-key reference trong BODY, nên 400 được chấp nhận (khác với một ghost PATH id → 404); nó tự chứng minh (endpoint trả "Partner … not found").

#### PARTNER_API_PARTNER_USERS_013
**Mô tả test:** Đối trọng idempotency/duplicate của _002 (invite): mời cùng email hai lần không được tạo một user duplicate.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một user (email E); cùng payload được dùng lại cho lần re-invite.
**Các bước:**
1. Re-invite CÙNG email E.
   → Expected: một outcome xác định — reject (409) HOẶC idempotent (không user mới).
2. Verify partner KHÔNG kết thúc với một user duplicate-email (list các user của partner).
   → Expected: đúng 1 user cho email E. **Hiện FAIL** — list hiện 2.
**Teardown:** xóa partner cha.
**Expected (tổng):** Re-invite không được tạo một user duplicate-email (email là login identity).
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker BUG-004). Gap: re-invite trả 201 và tạo một user THỨ HAI cùng email (list hiện 2). BE nên reject (409) hoặc idempotent. Xác nhận với BE.

#### PARTNER_API_PARTNER_USERS_014
**Mô tả test:** Đối trọng negative của _003 (reset password): id không hợp lệ bị từ chối với code đúng (không bao giờ 5xx). Tự chứng minh; tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một POST /v1/sa/partner-users/{userId}/reset-password)
1. Ghost userId (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400 ("User 000… not found").
2. Malformed userId ('not-an-id') → **400** Bad Request, message "invalid id".
**Expected (tổng):** userId không tồn tại → 404; malformed userId → 400; không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một userId đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 2 đúng. Xác nhận với BE.
### API · TERRITORIES

#### PARTNER_API_TERRITORIES_001
**Mô tả test:** SA gán một territory cho một partner: POST /sa-partners-api/v1/sa/territories lưu nó với effective date.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; dựng một payload territory (partnerId + label + countries=[US,CA] + exclusivityType='preferred' + effective date).
**Các bước:**
1. Gán territory.
   → Expected: HTTP 201 (envelope statusCode 200/201); id do server cấp; message xác nhận.
2. Verify mọi field gửi đi được lưu (kể cả effective date).
   → Expected: partnerId/label/countries/exclusivityType echo; exclusivityStartDate/EndDate được giữ.
3. Verify truy xuất được qua GET by id.
   → Expected: trả về đúng territory.
**Teardown:** xóa territory + partner cha.
**Expected (tổng):** Gán territory được lưu với field + effective date, truy xuất được theo id.
**Ghi chú:** PASSED. exclusivityType ∈ exclusive/preferred/open; countries là ISO 3166-1 alpha-2. Đối trọng negative (field không hợp lệ) là _011; exclusive-conflict là _012.

#### PARTNER_API_TERRITORIES_002
**Mô tả test:** SA list territory với filter: GET /sa-partners-api/v1/sa/territories (paginated, scoped, filterable).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + gán một territory (countries=[US], exclusivityType='preferred').
**Các bước:**
1. GET territory lọc theo partnerId (limit=20).
   → Expected: HTTP 200; envelope {statusCode, data[], total} (list này không có field message).
2. Verify territory đã gán xuất hiện, scoped, với schema.
   → Expected: hiện diện với label/countries/exclusivityType; mọi row có partnerId == partner yêu cầu.
3. Lọc theo exclusivityType=preferred.
   → Expected: chỉ trả về row 'preferred'.
**Teardown:** xóa territory + partner cha.
**Expected (tổng):** Danh sách territory scope-partner, well-formed và filterable.
**Ghi chú:** PASSED. Envelope territory list không có field `message` (khác các list khác). Đối trọng negative (filter/pagination không hợp lệ) là _013.

#### PARTNER_API_TERRITORIES_003
**Mô tả test:** SA lấy một territory đơn theo id: GET /sa-partners-api/v1/sa/territories/{id}.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + gán một territory (countries=[US]); lấy id.
**Các bước:**
1. GET territory theo id.
   → Expected: HTTP 200; id khớp; có partnerId/label/countries/exclusivityType.
**Teardown:** xóa territory + partner cha.
**Expected (tổng):** Get-by-id trả về full territory.
**Ghi chú:** PASSED. Đối trọng negative (id không hợp lệ) là _014.

#### PARTNER_API_TERRITORIES_004
**Mô tả test:** SA gỡ một territory assignment: DELETE /sa-partners-api/v1/sa/territories/{id}.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + gán một territory (countries=[US]); lấy id.
**Các bước:**
1. Xóa territory.
   → Expected: HTTP 200/204 (delete thành công).
2. Verify territory không còn truy xuất được (GET by id).
   → Expected: GET trả 4xx not-found.
**Teardown:** xóa partner cha.
**Expected (tổng):** Delete gỡ territory; không còn truy xuất được.
**Ghi chú:** PASSED. Đối trọng negative (không hợp lệ/đã-gỡ) là _015.

#### PARTNER_API_TERRITORIES_011
**Mô tả test:** Đối trọng negative của _001 (assign): tám payload không hợp lệ/thiếu, mỗi cái bị từ chối với 400 + một message mô tả. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner (payload territory baseline hợp lệ).
**Các bước:** (mỗi case = một POST /v1/sa/territories với field đang test bị hỏng)
1. Thiếu partnerId → **400** 'partnerId must be a mongodb id'.
2. Thiếu label → **400** message đề cập "label".
3. Thiếu countries → **400** message đề cập "countries".
4. exclusivityType không hợp lệ ('bogus') → **400** 'exclusivityType must be one of'.
5. Country code không hợp lệ ('ZZ') → **400** message đề cập "iso31661".
6. Start date sai ('31-12-2026') → **400** 'iso 8601'.
7. Ghost partnerId (đúng định dạng nhưng không tồn tại, gửi như một BODY FK) → **400** 'Partner … not found'.
8. Malformed partnerId ('not-an-id') → **400** 'mongodb id'.
**Teardown:** xóa partner cha.
**Expected (tổng):** Mọi assign không hợp lệ bị từ chối với 400 + một message field/rõ ràng; không tạo territory.
**Ghi chú:** PASSED. Case 7 (ghost partnerId) là một foreign-key reference trong BODY, nên 400 được chấp nhận (khác với một ghost PATH id → 404); tự chứng minh.

#### PARTNER_API_TERRITORIES_012
**Mô tả test:** Conflict territory exclusive (đối trọng duplicate/conflict của _001): một partner thứ 2 không thể lấy một country đã được giữ exclusive.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo hai partner (p1, p2); chọn một country code ít gặp (IS) để giảm collision.
**Các bước:**
1. Partner 1 lấy một territory EXCLUSIVE trên country.
   → Expected: HTTP 201, territory được tạo (country còn trống).
2. Partner 2 gán một territory EXCLUSIVE trên CÙNG country.
   → Expected: 4xx; message chứa "exclusive" + "conflict".
3. Verify không có territory nào được tạo cho partner 2 (soi response bị từ chối).
   → Expected: không có territory id trong body.
**Teardown:** xóa territory + cả hai partner.
**Expected (tổng):** Overlap exclusive cross-partner bị từ chối; overlap same-partner được cho phép theo thiết kế.
**Ghi chú:** PASSED. BE enforce conflict exclusive cross-partner.

#### PARTNER_API_TERRITORIES_013
**Mô tả test:** Đối trọng negative của _002 (list): năm input filter/pagination không hợp lệ, mỗi cái bị từ chối với 400 + một message rõ ràng (endpoint này validate chặt — không default lỏng; không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/territories với một query không hợp lệ)
1. exclusivityType sai ('bogus') → **400** 'exclusivityType must be one of'.
2. Country sai ('ZZ') → **400** message đề cập "iso31661".
3. limit quá max (999999) → **400** 'must not exceed'.
4. page=0 → **400** 'non-negative'.
5. Malformed partnerId ('not-an-id') → **400** 'mongodb id'.
**Expected (tổng):** Mọi filter/pagination không hợp lệ bị từ chối với 400; không bao giờ 5xx.
**Ghi chú:** PASSED. Endpoint này validate chặt (không default lỏng, khác partner-users list _011).

#### PARTNER_API_TERRITORIES_014
**Mô tả test:** Đối trọng negative của _003 (get by id): id không hợp lệ bị từ chối với code đúng (không bao giờ 5xx). Tự chứng minh; tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/territories/{id})
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400 ("Territory 000… not found").
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1): một id đúng định dạng nhưng không tồn tại trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 2 đúng. Xác nhận với BE.

#### PARTNER_API_TERRITORIES_015
**Mô tả test:** Đối trọng negative của _004 (delete): không hợp lệ/đã-gỡ bị từ chối với code đúng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + gán một territory (target cho case đã-gỡ).
**Các bước:** (mỗi case = một DELETE /v1/sa/territories/{id})
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → kỳ vọng **404** Not Found, message "not found". **Hiện FAIL** — BE trả 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Territory đã-gỡ (xóa nó, rồi xóa lại) → kỳ vọng **404** Not Found (target không còn tồn tại). **Hiện FAIL** — BE trả 400 ("Territory … not found").
**Teardown:** xóa partner cha.
**Expected (tổng):** Target không tồn tại / đã-gỡ → 404; malformed id → 400. (Đã-gỡ ghi lại hành vi lặp của delete; mutating action, không phải duplicate-create.)
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1 & 3): một target not-found trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 2 (malformed) đúng. Xác nhận với BE.
### API · CERTIFICATIONS_SA

#### PARTNER_API_CERTIFICATIONS_SA_001
**Ghi chú (CROSS-REF):** Grant một certification đã được cover bởi PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010 (certification earned: granted + listed + event + re-evaluate tier), với _020 (grant input không hợp lệ) và _022 (re-grant idempotency, fail-by-design). Không re-implement ở đây để tránh một test duplicate. Nếu cần một CERTIFICATIONS_SA_001 standalone, trỏ nó vào cùng endpoint POST /v1/sa/partner-users/{userId}/certifications.

#### PARTNER_API_CERTIFICATIONS_SA_002
**Mô tả test:** SA revoke một partner certification: DELETE /sa-partners-api/v1/sa/partner-users/{userId}/certifications/{type} (body reason) soft-revoke nó.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một user + grant một active sales_certified cert.
**Các bước:**
1. Revoke certification (với một reason).
   → Expected: HTTP 200; message xác nhận; status='revoked'.
2. Verify cert hiện là revoked trong cert list của partner (soft-revoke).
   → Expected: record cert vẫn còn với status='revoked' (không bị hard-remove).
**Teardown:** xóa partner cha.
**Expected (tổng):** Revoke soft-remove cert (status='revoked'), giữ trong list.
**Ghi chú:** PASSED. TC↔BE: plan ghi "certification removed", BE soft-revoke (status='revoked', giữ record) — xác nhận BE. Đối trọng negative (input/state không hợp lệ) là _012.

#### PARTNER_API_CERTIFICATIONS_SA_003
**Mô tả test:** SA list certification của một partner team: GET /sa-partners-api/v1/sa/partners/{partnerId}/certifications.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một user + grant một sales_certified cert.
**Các bước:**
1. GET certification của partner (limit=20).
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}.
2. Verify cert đã grant xuất hiện với schema, scope theo partner.
   → Expected: cert hiện diện với certificationType/status/userId/earnedAt/expiresAt; mọi row có partnerId == partner yêu cầu.
3. Lọc theo status=active.
   → Expected: chỉ trả về active cert.
**Teardown:** xóa partner cha.
**Expected (tổng):** Danh sách cert scope-partner, well-formed và filterable.
**Ghi chú:** PASSED. Filter: status ∈ active/expired/revoked; enum certificationType; expiringWithinDays. Đối trọng negative (filter/pagination không hợp lệ) là _013.

#### PARTNER_API_CERTIFICATIONS_SA_004
**Mô tả test:** SA list certification sắp hết hạn: GET /sa-partners-api/v1/sa/certifications?expiringWithinDays=N.
**Các bước:**
1. GET /sa/certifications?expiringWithinDays=30.
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}; mọi cert trả về hết hạn trong 30 ngày (một kết quả rỗng chấp nhận được — WARN-skip).
2. Boundary max của expiringWithinDays (365) được chấp nhận.
   → Expected: HTTP 200.
**Expected (tổng):** Danh sách cert sắp hết hạn trả về một envelope well-formed; cửa sổ expiringWithinDays giới hạn 1..365.
**Ghi chú:** PASSED. Xác nhận BE: list SA-wide trả total=0 ngay cả khi có active cert (thấy được qua per-partner list _003) — có thể khác biệt scoping/index; ngữ nghĩa filter được assert trên bất kỳ cái gì trả về, case rỗng WARN-skip. Đối trọng negative (filter/pagination không hợp lệ) là _014.

#### PARTNER_API_CERTIFICATIONS_SA_012
**Mô tả test:** Đối trọng negative của _002 (revoke): năm case input/state không hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner + mời một user + grant một active sales_certified cert.
**Các bước:** (mỗi case = một DELETE /v1/sa/partner-users/{userId}/certifications/{type})
1. Thiếu reason → **400** 'reason should not be empty'.
2. Cert không có ('hr_specialist', user hợp lệ không có nó) → kỳ vọng **404** Not Found ('Active … not found'). **Hiện FAIL** — BE trả 400.
3. Ghost userId (đúng định dạng nhưng không tồn tại) → kỳ vọng **404** Not Found ('User … not found'). **Hiện FAIL** — BE trả 400.
4. Malformed userId ('not-an-id') → **400** 'invalid id'.
5. Cert đã-revoke (revoke, rồi revoke lại) → kỳ vọng **404** Not Found (không có active cert). **Hiện FAIL** — BE trả 400.
**Teardown:** xóa partner cha.
**Expected (tổng):** Thiếu reason / malformed id → 400; mọi target not-found → 404. Không bao giờ 5xx.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 2, 3, 5): một target not-found trả **400** ("not found") thay vì **404** — cùng root cause với gap get-by-id của deals. Case 1 & 4 đúng. Xác nhận với BE.

#### PARTNER_API_CERTIFICATIONS_SA_013
**Mô tả test:** Đối trọng negative của _003 (list cert theo partner): filter/pagination không hợp lệ được xử lý với code đúng — case đã validate 4xx, một ghost partner scope 200-empty — không bao giờ 5xx. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner (baseline).
**Các bước:** (mỗi case = một GET /v1/sa/partners/{partnerId}/certifications với param đang test)
1. Enum status sai ('bogus') → **400** 'status must be one of'.
2. Enum certificationType sai ('bogus') → **400** 'certificationType must be one of'.
3. limit quá max (999999) → **400** 'must not exceed 100'.
4. Malformed partnerId ('not-an-id') → **400** 'invalid id'.
5. Ghost partnerId (đúng định dạng nhưng không tồn tại, dùng như SCOPE của list) → **200** với một list rỗng (một scope không khớp gì, không phải 404).
6. page=0 → **400** 'non-negative' (bị từ chối; không bao giờ 5xx).
**Expected (tổng):** Filter/pagination không hợp lệ đã validate → 4xx; một ghost partner scope → 200-empty; không bao giờ 5xx.
**Ghi chú:** PASSED. Ghost partnerId ở đây là SCOPE của list → 200-empty được chấp nhận (khác với một ghost PATH id trong get/revoke → 404). page=0 bị từ chối (400), không lỏng.

#### PARTNER_API_CERTIFICATIONS_SA_014
**Mô tả test:** Đối trọng negative của _004 (SA cert list): bảy input filter/pagination không hợp lệ, mỗi cái bị từ chối với 400 + một message rõ ràng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/certifications với một query không hợp lệ)
1. Enum status sai ('bogus') → **400** 'status must be one of'.
2. Enum certificationType sai ('bogus') → **400** 'certificationType must be one of'.
3. expiringWithinDays = 0 → **400** 'must not be less than 1'.
4. expiringWithinDays âm → **400** 'must not be less than 1'.
5. expiringWithinDays > 365 (366) → **400** 'must not be greater than 365'.
6. limit quá max (999999) → **400** 'limit must not exceed 100'.
7. page=0 → **400** 'non-negative'.
**Expected (tổng):** Mọi filter/pagination không hợp lệ bị từ chối với 400; không bao giờ 5xx. expiringWithinDays giới hạn 1..365.
**Ghi chú:** PASSED.
### API · TEAM_REFERRAL_LINKS

#### PARTNER_API_TEAM_REFERRAL_LINKS_001
**Ghi chú (BLOCKED):** Endpoint referral vắng khỏi spec đã deploy (xác nhận 2026-06-30: 0 referral path). GET /v1/partner/referral-links chưa implement. Unblock khi BE ship API referral-links.

#### PARTNER_API_TEAM_REFERRAL_LINKS_002
**Ghi chú (BLOCKED):** Endpoint referral vắng (0 referral path, 2026-06-30). POST /v1/partner/referral-links (tạo link tracking campaign) chưa implement.

### API · RESOURCES_SANDBOX

#### PARTNER_API_RESOURCES_SANDBOX_001
**Ghi chú (BLOCKED):** Endpoint sandbox vắng khỏi spec đã deploy (xác nhận 2026-06-30: 0 sandbox path). Không có API để request reset sandbox / apply một profile. Unblock khi BE ship module sandbox.

#### PARTNER_API_RESOURCES_SANDBOX_002
**Ghi chú (BLOCKED):** Endpoint sandbox vắng (0 sandbox path, 2026-06-30); cũng là một CRON theo lịch (auto-reset hàng tuần, mặc định off). Không có API để trigger/quan sát. Unblock khi BE ship sandbox + một job trigger.

#### PARTNER_API_RESOURCES_SANDBOX_003
**Ghi chú (BLOCKED):** Endpoint sandbox vắng (0 sandbox path, 2026-06-30). Không có API để chạy reseed một profile (SMB/Mid-market/Enterprise) hay assert việc hoàn thành ≤5 phút.
### API · DASHBOARD_DATA

#### PARTNER_API_DASHBOARD_DATA_001
**Mô tả test:** Stats dashboard của partner: GET /sa-partners-api/v1/partner/portal/dashboard trả về schema KPI (partner JWT).
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal (SA tạo + approve một partner, mời một user, login bằng user đó → partner JWT).
**Các bước:**
1. GET dashboard partner.
   → Expected: HTTP 200; envelope {statusCode, data{}, message}; `data` là một object không rỗng.
2. Verify schema KPI + không lộ field nhạy cảm.
   → Expected: `data` có các section 'partner' (tier/status/openDealsCount), 'deals', 'commissions'; không có key password/token/secret/credential.
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Dashboard partner trả về schema KPI well-formed, không lộ credential.
**Ghi chú:** PASSED. Endpoint PARTNER-PORTAL (cần một partner JWT, không phải SA token; SA token → 401). Không có negative invalid-input (không param); 401 auth thuộc về Auth & Access Control. Idempotency: GET read-only → N/A.
### API · CRM_INTEGRATION

> Tất cả BLOCKED — CRM connector downstream (event được consume bởi service connectors/CRM, không tiếp cận được từ domain này). Các event quan sát được qua API đã được cover bởi DEAL_010 / AUDIT_LOG_*; side-effect phía CRM ngoài phạm vi ở đây. Unblock khi việc verify CRM được expose cho QA.

#### PARTNER_API_CRM_INTEGRATION_001
**Ghi chú (BLOCKED):** "Deal registered → tạo opportunity trong dogfood CRM." Phía CRM không tiếp cận được.

#### PARTNER_API_CRM_INTEGRATION_002
**Ghi chú (BLOCKED):** "Deal protection extended → cập nhật meta opportunity CRM." Phía CRM không tiếp cận được.

#### PARTNER_API_CRM_INTEGRATION_003
**Ghi chú (BLOCKED):** "Deal lost → CRM Close Lost + close reason." Phía CRM không tiếp cận được.

#### PARTNER_API_CRM_INTEGRATION_004
**Ghi chú (BLOCKED):** "Deal expired → CRM mark stale + SA task." Phụ thuộc expiry CRON + CRM connector, cả hai không tiếp cận được.

#### PARTNER_API_CRM_INTEGRATION_005
**Ghi chú (BLOCKED):** "client.health_alert → CRM task." Phụ thuộc module MSP/client-health (cũng vắng) + CRM connector.

### API · EVENT_ARCHITECTURE

#### PARTNER_API_EVENT_ARCHITECTURE_001
**Ghi chú (BLOCKED):** Envelope/metadata Kafka là một thuộc tính event-bus internal không có API để soi trực tiếp. Sự hiện diện của event quan sát được một phần qua SA audit log (DEAL_010 / AUDIT_LOG_*), nhưng assertion "Kafka standard envelope" theo nghĩa đen không verify được qua API. Re-scope sang envelope audit-log, hoặc verify qua BE/infra.
### API · PARTNER_PORTAL

> Mọi endpoint partner-portal cần một PARTNER JWT (không phải SA token). Session được
> mint self-contained từ phía SA qua `utils.partner_portal.mint_partner_session`
> (create + approve partner, invite user, partner login). Mọi read endpoint là GET
> (read-only → idempotency N/A). Không phụ thuộc sa-plans trừ _002 (deal detail).

#### PARTNER_API_PARTNER_PORTAL_001
**Mô tả test:** Partner lấy profile account của chính mình: GET /partner/portal/profile.
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal (partner JWT).
**Các bước:**
1. GET profile của chính mình.
   → Expected: HTTP 200; `data` là account của partner đang login (id==own, có code/email/tier/status); không có key password/token/secret/credential.
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Profile của chính mình được trả về, không lộ credential.
**Ghi chú:** PASSED. Không param (không có input-negative; 401 → Auth feature). GET → idempotency N/A.

#### PARTNER_API_PARTNER_PORTAL_002
**Mô tả test:** Partner lấy deal của chính mình theo id: GET /partner/portal/deals/{id} — full record.
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal; partner đăng ký một deal qua POST /partner/portal/deals; lấy id.
**Các bước:**
1. GET deal của chính mình theo id.
   → Expected: HTTP 200; id trả về khớp; partnerId == partner đang login; có dealType/prospectName/status.
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Một partner có thể đọc full record của deal của chính mình.
**Ghi chú:** PASSED. Đối trọng negative (id không hợp lệ) là _012.

#### PARTNER_API_PARTNER_PORTAL_003
**Mô tả test:** Partner lấy các certification của chính mình: GET /partner/portal/certifications.
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal; SA grant một sales_certified cert cho partner user.
**Các bước:**
1. GET các certification của chính mình.
   → Expected: HTTP 200; `data` là một list không rỗng.
2. Verify cert đã grant xuất hiện với schema đúng.
   → Expected: cert đã grant hiện diện với status + earnedAt + expiresAt.
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Cert của chính mình được list với schema đúng.
**Ghi chú:** PASSED. Đối trọng negative (filter không hợp lệ) là _013.

#### PARTNER_API_PARTNER_PORTAL_004
**Mô tả test:** Partner lấy commission summary của chính mình: GET /partner/portal/commissions/summary.
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal.
**Các bước:**
1. GET commission summary của chính mình.
   → Expected: HTTP 200; totalEarnedCents/totalPendingCents/totalPaidCents là int không âm (+ clawbackExposureCents).
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Total earned/pending/paid được trả về.
**Ghi chú:** PASSED. Không param (không có input-negative); GET → idempotency N/A.

#### PARTNER_API_PARTNER_PORTAL_005
**Mô tả test:** Partner lấy các territory được gán của chính mình: GET /partner/portal/territories.
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal; SA gán một territory (countries=[DE]) cho partner.
**Các bước:**
1. GET các territory của chính mình.
   → Expected: HTTP 200; `data` là một list không rỗng; territory đã gán xuất hiện và mọi row scope theo partner (partnerId == own).
**Teardown:** đóng session portal; xóa territory + partner.
**Expected (tổng):** Territory của chính mình được trả về, scoped.
**Ghi chú:** PASSED. Không param (không có input-negative); GET → idempotency N/A.

#### PARTNER_API_PARTNER_PORTAL_006
**Mô tả test:** Partner lấy tier commission rate của chính mình: GET /partner/portal/rates.
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal.
**Các bước:**
1. GET commission rate của chính mình.
   → Expected: HTTP 200; `data` là một list tier rate well-formed (có thể rỗng cho tier registered — WARN-skip).
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Rate theo tier được trả về dưới dạng một list.
**Ghi chú:** PASSED. List rate rỗng cho một partner tier-registered trên staging (vẫn là một list well-formed). Không param (không có input-negative); GET → idempotency N/A.
#### PARTNER_API_PARTNER_PORTAL_012
**Mô tả test:** Đối trọng negative của _002 (own deal by id): một ghost / malformed deal id bị từ chối với code đúng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal.
**Các bước:** (mỗi case = một GET /partner/portal/deals/{id})
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → **404** Not Found, message "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; không bao giờ 5xx.
**Ghi chú:** PASSED. Đáng chú ý: endpoint partner-portal này trả **404** đúng cho một ghost id — khác với các endpoint get-by-id phía SA vốn trả 400 (gap hệ thống tracked trong Bug_Tracker BUG-006…019). Test ghim đúng 404 để một regression sẽ bị bắt.

#### PARTNER_API_PARTNER_PORTAL_013
**Mô tả test:** Đối trọng negative của _003 (own certs): ba filter không hợp lệ, mỗi cái bị từ chối với 400 + một message rõ ràng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** Mint một session partner-portal.
**Các bước:** (mỗi case = một GET /partner/portal/certifications với một filter không hợp lệ)
1. Enum status sai ('bogus') → **400** 'status must be one of'.
2. Enum certificationType sai ('bogus') → **400** 'certificationType must be one of'.
3. limit quá max (999999) → **400** 'must not exceed'.
**Teardown:** đóng session portal; xóa partner.
**Expected (tổng):** Filter cert không hợp lệ bị từ chối với 400; không bao giờ 5xx.
**Ghi chú:** PASSED.

### API · SECURITY_COMPLIANCE

#### PARTNER_API_SECURITY_COMPLIANCE_001
**Ghi chú (NOT_STARTED — buildable):** Endpoint audit-log tồn tại: thực hiện một SA action (approve/deactivate) rồi GET /v1/sa/audit-logs và assert entry mang actor + action + reasoning + correlationId. Được cover một phần bởi DEAL_010 / ACCOUNT_MANAGEMENT_004; một TC envelope-completeness chuyên dụng build được.

#### PARTNER_API_SECURITY_COMPLIANCE_002
**Ghi chú (BLOCKED):** Không có API/rule để assert data-minimization của prospect (PII không cần thiết bị reject / không lưu). Không có endpoint enforce hay expose một rule PII-minimization để test. Xác nhận với BE nơi cái này được enforce.

#### PARTNER_API_SECURITY_COMPLIANCE_003
**Ghi chú (BLOCKED):** Data residency (lưu trữ khu vực UAE) là một thuộc tính infra/region không có API để xác nhận dữ liệu lưu ở đâu. Verify qua review infra/DB, không qua API.
### API · AUDIT_LOG

#### PARTNER_API_AUDIT_LOG_001
**Mô tả test:** SA list các entry audit log: GET /sa-partners-api/v1/sa/audit-logs trả về một audit trail paginated, filterable, well-formed.
**Các bước:**
1. GET audit-logs (page=1, limit=5).
   → Expected: HTTP 200, envelope {statusCode, data[], total, message}.
2. Kiểm tra pagination.
   → Expected: page size trả về ≤ limit.
3. Kiểm tra schema mỗi entry + không lộ field nhạy cảm.
   → Expected: có id/action/category/severity/createdAt với type đúng; actor/resource là object; không có key password/token/secret.
4. Lọc theo category (lấy từ entry đầu).
   → Expected: chỉ trả về entry của category đó.
**Expected (tổng):** Audit-log list trả về một envelope đúng, paginated, filterable với các entry well-formed, không nhạy cảm.
**Ghi chú:** PASSED — verified 2026-06-25. Read-only (không setup/cleanup, không phụ thuộc sa-plans).

#### PARTNER_API_AUDIT_LOG_002
**Mô tả test:** SA lấy KPI stats của audit-log: GET /sa-partners-api/v1/sa/audit-logs/stats trả về counter 24h + chain integrity.
**Các bước:**
1. GET audit-logs/stats.
   → Expected: HTTP 200, envelope {statusCode, data{}, message}.
2. Kiểm tra field KPI + type.
   → Expected: totalEvents24h/criticalEvents24h/warnings24h/uniqueActors24h là int không âm; chainIntegrityPct là một percentage 0..100.
3. Kiểm tra tính nhất quán nội bộ.
   → Expected: count critical/warnings/uniqueActors không bao giờ vượt totalEvents24h.
**Expected (tổng):** Endpoint stats trả về các KPI 24h well-typed, nhất quán nội bộ.
**Ghi chú:** PASSED — verified 2026-06-25. Read-only, không param (nên không có negative invalid-input), không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_003
**Mô tả test:** SA export audit log dưới dạng JSON hoặc CSV: GET /sa-partners-api/v1/sa/audit-logs/export trả về một file tải xuống được (cap ở 10000 row).
**Các bước:**
1. Export format=json.
   → Expected: 200, content-type application/json, body là một JSON array; ≤10000 row; mỗi row có _id/action/category/severity/createdAt.
2. Export format=csv.
   → Expected: 200, content-type text/csv, header row mang các cột audit.
3. Không có param format.
   → Expected: 200, default sang CSV.
**Expected (tổng):** Export audit-log trả về một file JSON hoặc CSV well-formed (default CSV), trong cap 10000 row.
**Ghi chú:** PASSED — verified 2026-06-25. format enum [csv, json], default csv. Không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_004
**Mô tả test:** SA lấy một entry audit-log đơn theo id: GET /sa-partners-api/v1/sa/audit-logs/{id} trả về full entry.
**Các bước:**
1. List với limit=1 để chọn một entry id thật.
   → Expected: một entry có một _id (skip nếu log rỗng).
2. GET audit-logs/{id}.
   → Expected: 200; data._id khớp; có action/category/severity/createdAt; actor/resource là object; không có key nhạy cảm.
**Expected (tổng):** Get-by-id trả về full entry well-formed, không lộ field nhạy cảm.
**Ghi chú:** PASSED — verified 2026-06-25. Read-only, không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_005
**Mô tả test:** Đối trọng negative của _001 (audit-log list): mười một input pagination/filter không hợp lệ mỗi cái bị từ chối với 400 (không bao giờ 5xx), cộng một range hợp lệ-nhưng-rỗng-về-logic được xử lý gracefully. Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/audit-logs với param đang test)
1. page=0 → **400** 'page must not be less than 1'.
2. page=-1 → **400** 'page must not be less than 1'.
3. limit=0 → **400** 'limit must not be less than 1'.
4. limit=-5 → **400** 'limit must not be less than 1'.
5. limit quá max (999999) → **400** 'limit must not be greater than 100'.
6. page không phải số ('abc') → **400** 'page must be an integer'.
7. severity không hợp lệ ('bogus') → **400** 'severity must be one of'.
8. category không hợp lệ ('bogus') → **400** 'category must be one of'.
9. actorType không hợp lệ ('bogus') → **400** 'actorType must be one of'.
10. dateFrom sai ('31-12-2026') → **400** 'dateFrom must be a valid ISO…'.
11. dateTo sai ('not-a-date') → **400** 'dateTo must be a valid ISO…'.
12. Range hợp lệ-nhưng-rỗng (dateFrom > dateTo) → xử lý gracefully (< 500; 200 rỗng, không phải error).
**Expected (tổng):** Mọi pagination/filter không hợp lệ → 400 (không bao giờ 5xx); một range rỗng hợp lệ trả về gracefully.
**Ghi chú:** PASSED. Enum: severity ∈ info/warning/critical; category ∈ SA_AUDIT_*; actorType ∈ sa-staff/impersonation/…

#### PARTNER_API_AUDIT_LOG_006
**Mô tả test:** Đối trọng negative của _003 (audit-log export): bảy input format/filter không hợp lệ, mỗi cái bị từ chối với 400 + một message rõ ràng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/audit-logs/export với param đang test)
1. format bogus ('bogus') → **400** 'format must be one of'.
2. severity không hợp lệ ('bogus') → **400** 'severity must be one of'.
3. category không hợp lệ ('bogus') → **400** 'category must be one of'.
4. actorType không hợp lệ ('bogus') → **400** 'actorType must be one of'.
5. retentionClass không hợp lệ ('bogus') → **400** 'retentionClass must be one of'.
6. dateFrom sai ('31-12-2026') → **400** 'dateFrom must be a valid ISO…'.
7. dateTo sai ('not-a-date') → **400** 'dateTo must be a valid ISO…'.
**Expected (tổng):** Mọi format/filter export không hợp lệ bị từ chối với 400 (không bao giờ 5xx).
**Ghi chú:** PASSED. retentionClass enum ∈ standard/extended/permanent; format enum ∈ csv/json.
#### PARTNER_API_AUDIT_LOG_007
**Mô tả test:** Negative của _004 (get audit entry theo id): id không hợp lệ bị từ chối (4xx, không bao giờ 5xx).
**Các bước:**
1. GET audit-logs/{ghost id}.
   → Expected: 404 'Audit log entry ... not found'.
2. GET audit-logs/{malformed id}.
   → Expected: 400 'Invalid id'.
**Expected (tổng):** Id không tồn tại → 404, malformed id → 400; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Tự chứng minh (endpoint trả not-found), không cần setup, không phụ thuộc sa-plans.
