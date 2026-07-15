# Partner Platform — Tổng hợp Kịch bản Cần Kiểm tra (theo Workflow)

> **Nguồn gốc:** `partner-platform-prd-v1.8.md`
> **Mục đích:** Tóm tắt từng scenario trong PRD thành các kịch bản kiểm tra (workflow), để hiểu rõ *cần check những gì* trước khi viết/chạy test case.
> **Cách đọc:** Mỗi kịch bản gồm **Mục đích** → **Luồng (workflow)** → **Điểm cần check (assertions)** → **Tham chiếu PRD**.
> **Ký hiệu trạng thái test:** ✅ chạy được · ⚠️ chờ BE / blocked · 🔗 thuộc module khác (ngoài PRD partner)

---

## 0. Bản đồ phạm vi (đọc trước)

| Khối | PRD | Thuộc test plan partner? |
|---|---|---|
| Partner Portal (`partner.blazeup.ai`) | §4 | ✅ Có |
| SA Partner Module (admin) | §5 | ✅ Có |
| CRM Integration (dogfood) | §6 | ⚠️ Downstream |
| Tenant Provisioning | §7 | ⚠️ Trigger + attribution (không phải "tạo tenant") |
| **Tạo tenant trần trụi** (`POST /sa-tenants-api/tenants`) | — (chỉ tham chiếu B2) | 🔗 **Module Tenant Creation khác** |

> **Lưu ý quan trọng:** PRD partner **không** đặc tả chức năng "add tenant". Tenant chỉ được *provision như hệ quả của deal close* bằng cách gọi sang `SA /internal/tenants/provision` (§7.1, §7.3). "Tạo tenant" là của `tenant-creation-module-spec-v1.1.md`.

### 0.1 Chú giải Vị trí (dùng cho dòng 📍)

| Ký hiệu | Domain | Host staging (thực tế) | PRD gọi là |
|---|---|---|---|
| 🟦 **Partner** | Partner portal | **`https://stgpartners.blazeup.ai`** | `partner.blazeup.ai` (§4.2) |
| 🟥 **SA** | SuperAdmin | **`https://stgsa.blazeup.ai`** | `blazeup-hostapp-superadmin` (§5) |
| ⚙️ **Backend** | Service/cron/event | (không có UI) | guard, engine, Kafka |
| 🔗 **Module khác** | Ngoài PRD partner | — | CRM dogfood / Tenant Creation / Marketplace |

> **Lưu ý:** Host là staging thật; **route** dưới đây lấy từ PRD (§4.2 / §5) — cần đối chiếu lại với UI thật khi test (một số route có thể khác, vd SA partner module có thể ở `stgsa.blazeup.ai/partners` hoặc dưới menu khác).

**Route 🟦 Partner (`stgpartners.blazeup.ai`, §4.2):** `/` Home · `/deals` Pipeline · `/deals/register` · `/deals/:id` · `/clients` · `/clients/:id` · `/commissions` · `/training` · `/resources` · `/team` · `/settings` · `/support`
**Khu 🟥 SA (`stgsa.blazeup.ai`, §5 — partner module tại `/partners`):** Directory (§5.1) · Deal Management/Approval Queue (§5.2) · Commission Config (§5.3) · Territory (§5.4) · Analytics (§5.5) · Commission Ledger (§5.6)

---

## 1. Onboarding & Phê duyệt Partner

### 1.1 Đăng ký partner mới + FSM duyệt 3 bước
- 📍 **Vị trí:** 🟦 Partner nộp đơn ở form đăng ký (onboarding) · 🟥 SA duyệt ở `/partners → tab "Pending Approval" → Partner Application Review` (§5.1)
- **Mục đích:** Partner nộp đơn → SA duyệt theo quy trình 3 giai đoạn (B3).
- **Luồng:**
  1. Partner nộp đơn (company, contact, regions, **primary type**).
  2. **Stage 1 — SA Review:** SA xem đơn; **phải đính kèm signed agreement** mới được advance. Thiếu → SA bấm "Request agreement" (notify applicant).
  3. **Stage 2 — Legal Countersign:** Legal ký đối ứng trong SA portal. SA **không** qua bước 3 được nếu chưa có Legal countersign.
  4. **Stage 3 — SA Final Approval:** SA Approve → emit `blazeup.partner.approved`.
