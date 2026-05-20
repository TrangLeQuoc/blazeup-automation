# BlazeUp Partner Platform — PRD

**Version:** v1.8
**Date:** 2026-05-15
**Author:** BlazeUp Admin
**Status:** PRD — Renil's 7 programme-policy answers embedded into body. All 6 BLOCKING items resolved (see §12.1). Build can start. Non-blocking open questions and Legal/Compliance items remain in §12.2 and §12.3.
**Supersedes:** `partner-platform-prd-v1.1.md` (kept on disk for change-history reference)

---

## Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| v1.8 | 2026-05-15 | BlazeUp Admin | B6 resolved: commission engine must support 3-stage customer lifecycle model — NN (Net New, full rate for SA-configured window) → EN (Existing customer Net New licenses, lower SA-configured rate) → EE (Existing customer Existing licenses, lowest rate). All rates and window durations SA-configurable before launch. `partner_rate_table` schema updated to store all 3 rate bands per tier × deal-type (§8.2). All 6 blocking items resolved — build can start. |
| v1.7 | 2026-05-15 | BlazeUp Admin | B5 resolved: sandbox-data service spec locked — 3 profiles (SMB/Mid-market/Enterprise), collections list defined, on-demand reset primary + optional weekly auto-reset toggle. `blazeup.partner.sandbox.reset_requested` Kafka event added (§8.3). 1 blocking item remains. |
| v1.6 | 2026-05-15 | BlazeUp Admin | B4 resolved: 4 attribution edge cases locked — no-registration=no commission; prospective-only partner attach for pre-programme tenants; SA-only MSP handoff with both-party consent; SA attribution override requires two-eye approval + `attributionHistory[]`. `blazeup.partner.client.transferred` Kafka event added (§8.3). `attributionHistory[]` added to tenant attribution schema (§7.5). 2 blocking items remain. |
| v1.5 | 2026-05-15 | BlazeUp Admin | B3 resolved: partner-org approval is a 3-stage workflow — SA Review → Legal Countersign → SA Final Approval. Signed agreement required before SA can advance. SA application review UI (§5.1) must surface all 3 stages as a visible FSM. 3 blocking items remain. |
| v1.4 | 2026-05-15 | BlazeUp Admin | B2 resolved: first-admin enrollment follows tenant creation model — `PENDING_ACTIVATION` user on partner approval, self-set password via activation email link, token TTL deferred to Auth team standard. 4 blocking items remain. |
| v1.3 | 2026-05-15 | BlazeUp Admin | B1 (Auth Phase 0) unblocked: engineer to work directly with Auth team in parallel; all non-auth coding to proceed without waiting. B1 removed from hard-gate list; 5 blocking items remain. |
| v1.2 | 2026-05-15 | BlazeUp Admin | Renil's 7 locked answers from v1.1 changelog and from `ms-sa-partners-open-questions-v0.4.md` (OQ-19…OQ-25) embedded into the body of the PRD — §2.1 PSM allocation · §2.2 reseller self-pricing + MSP tier basis · §3 Scenario C co-sell split · §3 Scenario G + §9.2 MSP ticket visibility · §5.2 deal-protection auto-extend · §5.3 clawback product-failure waiver. §11 replaced with **Locked Decisions** table. New §12 lists remaining BLOCKING open questions and pending Legal/Compliance items still owed by Renil / Aashwij / Khoa / Legal. |
| v1.1 | 2026-05-08 | BlazeUp Admin | 7 open questions locked in changelog (not yet embedded into body): reseller own pricing · deal protection auto-extend-once + activity gate · MSP tier = total managed ARR · MSP ticket visibility = client opt-in default off · co-sell 70/30 default + $100K large-deal override · clawback waived on confirmed product failure (30-day SA review) · dedicated PSM at $1.5M within Premier (shared PSM max 1:3 below threshold) |
| v1.0 | 2026-05-05 | BlazeUp Admin | Initial PRD — full partner platform design: channel partner program, partner portal (`partner.blazeup.ai`), SA partner module, CRM integration, tenant provisioning flows, commission engine, all deal combinations |

---

## ⚠️ Risk Flags

| # | Severity | Risk | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **CRITICAL** | Deal conflict — two partners (or partner + direct inbound) register the same prospect | Commission disputes, partner trust destroyed, channel conflict | First-registered-wins rule + SA conflict queue + 5-business-day SLA for resolution |
| R2 | **HIGH** | Commission opacity — partners don't trust what they'll earn until after the deal closes | Low deal registration adoption | Show projected commission at registration time, before submission, updated live as ACV is typed |
| R3 | **HIGH** | MSP billing ambiguity — partner-managed tenants billed to partner vs. end client | Revenue leakage + tax/VAT complications across Vietnam/UAE/India | Explicit `billing.model: 'direct' | 'reseller' | 'partner_managed'` on every partner-sourced tenant; set at deal registration, immutable after provisioning |
| R4 | **HIGH** | Referral attribution loss — prospect clicks referral link, signs up days later in a different browser | Partner loses commission on a valid referral | First-touch `partner_id` captured server-side on link click; stored with 30-day TTL; survives browser sessions |
| R5 | **MEDIUM** | Pack partner vs. channel partner conflation | Wrong commission structure applied; incorrect portal access | Two distinct account types; a partner can hold both; managed independently in SA |
| R6 | **MEDIUM** | Clawback rules unclear at deal close | Partner disputes clawback when a client churns at month 10 | Clawback policy + product-failure waiver path (§5.3, locked by Renil 2026-05-08) must be in the partner agreement AND displayed at commission approval time |
| R7 | **MEDIUM** | PDPA/PDPL compliance for partner-held prospect data | Partners in Vietnam/UAE uploading prospect data to deal registration | Partner agreement + DPA required per region; prospect data minimised at registration — domain + name + email only |
| R8 | **LOW** | Tier downgrade psychology — partner drops from Advanced to Select | Partner disengagement | Downgrade is quarterly, announced 30 days in advance; give partner a grace quarter to recover |

---

## 1. Context and Strategic Fit

### 1.1 Foundational Principle (from Control Plane Architecture, locked)

> BlazeUp does not build an SA CRM. The dogfood tenant at `blazeup.blazeup.ai` running BlazeUp's own CRM module is the only CRM. Partner-registered deals appear there automatically as opportunities with `source = 'partner_registered'`. BlazeUp's sales team works all deals — direct and partner — in one place.

This is not a product decision. It is an architectural invariant. The partner platform is built around this.

### 1.2 Two Partner Populations

| Population | Who | What They Build / Sell | Where They Live |
|---|---|---|---|
| **Channel Partners** | Resellers, referral agents, SIs, MSPs | Sell BlazeUp licenses to end customers | `partner.blazeup.ai` (this PRD) |
| **Pack Partners** | ISVs, vertical specialists | Build apps and vertical packs on the marketplace | SA Tier K — marketplace module (`docs/marketplace-pack-architecture-v1.1.md`) |

A single company can hold both account types. They are managed independently with separate credentialing, commission structures, and portals. This PRD covers **Channel Partners only**.

### 1.3 The Moat

Every competitor (Salesforce, HubSpot, Rippling) tells channel partners their deal status. BlazeUp tells partners their **clients' health** — DAU/MAU trend, module adoption depth, renewal date, AI-generated upsell signals — because BlazeUp is the platform those clients run on. No integration needed. The data is native. This is the single largest retention lever for the partner programme.

---

## 2. Partner Programme Structure

### 2.1 Partner Tiers

Tier qualification is automatic. The system calculates each partner's trailing-12-month ARR sourced through BlazeUp on the first day of each quarter. Upgrade is immediate; downgrade is announced 30 days in advance with a grace quarter.

| Tier | ARR Threshold (T12M) | Referral Rate | Reseller Margin | Key Perks |
|---|---|---|---|---|
| **Registered** | $0 (signed agreement only) | 5% of Y1 ACV | — | Portal access · sandbox tenant · basic collateral |
| **Select** | $50K | 10% of Y1 ACV | 20% off list | Deal protection 60 days · co-branded materials · dedicated email support |
| **Advanced** | $200K | 15% of Y1 ACV | 30% off list | Partner Success Manager (shared) · co-sell access · MDF pool · NFR licences |
| **Premier** | $750K | 20% Y1 ACV + 5% Y2 ACV | 35% off list | Named BlazeUp exec sponsor · joint GTM plan · earliest product access · quarterly business reviews |

Tier transitions publish `blazeup.partner.tier.changed` on Kafka → partner portal updates immediately → SA analytics reflects new tier.

**PSM allocation within Premier (locked — Renil, 2026-05-08):** A **dedicated** Partner Success Manager is allocated only at **$1.5M ARR** within the Premier tier. Below the $1.5M threshold, Premier partners share a PSM at a **maximum 1:3 ratio**. Advanced-tier partners use the same shared-PSM pool (max 1:3). The threshold is reviewed annually as the programme scales.

### 2.2 Partner Types

Each partner company selects a primary type at registration. Type determines the deal flows and billing models available.

