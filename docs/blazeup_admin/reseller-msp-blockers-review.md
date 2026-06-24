# Reseller + MSP — Review & Blockers

**Nguồn:** `partner-platform-prd-v1.8.md` (chính) · `Partner Platform - User Flows - v1.8.docx` · `partner_requirement.xlsx` (sheet 🎯 Feature Requirements)
**Mục đích:** Tổng hợp các mục liên quan Reseller & MSP, note các điểm chưa rõ / đang block để làm rõ requirements.
**Ngày:** 2026-06-23

---

## 1. RESELLER — nội dung liên quan

### Định nghĩa & chính sách (PRD)
- **§1.2, §2.2:** Reseller/VAR là Channel Partner, billing model = `reseller` (BlazeUp xuất hóa đơn cho partner theo giá discount; partner tự xuất hóa đơn cho khách cuối).
- **§2.2a — Reseller Pricing Authority (LOCKED — Renil, OQ-19):** Reseller tự đặt giá bán cho khách cuối. **BlazeUp KHÔNG lưu giá bán của partner ở bất kỳ record nào.**
- **§2.3 / §3 Scenario B:** Reseller tự bán, tự close, mark Won → tenant provisioned với `billing.model='reseller'`.
- **§5.3 Clawback:** **KHÔNG áp dụng cho Reseller** (vì partner đã thu margin tại thời điểm invoice).
- **§7.2 Reseller Close:** giống flow Referral nhưng `billing.model='reseller'`, invoice gửi tới partner.
- **Commission Reseller = margin (list − discount price)** theo tier: Select 20% / Advanced 30% / Premier 35% off list.

### Trạng thái trong Excel
| Dòng | Mục | Confirmed? | FE | BE |
|---|---|---|---|---|
| 2.2 | 4 Partner Types | Confirmed — *"Focus on a flow with a simple partner type first"* | Done | Done |
| 2.2a | Reseller Pricing Authority | Confirmed (Renil, OQ-19) | In Progress (*no UI for sell price*) | Done (*no sell-price field*) |
| 2.3 | Deal Types | Confirmed — *"Focus on a simple deal type first"* | In Progress | Done |
| 3-B | Scenario B: Reseller-Led | Confirmed — *"Focus on this scenario second"* | Done | Done |
| 7.2 | Reseller Close (`billing.model='reseller'`) | Confirmed | N/A | In Progress |

→ Phần lớn BE Done/In Progress; vướng chủ yếu ở **ưu tiên/scope** (xem §3).

---

## 2. MSP — nội dung liên quan

### Định nghĩa & chính sách (PRD)
- **§2.2:** MSP quản lý BlazeUp thay cho nhiều khách, billing = `partner_managed` (BlazeUp invoice MSP; MSP invoice khách).
- **§2.2b — MSP Tier Qualification (LOCKED — OQ-21):** ARR tính tier = **tổng ARR đang quản lý** (tất cả subscription chạy qua họ), không chỉ logo net-new.
- **§3 Scenario G + §7.3 + §9.2 — MSP model:**
  - MSP có **scoped admin**: cấu hình module, quản lý user, raise ticket, xem health metrics.
  - **Hard limits:** không xem payroll, không xem PII trên "SA-configured ceiling", không export, không impersonate, không billing config.
  - **Ticket-content consent (LOCKED — OQ-22):** mặc định **OFF**. MSP luôn thấy **count + severity**; chỉ thấy **nội dung ticket** khi client opt-in (ghi timestamp + actor). Revoke có hiệu lực ngay. Enforce bằng `PartnerScopeGuard` ở **mọi** microservice.
- **§7.3 MSP Provisioning:** nút "+ Add Managed Client" → provision với `billingModel='partner_managed'` + block `mspTicketContentConsent`.
- **§B4(c) MSP handoff:** chỉ SA thực hiện, cần cả 2 bên (hoặc client) đồng ý; lịch sử commission của MSP cũ được giữ; bắn event `blazeup.partner.client.transferred`.
- **Support escalation:** client → MSP support → (nếu chưa xong) → BlazeUp support (qua partner ticket, không phải ticket trực tiếp của client).

### Trạng thái trong Excel
| Dòng | Mục | Confirmed? | FE | BE |
|---|---|---|---|---|
| 2.2b | MSP Tier = Total ARR Managed | Confirmed (Renil, OQ-21) | Done | In Progress |
| 3-G | Scenario G: MSP Model | Confirmed (Renil, OQ-22) | **Not Started** | In Progress |
| 7.3 | MSP Provisioning Flow | **Planned** | **Not Started** | In Progress |
| 9.2 | MSP Access Scope + `PartnerScopeGuard` | **Planned** (Renil, OQ-22) | N/A | **Not Started** |