- **Điểm cần check:**
  - [ ] UI review hiển thị **cả 3 stage dạng FSM**, không phải 1 nút Approve/Decline.
  - [ ] Không thể skip stage (chưa có agreement → chặn; chưa Legal countersign → chặn final).
  - [ ] Decline ở bất kỳ stage nào → **bắt buộc lý do** + ghi audit trail.
  - [ ] Approve → emit event `blazeup.partner.approved`.
- **PRD:** §5.1, B3 (d.1141)

### 1.2 Tạo first-admin của partner (B2)
- 📍 **Vị trí:** 🟥 SA bấm Approve tại `/partners → Application Review` · 🟦 Partner nhận email activation → tự đặt mật khẩu qua link (§5.1)
- **Mục đích:** Khi partner được duyệt → tạo user admin đầu tiên theo model tenant creation.
- **Luồng:** Approve → tạo user `{ userType: 'PARTNER_ORG_ADMIN', status: 'PENDING_ACTIVATION' }` → `blazeup.partner.approved` kích `ms-notification` gửi email kích hoạt → partner **tự đặt mật khẩu** qua link.
- **Điểm cần check:**
  - [ ] User tạo ra ở trạng thái `PENDING_ACTIVATION`.
  - [ ] Có email kích hoạt gửi tới primary contact.
  - [ ] **Không** có mật khẩu tạm do SA đặt — partner tự set.
  - [ ] Link kích hoạt hết hạn theo chuẩn Auth token.
- **PRD:** B2 (d.1140), §5.1

---

## 2. Tier & Partner Type

### 2.1 Tự động tính & chuyển tier
- 📍 **Vị trí:** 🟥 SA `/partners` (cột Tier) + `Analytics` (§5.5) · 🟦 Partner Home dashboard — thanh "Tier Progress" (§4.3) · ⚙️ tính tự động đầu quý
- **Mục đích:** Tier tính tự động theo ARR T12M vào ngày đầu mỗi quý.
- **Điểm cần check:**
  - [ ] Ngưỡng: Registered $0 · Select $50K · Advanced $200K · Premier $750K.
  - [ ] **Upgrade** hiệu lực ngay; **downgrade** báo trước 30 ngày + grace quarter.
  - [ ] Chuyển tier → emit `blazeup.partner.tier.changed` → portal + analytics cập nhật.
  - [ ] PSM: **dedicated** khi ≥$1.5M (trong Premier); dưới ngưỡng **shared** tối đa 1:3; Advanced cũng dùng pool shared 1:3.
  - [ ] **MSP tier** tính trên **total ARR managed** (cả book), không chỉ net-new logo.
- **PRD:** §2.1, §2.2, §5.5

### 2.2 Partner type ↔ billing model
- 📍 **Vị trí:** 🟦 Partner chọn type tại bước đăng ký · 🟥 SA xem ở Partner Profile (§5.1)
- **Mục đích:** Type quyết định billing model & deal flow khả dụng.
- **Điểm cần check:**
  - [ ] Referral → `direct`; Reseller/VAR → `reseller`; SI → `direct`; MSP → `partner_managed`.
  - [ ] Reseller **tự đặt giá bán** cho end-client; BlazeUp **không** lưu sell price ở bất kỳ record nào.
- **PRD:** §2.2

### 2.3 Certification mở khóa quyền
- 📍 **Vị trí:** 🟦 Partner `/training` (§4.8) · 🟥 SA xem ở Partner Profile → Team certifications (§5.1)
- **Điểm cần check:**
  - [ ] Sales Certified → mở deal registration + referral commission.
  - [ ] HR/CRM Specialist → mở **co-sell eligibility** theo module tương ứng.
  - [ ] Implementation Certified → mở **MSP billing model** + implementation revenue.
  - [ ] Hoàn thành cert → emit `blazeup.partner.certification.earned` → tier engine tính lại.
