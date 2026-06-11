# Product Backlog — Partner Module (Phân tích tiếng Việt)

> Nguồn: `[PartnerAdmin] Product Backlog_Partner Module.xlsx` (sheet `T7_Partner`).
> Actor chính: **Partner Admin** (một số mục là **Partner Member**). Dựa trên PRD v1.8+.
> Tài liệu này tóm tắt **công việc cần làm** cho từng user story, nhóm theo **Phase** và **ID**.

## Tổng quan

| Phase | Chủ đề | Số user story | ID |
|---|---|---|---|
| 1 | Onboarding & Kích hoạt | 2 | PP001, PP002 |
| 2 | Quản lý Deal | 6 | PP004, PP005, PP006, PP007, PP008, PA025 |
| 3 | Hoa hồng & Thanh toán | 3 | PP009, PP010, PP011 |
| 4 | Quản lý Khách hàng | 2 | PP012, PP013 |
| 5 | Đào tạo & Chứng chỉ | 1 | PP015 |
| 6 | Quản lý Nhóm | 4 | PP018, PP019, PP003, PP023 |
| 7 | Cài đặt & Hồ sơ | 3 | PP020, PP021, PP024 |
| 8 | Hỗ trợ | 1 | PP022 |

**Quy ước Priority:** High = ưu tiên cao, Medium = ưu tiên vừa.
**Trạng thái hiện tại:** tất cả đều `To Do`.

---

## Phase 1 — Onboarding & Kích hoạt

### PP001 — Kích hoạt tài khoản partner qua email mời
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Neven
- **Điều kiện trước:** SA đã duyệt đơn; tài khoản ở trạng thái `PENDING_ACTIVATION`; email mời đã gửi kèm token dùng-một-lần (TTL 72h).
- **Mô tả:** Partner đặt mật khẩu qua link mời trong email để truy cập portal lần đầu.
- **Công việc cần làm:**
  - [ ] Link kích hoạt chứa token dùng-một-lần; validate token (hết hạn > 72h hoặc đã dùng → báo lỗi + gợi ý xin mời lại).
  - [ ] Form đặt mật khẩu (không pre-fill); ràng buộc độ mạnh: ≥ 8 ký tự, 1 hoa, 1 số, 1 ký tự đặc biệt; validate inline.
  - [ ] Tier **Registered/Select**: TOTP (2FA) tùy chọn (cho phép Skip). Tier **Advanced/Premier**: TOTP **bắt buộc** (ẩn nút Skip).
  - [ ] Kích hoạt thành công: chuyển trạng thái `PENDING_ACTIVATION → Active`; cấp JWT (access 8h, refresh 30 ngày).
  - [ ] Redirect về `/dashboard` sau lần đăng nhập đầu; vô hiệu token ngay sau khi dùng.
  - [ ] Ghi audit log: account ID, action `account_activated`, timestamp.

### PP002 — Xem Home Dashboard
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Neven
- **Route:** `/dashboard` (hoặc `/`)
- **Mô tả:** Trang tổng quan pipeline, hoa hồng, sức khỏe khách hàng để biết ngay việc cần xử lý.
- **Công việc cần làm:**
  - [ ] KPI cards: Active deals, Pending SA approval (kèm deal chờ lâu nhất), Tổng hoa hồng YTD, Khách hàng có nguy cơ rủi ro gia hạn.
  - [ ] Pipeline snapshot: top 5 deal active theo ACV (stage + số ngày bảo vệ còn lại).
  - [ ] Recent activity: 5 sự kiện gần nhất (deal approved, commission paid, health alert, tier change).
  - [ ] Empty state khi chưa có deal: CTA "Register your first deal".
  - [ ] Header: tier badge + tiến độ T12M ARR.
  - [ ] Widget Blazey AI: gợi ý upsell theo dữ liệu sử dụng.
  - [ ] **Bảo mật:** chỉ hiển thị dữ liệu của chính partner đó (không lộ data partner khác).

---

## Phase 2 — Quản lý Deal