→ Đây là phần **rủi ro nhất**: Scenario G FE chưa làm, `PartnerScopeGuard` (9.2) BE chưa làm.

---

## 3. Những điểm CHƯA RÕ / cần làm rõ — và VÌ SAO

> Phần này giải thích **vì sao** mỗi điểm cần làm rõ (bối cảnh + mâu thuẫn + impact), để lần sau xem lại hiểu ngay. Câu hỏi tương ứng (tiếng Anh) ở §4.

### A. RESELLER

**A1 — Reseller có sinh `partner_commissions` record không?**
- Có **2 loại tiền khác nhau, đừng nhầm**: *sell price* (giá partner bán cho khách cuối — §2.2a quy định **KHÔNG bao giờ lưu**) vs *commission/margin* (lãi partner kiếm được). §2.2a **chỉ** nói về sell price, **không** trả lời chuyện commission record.
- **Vì sao mơ hồ:** Referral/Co-sell → BlazeUp **trả tiền RA** cho partner → chắc chắn có row trong `partner_commissions` (vòng đời `pending → approved → paid`). Reseller → BlazeUp **không trả ra đồng nào**; partner đã "ăn lãi" ngay tại invoice (mua ở giá discount). §5.3 nói *clawback không áp dụng cho reseller "vì margin collected at invoice"* → ngụ ý reseller **không nằm trong vòng đời payout** → **có thể không có row** nào.
- **`partner_commissions` sinh ra để làm gì:** sổ cái theo dõi tiền BlazeUp **NỢ** partner — để (1) duyệt chi, (2) hiển thị màn hình payout cho partner, (3) tính ARR/analytics, (4) xử lý clawback. Với reseller, cả 4 mục đích đều **không cần**.
- **Impact:** quyết định BE có tạo record không · FE hiển thị gì · QA assert "có row + giá trị đúng" hay assert "**không có** row".

**A2 — Gọi là "margin" hay "discount"?**
- Rate table ghi *"Reseller Margin 20/30/35% off list"* — nhưng vì không có sell price, con số đó **thực chất là DISCOUNT** (BlazeUp giảm bao nhiêu), **không phải margin thật**. Margin thật = sell price − discounted price, mà sell price thì BlazeUp **vĩnh viễn không biết**.
- **Impact:** đặt tên "margin" ngụ ý BlazeUp biết lãi thật của partner → gây hiểu nhầm cho cả team. Cần thống nhất label.

**A3 — UI hiển thị gì cho reseller?**
- Referral có widget *"estimated commission $X"* vì tính được con số. Reseller **không có sell price** → không thể hiện "$ margin thật". Vậy hiện gì: discounted price / % off / discount amount / không gì?
- **Impact:** FE build widget · QA assert đúng số ở đúng chỗ (assert "margin = $15K" sẽ **luôn sai** vì hệ thống không bao giờ có số đó).

**A4 — Reporting: ARR sourced tính từ đâu?**
- Nếu reseller **không** có commission record, thì doanh thu reseller & **"ARR sourced"** (dùng tính tier) lấy từ nguồn nào — từ deal hay từ tenant subscription?

**A5 — (Gap A) Reseller expansion / renewal có áp NN/EN/EE không?**
- **B6 (mô hình 3-stage NN/EN/EE) áp cho MỌI deal type**, kể cả reseller expansion (Scenario F, §7.4) — nhưng các câu NN/EN/EE hiện chỉ đang hỏi cho MSP, **bỏ sót reseller**.
- **Vì sao mơ hồ:** khi khách **renew**, reseller mua lại ở giá discount (margin **tự lặp** mỗi kỳ) hay rate tụt dần về **EE ≈ 0**? §7.4 nói expansion commission trên delta ARR nhưng **không nói riêng cho reseller**.

### B. MSP

**B1 — PII ceiling: §3 vs §9.2 mâu thuẫn**
- **§3 Scenario G:** MSP không thấy *"PII above their SA-configured ceiling"* → ngụ ý có **ngưỡng cấu hình được** (mỗi partner/tenant một mức).
- **§9.2 + User Flows v1.8:** quy tắc **CỐ ĐỊNH** — MSP chỉ thấy **name + email**, không bao giờ thấy payroll/salary/health. **Không hề** nhắc "ceiling".
- "Ceiling" còn **chưa định nghĩa**: cấu hình theo cái gì? (field nào? mức nhạy cảm? số bản ghi?).
- **Impact:** build `PartnerScopeGuard` **cứng (fixed list)** hay **cấu hình được** — 2 cách implement khác hẳn. *Nghiêng về fixed* vì User Flows v1.8 (bản mới nhất) viết cứng name+email; "ceiling" nhiều khả năng là **tàn dư bản nháp cũ** chưa xóa — nhưng cần xác nhận chính thức.