- **PRD:** §2.4

---

## 3. Deal Registration & Các Tổ hợp Deal (§3 — phần cốt lõi)

### 3.1 Đăng ký deal (wizard < 90s)
- 📍 **Vị trí:** 🟦 Partner `/deals/register` (§4.4)
- **Luồng:** Company (auto-enrich domain) → Contact → Deal (ACV, close date, modules, deal type) → Confirm.
- **Điểm cần check:**
  - [ ] Auto-enrich khi blur domain (logo, country, headcount).
  - [ ] Domain đã là tenant/deal active → **cảnh báo inline** nhưng vẫn cho submit (vào conflict queue).
  - [ ] **Commission dự kiến hiện realtime** khi gõ ACV (đúng theo tier + deal type).
  - [ ] Submit → trả `Deal ID` + status "Pending SA approval" < 2s.
  - [ ] Emit `blazeup.partner.deal.registered`.
- **PRD:** §4.4

### 3.2 Scenario A — Pure Referral
- 📍 **Vị trí:** 🟦 Partner `/deals/:id` (Deal Detail, read-only sau handoff) (§4.5) · 🔗 BlazeUp sales đóng ở dogfood CRM
- **Luồng:** Partner giới thiệu → step back → **BlazeUp sales đóng deal** → commission = tier rate × Y1 ACV.
- **Điểm cần check:**
  - [ ] Sau handoff partner ở chế độ **read-only** trên deal.
  - [ ] Hiển thị BlazeUp rep (tên + ảnh), partner nhắn được trên deal thread.
  - [ ] Commission = referral rate × Y1 ACV.
- **PRD:** §3-A

### 3.3 Scenario B — Reseller-Led
- 📍 **Vị trí:** 🟦 Partner `/deals/:id` → nút **Mark Won** (§4.5, §3-B)
- **Luồng:** Partner tự bán, tự làm procurement → **partner tự bấm "Mark Won"** → tenant provisioned → BlazeUp invoice **partner** giá discount.
- **Điểm cần check:**
  - [ ] Partner (không phải BlazeUp) là người mark Won.
  - [ ] `billing.model = 'reseller'`.
  - [ ] Invoice trỏ về **partner**, không phải client.
  - [ ] BlazeUp **không** đụng payment của client; **không** lưu sell price.
- **PRD:** §3-B, §7.2

### 3.4 Scenario C — Co-sell
- 📍 **Vị trí:** 🟦 Partner `/deals/:id` (shared record) + accept override · 🟥 SA đề xuất override tại Approval Queue (§5.2)
- **Luồng:** Partner chọn "Co-sell" → SA gán rep trong 1 ngày làm việc → cùng làm trên shared deal record.
- **Điểm cần check:**
  - [ ] Split **mặc định 70/30** áp tự động.
  - [ ] Deal **>$100K ACV**: SA đề xuất override → **bắt buộc partner đồng ý bằng văn bản** trên deal record.
  - [ ] Split **khóa cứng tại approval**, không renegotiate sau đó.
  - [ ] BlazeUp **không** áp split khác mặc định một chiều.
- **PRD:** §3-C, §5.2, §8.5

### 3.5 Scenario D — Deal Conflict
- 📍 **Vị trí:** 🟥 SA `/partners → Deal Management → tab "Conflict Queue"` (§5.2)
- **Luồng:** 2 bên đăng ký cùng domain → vào conflict queue → SA xử theo thứ tự luật.
- **Điểm cần check:**
  - [ ] Thứ tự: (1) prospect xác nhận engage với ai → bên đó thắng; (2) first-registered wins nếu không liên hệ được; (3) SA mediate trong **5 ngày làm việc**.
  - [ ] Quyết định **ghi audit trail (immutable)** + notify 2 bên kèm lý do (bắt buộc).
  - [ ] Bên thua có thể đăng ký lại sau **90 ngày** nếu bên thắng không close.
  - [ ] Emit `blazeup.partner.deal.conflict_raised`.
- **PRD:** §3-D, §5.2