| Type | Description | Billing Model Available |
|---|---|---|
| **Referral** | Introduces prospects, hands off to BlazeUp sales | `direct` (BlazeUp invoices client) |
| **Reseller / VAR** | Sells and closes independently, owns the client relationship | `reseller` (BlazeUp invoices partner at discount; partner invoices client) |
| **System Integrator** | Implements BlazeUp for clients, earns services revenue + referral | `direct` |
| **MSP** | Manages BlazeUp on behalf of multiple clients | `partner_managed` (BlazeUp invoices MSP; MSP invoices clients) |

**Reseller pricing authority (locked — Renil, 2026-05-08):** Reseller partners set their own end-client price. BlazeUp invoices the partner at the tier discount; whatever the partner charges the end client is the partner's business. BlazeUp does **not** capture the partner's sell price on the deal record or in any other system. Standard VAR norm.

**MSP tier qualification basis (locked — Renil, 2026-05-08):** An MSP partner's trailing-12-month ARR for tier qualification is calculated on **total ARR managed** — every client subscription billed through them counts — not only net-new logos they introduce. The MSP's value to BlazeUp is the ongoing managed relationship, not just the introduction.

### 2.3 Deal Types (selected per deal at registration)

| Deal Type | Partner's Role | BlazeUp's Role | Commission |
|---|---|---|---|
| **Referral** | Introduces and steps back | BlazeUp sales closes | Tier referral rate × Y1 ACV |
| **Reseller** | Partner sells and closes independently | SA provisions on win | Margin (list price − discount price) |
| **Co-sell** | Joint opportunity, active in sales cycle | BlazeUp rep assigned | 70/30 default; override above $100K ACV — locked at deal approval (§3 Scenario C) |

### 2.4 Certification Programme

Certification unlocks tier perks and co-sell eligibility. Delivered inside the partner portal's training module.

| Certification | Content | Duration | Unlocks |
|---|---|---|---|
| BlazeUp Sales Certified | Platform overview · competitive positioning · demo flow | 4h | Deal registration · referral commission |
| BlazeUp HR Specialist | HR · Payroll · Compliance modules | 6h | Co-sell eligibility on HR deals |
| BlazeUp CRM Specialist | CRM · Marketing modules | 4h | Co-sell eligibility on CRM deals |
| BlazeUp Implementation Certified | Full platform: setup · config · data migration | 12h | Implementation revenue recognition · MSP billing model |

---

## 3. All Deal Combinations

Every possible way a partner-sourced deal can originate, progress, and close.

### Scenario A — Pure Referral
Partner introduces a prospect and steps back. Partner registers the deal. BlazeUp sales owns the close. On won: commission = tier referral rate × Y1 ACV. Partner sees the deal progressing in their pipeline view (read-only after handoff). BlazeUp rep is visible with name and photo; partner can message them directly on the deal thread.

### Scenario B — Reseller-Led
Partner sells BlazeUp independently to a client. Registers the deal upfront. Works through procurement alone. Marks the deal Won in the portal when the client signs. Tenant provisioned. BlazeUp invoices the partner at the reseller discount price. Partner invoices the client at their negotiated price (Renil 2026-05-08 — partner-set, not captured by BlazeUp). BlazeUp never touches the client's payment in this path.

### Scenario C — Co-sell (Collaborative)
Partner has the relationship; BlazeUp has the product depth. Partner registers the deal and selects "Co-sell." BlazeUp assigns a rep within 1 business day. Both parties collaborate on a shared deal record — notes, documents, stage updates visible to both.

**Commission split (locked — Renil, 2026-05-08):**
- **Default 70 / 30** (partner / BlazeUp quota credit) applied automatically to every co-sell deal.
- **Override above $100K ACV:** SA may propose an adjusted split at deal approval for deals above $100K ACV. The override **requires partner agreement** in writing on the deal record — BlazeUp cannot impose a non-default split unilaterally.
- Whatever split is approved is **locked at deal approval** and cannot be renegotiated after the fact.

### Scenario D — Deal Conflict
Partner A registers `acme.com` on Monday. Partner B (or BlazeUp direct inbound) registers `acme.com` on Wednesday.

Resolution rules applied in order:
1. **Prospect confirmation**: did the prospect confirm engagement with Partner A? If yes, Partner A wins. If no, Partner B wins.
2. **First registered wins** as a tiebreaker if the prospect cannot be reached.
3. **Manual escalation**: if genuinely ambiguous, SA partner team mediates within 5 business days. Decision is final, logged to audit trail, both parties notified with written reasoning.
4. A partner whose deal is rejected on conflict grounds may register the same prospect again after 90 days if no deal closes with the winning party.

### Scenario E — Referral Link Attribution (No Registration Required)
Partner shares their unique tracking link `blazeup.ai/ref/{partner-slug}`. Prospect clicks it, browses, and signs up 3 weeks later — directly, without deal registration.

The server-side attribution engine captures `partner_id` on first click (30-day TTL, server-side — survives browser close, incognito, device change). On signup, the tenant is automatically attributed to the partner. Commission triggered automatically. Partner receives a notification: "Your referral link brought in a new client."

### Scenario F — Expansion at Existing Client
Partner's existing client wants to add modules or more seats. Partner registers an expansion deal against the existing `tenant_id`.

On approval and close: additional modules or seats provisioned on the existing tenant (no new tenant created). Expansion commission applies (SA-configured; typically 50% of new-logo rate — see §12 OQ-16: confirmation still owed from Renil). Partner's "My Clients" dashboard updates with the expanded ARR.

### Scenario G — MSP Model (Partner Manages Client)
Partner is an MSP. They provision tenants on behalf of clients. BlazeUp invoices the partner; partner invoices their clients.

In the portal, these tenants are "Managed Clients." The partner has scoped admin access: configure modules, manage users, raise support tickets, view health metrics. Hard limits: the partner cannot access payroll data, see individual PII above their SA-configured ceiling, or export employee records.

**Support ticket visibility (locked — Renil, 2026-05-08):** MSP partners see **ticket count + severity by default** for their managed clients. **Full ticket content** is gated on **explicit client opt-in** at tenant provisioning — opt-in is recorded with timestamp and actor for PDPA / PDPL audit. Until the client opts in, the MSP sees counts and severities only, never the body of the ticket. Consent can be revoked by the client at any time and the change applies immediately. See §9.2 for the schema and `PartnerScopeGuard` enforcement.

Support escalation path: client issue → partner support team → if unresolved → BlazeUp support (elevated via partner ticket, not direct client ticket).

### Scenario H — Technology Partner Also Resells
A pack partner (marketplace) wants to also be a channel partner. They hold two account types under one login. Pack developer account managed in SA Tier K marketplace module. Channel partner account managed in `ms-sa-partners`. Revenue share from pack sales and channel commissions are tracked in completely separate ledgers. One login; the portal surfaces both dashboards with a switcher.

### Scenario I — Multi-Partner Influenced Deal
Two partners both touched the same prospect at different points in the sales cycle (one at conference, one through a demo). Neither registered a formal deal.

Policy: attribution goes to the partner who registered the deal first. If neither registered, no partner commission is paid (this is the incentive to register deals). If both registered, see Scenario D conflict resolution.

---

## 4. Partner Portal — `partner.blazeup.ai`

### 4.1 Technical Shell

- Host app: `blazeup-hostapp-partner` (new repo, Tailwind prefix `pp-`)
- Auth: separate credential store from tenant and SA (distinct JWT issuer)
- Module Federation: subapps federated into host on demand
- Shared singletons: react, react-dom, react-router aligned with tenant host versions

### 4.2 Information Architecture

```
partner.blazeup.ai/
├── /               → Home / Dashboard
├── /deals          → My Pipeline
├── /deals/register → Deal Registration wizard
├── /deals/:id      → Deal Detail
├── /clients        → My Clients (post-close tenants)
├── /clients/:id    → Client Health Detail
├── /commissions    → Commission & Payouts
├── /training       → Certification & Training
├── /resources      → Marketing Resources
├── /team           → Partner Team Members
├── /settings       → Profile, payment details, referral links
└── /support        → Support tickets
```

### 4.3 Home / Dashboard

The one screen that answers: *"How am I doing right now?"*

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Good morning, Sarah.  You have 2 items that need your attention.           │
├────────────────┬───────────────┬─────────────────┬───────────────────────── │
│  Pipeline      │  Commission   │  Active Clients  │  Tier Progress           │
│  $1.2M         │  $48K earned  │  14 clients      │  ████████░░ Select →    │
│  8 open deals  │  $12K pending │  2 renewing <30d │  $87K of $200K Advanced  │
├────────────────┴───────────────┴─────────────────┴───────────────────────── │
│  ACTION REQUIRED                                                             │
│  • "Nexus Corp" co-sell: BlazeUp rep is awaiting your POC results — 3d left │
│  • Client "Meridian Ltd" renewal in 18 days — no contact logged yet         │
│  • Commission dispute on "Apex Group" resolved in your favour (+$4,200)     │
├─────────────────────────────────────────────────────────────────────────────┤
│  PIPELINE SNAPSHOT                                                           │
│  Registered 3 → Approved 2 → In Progress 2 → Closing 1                     │
│  (Mini kanban — click any card to open full deal)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  BLAZEY  "What's my commission rate on a $200K co-sell as Advanced?"   [→]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