### PP004 — Đăng ký deal mới
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Bastian
- **Route:** `/deals/register` · **Điều kiện:** có ≥ 1 thành viên đạt *BlazeUp Sales Certified*.
- **Mô tả:** Wizard 4 bước hoàn tất < 90s trên mobile; prospect được bảo vệ domain và xem trước hoa hồng.
- **Công việc cần làm:**
  - [ ] **Bước 1 — Company:** Company name, Domain, Country (bắt buộc). Nhập domain → auto-enrich logo/HQ/headcount (Apollo/Clearbit); **check trùng domain real-time** (cảnh báo inline nếu đã bị partner khác đăng ký).
  - [ ] **Bước 2 — Contact:** Full name, Email (bắt buộc), Job title (tùy chọn).
  - [ ] **Bước 3 — Deal details:** ACV, Expected close date, Modules (multi-select), Deal type (Referral/Reseller/Co-sell). **Xem trước hoa hồng real-time** theo tier rate + deal type.
  - [ ] **Bước 4 — Confirm & Submit:** tóm tắt read-only, cho phép quay lại sửa; nút Submit chỉ bật khi đủ field bắt buộc.
  - [ ] Khi submit: tạo deal `Pending Review`; stamp `registeredAt` (ms); bắn Kafka `blazeup.partner.deal.registered`; phản hồi < 2s.
  - [ ] Xác nhận in-portal + email; redirect `/deals/:id`.
  - [ ] Race condition trùng domain sau submit → tự chuyển `Conflict Detected` + thông báo.

### PP005 — Xem Deal Pipeline (My Pipeline)
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Cofadict
- **Route:** `/deals`
- **Công việc cần làm:**
  - [ ] Bảng cột: Deal (company + domain), Deal ID, Type, ACV, Stage, Commission, Protection (progress bar ngày còn lại), Last updated.
  - [ ] Filter tabs: All / Pending Approval / Approved / In Progress / Won / Lost / Expired (kèm số đếm).
  - [ ] Search real-time theo company/domain; Sort theo ACV/stage/ngày đăng ký.
  - [ ] Cảnh báo: deal sắp hết bảo vệ (≤ 14 ngày) gắn nhãn **amber**; deal `Conflict Detected` gắn nhãn **đỏ**.
  - [ ] Mỗi dòng click → `/deals/:id`; CTA "Register new deal" trên toolbar.
  - [ ] **Bảo mật:** chỉ thấy deal của chính mình.

### PP006 — Xem chi tiết Deal
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Cofadict
- **Route:** `/deals/:id`
- **Công việc cần làm:**
  - [ ] Header: company, domain, deal type, stage, ACV, expected close date.
  - [ ] Section **Commission**: payout ước tính (hoặc đã khóa nếu approved), rate basis, công thức theo deal type; khóa rate + icon khóa + ngày duyệt.
  - [ ] Section **Protection window**: domain, ngày bắt đầu, ngày hết hạn, progress bar; điều kiện auto-extend.
  - [ ] Section **Approval timeline** (read-only, **bất biến** — không sửa/xóa).
  - [ ] Co-sell: hiển thị BlazeUp Sales Rep + commission split (khóa sau duyệt). Reseller: tóm tắt billing flow + ghi chú clawback không áp dụng.
  - [ ] Nút **Mark as Won** (deal Approved, Reseller/Co-sell) yêu cầu ACV + close date; nút **Mark as Lost** yêu cầu lý do.

### PP007 — Đánh dấu deal Reseller là Won
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Cofadict
- **Điều kiện:** deal `Approved`, type Reseller/Co-sell, người dùng là owner.
- **Công việc cần làm:**
  - [ ] Nhập: confirmed ACV (số dương, validate), close date (bắt buộc), notes (tùy chọn).
  - [ ] Confirm → status `Won`; stamp `closedAt`; bắn Kafka `blazeup.partner.deal.won`.
  - [ ] Commission engine tính tự động: Reseller = list − wholesale; Co-sell = ACV × tier rate × split %. Tạo commission `Pending Approval`.
  - [ ] Trigger provisioning tenant theo billing model; stamp `go_live_at` (mốc clawback cho Co-sell).
  - [ ] Thông báo payout dự kiến (net-30); redirect Deal Detail hiển thị `Won` + hoa hồng đã khóa.

### PP008 — Đăng ký Expansion deal
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Điều kiện:** có deal `Won` còn attribution (trong 12 tháng).
- **Công việc cần làm:**
  - [ ] Vào từ `/clients/:id` hoặc `/deals/register` với type `Expansion`; pre-populate `tenant_id` từ client.
  - [ ] Chọn loại expansion: thêm seats / module mới / nâng tier. Validate attribution còn trong 12 tháng (hết → chặn + báo).
  - [ ] Nhập ACV delta, modules/seats thêm, expected close date; xem trước hoa hồng (expansion rate × delta ARR) live.
  - [ ] Submit → tạo Expansion deal; Kafka `deal.registered (deal_type=expansion)`; **không tạo tenant mới** (cập nhật tenant khi Won).