### 3.6 Scenario E — Referral Link Attribution (không cần đăng ký deal)
- 📍 **Vị trí:** 🟦 Partner `/team` (referral links) hoặc `/settings` (§4.10) · ⚙️ attribution server-side (Redis) + auto commission (§8.4)
- **Luồng:** Prospect click link → server ghi `partner_id` (Redis, TTL 30 ngày) → signup sau đó → auto-attribute + commission tự động.
- **Điểm cần check:**
  - [ ] First-touch wins (TTL set ở lần click đầu tiên).
  - [ ] Attribution **sống qua** đóng browser/incognito/đổi thiết bị (server-side cookie `__blazeup_ref`).
  - [ ] Click 40 ngày trước (quá TTL) → **không** attribute.
  - [ ] Signup không cookie → direct, không partner.
  - [ ] Auto fire `blazeup.partner.deal.won` + commission.
- **PRD:** §3-E, §8.4

### 3.7 Scenario F — Expansion tại client cũ
- 📍 **Vị trí:** 🟦 Partner `/clients/:id → "Register Renewal Deal"` hoặc `/deals/register` (chọn tenant cũ) (§4.6)
- **Luồng:** Partner đăng ký expansion trên `tenant_id` cũ → approve → **thêm module/seat vào tenant cũ (KHÔNG tạo tenant mới)**.
- **Điểm cần check:**
  - [ ] Không tạo tenant mới; subscription line-items được cập nhật.
  - [ ] Commission theo mô hình **lifecycle NN/EN/EE** (B6):
    - **NN** (trong honeymoon window, tính theo năm SA-config) → full new-logo rate.
    - **EN** (sau NN, thêm license mới) → rate thấp hơn.
    - **EE** (renewal license cũ) → rate thấp nhất (có thể = 0).
  - [ ] Engine phân loại NN/EN/EE dựa trên `tenant.goLiveAt` + window config.
  - [ ] My Clients cập nhật ARR mới.
- **PRD:** §3-F, §7.4, §8.2, B6

### 3.8 Scenario G — MSP Model
- 📍 **Vị trí:** 🟦 Partner (MSP) `/clients → "Managed Clients" → "+ Add Managed Client"` (§7.3)
- **Luồng:** MSP provision tenant hộ client ("+ Add Managed Client") → BlazeUp invoice MSP → MSP invoice client. Xem chi tiết access ở §7 checklist.
- **Điểm cần check:**
  - [ ] Tenant xuất hiện trong "Managed Clients".
  - [ ] MSP có scoped admin (config module, manage user, raise ticket, view health).
  - [ ] **Hard limit:** không payroll, không PII quá ceiling, không export.
  - [ ] Escalation: client → MSP support → BlazeUp support (qua partner ticket).
- **PRD:** §3-G, §7.3, §9.2

### 3.9 Scenario H — Tech partner cũng resell
- 📍 **Vị trí:** 🟦 Partner portal — **switcher** giữa 2 dashboard (pack ↔ channel) · 🔗 pack account ở SA Tier K marketplace (§3-H)
- **Điểm cần check:**
  - [ ] 1 login giữ 2 account type; pack account ở SA Tier K, channel account ở ms-sa-partners.
  - [ ] Revenue share pack vs channel commission ghi **2 ledger tách biệt**.
  - [ ] Portal có switcher giữa 2 dashboard.
- **PRD:** §3-H

### 3.10 Scenario I — Multi-partner influenced
- 📍 **Vị trí:** ⚙️ Attribution engine (first-registered) · 🟥 SA Conflict Queue nếu cả 2 đăng ký (§5.2)
- **Điểm cần check:**
  - [ ] Attribution về partner **đăng ký deal trước**.
  - [ ] Không ai đăng ký → **không trả commission** (đây là incentive để đăng ký).
  - [ ] Cả hai đăng ký → về Scenario D.
- **PRD:** §3-I

---

## 4. Deal Approval, Protection & Auto-extend (phía SA)

