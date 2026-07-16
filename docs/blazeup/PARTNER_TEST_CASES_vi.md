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

> Auth flow partner. Session mint self-contained từ phía SA (`utils.partner_portal`).
> Endpoint auth (`/partner/auth/*`) trả token + `/me` identity ở TOP-LEVEL (không có
> wrapper `data`). Không phải resource-create → không idempotency; mỗi TC tự gồm
> negative (rejection/invalidation).

#### PARTNER_API_AUTH_ACCESS_CONTROL_001
**Mô tả test:** Partner JWT hợp lệ authorize request scope partner.
**Các bước:**
1. Provision + login partner user; GET /partner/auth/me với JWT.
   → Expected: 200, identity (userId + email).
**Expected (tổng):** JWT partner hợp lệ authorize request.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_002
**Mô tả test:** Token non-partner / thiếu token trên partner API → unauthorized.
**Các bước:**
1. GET /partner/auth/me không token → 401.
2. GET /partner/auth/me với token SA (non-partner) → 401.
**Expected (tổng):** Token thiếu / non-partner bị 401.
**Ghi chú:** PASSED — verified 2026-06-25. (Dùng SA admin token thay cho "tenant JWT" — đều là token non-partner.) Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_003
**Mô tả:** Cross-partner — partner JWT KHÔNG đọc được deal của partner khác (tenant isolation).
**Các bước:**
1. Partner A (session riêng) đăng ký 1 deal; lấy id.
2. Partner B (session riêng) GET /partner/portal/deals/{A_deal_id}.
   → Kỳ vọng: bị từ chối (4xx — BE trả 400), và body KHÔNG trả deal của A.
**Kỳ vọng (tổng):** Partner không truy cập được deal của partner khác — bị từ chối, không lộ dữ liệu.
**Ghi chú:** PASSED — verified 2026-06-30 (sa-plans UP lại). Đây là case cross-entity của rule 5. BE trả 400 (không phải 403/404) khi partner gọi deal id của partner khác; vẫn bị từ chối, không lộ dữ liệu.

