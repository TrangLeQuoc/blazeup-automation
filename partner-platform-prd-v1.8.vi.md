# BlazeUp Partner Platform - PRD ban tieng Viet

**Phien ban:** v1.8  
**Ngay:** 2026-05-15  
**Tac gia:** BlazeUp Admin  
**Trang thai:** PRD da nhung cac quyet dinh chuong trinh cua Renil. Tat ca 6 muc BLOCKING da duoc xu ly; co the bat dau build cac phan khong bi gate boi Auth. Cac cau hoi khong chan build va cac hang muc Legal/Compliance van con mo.

> File nay la ban tieng Viet tuong duong cua `partner-platform-prd-v1.8.md`, duoc viet lai gon hon de doc, trien khai va trao doi noi bo. Cac ten service, route, event, schema field va policy keyword duoc giu nguyen bang tieng Anh de tranh lech implementation.

---

## Lich su phien ban

| Phien ban | Ngay | Noi dung chinh |
|---|---|---|
| v1.8 | 2026-05-15 | Giai quyet B6: commission engine phai ho tro lifecycle 3 giai doan NN/EN/EE, tat ca rate va window do SA cau hinh. |
| v1.7 | 2026-05-15 | Giai quyet B5: sandbox-data service co 3 profile SMB/Mid-market/Enterprise, reset on-demand va optional weekly auto-reset. |
| v1.6 | 2026-05-15 | Giai quyet B4: cac edge case attribution, MSP handoff, SA override va `attributionHistory[]`. |
| v1.5 | 2026-05-15 | Giai quyet B3: partner-org approval la workflow 3 buoc. |
| v1.4 | 2026-05-15 | Giai quyet B2: first-admin enrollment theo mo hinh tenant creation. |
| v1.3 | 2026-05-15 | B1 duoc go hard-gate cho non-auth coding; engineer lam song song voi Auth team. |
| v1.2 | 2026-05-15 | Nhung 7 cau tra loi cua Renil vao noi dung PRD. |
| v1.1 | 2026-05-08 | Chot 7 open questions trong changelog. |
| v1.0 | 2026-05-05 | PRD ban dau cho partner platform. |

---

## 1. Muc tieu va nguyen tac kien truc

### 1.1 Nguyen tac nen tang

BlazeUp **khong xay mot SA CRM rieng**. Tenant dogfood `blazeup.blazeup.ai`, dang chay CRM module cua BlazeUp, la CRM duy nhat cho doi sales noi bo.

Deal do partner dang ky se tu dong xuat hien trong CRM nay voi:

- `source = 'partner_registered'`
- opportunity duoc sales team xu ly chung voi cac deal direct/inbound
- SA Partner Module chi dung de quan ly chuong trinh partner: approval, conflict, territory, commission, audit

Day la invariant kien truc, khong phai tuy chon san pham.

### 1.2 Hai nhom partner

| Nhom | Ai | Ban/xay gi | Noi quan ly |
|---|---|---|---|
| Channel Partners | Referral agents, resellers, SIs, MSPs | Ban license BlazeUp cho end customers | `partner.blazeup.ai` |
| Pack Partners | ISVs, vertical specialists | Xay app/vertical pack tren marketplace | SA Tier K marketplace module |

Mot cong ty co the la ca Channel Partner va Pack Partner, nhung hai loai account duoc quan ly doc lap: credentialing, commission, portal va ledger tach rieng.

### 1.3 Loi the canh tranh

BlazeUp khong chi cho partner xem deal status. BlazeUp cho partner xem **suc khoe khach hang** sau khi close:

- DAU/MAU trend
- muc do adoption theo module
- ngay renewal
- upsell signals do AI goi y
- ticket count/severity

Day la moat cua partner programme vi du lieu nam native trong platform, khong can tich hop ngoai.

---

## 2. Cau truc Partner Programme

### 2.1 Partner tiers

Tier duoc tinh tu dong theo trailing-12-month ARR vao ngay dau moi quy. Upgrade co hieu luc ngay. Downgrade duoc bao truoc 30 ngay va co grace quarter.

