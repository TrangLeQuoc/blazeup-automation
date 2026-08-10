# Partner Platform — Kế hoạch Test (Automation)

> Sinh tự động từ test plan. TC NOT_STARTED chỉ hiện tên; BLOCKED hiện lý do block; PASSED/FAILED hiện đầy đủ mô tả, các bước (kèm expected mỗi bước), expected tổng, và ghi chú.

## 0. TC còn THIẾU (Figma design có, plan chưa có TC)

Các workflow partner-management phía SA này có design Figma "Ready for dev" (`design_partner/…`, `[PN…]`) nhưng **chưa có TC tương ứng**. Đề xuất thêm vào plan, rồi automate khi UI deploy.

> Các candidate trước đây giờ đã thành **TC documented** nên đã bỏ khỏi danh sách này: PN002 → `SA_PARTNER_MODULE_013`, PN014 → `_014`, PN015 → `_015`, PN016 → `_016`, PN004 → `_017`, PN005 → `_018`, PN027 (request-info) → `_019`, PN013 (clawback) → `COMMISSIONS_010`.

| Design | TC đề xuất |
|---|---|
| PN011 Mark deal Won → trigger commission | SA mark-won (UI) [+ API commission-calc] |
| PN019 Mark deal Lost | SA mark-lost (UI) |
| PN027 Review custom plan request | SA review/respond custom-plan request |
| PN028 Propose co-sell split override (ACV > $100K) | SA co-sell split override |

## 1. UI

### UI · COMMISSIONS

#### PARTNER_UI_COMMISSIONS_001
**Ghi chú (BLOCKED):** Nhập estimated annual value → commission projection update live (trong deal-register wizard, step 2). Blocked do thiếu test data (verify live 2026-07-27): partner test **chưa cấu hình commission rate** — `/resources` hiện *"Commission Rates: No rates configured yet. Contact your programme manager."* Projection = `Total rate × Estimated ACV`, rate trống → **không tính ra giá trị** (probe: đổi input không hiện `$` projection). Ngoài ra ACV không phải input trực tiếp — "Estimated ACV / Rate / Projected commission" là các section collapsible hiển thị trong wizard (ACV derive từ plan × seats), nên không có gì để "type" cho live rate×ACV. Unblock khi **cấu hình commission rate** cho partner test (qua SA rate-table) để projection ra giá trị verify được.
#### PARTNER_UI_COMMISSIONS_002
**Mô tả test:** Mở trang Commissions và xác nhận summary totals (earned/pending/paid) + các ledger status tab render. Read-only: hoạt động cả khi ledger rỗng (amount có thể $0) — kiểm cấu trúc trang, không phụ thuộc dữ liệu cụ thể.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; mở `/commissions` qua shell và chờ READY_MARKER "Commissions"; chờ data settle.
**Các bước:**
1. 4 summary total render, mỗi cái có giá trị $.
   → Expected: card **Pending Payout**, **Paid YTD**, **Total Earned**, **Clawback Risk** đều hiển thị $ (vd $0 khi ledger rỗng).
2. Tất cả ledger status tab hiển thị.
   → Expected: **All / Earned / Pending / Approved / Paid / Disputed / Clawback**.
**Expected (tổng):** Trang Commissions render summary totals + tất cả ledger tab (không phụ thuộc số commission).
**Ghi chú:** PASSED — verified 2026-07-28 (TC 12060302). Content-test COMMISSIONS đầu tiên — dựng nền page-object `CommissionsPage` (summary cards, ledger tabs). Ledger rỗng hiện "No commissions yet" (partner chưa có deal won). Negative: N/A — view read-only. Idempotency: N/A — read-only.
#### PARTNER_UI_COMMISSIONS_003 — BLOCKED (thiếu data ledger)
**Intent:** Trace 1 dòng commission — mở row và verify đủ trường lifecycle (deal → close → rate/version → approval → payout → clawback/waiver → payment status); tổng khớp các dòng hiển thị.
**Lý do block:** Ledger commission **rỗng** — partner test chưa có deal **Won** nào nên không có commission row ("No commissions yet"). Không có gì để mở/verify. Chuỗi phụ thuộc: rate cấu hình (SA_PARTNER_MODULE_009, chưa deploy) → deal approve (SA deal queue bị BUG-UI-005) → deal Won → commission row. Unblock khi ledger có ít nhất 1 commission.
#### PARTNER_UI_COMMISSIONS_004 — BLOCKED (thiếu data ledger)
**Intent:** Submit commission dispute từ 1 ô text trên 1 dòng commission.
**Lý do block:** Giống _003 — không có commission row nào để dispute (partner chưa có Won deal → ledger rỗng). Cần 1 commission thật trước (rate → approved deal → Won).
#### PARTNER_UI_COMMISSIONS_005 — BLOCKED (thiếu data ledger)
**Intent:** Submit product-failure waiver request kèm evidence, gắn vào 1 dòng commission/clawback.
**Lý do block:** Giống _003/_004 — không có commission row đủ điều kiện clawback (ledger rỗng). Cần 1 commission ở trạng thái clawback-eligible trước.
#### PARTNER_UI_COMMISSIONS_006 — BLOCKED (UI + data chưa có) — Security
**Intent:** Duyệt payout commission **> $10K** — bắt buộc **two-eye approval** (1 người không tự duyệt khoản lớn).
**Lý do block:** Cần (a) 1 payout >$10K đang chờ duyệt — mà cần Won deal → commission → payout (ledger rỗng, block như _003), và (b) UI two-eye approval (SA-side, design PN012) **chưa deploy** staging. Unblock khi có cả data payout + UI two-eye.
#### PARTNER_UI_COMMISSIONS_007 — BLOCKED (UI config SA-side chưa deploy)
**Ở đâu:** theo design (PN021), clawback **policy/waiver** là **SA-side** — stgsa → Partners → Commission → Commission configuration → **Clawback settings** + **Waiver Review Queue** (không phải trang Commissions của partner portal). Design ready-for-dev.
**Intent:** Display Clawback notification — policy terms + product-failure waiver path hiển thị (thông tin nhạy cảm được mask).
**Lý do block:** View Commission **configuration** phía SA (chứa Clawback settings + Waiver Review Queue) **chưa deploy trên staging** (re-verify 2026-07-30, giống _009/_010: không có entry "View configuration" trên `/partners/commissions`, route config 404). Ghi chú cũ ở đây check nhầm trang partner-portal `/commissions` (tab "Clawback" chỉ filter ledger rỗng) — trải nghiệm clawback-policy/waiver thật là SA-side theo PN021. Unblock khi FE deploy view Commission configuration.
#### PARTNER_UI_COMMISSIONS_008 — BLOCKED (feature Blazey AI)
**Intent:** Hỏi trợ lý AI Blazey câu về commission → nhận trả lời đúng ngữ cảnh (deal/tier/rate của chính partner, không lộ partner khác) kèm next-step actionable.
**Lý do block:** Phụ thuộc **Blazey AI assistant** (feature AI defer) + data commission context thật. Assistant chưa có/không test được trên build hiện tại, ledger rỗng (không có context). Unblock khi Blazey ra + có commission data.
#### PARTNER_UI_COMMISSIONS_009 — BLOCKED (không tìm thấy UI) — Security
**Intent:** Sửa payout/banking details theo region → chỉ hiện payment methods đúng region; dữ liệu nhạy cảm được mask.
**Lý do block:** Không tìm thấy UI edit payout/banking details trên build partner — `/commissions` chỉ là ledger read-only; màn payout-details/settings (theo region) chưa định vị được. Cần UI payout-details + region fixtures. Unblock khi có màn payout-details.
#### PARTNER_UI_COMMISSIONS_010 — BLOCKED (không có commission data + không có UI process-clawback)
**Intent:** Process clawback commission khi client churn trong clawback window → commission bị điều chỉnh thành Clawback, partner được notify, và có product-failure waiver path.
**Lý do block:** Verify live 2026-07-31 (SA commission ledger, stgsa `/partners/commissions`): ledger **rỗng** ("No Data Found", 0 commission) nên không có commission để clawback, và **không có action process-clawback** trên UI (chỉ có summary card "Clawback Exposure" + tab filter status Clawback — không có control "process clawback" theo row; design PN013 chưa deploy). Cần chuỗi đầy đủ — rate config → deal approve (bị BUG-UI-005) → deal Won → commission — + UI process-clawback. Unblock khi có commission client-churn + UI process-clawback deploy.
#### PARTNER_UI_COMMISSIONS_011 — BLOCKED (cần reseller partner + Won reseller deal)
**Intent:** Với reseller deal đã Won, commission hiện **rate reseller** (không phải referral/co-sell), nhãn ghi rõ reseller.
**Lý do block:** Cần **partner type Reseller** có **Won reseller deal** + reseller rate cấu hình. Partner test là Channel, wizard fix deal type Referral, chưa có rate/Won deal → không có commission reseller để kiểm. Unblock với reseller partner + Won reseller deal + rate.
#### PARTNER_UI_COMMISSIONS_012 — BLOCKED (cần reseller partner + Won reseller deal)
**Intent:** Khi reseller deal close, invoice xuất **cho partner entity** (không phải end-client); số tiền = reseller rate × deal value; không lộ billing của end-client.
**Lý do block:** Cùng phụ thuộc reseller — cần reseller partner + Won reseller deal đã qua commission processing, + UI invoice/billing (chưa thấy trên build partner). Unblock với reseller data + UI invoice.
### UI · DASHBOARD

#### PARTNER_UI_DASHBOARD_001
**Mô tả test:** Shell partner load được cho user channel-partner và mặc định vào Dashboard. Xác nhận shell chrome (brand + nav + profile), nav chỉ dành cho partner (không lộ route SA/tenant-only), và Dashboard load không có banner lỗi/authorization.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; điều hướng về root portal `/` (Dashboard là trang mặc định) và chờ READY_MARKER "Tier & Performance".
**Các bước:**
1. Shell chrome partner render.
   → Expected: brand "PARTNER PORTAL", ≥5 link nav sidebar, và control "Open profile menu" hiển thị.
2. Chỉ nav partner được expose.
   → Expected: có route partner `/dashboard`, `/deals`, `/commissions`; KHÔNG có route SA/tenant-only (`/tenants`, `/billing`, `/plans`, `/partners`, `/connectors`, `/auditLog`).
3. Dashboard content load không banner lỗi/authorization.
   → Expected: không có "Something went wrong" / "not authorized" / "Unauthorized" / "403" / "Access denied"; panel "Tier & Performance" hiển thị trong `<main>`.
**Expected (tổng):** Shell partner load cho channel partner với Dashboard active, chỉ nav partner-scoped, không banner lỗi/auth.
**Ghi chú:** PASSED — verified 2026-07-28 (TC 12060401). Test shell kiểu access-control: chứng minh portal partner chỉ expose route partner và Dashboard là trang landing mặc định. Negative: N/A — assertion access-control đã nhúng sẵn (assert route SA-only vắng mặt). Idempotency: N/A — view read-only.
#### PARTNER_UI_DASHBOARD_002
**Mô tả test:** Mở Dashboard partner và xác nhận KPI metric card + các section panel render. Read-only: hoạt động với data rỗng (value có thể 0 / USD 0) — kiểm card render, không phụ thuộc con số cụ thể.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; mở `/dashboard` qua shell và chờ READY_MARKER "Tier & Performance".
**Các bước:**
1. KPI card render, mỗi cái có metric value.
   → Expected: **Total pipeline ACV**, **Commission YTD**, **Active Tenants** đều hiển thị value (vd "USD 0" / 0).
2. Các section chính render.
   → Expected: **Tier & Performance**, **Territory Assignments**, **Action Required**, **Pipeline Snapshot** hiển thị.
**Expected (tổng):** Dashboard render KPI metric card + tất cả section chính (không phụ thuộc data).
**Ghi chú:** PASSED — verified 2026-07-28 (TC 12060402). Content-test DASHBOARD đầu tiên — dựng nền page-object `DashboardPage` (KPI cards, sections). Data partner rỗng hiện "No Data Found" ở Action Required / Pipeline Snapshot. Negative: N/A — view read-only. Idempotency: N/A.
#### PARTNER_UI_DASHBOARD_003
**Mô tả test:** Component Tier Progress trên dashboard hiển thị tiến độ lên tier tiếp theo. Read-only.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; mở `/dashboard` và chờ READY_MARKER "Tier & Performance".
**Các bước:**
1. Tier Progress hiển thị current tier + "working towards" next tier + current ARR.
   → Expected: "Tier Progress" có; **current tier** (SELECT/ADVANCED/PREMIER), copy **"Working towards \<next tier\>"**, và **T12M ARR** hiển thị.
2. Progress metrics hiển thị.
   → Expected: **số deal** và **Win rate** hiển thị trong panel tier progress.