### 4.1 Duyệt deal + gán rep
- 📍 **Vị trí:** 🟥 SA `/partners → Deal Management → tab "Pending Approval"` (§5.2)
- **Điểm cần check:**
  - [ ] Approve → emit `blazeup.partner.deal.approved`.
  - [ ] **Protection clock** bắt đầu: Select 60d · Advanced 90d · Premier 120d.
  - [ ] `commissionRate` + `rateTableVersion` **stamp tại thời điểm approval** (rate khóa tại approve, không phải registration/invoice).
  - [ ] Co-sell >$100K: override 70/30 ghi dạng **pending proposal** đến khi partner accept.
  - [ ] Assigned rep nhận task trong dogfood CRM; partner nhận in-app + email.
- **PRD:** §5.2, §6.3

### 4.2 Auto-extend protection (activity gate)
- 📍 **Vị trí:** ⚙️ System cron (activity check) · 🟥 SA thấy trên deal record · 🟦 Partner nhận notify + `/deals/:id` (xin manual extend) (§5.2)
- **Điểm cần check:**
  - [ ] Hết window + **có ≥1 stage update trong 30 ngày qua** + **chưa từng auto-extend** → **auto-extend 1 lần** thành 2× window; emit `protection_extended`; notify partner.
  - [ ] Không có update 30 ngày HOẶC đã auto-extend rồi → **hard expiry**; emit `deal.expired`; partner có thể xin **manual SA extension** (kèm lý do).
  - [ ] `protectionExtensionCount` tối đa = 1.
- **PRD:** §5.2

### 4.3 Conflict queue (SA)
- 📍 **Vị trí:** 🟥 SA `/partners → Deal Management → tab "Conflict Queue"` (§5.2)
- **Điểm cần check:** (đã liệt ở 3.5) — UI conflict queue, chọn kết quả, lý do bắt buộc, notify + audit.
- **PRD:** §5.2

---

## 5. Commission, Clawback, Payout

### 5.1 Rate table & SPIFF (SA config)
- 📍 **Vị trí:** 🟥 SA `/partners → Commission Configuration` (rate table + SPIFF + version history) (§5.3)
- **Điểm cần check:**
  - [ ] Sửa rate **không cần deploy code**; mọi version được lưu (version history).
  - [ ] Bảng rate theo Tier × Deal Type (Referral/Reseller Margin/Co-sell).
  - [ ] SPIFF: bonus theo region/module/tier + khoảng thời gian; áp đúng đối tượng.
- **PRD:** §5.3, §8.2

### 5.2 Clawback
- 📍 **Vị trí:** 🟥 SA `/partners → Commission Configuration → Clawback Policy` (§5.3) · 🟦 Partner thấy tại lúc approve commission + `/commissions`
- **Điểm cần check:**
  - [ ] Client churn trong **12 tháng** kể từ go-live → clawback **50%** commission đã trả.
  - [ ] Áp cho **Referral, Co-sell**; **KHÔNG** áp cho **Reseller** (đã thu margin lúc invoice).
  - [ ] Điều khoản clawback **hiển thị tại lúc approve commission** + trên thông báo clawback (không bất ngờ).
  - [ ] Dispute window 30 ngày.
- **PRD:** §5.3
- **⚠️ Cần làm rõ:** MSP (`partner_managed`) có bị clawback không? PRD chỉ liệt Referral + Co-sell — logic giống Reseller → nhiều khả năng **không**. Cần confirm BE/PO.

### 5.3 Product-failure waiver
- 📍 **Vị trí:** 🟦 Partner `/commissions → "Request Product-Failure Waiver"` (§4.7) · 🟥 SA Waiver review queue (§5, effort estimates)
- **Điểm cần check:**
  - [ ] Partner bấm waiver trên clawback row → 1 ô lý do + **link ticket/incident** → submit.
  - [ ] SA partner-ops quyết trong **30 ngày**.
  - [ ] Kết quả ghi dạng **partial/full credit** trên clawback debit (không xóa commission row — ledger reconcile sạch).
  - [ ] **Không** có appeal; quyết định final + ghi audit.
  - [ ] Emit `blazeup.partner.commission.waiver_decided`.