Design rules:
- No vanity metrics — every number is actionable or clickable
- Action Required section drives daily behaviour; the partner always knows what to do next
- Tier progress bar is always visible — creates momentum toward tier upgrades
- Blazey partner assistant embedded bottom-right; answers commission, tier, deal status questions in natural language; never requires the partner to navigate to a rate table

### 4.4 Deal Registration — Under 90 Seconds on Mobile

The single most important flow in the entire portal. If it takes more than 2 minutes, partners email BlazeUp directly instead of registering, defeating the programme. Design target: 90 seconds on a mobile phone, standing in a prospect's car park after a meeting.

**Step 1 — Company** (30 seconds)
```
Company name: [ Acme Corporation           ]
Domain:       [ acme.com                   ] → auto-enriches: logo, HQ country, headcount
Country:      [ United States              ▾]
```

Auto-enrichment fires on domain blur via an enrichment API (Apollo/Clearbit). If the domain is already a BlazeUp tenant or an active deal, an inline warning appears immediately: "This domain already has an active BlazeUp account." Partner can still submit — it enters the conflict queue.

**Step 2 — Contact** (20 seconds)
```
First name: [         ]   Last name:  [         ]
Email:      [                         ]
Title:      [         ]   (optional)
```

**Step 3 — Deal** (30 seconds)
```
Estimated annual value:  $[ ________ ]
Expected close date:     [ ________ ]
Modules of interest:     ☐ HR  ☐ Payroll  ☐ CRM  ☐ Finance  ☐ IT  ☐ All
Deal type:               ○ Referral   ○ Reseller   ○ Co-sell with BlazeUp

┌────────────────────────────────────────────┐
│  Your estimated commission                  │
│  $18,000  (10% of $180,000 · Select tier)  │  ← Updates live as ACV is typed
│  Protected for 60 days on approval          │
└────────────────────────────────────────────┘
```

The projected commission shown in real-time is the single most powerful feature of the registration flow. It answers the partner's primary question ("is it worth my time to register this?") before they hit Submit.

**Step 4 — Confirm and Submit**
Summary card showing all fields → one-tap submit.

Immediate response (< 2 seconds):
```
Deal registered ✓
Deal ID: #BZ-2026-04812
Status: Pending SA approval (typically < 4 business hours)
You will receive an email and in-app notification when approved.
```

### 4.5 My Pipeline

A CRM-lite pipeline scoped entirely to BlazeUp deals. Partners are not asked to run their full sales pipeline here — they use Salesforce or HubSpot for that. This is BlazeUp-deal-specific.

```
[ All ] [ Registered ] [ Approved ] [ In Progress ] [ Closing ] [ Won ] [ Lost ]
                                                                    [+ Register Deal]

Search: [__________]   Filter: [ Deal Type ▾ ] [ Module ▾ ]

┌────────────────────┬─────────┬───────────┬──────────────┬────┬──────────┬──────┐
│ Company            │ ACV     │ Type      │ Stage        │Age │Close     │      │
├────────────────────┼─────────┼───────────┼──────────────┼────┼──────────┼──────┤
│ 🔒 Nexus Corp      │ $180K   │ Co-sell   │ Demo Done    │12d │ Jun 30   │ ⋯   │
│ ✅ Meridian Ltd    │ $95K    │ Referral  │ Approved     │ 5d │ Jul 15   │ ⋯   │
│ ⏳ Apex Group      │ $240K   │ Reseller  │ Registered   │ 2d │ Aug 01   │ ⋯   │
└────────────────────┴─────────┴───────────┴──────────────┴────┴──────────┴──────┘

🔒 = deal protection active   ✅ = approved   ⏳ = pending approval
```

**Deal Detail View:**

```
Nexus Corp                                             🔒 Protected until 30 Jun 2026
─────────────────────────────────────────────────────────────────────────────────────
$180K ACV   ·   Co-sell   ·   Registered 12 days ago   ·   Expected close: 30 Jun

TIMELINE
  ● Registered          22 Apr — Sarah Chen (you)
  ● Conflict check      22 Apr — Passed: no existing account or competing registration
  ✅ Approved           23 Apr — Jamie Walsh (BlazeUp) assigned as co-sell rep
  ● Demo completed      29 Apr — noted by you
  ○ Proposal sent       — upcoming

SHARED NOTES                                          [Add note]
  Jamie Walsh  1 May  "Sent proposal, waiting on procurement review. They have
                       budget sign-off by Jun 15. Need partner to confirm legal
                       entity details for MSA."
  Sarah Chen  2 May   "Confirmed — entity is Nexus Corp LLC, Delaware. Sending
                       over entity docs today."

YOUR COMMISSION PROJECTION
  $27,000  (15% of $180K · Advanced tier · Co-sell rate)
  Paid net-30 after close

DOCUMENTS                                             [Upload]
  NDA_Nexus_Signed.pdf       · 2 Apr
  BlazeUp_Proposal_v2.pdf    · 1 May

BlazeUp REP
  [Photo]  Jamie Walsh  ·  jamie@blazeup.ai  ·  [Schedule a call]
```

### 4.6 My Clients

The partner's book of business. Visible post-close only.

```
[ All ] [ Renewal This Quarter ] [ Health: At Risk ]   Search: [__________]

┌──────────────────┬─────────┬──────────────┬───────────┬────────────────────┐
│ Client           │ ARR     │ Health       │ Renewal   │ Modules Active     │
├──────────────────┼─────────┼──────────────┼───────────┼────────────────────┤
│ Nexus Corp       │ $180K   │ 🟢 Healthy  │ Apr 2027  │ HR · CRM · Finance │
│ Meridian Ltd     │ $95K    │ 🟡 At Risk  │ Jun 2026  │ HR only            │
│ Apex Group       │ $240K   │ 🔴 Inactive │ Aug 2026  │ CRM · IT           │
└──────────────────┴─────────┴──────────────┴───────────┴────────────────────┘
```

**Client Health Card (drill-in):**

```
Meridian Ltd                                         🟡 At Risk — renewal 18 Jun 2026
─────────────────────────────────────────────────────────────────────────────────────
ARR: $95K   ·   Closed: 14 Aug 2025   ·   Billing: Direct   ·   Deal: Referral

HEALTH SIGNALS
  Monthly active users:    42 of 210 licensed   (20% — low)
  Modules adopted:         1 of 6 licensed
  Last login (any user):   3 days ago
  Open support tickets:    2 (1 high severity)

BLAZEY INSIGHTS
  💡 "Meridian has 210 HR licences but is only using employee profiles and leave.
      Payroll and Expense modules are fully licensed but unused. Consider offering
      a half-day onboarding session to drive adoption before renewal."

RENEWAL PIPELINE
  Renewal date:  18 Jun 2026
  Deal registered: No       [Register Renewal Deal]
  BlazeUp CSM:  Priya Sharma · priya@blazeup.ai

COMMISSION HISTORY
  Original deal (Aug 2025):  $9,500 paid  ✅
  Renewal (if closes):        $9,500 projected
```

**Why this is the product's moat:** No partner programme in enterprise SaaS provides this. A Salesforce reseller never knows their client's Salesforce adoption rate. A BlazeUp partner knows — because BlazeUp is the system of record and the partner portal reads from the same data. Partners who join BlazeUp's channel programme have a structural advantage in retaining and expanding their book of business.

### 4.7 Commissions and Payouts

No mystery. Every dollar is traceable from deal close to bank transfer.

```
SUMMARY
Earned YTD:  $48,200   |   Pending:  $12,400   |   Paid:  $35,800

┌────────────────┬─────────────────┬──────────┬───────────────┬─────────────────────┐
│ Deal           │ Client          │ Amount   │ Status        │ Expected Payment    │
├────────────────┼─────────────────┼──────────┼───────────────┼─────────────────────┤
│ Nexus Corp     │ Nexus Corp      │ $27,000  │ ✅ Approved   │ Pays 30 Jul 2026   │
│ Meridian Ltd   │ Meridian Ltd    │ $9,500   │ ⏳ Pending   │ Awaiting deal close │
│ Apex Group     │ —               │ $24,000  │ 🔴 Disputed  │ Under review        │
│ Bright Retail  │ Bright Retail   │ $7,200   │ ✅ Paid      │ Paid 1 May 2026    │
└────────────────┴─────────────────┴──────────┴───────────────┴─────────────────────┘

[ Request Payout ]   [ Dispute Commission ]   [ Update Payout Details ]   [ Request Product-Failure Waiver ]
```

**Commission dispute flow:** Click deal → "Dispute commission" → one text field ("What's wrong?") → Submit. No form, no email, no ticket number hunting. BlazeUp partner team receives a Slack notification. SLA: 5 business days.