### PA025 — Duyệt/chấp nhận đề xuất chia hoa hồng Co-sell từ SA
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Cofadict
- **Điều kiện:** deal Co-sell ACV > $100K; SA đề xuất split khác mặc định.
- **Mô tả:** Split chỉ được khóa khi có **đồng ý bằng văn bản** của Partner; BlazeUp không tự áp đặt.
- **Công việc cần làm:**
  - [ ] Thông báo "Action Required" trên dashboard kèm đếm ngày; banner trên deal hiển thị split đề xuất vs mặc định 70/30.
  - [ ] Deal **không tiến stage** và **đồng hồ bảo vệ không chạy** cho tới khi Partner Accept/Decline.
  - [ ] **Accept:** modal yêu cầu gõ "I AGREE" / tick consent → set `overrideApproved=true`, khóa split, deal sang `Approved`, thông báo 2 bên.
  - [ ] **Decline:** modal lý do (tùy chọn) → SA được báo, deal về 70/30 hoặc vào SA review.
  - [ ] Ghi audit log: actor, split đề xuất, quyết định, timestamp.

---

## Phase 3 — Hoa hồng & Thanh toán

### PP009 — Xem lịch sử hoa hồng & payout
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Bastian
- **Route:** `/commissions`
- **Công việc cần làm:**
  - [ ] Bảng cột: Commission ID, Deal, Type, Base ACV, Rate (khóa tại duyệt + version bảng rate), Amount, Status (Pending/Approved/Paid/Clawback), Expected payout date.
  - [ ] Filter tabs theo status (kèm count + tổng tiền); filter theo MTD/QTD/YTD.
  - [ ] Mỗi dòng expand → breakdown đầy đủ (công thức, version rate, lock date, chuỗi duyệt 2-mắt nếu > $10K).
  - [ ] Dòng clawback tô **amber** + lý do + số tiền trừ.
  - [ ] KPI đầu trang: Total YTD earned, Pending payout. **Chỉ thấy hoa hồng của mình.**

### PP010 — Yêu cầu miễn clawback (do lỗi sản phẩm)
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** Bastian
- **Điều kiện:** đã bị clawback; churn trong 12 tháng từ `go_live_at`; type Referral/Co-sell (**không** áp dụng Reseller).
- **Công việc cần làm:**
  - [ ] Nút "Request Waiver" trên dòng clawback; nhập lý do (bắt buộc) + link ticket/incident (bắt buộc).
  - [ ] Tạo waiver request `Pending SA Review`; xác nhận SLA review 30 ngày.
  - [ ] SA quyết định (approved full/partial hoặc rejected); bắn Kafka `commission.waiver_decided`; thông báo + lý do.
  - [ ] Quyết định **chung thẩm** (không kháng nghị); hiển thị read-only. Ẩn nút với deal Reseller.

### PP011 — Cập nhật thông tin thanh toán
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Bastian
- **Route:** `/settings` → Payment details · **Điều kiện:** đã hoàn tất MFA.
- **Công việc cần làm:**
  - [ ] Fields: Bank name, Account holder, Account number (mask còn 4 số cuối), BSB/IBAN/SWIFT, Currency.
  - [ ] **Mã hóa khi lưu** (AES-256-GCM, field-level) — không lưu plaintext; UI chỉ hiện 4 số cuối.
  - [ ] Lưu thay đổi yêu cầu **re-auth (MFA)**; áp dụng cho payout kế tiếp (payout đang chạy dùng thông tin cũ).
  - [ ] Audit log (actor, action, timestamp, IP — giữ 7 năm); email xác nhận thay đổi.

---

## Phase 4 — Quản lý Khách hàng