**Expected (tổng):** Tiến độ lên tier tiếp theo hiển thị (current tier + next-tier copy + ARR + metrics).
**Ghi chú:** PASSED — verified 2026-07-28 (TC 12060403; current=SELECT, working towards ADVANCED, ARR USD 0). **Plan-vs-live:** plan còn liệt kê **threshold target**, **progress bar**, **remaining delta** — build này KHÔNG render (không có element `role=progressbar`, không có text threshold/remaining); chỉ hiển thị current tier + next-tier copy + ARR + deals/win-rate. Test assert đúng cái UI render. Negative: N/A — view read-only. Idempotency: N/A.
#### PARTNER_UI_DASHBOARD_004 — BLOCKED
**Intent:** Render — list Action Required CÓ pending tasks để partner thấy next actions (mỗi item có client/deal name, urgency/status, và action control).
**Lý do block:** Không có fixture / đường seed để list Action Required khác rỗng. Partner test (channel-partner) data rỗng — section render empty-state graceful ("Action Required · No Data Found · Looks like there's nothing here yet"). Item Action-Required là DERIVED (renewal đến hạn, deal cần partner xử lý); không có API partner-side để seed, và các deal QA-AUTO đang có (chờ SA duyệt) không surface vào đây. Positive "has pending tasks" chưa verify được cho tới khi có partner account có action item thật (hoặc seed hook). Xem lại khi có partner data đầy đủ.
#### PARTNER_UI_DASHBOARD_005 — FAILED (by design · BE gap)
**Mô tả test:** Tier-qualification math trên dashboard — theo PRD §2.1/§4.3, component Tier Progress phải hiển thị **T12M ARR threshold target** của tier kế, **remaining delta** để đạt, và **progress bar**, bên cạnh current tier + ARR.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; mở `/dashboard` và chờ READY_MARKER "Tier & Performance"; định vị component Tier Progress.
**Các bước:**
1. Current tier + current T12M ARR hiển thị (baseline).
   → Expected: current tier (SELECT/ADVANCED/PREMIER) + "T12M ARR" hiển thị. **(PASS — build có render.)**
2. Next-tier T12M ARR threshold target + remaining delta hiển thị.
   → Expected: có figure threshold/target/remaining hướng tới tier kế. **(FAIL — không render.)**
3. Progress bar hướng tới threshold hiển thị.
   → Expected: có element `role=progressbar` / `<progress>`. **(Sẽ FAIL — không render.)**
**Expected (tổng):** Threshold + remaining delta + progress bar của tier-qualification hiển thị.
**Ghi chú:** FAILED by design (`be_gap`) — verified 2026-07-28 (TC 12060405). Build hiện chỉ render current tier, copy "Working towards \<next tier\>", current ARR (USD 0), và deal/win-rate ("0/0 deals") — KHÔNG render bất kỳ ARR threshold, remaining-delta, hay progress bar (không có `role=progressbar`). Assertion fail với "confirm with BE". Bổ trợ cho DASHBOARD_003 (chỉ assert cái UI *có* render); TC này ghim phần tier-qualification math còn thiếu như một gap được track. Loại khỏi merge gate (`be_gap`). Negative: N/A — view calc read-only. Idempotency: N/A.
#### PARTNER_UI_DASHBOARD_006 — BLOCKED (cần fixture trạng thái downgrade)
**Intent:** Cảnh báo **tier downgrade pending** — dashboard hiện notice 30 ngày + thông tin grace-quarter (PRD §2.1/§5.5).
**Lý do block:** Partner test không ở trạng thái **tier-downgrade-pending**, và không có đường seed (downgrade suy ra từ T12M ARR tụt dưới threshold của tier hiện tại qua 1 grace quarter). Không có partner ở trạng thái đó → không trigger/verify được notice 30 ngày + grace quarter. Cũng phụ thuộc tier-qualification math mà _005 đã cho thấy UI chưa render đủ. Unblock với partner fixture ở trạng thái downgrade-pending (+ UI cảnh báo).
#### PARTNER_UI_DASHBOARD_007 — PASSED
**Mô tả test:** (Negative guard) Dashboard ẩn vanity metrics — theo PRD §4.3, view dashboard đầu tiên chỉ hiển thị giá trị actionable/decision-supporting (pipeline ACV, commission, active tenants, tier progress, action items, pipeline snapshot) và KHÔNG surface vanity metric (page/profile views, impressions, followers, bounce rate, login count, …).
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; mở `/dashboard` và chờ READY_MARKER "Tier & Performance".
**Các bước:**
1. Chỉ KPI metric actionable/decision-supporting hiển thị.
   → Expected: Total pipeline ACV, Commission YTD, Active Tenants hiển thị.
2. Không có vanity metric non-actionable.
   → Expected: không có {page views, profile views, impressions, followers, bounce rate, time on page, click-through, logins, vanity} trong `<main>`.
3. Hierarchy trang vẫn highlight các section actionable.
   → Expected: Action Required, Tier Progress, Pipeline Snapshot hiển thị.
**Expected (tổng):** Dashboard chỉ surface metric actionable + hierarchy action/tier/pipeline; vanity metric bị ẩn.
**Ghi chú:** PASSED — TC 12060407, verified 2026-07-30 (chạy xanh khi staging hồi; "pending verify" trước đó là do staging MFE outage tạm thời 2026-07-28, không phải lỗi test). Negative TC by design (guard vắng mặt vanity metric); đây chính là negative counterpart. Idempotency: N/A — view read-only.
#### PARTNER_UI_DASHBOARD_008 — BLOCKED (feature Blazey AI)
**Intent:** Hỏi Blazey (widget trên dashboard) câu **status deal** → trả lời gồm stage hiện tại, next action, contact của BlazeUp rep; scope đúng deal của partner đang login.
**Lý do block:** Phụ thuộc **Blazey AI assistant** (feature AI defer) — widget chưa có/không test được trên build hiện tại — + cần deal data thật. Unblock khi Blazey ra + partner có deal.
#### PARTNER_UI_DASHBOARD_009 — BLOCKED (feature Blazey AI)
**Intent:** Hỏi Blazey câu **tier projection** ("cần thêm bao nhiêu ARR để lên Premier?") → trả lời gồm current tier, T12M ARR, ARR gap tới tier kế, và timeline ước tính; số khớp tier progress bar.
**Lý do block:** Giống _008 — phụ thuộc Blazey AI (defer) + tier data. Lưu ý các số tier-qualification (threshold/gap) nó cần cũng chính là phần _005 cho thấy UI chưa render đủ. Unblock khi Blazey ra.
### UI · MY_CLIENTS

**Cả module BLOCKED — chưa deploy trên partner portal** (re-verify live 2026-07-30, probe kỹ: login sạch + wait đủ). Nav partner có 6 mục — Dashboard, Deals, Commissions, Directory, Resources, My Apps — **không có "My Clients"**; `/clients` và `/my-clients` **không render** `<main>`; `/apps` là trang "My Apps" submit app (Draft/Certified/Published…), không phải client management. Trải nghiệm quản lý client post-close (list / health / renewal / MSP provisioning / expansion) mà các TC mô tả chưa build/expose trên build này. Ngoài ra: nhiều TC cần **client data thật** (deal đã close → client) mà partner test chưa có, và _010/_012/_013 phụ thuộc **Blazey AI** (defer). Unblock khi module My Clients deploy (nav + trang) + có ít nhất 1 client từ deal đã close.
- PARTNER_UI_MY_CLIENTS_001 — BLOCKED (CTA renewal ở Action Required mở flow renewal: module chưa deploy)
- PARTNER_UI_MY_CLIENTS_002 — BLOCKED (mở My Clients → list client post-close: module chưa deploy)
- PARTNER_UI_MY_CLIENTS_003 — BLOCKED (client health detail: ARR/renewal/usage/tickets/CSM — module chưa deploy + cần client data)
- PARTNER_UI_MY_CLIENTS_004 — BLOCKED (đăng ký renewal deal từ client detail, prefill: module chưa deploy)
- PARTNER_UI_MY_CLIENTS_005 — BLOCKED (thêm MSP managed client → form provisioning: module chưa deploy)
- PARTNER_UI_MY_CLIENTS_006 — BLOCKED (Security: MSP ticket consent mặc định OFF: module chưa deploy)
- PARTNER_UI_MY_CLIENTS_007 — BLOCKED (filter "Renewal This Quarter": module chưa deploy + cần client data)
- PARTNER_UI_MY_CLIENTS_008 — BLOCKED (filter "Health At Risk": module chưa deploy + cần client data)
- PARTNER_UI_MY_CLIENTS_009 — BLOCKED (search client theo tên: module chưa deploy + cần client data)
- PARTNER_UI_MY_CLIENTS_010 — BLOCKED (Blazey client insight / adoption recommendation: module chưa deploy + Blazey AI defer)
- PARTNER_UI_MY_CLIENTS_011 — BLOCKED (đăng ký expansion deal từ My Clients, prefill client: module chưa deploy)
- PARTNER_UI_MY_CLIENTS_012 — BLOCKED (Blazey client insight: module chưa deploy + Blazey AI defer)
- PARTNER_UI_MY_CLIENTS_013 — BLOCKED (Blazey client insight: module chưa deploy + Blazey AI defer)
### UI · MY_PIPELINE

#### PARTNER_UI_MY_PIPELINE_001
**Mô tả test:** Wizard Register-a-Deal, bước 1: nhập company details hợp lệ → wizard sang bước tiếp theo và giữ nguyên dữ liệu đã nhập. Chỉ thao tác modal (mở → điền → advance → back); không submit nên không tạo deal.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner; mở `/deals`; click "Register a deal" mở wizard (mở ở "Step 1 of 3 — Register company").
**Các bước:**
1. Nhập company details (name, domain, country) + primary contact (name, email), rồi verify mỗi field giữ đúng giá trị đã nhập.
   → Expected: mỗi field **echo** đúng giá trị nhập (company name, domain, contact name, email — không bị mutate/clear), country đã chọn, và — khi đủ required — "Next" **enabled**. ("Hợp lệ" ở đây = đủ required + field echo đúng; build này không format-check field — gap đó là _003.)
2. Click Next.
   → Expected: wizard sang **Step 2 of 3 (Deal info)** và nội dung Deal-info render (field chỉ có ở step 2, vd "Expected close date", hiển thị — chứng minh đã sang đúng Deal info, không chỉ đổi counter). Kiểm sâu các field Deal-info là _008–_012.
3. Back về bước 1.
   → Expected: về Step 1 of 3 và **company name được giữ nguyên**.
**Expected (tổng):** Bước 1 hợp lệ đưa wizard tiến tới và dữ liệu được giữ qua các bước.
**Ghi chú:** PASSED — verified 2026-07-24 (TC 12060201). **Plan-vs-live:** plan ghi "advances to the contact step", nhưng wizard thật đặt primary contact NGAY trong bước 1 ("Register company"); bước 1 hợp lệ → sang bước 2 ("Deal info"). Validation bằng cách **disable "Next"** cho tới khi đủ required (build này không có inline error text). Không dính bug deals-list (_024/_025) — wizard là modal độc lập. Negative counterpart: **_002**. Idempotency: N/A — điều hướng modal, không submit/tạo.

#### PARTNER_UI_MY_PIPELINE_002
**Mô tả test:** Đối trọng negative của _001: để trống required **company name** → wizard bị chặn tiến bước; điền vào thì bỏ chặn — chứng minh company name là required.
**Chuẩn bị (điều kiện tiên quyết):** Mở `/deals`; mở wizard Register-a-Deal (Step 1 of 3).
**Các bước:**
1. Điền mọi field required KHÁC (domain, country, contact name, email) và CHỈ để trống company name.
   → Expected: xác nhận company field trống trong khi các field khác giữ giá trị; "Next" giữ **disabled** và wizard vẫn ở Step 1 of 3 — nên việc bị chặn quy **chỉ** do thiếu company name.
2. Điền company name.
   → Expected: "Next" thành **enabled** (company name là field required đang chặn).
**Expected (tổng):** Thiếu required (company name) chặn advance; điền vào cho phép advance.
**Ghi chú:** PASSED — verified 2026-07-24 (TC 12060202). **Plan-vs-live:** plan ghi "required field error is shown", nhưng build này KHÔNG có inline error text — nó enforce required bằng cách **disable "Next"**, nên test assert chuyển đổi disabled→enabled thay vì error message. Idempotency: N/A (validation negative, không submit).
#### PARTNER_UI_MY_PIPELINE_003
**Mô tả test:** Negative (fail-by-design): domain không hợp lệ/malformed trong register wizard phải bị từ chối với domain-format error (chặn advance hoặc flag field). Tất cả case đều chạy (thu thập).
**Chuẩn bị (điều kiện tiên quyết):** Mở wizard Register-a-Deal (bước 1) với company name, country, primary contact hợp lệ; chỉ thay đổi field Domain.
**Các bước:** (mỗi case = nhập domain malformed, blur, kiểm tra bị từ chối)
1. `@@@` → Expected: bị từ chối (Next disabled hoặc field flagged). **Hiện FAIL** — được chấp nhận (Next vẫn enabled, field không flag).
2. `ab cd` (có space) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận.
3. `notadomain` (không TLD) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận.
4. `http://x.com` (có scheme, không phải bare domain) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận.
**Expected (tổng):** Domain malformed bị từ chối với format error rõ ràng; không tạo deal.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate) — verified 2026-07-24 (TC 12060203). Register wizard **không validate domain format**: mọi domain malformed (kể cả `@@@` / `ab cd`) đều được chấp nhận — field Domain **giữ nguyên giá trị rác**, "Next" vẫn enabled, và field không bao giờ bị flag (`aria-invalid` không set), nên deal có thể tiếp tục với domain rác (mà domain "derive tenant subdomain"). **Confirm với FE** — thêm validate domain-format ở field Domain. Positive sibling: _001. Idempotency: N/A (không submit).
#### PARTNER_UI_MY_PIPELINE_004
**Mô tả test:** Trong register wizard, nhập domain (subdomain label) đã bị reserve bởi 1 deal active khác → hiện inline warning active-account/conflict; domain free → không warning. Chỉ UI (không submit).
**Chuẩn bị (điều kiện tiên quyết):** Chứng minh qua API partner `check-domain` label ứng viên nào reserved (`available=false`) vs free (`available=true`) — để assertion UI không vòng vo. Mở wizard với company/country/contact hợp lệ. LƯU Ý: field "Domain" là **subdomain label** (lowercase/số/gạch nối, KHÔNG dấu chấm) — placeholder "acme.com" gây nhầm; giá trị có dấu chấm → check-domain trả 400.
**Các bước:**
1. Nhập domain RESERVED (đã chứng minh `available=false`, vd "test").
   → Expected: hiện inline warning, vd **"This domain is reserved by another active deal. Register will get a conflict queue."** (Next vẫn enabled — deal sẽ vào conflict queue khi submit, không bị chặn.)