**Product-failure clawback waiver flow (locked — Renil, 2026-05-08):** If a client churned within the 12-month clawback window because of a confirmed BlazeUp product failure, click the clawback row → "Request product-failure waiver" → one text field for context → link the relevant support ticket(s) or incident report → Submit. SA partner-ops decides within 30 days. See §5.3 for the policy.

**Payout details:** Supports bank transfer (SWIFT for international, ACH for US, NEFT/IMPS for India, Vietnamese bank transfer). PDPL/PDPA compliant storage — banking details CSFLE-encrypted at rest.

### 4.8 Training and Certification

```
MY CERTIFICATIONS
  ✅ BlazeUp Sales Certified          Earned 15 Mar 2026  (renewed annually)
  ⏳ BlazeUp HR Specialist            In progress — 4.5h of 6h complete
  ○  BlazeUp CRM Specialist          Not started
  ○  BlazeUp Implementation Certified Not started

LEARNING PATHS
  ┌─────────────────────────────────────────────────────────────────────┐
  │ HR Specialist                                          4.5h / 6h   │
  │ ████████████████░░░░  75%                                           │
  │ Module 5: Payroll Configuration  →  [Continue]                     │
  └─────────────────────────────────────────────────────────────────────┘
```

Content hosting platform: see §12 OQ-8 (build vs. buy — Aashwij still owed). Completion triggers `blazeup.partner.certification.earned` → tier qualification engine re-evaluates.

### 4.9 Resources

- Co-branded pitch decks (partner name + logo auto-inserted via template engine)
- Product one-pagers per module (downloadable PDF)
- Battle cards: BlazeUp vs. Workday, Darwinbox, Zoho, Salesforce
- ROI calculator (web tool — partner fills in prospect details, gets a PDF)
- Partner-only pricing sheets (tiered by deal size)
- Demo environment: each partner gets one persistent sandbox tenant at `{partner-slug}-demo.blazeup.ai` — see §12 OQ-12 (sandbox-data service spec still owed by Khoa)
- API documentation: for partners who want to integrate deal registration into their own CRM via API

### 4.10 Partner Team

```
TEAM MEMBERS (4)

Sarah Chen         Admin     ·  Sales Certified  ·  HR Specialist
Marcus Lee         Member    ·  Sales Certified
Priya Rajan        Member    ·  No certifications yet
Tom Nguyen         Member    ·  In progress

[ Invite team member ]

REFERRAL LINKS
  Default link:   blazeup.ai/ref/bright-tech          [Copy] [QR code]
  Sarah Chen:     blazeup.ai/ref/bright-tech/sarah    [Copy]
  Per-campaign:   [ + Create campaign link ]           (for tracking specific events/channels)
```

Per-campaign referral links allow partners to measure which marketing activities drive signups. Analytics per link: clicks, conversions, ARR attributed.

---

## 5. SA Partner Module — `blazeup-subapp-sa-partners`

The SuperAdmin module manages the partner programme from BlazeUp's side. Mounted in `blazeup-hostapp-superadmin` at route `/partners`.

### 5.1 Partner Directory

```
[ All ] [ Registered ] [ Select ] [ Advanced ] [ Premier ] [ Pending Approval (3) ]

Search: [________________]   Filter: [ Region ▾ ] [ Tier ▾ ] [ Type ▾ ] [ Status ▾ ]

┌─────────────────┬────────────────┬─────────┬────────────┬──────────┬────────────┐
│ Partner         │ Tier           │ ARR     │ Open Deals │ Clients  │ Status     │
├─────────────────┼────────────────┼─────────┼────────────┼──────────┼────────────┤
│ Acme Systems    │ 🥇 Premier    │ $1.2M   │ 8          │ 34       │ Active     │
│ Nexus Partners  │ 🥈 Advanced   │ $380K   │ 3          │ 11       │ Active     │
│ Bright Tech     │ 🥉 Select     │ $95K    │ 1          │ 4        │ Active     │
│ Delta Corp      │ Registered    │ —       │ 0          │ 0        │ Pending    │
└─────────────────┴────────────────┴─────────┴────────────┴──────────┴────────────┘
```

**Partner Profile (drill-in):**
- Company info, logo, regions, type, agreement date, PSM assigned (dedicated when ≥$1.5M ARR; shared 1:3 otherwise — Renil 2026-05-08)
- Team members and their certifications
- Full deal history (all deals, historical + open, total ARR sourced)
- Commission ledger (all earned, pending, paid)
- Territory assignments
- Performance vs. tier thresholds (progress bars)
- Notes (internal — not visible to partner)
- Activity log: all SA actions on this partner account

**Partner Application Review (for new Registered applicants):**
```
Delta Corp  ·  Applied 3 May 2026

Company:      Delta Corp  ·  delta-corp.com  ·  Singapore
Contact:      Raj Patel · raj@delta-corp.com · CEO
Regions:      Singapore, Malaysia, Thailand
Type:         Reseller

Team certifications:  None yet (acceptable at Registered)

Agreement:    [ View signed Partner Agreement ]

[ Approve — Create Portal Account ]   [ Request More Info ]   [ Decline ]
```

> See §12 OQ-10 — Aashwij still owed: is partner-org approval a single SA-step or a staged workflow (legal review, agreement countersign before SA can approve)?

### 5.2 Deal Management — Approval Queue

The SA's primary daily workflow. Every registered deal lands here before the partner can use it.

```
PENDING APPROVAL (5)   CONFLICT QUEUE (1)   ALL DEALS

┌────────────────────────────────────────────────────────────────────────────────┐
│  Nexus Corp                                                                    │
│  Partner: Bright Tech (Select)  ·  ACV: $180K  ·  Type: Co-sell               │
│  Registered: 2 hours ago  ·  Domain: nexus-corp.com                            │
│                                                                                │
│  Conflict check:  ✅ No existing BlazeUp tenant at this domain                │
│                   ✅ No competing deal registrations                           │
│  Enrichment:      Nexus Corp LLC · 420 employees · New York, US · SaaS        │
│                                                                                │
│  Assign BlazeUp rep: [ Jamie Walsh            ▾ ]                              │
│                                                                                │
│  [ Approve + Assign ]   [ Reject ]   [ Request Info from Partner ]            │
└────────────────────────────────────────────────────────────────────────────────┘
```

**On Approve + Assign:**
- `blazeup.partner.deal.approved` published on Kafka
- Deal protection clock starts (60 days for Select, 90 days for Advanced+, 120 days for Premier)
- `commissionRate` + `rateTableVersion` stamped on `partner_deals` at this moment — rate locked at approval (PRD §6.3 authoritative per `ms-sa-partners-open-questions-v0.4.md` OQ-5)
- For co-sell deals above $100K ACV, the SA may propose an override to the 70/30 default split on this screen — change is recorded as a pending proposal until the partner accepts in the portal (Renil 2026-05-08; see §3 Scenario C)
- Assigned rep receives task in dogfood CRM: "Reach out to Bright Tech re: Nexus Corp co-sell"
- Partner receives in-app + email notification

**Deal protection expiry — auto-extend rule (locked — Renil, 2026-05-08):** When the protection window elapses without close, the system runs an **activity check**:

| Condition at expiry | System action |
|---|---|
| At least one stage update in the last 30 days **AND** never auto-extended before | **Auto-extend once** to 2× original window (Select 60d → 120d; Advanced 90d → 180d; Premier 120d → 240d). `blazeup.partner.deal.protection_extended` emitted. Partner notified. |
| No stage update in last 30 days, or already auto-extended once | **Hard expiry.** `blazeup.partner.deal.expired` emitted. Partner can request **manual SA extension** via portal — SA reviews on the deal record with reasoning required. |

The 30-day activity gate keeps the queue clean — stale deals cannot park indefinitely behind the protection shield while a partner sits on them.

**Conflict Queue:**
```
CONFLICT: Same domain registered by two parties

  Partner A:  Bright Tech  ·  Registered 2 May 10:14 AM
  Party B:    BlazeUp direct inbound  ·  Registered 3 May 09:00 AM
  Domain:     conflicted-prospect.com

  Prospect contacted: [ Yes — confirmed Bright Tech engagement  ○  No  ○  Cannot reach ]

  Decision: [ Award to Partner A ]  [ Award to BlazeUp Direct ]  [ Split (N/A for direct) ]
  Reasoning: [ _________________________________________________ ]  (required)

  [ Submit Decision ]  — Both parties notified with reasoning. Logged to audit trail.
```

### 5.3 Commission Configuration

A rate table managed entirely by SA operators — no code change required to adjust rates.

```
COMMISSION RATE TABLE

Deal Type × Tier          Referral    Reseller Margin    Co-sell
Registered                5%          —                  3%
Select                    10%         20%                8%
Advanced                  15%         30%                12%
Premier                   20%+5%Y2    35%                15%

[ Edit rates ]   [ Version history ]

ACTIVE SPIFF PROGRAMMES

  Vietnam HR Push Q2 2026
  Bonus: +5% on all HR module deals closed in Vietnam, 1 Apr–30 Jun 2026
  Applicable tiers: Select, Advanced, Premier
  [ Edit ]  [ Deactivate ]

[ + Add SPIFF Programme ]
```