- **PRD:** §4.7, §5.3

### 5.4 Dispute commission
- 📍 **Vị trí:** 🟦 Partner `/commissions → "Dispute Commission"` (§4.7) · 🟥 SA nhận notify + xử tại Commission Ledger
- **Điểm cần check:**
  - [ ] Deal → "Dispute commission" → 1 ô text → submit (không form/email/ticket number).
  - [ ] SA nhận notify; SLA **5 ngày làm việc**.
- **PRD:** §4.7

### 5.5 Commission Ledger — SA approval
- 📍 **Vị trí:** 🟥 SA `/partners → Commission Ledger` (§5.6)
- **Điểm cần check:**
  - [ ] Mọi commission tính ra **phải SA approve** trước khi queue payout.
  - [ ] **Two-eye** cho amount > $10K.
  - [ ] Emit `commission.earned` khi tính, `commission.paid` khi trả.
- **PRD:** §5.6

### 5.6 Payout details
- 📍 **Vị trí:** 🟦 Partner `/commissions → "Update Payout Details"` hoặc `/settings` (§4.7)
- **Điểm cần check:**
  - [ ] Hỗ trợ SWIFT/ACH/NEFT-IMPS/VN bank.
  - [ ] Banking details **CSFLE-encrypted at rest** (PDPL/PDPA).
- **PRD:** §4.7

---

## 6. My Clients / Client Health (§4.6)

### 6.1 Xem sức khỏe client
- 📍 **Vị trí:** 🟦 Partner `/clients` + `/clients/:id` (Client Health Detail) (§4.6)
- **Điểm cần check:**
  - [ ] Chỉ hiện **post-close**.
  - [ ] Health signals: DAU/MAU, module adoption, last login, open tickets (count + severity).
  - [ ] Blazey insight gợi ý upsell.
  - [ ] Renewal pipeline + nút "Register Renewal Deal".
  - [ ] Commission history của client.
- **PRD:** §4.6, §1.3

---

## 7. MSP Access Scope & Ticket Consent (§9.2 — nhạy cảm PDPA)

### 7.1 Scoped access enforcement (`PartnerScopeGuard`)
- 📍 **Vị trí:** ⚙️ Backend guard (mọi MS) — không có page riêng; áp khi MSP thao tác trên managed tenant (§9.2)
- **Điểm cần check:** (bảng access §9.2)
  - [ ] MSP **được:** config module, user management, ticket count+severity (luôn), PII cơ bản (name/email).
  - [ ] MSP **không:** payroll/salary/health, export data, billing config, impersonate.

### 7.2 Ticket-content consent (default OFF)
- 📍 **Vị trí:** 🟦 MSP set tại "+ Add Managed Client" / tenant admin bật sau; xem tại `/clients/:tenantId/tickets` (§7.3, §9.2)
- **Luồng:** Consent set tại provisioning (hoặc sau bởi tenant admin) → lưu `mspTicketContentConsent{}` trên tenant.
- **Điểm cần check:**
  - [ ] Mặc định OFF → MSP chỉ thấy **count + severity**; body thay bằng sentinel "Content restricted...".
  - [ ] Consent ON → MSP thấy **full content**.
  - [ ] Revoke → **hiệu lực ngay lập tức**.
  - [ ] Mọi grant/revoke → emit `blazeup.partner.msp_ticket_consent.changed` + ghi audit (timestamp + actor).
- **PRD:** §3-G, §7.3, §9.2

---

## 8. Tenant Provisioning & Attribution (§7)

> **Nhắc lại:** đây là kiểm chứng *hệ quả provision + attribution*, **không** phải "add tenant". Tenant tạo qua call `SA /internal/tenants/provision`.

### 8.1 Provision on close
- 📍 **Vị trí:** ⚙️ Downstream — call `SA /internal/tenants/provision`, hội tụ `blazeup.tenant.provisioned` (không có page partner) (§7.1–7.4)
- **Điểm cần check:**
  - [ ] Referral/Reseller close → tenant được tạo; mọi path hội tụ ở `blazeup.tenant.provisioned`.
  - [ ] Reseller → `billing.model='reseller'`, invoice tới partner.
  - [ ] MSP → `billingModel='partner_managed'`, `billingPartnerId` set, invoice tới MSP.
  - [ ] Expansion → **không** tenant mới.