2. Nhập domain AVAILABLE (đã chứng minh `available=true`) — control.
   → Expected: không có warning reserved/active-deal.
**Expected (tổng):** Domain reserved hiện inline warning active-account/conflict; domain free thì không.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060204). Khi blur, field gọi `GET /v1/partner/portal/check-domain?domain=<label>`; `available=false` (reason vd `deal_won`) trigger warning inline. Trạng thái reserved/free được chứng minh qua API trước (không vòng vo). Nếu không có label reserved nào trong danh sách ứng viên, test SKIP với lý do rõ (không false-pass). Kết quả submit → conflict-queue là _005. Negative/control: nhánh domain available (không warning) đã bao gồm. Idempotency: N/A (read-only check).
#### PARTNER_UI_MY_PIPELINE_005
**Mô tả test:** Submit toàn bộ register wizard với domain đã reserved (nhánh conflict). Điền hết các bước (company + contact + domain reserved; deal info: plan / seats / region / expected close date) rồi submit; deal được tạo (sẽ vào conflict queue).
**Chuẩn bị (điều kiện tiên quyết):** Chứng minh qua API `check-domain` 1 label reserved (available=false). Mở wizard.
**Các bước:**
1. Step 1 với domain RESERVED → hiện inline warning conflict ("reserved by another active deal … conflict queue"); advance.
   → Expected: warning hiện; wizard sang Deal info.
2. Điền Deal info — plan (billing cycle tự set), granted seats, region, expected close date (tháng sau) → sang Summary.
   → Expected: Deal info đủ → "Next" enabled; wizard tới Step 3 of 3 (Summary).
3. Submit.
   → Expected: submit thành công — `POST /v1/partner/portal/deals` trả **201** + deal id.
**Expected (tổng):** Wizard submit e2e với domain reserved và deal được tạo.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060205). Full e2e submit chạy được: reserved-domain warning → Deal info → **submit → 201** (deal id đã log trong run để tra tay). **PENDING (bước verify — cố ý CHƯA assert):** xác nhận deal thực sự VÀO conflict queue được hoãn — endpoint deals-list partner đang 400 (`_024`) nên deal không list được, và không có API xóa để dọn deal vừa tạo. **Sẽ improve khi BE cung cấp cách fetch/remove deal** (user đang làm việc với BE). Side-effect: mỗi run tạo 1 deal không xóa được. Negative/phát hiện-conflict đã cover ở _004 (UI warning) + API `2060204`. Idempotency: N/A ở đây (duplicate-register là _022).
#### PARTNER_UI_MY_PIPELINE_006
**Mô tả test:** Negative (required): để trống **email** primary-contact → chặn wizard advance; điền email hợp lệ → bỏ chặn — chứng minh email là required.
**Chuẩn bị (điều kiện tiên quyết):** Mở wizard (Step 1); điền mọi field required khác (company name, domain, country, contact name).
**Các bước:**
1. Để trống contact email (các field khác đã điền).
   → Expected: xác nhận email trống trong khi field khác giữ giá trị; "Next" giữ **disabled** — chặn quy chỉ do thiếu email.
2. Điền email hợp lệ.
   → Expected: "Next" thành **enabled**.
**Expected (tổng):** Email required trống chặn advance; email hợp lệ cho advance.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060206). Cùng cơ chế _002: required enforce bằng disable "Next" (không inline error). Idempotency: N/A (validation, không submit).

#### PARTNER_UI_MY_PIPELINE_007
**Mô tả test:** Negative (fail-by-design): **email** contact malformed phải bị từ chối với format error (chặn advance hoặc flag field). Tất cả case đều chạy (thu thập).
**Chuẩn bị (điều kiện tiên quyết):** Mở wizard (Step 1) với company/domain/country/contact-name hợp lệ; chỉ thay đổi email.
**Các bước:** (mỗi case = nhập email malformed, blur, kiểm bị từ chối)
1. `notanemail` (không @) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận (field giữ giá trị, Next enabled, không flag).
2. `abc@` (không domain) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận.
3. `abc@x` (không TLD) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận.
4. `a b@x.com` (có space) → Expected: bị từ chối. **Hiện FAIL** — được chấp nhận.
**Expected (tổng):** Email malformed bị từ chối với format error rõ ràng; không tạo deal.
**Ghi chú:** PASSED — verify lại 2026-08-10 (TC 12060207); trước đây FAILED có chủ đích (`be_gap`, **BUG-UI-004**, nay đã Closed). FE đã bổ sung validation, nên marker `be_gap` được gỡ và TC này quay lại trong merge gate. Gap gốc, giữ lại để tra cứu: Register wizard **không validate email format**: mọi email malformed (kể cả `notanemail` / `a b@x.com` có space) đều được chấp nhận — field giữ giá trị, "Next" vẫn enabled, field không bao giờ bị flag (`aria-invalid` không set). Cùng loại gap với _003 (domain). **Confirm với FE** — thêm validate email-format ở field contact email. Positive sibling: _001. Idempotency: N/A (không submit).
#### PARTNER_UI_MY_PIPELINE_008
**Mô tả test:** Chọn referral deal type: trên wizard này deal type là Referral (mặc định) và persist tới Summary. Chỉ UI (không submit).
**Chuẩn bị (điều kiện tiên quyết):** Mở wizard; hoàn tất step 1 (company/domain/country/contact).
**Các bước:**
1. Ở Deal info, deal type hiển thị **Referral** (Reseller/Co-sell không có — xem _009/_010).
   → Expected: "Referral" hiển thị; không có option "Reseller".
2. Hoàn tất Deal info (plan/seats/region/date) → sang Summary.
   → Expected: tới Step 3 of 3 (Summary).
3. Summary persist deal type.
   → Expected: Summary hiển thị **Deal type = Referral**.
**Expected (tổng):** Referral deal type được capture và persist qua navigation tới Summary.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060208). Trên build này deal type là **badge "Referral" read-only cố định** (reseller/co-sell KHÔNG chọn được — click không mở gì, không có dropdown deal-type, không có text "Reseller"/"Co-sell"). Referral implies direct billing model (nghiệp vụ); UI chỉ hiển thị nhãn "Referral" (không có chữ "direct billing" riêng). Không submit → không side-effect. Idempotency: N/A.

#### PARTNER_UI_MY_PIPELINE_009
**Ghi chú (BLOCKED):** Chọn reseller deal type → reseller billing path. Blocked (verify live 2026-07-27): register wizard **không có reseller deal type** — deal type là badge "Referral" read-only cố định (không có dropdown deal-type; click không mở gì; không có text "Reseller"). Không có control UI để chọn reseller, nên không thể exercise reseller billing path từ wizard. (API hỗ trợ dealType `reseller` — xem `make_deal` / API deal TCs — nên đây là gap UI.) Unblock khi wizard có deal-type selector với reseller.

#### PARTNER_UI_MY_PIPELINE_010
**Ghi chú (BLOCKED):** Chọn co-sell deal type → co-sell option captured. Blocked (verify live 2026-07-27): giống _009 — deal type wizard là badge "Referral" read-only không có selector; "Co-sell" không có trong UI. Không có control chọn co-sell. (API hỗ trợ `co_sell`.) Unblock khi wizard có deal-type selector với co-sell.
#### PARTNER_UI_MY_PIPELINE_011
**Mô tả test:** Summary review (step 3) hiển thị tất cả data đã nhập. Điền wizard với giá trị unique biết trước (company / domain / contact name / email) + deal info, tới Summary, xác nhận mọi giá trị nhập được hiển thị để review. Verify ở Summary (trước submit); không submit → không tạo deal.
**Chuẩn bị (điều kiện tiên quyết):** Mở wizard; điền step 1 (company/domain/country/contact) + Deal info (plan/seats/region/expected close date) với data biết trước.
**Các bước:**
1. Summary hiển thị các giá trị COMPANY + CONTACT đã nhập.
   → Expected: company name, domain, contact name, email (unique) đều hiển thị trên Summary.
2. Summary hiển thị các field phần DEAL.
   → Expected: Deal type = **Referral**, cùng Expected close date, Plan source, Country.
**Expected (tổng):** Summary phản ánh mọi giá trị đã nhập để review trước khi submit.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060211). Dùng 4 text input unique (company/domain/contact/email) assert verbatim trên Summary → bằng chứng mạnh data nhập được hiển thị. Verify trước submit (không submit → không side-effect). Idempotency: N/A.
#### PARTNER_UI_MY_PIPELINE_012
**Mô tả test:** Performance — đăng ký deal hợp lệ trả success response trong 2 giây. Submit toàn bộ wizard với domain hợp lệ (available) và đo round-trip mạng của API register.
**Chuẩn bị (điều kiện tiên quyết):** Mở wizard; điền step 1 (company/domain/country/contact) + Deal info (plan/seats/region/expected close date) với domain unique available.
**Các bước:**
1. Submit deal.
   → Expected: `POST /v1/partner/portal/deals` trả **2xx** (201) + deal id.
2. Đo response time.
   → Expected: round-trip request→response **< 2000 ms** (đo từ network timing: responseEnd − requestStart; không tính UI render).
**Expected (tổng):** Đăng ký hợp lệ thành công và API trả về trong budget 2s.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060212; quan sát ~642 ms). Đo round-trip API register (server + network), không tính UI render. Side-effect: submit tạo 1 deal thật (không có API xóa — xem _005; deal id đã log trong run). Staging chậm có thể vượt 2s → chạy lại trước khi file perf bug. Idempotency: N/A ở đây (duplicate-register là _022).
#### PARTNER_UI_MY_PIPELINE_013
**Mô tả test:** Performance/mobile — luồng đăng ký deal hoàn tất dưới 90 giây trên mobile viewport (375×812). Hoàn tất toàn bộ wizard + submit ở kích thước mobile, đo tổng thời gian flow (mở wizard → submitted).
**Chuẩn bị (điều kiện tiên quyết):** Resize page về 375×812; mở wizard.
**Các bước:**
1. Ở mobile, điền step 1 (company/domain/country/contact) và advance.
2. Điền Deal info (plan/seats/region/expected close date) và sang Summary.
3. Submit → register thành công và cả flow hoàn tất trong budget.
   → Expected: `POST /v1/partner/portal/deals` 2xx (201); thời gian từ mở wizard tới success response **< 90 s**.
**Expected (tổng):** Đăng ký hoàn tất được trên mobile trong 90 giây.
**Ghi chú:** PASSED — verified 2026-07-27 (TC 12060213; quan sát ~6 s, thừa dưới 90 s). Mọi control wizard (dropdown, date picker, submit) chạy được ở 375×812. Side-effect: submit tạo 1 deal thật (không có API xóa — xem _005; deal id đã log). Login UI partner có thể flaky (login page render chậm) → run có thể BLOCK do login timeout; chạy lại. Idempotency: N/A.
#### PARTNER_UI_MY_PIPELINE_014
**Mô tả test:** Mở My Pipeline (trang Deals) và xác nhận tất cả deal stage + count hiển thị — pipeline hiện 6 stage tab (All / Pending / Approved / Won / Lost / Expired), mỗi tab có count dạng số, cùng summary pipeline và nút Register. Read-only: hoạt động cả khi pipeline rỗng (count có thể = 0) — kiểm tra stage RENDER, không phụ thuộc dữ liệu cụ thể.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập một lần bằng user channel-partner; mở `/deals` qua shell và chờ READY_MARKER "Deal Pipeline".
**Các bước:**
1. Cả 6 stage tab hiển thị.
   → Expected: All, Pending, Approved, Won, Lost, Expired đều render (role=tab).
2. Mỗi stage tab hiển thị count dạng số.
   → Expected: mỗi tab có số nguyên ≥ 0 (vd "All 0").
3. Summary pipeline + nút Register hiển thị.
   → Expected: summary "… deals in your pipeline" và nút "Register a deal" hiển thị.