**Clawback configuration:**

```
CLAWBACK POLICY

  If a client churns within:   12 months of go-live
  Clawback amount:             50% of paid commission
  Applies to deal types:       Referral, Co-sell
  Does NOT apply to:           Reseller (partner collected margin at invoice)
  Dispute window:              30 days from clawback notification

  PRODUCT-FAILURE WAIVER (locked — Renil, 2026-05-08)
  Trigger:         Partner requests waiver on clawback row
  Evidence req:    Linked support ticket(s) or post-incident report
  Reviewer:        SA partner-ops team
  Decision SLA:    30 days from waiver request
  Outcome:         Recorded as partial/full credit on the clawback debit
                   (no commission row deletion — ledger reconciles cleanly)
  Appeal:          None — SA decision is final and logged to audit trail

[ Edit policy ]
```

All clawback terms — including the product-failure waiver path — are displayed to the partner at commission approval time and on the clawback notification, never as a surprise. The waiver path closes the partner-trust gap without creating a blanket "blame the product" loophole — every waiver has a documented incident behind it.

### 5.4 Territory Management

```
TERRITORY ASSIGNMENTS

Partner           Regions                          Verticals         Exclusivity
Acme Systems      Vietnam · Thailand · Malaysia    All               Preferred (not exclusive)
Nexus Partners    UAE · Saudi Arabia · Qatar       HR + Payroll      Exclusive (HR vertical)
Bright Tech       United States                    SMB (<200 seats)  Preferred

[ + Assign Territory ]

TERRITORY RULES
  Exclusive:  Only this partner may register deals in this region/vertical combination.
              Conflicts auto-routed to this partner.
  Preferred:  Multiple partners may operate in this space. First-registered-wins on conflicts.
  None:       Open market. No geographic protections.
```

### 5.5 Analytics

```
PARTNER PROGRAMME HEALTH

Partner-Sourced ARR:        $4.2M   (28% of total ARR)   ↑ 12% vs last quarter
Deals Registered (MTD):     23
Approval Rate:              78%  (18 of 23 approved)
Win Rate (approved):        39%  (7 of 18 won)
Avg Partner Deal Size:      $142K   vs $98K direct
Avg Deal Velocity:          47 days  vs 62 days direct

FUNNEL
  Registered 23 → Approved 18 → In Progress 11 → Won 7 → Lost 4

Commission Paid YTD:        $380K
Commission Pending:         $95K
Clawbacks Issued YTD:       $12K
Clawback Waivers Granted:   $4K   ← Renil 2026-05-08 — separate tracking

TOP 5 PARTNERS BY ARR SOURCED
  1. Acme Systems        $1.2M   ·  34 clients   ·  🥇 Premier   ·  Shared PSM (1.2M < $1.5M)
  2. Nexus Partners      $380K   ·  11 clients   ·  🥈 Advanced
  3. Bright Tech         $95K    ·   4 clients   ·  🥉 Select
  4. Delta Corp          $62K    ·   2 clients   ·  Registered
  5. Atlas Group         $48K    ·   2 clients   ·  Registered

TIER DISTRIBUTION
  Premier: 2   Advanced: 4   Select: 9   Registered: 23
```

### 5.6 Commission Ledger (SA Approval Workflow)

All calculated commissions require SA approval before payout is queued. Two-eye principle for amounts > $10K.

```
PENDING APPROVAL (3)

  Bright Tech · Nexus Corp deal · $27,000
  Basis: $180K ACV × 15% (Advanced, Co-sell)
  Deal closed: 30 Jun 2026 · Tenant provisioned: 1 Jul 2026
  Clawback window: until 1 Jul 2027

  [ Approve for payout ]   [ Dispute ]   [ Request clarification ]
```

---

## 6. CRM Integration Architecture

### 6.1 The Contract

Partner-registered deals flow automatically into BlazeUp's dogfood CRM at `blazeup.blazeup.ai`. BlazeUp's sales team works all deals — direct and partner — in one pipeline. There is no separate partner deal management tool for BlazeUp's internal team. The SA partner module is the programme management tool (approvals, territories, commissions); the dogfood CRM is the sales execution tool.

### 6.2 Event-Driven Sync

```
PARTNER EVENT                           DOGFOOD CRM EFFECT
────────────────────────────────────────────────────────────────────────
partner.deal.registered            →   Create opportunity
                                        stage: 'Partner Deal — Pending Approval'
                                        source: 'partner_registered'
                                        owner: unassigned

partner.deal.approved              →   Update opportunity
                                        stage: 'Partner Deal — Approved'
                                        owner: assigned BlazeUp rep
                                        task: "Reach out to [partner] re: [prospect]"

partner.deal.protection_extended   →   Update opportunity meta
                                        protectionExpiresAt += original_window
                                        task: "Partner deal auto-extended — keep advancing"

partner.deal.won                   →   Close opportunity Won
                                        ARR stamped
                                        tenant_id stamped on go-live

partner.deal.lost                  →   Close opportunity Lost
                                        close reason from SA recorded

partner.deal.expired               →   Opportunity marked Stale
                                        task: "Follow up — partner deal protection expired"

partner.client.health_alert        →   Task on account record
                                        e.g., "Client health dropped to At Risk — partner notified"
```

### 6.3 Opportunity Record Shape (dogfood CRM)

```typescript
{
  name: "Nexus Corp [Partner: Bright Tech]",
  source: 'partner_registered' | 'partner_link' | 'direct' | 'inbound',
  attribution: {
    partnerId: ObjectId,
    partnerName: string,
    partnerTier: string,
    partnerDealId: ObjectId,
    dealType: 'referral' | 'reseller' | 'cosell',
    commissionRate: number,           // locked at deal approval
    rateTableVersion: string,         // ⬅ added (Renil 2026-05-08, OQ-5 v0.4)
    commissionAmount: number,         // projected at approval; final on close
    cosellSplit?: { partnerPct: number, blazeupPct: number, overrideApproved: boolean },  // ⬅ Scenario C
  },
  stage: string,
  estimatedACV: number,
  closedACV: number | null,
  expectedCloseDate: Date,
  assignedRepId: ObjectId | null,
  tenantId: ObjectId | null,         // set on tenant provisioning
  createdAt: Date,
}
```

---

## 7. Tenant Provisioning on Deal Close

When a partner deal closes, the provisioning path depends on the deal type. All paths converge on `blazeup.tenant.provisioned`.

### 7.1 Referral Close

```
Partner marks deal Won in portal
  OR
BlazeUp rep closes opportunity in dogfood CRM
       │
       ▼ Kafka: blazeup.partner.deal.won
       │
ms-sa-partners:
  ├── Commission calculated → blazeup.partner.commission.earned
  ├── Provision call → SA /internal/tenants/provision
  │      payload includes attribution block
  └── Tenant created → blazeup.tenant.provisioned
       │
       ├── Dogfood CRM: opportunity closed, account activated, tenant_id stamped
       ├── SA billing: subscription created (billed direct to new tenant)
       ├── Dogfood Projects: CSM onboarding project created
       ├── Partner portal: +1 client in My Clients, health card available
       └── Commission: queued for SA approval
```

### 7.2 Reseller Close

Same flow except `billing.model = 'reseller'`. BlazeUp creates an invoice addressed to the reseller partner at the discounted price. The tenant is provisioned normally. The reseller manages their billing relationship with the end client independently — and at whatever price they negotiate with the client (Renil 2026-05-08 — BlazeUp does not capture the sell price).

### 7.3 MSP Provisioning

```
MSP partner provisions a new tenant from partner portal
  [ + Add Managed Client ] button in My Clients
       │
       ▼
MSP fills in client details (company name, admin email, modules)
  + MSP ticket-content consent toggle (default OFF; can be enabled now or later by client admin)
       │
       ▼
ms-sa-partners calls SA /internal/tenants/provision
  { billingModel: 'partner_managed', billingPartnerId: X,
    mspTicketContentConsent: { granted: false, grantedAt: null, grantedBy: null } }
       │
       ▼
Tenant provisioned
  ├── BlazeUp invoices the MSP (not the client)
  ├── MSP gets scoped admin token for this tenant
  │      (configure modules, manage users, raise tickets — not payroll/sensitive PII)
  │      (ticket content gated on mspTicketContentConsent.granted — §9.2)
  └── Client tenant appears in MSP's "Managed Clients" list
```

### 7.4 Expansion Close

```
Partner registers expansion deal with existing tenant_id
       │
       ▼ Approved by SA
       │
Deal closes:
  ├── Additional modules/seats provisioned on existing tenant
  │      (no new tenant created)
  ├── Subscription line items updated in ms-billing
  ├── Expansion commission calculated on delta ARR (rate — see §12 OQ-16, Renil still owed)
  └── Partner portal: client ARR updated in My Clients
```

### 7.5 Tenant Record Attribution Block

Every partner-sourced tenant carries attribution permanently:

```typescript
attribution: {
  source: 'partner_referral' | 'partner_reseller' | 'partner_cosell'
          | 'partner_msp' | 'partner_link' | 'direct' | 'inbound',
  partnerId: ObjectId | null,
  partnerName: string | null,
  partnerTier: string | null,           // tier at deal close — locked
  dealId: ObjectId | null,
  commissionStructure: {
    rate: number,
    rateTableVersion: string,           // ⬅ added (Renil 2026-05-08, OQ-5 v0.4)
    type: 'referral' | 'cosell',
    baseACV: number,
    clawbackExpiresAt: Date,            // typically go-live + 12 months
    productFailureWaiver?: {            // ⬅ Renil 2026-05-08
      requestedAt: Date,
      requestedBy: ObjectId,
      decision: 'pending' | 'granted' | 'denied',
      decidedAt?: Date,
      decidedBy?: ObjectId,
      evidence: ObjectId[],             // support tickets / incident reports
    },
  } | null,
  billingModel: 'direct' | 'reseller' | 'partner_managed',
  attributionHistory?: Array<{           // ⬅ Renil 2026-05-15 — preserved on any SA override or MSP handoff
    partnerId: ObjectId | null,
    source: string,
    effectiveFrom: Date,
    effectiveTo: Date,
    changedBy: ObjectId,                 // SA admin userId
    reason: string,                      // mandatory written justification
    approvedBy: ObjectId,                // second SA admin (two-eye rule)
  }>,
}

// On the TENANT record (for MSP-managed tenants only):
mspTicketContentConsent: {              // ⬅ Renil 2026-05-08, Scenario G / §9.2
  granted: boolean,                     // default false
  grantedAt: Date | null,
  grantedBy: ObjectId | null,           // tenant admin who toggled it on
  revokedAt: Date | null,
  revokedBy: ObjectId | null,
}
```

---

## 8. Technical Architecture

### 8.1 New Services and Repos

| Artifact | Type | Description |
|---|---|---|
| `blazeup-microservice-sa-partners` | Backend MS | Partner accounts, deal FSM, commission engine, territory, referral attribution |
| `blazeup-hostapp-partner` | Frontend host | Shell for `partner.blazeup.ai`, Tailwind prefix `pp-` |
| `blazeup-subapp-sa-partners` | SA subapp | Partner directory, deal approval, commissions, territories, analytics |
| `blazeup-subapp-partner-dashboard` | Partner subapp | Home, pipeline, clients, commissions (federated into partner host) |
| `blazeup-subapp-partner-training` | Partner subapp | Certification and training (platform — see §12 OQ-8 build-vs-buy) |

### 8.2 MongoDB Collections (`ms-sa-partners`)

```typescript
partner_accounts
  { tenantId (BlazeUp SA), name, slug, type, tier, status, regions[], verticals[],
    managerId (BlazeUp PSM), managerAllocation: 'dedicated' | 'shared',  // ⬅ Renil 2026-05-08
    agreementSignedAt, certifications[], contacts[],
    referralLinks[], apiKeys[], notes[], createdAt, updatedAt }

partner_deals
  { partnerId, prospectDomain, prospectCompany, prospectContact{},
    dealType, estimatedACV, closedACV, expectedCloseDate, closedAt,
    stage, assignedRepId, conflictStatus, conflictResolution{},
    billingModel, protectionExpiresAt,
    protectionExtensionCount: number,   // ⬅ Renil 2026-05-08 — auto-extend gate (max 1)
    lastStageUpdateAt: Date,            // ⬅ Renil 2026-05-08 — 30-day activity check
    commissionRate: number,             // ⬅ stamped at approval (OQ-5 v0.4)
    rateTableVersion: string,           // ⬅ stamped at approval (OQ-5 v0.4)
    cosellSplit?: { partnerPct, blazeupPct, overrideApproved },  // ⬅ Scenario C
    tenantId (set on close),
    commissionSnapshot{rate, amount, status, paidAt},
    notes[], documents[], createdAt, updatedAt }

partner_commissions
  { partnerId, dealId, tenantId, amount, rate, basis,
    status: 'pending' | 'approved' | 'paid' | 'disputed' | 'clawback' | 'clawback_waived',
    paidAt, clawbackAmount, clawbackReason, clawbackWaiver?{requestedAt, decision, evidence[]},
    disputeLog[], payoutBatchId, createdAt, updatedAt }

partner_territories
  { partnerId, regions[], verticals[], exclusivityType, effectiveFrom, effectiveTo }

partner_certifications
  { partnerId, userId, certificationType, earnedAt, expiresAt, score }

partner_referral_links
  { partnerId, userId (optional), slug, campaignName,
    clicks, conversions, attributedARR, createdAt }

partner_rate_table
  { version, effectiveFrom,
    rates: {
      tier × dealType → {
        nn: { rate, windowYears },        // Net New — full rate for X years from go-live
        en: { rate },                     // Existing customer Net New licenses — after NN window
        ee: { rate },                     // Existing customer Existing licenses — renewal only
      }
    },
    spiffProgrammes[{ name, bonus, regions[], tiers[], validFrom, validTo }] }
  // Commission engine classifies each deal as NN/EN/EE at calculation time
  // based on tenant.goLiveAt + nn.windowYears. All values SA-configurable.

partner_conflicts
  { dealId, parties[], status, resolution, resolvedBy, resolvedAt, reasoning }
```

### 8.3 Kafka Events

```
blazeup.partner.registered             partner account created (pending SA approval)
blazeup.partner.approved               SA approved partner application
blazeup.partner.tier.changed           tier upgraded or downgraded (quarterly)
blazeup.partner.deal.registered        deal registration submitted
blazeup.partner.deal.approved          SA approved deal, protection clock starts
blazeup.partner.deal.rejected          SA rejected deal (with reason)
blazeup.partner.deal.conflict_raised   two parties registered same domain
blazeup.partner.deal.protection_extended  ⬅ Renil 2026-05-08 — auto-extend fired
blazeup.partner.deal.won               deal closed won
blazeup.partner.deal.lost              deal closed lost
blazeup.partner.deal.expired           deal protection window elapsed without close
blazeup.partner.commission.earned      commission calculated on close
blazeup.partner.commission.paid        payout processed
blazeup.partner.commission.waiver_decided  ⬅ Renil 2026-05-08 — product-failure waiver outcome
blazeup.partner.client.health_alert    client health signal changed (at-risk, inactive)
blazeup.partner.msp_ticket_consent.changed  ⬅ Renil 2026-05-08 — client granted/revoked
blazeup.partner.client.transferred         ⬅ Renil 2026-05-15 — MSP handoff, old+new partnerId stamped
blazeup.partner.sandbox.reset_requested    ⬅ Renil 2026-05-15 — partner triggers demo sandbox re-seed
```

All events carry the standard BlazeUp Kafka envelope: `eventId`, `eventType`, `schemaVersion`, `tenantId` (BlazeUp SA tenant), `occurredAt`, `triggeredBy`, `correlationId`.

### 8.4 Referral Attribution Service

```
1. Partner share link: blazeup.ai/ref/{partner-slug}[/{user-slug}][/{campaign}]

2. On click:
   GET blazeup.ai/ref/{slug}
   → Server writes to Redis: attr:{sessionToken} = { partnerId, userId?, campaignId, clickedAt }
     TTL: 30 days
   → Server sets first-party cookie: __blazeup_ref={sessionToken}; SameSite=Lax; HttpOnly
   → 302 redirect to blazeup.ai/signup?ref={sessionToken}

3. On signup (or trial activation):
   → /v1/tenants/provision reads __blazeup_ref cookie or ?ref param
   → Resolves attribution from Redis
   → Stamps tenant.attribution block
   → Fires blazeup.partner.deal.won (auto, no deal registration required)
   → Commission calculated automatically

4. Edge cases:
   - Multiple referral link clicks: first-touch wins (TTL is set on first click only)
   - Direct signup with no cookie: no partner attribution; remains direct
   - Prospect clicked 40 days ago: TTL expired, no attribution
```

### 8.5 APIs

Core routes in `ms-sa-partners`:

```
Partner management (SA-only):
GET    /internal/partners                     list all partners
POST   /internal/partners                     create partner account
PATCH  /internal/partners/:id                 update partner
POST   /internal/partners/:id/approve         approve application
GET    /internal/partners/:id/commissions     commission ledger
POST   /internal/partners/:id/commissions/:cid/approve  approve payout
POST   /internal/partners/:id/commissions/:cid/waiver-decision  ⬅ Renil 2026-05-08

Deal management (SA-only):
GET    /internal/deals                        all deals, filterable
PATCH  /internal/deals/:id/approve            approve deal registration (stamps rate+version, cosellSplit)
PATCH  /internal/deals/:id/reject             reject with reason
PATCH  /internal/deals/:id/protection-extend  manual SA extension (after auto-extend exhausted)  ⬅
GET    /internal/deals/conflicts              conflict queue
PATCH  /internal/deals/conflicts/:id/resolve  resolve conflict

Commission engine (SA-only):
GET    /internal/commission/rates             current rate table
PUT    /internal/commission/rates             update rates (versioned)
POST   /internal/commission/spiff             create SPIFF programme

Partner portal APIs (partner-JWT-gated):
GET    /v1/partner/dashboard                  dashboard stats
POST   /v1/partner/deals                      register deal
GET    /v1/partner/deals                      list own deals
PATCH  /v1/partner/deals/:id                  update deal (notes, docs)
POST   /v1/partner/deals/:id/cosell-split-accept  ⬅ Renil 2026-05-08 — accept SA-proposed override
POST   /v1/partner/deals/:id/protection-extend-request  ⬅ request manual SA extension
GET    /v1/partner/clients                    list post-close clients
GET    /v1/partner/clients/:tenantId/health   client health metrics
GET    /v1/partner/clients/:tenantId/tickets  list tickets (count+severity always; content gated on consent)  ⬅
GET    /v1/partner/commissions                commission history
POST   /v1/partner/commissions/:id/dispute    raise dispute
POST   /v1/partner/commissions/:id/waiver     request product-failure waiver (with evidence)  ⬅
GET    /v1/partner/referral-links             list referral links
POST   /v1/partner/referral-links             create campaign link
```