**B2 — MSP commission: toàn bộ book hay chỉ net-new?**
- **Tách 2 khái niệm:** TIER tính trên **tổng ARR managed** (§2.2b — đã rõ) vs COMMISSION RATE đi theo **NN/EN/EE** (B6).
- **Mâu thuẫn:** tier khen "toàn bộ book của MSP có giá trị" (gồm cả renew), nhưng NN/EN/EE làm phần renew (**EE**) tụt về ≈ 0. → BlazeUp **dùng cả book để nâng tier** cho MSP nhưng lại **gần như không trả commission** trên chính phần đó.
- **Câu hỏi cốt lõi:** MSP ăn commission trên **cả book** hay **chỉ NN**? Nếu chỉ NN → "total ARR managed" **chỉ ảnh hưởng tier/perks, không ảnh hưởng tiền trả** — đúng ý đồ chưa?
- **Phụ thuộc B6:** rates & độ dài window **vẫn TBD** ("SA-configurable before launch, pending benchmarking") → kể cả chốt logic vẫn **chưa test được giá trị số**.

**B3 — MSP handoff: consent capture ở đâu? (B4c)**
- B4c: handoff là **SA-only**, *"SA confirms both parties (or client) agree"* trước khi chuyển — nhưng **không spec cách capture** sự đồng ý đó.
- **So sánh để thấy chỗ thiếu:** ticket consent (§9.2) được spec **rất rõ** — `mspTicketContentConsent { granted, grantedAt, grantedBy, revokedAt, revokedBy }`, có audit. Handoff consent thì **không có** cấu trúc tương đương → là một bước "niềm tin", không có dấu vết số.
- **Impact:** pháp lý/audit (chuyển quyền quản lý dữ liệu khách sang bên thứ ba — PDPA/PDPL) · tranh chấp commission MSP cũ ("tôi đâu có đồng ý nhả") · BE có cần field/endpoint mới · FE màn hình handoff trông thế nào.

**B4 — PartnerScopeGuard: shared hay per-service? Ai own?**
- §9.2 yêu cầu guard ở **"every MS"** nhưng **không spec hiện thực**; §8 (Technical Architecture) **không liệt kê** nó là artifact/repo nào.
- **Rủi ro:** chỉ cần **1 service quên gắn** guard → MSP lọt qua khe đó, chạm được payroll/PII → **vi phạm PDPA/PDPL**.
- **Phạm vi vượt khỏi partner platform:** guard phải sống ở cả ms-payroll, ms-hr... (những service không thuộc partner platform) → cần phối hợp cross-team mà PRD không đề cập, **owner chưa rõ**.
- **Hai cách:** *shared lib/middleware* (build 1 lần, mọi MS import — sửa/audit 1 chỗ, nên theo) vs *per-service* (mỗi service tự viết — dễ lệch logic, dễ sót, sửa policy phải sửa nhiều chỗ).

**B5 — (Gap B) MSP support escalation: chưa có spec**
- §3 Scenario G + User Flows v1.8: *"Client issue → MSP support → (if unresolved) → BlazeUp support (elevated via partner ticket, not direct client ticket)"*. Chỉ có **policy path**, **không có spec** cách MSP "elevate" lên BlazeUp (endpoint nào? link ngược về ticket gốc của khách ra sao?).

### C. MSP + RESELLER

**C1 — MFA: theo role hay theo tier? (OQ-14, non-blocking)**
- **Xung đột giữa 2 tài liệu:** PRD §9.1 = theo **tier** (Advanced/Premier); sa-portal-architecture v2.6 §14.8 = theo **role** (mọi `PARTNER_ORG_ADMIN`). PRD §9.1 ghi cả hai nhưng tự đánh dấu *"Definitive policy still owed"*.
- **Khác biệt rõ ở tier thấp:** admin của **Reseller/MSP nhỏ** — theo role thì **vẫn phải** MFA; theo tier thì **được miễn**.
- **Vì sao quan trọng riêng cho Reseller/MSP:** admin của họ nắm dữ liệu **nhiều khách** (MSP cross-tenant) → tài khoản rủi ro cao → về an ninh **nên bắt MFA bất kể tier**.
- **Impact:** logic `partner-iam` MFA enforcement khác nhau hẳn — role / tier / AND / OR ra **4 nhóm người bị MFA khác nhau**.

---

## 4. Bộ câu hỏi đề xuất để làm rõ

### Reseller deals — commission & margin handling
Since we never capture the reseller's sell price (§2.2a) and clawback doesn't apply to resellers (§5.3, "margin collected at invoice"), a few things need clarifying so BE/FE/QA can align:

1. **Commission record:** When a Reseller deal is Won, do we create a row in `partner_commissions`?
   - *If yes:* what's stored in `amount` (margin = list − discount?), and what `status` applies, given there's no payout step like referral?
   - *If no:* please confirm the margin is implicit (only reflected via the discounted invoice to the partner), and there's no commission record for reseller deals.
2. **Terminology:** The rate table labels this "Reseller Margin 20/30/35% off list" — but since we don't capture sell price, that value is really the **discount**, not the partner's actual margin. Should the label stay "margin" or become "discount", to avoid implying we know their real profit?
3. **UI:** What does the reseller see in the deal registration / commissions UI — the discounted price they pay, the % off, the discount amount, or nothing?
4. **Reporting:** Where do reseller revenue & "ARR sourced" (for tier calculation) get computed from, if there's no commission record?
5. **Expansion / renewal (Gap A):** Does the 3-stage NN/EN/EE model (B6) also apply to **Reseller** deals on expansion/renewal? At renewal, does the reseller re-purchase at the tier discount (margin recurs each term), or does the discount drop toward EE? §7.4 mentions expansion commission on delta ARR but doesn't address reseller specifically.

### MSP

**1. MSP PII access — §3 vs §9.2 conflict.**
§3 (Scenario G) says MSP cannot see "individual PII above their SA-configured ceiling" — implying a configurable threshold. But §9.2 and User Flows v1.8 define a fixed rule: MSP sees name + email only, never payroll/salary/health. These two models don't match, and "ceiling" isn't defined (configurable by what — which fields? sensitivity level? record count?).
- Which is authoritative — a fixed field list (name + email), or an SA-configurable ceiling?
- If fixed: can we drop the "SA-configured ceiling" wording in §3 to avoid confusion?
- If configurable: what exactly does it configure (which PII fields are allowed/blocked?), at what scope (per-partner or per-tenant?), and what's the default?
- This affects how `PartnerScopeGuard` is built and what we test.

**2. MSP commission basis — whole book vs net-new?**
MSP tier is calculated on total ARR managed (§2.2b), but commission rate follows the 3-stage NN/EN/EE model (B6), where renewals (EE) can drop to ~0.
- Does an MSP earn commission on their entire managed book (including renewals, consistent with "the ongoing relationship is the value"), or only on net-new (NN) like other partners — with renewals falling to EE ≈ 0?
- If the latter, then "total ARR managed" only affects tier/perks, not payout — is that the intended behavior?
- Since B6 rates & NN-window durations are still TBD, when will MSP-specific NN/EN/EE values be set so we can build/verify the commission engine?

**3. MSP handoff — how is "both-party consent" captured? (B4c)**
B4c says an MSP handoff is SA-only and that "SA confirms both parties (or the client) agree" before transferring. But there's no spec for how that consent is captured:
- How does the outgoing MSP request the handoff — is there a portal action/endpoint for it?
- How is the agreement of the parties (outgoing MSP / incoming MSP / client) recorded — a UI step, a consent field, an uploaded document, or just SA's manual off-system verification?
- Is consent stored for audit (who agreed, when, by whom) — similar to `mspTicketContentConsent`? If so, do we need a schema field + endpoint for it?
- What does the SA handoff UI look like?
- Right now only the policy exists; we need the UI/endpoint/data spec to build and verify it.

**4. PartnerScopeGuard — shared component or per-service? Who owns it?**
§9.2 requires `PartnerScopeGuard` to enforce MSP access limits "in every MS", but the PRD doesn't spec the implementation:
- Is it a shared library/middleware (built once, imported by all services) or per-service? It's written as a named component but §8 doesn't list it as an artifact.
- Who owns it? It must live in services outside the partner platform too (ms-payroll, ms-hr…) — which team builds/maintains it?
- How do we guarantee no service is missed (mandatory middleware / CI check)? One unguarded service = MSP reaching payroll/PII → PDPA/PDPL breach.

**5. MSP support escalation — no spec (Gap B).**
§3 Scenario G + User Flows v1.8 describe "Client issue → MSP support → (if unresolved) → BlazeUp support (elevated via partner ticket, not direct client ticket)", but there's no implementation spec.
- How does an MSP escalate an unresolved client issue to BlazeUp support — is there a dedicated endpoint/flow for the "elevated partner ticket"?
- How does it link back to the client's original ticket? Only the policy path exists today.

### MSP + Reseller

**1. MFA trigger — role vs tier? (OQ-14)**
PRD §9.1 and sa-portal-architecture v2.6 §14.8 conflict on the MFA trigger for partners:
- PRD: tier-based (Advanced/Premier).
- sa-portal: role-based (any `PARTNER_ORG_ADMIN`).
- Which is authoritative — role, tier, or a combination (AND/OR)?
- For low-tier MSP/Reseller org admins (who hold multiple clients' data), is MFA required? Security-wise it should apply regardless of tier — please confirm.