**Expected (tổng):** Pipeline render đủ 6 stage + count + summary + Register CTA (không phụ thuộc số deal đang có).
**Ghi chú:** PASSED — verified 2026-07-24 (TC 12060214). Cả 6 stage render với count (0 trên pipeline test rỗng); summary + Register hiển thị. Content-test MY_PIPELINE đầu tiên — dựng nền page-object `DealsPage` (stage tabs, counts, controls) để các TC filter/card sau (_024/_025/_026/_027/_033) dùng lại. Negative: N/A — view read-only không có bề mặt input sai. Idempotency: N/A — read-only (không tạo gì).
- PARTNER_UI_MY_PIPELINE_015 — BLOCKED (deal detail timeline / approval history: deals-list 400 "Invalid id: 'pro-v1'" → pipeline rỗng, không có deal để mở; cùng BE defect với _024)
- PARTNER_UI_MY_PIPELINE_016 — BLOCKED (accept co-sell override proposal: wizard không cho chọn co-sell + cần proposal; feature absent)
- PARTNER_UI_MY_PIPELINE_017 — BLOCKED (Negative: co-sell override ≤ $100K không khả dụng: co-sell không có trên UI)
- PARTNER_UI_MY_PIPELINE_018 — BLOCKED (co-sell override > $100K yêu cầu written agreement: co-sell không có trên UI)
- PARTNER_UI_MY_PIPELINE_019 — BLOCKED (enrich khi blur domain hợp lệ: không có feature enrichment — verify live 2026-07-30, Headcount là dropdown "Select range" nhập tay + Logo là ô URL nhập tay; blur chỉ derive subdomain)
- PARTNER_UI_MY_PIPELINE_020 — BLOCKED (chọn modules of interest: wizard không có bước chọn modules — verify live 2026-07-30, step 2 chỉ có deal type/plan/seats/region/close date)
- PARTNER_UI_MY_PIPELINE_021 — BLOCKED (đăng ký lại conflict-lost prospect sau 90 ngày: cần deal conflict-lost aged 90 ngày — data theo thời gian, không có)
- PARTNER_UI_MY_PIPELINE_022 — BLOCKED (Negative: không partner nào đăng ký → commission không award: outcome behavior/backend, không có action UI partner để test)
- PARTNER_UI_MY_PIPELINE_023 — BLOCKED (reseller deal → ô end-client price vắng mặt: wizard không cho chọn reseller; feature absent)
#### PARTNER_UI_MY_PIPELINE_024
**Ghi chú (BLOCKED):** Click deal card trong pipeline để mở deal detail. Bị chặn bởi BE defect (verify live 2026-07-24): endpoint danh sách deals partner-portal `GET /v1/partner/portal/deals` trả **400 "Invalid id: 'pro-v1'"**, nên pipeline **không bao giờ render deal row/card** (UI fallback về empty-state "No deals found" kể cả khi partner CÓ deal). Root cause = contract drift tham chiếu plan: deal cũ lưu **slug** (`planId:"pro-v1"`) trong khi BE giờ resolve plan bằng Mongo **_id** (ObjectId), nên list partner có deal tham chiếu slug → "Invalid id" → cả list vỡ. Đã xác nhận deal SA vừa register cho partner vẫn không hiện (list giữ 400 ~40s). Không có card để click → không thể thực hiện luồng "mở deal detail". **Bug này chặn luôn các TC deal-list/detail khác** (_015 detail, _025/_026/_027 filter, _033 card tag). Unblock khi BE fix endpoint deals-list (tha/migrate plan-ref slug cũ, hoặc resolve bằng _id) để pipeline render card. **Liên quan:** register giờ cần plan **_id** (slug → 400) — đã cập nhật `pick_billing_plan_id`.
#### PARTNER_UI_MY_PIPELINE_025
**Ghi chú (BLOCKED):** Filter deals theo company text để hiển thị deal khớp. Bị chặn bởi cùng BE defect với _024 (verify live 2026-07-24): endpoint deals-list `GET /v1/partner/portal/deals` trả **400 "Invalid id: 'pro-v1'"** — và biến thể search `?search=QA` cũng trả **cùng 400** (filter đi qua cùng endpoint). List vỡ nên không deal nào render → không thể verify "deal khớp được hiển thị". Unblock cùng _024 (BE phải fix endpoint deals-list để tha/resolve plan-ref slug cũ).
- PARTNER_UI_MY_PIPELINE_026 — BLOCKED (filter theo deal type: deals-list 400 → pipeline rỗng; có nút Filter nhưng 0 deal không verify được kết quả lọc; cùng BE defect _024/_025)
- PARTNER_UI_MY_PIPELINE_027 — BLOCKED (filter theo module: cùng deals-list 400 + không có concept "module" trong deal model/wizard)
- PARTNER_UI_MY_PIPELINE_028 — BLOCKED (add shared note vào deal: không có deal detail — deals-list 400, pipeline rỗng, không có deal để mở)
- PARTNER_UI_MY_PIPELINE_029 — BLOCKED (upload document vào deal: không có deal detail — như _028)
- PARTNER_UI_MY_PIPELINE_030 — BLOCKED (xem BlazeUp rep được assign: rep assign khi SA approve (bị BUG-UI-005) + deals-list 400, không có deal để mở)
- PARTNER_UI_MY_PIPELINE_031 — BLOCKED (request gia hạn protection thủ công: cần deal approved có protection clock chạy + deal detail — deals-list 400 / chưa SA approve)
- PARTNER_UI_MY_PIPELINE_032 — BLOCKED (reseller tự mark deal Won: wizard không cho chọn reseller)
- PARTNER_UI_MY_PIPELINE_033 — BLOCKED (card pipeline hiện tag reseller billing: deals-list 400 → không render card + không có reseller)
### UI · PARTNER_PORTAL_SHELL

#### PARTNER_UI_PARTNER_PORTAL_SHELL_001
**Mô tả test:** Mở tất cả route nav chính của shell partner portal và xác nhận mỗi trang render đúng nội dung (đúng page content, không có lỗi micro-frontend). Một test lặp đi qua tất cả trang bằng URL trực tiếp và thu thập failure → một verdict duy nhất nêu trang nào lỗi.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập một lần bằng user channel-partner đã cấu hình (login UI partner cache theo session). Warm up SPA (mở Dashboard một lần) để trang đầu trong vòng lặp không bị tính chi phí bootstrap một lần.
**Các bước:** (mỗi trang = một `page.goto(route)`; chờ READY_MARKER trong `<main>` — fast-fail nếu hiện panel "Something went wrong" — **rồi** kiểm tra content đã load: không có banner "Failed to load"/"Please refresh and try again" trong `<main>`) — nav chính đã verify live 2026-07-23:
1. Dashboard → `/dashboard` → Expected: title **"Tier & Performance"** hiện + không banner lỗi. → **PASS**
2. Deals → `/deals` → Expected: **"Deal Pipeline"** hiện + không banner lỗi. → **PASS**
3. Commissions → `/commissions` → Expected: **"Commissions"** hiện + không banner lỗi. → **PASS**
4. Resources → `/resources` → Expected: **"Resources"** hiện + không banner lỗi. → **PASS**
5. My Apps → `/apps` → Expected: **"My Apps"** hiện + không banner lỗi. → **FAIL** — shell render được (title "My Apps" + tabs + nút Submit) nhưng data-fetch danh sách apps lỗi, hiện banner đỏ **"Failed to load your apps. Please refresh and try again."**
**Expected (tổng):** Cả 5 trang chính render được module VÀ content (không MFE panel, không banner lỗi content); trang lỗi sẽ fast-fail nêu rõ trang nào.
**Ghi chú:** FAILED (by design) — verified 2026-07-23 (TC 12060101). 4/5 trang pass; **`/apps` (My Apps) FAIL**: shell render được nhưng data-fetch danh sách apps lỗi → banner "Failed to load your apps. Please refresh and try again." (lỗi backend/data-load của trang này — **confirm với BE**). Đã reproduce live, không phải flap một lần. **TC này cũng siết lại readiness check:** chỉ dựa marker (title) cho FALSE PASS vì tiêu đề vẫn render dù data lỗi — đã thêm assertion bắt banner lỗi content sau marker, nhờ đó `/apps` đúng là đỏ. **Mapping plan-vs-live:** plan ghi "My Pipeline / My Clients / Training", nhưng nav chính thực tế là Deals / Resources / My Apps ("My Pipeline" = trang Deals, title "Deal Pipeline"). Test UI partner-portal đầu tiên — tạo bản đồ route live để các content-test sau dùng lại. Negative: N/A (smoke page-load không có bề mặt input sai; case trang lỗi/content-error đã built-in). Idempotency: N/A (điều hướng read-only).
#### PARTNER_UI_PARTNER_PORTAL_SHELL_002
**Mô tả test:** Mở partner portal ở mobile viewport phổ biến (375×812) và xác nhận shell vẫn dùng được trên mọi trang nav chính — trang render, sidebar nav vẫn truy cập được, và layout KHÔNG tràn ngang (không bị cắt nội dung / cuộn ngang) — rồi tap một link sidebar để chứng minh điều hướng mobile hoạt động. Một test lặp thu thập failure theo trang → một verdict.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập một lần bằng user channel-partner đã cấu hình; resize page về 375×812; warm up SPA (mở Dashboard một lần).
**Các bước:** (mỗi trang ở mobile: READY_MARKER hiện + ≥1 nav link hiện + tràn ngang ≤ 5px cho scrollbar) — verify live 2026-07-24:
1. Dashboard `/dashboard` → Expected: render, nav truy cập được, không tràn ngang. → **PASS** (tràn 0px).
2. Deals `/deals` → Expected: không tràn ngang. → **FAIL** — nội dung tràn viewport 375px **+162px** (tabs/filter/nút không fit → cuộn ngang).
3. Commissions `/commissions` → Expected: không tràn ngang. → **PASS** (0px).
4. Resources `/resources` → Expected: không tràn ngang. → **PASS** (0px).
5. My Apps `/apps` → Expected: không tràn ngang. → **FAIL** — tràn **+263px**.
6. Tap link sidebar ở mobile → Commissions điều hướng + render. → **PASS** (nav mobile dùng được).
**Expected (tổng):** Mọi trang chính fit mobile viewport (không tràn ngang) và nav truy cập được; tap nav điều hướng đúng.
**Ghi chú:** FAILED (by design) — verified 2026-07-24 (TC 12060102). 3/5 trang fit + nav mobile hoạt động, nhưng **Deals (+162px) và My Apps (+263px) tràn ngang ở 375px** = lỗi responsive-layout (nội dung không fit màn nhỏ → cuộn ngang; **confirm với FE**). Sidebar mobile vẫn là icon-bar (không ẩn) và tap nav điều hướng đúng, nên bản thân navigation dùng được — lỗi nằm ở độ rộng nội dung trang Deals/My Apps. Đã reproduce live. Negative: N/A (responsive smoke không có bề mặt input sai; case "layout không fit" chính là điều đang kiểm). Idempotency: N/A (điều hướng/resize read-only).
#### PARTNER_UI_PARTNER_PORTAL_SHELL_003
**Ghi chú (BLOCKED):** Partner dual-account chuyển đổi giữa dashboard **Pack** và **Channel**. Không thể tự động hóa — tính năng lẫn test data đều chưa có trên staging (verify live 2026-07-24): (a) **không có account-switcher** trong portal shell — chữ "Select" ở header là badge **tier** (tier=`select`), không phải công tắc đổi account; profile menu chỉ có Profile/Logout; (b) partner đang đăng nhập là **single account** — `GET /v1/partner/auth/me` trả về 1 `partnerId`, `type:"channel"`, `tier:"select"`, không có mảng accounts; (c) **không có khái niệm "Pack"** — enum partner `type` là channel/referral/msp/system_integrator (không có "pack"), nên không thể biểu diễn dual-account Pack↔Channel. Unblock khi BE ship multi-account membership (1 user → 1 account Pack + 1 Channel) + account switcher ở shell, VÀ có test partner dual-account.
### UI · PARTNER_TEAM

**Sửa lại (2026-07-30):** nav partner portal có **6 mục** — Dashboard, Deals, Commissions, **Directory**, Resources, My Apps. Ghi chú cũ ở đây nói sai "5 nav / không có UI team" — đó là false-negative do probe chờ quá ngắn (bài học `probe-mfe-with-long-wait`). `/directory` chính là trang team-members của partner.
#### PARTNER_UI_PARTNER_TEAM_001 — PASSED
**Mô tả test:** Invite partner team member. Trên partner Directory (`/directory`), mở "Invite User", điền email + name + role của member mới, gửi invite, xác nhận invite được tạo (hiện credential 1 lần) và member xuất hiện trong bảng team với role.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập user channel-partner (stgpartners, 2FA); mở `/directory` và chờ READY_MARKER "Directory".
**Các bước:**
1. Bảng member + action Invite User render.
   → Expected: cột MEMBER / ROLE / STATUS / LAST LOGIN + nút "Invite User".
2. Dialog Invite có email + name + role selector.
   → Expected: Email*, First name*, Last name*, Role (mặc định "Viewer") + Send Invite.
3. Gửi invite → confirmation "User invited".
   → Expected: dialog credential ("User invited" — temp password 1 lần) hiện; đóng bằng Done.
4. Member được invite xuất hiện trong Directory với role.
   → Expected: dòng cho email vừa invite hiện role "Viewer", status Active.
**Expected (tổng):** Invite được tạo với role và member mới hiển thị trong Directory.
**Ghi chú:** PASSED — verified 2026-07-30 (TC 12060601). Team management phía partner ở `/directory` (Invite User → email/name/role → Send → credential 1 lần → member Active). Section config mới `PARTNER.ui.PARTNER_TEAM = 6`. Side-effect: mỗi run tạo 1 member Active thật (email `qa.auto+…` unique; UI không có xoá — member tích lũy). Negative: N/A (có thể thêm validation required-field sau). Idempotency: N/A (email unique mỗi run). **Cleanup:** không thể dọn — ngoài việc UI không có control, `sa-partners-api` cũng **không có** endpoint delete/revoke cho partner user (chỉ có cho certifications; đối chiếu `docs/api-snapshots/blazeup/sa-partners-api.endpoints.json`), và member nằm trong org partner DÙNG CHUNG nên không thể xoá bằng đường nào. Mỗi lần chạy log `CLEANUP LEAK` kèm email.
- PARTNER_UI_PARTNER_TEAM_002 — BLOCKED (tạo campaign referral link: không tìm thấy UI referral-link trên `/directory`; feature chưa định vị được trên partner portal — recheck khi có khu referral-link)
- PARTNER_UI_PARTNER_TEAM_003 — BLOCKED (copy referral link: giống trên — không tìm thấy UI referral-link)
### UI · RESOURCES