### 8.6 Redis Keys (`ms-sa-partners`)

```
partners:account:{partnerId}                → 1 hour (tier, status, config, managerAllocation)
partners:rate_table:current                 → 24 hours (commission rates)
partners:rate:{tenantId}:{tier}             → 1 hour (rate lookup; invalidated on rate-table update)
partners:deal:{dealId}:protection           → TTL = protectionExpiresAt
partners:attr:{sessionToken}                → 30 days (referral attribution)
partners:conflict:{domain}                  → 7 days (active conflict lock)
```

---

## 9. Security and Compliance

### 9.1 Partner Portal Auth

- Separate JWT issuer from tenant and SA (distinct `iss` claim)
- 8-hour access token, 30-day refresh token
- MFA — required for `PARTNER_ORG_ADMIN` role and for Advanced/Premier tiers. **Definitive policy still owed** — see §12 OQ-14 (role-vs-tier axis conflict between this PRD §9.1 and `sa-portal-architecture-v2.6.md` §14.8)
- Session scoped to `partnerId` — partners cannot see other partners' data under any circumstances

### 9.2 MSP Access Scope

MSP partners have scoped admin access to their managed tenants. Hard limits enforced by a `PartnerScopeGuard` in every MS:

| Access | MSP Can | MSP Cannot |
|---|---|---|
| Module configuration | ✅ | — |
| User management (add/remove/roles) | ✅ | — |
| Support ticket **count + severity** | ✅ (always) | — |
| Support ticket **content (body, attachments)** | ✅ **only after client opt-in** (default OFF) | See content until client opts in |
| Employee PII | ✅ (name, email) | Payroll, salary, health data |
| Export data | ❌ | — |
| Billing configuration | ❌ | — |
| Impersonate users | ❌ | — |

**Ticket-content consent (locked — Renil, 2026-05-08):** Client opt-in is captured at tenant provisioning (or later by the tenant admin) and stored on the tenant record as `mspTicketContentConsent { granted, grantedAt, grantedBy, revokedAt?, revokedBy? }`. The default is **OFF**. `PartnerScopeGuard` checks this flag on every MSP request that resolves ticket body content; without consent the body is replaced by a sentinel "Content restricted — client has not granted MSP visibility." Revocation is immediate. Grant/revoke events emit `blazeup.partner.msp_ticket_consent.changed` for audit. The consent record is the legal basis for PDPA / PDPL compliance on cross-tenant ticket data access.

### 9.3 Data Residency

Partner prospect data (deal registrations) stored in the BlazeUp SA region (us-west1 today). When Middle East region is added: partners in UAE/Saudi store prospect data there. PDPL-compliant — prospect's contact details are never transferred cross-region without consent.

### 9.4 Audit Trail