### PP012 — Dashboard sức khỏe khách hàng
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Neven
- **Route:** `/clients`
- **Công việc cần làm:**
  - [ ] Bảng cột: Client name, Modules active, DAU/MAU (%), Renewal date (ngày còn lại), Open tickets (count + severity), Health score.
  - [ ] Health score từ: xu hướng DAU/MAU, mức độ dùng module, ngày đến hạn gia hạn, ticket critical mở.
  - [ ] Cảnh báo: nguy cơ churn (health thấp) → **đỏ**; gia hạn trong 30 ngày → **amber**.
  - [ ] Mỗi dòng → `/clients/:id`; widget Blazey AI gợi ý upsell theo client.
  - [ ] **Phân quyền ticket:** non-MSP chỉ thấy count + severity; MSP thấy nội dung đầy đủ **nếu** `mspTicketContentConsent.granted = true`.

### PP013 — Chi tiết sức khỏe một khách hàng
- **Priority:** High · **Actor:** Partner Admin · **PIC:** Neven
- **Route:** `/clients/:id`
- **Công việc cần làm:**
  - [ ] Header: client name, industry, headcount, modules active, billing model, renewal date.
  - [ ] Section **Usage**: DAU/MAU theo module (chart), xu hướng 30/60/90 ngày, số user inactive.
  - [ ] Section **Module adoption**: % seat dùng từng module; module < 30% gắn cờ.
  - [ ] Section **Support**: count + severity (non-MSP) / nội dung đầy đủ (MSP nếu consent).
  - [ ] Section **Upsell** (Blazey AI) + **Expansion deals** liên quan; CTA "Register expansion deal" nếu còn attribution 12 tháng.
  - [ ] **Chặn truy cập:** payroll/salary, PII trên ngưỡng SA, hồ sơ nhân viên, cấu hình billing.

---

## Phase 5 — Đào tạo & Chứng chỉ

### PP015 — Xem & bắt đầu khóa chứng chỉ
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Route:** `/training`
- **Công việc cần làm:**
  - [ ] Catalogue: Sales Certified (4h), HR Specialist (6h), CRM Specialist (4h), Implementation Certified (12h).
  - [ ] Mỗi card: tiêu đề, thời lượng, "mở khóa gì", trạng thái hoàn thành theo từng thành viên.
  - [ ] "Mở khóa": Sales→đăng ký deal + referral; HR→co-sell HR/Payroll; CRM→co-sell CRM; Implementation→MSP billing.
  - [ ] Hoàn thành → Kafka `certification.earned`; kích hoạt tính năng ngay; nhắc cert còn thiếu cho deal đang chờ.

---

## Phase 6 — Quản lý Nhóm

### PP018 — Mời & quản lý thành viên
- **Priority:** High · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Route:** `/team`
- **Công việc cần làm:**
  - [ ] Danh sách: name, email, role (Admin/Member), status (Active/Invited/Deactivated), last login, certifications.
  - [ ] "Invite member": gửi email link kích hoạt dùng-một-lần (72h, model PENDING_ACTIVATION).
  - [ ] Gán role: Admin (full) / Member (đăng ký deal + xem pipeline chung).
  - [ ] Deactivate/Reactivate thành viên (deal của họ vẫn giữ); **chỉ 1 Admin/tài khoản** (Admin không tự hạ mình).

### PP019 — Xem pipeline nhóm (góc nhìn Member)
- **Priority:** Medium · **Actor:** Partner **Member** · **PIC:** *(chưa giao)*
- **Route:** `/deals`
- **Công việc cần làm:**
  - [ ] Member thấy **mọi deal** của cùng tài khoản partner (không chỉ của mình).
  - [ ] Member **được:** đăng ký deal, xem chi tiết, update stage deal của mình, mark Won deal Reseller.
  - [ ] Member **không được:** quản lý thành viên, sửa payment, sửa account settings.
  - [ ] Deal gán cho member đăng ký; hoa hồng ghi về **tài khoản partner** (không cá nhân).

### PP003 — Đổi role thành viên (Admin ↔ Member)
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Công việc cần làm:**
  - [ ] `/team`: mỗi dòng có action [Edit role]; dropdown Admin/Member (pre-select role hiện tại).
  - [ ] **Chặn** đổi role chính mình nếu là Admin duy nhất ("gán Admin khác trước").
  - [ ] Lưu → cập nhật role ngay (không hủy session); ghi audit log (actor, member, role cũ/mới, timestamp).