| Tier | Nguong ARR T12M | Referral rate | Reseller margin | Quyen loi chinh |
|---|---:|---:|---:|---|
| Registered | $0 | 5% Y1 ACV | - | Portal, sandbox tenant, collateral co ban |
| Select | $50K | 10% Y1 ACV | 20% off list | Deal protection 60 ngay, co-branded materials, email support |
| Advanced | $200K | 15% Y1 ACV | 30% off list | Shared PSM, co-sell access, MDF pool, NFR licences |
| Premier | $750K | 20% Y1 ACV + 5% Y2 ACV | 35% off list | Exec sponsor, joint GTM plan, early access, QBR |

PSM allocation:

- Dedicated PSM chi bat dau khi Premier partner dat **$1.5M ARR**.
- Duoi $1.5M, Premier dung shared PSM voi ty le toi da 1:3.
- Advanced cung dung shared PSM pool.

### 2.2 Partner types

| Type | Vai tro | Billing model |
|---|---|---|
| Referral | Gioi thieu prospect, ban giao cho BlazeUp sales | `direct` |
| Reseller / VAR | Tu ban va tu close, giu quan he voi client | `reseller` |
| System Integrator | Trien khai BlazeUp, co services revenue + referral | `direct` |
| MSP | Quan ly BlazeUp thay cho nhieu client | `partner_managed` |

Quyet dinh da chot:

- Reseller tu quyet dinh gia ban cho end-client.
- BlazeUp chi invoice reseller theo tier discount.
- BlazeUp khong luu gia reseller ban cho end-client.
- MSP tier duoc tinh theo **tong ARR managed**, khong chi net-new logos.

### 2.3 Deal types

| Deal type | Partner lam gi | BlazeUp lam gi | Commission |
|---|---|---|---|
| Referral | Gioi thieu roi lui lai | BlazeUp sales close | Tier referral rate x Y1 ACV |
| Reseller | Partner tu ban va close | SA provision khi won | Margin theo discount |
| Co-sell | Hai ben cung ban | BlazeUp rep duoc gan | Mac dinh 70/30, co override neu ACV > $100K |

### 2.4 Certification

| Certification | Noi dung | Thoi luong | Unlocks |
|---|---|---:|---|
| BlazeUp Sales Certified | Overview, positioning, demo flow | 4h | Deal registration, referral commission |
| BlazeUp HR Specialist | HR, Payroll, Compliance | 6h | Co-sell eligibility cho HR deals |
| BlazeUp CRM Specialist | CRM, Marketing | 4h | Co-sell eligibility cho CRM deals |
| BlazeUp Implementation Certified | Setup, config, migration | 12h | Implementation revenue, MSP billing model |

---

## 3. Cac scenario deal

### Scenario A - Pure Referral

Partner dang ky deal, gioi thieu prospect, sau do BlazeUp sales so huu viec close. Khi won, partner nhan commission theo tier referral rate x Y1 ACV. Partner xem pipeline read-only sau handoff va co the message BlazeUp rep trong deal thread.

### Scenario B - Reseller-Led

Partner tu ban, tu procurement, tu mark deal Won trong portal. BlazeUp provision tenant va invoice partner theo gia discount. Partner invoice end-client theo gia rieng cua minh. BlazeUp khong cham vao payment cua end-client trong luong nay.

### Scenario C - Co-sell

Partner co relationship, BlazeUp co product depth. Sau khi partner chon Co-sell, BlazeUp gan rep trong 1 business day. Hai ben cung lam viec tren mot deal record chung.

Commission split:

- Mac dinh 70/30: partner / BlazeUp quota credit.
- Deal tren $100K ACV co the duoc SA de xuat split khac.
- Override can partner dong y bang van ban tren deal record.
- Split da approve duoc lock tai thoi diem deal approval.

### Scenario D - Deal Conflict

Khi hai ben cung dang ky mot domain/prospect:

1. Kiem tra prospect co xac nhan dang lam voi partner dau tien khong.
2. Neu khong ro, dung first-registered-wins.
3. Neu van ambiguous, SA partner team mediation trong 5 business days.
4. Partner thua conflict co the dang ky lai sau 90 ngay neu khong co deal close voi ben thang.

### Scenario E - Referral Link Attribution

Partner chia se link `blazeup.ai/ref/{partner-slug}`. Khi prospect click:

- server capture `partner_id`
- luu attribution 30 ngay server-side
- signup sau do van duoc attribute neu con TTL
- first-touch wins

Neu khong co cookie/ref token hoac qua 30 ngay, signup duoc xem la direct.

### Scenario F - Expansion tai existing client

Partner dang ky expansion deal voi `tenant_id` hien huu. Khi close, he thong them module/seat vao tenant cu, khong tao tenant moi. Commission tinh tren delta ARR theo lifecycle NN/EN/EE.

### Scenario G - MSP Model

MSP provision va quan ly tenant thay cho client. BlazeUp invoice MSP; MSP invoice client. MSP co scoped admin access:

- duoc config modules
- duoc quan ly users
- duoc raise tickets
- duoc xem health metrics
- khong duoc xem payroll/sensitive PII
- khong duoc export employee records

Ticket content:

- Count + severity luon hien thi.
- Full body/attachments chi hien thi neu client opt-in.
- Default OFF.
- Consent co the revoke bat ky luc nao va co hieu luc ngay.

### Scenario H - Technology Partner Also Resells

Mot pack partner co the dang ky them channel partner. Hai account type dung chung login nhung ledger, dashboard va commission/revenue share tach rieng.

### Scenario I - Multi-Partner Influenced Deal

Neu nhieu partner tung cham vao prospect nhung khong ai dang ky deal, khong ai duoc commission. Neu co deal registration, ap dung rule first registration / conflict resolution.

---

## 4. Partner Portal - `partner.blazeup.ai`

### 4.1 Technical shell

- Host app: `blazeup-hostapp-partner`
- Tailwind prefix: `pp-`
- Auth: credential store rieng voi tenant va SA
- JWT issuer rieng
- Module Federation cho cac subapp
- Shared singletons: `react`, `react-dom`, `react-router`

### 4.2 Information architecture

| Route | Man hinh |
|---|---|
| `/` | Dashboard |
| `/deals` | My Pipeline |
| `/deals/register` | Deal Registration wizard |
| `/deals/:id` | Deal Detail |
| `/clients` | My Clients |
| `/clients/:id` | Client Health Detail |
| `/commissions` | Commission & Payouts |
| `/training` | Certification & Training |
| `/resources` | Marketing Resources |
| `/team` | Partner Team Members |
| `/settings` | Profile, payment details, referral links |
| `/support` | Support tickets |

### 4.3 Dashboard

Dashboard tra loi cau hoi: "Hom nay partner can lam gi va dang tien trien ra sao?"

Thanh phan chinh:

- ARR sourced
- open deals
- pending commissions
- tier progress
- action required
- client health alerts
- Blazey assistant cho cac cau hoi ve commission, deal status, tier projection va client health

Nguyen tac design:

- Khong hien vanity metrics.
- Moi so lieu phai actionable hoac clickable.
- Action Required la trung tam hanh vi hang ngay.
- Tier progress luon thay duoc de tao dong luc len tier.

### 4.4 Deal Registration

Day la flow quan trong nhat cua portal. Muc tieu: dang ky deal duoi 90 giay tren mobile.

Flow:

1. Company: company name, domain, country, auto-enrichment theo domain.
2. Contact: first name, last name, email, title optional.
3. Deal: ACV, expected close date, modules, deal type.
4. Confirm and Submit.

Khi partner nhap ACV, portal hien **estimated commission** realtime. Day la dong luc chinh de partner dang ky deal thay vi gui email ngoai he thong.

Sau submit:

- deal co status `Pending SA approval`
- partner nhan Deal ID
- email + in-app notification khi approved

### 4.5 My Pipeline