**Tất cả BLOCKED** — trang Resources có tồn tại nhưng nội dung KHÔNG khớp các TC (verified live 2026-07-29). `/resources` render view read-only **"Commission Rates + Assigned Territories"** (rate theo tier; regions được phép bán) — **không** có demo sandbox, không download marketing-resource, không generator pitch-deck co-branded, không ROI calculator (không có nút action nào). Trải nghiệm demo-sandbox / marketing-assets / pitch-deck / ROI-calculator mà các TC mô tả chưa implement trên build này (có thể bị gate ở tier cao hơn tier Select/Registered của partner test).
- PARTNER_UI_RESOURCES_001 — BLOCKED (demo sandbox reset: không có UI sandbox)
- PARTNER_UI_RESOURCES_002 — BLOCKED (sandbox weekly auto-reset toggle: không có UI sandbox)
- PARTNER_UI_RESOURCES_003 — BLOCKED (download marketing resource: không có UI marketing-assets)
- PARTNER_UI_RESOURCES_004 — BLOCKED (generate co-branded pitch deck: không có UI generator)
- PARTNER_UI_RESOURCES_005 — BLOCKED (ROI calculator → prospect PDF: không có UI calculator)
### UI · SA_PARTNER_MODULE

#### PARTNER_UI_SA_PARTNER_MODULE_001 — BLOCKED
**Intent:** Resolve entry Conflict Queue với written reasoning — decision lưu, thông báo 2 bên, record thành immutable.
**Lý do block:** Bị chặn bởi defect backend của SA Deal Approval Queue (xem _007 / BUG-UI-005). Conflict Queue (`/partners/deals` → tab Conflicts) không load được deal — mọi tab báo "Server Error — Invalid id: 'pro-v1'" — nên không mở được conflicted deal để resolve. Xem lại khi BUG-UI-005 fix + có fixture 2-bên-cùng-domain.
#### PARTNER_UI_SA_PARTNER_MODULE_002 — BLOCKED
**Intent:** UI decision Conflict Queue hiện prospect-confirmation + first-registered timestamp + written reasoning bắt buộc + SLA 5-ngày-làm-việc.
**Lý do block:** Giống _001 — deal list Conflict Queue không load (BUG-UI-005), nên không tới được UI conflict-decision. Cần BUG-UI-005 fix + fixture conflict có prospect-confirmation.
#### PARTNER_UI_SA_PARTNER_MODULE_003
**Mô tả test:** Partner Directory phía SA load (stgsa SA Dashboard → Partners). Xác nhận directory render với breadcrumb + summary stat cards, filter Status/Tier + action "Onboard Partner", và table partner với đủ header cột. Read-only + empty-safe.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập super-admin (stgsa); mở `/partners` và chờ READY_MARKER "Partners" trong `<main>`.
**Các bước:**
1. Directory load với breadcrumb + summary cards.
   → Expected: breadcrumb "Directory" + 4 summary card (**Total Partners**, **Active**, **Pending Approval**, **Premier Tier**) hiển thị.
2. Filter controls + action Onboard hiển thị.
   → Expected: filter **Status** và **Tier** + action **Onboard Partner** hiển thị.
3. Table partner render (đủ header cột; có row khi có data).
   → Expected: table có đủ 8 header (PARTNER, TIER, TYPE, CONTACT, TOTAL ARR, OPEN DEALS, STATUS, JOINED); partner rows render khi có partner, ngược lại hiện empty-state "No Data Found".
**Expected (tổng):** SA Partner Directory load với summary, filters, và cấu trúc table partner (không phụ thuộc data).
**Ghi chú:** PASSED — verified 2026-07-29 (TC 12060503). Test SA_PARTNER_MODULE đầu tiên — dựng nền surface phía SA (stgsa SA Dashboard, super-admin) qua `ShellPage` sẵn có + `PartnerDirectoryPage` mới. Chạy trên SA domain (`make_page`/`authenticated_page`), KHÔNG phải partner portal. Section config mới `PARTNER.ui.SA_PARTNER_MODULE = 5`. Empty-safe: verified cả 0 row (empty state) lẫn ≥1 partner row. Negative: N/A — directory load read-only. Idempotency: N/A. LƯU Ý: stgsa flap khi verify (login-fail + render-timeout 90s ở 2 lần trước) — pass sạch khi staging ổn; env flakiness, không phải lỗi test.
#### PARTNER_UI_SA_PARTNER_MODULE_004 — BLOCKED (UI FSM chưa deploy)
**Ở đâu:** stgsa → Partners → Directory → Pending Approval → mở application. **Design:** PN003 (FSM 3-stage), ready-for-dev.
**Intent:** FSM review partner-application — stage SA Review / Legal Countersign / Final Approval hiển thị với status indicator; chặn skip stage; hiện thông tin applicant.
**Lý do block:** UI FSM review **chưa deploy trên staging** (re-verify kỹ 2026-07-30). **Fixture pending TẠO ĐƯỢC**: stgsa Partners→Directory→"Onboard Partner" tạo partner ở trạng thái **Pending** (verified — onboard PAR-795503, Pending Approval 0→1). NHƯNG detail của partner Pending vẫn chỉ có tab Overview/Deals/Commission/Members — **không có SA Review/Legal Countersign/Final Approval, không Approve/Reject**. Vậy blocker là màn FSM chưa deploy, KHÔNG phải thiếu fixture. Khi FE ship UI FSM review, test tự onboard partner để seed là build được.
#### PARTNER_UI_SA_PARTNER_MODULE_005 — BLOCKED (UI FSM chưa deploy)
**Design:** PN003 variant "lack of document", ready-for-dev.
**Intent:** (Negative) Thiếu signed agreement chặn advance sang Legal Countersign; Request Agreement thông báo applicant; attach agreement thì enable Advance.
**Lý do block:** Giống _004 — UI FSM review (stage SA Review / Advance-to-Legal-Countersign / attach agreement) chưa deploy. Fixture tạo được qua Onboard Partner; unblock khi UI FSM ra.
#### PARTNER_UI_SA_PARTNER_MODULE_006 — BLOCKED (UI FSM chưa deploy)
**Design:** PN003, ready-for-dev.
**Intent:** Legal countersign partner agreement → Final Approval khả dụng (+ audit trail / notification).
**Lý do block:** Giống _004/_005 — stage Legal-Countersign của UI FSM review chưa deploy. Unblock khi UI FSM ra.
#### PARTNER_UI_SA_PARTNER_MODULE_007 — FAILED (app bug · BE defect, be_gap · BUG-UI-005)
**Mô tả test:** SA Deal Approval Queue (stgsa `/partners/deals`, PRD §5.2) render shell — filter **Deal Type** + **Conflicts only** và header table deal — rồi load deal không lỗi backend. (Trang đã redesign 2026-08-05: status giờ là chip `<span>` custom **All / Pending / Approved / In Progress / Won / Expired / Lost / Rejected**; tab cũ "All Deals / Pending Approval / Conflicts" không còn — readiness/assert dựa vào filter + header table ổn định, không dựa chip.)
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập super-admin (stgsa); mở `/partners/deals` và chờ filter **Deal Type** (queue shell) render.
**Các bước:**
1. Shell queue render — filter + header table deal.
   → Expected: filter **Deal Type** + **Conflicts only** hiển thị; header **DEAL ID, DOMAIN, COMPANY, PARTNER, ESTIMATED ACV, DEAL TYPE, PLAN, STATUS, ACTIONS**. **(PASS.)**
2. Deal list load không server error (chờ deal-list fetch async settle trước khi assert).
   → Expected: không lỗi backend; deal rows load (partner có open deal). **(FAIL.)**
**Expected (tổng):** SA deal approval queue render và load được deal.
**Ghi chú:** FAILED by design — BE defect thật, `be_gap`, **BUG-UI-005** (re-verify 2026-08-05, TC 12060507). Shell render OK (filter + header 9 cột pass), nhưng deal-list fetch `GET /sa/deals?page=1&limit=20` trả **"Server Error — Invalid id: 'pro-v1'"** (plan-slug bị dùng chỗ cần Mongo `_id`) trong khi `GET /sa/deals/stats` (KPI counts) trả 200 — nên table hiện **"No Data Found"** dù counts khác 0. FE hiện lỗi dưới dạng **toast thoáng qua** (mắt thường dễ miss; thấy rõ ở DevTools → Network là call 400). Test **chờ deal-list settle** rồi mới assert nên bắt lỗi deterministic (bản cũ race async → có thể PASS oan). Assertion kết thúc "confirm with BE". Negative: N/A — view read-only. Idempotency: N/A. **Chặn (5 TC):** `PARTNER_UI_SA_PARTNER_MODULE_001`, `PARTNER_UI_SA_PARTNER_MODULE_002`, `PARTNER_UI_COMMISSIONS_003`, `PARTNER_UI_COMMISSIONS_010`, `PARTNER_UI_MY_PIPELINE_030` — tất cả đều chờ đúng defect BE này, nên fix **BUG-UI-005** sẽ mở khoá cả nhóm.
- PARTNER_UI_SA_PARTNER_MODULE_008
#### PARTNER_UI_SA_PARTNER_MODULE_009 — BLOCKED (UI config chưa deploy)
**Ở đâu:** stgsa → Partners → Commission → (Commission configuration → Commission rate). **Design:** PN020, ready-for-dev.
**Intent:** Cấu hình Commission Rate Table versioned — tier × deal-type (Registered/Select/Advanced/Premier × Referral/Reseller/Co-sell) với field NN/EN/EE; edit tạo version mới, giữ history; rate locked theo deal.
**Lý do block:** View Commission **configuration** **chưa deploy trên staging** (re-verify kỹ 2026-07-30: full-page text + mọi clickable + route). `/partners/commissions` chỉ render payout ledger (Pending Payout / Paid YTD / Clawback Exposure + table payout) — **không có entry "View configuration"**, không chữ rate/version ở đâu, route config (`/partners/commissions/configuration`, `/partners/commission-rates`…) 404 / "Invalid id". Design PN020 ready-for-dev nhưng UI config chưa lên. Unblock khi FE deploy view Commission configuration.
#### PARTNER_UI_SA_PARTNER_MODULE_010 — BLOCKED (UI config chưa deploy)
**Ở đâu:** stgsa → Partners → Commission → (Commission configuration → SPIFF Program). **Design:** PN020 (section SPIFF), ready-for-dev.
**Intent:** Tạo SPIFF bonus programme (name, bonus %, regions, tiers, valid dates) → hiện trong Active SPIFF Programmes; phản ánh vào commission projection của partner.
**Lý do block:** Giống _009 — cấu hình SPIFF nằm trong cùng view Commission configuration, chưa deploy trên staging. Unblock khi FE deploy.
#### PARTNER_UI_SA_PARTNER_MODULE_011 — FAILED (app bug · BE defect)
**Mô tả test:** SA Partner Programme Analytics dashboard (stgsa `/partners/analytics`, PRD §7) — funnel + KPI + tier-distribution + top-partners render và load không lỗi backend.
**Chuẩn bị (điều kiện tiên quyết):** Đăng nhập super-admin (stgsa); mở `/partners/analytics` và chờ section "Deal Funnel".
**Các bước:**
1. KPI cards + Deal Funnel stages render.
   → Expected: Total Partners, Total ARR, Avg Deal Size, Win Rate, Pending Payouts, Clawback Exposure + funnel Registered/Approved/In Progress/Won. **(PASS.)**
2. Section Tier Distribution + Top Partners render.
   → Expected: Deal Funnel, Tier Distribution, Top Partners by ARR hiển thị. **(PASS.)**
3. Data analytics load không server error.
   → Expected: không lỗi backend. **(FAIL.)**
**Expected (tổng):** Dashboard analytics hiện funnel + KPIs + sections với data đã load.
**Ghi chú:** FAILED — BE defect thật, verified 2026-07-29 (TC 12060511, **BUG-UI-006**). Dashboard shell render (KPIs + funnel + tier distribution + top-partners đều pass), nhưng 1 query analytics phân trang fail với **"Server Error — Invalid pagination: limit must not exceed 100"** (defect backend: frontend request page size > 100 bị API từ chối). Deterministic. Assertion fail với "confirm with BE". Lưu ý: KPI set live khác plan một chút (Approval Rate / Avg Deal Velocity / line-item commission chi tiết không render) — test assert đúng cái UI render. Negative: N/A — dashboard read-only. Idempotency: N/A.
#### PARTNER_UI_SA_PARTNER_MODULE_012 — BLOCKED (Territory chưa deploy)
**Ở đâu:** stgsa → Partners → Territory (và từ Partner detail). **Design:** Territory PN021, ready-for-dev.
**Intent:** Assign Territory (regions, verticals, exclusivity type, effective dates) cho partner; hiện warning conflict exclusivity; territory exclusive auto-route deal conflict.
**Lý do block:** Trang Territory **chưa deploy trên staging** (re-verify 2026-07-30). `/partners/territory` và `/partners/territories` trả "Server Error — Invalid id: 'territory'" (route chưa đăng ký), và section Territory ở partner-detail read-only "No territories assigned" không có control "+ Assign Territory" / form / warning conflict. Design PN021 ready-for-dev nhưng UI Territory management chưa lên. Unblock khi FE deploy.
#### PARTNER_UI_SA_PARTNER_MODULE_013 — PASSED
**Mô tả:** Trang Partner Detail phía SA (stgsa `/partners/<id>`) load đầy đủ chrome — các tab Overview / Deals / Commission / Members, section Tier & Performance + Territory Assignments, thông tin partner (id + type + tier) và control Partner-actions.
**Setup (điều kiện):** Login super-admin (stgsa); tự tạo 1 partner tạm qua **Onboard Partner** (danh sách Directory không ổn định trên staging), rồi mở detail.
**Test Steps:**
1. Các tab của detail render.
   → Expected: tab **Overview**, **Deals**, **Commission**, **Members** hiển thị (Radix `role="tab"`). **(PASS.)**