- **PRD:** §7.1–7.4

### 8.2 Attribution block (vĩnh viễn)
- 📍 **Vị trí:** ⚙️ Trên tenant record (block `attribution{}`) — cần read surface để verify (§7.5)
- **Điểm cần check:**
  - [ ] Mỗi tenant partner-sourced mang `attribution{ source, partnerId, partnerTier(khóa tại close), dealId, commissionStructure, billingModel }`.
  - [ ] `commissionStructure` có `rate, rateTableVersion, type, baseACV, clawbackExpiresAt (~go-live+12m), productFailureWaiver?`.
- **PRD:** §7.5

### 8.3 Attribution edge cases (B4)
- 📍 **Vị trí:** 🟥 SA-only (prospective attach / MSP handoff confirm / attribution override two-eye) (§7.5, B4)
- **Điểm cần check:**
  - [ ] (a) Partner liên quan nhưng **không đăng ký** → **không commission** (tuyệt đối).
  - [ ] (b) Tenant có trước programme → SA "prospective attribution" chỉ áp expansion/renewal tương lai, **không hồi tố**; bắt buộc lý do + audit.
  - [ ] (c) MSP handoff → **SA-only**, MSP cũ request (không tự chuyển), cần 2 bên đồng ý; history cũ giữ; emit `client.transferred`.
  - [ ] (d) SA override attribution → **two-person approval** + lý do bắt buộc + lưu `attributionHistory[]` (không xóa, chỉ supersede).
- **PRD:** §7.5, B4

---

## 9. CRM Integration (dogfood) (§6)

- 📍 **Vị trí:** 🔗 Dogfood CRM `blazeup.blazeup.ai` (module riêng) · ⚙️ đồng bộ qua Kafka `DogfoodCrmBridge` (§6)
- **Điểm cần check (event → CRM effect):**
  - [ ] `deal.registered` → tạo opportunity, stage "Partner Deal — Pending Approval", `source='partner_registered'`, owner unassigned.
  - [ ] `deal.approved` → update stage "Approved", gán owner rep, tạo task reach-out.
  - [ ] `deal.protection_extended` → cập nhật `protectionExpiresAt`, task "keep advancing".
  - [ ] `deal.won` → close Won, stamp ARR + `tenant_id` khi go-live.
  - [ ] `deal.lost` → close Lost + reason.
  - [ ] `deal.expired` → mark Stale + task follow-up.
  - [ ] `client.health_alert` → task trên account record.
  - [ ] Opportunity record mang đủ `attribution{}` (partnerId, tier, dealType, commissionRate, rateTableVersion, cosellSplit?).
- **PRD:** §6.1–6.3

---

## 10. Security / Auth / Audit (§9)

### 10.1 Partner Auth
- 📍 **Vị trí:** ⚙️ Cross-cutting (JWT issuer riêng cho partner) · 🟦 login `partner.blazeup.ai` (§9.1)
- **Điểm cần check:**
  - [ ] JWT issuer **tách riêng** khỏi tenant & SA (khác `iss`).
  - [ ] Access token 8h, refresh 30 ngày.
  - [ ] **Tenant isolation:** partner JWT **không** đọc được data của partner khác (any circumstance).
  - [ ] MFA — bắt buộc cho `PARTNER_ORG_ADMIN` và Advanced/Premier. **⚠️ OQ-14 chưa chốt** role-vs-tier.
- **PRD:** §9.1

### 10.2 Data residency
- 📍 **Vị trí:** ⚙️ Backend/infra (region storage) (§9.3)
- **Điểm cần check:**
  - [ ] Prospect data lưu tại region SA; khi có Middle East → UAE/Saudi lưu tại đó.
  - [ ] Không transfer cross-region không consent (PDPL).
- **PRD:** §9.3