Portal chi la CRM-lite cho BlazeUp deals, khong thay the CRM rieng cua partner. Partner co the xem deal theo stage:

- Registered
- Approved
- In Progress
- Closing
- Won
- Lost

Deal detail gom:

- timeline
- shared notes
- documents
- assigned BlazeUp rep
- commission projection
- protection expiry

### 4.6 My Clients

Hien sau khi deal close. Partner xem:

- ARR
- health status
- renewal date
- active modules
- usage/adoption signals
- support ticket count/severity
- upsell/renewal insight

Day la diem khac biet lon nhat cua partner portal.

### 4.7 Commissions and Payouts

Trang nay phai lam commission minh bach:

- earned YTD
- pending
- paid
- commission history
- expected payment date
- dispute button
- product-failure waiver request
- payout details

Product-failure clawback waiver:

- Neu client churn trong clawback window vi loi san pham BlazeUp da duoc xac nhan, partner co the request waiver.
- Can link support ticket hoac incident report.
- SA partner-ops quyet trong 30 ngay.
- Ket qua duoc ghi vao ledger, khong xoa row commission.

### 4.8 Training

Theo doi certification:

- Sales Certified
- HR Specialist
- CRM Specialist
- Implementation Certified

Nen tang training build hay buy van la open question OQ-8.

### 4.9 Resources

Partner co:

- co-branded pitch decks
- product one-pagers
- battle cards
- ROI calculator
- partner-only pricing sheets
- sandbox tenant `{partner-slug}-demo.blazeup.ai`
- API docs

Sandbox data co 3 profile: SMB, Mid-market, Enterprise. Reset on-demand la primary; weekly auto-reset optional va default OFF.

### 4.10 Partner Team

Quan ly team members, certifications va referral links:

- default link
- per-user link
- per-campaign link
- analytics theo clicks, conversions, attributed ARR

---

## 5. SA Partner Module - `blazeup-subapp-sa-partners`

Module nay duoc mount trong `blazeup-hostapp-superadmin` tai route `/partners`.

### 5.1 Partner Directory

SA xem va quan ly:

- partner profile
- tier, ARR, open deals, clients, status
- agreement date
- PSM assigned
- team members va certifications
- deal history
- commission ledger
- territory assignments
- performance vs tier threshold
- internal notes
- activity log

Partner application approval la workflow 3 buoc:

1. **SA Review**: SA review application; signed agreement bat buoc.
2. **Legal Countersign**: Legal countersign trong SA portal.
3. **SA Final Approval**: SA approve, emit `blazeup.partner.approved`, tao `PARTNER_ORG_ADMIN`.

Moi decline can mandatory reason va audit log.

### 5.2 Deal Management - Approval Queue

SA duyet moi deal registration. Khi approve:

- publish `blazeup.partner.deal.approved`
- bat dau deal protection clock
- stamp `commissionRate`
- stamp `rateTableVersion`
- voi co-sell > $100K ACV, SA co the propose override split
- assigned rep nhan task trong dogfood CRM
- partner nhan email + in-app notification

Deal protection:

- Select: 60 ngay
- Advanced: 90 ngay
- Premier: 120 ngay

Auto-extend rule:

- Neu het window va co it nhat 1 stage update trong 30 ngay gan nhat, dong thoi chua auto-extend lan nao: auto-extend 1 lan len 2x original window.
- Neu khong co activity hoac da auto-extend: hard expiry.
- Partner co the request manual SA extension.

### 5.3 Commission Configuration

SA quan ly rate table, version history va SPIFF program khong can code change.

Commission engine phai ho tro:

- referral rate
- reseller margin
- co-sell rate
- SPIFF bonus
- clawback policy
- product-failure waiver
- lifecycle NN/EN/EE

Clawback policy mac dinh:

- churn trong 12 thang tu go-live
- clawback 50% paid commission
- ap dung Referral va Co-sell
- khong ap dung Reseller
- dispute window 30 ngay

### 5.4 Territory Management

Territory gom:

- regions
- verticals
- exclusivity type