2. Section Overview + thông tin partner render.
   → Expected: section **Tier & Performance** + **Territory Assignments** + tên công ty + type **Channel** + id **PAR-…** hiển thị. **(PASS.)**
3. Control Partner-actions render.
   → Expected: control **Partner actions** (kebab) hiển thị trên header. **(PASS.)**
**Expected (tổng):** Partner Detail load với tabs, sections, thông tin partner và control actions.
**Note:** PASSED, verify 2026-07-31 (TC 12060513). Check load read-only (an toàn khi rỗng). Negative: N/A — chỉ load read-only. Idempotency: N/A. **Cleanup:** đã đăng ký — partner tạm được xoá qua SA API ở teardown — nhưng hiện **chưa có tác dụng**: `DELETE /v1/sa/partners/{id}` chỉ soft-delete (**BUG-API-021**), nên mỗi lần chạy vẫn để lại partner trên staging (log `CLEANUP LEAK`).
#### PARTNER_UI_SA_PARTNER_MODULE_014 — PASSED (add member; deactivate/reactivate chưa có UI)
**Mô tả:** Từ trang Partner Detail phía SA → tab **Members**, SA thêm 1 portal user (member) cho partner đang active; user mới xuất hiện trong danh sách Portal Users với status **Active**.
**Setup (điều kiện):** Login super-admin (stgsa); tự tạo 1 partner tạm, **Approve** (Pending → Active), mở tab Members.
**Test Steps:**
1. Tab Members hiện danh sách Portal Users (rỗng).
   → Expected: heading **Portal Users** + control **Add User** / **Add First User**; empty-state "No portal users yet". **(PASS.)**
2. Thêm portal user (First / Last / Email / Password / Role qua form → **Create Portal User**).
   → Expected: xác nhận **"Portal user created successfully"**. **(PASS.)**
3. User mới xuất hiện ở row Active.
   → Expected: row của user mới hiện email + role **Viewer** + status **Active**; header hiện **Portal Users (1)**. **(PASS.)**
**Expected (tổng):** SA thêm được portal user cho partner; user hiện Active trong danh sách Portal Users.
**Note:** PASSED, verify 2026-08-03 (TC 12060514). Password của user tạm (staging) được sinh ngẫu nhiên và **không log**. **Phạm vi:** tab Members chỉ có **Add User** (tạo) + action **Reset Password** trên từng row — **KHÔNG có** control member deactivate / reactivate / suspend / remove nào trên build này (verify live 2026-08-03: full HTML row + hover + quét keyword), nên phần deactivate/reactivate của intent gốc _014 **không tự động hóa được** (UI chưa có). Khi control đó lên, mở rộng thêm cho TC này. Negative: N/A — happy-path add (validate form là TC riêng). Idempotency: N/A — mỗi lần add tạo user khác nhau (email unique). **Cleanup:** đã đăng ký — partner tạm được xoá qua SA API ở teardown — nhưng hiện **chưa có tác dụng**: `DELETE /v1/sa/partners/{id}` chỉ soft-delete (**BUG-API-021**), nên mỗi lần chạy vẫn để lại partner trên staging (log `CLEANUP LEAK`).
#### PARTNER_UI_SA_PARTNER_MODULE_015 — FAILED (app bug · BUG-UI-008, lệch contract FE↔BE)
**Mô tả:** Từ trang Partner Detail phía SA, suspend một partner đang Active qua **Partner actions → Deactivate**. Kỳ vọng: partner chuyển khỏi Active (Suspended/Inactive) và mất quyền truy cập portal.
**Setup (điều kiện):** Login super-admin (stgsa); tự tạo 1 partner tạm, **Approve** (Pending → Active).
**Test Steps:**
1. Deactivate (suspend) partner đang active — Partner actions → Deactivate → confirm dialog "Deactivate Partner".
   → Expected: request thành công. **(FAIL.)**
2. Partner bị suspend, không có lỗi.
   → Expected: không có banner lỗi; partner không còn Active (Suspended/Inactive). **(FAIL.)**
**Expected (tổng):** SA suspend được partner Active từ UI; partner mất quyền truy cập portal.
**Note:** FAILED — app bug thật, verify 2026-07-31 (TC 12060515, **BUG-UI-008**, gắn `be_gap`). Dialog confirm **"Deactivate Partner" KHÔNG có ô nhập reason** (chỉ có nút Cancel / Deactivate), nhưng API deactivate **bắt buộc** field `reason` (chuỗi không rỗng). FE gửi request thiếu reason → BE reject — **"Server Error — reason should not be empty / reason must be a string / reason must be shorter than or equal to 2000 characters"** — UI hiện **"Failed to deactivate partner"** và partner **vẫn Active**. Lệch contract FE↔BE, deterministic: **không SA nào suspend được partner qua UI**. Fix: thêm ô Reason bắt buộc vào dialog (và gửi nó), hoặc để `reason` optional ở API. Cũng chặn luôn _016 (reactivate — không tới được state Suspended). Negative: N/A (1 action chuyển state). Idempotency: N/A — action không bao giờ thành công. **Cleanup:** đã đăng ký — partner tạm được xoá qua SA API ở teardown — nhưng hiện **chưa có tác dụng**: `DELETE /v1/sa/partners/{id}` chỉ soft-delete (**BUG-API-021**), nên mỗi lần chạy vẫn để lại partner trên staging (log `CLEANUP LEAK`).
#### PARTNER_UI_SA_PARTNER_MODULE_016 — BLOCKED (phụ thuộc BUG-UI-008)
**Mô tả:** Từ trang Partner Detail phía SA, reactivate một partner đang **Suspended** qua **Partner actions → Reactivate**; partner trở lại Active và có lại quyền truy cập portal.
**Intent:** Verify chuyển state Suspended → Active (đối xứng với _015).
**Lý do block:** Không tạo được điều kiện tiên quyết **Suspended**. Việc suspend partner đang hỏng do **BUG-UI-008** — dialog confirm "Deactivate Partner" không gửi `reason`, nên API deactivate reject ("reason should not be empty / must be a string / ≤ 2000 chars") và partner vẫn Active. Vì không tạo được partner Suspended qua UI (và không tới được control reactivate cho tới khi có state đó), flow reactivate không test được. **Unblock khi BUG-UI-008 được fix** (rồi build: onboard → Approve → Deactivate → Reactivate → assert Active). Negative: N/A. Idempotency: N/A.
#### PARTNER_UI_SA_PARTNER_MODULE_017 — BLOCKED (candidate; UI review hồ sơ chưa deploy)
**Candidate TC** (chưa có trong plan). **Design:** PN004 — Reject partner application.
**Intent:** Từ màn review hồ sơ partner phía SA, reject một application Pending (kèm lý do) → application chuyển sang Rejected và applicant được thông báo.
**Lý do block:** Không có control **Reject / Decline** trên build này (verify live 2026-08-03). Menu **Partner actions** của partner Pending **chỉ có "Approve Partner"**; row Directory không có action; quét keyword toàn trang không thấy Reject/Decline. Đây là **UI review hồ sơ (FSM)** — **chưa deploy trên staging** (cùng gap với _004/_005/_006). Unblock khi UI review (có Reject) lên.
#### PARTNER_UI_SA_PARTNER_MODULE_018 — BLOCKED (candidate; UI activation-invite chưa deploy)
**Candidate TC** (chưa có trong plan). **Design:** PN005 — Resend expired activation invite.
**Intent:** Với partner/user có activation invite đã hết hạn, resend invite từ phía SA → gửi lại email invite/activation mới.
**Lý do block:** Không có surface **Resend / Invite / Activation** nào trên build này (verify live 2026-08-03, cả Pending lẫn Approved + tab Members). Tab Members tạo portal user bằng cách **đặt password trực tiếp** ("Share these credentials with the partner") — không có flow email-invite / activation-link, nên không có state "invite hết hạn" để resend, và không có control Resend ở đâu cả. Unblock khi có flow activation-invite (email) kèm action Resend.
#### PARTNER_UI_SA_PARTNER_MODULE_019 — BLOCKED (candidate; UI review hồ sơ chưa deploy)
**Candidate TC** (chưa có trong plan). **Design:** PN027 — Request additional information from applicant.
**Intent:** Từ màn review hồ sơ partner phía SA, yêu cầu applicant Pending bổ sung thông tin → application vào state "info requested" và applicant được nhắc.
**Lý do block:** Không có control **Request info / Additional information / More info** trên build này (verify live 2026-08-03). Giống _017, menu actions của partner Pending chỉ có "Approve Partner" và quét keyword toàn trang không thấy wording request-info. Cùng thuộc UI review hồ sơ (FSM) chưa deploy. Unblock khi UI review (có Request-info) lên.
### UI · SECURITY_COMPLIANCE

TC bảo mật/tuân thủ cross-cutting — phần lớn SA-side / multi-partner / behavioral, nên chưa build trực tiếp được với setup partner-portal hiện tại.
- PARTNER_UI_SECURITY_COMPLIANCE_001 — BLOCKED (Security: deny cross-partner data access — cần ≥2 partner fixture + vector cross-access xác định; portal đã scope theo partner đang login nhưng chưa có setup để thử xem data partner khác)
- PARTNER_UI_SECURITY_COMPLIANCE_002 — BLOCKED (Security: audit — activity-log entry của SA action; partner portal không có audit log (nav 6 mục), Audit Log là SA-side (stgsa); cần SA action + log)
- PARTNER_UI_SECURITY_COMPLIANCE_003 — CANDIDATE (Security: data minimization khi đăng ký deal). TC duy nhất chạm surface partner tồn tại — register wizard request tập field đã biết (company name, domain, country, headcount, logo URL + contact name/email/phone/title). Build được = assert tập field ⊆ allowlist chính sách — **cần allowlist do PRD định nghĩa** để so sánh (không phải thiếu UI, mà thiếu chuẩn/spec).
- PARTNER_UI_SECURITY_COMPLIANCE_004 — BLOCKED (Compliance: SA impersonation → placeholder "pending legal decision"; feature impersonation/legal-placeholder chưa implement trên build)
### UI · TRAINING

**Cả module BLOCKED — chưa deploy trên partner portal** (re-verify live 2026-07-30, probe kỹ: login sạch + wait đủ). Nav partner có 6 mục — Dashboard, Deals, Commissions, Directory, Resources, My Apps — **không có "Training"**; `/training`, `/certifications`, `/learning` **không render** `<main>`. Trải nghiệm training/certification mà các TC mô tả chưa build/expose (data certification có phía SA — tab Members của partner-detail SA có cột CERTIFICATE — nhưng không có trang Training phía partner). Unblock khi module Training deploy + có certification fixture.
- PARTNER_UI_TRAINING_001 — BLOCKED (xem trang Training: certifications + progress + modules locked/unlocked — module chưa deploy)
- PARTNER_UI_TRAINING_002 — BLOCKED (certification completed → status cập nhật: module chưa deploy)
- PARTNER_UI_TRAINING_003 — BLOCKED (continue learning path đang dở → module hiện tại mở: module chưa deploy)

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
**Ghi chú:** PASSED — verified 2026-07-23. Case cross-entity của rule-5. BE giờ trả **404** cho cross-partner access (giấu sự tồn tại của resource); lỗ hổng cũ (gán nhầm 400) đã được fix. Tenant isolation vẫn đúng (không lộ dữ liệu). Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