### 10.3 Audit trail
- 📍 **Vị trí:** 🟥 SA audit log (`sa_audit_log` collection, Tier J) (§9.4)
- **Điểm cần check:** mọi hành động SA ghi `sa_audit_log`:
  - [ ] Deal approve/reject (lý do); protection extend (auto & manual); conflict resolution (immutable); co-sell override (kèm partner accept); commission approve/dispute; product-failure waiver (kèm evidence); MSP ticket-consent grant/revoke; territory changes; rate-table modifications (versioned).
- **PRD:** §9.4

---

## 11. SA Module — Directory, Territory, Analytics (§5)

### 11.1 Partner Directory
- 📍 **Vị trí:** 🟥 SA `/partners → Partner Directory` (§5.1)
- **Điểm cần check:** filter Region/Tier/Type/Status; drill-in profile (deal history, commission ledger, territory, PSM allocation, cert, activity log).
- **PRD:** §5.1

### 11.2 Territory Management
- 📍 **Vị trí:** 🟥 SA `/partners → Territory Management` (§5.4)
- **Điểm cần check:**
  - [ ] **Exclusive:** chỉ 1 partner được đăng ký trong region/vertical; conflict auto-route về partner này.
  - [ ] **Preferred:** nhiều partner; first-registered wins.
  - [ ] **None:** open market.
- **PRD:** §5.4

### 11.3 Analytics
- 📍 **Vị trí:** 🟥 SA `/partners → Analytics` (§5.5)
- **Điểm cần check:** partner-sourced ARR, deals registered, approval/win rate, avg deal size/velocity, funnel, commission paid/pending, clawbacks + **clawback waivers (track riêng)**, top partners, tier distribution.
- **PRD:** §5.5

---

## 12. Kafka Events — Checklist phát sự kiện

| Event | Khi nào | Scenario |
|---|---|---|
| `partner.registered` / `partner.approved` | tạo / duyệt partner | §1 |
| `partner.tier.changed` | đổi tier | §2.1 |
| `deal.registered` / `deal.approved` / `deal.rejected` | vòng đời deal | §3–4 |
| `deal.conflict_raised` | 2 bên cùng domain | 3.5 |
| `deal.protection_extended` | auto-extend | 4.2 |
| `deal.won` / `deal.lost` / `deal.expired` | close / hết hạn | 4 |
| `commission.earned` / `commission.paid` | tính / trả | 5 |
| `commission.waiver_decided` | quyết waiver | 5.3 |
| `client.health_alert` | health đổi | 6 |
| `msp_ticket_consent.changed` | grant/revoke consent | 7.2 |
| `client.transferred` | MSP handoff | 8.3c |
| `sandbox.reset_requested` | reset demo | §4.9/B5 |

- **PRD:** §8.3

---

## 13. Ngoài phạm vi PRD partner (tham chiếu)

| Kịch bản | Ghi chú |
|---|---|
| 🔗 **SA tạo tenant** (`POST /sa-tenants-api/tenants`, form "Create new tenant") | Thuộc `tenant-creation-module-spec-v1.1.md`, **không** thuộc PRD partner. Nếu cần test → làm test plan riêng cho module Tenant Creation. |
| 🔗 Pack partner / marketplace | SA Tier K — `marketplace-pack-architecture` |
| 🔗 Sandbox-data service (seed/reset demo tenant) | B5 — `blazeup-microservice-sandbox-data` |

---

## Phụ lục — Open questions ảnh hưởng test (chưa chốt)

| ID | Vấn đề | Ảnh hưởng check |
|---|---|---|
| OQ-14 | MFA role-based vs tier-based | Logic enforce MFA |
| OQ-15 | Định nghĩa "grace quarter" | Timing tier FSM |
| OQ-16→B6 | Rate expansion (đã chốt kiến trúc NN/EN/EE, rate TBD) | Commission expansion |
| OQ-17 | Conflict-loser 90 ngày: auto-unlock hay manual | Deal FSM |
| Clawback cho MSP | PRD chỉ liệt Referral+Co-sell | Xác nhận MSP có/không clawback |

**PRD:** §12