#### PARTNER_API_AUTH_ACCESS_CONTROL_004
**Ghi chú (NOT_STARTED):** Admin MFA policy — cần flow MFA enroll/challenge. Chưa automate (assess /partner/auth/mfa/*).

#### PARTNER_API_AUTH_ACCESS_CONTROL_005
**Ghi chú (NOT_STARTED):** Guard — MSP truy cập payroll bị cấm. Cần xác định có API surface trong domain này không.

#### PARTNER_API_AUTH_ACCESS_CONTROL_006
**Ghi chú (NOT_STARTED):** Guard — MSP export employee records bị cấm. Như _005.

#### PARTNER_API_AUTH_ACCESS_CONTROL_007
**Mô tả test:** Refresh token hợp lệ cấp access token mới (không re-login).
**Các bước:**
1. Login (lưu refresh token); POST /partner/auth/refresh.
   → Expected: 200, accessToken mới (khác cũ).
2. Access token mới authorize GET /me.
   → Expected: 200.
3. Refresh token sai.
   → Expected: 401.
**Expected (tổng):** Refresh cấp access token mới hoạt động; refresh sai bị từ chối.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_008
**Mô tả test:** Logout invalidate refresh token.
**Các bước:**
1. Login; POST /partner/auth/logout (access token) → 204.
2. POST /partner/auth/refresh với refresh token đã invalidate → 401.
**Expected (tổng):** Sau logout refresh token không cấp access token được nữa.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_AUTH_ACCESS_CONTROL_009
**Mô tả test:** Change password cập nhật credential (mới được, cũ fail).
**Các bước:**
1. Change-password với currentPassword SAI → 401 ("Current password is incorrect").
2. Change-password với currentPassword đúng → 204.
3. Login bằng password MỚI → 200.
4. Login bằng password CŨ → 401.
**Expected (tổng):** Đổi pass từ chối current sai; credential mới hoạt động, cũ bị từ chối.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.
### API · DEAL_REGISTRATION_PIPELINE

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_001
**Mô tả test:** Happy-path đăng ký deal POST /v1/sa/deals — payload hợp lệ tạo deal 'registered' + cửa sổ bảo vệ.
**Các bước:**
1. Auth SA; tạo partner; lấy 1 billing plan published.
   → Expected: partner tạo xong; có planId published.
2. POST /v1/sa/deals đủ field (partnerId, planId, dealType='referral', prospect*, ACV, closeDate, notes).
   → Expected: HTTP 201 + _id do server cấp.
3. Assert mọi field gửi đi được lưu nguyên vẹn.
   → Expected: đủ 10 field echo; expectedCloseDate giữ đúng ngày.
4. Assert lifecycle.
   → Expected: status 'registered', có protectionExpiresAt, conflictStatus 'none'.
5. GET /v1/sa/deals/{id}.
   → Expected: trả đúng deal, status 'registered'.
6. Teardown: xóa partner cha.
   → Expected: cleanup OK (deal không có endpoint delete).
**Expected (tổng):** Deal đăng ký, mọi field lưu chính xác, mở cửa sổ bảo vệ, truy xuất được.
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_002
**Mô tả test:** Đăng ký reseller deal — billing model 'reseller' được lưu.
**Các bước:**
1. Tạo partner; lấy plan published; register deal dealType='reseller'.
   → Expected: HTTP 201 + _id.
2. Assert billing model + echo.
   → Expected: dealType lưu == 'reseller'; mọi field echo.
3. Assert lifecycle + GET by id.
   → Expected: status 'registered', có protection, dealType 'reseller' lưu.
**Expected (tổng):** Reseller deal đăng ký; dealType='reseller' chính là billing model (không có field riêng).
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_003
**Mô tả test:** Đăng ký co-sell deal — co-sell metadata được lưu.
**Các bước:**
1. Tạo partner; lấy plan published; register deal dealType='co_sell'.
   → Expected: HTTP 201 + _id.
2. Assert co-sell + echo.
   → Expected: dealType lưu == 'co_sell'; mọi field echo.
3. Assert lifecycle + GET by id.
   → Expected: status 'registered', có protection, dealType 'co_sell' lưu.
**Expected (tổng):** Co-sell deal đăng ký; dealType='co_sell' chính là metadata. Split 70/30 là downstream (_011, blocked).
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_004
**Mô tả test:** Bảo vệ deal: partner thứ hai đăng ký cùng prospect bị gắn conflict.
**Các bước:**
1. Tạo 2 partner + 1 prospect chung (name+email); partner 1 đăng ký deal.
   → Expected: deal A conflictStatus 'none'.
2. Partner 2 đăng ký CÙNG prospect.
   → Expected: HTTP 201 nhưng conflictStatus 'flagged'; conflictingDealId == deal A.
3. GET /v1/sa/deals/{id} deal B.
   → Expected: conflictStatus vẫn 'flagged'.
**Expected (tổng):** Deal cross-partner cùng prospect được tạo nhưng bị flag tham chiếu deal đầu.
**Ghi chú:** Cùng partner đăng ký lại prospect đó → 400 duplicate (behavior khác).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_005
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_006
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_007
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_008
**Mô tả test:** Approve deal đã register (POST /v1/sa/deals/{id}/approve): status -> approved, stamp reviewer; kỳ vọng rate + rate table version.
**Các bước:**
1. Tạo partner; register deal (registered).
   → Expected: deal 'registered'.
2. Approve (reviewNotes).
   → Expected: HTTP 201; status 'approved'.
3. Assert stamp reviewer.
   → Expected: có reviewedAt + reviewedBy.
4. Assert stamp rate + rateTableVersion.
   → Expected: có rate + rateTableVersion trong response.
**Expected (tổng):** Deal approved + stamp reviewer; phần rate/rate-table-version chờ BE.
**Ghi chú:** FAILED (có chủ đích) — gap: rate/rateTableVersion KHÔNG có trong response (và approve không tạo commission). Confirm BE: stamp nội bộ / stage khác (win) / chưa implement.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_009
**Mô tả test:** Resolve conflict deal (POST /v1/sa/deals/{id}/resolve-conflict): decision + reasoning được stamp và bất biến.
**Các bước:**
1. Tạo conflict flagged (2 partner, cùng prospect).
   → Expected: deal B 'flagged'.
2. Resolve (decision='resolved_for_partner', reasoning).
   → Expected: HTTP 201; conflictStatus='resolved_for_partner'; conflictResolution{decision,reasoning,resolvedBy,resolvedAt} khớp.
3. Resolve lại với decision/reasoning khác.
   → Expected: 4xx ('not in FLAGGED conflict state') — bất biến.
4. GET /v1/sa/deals/{id}.
   → Expected: decision + reasoning giữ nguyên (gốc).
**Expected (tổng):** Conflict resolve 1 lần; decision + reasoning bất biến.
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_010
**Mô tả test:** Approve deal phát event partner.deal.approved (trigger CRM sync).
**Các bước:**
1. Tạo partner; register deal.
   → Expected: deal 'registered'.
2. Approve deal.
   → Expected: status 'approved'.
3. GET /v1/sa/audit-logs.
   → Expected: event partner.deal.approved ghi chuyển registered->approved.
**Expected (tổng):** Event deal-approved được publish. Cập nhật CRM owner/stage là service downstream (connectors/CRM Integration), ngoài scope.
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_011
**Ghi chú (BLOCKED):** Chưa automate — trước đó bị gán nhầm PASSED/Auto=YES (false-green), đã sửa về BLOCKED. Split co-sell 70/30 được tính DOWNSTREAM; lúc register deal record không có field split (đã verify qua _003) và không có API đọc split đã tính → không assert được mức 70/30. Cùng họ dependency với _012. Unblock khi BE expose split đã tính (hoặc API split-calc).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_012
**Ghi chú (BLOCKED):** Phụ thuộc engine tính co-sell split (feature _011), vốn là downstream và không expose API — không có endpoint để submit split override, nên rule "override ≤$100K ACV bị từ chối" không test được (ngưỡng là TRÊN $100K ACV). Unblock khi BE expose API split-override.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_013
**Mô tả test:** Resolve deal đang FLAGGED THEO partner của nó (decision=resolved_for_partner, viện dẫn prospect xác nhận) → deal đó thắng và deal đối thủ tự động bị flip thành thua; cả 2 giữ status 'registered'.
**Các bước:**
1. Hai partner đăng ký CÙNG prospect (name+email); deal B (thứ hai) bị flagged.
   → Expected: deal B conflictStatus='flagged'.
2. Resolve deal B THEO partner của nó (decision='resolved_for_partner', reasoning viện dẫn prospect xác nhận).
   → Expected: HTTP 201; deal B conflictStatus='resolved_for_partner'; có ghi conflictResolution.
3. Kiểm deal đối thủ A.
   → Expected: deal A tự flip conflictStatus='resolved_against_partner' (thua).
4. GET cả 2 deal.
   → Expected: B 'resolved_for_partner' + status 'registered'; A 'resolved_against_partner' (đã lưu).
5. Teardown: xóa cả 2 partner.
   → Expected: cleanup OK.

**Expected (tổng):** partner được xác nhận thắng conflict, deal còn lại bị flip thành thua.
**Ghi chú:** Tính bất biến của decision/reasoning đã có ở _009; negative resolve ở _029.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_014
**Ghi chú (BLOCKED):** Không có API surface riêng. resolve-conflict (POST /v1/sa/deals/{id}/resolve-conflict) là quyết định thủ công của SA (enum resolved_for_partner|resolved_against_partner); không nhận tín hiệu "prospect unreachable" và không tự áp tiebreaker "first-registered-wins". Đường chạy duy nhất (SA tự resolve cho deal đăng ký trước) giống hệt _013 → không có gì riêng để assert. Unblock nếu BE implement tiebreaker tự động; nếu không thì coi như covered by _013.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_015
**Ghi chú (BLOCKED):** Phụ thuộc hạ tầng tenant-provisioning + commission không gọi được từ domain test này. Verify "no registration → no attribution/commission" cần POST /internal/tenants/provision (internal-only), đọc tenant.attribution.partnerId == null, assert không có dòng partner_commissions, và confirm không phát event blazeup.partner.commission.earned — không surface nào expose cho QA ở đây. Negative companion của PARTNER_API_006 (§3 Scenario I). Unblock khi có endpoint provisioning + verify commission/event.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_016
**Mô tả test:** SA gia hạn thủ công protection window của một deal đã registered (POST /v1/sa/deals/{id}/extend-protection, body addedDays + reasoning).
**Các bước:**
1. Tạo partner + chọn plan đã publish + register deal (lưu protectionExpiresAt).
   → Expected: deal registered có protection window.
2. POST extend-protection với addedDays=30 + reasoning.
   → Expected: HTTP 201 / body statusCode 200; có message xác nhận.
3. So sánh protectionExpiresAt mới với cũ.
   → Expected: window dời sau 30 ngày; deal vẫn 'registered'.
4. GET /v1/sa/deals/{id}.
   → Expected: protectionExpiresAt mới được lưu.
**Expected (tổng):** SA gia hạn thủ công đẩy protection window ra thêm đúng số ngày yêu cầu.
**Ghi chú:** PASSED — verified 2026-06-30. Window cộng đúng addedDays vào expiry CŨ (vd +30d: 2026-08-29 → 2026-09-28). Plan mô tả "request queued cho SA" nhưng endpoint thực tế là SA gia hạn TRỰC TIẾP (HTTP 201) — confirm BE nếu cần thêm flow partner-request. (CreateDealDto giờ còn yêu cầu tenantDomain / numberOfEmployee / billingCycle — đã cập nhật make_deal.)

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_017
**Ghi chú (BLOCKED):** Cần clock 90 ngày mà staging không cung cấp. Rule "re-register prospect đã thua conflict được chấp nhận sau 90 ngày (khi chưa có close)" cần một deal thua conflict có thời điểm thua ≥ 90 ngày trước; createdAt/lostAt do server gán, không backdate được, và không có test-clock/fast-forward. Vế negative ("reject re-register TRƯỚC 90 ngày") thì làm được ngay như một TC riêng. Unblock khi BE cung cấp test-clock hoặc cho backdate.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_018
**Ghi chú (DEFERRED):** Win deal (POST /v1/sa/deals/{id}/win). WinDealDto kèm thẻ thanh toán + billing + provision tenant — gọi nó có side-effect nặng (tạo tenant, có thể đụng billing). Defer để không làm bẩn staging; build khi có teardown riêng / cờ sandbox từ BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_019
**Mô tả test:** SA đánh dấu một deal đã approved là lost (POST /v1/sa/deals/{id}/lose).
**Các bước:**
1. Đăng ký deal rồi approve (tiền đề: lose cần deal đã approved).
   → Expected: deal ở trạng thái 'approved'.
2. POST /lose.
   → Expected: HTTP 201 / body statusCode 200; status thành 'lost'.
3. GET /v1/sa/deals/{id}.
   → Expected: 'lost' được lưu.
**Expected (tổng):** Deal approved chuyển sang 'lost'.
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_020
**Mô tả test:** SA lấy một deal theo id (GET /v1/sa/deals/{id}) — full record.
**Các bước:**
1. Đăng ký deal; lấy id.
2. GET /v1/sa/deals/{id}.
   → Expected: HTTP 200; record khớp (id, partnerId, dealType, status, các field prospect) và không lộ field nhạy cảm.
**Expected (tổng):** Get-by-id trả về full record đúng.
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_031
**Mô tả test:** Negative của _020 (get-by-id): id ghost / id sai bị từ chối.
**Các bước:**
1. GET /v1/sa/deals/{ghost-id-đúng-định-dạng} → 404 (not found).
2. GET /v1/sa/deals/{id-sai-định-dạng} → 400 ('Invalid id').
**Expected (tổng):** Mọi get-by-id không hợp lệ bị từ chối (4xx), không 5xx, không trả record.
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_032
**Mô tả test:** Negative của _019 (lose): target lose không hợp lệ bị từ chối.
**Các bước:**
1. lose id không tồn tại / id sai / deal không ở trạng thái approved (vd vừa registered).
   → Expected: mỗi cái 4xx ('not found' / 'Invalid id' / 'cannot transition...').
**Expected (tổng):** Mọi lose không hợp lệ bị từ chối (4xx).
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_021
**Mô tả test:** Negative của register: field thiếu/sai phải bị 400.
**Các bước:**
1. Xác minh ghost planId 'no-such-plan-qa' không tồn tại (GET sa-plans).
   → Expected: GET billing-plans/{ghost} trả 4xx (xác nhận vắng).
2. POST register với: thiếu partnerId/dealType/prospectName/prospectCountry/ACV/closeDate, dealType sai, email sai, ACV âm, date sai, ghost partnerId.
   → Expected: mỗi cái 400 + message rõ.
3. POST register với planId không tồn tại.
   → Expected: phải 4xx.
**Expected (tổng):** Mọi payload register sai bị từ chối; planId phải được validate.
**Ghi chú:** FAILED (có chủ đích) — gap: planId không tồn tại vẫn 201. sa-plans trả 400 cho nó nhưng endpoint deals không validate cross-service. Confirm BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_022
**Mô tả test:** Idempotency/trùng: CÙNG partner đăng ký CÙNG prospect lần 2 bị từ chối (không tạo deal thứ 2).
**Các bước:**
1. Một partner + một plan đã publish + một prospect identity unique; partner đăng ký deal lần đầu.
   → Expected: HTTP 201, conflictStatus 'none'.
2. CÙNG partner đăng ký LẠI CÙNG prospect (name+email).
   → Expected: HTTP 400, message '...already exists...'.
3. Kiểm tra body của response bị từ chối.
   → Expected: không có deal id thứ 2 (không deal nào được tạo).
**Expected (tổng):** Trùng cùng-partner là hard 400 reject; khác với _004 (partner KHÁC → 201 + flagged).
**Ghi chú:** PASSED — verified 2026-06-22.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_028
**Mô tả test:** Negative của approve: target không hợp lệ bị từ chối.
**Các bước:**
1. approve id không tồn tại / id sai / deal đã approved.
   → Expected: mỗi cái 4xx ('not found' / 'Invalid id' / 'cannot transition...').
**Expected (tổng):** Mọi approve không hợp lệ bị từ chối.
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_029
**Mô tả test:** Negative của resolve-conflict: input sai bị từ chối.
**Các bước:**
1. resolve-conflict với decision sai / thiếu decision / thiếu reasoning / id không tồn tại / id sai / deal không-flagged.
   → Expected: mỗi cái 4xx + message rõ ('decision must be one of' / 'reasoning...' / 'not found' / 'Invalid id' / 'not in FLAGGED conflict state').
**Expected (tổng):** Mọi resolve-conflict sai bị từ chối.
**Ghi chú:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_030
**Mô tả test:** Negative của _016 (extend-protection): input sai bị từ chối với message rõ.
**Các bước:**
1. extend-protection với: thiếu addedDays / thiếu reasoning / addedDays 0 / âm / quá max (181) / không phải số / ghost deal id (body hợp lệ) / id sai.
   → Expected: mỗi cái 400 + message rõ ('addedDays must be 1..180' / 'reasoning should not be empty' / 'must not be less than 1' / 'must not be greater than 180' / 'not found' / 'Invalid id').
**Expected (tổng):** Mọi extend-protection sai bị từ chối. BE validate body trước khi lookup deal nên các case field tự chứng minh trên ghost id (không cần deal thật).
**Ghi chú:** PASSED — verified 2026-06-25. Phát hiện constraint: addedDays ∈ 1..180; reasoning bắt buộc + non-empty.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_033
**Mô tả test:** Idempotency của _016 (extend-protection): gọi lại lần 2 là ADDITIVE (cộng dồn), không phải no-op hay cap.
**Các bước:**
1. Register deal (lưu protectionExpiresAt = exp0).
   → Expected: deal registered có protection window.
2. Extend +30 ngày.
   → Expected: exp1 == exp0 + 30d.
3. Extend +30 ngày lần nữa.
   → Expected: 200; exp2 == exp1 + 30d (cộng dồn từ expiry hiện tại); deal vẫn 'registered'.
4. GET /v1/sa/deals/{id}.
   → Expected: window lưu == exp0 + 60d.
**Expected (tổng):** extend-protection là mutating action có tham số — repeat cộng dồn theo thiết kế (không phải idempotent no-op, không cap). Mỗi lần gọi còn được ghi vào protectionExtensions[].
**Ghi chú:** PASSED — verified 2026-07-01. Probe theo rule 8 (mutating action ≠ POST-create): hành vi additive (exp0 +30 → +30 = +60). BE stamp từng lần vào protectionExtensions[] (extendedBy/at, previous/newExpiresAt, addedDays, trigger, reasoning).

### API · DEAL_APPROVAL_QUEUE

#### PARTNER_API_DEAL_APPROVAL_QUEUE_001
**Mô tả test:** SA từ chối (reject) một deal đang trong hàng đợi duyệt (POST /v1/sa/deals/{id}/reject, body reviewNotes).
**Các bước:**
1. Đăng ký deal (tiền đề: 'registered', tức đang chờ duyệt).
2. POST /reject kèm reviewNotes.
   → Expected: HTTP 201 / body statusCode 200; status thành 'rejected'.
3. GET /v1/sa/deals/{id}.
   → Expected: 'rejected' được lưu.
**Expected (tổng):** Deal registered bị reject và giữ trạng thái rejected.
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_APPROVAL_QUEUE_011
**Mô tả test:** Negative của _001 (reject): target reject không hợp lệ bị từ chối.
**Các bước:**
1. reject id không tồn tại / id sai / deal đã rejected (hoặc không phải registered).
   → Expected: mỗi cái 4xx ('not found' / 'Invalid id' / 'cannot transition...').
**Expected (tổng):** Mọi reject không hợp lệ bị từ chối (4xx).
**Ghi chú:** PASSED — verified 2026-06-30.

### API · DEAL_COLLABORATION

#### PARTNER_API_DEAL_COLLABORATION_001
**Ghi chú (BLOCKED):** Không có API collaboration/notes-thread. Deal chỉ có 1 field `notes` dạng chuỗi phẳng (đặt lúc register / cập nhật deal) — không có endpoint thread comment/activity để thêm, liệt kê hay gán người tạo. Re-scope với BE: nếu "collaboration" chỉ là field notes phẳng thì đã được cover bởi TC register/update; nếu không thì endpoint chưa tồn tại.

#### PARTNER_API_DEAL_COLLABORATION_002
**Ghi chú (BLOCKED):** Không có API document/attachment cho deal. Không có endpoint upload/list/download tài liệu deal. Build khi BE expose surface deal-documents.

### API · PIPELINE_MANAGEMENT

#### PARTNER_API_PIPELINE_MANAGEMENT_001
**Mô tả test:** Partner liệt kê deal của mình (GET /partner/portal/deals) — chỉ trả deal CỦA CHÍNH MÌNH (scoped).
**Các bước:**
1. Mint partner session; partner đăng ký 1 deal.
2. GET /partner/portal/deals.
   → Expected: HTTP 200; deal vừa đăng ký xuất hiện VÀ mọi dòng có partnerId == partner gọi (không lộ cross-partner).
**Expected (tổng):** Danh sách deal được scope đúng theo partner đã xác thực.
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_PIPELINE_MANAGEMENT_002
**Mô tả test:** Partner lọc danh sách deal theo status (GET /partner/portal/deals?status=registered).
**Các bước:**
1. Mint partner session; đăng ký deal (status 'registered').
2. GET /partner/portal/deals?status=registered.
   → Expected: HTTP 200; mọi deal trả về có status 'registered' VÀ deal vừa đăng ký nằm trong đó.
**Expected (tổng):** Filter status được áp dụng đúng.
**Ghi chú:** PASSED — verified 2026-06-30. Enum deal-status hợp lệ: registered, approved, in_progress, won, lost, expired, rejected.

#### PARTNER_API_PIPELINE_MANAGEMENT_011
**Mô tả test:** Negative của _001/_002: filter không hợp lệ / pagination quá lớn được xử lý gọn gàng.
**Các bước:**
1. GET /partner/portal/deals?status=bogus → 400 (status phải thuộc enum).
2. GET /partner/portal/deals?limit=999999 → 400 ('limit must not exceed 100').
**Expected (tổng):** Filter/pagination không hợp lệ bị từ chối (4xx), không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-30.
### API · TENANT_PROVISIONING_ATTRIBUTION

> Ghi chú: id của section này gom nhiều feature (close→provision→commission→attribution). Theo quyết định của user, tạm GIỮ NGUYÊN grouping; một số dòng thực ra thuộc co-sell / commissions / CRM.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_001
**Ghi chú (BLOCKED):** Endpoint accept/lock co-sell split POST /v1/partner/deals/:id/cosell-split-accept chưa có trong dev build. (Mis-group — thực ra là case co-sell.) Unblock khi BE ship.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_002
**Ghi chú (BLOCKED):** Phụ thuộc luồng win/close (DEAL_018, deferred) + surface provisioning & commission/event downstream không reachable. Unblock khi win chạy an toàn + các surface đó được expose.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_003
**Ghi chú (BLOCKED):** Phụ thuộc win/close + billing/invoice downstream ("reseller close → invoice trỏ về reseller"). Unblock khi có win + verify billing.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_004
**Ghi chú (BLOCKED):** Phụ thuộc win/close + tenant đã provision + billing line-items downstream. Unblock khi có expansion-close + verify billing.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_005
**Ghi chú (BLOCKED):** Engine tính commission downstream, không có API đọc commission ("expansion NN → full rate"). Cùng họ COMMISSIONS_PAYOUTS_001. Unblock khi BE expose commission đã tính.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_006
**Ghi chú (BLOCKED):** Như _005 — commission-calc downstream, không API đọc ("expansion EN → lower rate"). Unblock khi BE expose commission đã tính.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_007
**Ghi chú (BLOCKED):** Phụ thuộc luồng win (DEAL_018, deferred) + CRM connector downstream để verify "deal won → CRM closes won kèm tenant id". Unblock khi win chạy an toàn.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_008
**Ghi chú (BLOCKED):** Cần tenant đã provision (sau win) để soi field tenant.attribution — surface downstream không reachable. Unblock khi expose surface đọc tenant/attribution.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_009
**Ghi chú (BLOCKED):** Không có API override-attribution của SA với two-eye (dual) approval + history. Unblock khi BE expose endpoint override-attribution.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_010
**Ghi chú (BLOCKED):** Endpoint lock-after-accept POST /v1/partner/deals/:id/cosell-split-accept chưa có trong dev build. Cùng endpoint với _001. Unblock khi BE ship.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_011
**Ghi chú (redundant):** "Invalid expectedCloseDate → 400" đã được cover bởi DEAL_REGISTRATION_PIPELINE_021 (step 2e). Không blocked; build riêng cũng không thêm coverage.
### API · REFERRAL_ATTRIBUTION

#### PARTNER_API_REFERRAL_ATTRIBUTION_001
**Ghi chú (BLOCKED):** Endpoint referral-attribution (GET/POST /v1/partner/referral-links) không có trên spec deploy (confirmed 2026-06-30: 0 referral paths); TTL 30 ngày trong Redis còn cần clock control. Unblock khi BE ship referral-links API + test-clock.

#### PARTNER_API_REFERRAL_ATTRIBUTION_002
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_003
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_004
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

### API · CLIENT_HEALTH_MSP

> Tất cả BLOCKED — module My Clients / Client Health / MSP (`/v1/partner/clients/*`) không có trên spec deploy (confirmed 2026-06-30: sa-partners-api = 68 paths, 0 /client* paths). Unblock khi BE ship module.

#### PARTNER_API_CLIENT_HEALTH_MSP_001
**Ghi chú (BLOCKED):** GET /v1/partner/clients (My Clients — tenant sau close) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_002
**Ghi chú (BLOCKED):** GET /v1/partner/clients/:tenantId/health (usage/renewal/ticket metrics) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_003
**Ghi chú (BLOCKED):** GET /v1/partner/clients/:tenantId/tickets (không MSP consent → chỉ count + severity) chưa implement. Cặp với _004.

#### PARTNER_API_CLIENT_HEALTH_MSP_004
**Ghi chú (BLOCKED):** GET /v1/partner/clients/:tenantId/tickets (có MSP consent → full ticket content) chưa implement. Cặp với _003.

#### PARTNER_API_CLIENT_HEALTH_MSP_005
**Ghi chú (BLOCKED):** PATCH MSP consent dưới /v1/partner/clients/* (revoke → ngắt content access ngay) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_006
**Ghi chú (BLOCKED):** POST MSP tenant provision dưới /v1/partner/clients/* (tạo tenant partner_managed) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_007
**Ghi chú (BLOCKED):** MSP handoff/transfer dưới /v1/partner/clients/* (giữ history cũ + phát event) chưa implement.

#### PARTNER_API_CLIENT_HEALTH_MSP_008
**Ghi chú (BLOCKED):** MSP tier qualification (total managed ARR) dưới /v1/partner/clients/* chưa implement; cũng là calc downstream.

#### PARTNER_API_CLIENT_HEALTH_MSP_009
**Ghi chú (BLOCKED):** Audit MSP consent grant/revoke dưới /v1/partner/clients/* (event kèm actor + timestamps, đổi access tức thì) chưa implement.
### API · COMMISSIONS_PAYOUTS

> Spec (confirmed 2026-06-30): endpoint commission CÓ (/v1/sa/commissions + /approve /mark-paid /dispute /clawback, /v1/partner/portal/commissions + /summary /dispute, /v1/sa/rate-table). KHÔNG có: waiver, spiff, approve-payout, payout/banking. Đa số TC lifecycle còn cần commission record — chỉ sinh ra từ win pipeline (DEAL_018, deferred). Chỉ _002 và _006 build được ngay.

#### PARTNER_API_COMMISSIONS_PAYOUTS_001
**Ghi chú (BLOCKED):** Commission-calc downstream ("renewal EE → lowest rate"); cần win→commission pipeline (deferred) và không có API đọc rate. Unblock khi tạo được commission + đọc được rate.

#### PARTNER_API_COMMISSIONS_PAYOUTS_002
**Ghi chú (NOT_STARTED — buildable now):** GET /v1/partner/portal/commissions (ledger/history) có sẵn; assert list schema + scoping partner (pass cả khi rỗng). Build candidate kế tiếp. Khác PARTNER_PORTAL_004 (commissions/summary, PASSED).

#### PARTNER_API_COMMISSIONS_PAYOUTS_003
**Ghi chú (BLOCKED, positive):** POST /v1/partner/portal/commissions/{id}/dispute có sẵn, nhưng dispute cần commission {id} thật (deferred win pipeline). Negative (dispute ghost id → 4xx) build được ngay. Unblock khi tạo được commission record.

#### PARTNER_API_COMMISSIONS_PAYOUTS_004
**Ghi chú (BLOCKED):** Product-failure waiver POST /v1/partner/commissions/:id/waiver không có trên spec (2026-06-30). Unblock khi BE ship waiver.

#### PARTNER_API_COMMISSIONS_PAYOUTS_005
**Ghi chú (BLOCKED):** Endpoint waiver decision / final-outcome event không có (0 waiver path, 2026-06-30). Cặp với _004/_012.

#### PARTNER_API_COMMISSIONS_PAYOUTS_006
**Ghi chú (NOT_STARTED — buildable now):** Rate-table endpoint là POST /v1/sa/rate-table (TC ghi PUT /internal/commission/rates — method PUT→POST, path đổi). Tạo version mới + assert persist. Phần "cached" (Redis invalidation) là internal/không observe qua API (xem _014).

#### PARTNER_API_COMMISSIONS_PAYOUTS_007
**Ghi chú (BLOCKED):** "Approve over threshold" 2-approver cần /v1/sa/commissions/{id}/approve-payout (dual approval), không có trên spec — chỉ có POST /{id}/approve đơn. Cũng cần commission record.

#### PARTNER_API_COMMISSIONS_PAYOUTS_008
**Ghi chú (BLOCKED):** Referral-attribution endpoints không có (0 referral paths, 2026-06-30) + TTL 40 ngày cần clock. Cùng gốc REFERRAL_ATTRIBUTION_003.

#### PARTNER_API_COMMISSIONS_PAYOUTS_009
**Ghi chú (BLOCKED):** Referral-link endpoints không có (0 referral paths, 2026-06-30). "Referral-link signup → notification + commission trigger" cần referral path.

#### PARTNER_API_COMMISSIONS_PAYOUTS_010
**Ghi chú (BLOCKED):** POST /v1/sa/commissions/{id}/clawback có sẵn, nhưng clawback cần commission tồn tại (deferred win pipeline) + control timing 12 tháng.

#### PARTNER_API_COMMISSIONS_PAYOUTS_011
**Ghi chú (BLOCKED):** Cần reseller commission record + churn event (đều downstream/unavailable) để assert "reseller churn → KHÔNG clawback".

#### PARTNER_API_COMMISSIONS_PAYOUTS_012
**Ghi chú (BLOCKED):** Endpoint waiver SLA/decision + ledger-credit không có (0 waiver path, 2026-06-30). Cặp với _004/_005.

#### PARTNER_API_COMMISSIONS_PAYOUTS_013
**Ghi chú (BLOCKED):** SPIFF programme POST /internal/commission/spiff không có trên spec (0 spiff paths, 2026-06-30).

#### PARTNER_API_COMMISSIONS_PAYOUTS_014
**Ghi chú (BLOCKED):** POST /v1/sa/rate-table có (phần update), nhưng "Redis cached rates invalidated" là side-effect internal, không có API observe. Re-scope thành "update persist + phản ánh ở read kế" (trùng _006), hoặc giữ blocked cho assertion cache-invalidation.

#### PARTNER_API_COMMISSIONS_PAYOUTS_015
**Ghi chú (BLOCKED):** "Pack vs channel partner ledger tách biệt" cần commission của cả 2 loại partner (deferred win pipeline). List endpoint có; data thì không.

#### PARTNER_API_COMMISSIONS_PAYOUTS_016
**Ghi chú (BLOCKED):** "Payout banking encrypted at rest" (CSFLE) là thuộc tính lưu trữ internal, không API confirm; cũng không có endpoint payout/banking trong commissions (banking nằm ở partner.payoutAccounts). Verify qua DB/infra, không qua API.
### API · PARTNER_ACCOUNT_MANAGEMENT

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001
**Mô tả test:** Kiểm contract read-only GET /v1/sa/partners: trả 200 với envelope (statusCode/data/total/message) và đúng phân trang.
**Các bước:**
1. Auth SA. GET /v1/sa/partners?page=1&limit=5.
   → Expected: HTTP 200.
2. Assert envelope.
   → Expected: data là list, total >= 0, có message.
3. Assert phân trang.
   → Expected: số dòng trả về <= limit (5).
4. Toàn vẹn dữ liệu + SA filter (phụ thuộc data).
   → Expected: mỗi partner là object không rỗng, id duy nhất; WARN-skip nếu staging 0 partner.
5. Cô lập SA / không rò rỉ chéo.
   → Expected: chỉ phạm vi SA; WARN-skip khi không có data.
**Expected (tổng):** List partner trả envelope phân trang hợp lệ.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002
**Mô tả test:** CRUD create POST /v1/sa/partners với required name/email/type.
**Các bước:**
1. Tạo payload partner duy nhất (name/email/type=channel).
   → Expected: payload sẵn sàng.
2. POST /v1/sa/partners.
   → Expected: HTTP 201; body statusCode 200; message thành công; đăng ký cleanup.
3. Assert đã lưu.
   → Expected: có _id + code (PAR-xxxxxx) do server cấp.
4. Assert echo.
   → Expected: name/email/type lưu == gửi.
5. Assert lifecycle.
   → Expected: status == 'pending' (chờ SA kích hoạt).
6. GET /v1/sa/partners/{id}.
   → Expected: trả đúng partner, vẫn 'pending'.
**Expected (tổng):** Partner pending được tạo, lưu, truy xuất được.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003
**Mô tả test:** Chuyển trạng thái POST /v1/sa/partners/{id}/approve: pending -> active + approval event.
**Các bước:**
1. Tạo partner pending (tiền đề).
   → Expected: partner 'pending'.
2. POST /v1/sa/partners/{id}/approve.
   → Expected: HTTP 201; message thành công; đúng partner.
3. Assert chuyển + event.
   → Expected: status 'active'; có approvedAt; có approvedBy.
4. GET /v1/sa/partners/{id}.
   → Expected: status 'active' đã lưu.
**Expected (tổng):** Partner pending được duyệt thành active + metadata duyệt; tạo activation-user là event downstream (ngoài scope).
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004
**Mô tả test:** Decline/suspend partner qua POST /v1/sa/partners/{id}/deactivate; reason phải bắt buộc + ghi audit log.
**Các bước:**
1. Tạo partner pending; decline CÓ reason.
   → Expected: HTTP 201; status -> 'suspended'.
2. GET /v1/sa/audit-logs.
   → Expected: có entry ghi action decline kèm reason.
3. Bắt buộc reason: decline thiếu / rỗng / khoảng trắng.
   → Expected: đều phải 400.
**Expected (tổng):** Decline chạy + reason vào audit log; reason phải bắt buộc.
**Ghi chú:** PASSED — verified 2026-06-29. BE giờ bắt buộc reason non-empty khi decline (absent/empty/whitespace → 400). Trước là gap; BE đã fix.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005
**Mô tả test:** Đổi tier POST /v1/sa/partners/{id}/upgrade-tier phát event partner.tier.changed (tín hiệu portal/analytics refresh).
**Các bước:**
1. Tạo partner (tier mặc định 'registered').
   → Expected: tier == 'registered'.
2. upgrade-tier sang 'select' (+reason).
   → Expected: HTTP 201; tier == 'select'.
3. GET /v1/sa/audit-logs.
   → Expected: event partner.tier.changed ghi before='registered', after='select'.
4. GET /v1/sa/partners/{id}.
   → Expected: tier 'select' đã lưu.
**Expected (tổng):** Tier đổi + event được publish; portal/analytics refresh là consumer downstream (ngoài scope).
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_006
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] Searched OpenAPI specs of all 11 platform services (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 fields for reseller/end-client price (only basePrice/totalPrice in plan/billing, unrelated). No endpoint or field to send/store an end-client price → the data-model this TC describes is not implemented in any current API. Confirm with product/BE: which service owns this, or is it a future PRD feature (§2.2/§7.2/§11)? Not automatable until the model exists.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_007
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] This is a scheduled background JOB (quarterly tier recalculation), not an API endpoint. No manual-trigger endpoint exists in any service to invoke it on demand, so it cannot be exercised via API automation. Belongs to BE unit/integration tests (or needs a QA-only trigger endpoint). Note: manual tier change IS covered by _005 (POST /upgrade-tier); this TC is specifically the automated quarterly job. Confirm with BE whether a trigger endpoint can be exposed.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_008
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Depends on the quarterly tier-calculation job (_007): the "downgrade grace quarter" rule (partner keeps current-tier benefits during the grace period) is applied by that scheduled job, not a callable endpoint. No API to set the clock/quarter or trigger the grace evaluation → not API-automatable. BE unit/integration test territory. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_009
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] No endpoint or field for PSM (Partner Success Manager) allocation or ARR thresholds in any of the 11 service specs (only unrelated carryForwardPolicy in setting-api). The "$1.5M ARR → dedicated PSM" rule is a calculation not exposed via API → not automatable now. Confirm with product/BE where this logic lives (likely a job/internal calc).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010
**Mô tả test:** Cấp certification (POST /v1/sa/partner-users/{userId}/certifications) = certification earned; phát partner.certification.granted.
**Các bước:**
1. Tạo partner + invite portal user (lấy userId).
   → Expected: partner + user sẵn sàng.
2. Grant cert (sales_certified, score=95).
   → Expected: HTTP 201; status 'active'; có earnedAt + expiresAt; type echo đúng.
3. GET /v1/sa/partners/{partnerId}/certifications.
   → Expected: cert vừa cấp xuất hiện cho user.
4. GET /v1/sa/audit-logs.
   → Expected: event partner.certification.granted ghi đúng cert type.
**Expected (tổng):** Cert được earned, liệt kê, event published; tier re-eval là downstream (ngoài scope).
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011
**Mô tả test:** Negative của list: phân trang sai phải xử lý duyên dáng (không bao giờ 5xx).
**Các bước:**
1. GET list với page=0 và page=-1.
   → Expected: phải < 500 (graceful).
2. Quan sát limit=-5 / 999999 / page='abc'.
   → Expected: log lại (hiện default, không 400).
**Expected (tổng):** Input phân trang sai không được làm sập endpoint.
**Ghi chú:** PASSED — verified 2026-06-29. BE giờ trả 400 cho pagination sai (page=0/-1 → "page must not be less than 1"); không còn HTTP 500. Trước là gap; BE đã fix.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012
**Mô tả test:** Negative của create: field thiếu/sai phải bị 400 + lỗi field, không tạo record.
**Các bước:**
1. POST create với: thiếu name / thiếu email / thiếu type / email sai / name rỗng / type ngoài enum.
   → Expected: mỗi cái 400 + message field; không lưu record.
**Expected (tổng):** Mọi payload create sai bị 400.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013
**Mô tả test:** Negative của approve: target không hợp lệ bị từ chối.
**Các bước:**
1. approve id không tồn tại / id sai / partner đã active.
   → Expected: mỗi cái 4xx + message rõ ('not found' / 'Invalid id' / 'cannot be approved from status active').
**Expected (tổng):** Mọi approve không hợp lệ bị từ chối.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014
**Mô tả test:** Negative của deactivate: id sai bị từ chối; lặp thì idempotent.
**Các bước:**
1. deactivate id không tồn tại / id sai.
   → Expected: mỗi cái 4xx ('not found' / 'Invalid id').
2. deactivate lại partner đã suspended.
   → Expected: không 5xx; vẫn 'suspended' (idempotent).
**Expected (tổng):** Deactivate id sai bị từ chối; lặp lại idempotent.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015
**Mô tả test:** Negative của đổi tier: input sai bị từ chối.
**Các bước:**
1. upgrade-tier với enum sai / thiếu tier / id không tồn tại / id sai.
   → Expected: mỗi cái 4xx + message rõ.
**Expected (tổng):** Mọi đổi tier sai bị từ chối.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_016
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] Searched OpenAPI specs of all 11 platform services (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 fields for reseller/end-client price (only basePrice/totalPrice in plan/billing, unrelated). No endpoint or field to send/store an end-client price → the data-model this TC describes is not implemented in any current API. Confirm with product/BE: which service owns this, or is it a future PRD feature (§2.2/§7.2/§11)? Not automatable until the model exists.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_017
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] This is a scheduled background JOB (quarterly tier recalculation), not an API endpoint. No manual-trigger endpoint exists in any service to invoke it on demand, so it cannot be exercised via API automation. Belongs to BE unit/integration tests (or needs a QA-only trigger endpoint). Note: manual tier change IS covered by _005 (POST /upgrade-tier); this TC is specifically the automated quarterly job. Confirm with BE whether a trigger endpoint can be exposed.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_018
**Ghi chú (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Depends on the quarterly tier-calculation job (_007): the "downgrade grace quarter" rule (partner keeps current-tier benefits during the grace period) is applied by that scheduled job, not a callable endpoint. No API to set the clock/quarter or trigger the grace evaluation → not API-automatable. BE unit/integration test territory. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_019
**Ghi chú (BLOCKED):** [BLOCKED — NO API 2026-06-17] No endpoint or field for PSM (Partner Success Manager) allocation or ARR thresholds in any of the 11 service specs (only unrelated carryForwardPolicy in setting-api). The "$1.5M ARR → dedicated PSM" rule is a calculation not exposed via API → not automatable now. Confirm with product/BE where this logic lives (likely a job/internal calc).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020
**Mô tả test:** Negative của grant cert: input sai bị từ chối.
**Các bước:**
1. grant cert với certificationType sai / thiếu type / userId không tồn tại / userId sai.
   → Expected: mỗi cái 4xx + message rõ.
**Expected (tổng):** Mọi grant-cert sai bị từ chối.
**Ghi chú:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_021
**Mô tả test:** Idempotency/trùng: tạo partner cùng email lần 2 bị từ chối (không tạo account thứ 2).
**Các bước:**
1. Tạo partner với email unique.
   → Expected: HTTP 201, account được tạo.
2. Tạo lại với CÙNG email.
   → Expected: HTTP 400, message '...already exists'.
3. Kiểm tra body response bị từ chối.
   → Expected: không tạo account thứ 2.
**Expected (tổng):** Trùng email là hard 400 reject; không có partner account trùng.
**Ghi chú:** PASSED — verified 2026-06-23.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_022
**Mô tả test:** Idempotency/trùng: cấp lại cùng loại certification cho cùng user không được tạo bản trùng (renew hoặc 409).
**Các bước:**
1. Tạo partner + invite user.
   → Expected: user được tạo.
2. Grant 'sales_certified' (lần đầu).
   → Expected: cert active.
3. Grant LẠI cùng type, rồi list certifications của partner.
   → Expected: đúng 1 cert 'sales_certified' (idempotent renew) HOẶC 409 khi re-grant.
**Expected (tổng):** Re-grant không được tạo cert trùng cùng loại đang active.
**Ghi chú:** FAILED (có chủ đích) — gap: re-grant trả 201 và tạo cert active THỨ HAI (list có 2). BE nên renew hoặc reject. Confirm BE.

### API · PARTNER_USERS

#### PARTNER_API_PARTNER_USERS_001
**Mô tả test:** SA list portal user của 1 partner: GET /sa-partners-api/v1/sa/partner-users?partnerId= trả list user kèm role.
**Các bước:**
1. Tạo partner + invite 1 portal user.
   → Expected: user được tạo, có userId.
2. GET partner-users lọc theo partnerId.
   → Expected: 200, envelope {statusCode, data[], total, message}.
3. Kiểm tra user đã invite xuất hiện + scope.
   → Expected: user có role + status + email; mọi row có partnerId == partner đang query.
4. Kiểm tra không lộ field nhạy cảm.
   → Expected: không có key password/tempPassword trong list (invite có tempPassword nhưng list thì không).
**Expected (tổng):** List user scope theo partner, có role/status, không lộ credential.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_USERS_011
**Mô tả test:** Negative của _001 (list partner-users): pagination/filter sai xử lý graceful (không bao giờ 5xx).
**Các bước:**
1. Case được validate: page=0 / page=-1 (skip non-negative), limit quá max (>100), partnerId sai format.
   → Expected: mỗi cái 400 ('skip must be a non-negative integer' / 'limit must not exceed 100' / 'partnerId must be a mongodb id').
2. Ghost partnerId (hợp lệ nhưng không tồn tại).
   → Expected: 200 list rỗng.
3. Param lỏng: limit=0 / page không phải số / sort lạ.
   → Expected: không bị từ chối (default ngầm, HTTP 200) — nhưng vẫn không bao giờ 5xx.
**Expected (tổng):** Input sai được validate → 4xx; param lỏng default graceful; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Gap WEAK-VALIDATION cần confirm BE: khác audit-log list (400 các case này), limit=0 / page non-numeric / sort lạ bị default ngầm (200) thay vì từ chối.

#### PARTNER_API_PARTNER_USERS_002
**Mô tả test:** SA invite portal user: POST /sa-partners-api/v1/sa/partner-users tạo user kèm role.
**Các bước:**
1. Tạo partner; POST invite (partnerId + email + firstName + lastName + role).
   → Expected: HTTP 201, có userId.
2. Kiểm tra field được lưu.
   → Expected: partnerId/email/firstName/lastName/role echo đúng.
3. Kiểm tra user dùng được.
   → Expected: status 'active' + có tempPassword cho SA bàn giao.
4. Kiểm tra xuất hiện trong list.
   → Expected: user có trong GET partner-users?partnerId.
**Expected (tổng):** Invite tạo portal user dùng được với role đã chọn.
**Ghi chú:** PASSED — verified 2026-06-25. TC↔BE: plan nói "email sent + PENDING user" nhưng BE tạo user ACTIVE + trả tempPassword (model temp-password). Confirm BE model nào đúng. Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_USERS_012
**Mô tả test:** Negative của _002 (invite): field thiếu/sai bị 400.
**Các bước:**
1. Invite thiếu email / firstName / lastName / partnerId, role sai enum, email sai, ghost partnerId, partnerId sai format.
   → Expected: mỗi cái 400 + message rõ ('email must be an email' / 'firstName...' / 'partnerId must be a mongodb id' / 'role must be one of' / 'Partner ... not found').
**Expected (tổng):** Mọi invite sai bị 4xx. Ghost partnerId self-proving (endpoint tự báo not-found).
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_USERS_013
**Mô tả test:** Idempotency/trùng của _002: invite cùng email 2 lần không được tạo user trùng.
**Các bước:**
1. Tạo partner + invite user (email E).
   → Expected: user được tạo.
2. Invite LẠI cùng email E.
   → Expected: 409 reject HOẶC idempotent (không tạo user mới).
3. List user của partner.
   → Expected: đúng 1 user cho email E.
**Expected (tổng):** Re-invite không được tạo user trùng email (email là login identity).
**Ghi chú:** FAILED (có chủ đích) — gap: re-invite trả 201 và tạo user THỨ HAI cùng email (list có 2). BE nên reject (409) hoặc idempotent. Confirm BE.

#### PARTNER_API_PARTNER_USERS_003
**Mô tả test:** SA reset password của portal user: POST /sa-partners-api/v1/sa/partner-users/{userId}/reset-password cấp credential mới.
**Các bước:**
1. Tạo partner + invite user (lưu tempPassword lúc invite).
   → Expected: user được tạo.
2. Reset password user.
   → Expected: 200 'Password reset successfully', response tham chiếu đúng userId.
3. Credential mới được cấp.
   → Expected: tempPassword mới, khác cái lúc invite.
4. Reset lặp được.
   → Expected: reset lần 2 cũng trả 200.
**Expected (tổng):** Reset cấp credential mới và là mutating action lặp được.
**Ghi chú:** PASSED — verified 2026-06-25. TC↔BE: plan nói "gửi LINK reset" nhưng BE trả tempPassword mới (model temp-password). Confirm BE. Idempotency: reset không phải create — lặp lại là hợp lệ, nên không có TC duplicate-create.

#### PARTNER_API_PARTNER_USERS_014
**Mô tả test:** Negative của _003 (reset password): id sai bị từ chối (4xx, không bao giờ 5xx).
**Các bước:**
1. Reset với ghost userId.
   → Expected: 4xx 'User ... not found'.
2. Reset với userId sai format.
   → Expected: 4xx 'Invalid id'.
**Expected (tổng):** userId không tồn tại/sai format bị 4xx; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Self-proving (endpoint tự báo not-found). Không phụ thuộc sa-plans.
### API · TERRITORIES

#### PARTNER_API_TERRITORIES_001
**Mô tả test:** SA gán territory cho partner: POST /sa-partners-api/v1/sa/territories lưu kèm effective dates.
**Các bước:**
1. Tạo partner; assign territory (partnerId + label + countries + exclusivityType + effective dates).
   → Expected: HTTP 201, có id.
2. Kiểm tra field lưu.
   → Expected: partnerId/label/countries/exclusivityType echo; exclusivityStartDate/EndDate giữ nguyên.
3. GET by id.
   → Expected: trả đúng territory.
**Expected (tổng):** Territory lưu kèm field + effective dates, lấy được theo id.
**Ghi chú:** PASSED — verified 2026-06-25. exclusivityType ∈ exclusive/preferred/open; countries ISO 3166-1 alpha-2. Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_011
**Mô tả test:** Negative của _001 (assign): field thiếu/sai bị 400.
**Các bước:**
1. Assign thiếu partnerId/label/countries, exclusivityType sai, country code sai, date sai, ghost/malformed partnerId.
   → Expected: mỗi cái 400 + message rõ ('mongodb id' / 'label' / 'countries...ISO31661' / 'exclusivityType must be one of' / 'ISO 8601' / 'Partner ... not found').
**Expected (tổng):** Mọi assign sai bị 4xx. Ghost partnerId self-proving.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_012
**Mô tả test:** Exclusive territory conflict: partner thứ 2 không được lấy country đã có partner khác giữ exclusive.
**Các bước:**
1. Hai partner; partner 1 lấy territory EXCLUSIVE trên 1 country.
   → Expected: 201.
2. Partner 2 assign EXCLUSIVE cùng country đó.
   → Expected: 4xx 'Exclusive territory conflict'.
3. Kiểm tra response bị từ chối.
   → Expected: không tạo territory cho partner 2.
**Expected (tổng):** Overlap exclusive cross-partner bị từ chối; same-partner overlap cho phép by design.
**Ghi chú:** PASSED — verified 2026-06-25. Đây là counterpart duplicate/conflict của _001 (BE enforce exclusive cross-partner conflict). Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_002
**Mô tả test:** SA list territories có filter: GET /sa-partners-api/v1/sa/territories (phân trang, scope, lọc được).
**Các bước:**
1. Tạo partner + assign territory; GET territories?partnerId.
   → Expected: 200, envelope {statusCode, data[], total} (không có field message).
2. Territory xuất hiện, scope, schema.
   → Expected: có label/countries/exclusivityType; mọi row partnerId == partner query.
3. Filter exclusivityType.
   → Expected: chỉ row khớp.
**Expected (tổng):** List territory scope theo partner, đúng schema, lọc được.
**Ghi chú:** PASSED — verified 2026-06-25. Envelope list territory không có field `message` (khác list khác). Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_013
**Mô tả test:** Negative của _002 (list): filter/pagination sai bị 4xx (không bao giờ 5xx).
**Các bước:**
1. List với exclusivityType sai / country sai / limit>max / page=0 / malformed partnerId.
   → Expected: mỗi cái 400 (endpoint validate chặt — không default ngầm).
**Expected (tổng):** Mọi filter/pagination sai bị 4xx; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_003
**Mô tả test:** SA lấy 1 territory theo id: GET /sa-partners-api/v1/sa/territories/{id}.
**Các bước:**
1. Tạo partner + assign territory; GET by id.
   → Expected: 200, id khớp; partnerId/label/countries/exclusivityType có.
**Expected (tổng):** Get-by-id trả full territory.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_014
**Mô tả test:** Negative của _003 (get by id): id sai bị 4xx.
**Các bước:**
1. GET với ghost id / malformed id.
   → Expected: 4xx ('Territory ... not found' / 'Invalid id').
**Expected (tổng):** id không tồn tại/sai format bị 4xx; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_004
**Mô tả test:** SA xóa territory assignment: DELETE /sa-partners-api/v1/sa/territories/{id}.
**Các bước:**
1. Tạo partner + assign territory; DELETE.
   → Expected: 200 'Territory removed successfully'.
2. GET territory theo id.
   → Expected: 4xx not-found (không lấy được nữa).
**Expected (tổng):** Delete xóa territory; không retrievable nữa.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_TERRITORIES_015
**Mô tả test:** Negative của _004 (delete): id sai/đã xóa bị 4xx.
**Các bước:**
1. DELETE với ghost id / malformed id / territory đã xóa.
   → Expected: mỗi cái 4xx ('Territory ... not found' / 'Invalid id').
**Expected (tổng):** Mọi delete sai/illegal bị 4xx. (Already-removed ghi nhận repeat behavior; mutating action, không phải duplicate-create.)
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.
### API · CERTIFICATIONS_SA

#### PARTNER_API_CERTIFICATIONS_SA_001
**Ghi chú (CROSS-REF):** Grant certification đã được cover bởi PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010 (cert earned: granted + listed + event + tier re-eval), kèm _020 (grant invalid) và _022 (re-grant idempotency, fail-by-design). Không làm lại để tránh trùng. Nếu cần CERTIFICATIONS_SA_001 độc lập thì trỏ về cùng endpoint POST /v1/sa/partner-users/{userId}/certifications.

#### PARTNER_API_CERTIFICATIONS_SA_002
**Mô tả test:** SA revoke certification: DELETE /sa-partners-api/v1/sa/partner-users/{userId}/certifications/{type} (body reason) soft-revoke.
**Các bước:**
1. Tạo partner + invite user + grant cert sales_certified active.
   → Expected: cert active.
2. Revoke cert kèm reason.
   → Expected: 200 'Certification revoked successfully', status='revoked'.
3. List certifications của partner.
   → Expected: cert vẫn còn với status='revoked' (soft-revoke).
**Expected (tổng):** Revoke soft-remove cert (status='revoked'), vẫn trong list.
**Ghi chú:** PASSED — verified 2026-06-25. TC↔BE: plan nói "certification removed", BE soft-revoke (status='revoked', giữ record) — confirm BE. Không phụ thuộc sa-plans.

#### PARTNER_API_CERTIFICATIONS_SA_012
**Mô tả test:** Negative của _002 (revoke): input/state sai bị 4xx.
**Các bước:**
1. Revoke với: thiếu reason / cert không có / ghost userId / malformed userId / cert đã revoked.
   → Expected: mỗi cái 400 ('reason should not be empty' / 'Active ... not found' / 'User ... not found' / 'Invalid id').
**Expected (tổng):** Mọi revoke sai/illegal bị 4xx. (Already-revoked cũng ghi nhận repeat behavior; mutating action, không phải duplicate-create.)
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_CERTIFICATIONS_SA_003
**Mô tả test:** SA list certifications của team partner: GET /sa-partners-api/v1/sa/partners/{partnerId}/certifications.
**Các bước:**
1. Tạo partner + invite user + grant cert sales_certified.
   → Expected: cert active.
2. GET partner certifications.
   → Expected: 200, envelope {statusCode, data[], total, message}.
3. Kiểm tra cert + schema + scope.
   → Expected: cert có certificationType/status/userId/earnedAt/expiresAt; mọi row partnerId == partner query.
4. Filter status=active.
   → Expected: chỉ trả cert active.
**Expected (tổng):** List cert scope theo partner, đúng schema, lọc được.
**Ghi chú:** PASSED — verified 2026-06-25. Filter: status ∈ active/expired/revoked; certificationType enum; expiringWithinDays. Không phụ thuộc sa-plans.

#### PARTNER_API_CERTIFICATIONS_SA_013
**Mô tả test:** Negative của _003 (list cert theo partner): filter/pagination sai xử lý graceful (không bao giờ 5xx).
**Các bước:**
1. status / certificationType ngoài enum, limit quá max (>100).
   → Expected: mỗi cái 400 ('must be one of' / 'limit must not exceed 100').
2. Malformed partnerId.
   → Expected: 400 'Invalid id'.
3. Ghost partnerId.
   → Expected: 200 list rỗng.
4. page=0.
   → Expected: xử lý graceful (4xx hoặc default), không bao giờ 5xx.
**Expected (tổng):** Filter/pagination sai → 4xx; ghost partner → 200 rỗng; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_CERTIFICATIONS_SA_004
**Mô tả test:** SA list certifications sắp hết hạn: GET /sa-partners-api/v1/sa/certifications?expiringWithinDays=N.
**Các bước:**
1. GET /sa/certifications?expiringWithinDays=30.
   → Expected: 200, envelope {statusCode, data[], total, message}; mọi cert trả về hết hạn trong 30 ngày (rỗng cũng chấp nhận).
2. Boundary max expiringWithinDays (365).
   → Expected: 200 (chấp nhận).
**Expected (tổng):** List expiring trả envelope đúng; expiringWithinDays bound 1..365.
**Ghi chú:** PASSED — verified 2026-06-25. Confirm BE: SA-wide list trả total=0 dù có cert active (thấy được qua per-partner list _003) — có thể scoping/index khác. Filter semantic assert trên dữ liệu trả về; rỗng thì log, không fail. Không phụ thuộc sa-plans.

#### PARTNER_API_CERTIFICATIONS_SA_014
**Mô tả test:** Negative của _004 (SA cert list): filter/pagination sai bị 4xx (không bao giờ 5xx).
**Các bước:**
1. status / certificationType ngoài enum; expiringWithinDays ngoài range (0 / âm / >365); limit quá max; page=0.
   → Expected: mỗi cái 400 ('must be one of' / 'expiringWithinDays must not be less than 1' / 'must not be greater than 365' / 'limit must not exceed 100' / 'skip must be a non-negative integer').
**Expected (tổng):** Mọi filter/pagination sai bị 4xx; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. expiringWithinDays bound 1..365. Không phụ thuộc sa-plans.
### API · TEAM_REFERRAL_LINKS

#### PARTNER_API_TEAM_REFERRAL_LINKS_001
**Ghi chú (BLOCKED):** Referral endpoints không có trên spec deploy (confirmed 2026-06-30: 0 referral paths). GET /v1/partner/referral-links chưa implement. Unblock khi BE ship referral-links API.

#### PARTNER_API_TEAM_REFERRAL_LINKS_002
**Ghi chú (BLOCKED):** Referral endpoints không có (0 referral paths, 2026-06-30). POST /v1/partner/referral-links (tạo campaign tracking link) chưa implement.

### API · RESOURCES_SANDBOX

#### PARTNER_API_RESOURCES_SANDBOX_001
**Ghi chú (BLOCKED):** Sandbox endpoints không có trên spec deploy (confirmed 2026-06-30: 0 sandbox paths). Không có API để request sandbox reset / apply profile. Unblock khi BE ship module sandbox.

#### PARTNER_API_RESOURCES_SANDBOX_002
**Ghi chú (BLOCKED):** Sandbox endpoints không có (0 sandbox paths, 2026-06-30); còn là CRON (weekly auto-reset, default off). Không có API trigger/observe. Unblock khi BE ship sandbox + job trigger.

#### PARTNER_API_RESOURCES_SANDBOX_003
**Ghi chú (BLOCKED):** Sandbox endpoints không có (0 sandbox paths, 2026-06-30). Không có API reseed profile (SMB/Mid-market/Enterprise) hay assert hoàn tất ≤5 phút.
### API · DASHBOARD_DATA

#### PARTNER_API_DASHBOARD_DATA_001
**Mô tả test:** Partner dashboard stats: GET /sa-partners-api/v1/partner/portal/dashboard trả KPI schema (partner JWT).
**Các bước:**
1. Mint partner-portal session (SA tạo + approve partner, invite user, login user → partner JWT).
   → Expected: session auth partner.
2. GET partner dashboard.
   → Expected: HTTP 200, envelope {statusCode, data{}, message}.
3. Kiểm tra KPI schema + không lộ field nhạy cảm.
   → Expected: data có section 'partner' (tier/status/openDealsCount), 'deals', 'commissions'; không key password/token/secret.
**Expected (tổng):** Dashboard trả KPI schema đúng, không lộ credential.
**Ghi chú:** PASSED — verified 2026-06-25. Endpoint PARTNER-PORTAL (cần partner JWT, không phải SA token; SA token → 401). Session mint self-contained từ phía SA. Không có negative input (không param; 401 auth thuộc Auth & Access Control). Không phụ thuộc sa-plans.
### API · CRM_INTEGRATION

> Tất cả BLOCKED — downstream CRM connector (event do service connectors/CRM consume, không reachable từ domain này). Event quan sát được qua API đã cover ở DEAL_010 / AUDIT_LOG_*; tác động phía CRM ngoài scope. Unblock khi expose verify CRM cho QA.

#### PARTNER_API_CRM_INTEGRATION_001
**Ghi chú (BLOCKED):** "Deal registered → tạo CRM opportunity (dogfood)." Phía CRM không reachable.

#### PARTNER_API_CRM_INTEGRATION_002
**Ghi chú (BLOCKED):** "Deal protection extended → cập nhật meta CRM opportunity." Phía CRM không reachable.

#### PARTNER_API_CRM_INTEGRATION_003
**Ghi chú (BLOCKED):** "Deal lost → CRM Close Lost + close reason." Phía CRM không reachable.

#### PARTNER_API_CRM_INTEGRATION_004
**Ghi chú (BLOCKED):** "Deal expired → CRM mark stale + SA task." Phụ thuộc expiry CRON + CRM connector, đều không reachable.

#### PARTNER_API_CRM_INTEGRATION_005
**Ghi chú (BLOCKED):** "client.health_alert → CRM task." Phụ thuộc module MSP/client-health (cũng absent) + CRM connector.

### API · EVENT_ARCHITECTURE

#### PARTNER_API_EVENT_ARCHITECTURE_001
**Ghi chú (BLOCKED):** Kafka envelope/metadata là thuộc tính event-bus internal, không có API để inspect trực tiếp. Sự hiện diện của event quan sát gián tiếp qua audit log (DEAL_010 / AUDIT_LOG_*), nhưng assertion "Kafka standard envelope" thì không verify được qua API. Re-scope sang audit-log envelope, hoặc verify qua BE/infra.
### API · PARTNER_PORTAL

> Mọi endpoint partner-portal cần PARTNER JWT (không phải SA token). Session mint
> self-contained từ phía SA qua `utils.partner_portal.mint_partner_session` (create +
> approve partner, invite user, partner login). Tất cả read endpoint là GET (read-only
> → idempotency N/A). Không phụ thuộc sa-plans trừ _002 (deal detail).

#### PARTNER_API_PARTNER_PORTAL_001
**Mô tả test:** Partner lấy profile account của mình: GET /partner/portal/profile.
**Các bước:**
1. Mint session; GET own profile.
   → Expected: 200; data là account của partner đang login (code/email/tier/status); không key nhạy cảm.
**Expected (tổng):** Trả profile của chính mình, không lộ credential.
**Ghi chú:** PASSED — verified 2026-06-25. Không param (no input-negative; 401 → Auth feature). Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_PORTAL_002
**Mô tả:** Partner lấy deal của chính mình theo id: GET /partner/portal/deals/{id} — full record.
**Các bước:**
1. Mint partner session; partner đăng ký deal qua /partner/portal/deals; lấy id.
2. GET /partner/portal/deals/{id}.
   → Expected: 200; record khớp (id, partnerId == của mình) và không lộ field nhạy cảm.
**Expected (tổng):** Partner đọc được full record deal của chính mình.
**Ghi chú:** PASSED — verified 2026-06-30 (sa-plans UP lại). Negative ở _012.

#### PARTNER_API_PARTNER_PORTAL_012
**Mô tả:** Negative của _002 (own deal by id): id ghost / id sai bị từ chối.
**Các bước:**
1. Mint session; GET /partner/portal/deals/{ghost-id-đúng-định-dạng} → 404 (not found).
2. GET /partner/portal/deals/{id-sai-định-dạng} → 400 ('Invalid id').
**Expected (tổng):** Mọi deal-detail không hợp lệ bị từ chối (4xx), không 5xx, không trả record.
**Ghi chú:** PASSED — verified 2026-06-30.

#### PARTNER_API_PARTNER_PORTAL_003
**Mô tả test:** Partner lấy certifications của mình: GET /partner/portal/certifications.
**Các bước:**
1. Mint session; SA grant cert cho partner user; GET own certs.
   → Expected: 200, list; cert được grant xuất hiện kèm status + earnedAt/expiresAt.
**Expected (tổng):** List cert của mình đúng schema.
**Ghi chú:** PASSED — verified 2026-06-25. Negative (filter sai) ở _013. Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_PORTAL_013
**Mô tả test:** Negative của _003 (own certs): filter sai bị 4xx (không bao giờ 5xx).
**Các bước:**
1. GET own certs với status / certificationType sai enum, limit quá max.
   → Expected: mỗi cái 400 ('must be one of' / 'must not exceed').
**Expected (tổng):** Filter cert sai bị 4xx; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_PORTAL_004
**Mô tả test:** Partner lấy commission summary của mình: GET /partner/portal/commissions/summary.
**Các bước:**
1. Mint session; GET commission summary.
   → Expected: 200; totalEarnedCents/totalPendingCents/totalPaidCents là int ≥0 (+ clawbackExposureCents).
**Expected (tổng):** Trả tổng earned/pending/paid.
**Ghi chú:** PASSED — verified 2026-06-25. Không param (no input-negative). Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_PORTAL_005
**Mô tả test:** Partner lấy territories được assign của mình: GET /partner/portal/territories.
**Các bước:**
1. Mint session; SA assign territory cho partner; GET own territories.
   → Expected: 200, list; territory được assign xuất hiện, scope theo partner.
**Expected (tổng):** Trả territories của mình, scope đúng.
**Ghi chú:** PASSED — verified 2026-06-25. Không param (no input-negative). Không phụ thuộc sa-plans.

#### PARTNER_API_PARTNER_PORTAL_006
**Mô tả test:** Partner lấy tier commission rates của mình: GET /partner/portal/rates.
**Các bước:**
1. Mint session; GET own rates.
   → Expected: 200, list tier rates đúng dạng (có thể rỗng cho registered tier).
**Expected (tổng):** Trả tier rates dạng list.
**Ghi chú:** PASSED — verified 2026-06-25. Rates rỗng cho registered-tier trên staging (list đúng dạng). Không param. Không phụ thuộc sa-plans.
### API · SECURITY_COMPLIANCE

#### PARTNER_API_SECURITY_COMPLIANCE_001
**Ghi chú (NOT_STARTED — buildable):** Audit-log endpoints có sẵn: thực hiện 1 SA action (approve/deactivate) rồi GET /v1/sa/audit-logs và assert entry có actor + action + reasoning + correlationId. Một phần đã cover ở DEAL_010 / ACCOUNT_MANAGEMENT_004; TC envelope-completeness riêng thì build được.

#### PARTNER_API_SECURITY_COMPLIANCE_002
**Ghi chú (BLOCKED):** Không có API/rule để assert data-minimization prospect (PII thừa bị reject / không lưu). Không endpoint nào enforce/expose rule PII-minimization để test. Confirm BE chỗ nào enforce.

#### PARTNER_API_SECURITY_COMPLIANCE_003
**Ghi chú (BLOCKED):** Data residency (lưu vùng UAE) là thuộc tính infra/region, không có API confirm nơi lưu. Verify qua infra/DB, không qua API.
### API · AUDIT_LOG

#### PARTNER_API_AUDIT_LOG_001
**Mô tả test:** SA list audit log: GET /sa-partners-api/v1/sa/audit-logs trả về audit trail có phân trang, lọc được, đúng schema.
**Các bước:**
1. GET audit-logs (page=1, limit=5).
   → Expected: HTTP 200, envelope {statusCode, data[], total, message}.
2. Kiểm tra phân trang.
   → Expected: số entry trả về ≤ limit.
3. Kiểm tra schema từng entry + không lộ field nhạy cảm.
   → Expected: id/action/category/severity/createdAt có + đúng type; actor/resource là object; không có key password/token/secret.
4. Lọc theo category (lấy từ entry đầu).
   → Expected: chỉ trả về entry đúng category đó.
**Expected (tổng):** List audit-log trả envelope đúng, phân trang + lọc được, entry well-formed, không nhạy cảm.
**Ghi chú:** PASSED — verified 2026-06-25. Read-only (không setup/cleanup, không phụ thuộc sa-plans).

#### PARTNER_API_AUDIT_LOG_002
**Mô tả test:** SA lấy KPI stats audit-log: GET /sa-partners-api/v1/sa/audit-logs/stats trả counter 24h + chain integrity.
**Các bước:**
1. GET audit-logs/stats.
   → Expected: HTTP 200, envelope {statusCode, data{}, message}.
2. Kiểm tra field KPI + type.
   → Expected: totalEvents24h/criticalEvents24h/warnings24h/uniqueActors24h là int ≥0; chainIntegrityPct là % 0..100.
3. Kiểm tra tính nhất quán.
   → Expected: critical/warnings/uniqueActors không vượt totalEvents24h.
**Expected (tổng):** Stats trả KPI 24h đúng type, nhất quán nội bộ.
**Ghi chú:** PASSED — verified 2026-06-25. Read-only, không param (nên không có negative input), không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_003
**Mô tả test:** SA export audit log dạng JSON hoặc CSV: GET /sa-partners-api/v1/sa/audit-logs/export trả file tải về (cap 10000 dòng).
**Các bước:**
1. Export format=json.
   → Expected: 200, content-type application/json, body là JSON array; ≤10000 dòng; mỗi dòng có _id/action/category/severity/createdAt.
2. Export format=csv.
   → Expected: 200, content-type text/csv, dòng header có các cột audit.
3. Không truyền format.
   → Expected: 200, mặc định CSV.
**Expected (tổng):** Export trả file JSON/CSV đúng định dạng (mặc định CSV), trong giới hạn 10000 dòng.
**Ghi chú:** PASSED — verified 2026-06-25. format enum [csv, json], default csv. Không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_004
**Mô tả test:** SA lấy 1 audit-log entry theo id: GET /sa-partners-api/v1/sa/audit-logs/{id} trả full entry.
**Các bước:**
1. List limit=1 để lấy id thật.
   → Expected: có entry với _id (skip nếu log rỗng).
2. GET audit-logs/{id}.
   → Expected: 200; data._id khớp; action/category/severity/createdAt có; actor/resource là object; không key nhạy cảm.
**Expected (tổng):** Get-by-id trả full entry đúng schema, không lộ field nhạy cảm.
**Ghi chú:** PASSED — verified 2026-06-25. Read-only, không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_007
**Mô tả test:** Negative của _004 (get audit entry theo id): id sai bị từ chối (4xx, không bao giờ 5xx).
**Các bước:**
1. GET audit-logs/{ghost id}.
   → Expected: 404 'Audit log entry ... not found'.
2. GET audit-logs/{malformed id}.
   → Expected: 400 'Invalid id'.
**Expected (tổng):** id không tồn tại → 404, id sai format → 400; không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-06-25. Self-proving (endpoint tự báo not-found), không cần setup, không phụ thuộc sa-plans.

#### PARTNER_API_AUDIT_LOG_005
**Mô tả test:** Negative của _001 (audit-log list): pagination / filter sai bị từ chối graceful (4xx, không bao giờ 5xx).
**Các bước:**
1. List với pagination sai: page=0 / page=-1 / limit=0 / limit=-5 / limit quá max (999999) / page không phải số.
   → Expected: mỗi cái 400 ('page/limit must not be less than 1', 'must not be greater than 100', 'must be an integer').
2. List với filter sai: severity / category / actorType ngoài enum, dateFrom / dateTo sai format.
   → Expected: mỗi cái 400 ('must be one of ...', 'must be a valid ISO 8601 date string').
3. List với range hợp lệ nhưng rỗng (dateFrom > dateTo).
   → Expected: xử lý graceful (200, list rỗng — không 5xx).
**Expected (tổng):** Mọi pagination/filter sai bị 4xx (không bao giờ 5xx); range rỗng hợp lệ trả 200 empty.
**Ghi chú:** PASSED — verified 2026-06-25. BE validate hết param (không phụ thuộc sa-plans). Enum: severity ∈ info/warning/critical; category ∈ SA_AUDIT_*; actorType ∈ sa-staff/impersonation/…

#### PARTNER_API_AUDIT_LOG_006
**Mô tả test:** Negative của _003 (audit-log export): format/filter sai bị từ chối (4xx, không bao giờ 5xx).
**Các bước:**
1. Export với format=bogus (ngoài enum).
   → Expected: 400 'format must be one of'.
2. Export với severity / category / actorType / retentionClass sai.
   → Expected: mỗi cái 400 'must be one of ...'.
3. Export với dateFrom / dateTo sai format.
   → Expected: mỗi cái 400 'must be a valid ISO 8601 date string'.
**Expected (tổng):** Mọi format/filter export sai bị 4xx (không bao giờ 5xx).
**Ghi chú:** PASSED — verified 2026-06-25. Không phụ thuộc sa-plans. retentionClass enum ∈ standard/extended/permanent.