#### PARTNER_API_AUTH_ACCESS_CONTROL_004
**Ghi chú (BLOCKED):** Enforce MFA phía partner — một protected action phải bắt buộc MFA cho phạm vi quy định (PRD §9.1: role `PARTNER_ORG_ADMIN` và/hoặc tier Advanced/Premier). BLOCKED do quyết định sản phẩm: OQ-14 chưa chốt — trục MFA mâu thuẫn giữa PRD §9.1 (theo tier, Advanced+) và sa-portal-architecture §14.8 (theo role, `PARTNER_ORG_ADMIN`); chưa biết cái nào authoritative (chờ Renil) thì expected (ai/action nào phải qua MFA) chưa xác định → không viết assertion được. Ngoài ra MFA enforcement còn gated theo Auth Hardening Phase 0 (PRs #633–641 phải merge trước khi bật live auth). Endpoint MFA phía BE ĐÃ có (partner: /v1/partner/auth/mfa/setup, /totp/enroll, /email-otp/send, /verify, /disable; sa-auth: /two-factors/otp, /sign-in/verify-otp) — nên KHÔNG phải bị chặn do thiếu endpoint. Khi unblock, build còn cần OTP/TOTP xác định (secret cố định hoặc test-only bypass) từ BE để hoàn tất bước challenge trong automation.

#### PARTNER_API_AUTH_ACCESS_CONTROL_005
**Ghi chú (BLOCKED):** MSP scope guard (PRD §9.2): MSP partner truy cập payroll/salary/health data của tenant đang quản lý phải bị cấm (403). Không có API surface trong Partner Platform để chạm — payroll nằm ở service HR/tenant riêng (module Payroll của sản phẩm lõi), ngoài sa-partners-api/sa-auth-api/connectors-api (grep cả 3 spec live → 0 endpoint payroll/salary, re-verify 2026-07-22). Còn cần MSP partner + managed tenant, mà MSP tenant provisioning cũng đang blocked (CLIENT_HEALTH_MSP_006). Unblock khi có payroll surface + MSP scope reachable từ domain này.

#### PARTNER_API_AUTH_ACCESS_CONTROL_006
**Ghi chú (BLOCKED):** MSP scope guard (PRD §9.2: "Export data ❌"): MSP partner export hồ sơ nhân viên của tenant đang quản lý phải bị cấm. Không có API surface trong Partner Platform — không có endpoint export-employee ở đây (chỉ có `/v1/sa/audit-logs/export` = export audit log của SA, không liên quan); hồ sơ nhân viên nằm ở service HR/tenant riêng. Cùng phụ thuộc như _005 (cần MSP partner + managed tenant, cũng đang blocked). Unblock khi có surface export-employee + MSP scope reachable từ domain này.

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
**Mục đích:** CRON — protection hết hạn mà KHÔNG có hoạt động gần đây → deal expire.
**Ghi chú (BLOCKED):** Job CRON theo thời gian (quét protection-expiry). Khi cửa sổ bảo vệ (theo tier: 60d Select / 90d Advanced / 120d Premier) trôi qua mà KHÔNG có hoạt động → deal phải chuyển 'expired'. Không có endpoint trigger job on-demand và không có test clock trên staging → không tua tới mốc hết hạn được và không chạy sweep theo yêu cầu, nên không quan sát được transition. Unblock khi BE expose trigger "run protection-expiry job" thủ công hoặc test clock / backdate protectionExpiresAt.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_007
**Mục đích:** CRON — deal đã auto-extend 1 lần thì KHÔNG được auto-extend lần 2 (cap).
**Ghi chú (BLOCKED):** Job CRON theo thời gian. Verify "không auto-extend lần 2" cần 1 deal đã auto-extend 1 lần (kết quả của _005) VÀ thêm 1 chu kỳ hết hạn nữa — cả hai đều cần job protection-expiry chạy + control clock để tới mốc hết hạn thứ 2, đều không có trên staging. Phụ thuộc _005. Unblock khi BE expose trigger job thủ công hoặc test clock / backdate.

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
**Ghi chú:** PASSED — verify lại 2026-08-10 (TC 2060208); trước đây FAILED có chủ đích (`be_gap`, **BUG-API-002**, nay đã Closed). Marker `be_gap` đã gỡ, TC quay lại trong merge gate. Gap gốc, giữ lại để tra cứu: rate/rateTableVersion KHÔNG có trong response của deal API và không có commission nào được tạo khi approve. Xác nhận với BE: đóng dấu nội bộ (không serialize) / stage khác (deal win) / chưa implement.

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
**Mô tả test:** SA đánh dấu deal approved là won (POST /v1/sa/deals/{id}/win, WinDealDto = intake tenant-provisioning): status → 'won', lưu actualAcvCents + intake, phát event partner.deal.won (tenant provisioning + commission là downstream/async).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo partner; register deal; approve (status 'approved'); build win intake (companyWebsite, industry, admin*, tenantDomain, region, billingCycle, actualAcvCents…).
**Các bước:**
1. Đánh dấu deal approved là won (capture intake tenant-provisioning).
   → Expected: accepted (HTTP 201, envelope statusCode 200); status 'won'; có message.
2. Verify deal won lưu actualAcvCents + các field intake đã gửi.
   → Expected: actualAcvCents echo; companyWebsite/industry/adminFirstName/adminLastName/tenantDomain lưu như gửi.
3. Verify phát event audit 'partner.deal.won' (approved → won).
   → Expected: một entry (action 'partner.deal.won') cho deal này với after.status == 'won'.
4. Verify status won bền vững (GET /v1/sa/deals/{id}).
   → Expected: status 'won', actualAcvCents persist.
**Teardown:** xóa partner cha.
**Expected (tổng):** Deal approved chuyển 'won' với intake được lưu và phát won-event; tenant provisioning + commission là downstream (async — commission không xuất hiện sync trong /v1/sa/commissions), ngoài phạm vi.
**Ghi chú:** PASSED. Approve giờ yêu cầu `planId` (ApproveDealDto đổi — client auto-resolve). Win message: "Deal marked as won; tenant provisioning kicked off". Đối trọng negative/illegal-state là _034.

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
12. Ghost planId ('no-such-plan-qa', đã verify không tồn tại ở trên) → **404**, message đề cập "plan".
**Teardown:** xóa partner cha (gỡ mọi deal vô tình tạo bởi gap planId).
**Expected (tổng):** Mọi payload register không hợp lệ bị từ chối với một message rõ ràng và không tạo deal nào; planId nên được validate với catalog.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap (case 12): một planId không tồn tại giờ bị từ chối với **404** (trước đây được chấp nhận 201). Cả 12 case đều pass. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

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
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → **404** Not Found, message "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Deal đã approved (illegal transition) → **400** 'cannot transition' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
**Teardown:** xóa partner cha.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; illegal transition → 400/409. Không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap ghost-id (case 1): một id đúng định dạng nhưng không tồn tại giờ trả **404** "not found" (trước là 400). Cả 3 case đều pass. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_029
**Mô tả test:** Đối trọng negative của _009 (resolve-conflict): sáu input không hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal (status 'registered', conflictStatus 'none' — một target non-flagged).
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/resolve-conflict)
1. Enum decision không hợp lệ ('whatever') → **400** 'decision must be one of'.
2. Thiếu decision → **400** 'decision must be one of'.
3. Thiếu reasoning → **400** message đề cập "reasoning".
4. Malformed id ('not-an-id') → **400** 'invalid id'.
5. Deal non-flagged (illegal state) → **400** message đề cập "flagged" (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
6. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → **404** Not Found, message "not found".
**Teardown:** xóa partner cha.
**Expected (tổng):** Lỗi validation/format/state → 400; id không tồn tại → 404. Không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap ghost-id (case 6): một id đúng định dạng nhưng không tồn tại giờ trả **404** "not found" (trước là 400). Cả 6 case đều pass. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

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
8. Ghost deal id (body hợp lệ, đúng định dạng nhưng không tồn tại) → **404** Not Found, message "not found".
**Expected (tổng):** Validation body / boundary / format / malformed → 400; id không tồn tại → 404. Không bao giờ 5xx. Ràng buộc spec: addedDays ∈ 1..180; reasoning bắt buộc + không rỗng.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap ghost-id (case 8): một id đúng định dạng nhưng không tồn tại giờ trả **404** "not found" (trước là 400). Cả 8 case đều pass. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_031
**Mô tả test:** Đối trọng negative của _020 (get-by-id): hai ngữ nghĩa từ chối riêng biệt — một malformed id là bad request (400), một ghost id là missing resource (404). Tự chứng minh; GET → không lo idempotency. Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/deals/{id}; kỳ vọng code + gợi ý message, không bao giờ 5xx)
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → **404** Not Found, message đề cập "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message đề cập "invalid id".
**Expected (tổng):** Một malformed id → 400; một id đúng định dạng nhưng không tồn tại → 404. Không bao giờ 5xx, không trả record.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap ghost-id (case 1): một id đúng định dạng nhưng không tồn tại giờ trả **404** "not found" (trước là 400, status mâu thuẫn message). Cả 2 case đều pass. Đây là TC root-cause của lỗ hổng ghost→404 mang tính hệ thống. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_032
**Mô tả test:** Đối trọng negative của _019 (lose): ba target lose bất hợp lệ, mỗi cái bị từ chối với code riêng + một message rõ ràng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo một partner; đăng ký một deal (status 'registered', CHƯA approved — lose yêu cầu 'approved').
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/lose)
1. Deal registered (illegal transition — chưa approved) → **400** 'cannot transition' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận ở đây).
2. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → **404** Not Found, message "not found".
3. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Teardown:** xóa partner cha.
**Expected (tổng):** Illegal transition → 400/409; malformed id → 400; id không tồn tại → 404. Không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap ghost-id (case 2): một id đúng định dạng nhưng không tồn tại giờ trả **404** "not found" (trước là 400). Cả 3 case đều pass. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

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

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_034
**Mô tả test:** Đối trọng negative của _018 (win): illegal transition + id sai bị từ chối đúng code; required intake fields của DTO cũng nên được enforce. Tất cả case đều chạy (thu thập failure).
**Chuẩn bị (điều kiện tiên quyết):** SA tạo partner; mỗi case required-field dùng 1 approved deal mới (win thành công tiêu thụ deal).
**Các bước:** (mỗi case = một POST /v1/sa/deals/{id}/win)
1. Missing companyWebsite → kỳ vọng **400** (required). **Hiện FAIL** — BE trả 201 (won).
2. Missing industry → kỳ vọng **400**. **Hiện FAIL** — BE trả 201.
3. Missing adminFirstName → kỳ vọng **400**. **Hiện FAIL** — BE trả 201.
4. Missing adminLastName → kỳ vọng **400**. **Hiện FAIL** — BE trả 201.
5. Win deal non-approved (registered) → **400** 'cannot transition'.
6. Ghost deal id (đúng định dạng, không tồn tại) → **404** 'not found'. (Win trả 404 đúng ở đây.)
7. Malformed deal id ('not-an-id') → **400** 'invalid id'.
8. Re-win một deal đã won → **400** 'cannot transition from won to won' (repeat bị từ chối; mutating action, không phải create).
**Teardown:** xóa partner cha.
**Expected (tổng):** Missing required intake → 400; non-approved/already-won → 400; ghost id → 404; malformed id → 400.
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker). Gap (case 1–4): WinDealDto khai companyWebsite/industry/adminFirstName/adminLastName là required, nhưng BE nhận win khi thiếu bất kỳ/tất cả (kể cả empty body → 201, deal won) — required-intake validation không được enforce. Case 5–8 đúng (lưu ý: win trả 404 cho ghost id, khác các SA endpoint khác). Confirm với BE.

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
1. Ghost id (đúng định dạng nhưng không tồn tại, 000000000000000000000000) → **404** Not Found, message "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Deal đã rejected (illegal transition) → **400** 'cannot transition' (409 Conflict sẽ chính xác hơn, nhưng 400 được chấp nhận).
**Teardown:** xóa partner cha.
**Expected (tổng):** Id không tồn tại → 404; malformed id → 400; illegal transition → 400/409. Không bao giờ 5xx.
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap ghost-id (case 1): một id đúng định dạng nhưng không tồn tại giờ trả **404** "not found" (trước là 400). Cả 3 case đều pass. Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

### API · DEAL_COLLABORATION

#### PARTNER_API_DEAL_COLLABORATION_001
**Ghi chú (BLOCKED):** PRD §4.5 / §8.5 mô tả một **SHARED NOTES thread** trên mỗi deal — partner (trên stgpartners) và BlazeUp SA rep (trên stgsa) cùng thêm note vào CÙNG một deal, mỗi note ghi tác giả (actor) + timestamp, append-only (xem mock "SHARED NOTES" §4.5: "Jamie Walsh 1 May …" / "Sarah Chen 2 May …"). PRD §8.5 đặt write ở phía partner: `PATCH /v1/partner/deals/:id (notes, docs)`. CHƯA build trên staging: (a) deal partner-portal **chỉ GET** (`GET /v1/partner/portal/deals/{id}` — không PATCH) → partner không thêm note được; (b) phía SA (`PATCH /v1/sa/deals/{id}`) chỉ **đè 1 chuỗi `notes` phẳng** — không actor/timestamp từng note, không append, không thread chung. Tức tính năng shared-notes chưa tồn tại. KHÔNG re-scope thành "SA đè 1 chuỗi notes phẳng" rồi gọi là collaboration (đó là tính năng khác, nhỏ hơn, gọi vậy là sai bản chất). Unblock khi BE ship shared-notes thread (actor + timestamp, append, cả partner + SA viết).

#### PARTNER_API_DEAL_COLLABORATION_002
**Ghi chú (BLOCKED):** PRD §4.5 hiển thị mục **DOCUMENTS** trên mỗi deal ("[Upload]" + danh sách document) và §8.5 gộp vào `PATCH /v1/partner/deals/:id (notes, docs)`. CHƯA build trên staging: deal partner-portal chỉ GET, `UpdateDealDto` phía SA không có field `documents`, và PATCH kèm payload `documents` bị từ chối ("No editable fields provided") — không có endpoint để upload/list/download document của deal. Unblock khi BE expose surface deal-documents.

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
**Ghi chú (NOT_STARTED — redundant / cross-ref):** "Validate expectedCloseDate không hợp lệ → 400" đã được kiểm bởi **DEAL_REGISTRATION_PIPELINE_021** (case bad-date: `expectedCloseDate` không đúng ISO-8601 → 400, và thiếu expectedCloseDate → 400). _021 hiện PASS nên validation này đã được cover. KHÔNG blocked — chỉ là không có assertion riêng nào để thêm nếu build standalone. KHÔNG build trùng; coi như đã cover bởi _021. (Nếu sau này cần dòng standalone thì trỏ vào cùng validation ngày của POST /v1/sa/deals.)
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
**Mô tả test:** SA liệt kê commission ledger: GET /sa-partners-api/v1/sa/commissions trả về ledger phân trang, lọc được, đúng cấu trúc.
**Các bước:**
1. GET /v1/sa/commissions (page=1, limit=5).
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}.
2. Verify phân trang.
   → Expected: page size trả về ≤ limit yêu cầu (5).