Exclusivity:

- Exclusive: chi partner nay duoc register trong region/vertical do.
- Preferred: nhieu partner co the hoat dong, conflict theo first-registered-wins.
- None: open market.

### 5.5 Analytics

SA xem suc khoe partner programme:

- partner-sourced ARR
- deals registered
- approval rate
- win rate
- average deal size
- deal velocity
- commission paid/pending
- clawbacks
- clawback waivers
- top partners
- tier distribution

### 5.6 Commission Ledger

Moi commission calculated can SA approval truoc payout. Amount > $10K can two-eye principle.

Ledger status:

- `pending`
- `approved`
- `paid`
- `disputed`
- `clawback`
- `clawback_waived`

---

## 6. CRM Integration Architecture

### 6.1 Contract

Partner-registered deals tu dong chay vao dogfood CRM tai `blazeup.blazeup.ai`. CRM la noi sales team lam viec. SA Partner Module khong phai CRM noi bo.

### 6.2 Event-driven sync

| Partner event | Dogfood CRM effect |
|---|---|
| `partner.deal.registered` | Tao opportunity, stage Pending Approval |
| `partner.deal.approved` | Update opportunity, gan owner/rep |
| `partner.deal.protection_extended` | Update metadata protection |
| `partner.deal.won` | Close Won, stamp ARR va tenant_id |
| `partner.deal.lost` | Close Lost, ghi close reason |
| `partner.deal.expired` | Mark Stale |
| `partner.client.health_alert` | Tao task tren account |

### 6.3 Opportunity shape

Opportunity can co attribution block:

```typescript
{
  source: 'partner_registered' | 'partner_link' | 'direct' | 'inbound',
  attribution: {
    partnerId: ObjectId,
    partnerName: string,
    partnerTier: string,
    partnerDealId: ObjectId,
    dealType: 'referral' | 'reseller' | 'cosell',
    commissionRate: number,
    rateTableVersion: string,
    commissionAmount: number,
    cosellSplit?: {
      partnerPct: number,
      blazeupPct: number,
      overrideApproved: boolean
    }
  }
}
```

---

## 7. Tenant Provisioning khi deal close

Tat ca provisioning path deu converge vao `blazeup.tenant.provisioned`.

### 7.1 Referral Close

Khi partner mark Won hoac BlazeUp rep close opportunity:

- emit `blazeup.partner.deal.won`
- tinh commission
- emit `blazeup.partner.commission.earned`
- goi SA `/internal/tenants/provision`
- tenant duoc tao voi attribution block
- CRM opportunity duoc stamp `tenant_id`
- billing tao subscription direct
- partner portal them client vao My Clients
- commission vao queue SA approval

### 7.2 Reseller Close

Giong referral close nhung:

- `billing.model = 'reseller'`
- BlazeUp invoice reseller theo discounted price
- reseller tu quan ly billing voi end-client
- BlazeUp khong luu end-client sell price

### 7.3 MSP Provisioning

MSP dung portal de `Add Managed Client`. Payload provision co:

```typescript
{
  billingModel: 'partner_managed',
  billingPartnerId: partnerId,
  mspTicketContentConsent: {
    granted: false,
    grantedAt: null,
    grantedBy: null
  }
}
```

Sau provisioning:

- BlazeUp invoice MSP
- MSP co scoped admin token
- tenant xuat hien trong Managed Clients
- ticket content van bi gate theo consent

### 7.4 Expansion Close

Expansion deal dung existing `tenant_id`. Khi close:

- add modules/seats vao tenant hien huu
- update subscription line items trong billing
- tinh commission tren delta ARR
- partner portal cap nhat ARR client

### 7.5 Tenant attribution block

Moi partner-sourced tenant phai co attribution vinh vien:

```typescript
attribution: {
  source: 'partner_referral' | 'partner_reseller' | 'partner_cosell'
    | 'partner_msp' | 'partner_link' | 'direct' | 'inbound',
  partnerId: ObjectId | null,
  partnerName: string | null,
  partnerTier: string | null,
  dealId: ObjectId | null,
  commissionStructure: {
    rate: number,
    rateTableVersion: string,
    type: 'referral' | 'cosell',
    baseACV: number,
    clawbackExpiresAt: Date,
    productFailureWaiver?: {
      requestedAt: Date,
      requestedBy: ObjectId,
      decision: 'pending' | 'granted' | 'denied',
      decidedAt?: Date,
      decidedBy?: ObjectId,
      evidence: ObjectId[]
    }
  } | null,
  billingModel: 'direct' | 'reseller' | 'partner_managed',
  attributionHistory?: Array<{
    partnerId: ObjectId | null,
    source: string,
    effectiveFrom: Date,
    effectiveTo: Date,
    changedBy: ObjectId,
    reason: string,
    approvedBy: ObjectId
  }>
}
```

Cho MSP-managed tenant:

```typescript
mspTicketContentConsent: {
  granted: boolean,
  grantedAt: Date | null,
  grantedBy: ObjectId | null,
  revokedAt: Date | null,
  revokedBy: ObjectId | null
}
```

---

## 8. Technical Architecture

### 8.1 Services va repos moi

| Artifact | Type | Mo ta |
|---|---|---|
| `blazeup-microservice-sa-partners` | Backend MS | Partner accounts, deal FSM, commission engine, territory, referral attribution |
| `blazeup-hostapp-partner` | Frontend host | Shell cho `partner.blazeup.ai` |
| `blazeup-subapp-sa-partners` | SA subapp | Partner directory, approval, commission, territory, analytics |
| `blazeup-subapp-partner-dashboard` | Partner subapp | Dashboard, pipeline, clients, commissions |
| `blazeup-subapp-partner-training` | Partner subapp | Certification/training |

### 8.2 MongoDB collections

Collections trong `ms-sa-partners`:

- `partner_accounts`
- `partner_deals`
- `partner_commissions`
- `partner_territories`
- `partner_certifications`
- `partner_referral_links`
- `partner_rate_table`
- `partner_conflicts`

`partner_rate_table` phai ho tro lifecycle:

```typescript
partner_rate_table {
  version,
  effectiveFrom,
  rates: {
    // tier x dealType
    nn: { rate, windowYears },
    en: { rate },
    ee: { rate }
  },
  spiffProgrammes: []
}
```

Commission engine phan loai deal la NN/EN/EE tai thoi diem tinh commission dua tren `tenant.goLiveAt` va config window.

### 8.3 Kafka events

Events chinh:

- `blazeup.partner.registered`
- `blazeup.partner.approved`
- `blazeup.partner.tier.changed`
- `blazeup.partner.deal.registered`
- `blazeup.partner.deal.approved`
- `blazeup.partner.deal.rejected`
- `blazeup.partner.deal.conflict_raised`
- `blazeup.partner.deal.protection_extended`
- `blazeup.partner.deal.won`
- `blazeup.partner.deal.lost`
- `blazeup.partner.deal.expired`
- `blazeup.partner.commission.earned`
- `blazeup.partner.commission.paid`
- `blazeup.partner.commission.waiver_decided`
- `blazeup.partner.client.health_alert`
- `blazeup.partner.msp_ticket_consent.changed`
- `blazeup.partner.client.transferred`
- `blazeup.partner.sandbox.reset_requested`

Moi event dung standard Kafka envelope:

- `eventId`
- `eventType`
- `schemaVersion`
- `tenantId`
- `occurredAt`
- `triggeredBy`
- `correlationId`

### 8.4 Referral Attribution Service

Flow:

1. Partner share link `blazeup.ai/ref/{partner-slug}[/{user-slug}][/{campaign}]`.
2. Server ghi Redis `attr:{sessionToken}` voi TTL 30 ngay.
3. Server set cookie `__blazeup_ref`, `SameSite=Lax`, `HttpOnly`.
4. Signup/provision doc cookie hoac `?ref`.
5. Resolve attribution, stamp tenant, emit `blazeup.partner.deal.won`, tinh commission.

