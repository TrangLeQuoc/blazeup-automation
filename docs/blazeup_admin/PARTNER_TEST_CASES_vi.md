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

- PARTNER_API_AUTH_ACCESS_CONTROL_001
- PARTNER_API_AUTH_ACCESS_CONTROL_002
- PARTNER_API_AUTH_ACCESS_CONTROL_003
- PARTNER_API_AUTH_ACCESS_CONTROL_004
- PARTNER_API_AUTH_ACCESS_CONTROL_005
- PARTNER_API_AUTH_ACCESS_CONTROL_006
- PARTNER_API_AUTH_ACCESS_CONTROL_007
- PARTNER_API_AUTH_ACCESS_CONTROL_008
- PARTNER_API_AUTH_ACCESS_CONTROL_009
### API · DEAL_REGISTRATION

- PARTNER_API_DEAL_REGISTRATION_001
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
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals | Default partner/BlazeUp quota credit split.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_012
**Ghi chú (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals | Threshold is above $100K ACV.

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

- PARTNER_API_DEAL_REGISTRATION_PIPELINE_014
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_015
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_016
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_017
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_018
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_019
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_020
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

### API · DEAL_APPROVAL_QUEUE

- PARTNER_API_DEAL_APPROVAL_QUEUE_001
### API · DEAL_COLLABORATION

- PARTNER_API_DEAL_COLLABORATION_001
- PARTNER_API_DEAL_COLLABORATION_002
### API · PIPELINE_MANAGEMENT

- PARTNER_API_PIPELINE_MANAGEMENT_001
- PARTNER_API_PIPELINE_MANAGEMENT_002
### API · TENANT_PROVISIONING_ATTRIBUTION

- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_001
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_002
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_003
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_004
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_005
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_006
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_007
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_008
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_009
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_010
- PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_011
### API · REFERRAL_ATTRIBUTION

- PARTNER_API_REFERRAL_ATTRIBUTION_001
#### PARTNER_API_REFERRAL_ATTRIBUTION_002
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_003
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_004
**Ghi chú (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

### API · CLIENT_HEALTH_MSP

- PARTNER_API_CLIENT_HEALTH_MSP_001
- PARTNER_API_CLIENT_HEALTH_MSP_002
- PARTNER_API_CLIENT_HEALTH_MSP_003
- PARTNER_API_CLIENT_HEALTH_MSP_004
- PARTNER_API_CLIENT_HEALTH_MSP_005
- PARTNER_API_CLIENT_HEALTH_MSP_006
- PARTNER_API_CLIENT_HEALTH_MSP_007
- PARTNER_API_CLIENT_HEALTH_MSP_008
- PARTNER_API_CLIENT_HEALTH_MSP_009
### API · COMMISSIONS_PAYOUTS

- PARTNER_API_COMMISSIONS_PAYOUTS_001
- PARTNER_API_COMMISSIONS_PAYOUTS_002
- PARTNER_API_COMMISSIONS_PAYOUTS_004
- PARTNER_API_COMMISSIONS_PAYOUTS_005
- PARTNER_API_COMMISSIONS_PAYOUTS_006
- PARTNER_API_COMMISSIONS_PAYOUTS_007
- PARTNER_API_COMMISSIONS_PAYOUTS_008
- PARTNER_API_COMMISSIONS_PAYOUTS_009
- PARTNER_API_COMMISSIONS_PAYOUTS_010
- PARTNER_API_COMMISSIONS_PAYOUTS_011
- PARTNER_API_COMMISSIONS_PAYOUTS_012
- PARTNER_API_COMMISSIONS_PAYOUTS_013
- PARTNER_API_COMMISSIONS_PAYOUTS_014
- PARTNER_API_COMMISSIONS_PAYOUTS_015
- PARTNER_API_COMMISSIONS_PAYOUTS_016
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
**Ghi chú:** FAILED (có chủ đích) — gap: API nhận decline KHÔNG reason vẫn 201. Confirm BE: reason có nên bắt buộc.

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
**Ghi chú:** FAILED (có chủ đích) — BUG: page=0 và page=-1 trả HTTP 500. Confirm BE (phải 400).

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

### API · PARTNER_USERS

- PARTNER_API_PARTNER_USERS_001
- PARTNER_API_PARTNER_USERS_002
- PARTNER_API_PARTNER_USERS_003
### API · TERRITORIES

- PARTNER_API_TERRITORIES_001
- PARTNER_API_TERRITORIES_002
- PARTNER_API_TERRITORIES_003
- PARTNER_API_TERRITORIES_004
### API · CERTIFICATIONS_SA

- PARTNER_API_CERTIFICATIONS_SA_001
- PARTNER_API_CERTIFICATIONS_SA_002
- PARTNER_API_CERTIFICATIONS_SA_003
- PARTNER_API_CERTIFICATIONS_SA_004
### API · TEAM_REFERRAL_LINKS

- PARTNER_API_TEAM_REFERRAL_LINKS_001
- PARTNER_API_TEAM_REFERRAL_LINKS_002
### API · RESOURCES_SANDBOX

- PARTNER_API_RESOURCES_SANDBOX_001
- PARTNER_API_RESOURCES_SANDBOX_002
- PARTNER_API_RESOURCES_SANDBOX_003
### API · DASHBOARD_DATA

- PARTNER_API_DASHBOARD_DATA_001
### API · CRM_INTEGRATION

- PARTNER_API_CRM_INTEGRATION_001
- PARTNER_API_CRM_INTEGRATION_002
- PARTNER_API_CRM_INTEGRATION_003
- PARTNER_API_CRM_INTEGRATION_004
- PARTNER_API_CRM_INTEGRATION_005
### API · EVENT_ARCHITECTURE

- PARTNER_API_EVENT_ARCHITECTURE_001
### API · PARTNER_PORTAL

- PARTNER_API_PARTNER_PORTAL_001
- PARTNER_API_PARTNER_PORTAL_002
- PARTNER_API_PARTNER_PORTAL_003
- PARTNER_API_PARTNER_PORTAL_004
- PARTNER_API_PARTNER_PORTAL_005
- PARTNER_API_PARTNER_PORTAL_006
### API · SECURITY_COMPLIANCE

- PARTNER_API_SECURITY_COMPLIANCE_001
- PARTNER_API_SECURITY_COMPLIANCE_002
- PARTNER_API_SECURITY_COMPLIANCE_003
### API · AUDIT_LOG

- PARTNER_API_AUDIT_LOG_001
- PARTNER_API_AUDIT_LOG_002
- PARTNER_API_AUDIT_LOG_003
- PARTNER_API_AUDIT_LOG_004