3. Verify schema từng entry + không lộ field nhạy cảm (phụ thuộc dữ liệu).
   → Expected: mỗi entry có id + status enum hợp lệ (earned/pending_approval/approved/paid/disputed/clawback/cancelled); không có key password/token/secret. WARN-skip nếu ledger rỗng.
4. Verify lọc theo status chỉ trả entry khớp (phụ thuộc dữ liệu).
   → Expected: status=<status của entry đầu> chỉ trả status đó. WARN-skip nếu rỗng.
**Expected (tổng):** Commission-ledger list trả envelope đúng, phân trang, lọc được, không lộ dữ liệu nhạy cảm.
**Ghi chú:** PASSED. Read-only (không setup/cleanup). Commission row được tạo downstream khi deal win (DEAL_018, hoãn), nên trên staging ledger rỗng hợp lệ → bước 3–4 WARN-skip; contract list vẫn đúng. Đối trọng negative (invalid filter/pagination) là _017.

#### PARTNER_API_COMMISSIONS_PAYOUTS_003
**Ghi chú (BLOCKED, positive):** POST /v1/partner/portal/commissions/{id}/dispute đã có, nhưng dispute cần một commission {id} thật (win pipeline deferred). Negative (dispute một ghost id → 4xx) build được ngay bây giờ. Unblock khi một commission record có thể được tạo.

#### PARTNER_API_COMMISSIONS_PAYOUTS_004
**Ghi chú (BLOCKED):** Waiver product-failure POST /v1/partner/commissions/:id/waiver vắng khỏi spec (2026-06-30). Unblock khi BE ship endpoint waiver.

#### PARTNER_API_COMMISSIONS_PAYOUTS_005
**Ghi chú (BLOCKED):** Endpoint quyết định waiver / event final-outcome vắng (không có waiver path, 2026-06-30). Cặp với _004/_012.

#### PARTNER_API_COMMISSIONS_PAYOUTS_006
**Mô tả test:** SA upsert một commission rate (POST /sa-partners-api/v1/sa/rate-table): rate mới được lưu in-place, giá trị cũ giữ trong previousRate (version 1 cấp); không tạo row trùng.
**Chuẩn bị (điều kiện tiên quyết):** GET rate table; chọn 1 combo ĐÃ tồn tại (tier, dealType, commissionType) + capture rate gốc và clawbackWindowDays. Đăng ký teardown RESTORE rate gốc (không có endpoint DELETE nên test không bao giờ tạo combo mới).
**Các bước:**
1. Upsert CÙNG combo với rate mới.
   → Expected: accepted (HTTP 201, envelope statusCode 200); có message.
2. Verify rate mới được lưu + giá trị cũ giữ trong previousRate (version trail).
   → Expected: stored rate == rate mới; previousRate.rate == rate gốc; combo (tier/dealType/commissionType) không đổi.
3. Verify GET phản ánh rate mới VÀ combo vẫn đúng MỘT row (in-place, không trùng).
   → Expected: đúng 1 row khớp với rate mới + cùng _id.
4. Upsert lại lần 2 (rate mới thứ 2) — probe hành vi repeat (mutating action).
   → Expected: update in-place — vẫn 1 row; rate == giá trị thứ 2; previousRate advance sang giá trị thứ 1 (không phải create trùng).
**Teardown:** restore rate gốc của combo.
**Expected (tổng):** Upsert lưu rate mới in-place, version giá trị cũ qua previousRate, không bao giờ nhân đôi combo.
**Ghi chú:** PASSED. Endpoint là POST /v1/sa/rate-table (plan ghi "PUT /internal/commission/rates" — PUT→POST, path đổi tên). rate ràng buộc 0..1. Phía "cached" (Redis invalidation) là internal / không observe qua API (xem _014). Mutating upsert → không có TC idempotency create-trùng riêng (repeat là in-place, verify ở bước 4). Đối trọng negative là _018.

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

#### PARTNER_API_COMMISSIONS_PAYOUTS_017
**Mô tả test:** Đối trọng negative của _002 (commission ledger): filter/pagination không hợp lệ bị từ chối với code đúng (không bao giờ 5xx). Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một GET /v1/sa/commissions với param đang test)
1. Bad status enum ('bogus') → **400** 'status must be one of'.
2. Malformed partnerId ('not-an-id') → **400** 'partnerId must be a mongodb id'.
3. page=0 → **400** 'skip must be a non-negative integer'.
4. page=-1 → **400** 'skip must be a non-negative integer'.
5. limit over max (999999) → **400** 'limit must not exceed 100'.
6. limit=0 → **200** (default lenient — observe, không 5xx).
**Expected (tổng):** Filter/pagination không hợp lệ đã validate → 400; limit=0 default gracefully; không bao giờ 5xx.
**Ghi chú:** PASSED. Dòng negative mới ghép với _002 (GET read-only → không có TC idempotency). limit=0 bị default lenient (200) — điểm weak-validation cần confirm với BE.

#### PARTNER_API_COMMISSIONS_PAYOUTS_018
**Mô tả test:** Đối trọng negative của _006 (rate upsert): input không hợp lệ bị từ chối 400 + message field-level TRƯỚC khi ghi (không tạo/sửa combo nào). Tất cả case đều chạy (thu thập failure).
**Các bước:** (mỗi case = một POST /v1/sa/rate-table với field đang test bị lỗi)
1. Invalid tier enum ('platinum') → **400** 'tier must be one of'.
2. Invalid dealType enum ('wholesale') → **400** 'dealType must be one of'.
3. Invalid commissionType enum ('bogus') → **400** 'commissionType must be one of'.
4. Missing tier → **400** 'tier must be one of'.
5. Missing dealType → **400** 'dealType must be one of'.
6. Missing commissionType → **400** 'commissionType must be one of'.
7. Missing rate → **400** message có "rate must".
8. Negative rate (-0.1) → **400** 'rate must not be less than 0'.
9. Rate over 1 (1.5) → **400** 'rate must not be greater than 1'.
10. Non-numeric rate ('abc') → **400** 'rate must be a number'.
**Expected (tổng):** Mọi upsert rate không hợp lệ bị từ chối 400 và không có gì được lưu (rate phải 0..1). Không cần teardown (không ghi).
**Ghi chú:** PASSED. Dòng negative mới ghép với _006.
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
**Mô tả test:** Enforce reseller sell-price / data-minimization: reseller tự đặt giá cho end-client, và BlazeUp KHÔNG được lưu giá đó. Register reseller deal kèm các field giá end-client thì không được persist.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo partner; pick plan; build payload RESELLER deal nhét field giá end-client (endClientPrice, sellPrice, resellerMarginCents — không định nghĩa trong CreateDealDto).
**Các bước:**
1. Register reseller deal (kèm các field giá end-client).
   → Expected: accepted (HTTP 201, envelope statusCode 200) + id server cấp; dealType == 'reseller'. BE nhận + strip (không reject).
2. Verify response KHÔNG lưu field giá end-client nào.
   → Expected: endClientPrice / sellPrice / resellerMarginCents vắng mặt trong deal lưu.
3. Verify GET follow-up xác nhận giá end-client không được lưu.
   → Expected: GET /v1/sa/deals/{id} không trả các field đó.
**Teardown:** xóa partner cha.
**Expected (tổng):** Giá end-client của reseller không được persist (enforced / data-minimized) — yêu cầu chính là BlazeUp KHÔNG lưu nó.
**Ghi chú:** PASSED. Xác nhận yêu cầu "end-client price không được lưu": CreateDealDto không có field này và BE strip field lạ khi register (nhận 201, bỏ đi). Cùng cơ chế SECURITY_COMPLIANCE_002. Đây là check path REGISTER; đối trọng path UPDATE/PATCH là negative _016. Happy-path reseller register là DEAL_REGISTRATION_PIPELINE_002; idempotency N/A (register trùng = _022).

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
**Mô tả test:** Đối trọng negative của _006 (cùng enforcement — BlazeUp không lưu giá end-client của reseller) qua entry-point UPDATE/PATCH: không thể SET giá end-client lên một reseller deal đang mở.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo partner; pick plan; register 1 RESELLER deal (mở / editable).
**Các bước:**
1. Update deal kèm 1 field hợp lệ (notes) + các field giá end-client (PATCH /v1/sa/deals/{id}).
   → Expected: HTTP 200; field hợp lệ (notes) được áp; endClientPrice/sellPrice/resellerMarginCents bị strip (không persist).
2. Update CHỈ với các field giá end-client (không có field editable).
   → Expected: HTTP 400 "No editable fields provided" — giá end-client không phải field editable hợp lệ.
3. Verify qua GET.
   → Expected: notes update đã persist; không field giá end-client nào được lưu.
**Teardown:** xóa partner cha.
**Expected (tổng):** Không set được giá end-client của reseller qua update — bị strip khi kèm field hợp lệ, bị reject (400) khi gửi một mình. Không bao giờ persist.
**Ghi chú:** PASSED. Đối trọng negative/update-path của _006 (register path). Whitelist editable của UpdateDealDto (dealType/prospectEmail/prospectPhone/estimatedAcvCents/planId/expectedCloseDate/notes/wonTenantId) không có field giá end-client → bị strip hoặc update bị reject.

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
**Ghi chú:** FAILED (by design / `be_gap`, loại khỏi merge gate; tracked trong Bug_Tracker BUG-API-001). Gap: re-grant trả 201 và tạo một active cert THỨ HAI (list hiện 2). BE nên renew hoặc reject (409). Xác nhận với BE.

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
   → Expected: đúng 1 user cho email E.
**Teardown:** xóa partner cha.
**Expected (tổng):** Re-invite không được tạo một user duplicate-email (email là login identity).
**Ghi chú:** PASSED — verified 2026-07-23. BE đã fix gap duplicate-invite: re-invite cùng email không còn tạo user thứ hai (list hiện đúng 1). Marker `be_gap` đã gỡ 2026-08-10 — TC quay lại trong merge gate, entry Bug_Tracker đã Closed.

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
**Ghi chú:** PASSED. Đáng chú ý: endpoint partner-portal này trả **404** đúng cho một ghost id — khác với các endpoint get-by-id phía SA vốn trả 400 (gap hệ thống tracked trong Bug_Tracker BUG-API-006…019). Test ghim đúng 404 để một regression sẽ bị bắt.

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
**Mô tả test:** Mọi SA action ghi một audit entry đúng cấu trúc + có correlation: thực hiện một SA action mang reason sẽ tạo entry GET /v1/sa/audit-logs mang actor + action + reasoning + correlationId (+ tham chiếu resource), không lộ field nhạy cảm.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo partner (đối tượng action); build reason tier-change duy nhất.
**Các bước:**
1. Thực hiện SA action mang reason: đổi tier partner sang 'select' kèm reason.
   → Expected: HTTP 200; tier == 'select'.
2. Verify action đã ghi audit entry (GET /v1/sa/audit-logs, retry tối đa 3× cho eventual consistency).
   → Expected: một entry có action chứa "tier" tham chiếu partner này.
3. Verify entry mang các field governance.
   → Expected: actor (có type, vd 'sa-staff'); action (string non-empty); correlationId (UUID); reasoning được ghi (after.reason == reason đã gửi); resource.id tham chiếu partner; không có key password/token/secret.
**Teardown:** xóa partner cha.
**Expected (tổng):** Một SA action được audit đầy đủ — actor, action, reasoning, correlation ID — kèm tham chiếu resource và không lộ dữ liệu nhạy cảm.
**Ghi chú:** PASSED. Reasoning nằm trong `after.reason` với các action mang reason (tier change / deactivate / resolve). Không có negative invalid-input (đây là verify side-effect; negative query audit-log là AUDIT_LOG_005). Idempotency N/A (side-effect, không phải create). Bổ trợ DEAL_010 (event published) / ACCOUNT_MANAGEMENT_004 (decline reason audit-logged).

#### PARTNER_API_SECURITY_COMPLIANCE_002
**Mô tả test:** Data minimization của prospect: register deal kèm PII thừa (SSN, ngày sinh, national id, passport — field CreateDealDto không định nghĩa) thì KHÔNG được lưu.
**Chuẩn bị (điều kiện tiên quyết):** SA tạo partner; pick plan; build deal payload nhét PII thừa (prospectSsn, prospectDateOfBirth, prospectNationalId, prospectPassportNumber).
**Các bước:**
1. Register deal (kèm các field PII thừa).
   → Expected: accepted (HTTP 201, envelope statusCode 200) + id server cấp — BE nhận + strip (không reject).
2. Verify response KHÔNG lưu bất kỳ field PII thừa nào.
   → Expected: prospectSsn / prospectDateOfBirth / prospectNationalId / prospectPassportNumber vắng mặt trong deal lưu.
3. Verify GET follow-up xác nhận PII không được lưu.
   → Expected: GET /v1/sa/deals/{id} không trả các field đó.
**Teardown:** xóa partner cha.
**Expected (tổng):** PII thừa không được lưu (data minimization) — nhánh "not persisted" của "rejected or not persisted".
**Ghi chú:** PASSED. BE STRIP field lạ âm thầm (nhận 201, bỏ đi) thay vì reject 400 — cả hai đều thoả yêu cầu; nếu policy chặt hơn muốn 400 khi có field lạ thì confirm với BE. Security check này CHÍNH là kịch bản input thừa (không có negative riêng); happy-path register là _001 của DEAL_REGISTRATION_PIPELINE. Idempotency N/A.

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