### PP023 — Thu hồi quyền truy cập thành viên
- **Priority:** High · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Công việc cần làm:**
  - [ ] `/team`: action [Revoke access] + dialog xác nhận (cảnh báo đăng xuất ngay, không hoàn tác trừ khi mời lại).
  - [ ] **Chặn** thu hồi Admin cuối cùng (disable + tooltip).
  - [ ] Confirm → status `Revoked`; **vô hiệu JWT (access + refresh) server-side ngay**; chấm dứt session.
  - [ ] Member bị thu hồi không đăng nhập được; lịch sử vẫn giữ trong audit log; ghi log thu hồi.

---

## Phase 7 — Cài đặt & Hồ sơ

### PP020 — Quản lý hồ sơ partner & cài đặt tài khoản
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Route:** `/settings`
- **Công việc cần làm:**
  - [ ] Sections: Company info (name, domain, address, logo), Primary contact, Notification preferences, Security (đổi mật khẩu, TOTP).
  - [ ] Đổi company name/domain → cần **SA duyệt** (hiển thị "Pending SA review" sau khi lưu).
  - [ ] Logo: ≤ 2MB, PNG/JPG. Notification lưu **theo từng user** (Admin & Member độc lập).
  - [ ] Đổi mật khẩu cần xác thực mật khẩu hiện tại; TOTP: enrol/regenerate backup codes/remove (Advanced/Premier **chặn remove**).
  - [ ] Audit log: actor, `profile_updated`, fields_changed, timestamp.

### PP021 — Xem trạng thái & tiến độ Tier
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Công việc cần làm:**
  - [ ] Tier badge ở header + section Tier trong Settings.
  - [ ] Hiển thị: T12M ARR hiện tại, ngưỡng tier hiện tại & tier kế, khoảng cách ARR còn thiếu; progress bar (cap 100% nếu Premier).
  - [ ] Bảng quyền lợi 4 tier (rate, protection window, features) — highlight tier hiện tại.
  - [ ] Grace period (sắp hạ tier): hiển thị `grace_tier_until`; ngày review quý kế; thông báo hạ tier báo trước 30 ngày.

### PP024 — Quản lý cài đặt TOTP (2FA)
- **Priority:** High · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Route:** `/settings` → Security
- **Công việc cần làm:**
  - [ ] Hiển thị trạng thái (Enabled / Not enrolled). Chưa enrol → [Set up 2FA] mở wizard QR (Google Authenticator/Authy) + manual key.
  - [ ] Nhập mã 6 số hợp lệ để hoàn tất ([Confirm] disable tới khi đủ 6 số; mã sai báo inline).
  - [ ] Enrol xong: status Enabled; sinh **recovery codes** hiển thị 1 lần (bắt buộc xác nhận đã lưu).
  - [ ] Tier Registered/Select: có [Disable 2FA] (cần xác nhận mật khẩu). Tier Advanced/Premier: **ẩn Disable** (không tắt được).
  - [ ] Audit log mỗi lần enrol/disable.

---

## Phase 8 — Hỗ trợ

### PP022 — Gửi & theo dõi support ticket
- **Priority:** Medium · **Actor:** Partner Admin · **PIC:** *(chưa giao)*
- **Route:** `/support`
- **Công việc cần làm:**
  - [ ] Form "New ticket": subject, category (Deal/Commission/Technical/Account/Other), description, attachments (≤ 10MB); link tới deal/commission cụ thể.
  - [ ] Danh sách ticket: ID, subject, category, status (Open/In progress/Resolved/Closed), created, last updated.
  - [ ] Xem full thread (kèm phản hồi SA); reply ticket mở; đóng ticket đã resolved.
  - [ ] Email thông báo: ticket created / SA reply / ticket closed.
  - [ ] Hiển thị SLA theo priority: Critical 4h, High 1 ngày làm việc, Medium 3 ngày làm việc.

---

## Ghi chú cho QA Automation
- **Route** đã liệt kê sẵn ở mỗi mục → dùng làm cơ sở viết test UI (page object theo `docs/page-objects.md`).
- Nhiều mục có **ràng buộc bảo mật/phân quyền** (chỉ thấy data của mình, MSP consent, chặn truy cập payroll...) → ưu tiên test các nhánh phân quyền.
- Các sự kiện **Kafka** (`deal.registered`, `deal.won`, `commission.waiver_decided`, `certification.earned`) → có thể kiểm ở tầng API/integration.
- Mục có **PIC *(chưa giao)*** = chưa phân công người làm; nên xác nhận với PM trước khi lên kế hoạch test.