Every SA action on partner data is written to the SA audit log (`sa_audit_log` collection, Tier J):
- Deal approval / rejection (with reasoning)
- Deal protection extension (auto and manual)  ⬅ Renil 2026-05-08
- Conflict resolution (with reasoning, immutable)
- Co-sell split override approval (with partner's written acceptance)  ⬅ Renil 2026-05-08
- Commission approval / dispute resolution
- Product-failure waiver decision (with linked evidence)  ⬅ Renil 2026-05-08
- MSP ticket-content consent grant / revoke  ⬅ Renil 2026-05-08
- Territory assignment changes
- Rate table modifications (versioned, every version preserved)

---

## 10. Effort Estimates

| Track | Deliverables | Estimate |
|---|---|---|
| `ms-sa-partners` — core | Collections, deal FSM, APIs, Kafka events, commission engine | 4 weeks |
| `ms-sa-partners` — dogfood CRM bridge | `DogfoodCrmBridge` consumer, opportunity create/update | 3 days |
| `ms-sa-partners` — referral attribution | Link tracking, Redis attribution, self-signup path | 1 week |
| `ms-sa-partners` — Renil-locked surface | Auto-extend cron + activity gate; cosell-split override flow; product-failure waiver workflow; MSP ticket-consent guard wiring; managerAllocation field on partner_accounts | 1 week |
| `blazeup-hostapp-partner` | Portal shell, auth, nav, federation scaffold | 1 week |
| Partner portal subapps | Dashboard · Deal Registration · Pipeline · Client Health (with ticket-content gating) | 4 weeks |
| Partner portal subapps | Commissions (incl. waiver request UI) · Training · Resources · Team · Settings | 3 weeks |
| `blazeup-subapp-sa-partners` | Partner directory · Deal approval (with cosell-override + extension UI) · Conflict queue · Territories · Waiver review queue | 3.5 weeks |
| SA analytics + commission ledger | Analytics dashboard · Commission approval workflow · Waiver-tracking metric | 2 weeks |
| Blazey partner assistant | 4 tools (commission query, deal status, tier projection, client health) + skill file | 1 week |

**Critical path to partner programme v1 (deal registration → approval → dogfood CRM → tenant creation → commission):** `ms-sa-partners` core + Renil-locked surface + CRM bridge + portal deal registration + SA approval queue = **~7 weeks** (added 1 week for the surface that came out of Renil's lock-in).

**Full partner portal (all pages + SA module + attribution):** ~14 weeks.

**Hard prerequisite:** the build cannot start on any partner-auth surface until Auth Hardening Phase 0 merges (§12 B1). Even if engineering is staffed, the auth track is dark until that gate closes.

---

## 11. Locked Decisions — Renil, 2026-05-08

The seven programme-policy questions Renil owned in v1.0 / v1.1 are now closed and embedded throughout this PRD. This table is the authoritative index — the wording source-of-truth lives in [`ms-sa-partners-open-questions-v0.4.md`](./ms-sa-partners-open-questions-v0.4.md) OQ-19 → OQ-25.

| ID (v1.1) | Cross-ref (v0.4) | Topic | Decision | Embedded in |
|---|---|---|---|---|
| Q1 | OQ-19 | Reseller pricing authority | Partner sets own end-client price; BlazeUp does not capture it on any record | §2.2 · §7.2 |
| Q2 | OQ-20 | Deal-protection expiry | Auto-extend once (2× window) if ≥1 stage update in last 30 days; otherwise hard expiry → partner may request manual SA extension | §5.2 |
| Q3 | OQ-21 | MSP tier qualification basis | Total ARR managed (full book), not net-new logos only | §2.2 |
| Q4 | OQ-22 | MSP ticket-content visibility | Client opt-in, default OFF; count + severity always visible; consent revocable | §3 Scenario G · §7.3 · §9.2 |
| Q5 | OQ-23 | Co-sell commission split | 70 / 30 default; SA may propose override above $100K ACV — partner agreement required, locked at approval | §3 Scenario C · §5.2 · §8.5 |
| Q6 | OQ-24 | Clawback on product failure | Waived on confirmed product failure with evidence; SA reviews within 30 days; decision logged and final | §5.3 · §4.7 |
| Q7 | OQ-25 | Dedicated PSM threshold | Dedicated PSM at $1.5M ARR within Premier; below threshold shared at max 1:3; reviewed annually | §2.1 · §5.1 · §5.5 |

Schema impact summary (now in §7.5 and §8.2):
- `partner_accounts.managerAllocation: 'dedicated' | 'shared'`
- `partner_deals.protectionExtensionCount`, `lastStageUpdateAt`, `commissionRate`, `rateTableVersion`, `cosellSplit`
- `partner_commissions.status: 'clawback_waived'` (new) + `clawbackWaiver{}` block
- `tenant.attribution.commissionStructure.productFailureWaiver{}`
- `tenant.mspTicketContentConsent{}`

---

## 12. Open Questions & Blockers — STILL OWED

Items below are **not** yet resolved. The 6 BLOCKING items must close before the named implementation slice can start. Sourced from [`partner-management-clarification-v1.0.md`](./partner-management-clarification-v1.0.md) and [`ms-sa-partners-open-questions-v0.4.md`](./ms-sa-partners-open-questions-v0.4.md).

### 12.1 BLOCKING — implementation cannot start until resolved

| ID | Question | Owner | Blocks | Status |
|---|---|---|---|---|
| **B1** (OQ-13 clarification doc) | **Auth Hardening Phase 0 merge timeline.** PRs #633–#641 must merge before any partner JWT class, OAuth 2.0 server, or partner-issued tokens go live. **Decision (Renil, 2026-05-15): Engineer to work directly with Auth team to drive PRs #633–#641 to completion. All non-auth coding (deal FSM, commission engine, portal UI, SA module) to proceed in parallel without waiting.** Auth surfaces (partner JWT issuance, token validation, MFA enforcement) remain gated on merge — do not wire live auth until PRs land. | **Auth team** | Partner auth surfaces only — all non-auth slices unblocked | **Unblocked — in progress with Auth team** |
| **B2** (OQ-9 clarification doc) | **First-admin enrollment flow.** **Decision (Renil, 2026-05-15): Follow the tenant creation model exactly (`tenant-creation-module-spec-v1.1.md` §4.6 + §6.6).** On SA approval: (1) `ms-sa-partners` creates a `PARTNER_ORG_ADMIN` user record `{ partnerId, email: primaryContactEmail, userType: 'PARTNER_ORG_ADMIN', status: 'PENDING_ACTIVATION' }`. (2) `blazeup.partner.approved` Kafka event triggers `ms-notification` to send a welcome/activation email to the primary contact. (3) Partner self-sets their own password on activation link click — no SA-created credentials, no temporary password. (4) Token format + TTL deferred to Auth team's activation token standard (same token infra used for tenant admin activation). | **Auth team (in parallel with B1)** | `partner-iam` implementation | **Resolved** |
| **B3** (OQ-10 clarification doc) | **Partner-org approval workflow stages.** **Decision (Aashwij, 2026-05-15): Staged workflow (Option B).** Three stages: (1) **SA Review** — SA operator reviews the application; signed partner agreement must be attached before SA can advance. If missing, SA clicks "Request agreement" which notifies the applicant. (2) **Legal Countersign** — Legal team countersigns the agreement inside the SA portal. SA cannot proceed to final approval until Legal countersign is recorded. (3) **SA Final Approval** — SA clicks Approve → `blazeup.partner.approved` emitted → `PARTNER_ORG_ADMIN` user created (B2 flow). At any stage SA may Decline with a mandatory reason (logged to audit trail). The SA application review UI (§5.1) must surface all three stages as a visible FSM — not a single Approve/Decline button. | **Auth team + SA subapp team** | SA partner application review UI (§5.1) | **Resolved** |
| **B4** (OQ-11 clarification doc) | **Partner-managed tenant linking — edge cases.** **Decision (Renil, 2026-05-15):** **(a) Partner involved, no registration:** No commission, no exceptions. Consistent with Scenario I — no registration = no attribution. Rule is absolute to prevent retroactive dispute claims. **(b) Tenant pre-dates partner programme:** SA may add "prospective attribution" (partner attach) — applies to future expansion deals and renewals only, never retroactive to original deal. SA must record written business justification, logged to audit trail. Original commission history unchanged. **(c) MSP handoff:** SA-only action. Outgoing MSP requests handoff in portal (cannot transfer unilaterally). SA confirms both parties (or client) agree, updates `attribution.partnerId` to new MSP. Old MSP commission history preserved. New MSP earns from handoff date forward. `blazeup.partner.client.transferred` Kafka event emitted. **(d) SA override of `tenant.attribution`:** Permitted but requires two-person SA approval (same two-eye principle as commission >$10K) + mandatory written reason + original attribution preserved in `attributionHistory[]` array (never deleted, superseded only). | — | `tenant.attribution` schema (§7.5) | **Resolved** |
| **B5** (OQ-12 clarification doc) | **`blazeup-microservice-sandbox-data` spec.** **Decision (Renil, 2026-05-15):** Three-profile model (follows `marketplace-prd-v1.0.md` pattern). **Profiles:** SMB (50 employees, HR + Expense + CRM + IT Assets) · Mid-market (200 employees, all core modules + Payroll stubs + Recruitment + Compliance) · Enterprise (500 employees, all modules + Multi-entity). Partner selects profile at provisioning; can switch on reset. **Collections seeded (all profiles):** `employees`, `departments`, `leave_requests`, `expense_reports`, `expense_categories`, `crm_contacts`, `crm_deals`, `assets`, `tickets`. Payroll: pre-computed stub rows only (no real payroll run). Compliance + Recruitment: Mid-market and Enterprise profiles only. **Refresh policy:** On-demand reset as primary — partner clicks "Reset demo" in portal, sandbox re-seeds within 5 minutes, partner picks profile on reset. Optional weekly auto-reset toggle (default OFF) to prevent surprise wipes mid-demo-cycle. Reset flow: `blazeup.partner.sandbox.reset_requested` Kafka event → sandbox-data service truncates tenant collections + re-seeds from profile template. | **Khoa (implementation)** | Partner sandbox provisioning (`{slug}-demo.blazeup.ai` — §4.9) | **Resolved** |
| **B6** (OQ-16 clarification doc) | **Expansion deal commission rate.** **Decision (Renil, 2026-05-15): Fully SA-configurable. Commission engine must support a 3-stage customer lifecycle model — rates and transition timings are SA-managed, not hardcoded.** The three stages: **(1) NN — Net New:** From go-live for X years (SA-configured per tier). Full new-logo rate applies. Partner sourced this customer and earns full credit during the honeymoon window. **(2) EN — Existing customer, Net New licenses:** After NN window expires. Customer is now established, but partner is still expanding the account with new modules or seats. A separate EN rate applies (lower than NN, SA-configured). **(3) EE — Existing customer, Existing licenses:** After a further SA-configured period. Customer is fully mature — renewals of existing licenses only. Lowest commission tier (SA-configured; may be zero for some tiers). `partner_rate_table` schema must store all three rate bands per tier × deal-type combination. Commission engine classifies every deal at calculation time (NN / EN / EE) based on `tenant.goLiveAt` + configured window durations. Specific rates and window durations pending industry benchmarking — SA operators configure before programme launch. | **Commission engine team** | Commission engine for Scenario F (Expansion) | **Architecture resolved — rates TBD (SA-configurable before launch)** |

### 12.2 Non-blocking but still open

| ID | Question | Owner | Impact |
|---|---|---|---|
| OQ-8 (clarification) | Training platform — build on dogfood LMS vs. buy (Docebo / Thought Industries) for v1? | Aashwij | Training subapp scope (§4.8) · time-to-launch |
| OQ-14 (clarification) | TOTP requirement — `sa-portal-architecture-v2.6.md` §14.8 says role-based (mandatory for `PARTNER_ORG_ADMIN`); this PRD §9.1 says tier-based (Advanced+). Which is authoritative? Or both? | Renil | `partner-iam` MFA enforcement logic |
| OQ-15 (clarification) | "Grace quarter" definition for tier downgrade — full next quarter after announcement, or remainder of current quarter? | Aashwij | Tier FSM timing |
| OQ-17 (clarification) | Conflict-loser 90-day re-registration — auto-unlock + notification, or manual partner re-submit with no system support? | Aashwij | Deal FSM · `partner_conflicts` design |
| OQ-18 (clarification) | Rate-table change retroactivity — confirm rates lock at deal approval (not registration, not invoice). PRD §6.3 and §5.2 both assert "locked at approval"; OQ-5 (v0.4) corrected this on 2026-05-11. Treat as confirmed pending Renil sign-off. | Renil | Commission engine version-pin behaviour |

### 12.3 Pending Legal / Compliance review

| ID | Question | Owner | Notes |
|---|---|---|---|
| OQ-17 (v0.4) | GDPR partner-org erasure spec — which fields can be pseudonymised vs. retained (commission records have 7-year US / 8-year India retention obligations)? | Legal + Compliance | Pending Legal sign-off |
| OQ-18 (v0.4) | Impersonation audit — when SA staff impersonates a tenant referred by a partner, does the partner get an active notification (email / in-portal) or audit log only? | Legal + Compliance | Pending decision; affects `auth.impersonation.partner-notified` Kafka event |

### 12.4 Hard build gates (summary)

Per `partner-management-clarification-v1.0.md` §15, nothing in the affected build slice moves forward until **B1–B6** are resolved. The remaining open questions in §12.2 / §12.3 do not block sprint start but should land before the affected work item enters scope.

| Gate | Owed By | Earliest needed for |
|---|---|---|
| **B1 — Auth Phase 0** | Auth team (engineer collaborating directly) | Partner auth surfaces only — non-auth coding proceeds now |
| **B2 — First-admin enrollment** | Renil | `partner-iam` ticket start (~week 11 day 1) |
| **B3 — Org approval workflow** | Aashwij | SA application review UI start (~week 11) |
| **B4 — Attribution edge cases** | Renil | Tenant provisioning schema freeze (~week 11) |
| **B5 — Sandbox-data spec** | Khoa | Partner-portal week 3 (sandbox per-partner provisioning) |
| **B6 — Expansion rate** | Renil | Commission engine week 4 (Scenario F coverage) |