Edge cases:

- Nhieu click: first-touch wins.
- Khong cookie/ref: direct.
- Click qua 40 ngay: TTL het, khong attribution.

### 8.5 APIs

SA-only:

```text
GET    /internal/partners
POST   /internal/partners
PATCH  /internal/partners/:id
POST   /internal/partners/:id/approve
GET    /internal/partners/:id/commissions
POST   /internal/partners/:id/commissions/:cid/approve
POST   /internal/partners/:id/commissions/:cid/waiver-decision

GET    /internal/deals
PATCH  /internal/deals/:id/approve
PATCH  /internal/deals/:id/reject
PATCH  /internal/deals/:id/protection-extend
GET    /internal/deals/conflicts
PATCH  /internal/deals/conflicts/:id/resolve

GET    /internal/commission/rates
PUT    /internal/commission/rates
POST   /internal/commission/spiff
```

Partner-JWT-gated:

```text
GET    /v1/partner/dashboard
POST   /v1/partner/deals
GET    /v1/partner/deals
PATCH  /v1/partner/deals/:id
POST   /v1/partner/deals/:id/cosell-split-accept
POST   /v1/partner/deals/:id/protection-extend-request
GET    /v1/partner/clients
GET    /v1/partner/clients/:tenantId/health
GET    /v1/partner/clients/:tenantId/tickets
GET    /v1/partner/commissions
POST   /v1/partner/commissions/:id/dispute
POST   /v1/partner/commissions/:id/waiver
GET    /v1/partner/referral-links
POST   /v1/partner/referral-links
```

### 8.6 Redis keys

```text
partners:account:{partnerId}
partners:rate_table:current
partners:rate:{tenantId}:{tier}
partners:deal:{dealId}:protection
partners:attr:{sessionToken}
partners:conflict:{domain}
```

---

## 9. Security va Compliance

### 9.1 Partner Portal Auth

- JWT issuer rieng voi tenant va SA.
- Access token 8 gio.
- Refresh token 30 ngay.
- Session scoped theo `partnerId`.
- Partner khong bao gio duoc xem data cua partner khac.
- MFA policy con open question: role-based, tier-based hay ca hai.

### 9.2 MSP Access Scope

MSP duoc:

- module configuration
- user management
- support ticket count + severity
- ticket content neu client opt-in
- employee name/email

MSP khong duoc:

- payroll/salary/health data
- export data
- billing configuration
- impersonate users

`PartnerScopeGuard` phai enforce o backend. UI gating khong du.

Ticket-content consent:

- default OFF
- luu `granted`, `grantedAt`, `grantedBy`, `revokedAt`, `revokedBy`
- revoke co hieu luc ngay
- event `blazeup.partner.msp_ticket_consent.changed` dung cho audit

### 9.3 Data Residency

Partner prospect data hien luu trong SA region `us-west1`. Khi co Middle East region, partner UAE/Saudi se luu prospect data tai region do. Contact details khong cross-region neu chua co consent.

### 9.4 Audit Trail

Moi SA action quan trong ghi vao `sa_audit_log`:

- deal approval/rejection
- protection extension
- conflict resolution
- co-sell split override
- commission approval/dispute
- product-failure waiver decision
- MSP ticket consent grant/revoke
- territory changes
- rate table modifications

---

## 10. Estimate

| Track | Estimate |
|---|---:|
| `ms-sa-partners` core | 4 tuan |
| Dogfood CRM bridge | 3 ngay |
| Referral attribution | 1 tuan |
| Renil-locked surface | 1 tuan |
| Partner host app | 1 tuan |
| Partner portal core subapps | 4 tuan |
| Partner portal remaining subapps | 3 tuan |
| SA partners subapp | 3.5 tuan |
| SA analytics + commission ledger | 2 tuan |
| Blazey partner assistant | 1 tuan |

Critical path cho partner programme v1:

**Deal registration -> approval -> dogfood CRM -> tenant creation -> commission**  
Khoang **7 tuan**.

Full partner portal + SA module + attribution: khoang **14 tuan**.

Auth surfaces van bi gate boi Auth Hardening Phase 0. Non-auth coding co the tien hanh song song.

---

## 11. Locked Decisions

| ID | Chu de | Quyet dinh |
|---|---|---|
| Q1 | Reseller pricing | Partner tu set end-client price; BlazeUp khong capture |
| Q2 | Deal protection expiry | Auto-extend mot lan neu co activity trong 30 ngay |
| Q3 | MSP tier basis | Tinh theo total managed ARR |
| Q4 | MSP ticket content | Client opt-in, default OFF |
| Q5 | Co-sell split | 70/30 default, override > $100K can partner agreement |
| Q6 | Product-failure clawback | Co the waive neu co evidence, SA quyet trong 30 ngay |
| Q7 | Dedicated PSM | Dedicated tai $1.5M ARR trong Premier |

Schema impact:

- `partner_accounts.managerAllocation`
- `partner_deals.protectionExtensionCount`
- `partner_deals.lastStageUpdateAt`
- `partner_deals.commissionRate`
- `partner_deals.rateTableVersion`
- `partner_deals.cosellSplit`
- `partner_commissions.status = 'clawback_waived'`
- `tenant.attribution.commissionStructure.productFailureWaiver`
- `tenant.mspTicketContentConsent`

---

## 12. Open Questions va Blockers

### 12.1 Blocking

Tat ca 6 blocking items da duoc giai quyet ve mat PRD, nhung co chi tiet can luu y:

| ID | Trang thai | Ghi chu |
|---|---|---|
| B1 Auth Phase 0 | Unblocked cho non-auth, auth surface van gate | Khong wire live partner JWT/MFA truoc khi Auth PRs merge |
| B2 First-admin enrollment | Resolved | Tao `PARTNER_ORG_ADMIN` o `PENDING_ACTIVATION`, user tu set password |
| B3 Org approval workflow | Resolved | SA Review -> Legal Countersign -> SA Final Approval |
| B4 Attribution edge cases | Resolved | No registration = no commission; override can two-eye approval |
| B5 Sandbox-data spec | Resolved | 3 profile, on-demand reset, weekly auto-reset optional |
| B6 Expansion commission | Architecture resolved | NN/EN/EE, rates TBD nhung SA-configurable |

### 12.2 Non-blocking open questions

- OQ-8: training platform build hay buy?
- OQ-14: MFA requirement theo role, tier hay ca hai?
- OQ-15: grace quarter definition cho tier downgrade.
- OQ-17: conflict-loser 90-day re-registration co auto-unlock/notification hay manual?
- OQ-18: rate-table change retroactivity, confirm lock tai deal approval.

### 12.3 Legal / Compliance pending

- GDPR partner-org erasure: field nao pseudonymize, field nao retain theo commission retention.
- Impersonation audit: partner co nhan notification khi SA impersonate tenant cua partner hay chi audit log.

### 12.4 Build gate summary

- Non-auth build co the bat dau.
- Partner auth surface phai doi Auth Hardening Phase 0.
- MFA enforcement can chot OQ-14 truoc khi implement logic cuoi.
- Legal/compliance can chot truoc khi go-live cac luong lien quan data retention va impersonation.

---

## 13. Diem can than khi implement

1. Lock `commissionRate` va `rateTableVersion` tai **deal approval**, khong phai registration hay invoice.
2. Enforce MSP scope o backend bang `PartnerScopeGuard`.
3. Referral attribution phai server-side va first-touch.
4. Conflict decision phai co reasoning va audit trail bat bien.
5. Co-sell override phai co partner acceptance.
6. Product-failure waiver khong xoa ledger row; chi ghi outcome de reconcile sach.
7. NN/EN/EE commission lifecycle phai config-driven.
8. Reseller sell price tuyet doi khong capture trong system.
9. Auth live wiring phai doi Auth Phase 0.
10. Tat ca SA override attribution phai co two-eye approval va `attributionHistory[]`.
