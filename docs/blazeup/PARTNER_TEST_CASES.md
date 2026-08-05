# Partner Platform — Test Plan (Automation)

> Generated from the test plan. NOT_STARTED test cases show the name only; BLOCKED show the block reason; PASSED/FAILED show full description, steps (with expected per step), overall expected, and notes.

## 0. Candidate MISSING test cases (Figma design exists, no plan TC)

These SA-side partner-management workflows have a "Ready for dev" Figma design (`design_partner/…`, `[PN…]`) but **no corresponding TC in the test plan**. Suggested to add (all SA-side / stgsa Partners area). Add to the plan then automate once the UI is deployed.

| Design | Suggested TC |
|---|---|
| PN002 View Partner Detail page | SA partner detail (Overview / Deals / Commission / Members / Notes) loads |
| PN004 Reject partner application | SA reject application (+ reason) |
| PN005 Resend expired activation invite | SA resend invite email |
| PN014 Manage partner team (deactivate/reactivate member) | SA deactivate + reactivate a partner's member (+ reason) |
| PN015 Suspend active partner | SA suspend partner |
| PN016 Reactivate suspended partner | SA reactivate partner |
| PN027 Request additional info from applicant | SA request-info (part of the FSM) |
| PN011 Mark deal Won → trigger commission calc | SA mark-won (UI) [+ API commission-calc] |
| PN019 Mark deal Lost | SA mark-lost |
| PN027 Review custom plan request | SA review/respond custom-plan request |
| PN028 Propose co-sell split override (ACV > $100K) | SA co-sell split override |
| PN013 Process commission clawback on early churn | SA process-clawback |

## 1. UI

### UI · COMMISSIONS

#### PARTNER_UI_COMMISSIONS_001
**Note (BLOCKED):** Type estimated annual value → commission projection updates live (in the deal-register wizard, step 2). Blocked on test data (verified live 2026-07-27): the test partner has **no commission rate configured** — `/resources` shows *"Commission Rates: No rates configured yet. Contact your programme manager."* The projection is `Total rate × Estimated ACV`, so with an empty rate it computes **no value** (probed: changing inputs shows no `$` projection). Also the ACV isn't a direct input — "Estimated ACV / Rate / Projected commission" are collapsible display sections in the wizard (ACV appears derived from plan × seats), so there's nothing to "type" for a live rate×ACV calc. Unblock when a commission **rate is configured** for the test partner (via SA rate-table) so the projection produces a verifiable value.
#### PARTNER_UI_COMMISSIONS_002
**Test Description:** Open the Commissions page and confirm the earned/pending/paid summary totals + ledger status tabs render. Read-only: works with an empty ledger (amounts may be $0) — verifies the page structure, not specific data.
**Setup (precondition):** Log in as the channel-partner user; open `/commissions` via the shell and wait for the "Commissions" READY_MARKER; let the data settle.
**Test Steps:**
1. The 4 summary totals render, each with a $ amount.
   → Expected: **Pending Payout**, **Paid YTD**, **Total Earned**, **Clawback Risk** cards each show a $ value (e.g. $0 on an empty ledger).
2. All ledger status tabs are visible.
   → Expected: **All / Earned / Pending / Approved / Paid / Disputed / Clawback** tabs render.
**Expected (overall):** The Commissions page renders its summary totals + all ledger tabs (independent of how many commissions exist).
**Note:** PASSED — verified 2026-07-28 (TC 12060302). First COMMISSIONS content test — establishes the `CommissionsPage` page-object (summary cards, ledger tabs). Empty ledger shows "No commissions yet" (partner has no won deals). Negative counterpart: N/A — read-only view. Idempotency: N/A — read-only.
#### PARTNER_UI_COMMISSIONS_003 — BLOCKED (no ledger data)
**Intent:** Trace a commission row — open a row and verify the full lifecycle fields (deal → close → rate/version → approval → payout → clawback/waiver → payment status); totals reconcile to the visible rows.
**Block reason:** The commission ledger is **empty** — the test partner has no **Won** deals, so no commission rows exist ("No commissions yet"). Nothing to open / verify. Data-dependency chain: rate configured (SA_PARTNER_MODULE_009, not deployed) → deal approved (SA deal queue blocked by BUG-025) → deal Won → commission row. Unblock once at least one commission exists in the ledger.
#### PARTNER_UI_COMMISSIONS_004 — BLOCKED (no ledger data)
**Intent:** Submit a commission dispute from a single text field on a commission row.
**Block reason:** Same as _003 — no commission rows in the ledger to dispute (partner has no Won deals → empty ledger). Needs a real commission entry first (rate → approved deal → Won).
#### PARTNER_UI_COMMISSIONS_005 — BLOCKED (no ledger data)
**Intent:** Submit a product-failure waiver request with evidence linked to a commission/clawback row.
**Block reason:** Same as _003/_004 — no clawback-eligible commission row exists (empty ledger). Needs a commission in a clawback-eligible state first.
#### PARTNER_UI_COMMISSIONS_006 — BLOCKED (UI + data not available) — Security
**Intent:** Approve a commission payout **> $10K** — two-eye approval is enforced (one person cannot approve a large payout alone).
**Block reason:** Needs (a) a payout > $10K pending approval — which requires a Won deal → commission → payout (empty ledger, blocked as _003), and (b) the two-eye approval UI (SA-side, design PN012) which is **not deployed** on staging. Unblock when both the payout data + the two-eye approval UI exist.
#### PARTNER_UI_COMMISSIONS_007 — BLOCKED (SA-side config UI not deployed)
**Where:** per the Figma design (PN021) the clawback **policy/waiver** is **SA-side** — stgsa → Partners → Commission → Commission configuration → **Clawback settings** + a **Waiver Review Queue** (not the partner-portal Commissions page). Design ready-for-dev.
**Intent:** Display Clawback notification — policy terms and the product-failure waiver path are visible (sensitive details masked).
**Block reason:** The SA Commission **configuration** view (which holds Clawback settings + the Waiver Review Queue) is **not deployed on staging** (re-verified 2026-07-30, same finding as _009/_010: no "View configuration" entry on `/partners/commissions`, config routes 404). An earlier note here checked the partner-portal `/commissions` (its "Clawback" tab only filters the empty ledger) — the actual clawback-policy/waiver experience is SA-side per PN021. Unblock when FE deploys the Commission configuration view.
#### PARTNER_UI_COMMISSIONS_008 — BLOCKED (Blazey AI feature)
**Intent:** Ask the Blazey AI assistant a commission question → get a context-aware answer (correct deal/tier/rate for this partner, without exposing other partners) with an actionable next step.
**Block reason:** Depends on the **Blazey AI assistant** (deferred AI feature) + real commission context data. The assistant is not available/testable on the current build, and the ledger is empty (no commission context). Unblock when Blazey ships + commission data exists.
#### PARTNER_UI_COMMISSIONS_009 — BLOCKED (UI not located) — Security
**Intent:** Edit payout / banking details by region → only the correct region-appropriate payment methods are offered; sensitive details are masked.
**Block reason:** No payout/banking-details edit UI found on the partner build — `/commissions` is a read-only ledger; a payout-details/settings screen (per region) was not located. Needs the payout-details UI + region fixtures. Unblock when the payout-details screen is available.
#### PARTNER_UI_COMMISSIONS_010 — BLOCKED (no commission data + no clawback-processing UI)
**Intent:** Process a commission clawback when a client churns within the clawback window → the commission is adjusted to Clawback, the partner is notified, and the product-failure waiver path is available.
**Block reason:** Verified live 2026-07-31 on the SA commission ledger (stgsa `/partners/commissions`): the ledger is **empty** ("No Data Found", 0 commissions) so there is no commission to clawback, and there is **no process-clawback action** in the UI (only a "Clawback Exposure" summary card + a Clawback status filter tab — no per-row "process clawback" control; design PN013 not deployed). Needs the full chain — rate configured → deal approved (blocked by BUG-025) → deal Won → commission — plus the process-clawback UI. Unblock when a churned-client commission exists + the process-clawback UI ships.
#### PARTNER_UI_COMMISSIONS_011 — BLOCKED (needs reseller partner + Won reseller deal)
**Intent:** For a Won **reseller** deal, the commission shows the configured **reseller rate** (not the referral/co-sell rate), clearly labelled as reseller commission.
**Block reason:** Needs a **Reseller-type partner** with a **Won reseller deal** and a reseller rate configured. The test partner is type Channel, the register wizard fixes deal type to Referral, and there is no configured rate / Won deal — so no reseller commission entry exists to verify. Unblock with a reseller partner + Won reseller deal + rate.
#### PARTNER_UI_COMMISSIONS_012 — BLOCKED (needs reseller partner + Won reseller deal)
**Intent:** On reseller-deal close, an invoice is generated **for the partner entity** (not the end-client); amount = reseller rate × deal value; no end-client billing details are exposed.
**Block reason:** Same dependency as _010 — needs a reseller partner + Won reseller deal that has passed commission processing, plus the invoice/billing UI (not seen on the partner build). Unblock with the reseller data + invoice UI.
### UI · DASHBOARD

#### PARTNER_UI_DASHBOARD_001
**Test Description:** The partner shell loads for a channel-partner user and lands on the Dashboard. Confirms the shell chrome (brand + nav + profile), partner-only navigation (no SA/tenant-only routes leaked), and Dashboard content loading with no error/authorization banner.
**Setup (precondition):** Log in as the channel-partner user; navigate to the portal root `/` (Dashboard is the default page) and wait for the "Tier & Performance" READY_MARKER.
**Test Steps:**
1. Partner shell chrome renders.
   → Expected: the "PARTNER PORTAL" brand, ≥5 sidebar nav links, and the "Open profile menu" control are visible.
2. Only partner navigation is exposed.
   → Expected: partner routes `/dashboard`, `/deals`, `/commissions` present; NO SA/tenant-only routes (`/tenants`, `/billing`, `/plans`, `/partners`, `/connectors`, `/auditLog`).
3. Dashboard content loads with no error/authorization banner.
   → Expected: no "Something went wrong" / "not authorized" / "Unauthorized" / "403" / "Access denied"; the "Tier & Performance" panel is visible in `<main>`.
**Expected (overall):** The partner shell loads for the channel partner with the Dashboard active, partner-scoped nav only, and no error/auth banner.
**Note:** PASSED — verified 2026-07-28 (TC 12060401). Access-control style shell test: proves the partner portal exposes only partner routes and the Dashboard is the default landing page. Negative counterpart: N/A — access-control assertion is embedded (asserts SA-only routes are absent). Idempotency: N/A — read-only view.
#### PARTNER_UI_DASHBOARD_002
**Test Description:** Open the partner Dashboard and confirm the KPI metric cards + main section panels render. Read-only: works with empty data (values may be 0 / USD 0) — verifies the cards render, not specific figures.
**Setup (precondition):** Log in as the channel-partner user; open `/dashboard` via the shell and wait for the "Tier & Performance" READY_MARKER.
**Test Steps:**
1. KPI cards render, each with a metric value.
   → Expected: **Total pipeline ACV**, **Commission YTD**, **Active Tenants** each show a value (e.g. "USD 0" / 0).
2. The main dashboard sections render.
   → Expected: **Tier & Performance**, **Territory Assignments**, **Action Required**, **Pipeline Snapshot** panels are visible.
**Expected (overall):** The dashboard renders its KPI metric cards + all main sections (independent of the data).
**Note:** PASSED — verified 2026-07-28 (TC 12060402). First DASHBOARD content test — establishes the `DashboardPage` page-object (KPI cards, sections). Empty partner data shows "No Data Found" in Action Required / Pipeline Snapshot. Negative counterpart: N/A — read-only view. Idempotency: N/A.
#### PARTNER_UI_DASHBOARD_003
**Test Description:** The dashboard Tier Progress component shows progress to the next tier. Read-only.
**Setup (precondition):** Log in as the channel-partner user; open `/dashboard` and wait for the "Tier & Performance" READY_MARKER.
**Test Steps:**
1. Tier Progress shows the current tier + "working towards" the next tier + current ARR.
   → Expected: "Tier Progress" present; the **current tier** (SELECT/ADVANCED/PREMIER), the **"Working towards \<next tier\>"** copy, and **T12M ARR** are shown.
2. Progress metrics are shown.
   → Expected: the **deal count** and **Win rate** are shown in the tier progress panel.
**Expected (overall):** Progress toward the next tier is visible (current tier + next-tier copy + ARR + metrics).
**Note:** PASSED — verified 2026-07-28 (TC 12060403; current=SELECT, working towards ADVANCED, ARR USD 0). **Plan-vs-live:** the plan also lists a **threshold target**, a **progress bar**, and a **remaining delta** — this build does NOT render those (no `role=progressbar` element, no threshold/remaining text); it shows current tier + next-tier copy + ARR + deals/win-rate. The test asserts what the UI actually renders. Negative counterpart: N/A — read-only view. Idempotency: N/A.
#### PARTNER_UI_DASHBOARD_004 — BLOCKED
**Intent:** Render — the Action Required list HAS pending tasks, so the partner sees next actions (each item shows client/deal name, urgency/status, and an action control).
**Block reason:** No fixture / seeding path to make the Action Required list non-empty. The test partner (channel-partner) has empty data — the section renders its graceful empty state ("Action Required · No Data Found · Looks like there's nothing here yet"). Action-Required items are DERIVED (renewals due, deals needing partner action); there is no partner-side API to seed them, and the existing QA-AUTO deals (pending SA approval) do not surface here. The "has pending tasks" positive path cannot be verified until a partner account with real action items (or a seed hook) is available. Revisit with a data-seeded partner.
#### PARTNER_UI_DASHBOARD_005 — FAILED (by design · BE gap)
**Test Description:** Tier-qualification math on the dashboard — per PRD §2.1/§4.3 the Tier Progress component must surface the next-tier **T12M ARR threshold target**, the **remaining delta** to reach it, and a **progress bar**, in addition to the current tier + ARR.
**Setup (precondition):** Log in as the channel-partner user; open `/dashboard` and wait for the "Tier & Performance" READY_MARKER; locate the Tier Progress component.
**Test Steps:**
1. Current tier + current T12M ARR are shown (baseline).
   → Expected: current tier (SELECT/ADVANCED/PREMIER) + "T12M ARR" are shown. **(PASSES — build renders these.)**
2. Next-tier T12M ARR threshold target + remaining delta are shown.
   → Expected: a threshold/target/remaining figure toward the next tier is shown. **(FAILS — not rendered.)**
3. A progress bar toward the next-tier threshold is shown.
   → Expected: a `role=progressbar` / `<progress>` element is present. **(Would FAIL — none rendered.)**
**Expected (overall):** The tier-qualification threshold + remaining delta + progress bar are visible.
**Note:** FAILED by design (`be_gap`) — verified 2026-07-28 (TC 12060405). The live build renders only the current tier, "Working towards \<next tier\>" copy, current ARR (USD 0), and deal/win-rate counts ("0/0 deals") — it does NOT render any ARR threshold amount, any remaining-delta amount, or a progress bar (no `role=progressbar`). Assertion fails with "confirm with BE". Complements DASHBOARD_003 (which asserts only what the UI *does* render); this TC pins the missing tier-qualification math as a tracked gap. Excluded from the merge gate (`be_gap`). Negative counterpart: N/A — read-only calc view. Idempotency: N/A.
#### PARTNER_UI_DASHBOARD_006 — BLOCKED (needs downgrade-state fixture)
**Intent:** Warn of a pending **tier downgrade** — the dashboard shows a 30-day notice + the grace-quarter info (PRD §2.1/§5.5).
**Block reason:** The test partner is not in a **tier-downgrade-pending** state, and there is no way to seed one (tier downgrade is derived from T12M ARR falling below the current tier's threshold over a grace quarter). With no partner in that state, the 30-day-notice / grace-quarter warning cannot be triggered or verified. Also depends on the tier-qualification math that _005 showed is not fully rendered. Unblock with a partner fixture in the downgrade-pending state (+ the warning UI).
#### PARTNER_UI_DASHBOARD_007 — PASSED
**Test Description:** (Negative guard) The dashboard hides vanity metrics — per PRD §4.3 the first dashboard view shows ONLY actionable/decision-supporting values (pipeline ACV, commission, active tenants, tier progress, action items, pipeline snapshot) and must NOT surface non-actionable "vanity" metrics (page/profile views, impressions, followers, bounce rate, login counts, …).
**Setup (precondition):** Log in as the channel-partner user; open `/dashboard` and wait for the "Tier & Performance" READY_MARKER.
**Test Steps:**
1. Only actionable/decision-supporting KPI metrics are shown.
   → Expected: Total pipeline ACV, Commission YTD, Active Tenants visible.
2. No non-actionable vanity metrics are present.
   → Expected: none of {page views, profile views, impressions, followers, bounce rate, time on page, click-through, logins, vanity} appear in `<main>`.
3. The page hierarchy still highlights the actionable sections.
   → Expected: Action Required, Tier Progress, Pipeline Snapshot are visible.
**Expected (overall):** The dashboard surfaces only actionable metrics + the action/tier/pipeline hierarchy; vanity metrics are hidden.
**Note:** PASSED — TC 12060407, verified 2026-07-30 (ran green once staging recovered; the earlier "pending verify" was a transient staging MFE outage on 2026-07-28, not a test defect). Negative TC by design (guards absence of vanity metrics). Negative counterpart: this IS the negative guard. Idempotency: N/A — read-only view.
#### PARTNER_UI_DASHBOARD_008 — BLOCKED (Blazey AI feature)
**Intent:** Ask the Blazey AI assistant (dashboard widget) a **deal-status** question → the answer includes the current deal stage, next action, and the BlazeUp rep contact, scoped to the logged-in partner's deals only.
**Block reason:** Depends on the **Blazey AI assistant** (deferred AI feature) — the widget is not available/testable on the current build — plus real deal data for the partner. Unblock when Blazey ships + the partner has deals.
#### PARTNER_UI_DASHBOARD_009 — BLOCKED (Blazey AI feature)
**Intent:** Ask Blazey a **tier-projection** question ("how much more ARR to reach Premier?") → the answer includes current tier, T12M ARR, ARR gap to next tier, and an estimated timeline; figures match the tier progress bar.
**Block reason:** Same as _008 — depends on the Blazey AI assistant (deferred) + tier data. Note the tier-qualification figures it would quote (threshold/gap) are also the ones _005 showed the UI doesn't fully render yet. Unblock when Blazey ships.
### UI · MY_CLIENTS

**Whole module BLOCKED — not deployed on the partner portal** (re-verified live 2026-07-30, thorough probe: clean login + long wait). The partner nav has 6 items — Dashboard, Deals, Commissions, Directory, Resources, My Apps — with **no "My Clients"** item; `/clients` and `/my-clients` do **not render** a `<main>`; `/apps` is the "My Apps" app-submission page (Draft/Certified/Published…), not client management. The post-close client-management experience (client list / health / renewal / MSP provisioning / expansion) these TCs describe is not built/exposed on this build. Additionally: several need real **client data** (a closed deal → client) which the test partner does not have, and _010/_012/_013 depend on the **Blazey AI** assistant (deferred). Unblock when the My Clients module is deployed (nav + pages) + at least one closed-deal client exists.
- PARTNER_UI_MY_CLIENTS_001 — BLOCKED (Action Required renewal CTA opens renewal flow: module not deployed)
- PARTNER_UI_MY_CLIENTS_002 — BLOCKED (open My Clients → post-close clients list: module not deployed)
- PARTNER_UI_MY_CLIENTS_003 — BLOCKED (client health detail: ARR/renewal/usage/tickets/CSM — module not deployed + needs client data)
- PARTNER_UI_MY_CLIENTS_004 — BLOCKED (register renewal deal from client detail, prefilled: module not deployed)
- PARTNER_UI_MY_CLIENTS_005 — BLOCKED (add MSP managed client → provisioning form: module not deployed)
- PARTNER_UI_MY_CLIENTS_006 — BLOCKED (Security: MSP ticket consent default OFF: module not deployed)
- PARTNER_UI_MY_CLIENTS_007 — BLOCKED (filter "Renewal This Quarter": module not deployed + needs client data)
- PARTNER_UI_MY_CLIENTS_008 — BLOCKED (filter "Health At Risk": module not deployed + needs client data)
- PARTNER_UI_MY_CLIENTS_009 — BLOCKED (search client by name: module not deployed + needs client data)
- PARTNER_UI_MY_CLIENTS_010 — BLOCKED (Blazey client insight / adoption recommendation: module not deployed + Blazey AI deferred)
- PARTNER_UI_MY_CLIENTS_011 — BLOCKED (register expansion deal from My Clients, client prefilled: module not deployed)
- PARTNER_UI_MY_CLIENTS_012 — BLOCKED (Blazey client insight: module not deployed + Blazey AI deferred)
- PARTNER_UI_MY_CLIENTS_013 — BLOCKED (Blazey client insight: module not deployed + Blazey AI deferred)
### UI · MY_PIPELINE

#### PARTNER_UI_MY_PIPELINE_001
**Test Description:** Register-a-Deal wizard, step 1: entering valid company details advances the wizard to the next step and preserves the entered data. Modal-only (open → fill → advance → back); does not submit, so no deal is created.
**Setup (precondition):** Log in as the channel-partner user; open `/deals`; click "Register a deal" to open the wizard (opens on "Step 1 of 3 — Register company").
**Test Steps:**
1. Enter company details (name, domain, country) + primary contact (name, email), then verify each field holds the entered value.
   → Expected: every field **echoes** the entered value (company name, domain, contact name, email — no silent mutation/clear), a country is selected, and — with all required fields filled — "Next" becomes **enabled**. ("Valid" here = required-complete + values echoed; this build does not format-check the fields — that gap is _003.)
2. Click Next.
   → Expected: wizard advances to **Step 2 of 3 (Deal info)** and the Deal-info content renders (a step-2-only field, e.g. "Expected close date", is visible — proving it landed on Deal info, not just a counter change). Deep Deal-info field testing is _008–_012.
3. Go Back to step 1.
   → Expected: returns to Step 1 of 3 and the **company name is preserved**.
**Expected (overall):** Valid step-1 details advance the wizard and the data persists across steps.
**Note:** PASSED — verified 2026-07-24 (TC 12060201). **Plan-vs-live:** the plan says "advances to the contact step", but the live wizard puts the primary contact IN step 1 ("Register company"); a valid step 1 advances to step 2 ("Deal info"). Validation is enforced by **disabling "Next"** until required fields are filled (no inline error text on this build). Not affected by the deals-list defect (_024/_025) — the wizard is a standalone modal. Negative counterpart: **_002**. Idempotency: N/A — modal navigation, does not submit/create.

#### PARTNER_UI_MY_PIPELINE_002
**Test Description:** Negative counterpart of _001: leaving the required **company name** blank blocks the wizard from advancing; providing it unblocks — proving company name is required.
**Setup (precondition):** Open `/deals`; launch the Register-a-Deal wizard (Step 1 of 3).
**Test Steps:**
1. Fill every OTHER required field (domain, country, contact name, email) and leave ONLY company name blank.
   → Expected: the company field is confirmed blank while the others hold their values; "Next" stays **disabled** and the wizard stays on Step 1 of 3 — so the block is attributable **only** to the missing company name.
2. Fill the company name.
   → Expected: "Next" becomes **enabled** (company name was the blocking required field).
**Expected (overall):** A blank required field (company name) prevents advancing; filling it allows advancing.
**Note:** PASSED — verified 2026-07-24 (TC 12060202). **Plan-vs-live:** the plan says "required field error is shown", but this build shows NO inline error text — it enforces required fields by **disabling "Next"**, so the test asserts the disabled→enabled transition instead of an error message. Idempotency: N/A (negative validation, no submit).
#### PARTNER_UI_MY_PIPELINE_003
**Test Description:** Negative (fail-by-design): an invalid/malformed domain in the register wizard must be rejected with a domain-format error (block advancing or flag the field). All cases run (collected).
**Setup (precondition):** Open the Register-a-Deal wizard (step 1) with valid company name, country, and primary contact; vary only the Domain field.
**Test Steps:** (each = enter a malformed domain, blur, check it is rejected)
1. `@@@` → Expected: rejected (Next disabled or field flagged). **Currently FAILS** — accepted (Next stays enabled, field not flagged).
2. `ab cd` (space) → Expected: rejected. **Currently FAILS** — accepted.
3. `notadomain` (no TLD) → Expected: rejected. **Currently FAILS** — accepted.
4. `http://x.com` (scheme, not a bare domain) → Expected: rejected. **Currently FAILS** — accepted.
**Expected (overall):** A malformed domain is rejected with a clear format error; no deal is created.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate) — verified 2026-07-24 (TC 12060203). The register wizard performs **no domain-format validation**: every malformed domain (even `@@@` / `ab cd`) is accepted — the Domain field **keeps the garbage value**, "Next" stays enabled, and the field is never flagged (`aria-invalid` unset), so the deal can proceed with a garbage domain (which "derives the tenant subdomain"). **Confirm with FE** — add domain-format validation on the Domain field. Positive sibling: _001. Idempotency: N/A (no submit).
#### PARTNER_UI_MY_PIPELINE_004
**Test Description:** In the register wizard, entering a domain (subdomain label) already reserved by another active deal shows an inline active-account/conflict warning; a free domain shows none. UI-only (no submit).
**Setup (precondition):** Prove via the partner `check-domain` API which candidate label is reserved (`available=false`) vs free (`available=true`) — so the UI assertion is not circular. Open the wizard with valid company/country/contact. NOTE: the "Domain" field is a **subdomain label** (lowercase/numbers/hyphens, no dots) — placeholder "acme.com" is misleading; a value with dots returns 400 from check-domain.
**Test Steps:**
1. Enter the RESERVED domain (proven `available=false`, e.g. "test").
   → Expected: inline warning shows, e.g. **"This domain is reserved by another active deal. Register will get a conflict queue."** (Next stays enabled — the deal would enter the conflict queue on submit, not blocked.)
2. Enter an AVAILABLE domain (proven `available=true`) — control.
   → Expected: no reserved/active-deal warning.
**Expected (overall):** A reserved domain surfaces the inline active-account/conflict warning; a free domain does not.
**Note:** PASSED — verified 2026-07-27 (TC 12060204). On blur the field calls `GET /v1/partner/portal/check-domain?domain=<label>`; `available=false` (reason e.g. `deal_won`) drives the inline warning. Reserved/free state is proven via that API first (non-circular). If no reserved label exists among the candidates, the test SKIPS with a clear reason (never false-passes). The submit → conflict-queue outcome is _005. Negative/control: the available-domain branch (no warning) is included. Idempotency: N/A (read-only check).
#### PARTNER_UI_MY_PIPELINE_005
**Test Description:** Submit the full register wizard on an already-reserved domain (the conflict path). Fills every step (company + contact + reserved domain; deal info: plan / seats / region / expected close date) and submits; a deal is created (would enter the conflict queue).
**Setup (precondition):** Prove via `check-domain` API a reserved label (available=false). Open the wizard.
**Test Steps:**
1. Step 1 with the RESERVED domain → the inline conflict warning shows ("reserved by another active deal … conflict queue"); advance.
   → Expected: warning shown; wizard advances to Deal info.
2. Fill Deal info — plan (billing cycle auto-sets), granted seats, region, expected close date (next month) → advance to Summary.
   → Expected: with Deal info complete, "Next" is enabled; wizard reaches Step 3 of 3 (Summary).
3. Submit.
   → Expected: submission succeeds — `POST /v1/partner/portal/deals` returns **201** and a deal id.
**Expected (overall):** The wizard submits end-to-end on a reserved domain and the deal is created.
**Note:** PASSED — verified 2026-07-27 (TC 12060205). Full e2e submit works: reserved-domain warning → Deal info → **submit → 201** (deal id logged in the run for manual lookup). **PENDING (verify step — intentionally not asserted yet):** confirming the deal actually LANDS in the conflict queue is deferred — the partner deals-list endpoint is 400 (`_024`) so the deal isn't listable, and there is no delete API to clean up the created deal. **To improve once BE provides a way to fetch/remove the created deal** (user following up with BE). Side-effect: each run creates one non-deletable deal. Negative/conflict-detection is covered by _004 (UI warning) + API `2060204`. Idempotency: N/A here (duplicate-register is _022).
#### PARTNER_UI_MY_PIPELINE_006
**Test Description:** Negative (required): leaving the primary-contact **email** blank blocks the wizard from advancing; providing a valid email unblocks — proving the email is required.
**Setup (precondition):** Open the wizard (Step 1); fill every other required field (company name, domain, country, contact name).
**Test Steps:**
1. Leave contact email blank (others filled).
   → Expected: email field confirmed blank while others hold values; "Next" stays **disabled** — block attributable only to the missing email.
2. Fill a valid email.
   → Expected: "Next" becomes **enabled**.
**Expected (overall):** A blank required email prevents advancing; a valid email allows it.
**Note:** PASSED — verified 2026-07-27 (TC 12060206). Same mechanism as _002: required fields enforced by disabling "Next" (no inline error text). Idempotency: N/A (validation, no submit).

#### PARTNER_UI_MY_PIPELINE_007
**Test Description:** Negative (fail-by-design): a malformed contact **email** must be rejected with a format error (block advancing or flag the field). All cases run (collected).
**Setup (precondition):** Open the wizard (Step 1) with valid company/domain/country/contact-name; vary only the email.
**Test Steps:** (each = enter a malformed email, blur, check it is rejected)
1. `notanemail` (no @) → Expected: rejected. **Currently FAILS** — accepted (field keeps value, Next enabled, not flagged).
2. `abc@` (no domain) → Expected: rejected. **Currently FAILS** — accepted.
3. `abc@x` (no TLD) → Expected: rejected. **Currently FAILS** — accepted.
4. `a b@x.com` (space) → Expected: rejected. **Currently FAILS** — accepted.
**Expected (overall):** A malformed email is rejected with a clear format error; no deal is created.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate) — verified 2026-07-27 (TC 12060207). The register wizard performs **no email-format validation**: every malformed email (even `notanemail` / `a b@x.com` with a space) is accepted — the field keeps the value, "Next" stays enabled, and the field is never flagged (`aria-invalid` unset). Same class of gap as _003 (domain). **Confirm with FE** — add email-format validation on the contact email field. Positive sibling: _001. Idempotency: N/A (no submit).
#### PARTNER_UI_MY_PIPELINE_008
**Test Description:** Choosing the referral deal type: on this wizard the deal type is Referral (default), and it persists to the Summary. UI-only (no submit).
**Setup (precondition):** Open the wizard; complete step 1 (company/domain/country/contact).
**Test Steps:**
1. On Deal info, the deal type shows **Referral** (Reseller/Co-sell are not offered — see _009/_010).
   → Expected: "Referral" visible; no "Reseller" option present.
2. Complete Deal info (plan/seats/region/date) → continue to Summary.
   → Expected: reaches Step 3 of 3 (Summary).
3. Summary persists the deal type.
   → Expected: Summary shows **Deal type = Referral**.
**Expected (overall):** Referral deal type is captured and persists across navigation to the Summary.
**Note:** PASSED — verified 2026-07-27 (TC 12060208). On this build the deal type is a **fixed read-only "Referral" badge** (reseller/co-sell are NOT selectable — clicking it opens nothing, there's no deal-type dropdown, and no "Reseller"/"Co-sell" text). Referral implies the direct billing model (business rule); the UI shows only the type label "Referral" (no explicit "direct billing" text). No submit → no side-effect. Idempotency: N/A.

#### PARTNER_UI_MY_PIPELINE_009
**Note (BLOCKED):** Choose reseller deal type → reseller billing path. Blocked (verified live 2026-07-27): the register wizard does **not offer a reseller deal type** — the deal type is a fixed read-only "Referral" badge (no deal-type dropdown; clicking it opens nothing; "Reseller" text is absent). There is no UI control to select reseller, so the reseller billing path cannot be exercised from the wizard. (The API supports dealType `reseller` — see `make_deal` / API deal TCs — so this is a UI gap.) Unblock when the wizard exposes a deal-type selector with reseller.

#### PARTNER_UI_MY_PIPELINE_010
**Note (BLOCKED):** Choose co-sell deal type → co-sell option captured. Blocked (verified live 2026-07-27): same as _009 — the wizard's deal type is a fixed read-only "Referral" badge with no selector; "Co-sell" is not offered in the UI. No control to choose co-sell. (API supports `co_sell`.) Unblock when the wizard exposes a deal-type selector with co-sell.
#### PARTNER_UI_MY_PIPELINE_011
**Test Description:** The review Summary (step 3) displays all entered data. Fills the wizard with known unique values (company / domain / contact name / email) + deal info, reaches the Summary, and confirms every entered value is shown for review. Verified at the Summary (pre-submit); no submit → no deal created.
**Setup (precondition):** Open the wizard; fill step 1 (company/domain/country/contact) + Deal info (plan/seats/region/expected close date) with known data.
**Test Steps:**
1. Summary shows the entered COMPANY + CONTACT values.
   → Expected: the unique company name, domain, contact name, and email are all visible on the Summary.
2. Summary shows the DEAL section fields.
   → Expected: Deal type = **Referral**, plus Expected close date, Plan source, and Country rows are shown.
**Expected (overall):** The Summary reflects every entered value for review before submission.
**Note:** PASSED — verified 2026-07-27 (TC 12060211). Uses 4 unique text inputs (company/domain/contact/email) asserted verbatim on the Summary → strong proof the entered data is displayed. Verified pre-submit (no submit → no side-effect). Idempotency: N/A.
#### PARTNER_UI_MY_PIPELINE_012
**Test Description:** Performance — a valid deal registration returns a success response within 2 seconds. Submits the full wizard with a valid (available) domain and measures the register API's own network round-trip.
**Setup (precondition):** Open the wizard; fill step 1 (company/domain/country/contact) + Deal info (plan/seats/region/expected close date) with a unique available domain.
**Test Steps:**
1. Submit the deal.
   → Expected: `POST /v1/partner/portal/deals` returns **2xx** (201) with a deal id.
2. Measure the response time.
   → Expected: the request→response round-trip is **< 2000 ms** (measured from the request's network timing: responseEnd − requestStart; excludes UI render).
**Expected (overall):** A valid registration succeeds and the API responds within the 2s budget.
**Note:** PASSED — verified 2026-07-27 (TC 12060212; observed ~642 ms). Measures the register API round-trip (server + network), not full UI render. Side-effect: submitting creates a real deal (no delete API — see _005; deal id logged in the run). A staging blip can push it over 2s → re-run before filing a perf bug. Idempotency: N/A here (duplicate-register is _022).
#### PARTNER_UI_MY_PIPELINE_013
**Test Description:** Performance/mobile — the deal registration flow finishes under 90 seconds on a mobile viewport (375×812). Completes the full wizard and submits at mobile width, timing the whole flow (open wizard → submitted).
**Setup (precondition):** Resize the page to 375×812; open the wizard.
**Test Steps:**
1. At mobile width, fill step 1 (company/domain/country/contact) and advance.
2. Fill Deal info (plan/seats/region/expected close date) and advance to Summary.
3. Submit → the register succeeds and the whole flow completes within budget.
   → Expected: `POST /v1/partner/portal/deals` 2xx (201); elapsed from opening the wizard to the success response is **< 90 s**.
**Expected (overall):** The registration is completable on mobile within 90 seconds.
**Note:** PASSED — verified 2026-07-27 (TC 12060213; observed ~6 s, well under 90 s). All wizard controls (dropdowns, date picker, submit) work at 375×812. Side-effect: submitting creates a real deal (no delete API — see _005; deal id logged). Partner UI login can flake (login page slow to render) → the run may BLOCK on a login timeout; re-run. Idempotency: N/A.
#### PARTNER_UI_MY_PIPELINE_014
**Test Description:** Open My Pipeline (the Deals page) and confirm all deal stages and their counts are visible — the pipeline shows the 6 stage tabs (All / Pending / Approved / Won / Lost / Expired), each with a numeric deal count, plus the pipeline summary and the Register CTA. Read-only: works with an empty pipeline (counts may be 0) — it verifies the stages RENDER, not any specific data.
**Setup (precondition):** Log in once as the configured channel-partner user; open `/deals` via the shell and wait for the "Deal Pipeline" READY_MARKER.
**Test Steps:**
1. All 6 pipeline stage tabs are visible.
   → Expected: All, Pending, Approved, Won, Lost, Expired tabs all render (role=tab).
2. Every stage tab shows a numeric deal count.
   → Expected: each tab shows an integer count ≥ 0 (e.g. "All 0").
3. Pipeline summary + Register CTA are visible.
   → Expected: "… deals in your pipeline" summary and the "Register a deal" button are visible.
**Expected (overall):** The pipeline renders all 6 stages with counts + summary + Register CTA (independent of how many deals exist).
**Note:** PASSED — verified 2026-07-24 (TC 12060214). All 6 stages render with counts (0 on the empty test pipeline); summary + Register CTA visible. First MY_PIPELINE content test — establishes the `DealsPage` page-object (stage tabs, counts, controls) reused by the filter/card TCs (_024/_025/_026/_027/_033). Negative counterpart: N/A — a read-only view has no invalid-input surface. Idempotency: N/A — read-only (creates nothing).
- PARTNER_UI_MY_PIPELINE_015 — BLOCKED (deal detail timeline / approval history: deals-list 400 "Invalid id: 'pro-v1'" → pipeline empty, no deal to open; same BE defect as _024)
- PARTNER_UI_MY_PIPELINE_016 — BLOCKED (accept co-sell override proposal: co-sell deal type not offered in the wizard + needs a proposal; feature absent)
- PARTNER_UI_MY_PIPELINE_017 — BLOCKED (Negative: co-sell override ≤ $100K unavailable: co-sell not offered in the UI)
- PARTNER_UI_MY_PIPELINE_018 — BLOCKED (co-sell override > $100K requires written agreement: co-sell not offered in the UI)
- PARTNER_UI_MY_PIPELINE_019 — BLOCKED (enrich on blur valid domain: no enrichment feature — verified live 2026-07-30, Headcount is a manual "Select range" dropdown + Logo is a manual URL field; blur only derives the tenant subdomain)
- PARTNER_UI_MY_PIPELINE_020 — BLOCKED (choose modules of interest: no modules-of-interest selection in the wizard — verified live 2026-07-30, step 2 has deal type/plan/seats/region/close date only)
- PARTNER_UI_MY_PIPELINE_021 — BLOCKED (register conflict-lost prospect after 90 days: needs a conflict-lost deal aged 90 days — time-based data not available)
- PARTNER_UI_MY_PIPELINE_022 — BLOCKED (Negative: no registration by either partner → commission not awarded: behavioural/backend outcome, no partner-UI action to exercise)
- PARTNER_UI_MY_PIPELINE_023 — BLOCKED (reseller deal → end-client price field absent: reseller deal type not offered in the wizard; feature absent)
#### PARTNER_UI_MY_PIPELINE_024
**Note (BLOCKED):** Click a pipeline deal card so the deal detail opens. Blocked by a BE defect (verified live 2026-07-24): the partner-portal deals-list endpoint `GET /v1/partner/portal/deals` returns **400 "Invalid id: 'pro-v1'"**, so the pipeline **never renders any deal row/card** (the UI falls back to the "No deals found" empty state even when the partner HAS deals). Root cause = the plan-reference contract drift: older deals store a plan **slug** (`planId:"pro-v1"`) while the BE now resolves plans by Mongo **_id** (ObjectId), so listing a partner whose deals include any slug-referenced plan throws "Invalid id" and the whole list fails. Confirmed a freshly SA-registered deal for the partner still does not appear (list stays 400 for ~40 s). With no deal card to click, the "open deal detail" flow cannot be exercised. **Same blocker applies to the other deal-list/detail pipeline TCs** (_015 detail, _025/_026/_027 filter, _033 card tag). Unblock when BE fixes the deals-list endpoint (tolerate/migrate legacy slug plan refs, or resolve by _id) so the pipeline renders deal cards. **Related:** register now requires the plan **_id** (slug → 400) — `pick_billing_plan_id` updated accordingly.
#### PARTNER_UI_MY_PIPELINE_025
**Note (BLOCKED):** Filter deals by company text so matching deals are displayed. Blocked by the same BE defect as _024 (verified live 2026-07-24): the deals-list endpoint `GET /v1/partner/portal/deals` returns **400 "Invalid id: 'pro-v1'"** — and the search variant `?search=QA` returns the **same 400** (filtering runs through the same endpoint). With the list broken, no deal ever renders, so a "matching deals displayed" assertion cannot be exercised. Unblock together with _024 (BE must fix the deals-list endpoint to tolerate/resolve legacy slug plan refs).
- PARTNER_UI_MY_PIPELINE_026 — BLOCKED (filter by deal type: deals-list 400 → pipeline empty; a Filter button exists but filtering can't be verified with 0 deals; same BE defect as _024/_025)
- PARTNER_UI_MY_PIPELINE_027 — BLOCKED (filter by module: same deals-list 400 + no "module" concept in the deal model/wizard)
- PARTNER_UI_MY_PIPELINE_028 — BLOCKED (add shared note to a deal: no deal detail — deals-list 400, pipeline empty, no deal to open)
- PARTNER_UI_MY_PIPELINE_029 — BLOCKED (upload document to a deal: no deal detail — same as _028)
- PARTNER_UI_MY_PIPELINE_030 — BLOCKED (view assigned BlazeUp rep: a rep is assigned on SA approval (blocked by BUG-025) + deals-list 400, no deal to open)
- PARTNER_UI_MY_PIPELINE_031 — BLOCKED (request manual protection extension: needs an approved deal with a running protection clock + deal detail — deals-list 400 / no SA approval)
- PARTNER_UI_MY_PIPELINE_032 — BLOCKED (reseller marks deal Won / self-confirm: reseller deal type not offered in the UI)
- PARTNER_UI_MY_PIPELINE_033 — BLOCKED (pipeline card shows reseller billing tag: deals-list 400 → no card renders + reseller not offered)
### UI · PARTNER_PORTAL_SHELL

#### PARTNER_UI_PARTNER_PORTAL_SHELL_001
**Test Description:** Open every primary nav route of the partner portal shell and confirm each page's content module renders (correct page content shown, no micro-frontend error). One looping test walks all pages via direct URL and soft-collects failures → a single verdict naming any bad page.
**Setup (precondition):** Log in once as the configured channel-partner user (session-cached partner UI login). Warm up the SPA (open Dashboard once) so the first page in the loop isn't charged the one-off bootstrap.
**Test Steps:** (each page = one `page.goto(route)`; wait for its READY_MARKER in `<main>` — fast-fail on the "Something went wrong" MFE panel — **then** assert the content loaded: no "Failed to load"/"Please refresh and try again" banner in `<main>`) — primary nav verified live 2026-07-23:
1. Dashboard → `/dashboard` → Expected: title **"Tier & Performance"** visible + no error banner. → **PASS**
2. Deals → `/deals` → Expected: **"Deal Pipeline"** visible + no error banner. → **PASS**
3. Commissions → `/commissions` → Expected: **"Commissions"** visible + no error banner. → **PASS**
4. Resources → `/resources` → Expected: **"Resources"** visible + no error banner. → **PASS**
5. My Apps → `/apps` → Expected: **"My Apps"** visible + no error banner. → **FAILS** — the shell renders (title "My Apps" + tabs + Submit button) but the app list data-fetch fails, showing the red banner **"Failed to load your apps. Please refresh and try again."**
**Expected (overall):** All 5 primary pages render their module AND their content (no MFE panel, no content-load error banner); a broken page fast-fails naming which one.
**Note:** FAILED (by design) — verified 2026-07-23 (TC 12060101). 4/5 pages pass; **`/apps` (My Apps) FAILS**: the section shell renders but the app-list data-fetch fails → persistent banner "Failed to load your apps. Please refresh and try again." (a backend/data-load defect for this page — **confirm with BE**). Reproduced live; not a one-off flap. **This TC also hardened the readiness check:** marker-only (page title) gave a FALSE PASS because the heading renders even when data fails — added a content-error-banner assertion after the marker, which correctly turns `/apps` red. **Plan-vs-live mapping:** the plan named "My Pipeline / My Clients / Training", but the live primary nav is Deals / Resources / My Apps ("My Pipeline" = the Deals page, title "Deal Pipeline"). First partner-portal UI test — establishes the live route map reused by later content tests. Negative counterpart: N/A (page-load smoke has no invalid-input surface; broken-page/content-error cases are built in). Idempotency: N/A (read-only navigation).
#### PARTNER_UI_PARTNER_PORTAL_SHELL_002
**Test Description:** Open the partner portal at a common mobile viewport (375×812) and confirm the shell stays usable on every primary nav page — the section renders, the sidebar nav stays reachable, and the layout does NOT overflow horizontally (no content cut off / sideways scroll) — then tap a sidebar link to prove mobile navigation works. One looping test soft-collects per-page failures → single verdict.
**Setup (precondition):** Log in once as the configured channel-partner user; resize the page to 375×812; warm up the SPA (open Dashboard once).
**Test Steps:** (per page at mobile width: shell READY_MARKER visible + ≥1 nav link visible + horizontal overflow ≤ 5px scrollbar allowance) — verified live 2026-07-24:
1. Dashboard `/dashboard` → Expected: renders, nav reachable, no h-overflow. → **PASS** (overflow 0px).
2. Deals `/deals` → Expected: no h-overflow. → **FAILS** — content overflows the 375px viewport by **+162px** (tabs/filter/view controls don't fit → sideways scroll).
3. Commissions `/commissions` → Expected: no h-overflow. → **PASS** (0px).
4. Resources `/resources` → Expected: no h-overflow. → **PASS** (0px).
5. My Apps `/apps` → Expected: no h-overflow. → **FAILS** — overflows by **+263px**.
6. Tap sidebar link at mobile → Commissions routes + renders. → **PASS** (mobile nav is usable).
**Expected (overall):** Every primary page fits the mobile viewport (no horizontal overflow) with the nav reachable; tapping nav routes correctly.
**Note:** FAILED (by design) — verified 2026-07-24 (TC 12060102). 3/5 pages fit + mobile nav works, but **Deals (+162px) and My Apps (+263px) overflow horizontally at 375px** = responsive-layout defects (content doesn't fit small screens → sideways scroll; **confirm with FE**). The mobile sidebar stays an icon-bar (not hidden) and nav taps route correctly, so navigation itself is usable — the defect is page-content width on Deals/My Apps. Reproduced live. Negative counterpart: N/A (a responsive smoke has no invalid-input surface; the "layout doesn't fit" case is exactly what it checks). Idempotency: N/A (read-only navigation/resize).
#### PARTNER_UI_PARTNER_PORTAL_SHELL_003
**Note (BLOCKED):** Dual-account partner switching between **Pack** and **Channel** dashboards. Cannot automate — the feature and the test data do not exist on staging (verified live 2026-07-24): (a) **no account-switcher control** in the portal shell — the header "Select" is the tier badge (tier=`select`), not an account switcher, and the profile menu only offers Profile/Logout; (b) the logged-in partner is a **single account** — `GET /v1/partner/auth/me` returns one `partnerId` with `type:"channel"`, `tier:"select"`, no accounts array; (c) **no "Pack" concept** — the partner `type` enum is channel/referral/msp/system_integrator (no "pack"), so a Pack↔Channel dual-account cannot even be represented. Unblock when BE ships multi-account membership (one user → a Pack + a Channel account) + a shell account switcher, AND a dual-account test partner is provisioned.
### UI · PARTNER_TEAM

**Correction (2026-07-30):** the partner portal nav has **6 items** — Dashboard, Deals, Commissions, **Directory**, Resources, My Apps. An earlier note here wrongly said "5 nav / no team UI" — that was a false negative from a too-short probe wait (see the `probe-mfe-with-long-wait` learning). `/directory` IS the partner team-members page.
#### PARTNER_UI_PARTNER_TEAM_001 — PASSED
**Test Description:** Invite a partner team member. On the partner Directory (`/directory`), open "Invite User", fill the new member's email + name + role, send the invite, and confirm the invitation is created (one-time credential shown) and the member appears in the team table with its role.
**Setup (precondition):** Log in as the channel-partner user (stgpartners, 2FA); open `/directory` and wait for the "Directory" READY_MARKER.
**Test Steps:**
1. The member table + Invite User action render.
   → Expected: MEMBER / ROLE / STATUS / LAST LOGIN columns + "Invite User" button.
2. The Invite dialog exposes email + name + a role selector.
   → Expected: Email*, First name*, Last name*, Role (default "Viewer") fields + Send Invite.
3. Send the invite → "User invited" confirmation.
   → Expected: the credential dialog ("User invited" — one-time temporary password) appears; close via Done.
4. The invited member appears in the Directory with its role.
   → Expected: a row for the invited email shows role "Viewer" and status Active.
**Expected (overall):** The invitation is created with the role and the new member is visible in the Directory.
**Note:** PASSED — verified 2026-07-30 (TC 12060601). Partner-side team management on `/directory` (Invite User → email/name/role → Send → one-time credential → member Active). New config section `PARTNER.ui.PARTNER_TEAM = 6`. Side-effect: each run creates a real Active member (unique `qa.auto+…` email; no UI delete — members accumulate). Negative counterpart: N/A here (could add required-field validation later). Idempotency: N/A (unique email each run).
- PARTNER_UI_PARTNER_TEAM_002 — BLOCKED (create campaign referral link: no referral-link UI found on `/directory`; feature not located on the partner portal — recheck if/when a referral-link area ships)
- PARTNER_UI_PARTNER_TEAM_003 — BLOCKED (copy referral link: same — no referral-link UI found)
### UI · RESOURCES

**All BLOCKED** — the Resources page exists but its content does not match these TCs (verified live 2026-07-29). `/resources` renders a read-only **"Commission Rates + Assigned Territories"** view (rates applicable to your tier; regions you are authorised to sell) — there is **no demo sandbox, no marketing-resource download, no co-branded pitch-deck generator, and no ROI calculator** (no action buttons at all). The demo-sandbox / marketing-assets / pitch-deck / ROI-calculator experiences these TCs describe are not implemented in this build (possibly gated to a higher tier than the test partner's Select/Registered).
- PARTNER_UI_RESOURCES_001 — BLOCKED (demo sandbox reset: no sandbox UI)
- PARTNER_UI_RESOURCES_002 — BLOCKED (sandbox weekly auto-reset toggle: no sandbox UI)
- PARTNER_UI_RESOURCES_003 — BLOCKED (download marketing resource: no marketing-assets UI)
- PARTNER_UI_RESOURCES_004 — BLOCKED (generate co-branded pitch deck: no generator UI)
- PARTNER_UI_RESOURCES_005 — BLOCKED (ROI calculator → prospect PDF: no calculator UI)
### UI · SA_PARTNER_MODULE

#### PARTNER_UI_SA_PARTNER_MODULE_001 — BLOCKED
**Intent:** Resolve a Conflict Queue entry with written reasoning — decision is saved, parties notified, record becomes immutable.
**Block reason:** Blocked by the SA Deal Approval Queue backend defect (see _007 / BUG-025). The Conflict Queue (`/partners/deals` → Conflicts tab) fails to load any deals — every tab shows "Server Error — Invalid id: 'pro-v1'" — so no conflicted deal can be opened to resolve. Revisit once BUG-025 is fixed and a two-parties-same-domain conflict fixture exists.
#### PARTNER_UI_SA_PARTNER_MODULE_002 — BLOCKED
**Intent:** Conflict Queue decision UI shows prospect-confirmation status + first-registered timestamps + mandatory written reasoning + 5-business-day SLA indicator.
**Block reason:** Same as _001 — the Conflict Queue deal list fails to load (BUG-025), so the conflict-decision detail UI cannot be reached. Needs BUG-025 fixed + a conflict fixture with prospect-confirmation data.
#### PARTNER_UI_SA_PARTNER_MODULE_003
**Test Description:** The SA-side Partner Directory loads (stgsa SA Dashboard → Partners). Confirms the directory renders with its breadcrumb + summary stat cards, the Status/Tier filter controls + "Onboard Partner" action, and the partner table with its full column header. Read-only + empty-safe.
**Setup (precondition):** Log in as the super-admin user (stgsa); open `/partners` and wait for the "Partners" READY_MARKER in `<main>`.
**Test Steps:**
1. The directory loads with its breadcrumb + summary cards.
   → Expected: the "Directory" breadcrumb + the 4 summary cards (**Total Partners**, **Active**, **Pending Approval**, **Premier Tier**) are visible.
2. The filter controls + Onboard action are visible.
   → Expected: the **Status** and **Tier** filter controls + the **Onboard Partner** action are visible.
3. The partner table renders (full column header; rows when present).
   → Expected: the table shows all 8 headers (PARTNER, TIER, TYPE, CONTACT, TOTAL ARR, OPEN DEALS, STATUS, JOINED); partner rows render when partners exist, otherwise the "No Data Found" empty state.
**Expected (overall):** The SA Partner Directory loads with its summary, filters, and partner table structure (data-independent).
**Note:** PASSED — verified 2026-07-29 (TC 12060503). First SA_PARTNER_MODULE test — establishes the SA-side surface (stgsa SA Dashboard, super-admin) via the existing `ShellPage` + new `PartnerDirectoryPage`. Runs on the SA domain (`make_page`/`authenticated_page`), NOT the partner portal. New config section `PARTNER.ui.SA_PARTNER_MODULE = 5`. Empty-safe: verified with both 0 rows (empty state) and ≥1 partner row. Negative counterpart: N/A — read-only directory load. Idempotency: N/A. NOTE: stgsa flapped during verification (login-fail + 90 s render-timeout on 2 earlier attempts) — passed cleanly once staging stabilized; env flakiness, not a test defect.
#### PARTNER_UI_SA_PARTNER_MODULE_004 — BLOCKED (FSM UI not deployed)
**Where:** stgsa (SA portal) → Partners → Directory → Pending Approval → open application. **Design:** PN003 (3-stage FSM), ready-for-dev.
**Intent:** Partner-application review FSM — the SA Review / Legal Countersign / Final Approval stages are visible with status indicators; stage-skip is prevented; applicant details shown.
**Block reason:** The FSM review UI is **not deployed on staging** (re-verified 2026-07-30, thorough probe). The pending-application **fixture IS creatable**: stgsa Partners→Directory→"Onboard Partner" creates a partner in **Pending** status (verified — onboarded PAR-795503, Pending Approval 0→1). BUT even a pending partner's detail page shows only Overview / Deals / Commission / Members tabs — **no SA Review / Legal Countersign / Final Approval stages, no Approve/Reject**. So the blocker is the FSM screen deploy, NOT the fixture. Once FE ships the FSM review UI, the test can self-seed via Onboard Partner.
#### PARTNER_UI_SA_PARTNER_MODULE_005 — BLOCKED (FSM UI not deployed)
**Design:** PN003 "lack of document" variant, ready-for-dev.
**Intent:** (Negative) Missing signed agreement blocks advancing to Legal Countersign; Request Agreement notifies applicant; attaching an agreement enables Advance.
**Block reason:** Same as _004 — FSM review UI (SA Review stage / Advance-to-Legal-Countersign / agreement-attach) not deployed on staging. Fixture creatable via Onboard Partner; unblock when the FSM UI ships.
#### PARTNER_UI_SA_PARTNER_MODULE_006 — BLOCKED (FSM UI not deployed)
**Design:** PN003, ready-for-dev.
**Intent:** Legal countersign of the partner agreement makes Final Approval available (+ audit trail / notification).
**Block reason:** Same as _004/_005 — the Legal-Countersign stage of the FSM review UI is not deployed on staging. Unblock when the FSM UI ships.
#### PARTNER_UI_SA_PARTNER_MODULE_007 — FAILED (app bug · BE defect)
**Test Description:** The SA Deal Approval Queue (stgsa `/partners/deals`, PRD §5.2) — the Pending Approval + Conflicts queues are visible and load their deals. Confirms the queue shell (3 tabs All Deals / Pending Approval / Conflicts + Status/Deal Type filters + deals table header), then that the Pending Approval and Conflicts queues actually load deals with no backend error.
**Setup (precondition):** Log in as super-admin (stgsa); open `/partners/deals` and wait for the "Pending Approval" tab (queue shell) to render.
**Test Steps:**
1. The three queue tabs + filters render.
   → Expected: **All Deals**, **Pending Approval**, **Conflicts** tabs + **Status**, **Deal Type** filters are visible. **(PASSES.)**
2. The deals table header renders (all columns).
   → Expected: PROSPECT, PARTNER, TYPE, EST. ACV, PLAN, STATUS, EXPECTED CLOSE, PROTECTION. **(PASSES.)**
3. The Pending Approval + Conflicts queues load without a server error.
   → Expected: no backend error; deals load (partners have open deals). **(FAILS.)**
**Expected (overall):** The SA deal approval queue shows the Pending + Conflict queues with their deals loaded.
**Note:** FAILED — real app/BE defect, verified 2026-07-29 (TC 12060507). The queue SHELL renders (tabs/filters/header all pass), but the deal-list fetch fails on **every** tab with **"Server Error — Invalid id: 'pro-v1'"**, so no deal rows load even though partners have open deals (Directory shows OPEN DEALS ≥ 1). Deterministic (not staging flakiness — sa-partners-api is UP, returns the error). Assertion fails with "confirm with BE". This is the SA-side view where partner-registered deals (incl. the QA-AUTO deals from the partner MY_PIPELINE _005/_012/_013 submits) should appear — blocked by this defect, so it also blocks verifying the partner-side conflict-queue (_005). Row-level checks (partner/ACV/type/conflict-status + Approve/Reject/Request-Info buttons per PRD §5.2) are unverifiable until the deal list loads. Negative counterpart: N/A — read-only queue view. Idempotency: N/A.
- PARTNER_UI_SA_PARTNER_MODULE_008
#### PARTNER_UI_SA_PARTNER_MODULE_009 — BLOCKED (config UI not deployed)
**Where:** stgsa → Partners → Commission → (Commission configuration → Commission rate). **Design:** PN020, ready-for-dev.
**Intent:** Configure a versioned Commission Rate Table — tier × deal-type (Registered/Select/Advanced/Premier × Referral/Reseller/Co-sell) with NN/EN/EE rate fields; editing creates a new version, preserving history; locked rate per deal.
**Block reason:** The Commission **configuration** view is **not deployed on staging** (re-verified 2026-07-30, thorough probe: full-page text + all clickables + routes). `/partners/commissions` renders only the payout ledger (Pending Payout / Paid YTD / Clawback Exposure + payout table) — there is **no "View configuration" entry point**, no rate/version text anywhere, and config routes (`/partners/commissions/configuration`, `/partners/commission-rates`, …) 404 / "Invalid id". Design PN020 is ready-for-dev but the config UI is not live yet. Unblock when FE deploys the Commission configuration view.
#### PARTNER_UI_SA_PARTNER_MODULE_010 — BLOCKED (config UI not deployed)
**Where:** stgsa → Partners → Commission → (Commission configuration → SPIFF Program). **Design:** PN020 (SPIFF section), ready-for-dev.
**Intent:** Create a SPIFF bonus programme (name, bonus %, regions, tiers, valid dates) → appears in Active SPIFF Programmes; reflected in partner commission projection.
**Block reason:** Same as _009 — the SPIFF configuration lives in the same Commission configuration view, which is not deployed on staging. Unblock when FE deploys it.
#### PARTNER_UI_SA_PARTNER_MODULE_011 — FAILED (app bug · BE defect)
**Test Description:** The SA Partner Programme Analytics dashboard (stgsa `/partners/analytics`, PRD §7) — funnel + KPI + tier-distribution + top-partners render and load with no backend error.
**Setup (precondition):** Log in as super-admin (stgsa); open `/partners/analytics` and wait for the "Deal Funnel" section.
**Test Steps:**
1. Summary KPI cards + Deal Funnel stages render.
   → Expected: Total Partners, Total ARR, Avg Deal Size, Win Rate, Pending Payouts, Clawback Exposure + funnel stages Registered/Approved/In Progress/Won. **(PASSES.)**
2. The Tier Distribution + Top Partners sections render.
   → Expected: Deal Funnel, Tier Distribution, Top Partners by ARR sections visible. **(PASSES.)**
3. The analytics data loads without a server error.
   → Expected: no backend error. **(FAILS.)**
**Expected (overall):** The analytics dashboard shows the funnel + KPIs + sections with data loaded.
**Note:** FAILED — real BE defect, verified 2026-07-29 (TC 12060511, **BUG-026**). The dashboard shell renders (KPIs + funnel + tier distribution + top-partners all pass), but a paginated analytics query fails with **"Server Error — Invalid pagination: limit must not exceed 100"** (a backend defect: the frontend requests a page size > 100 that the API rejects). Deterministic. Assertion fails with "confirm with BE". Note the live KPI set differs slightly from the plan (Approval Rate / Avg Deal Velocity / detailed commission line-items not rendered) — the test asserts what the UI renders. Negative counterpart: N/A — read-only dashboard. Idempotency: N/A.
#### PARTNER_UI_SA_PARTNER_MODULE_012 — BLOCKED (Territory page not deployed)
**Where:** stgsa → Partners → Territory (and from Partner detail). **Design:** Territory PN021, ready-for-dev.
**Intent:** Assign a Territory (regions, verticals, exclusivity type, effective dates) to a partner; shows an exclusivity-conflict warning; the exclusive territory auto-routes conflicting deals.
**Block reason:** The Territory page is **not deployed on staging** (re-verified 2026-07-30). `/partners/territory` and `/partners/territories` return "Server Error — Invalid id: 'territory'" (route not registered), and the partner-detail Territory section is read-only "No territories assigned to this partner" with no "+ Assign Territory" control / assignment form / exclusivity-conflict warning. Design PN021 is ready-for-dev but the Territory management UI is not live. Unblock when FE deploys it.
#### PARTNER_UI_SA_PARTNER_MODULE_013 — PASSED
**Test Description:** The SA-side Partner Detail page (stgsa `/partners/<id>`) loads with its detail chrome — the Overview / Deals / Commission / Members tabs, the Tier & Performance + Territory Assignments sections, the partner info (id + type + tier), and the Partner-actions control.
**Setup (precondition):** Log in as super-admin (stgsa); self-seed a throwaway partner via **Onboard Partner** (the Directory list is unreliable on staging), then open its detail.
**Test Steps:**
1. The detail tabs render.
   → Expected: **Overview**, **Deals**, **Commission**, **Members** tabs are visible (Radix `role="tab"`). **(PASSES.)**
2. The Overview sections + partner info render.
   → Expected: **Tier & Performance** + **Territory Assignments** sections + partner company name + **Channel** type + **PAR-…** id are visible. **(PASSES.)**
3. The Partner-actions control renders.
   → Expected: the **Partner actions** kebab control is visible on the header. **(PASSES.)**
**Expected (overall):** The SA Partner Detail loads with tabs, sections, partner info, and the actions control.
**Note:** PASSED, verified 2026-07-31 (TC 12060513). Read-only load check (empty-safe). Negative counterpart: N/A — read-only load. Idempotency: N/A.
#### PARTNER_UI_SA_PARTNER_MODULE_014 — PASSED (add member; deactivate/reactivate not in UI)
**Test Description:** From the SA Partner Detail → **Members** tab, an SA adds a portal user (member) to an active partner; the new user appears in the Portal Users list with **Active** status.
**Setup (precondition):** Log in as super-admin (stgsa); self-seed a throwaway partner, **Approve** it (Pending → Active), open the Members tab.
**Test Steps:**
1. The Members tab shows the Portal Users list (empty).
   → Expected: **Portal Users** heading + an **Add User** / **Add First User** control; empty-state "No portal users yet". **(PASSES.)**
2. Add a portal user (First / Last / Email / Password / Role via the Add-User form → **Create Portal User**).
   → Expected: **"Portal user created successfully"** confirmation. **(PASSES.)**
3. The new user appears as an Active row.
   → Expected: the new user's row shows the email + **Viewer** role + **Active** status; the header reads **Portal Users (1)**. **(PASSES.)**
**Expected (overall):** An SA can add a portal user to a partner; it appears Active in the Portal Users list.
**Note:** PASSED, verified 2026-08-03 (TC 12060514). Password for the throwaway staging user is generated and never logged. **Scope:** the Members tab exposes only **Add User** (create) + a per-row **Reset Password** action — there is **NO member deactivate / reactivate / suspend / remove** control on this build (verified live 2026-08-03: full row HTML + hover + keyword scan), so the deactivate/reactivate half of the original _014 intent is **not automatable** (UI not implemented). If/when that control ships, extend this TC. Negative counterpart: N/A — happy-path add (form-validation negatives are a separate TC). Idempotency: N/A — each add creates a distinct user (unique email).
#### PARTNER_UI_SA_PARTNER_MODULE_015 — FAILED (app bug · BUG-028, FE↔BE contract)
**Test Description:** From the SA Partner Detail page, an Active partner is suspended via **Partner actions → Deactivate**. Expected: the partner transitions out of Active (Suspended/Inactive) and portal access is revoked.
**Setup (precondition):** Log in as super-admin (stgsa); self-seed a throwaway partner, **Approve** it (Pending → Active).
**Test Steps:**
1. Deactivate (suspend) the active partner — Partner actions → Deactivate → confirm the "Deactivate Partner" dialog.
   → Expected: the request succeeds. **(FAILS.)**
2. The partner is suspended and no error is shown.
   → Expected: no error banner; partner is no longer Active (Suspended/Inactive). **(FAILS.)**
**Expected (overall):** An SA can suspend an Active partner from the UI; the partner loses portal access.
**Note:** FAILED — real app bug, verified 2026-07-31 (TC 12060515, **BUG-028**, marked `be_gap`). The **"Deactivate Partner" confirm dialog collects NO reason** (only Cancel / Deactivate buttons), but the deactivate API **requires** a non-empty reason string. The FE sends the request without one, so the BE rejects it — **"Server Error — reason should not be empty / reason must be a string / reason must be shorter than or equal to 2000 characters"** — the UI shows **"Failed to deactivate partner"** and the partner **stays Active**. Deterministic FE↔BE contract mismatch: **no SA can suspend a partner via the UI**. Fix: add a required Reason field to the dialog (and send it), or make `reason` optional on the API. This also blocks _016 (reactivate — cannot reach the Suspended state). Negative counterpart: N/A (single state-transition action). Idempotency: N/A — action never succeeds.
#### PARTNER_UI_SA_PARTNER_MODULE_016 — BLOCKED (depends on BUG-028)
**Test Description:** From the SA Partner Detail page, a **Suspended** partner is reactivated via **Partner actions → Reactivate**; the partner returns to Active and regains portal access.
**Intent:** Verify the Suspended → Active transition (the mirror of _015).
**Block reason:** Cannot reach the **Suspended** precondition. Suspending a partner is broken by **BUG-028** — the "Deactivate Partner" confirm dialog sends no `reason`, so the deactivate API rejects it ("reason should not be empty / must be a string / ≤ 2000 chars") and the partner stays Active. With no way to produce a Suspended partner through the UI (and no SA-side reactivate control reachable until one exists), the reactivate flow is untestable. **Unblock when BUG-028 is fixed** (then build: onboard → Approve → Deactivate → Reactivate → assert Active). Negative counterpart: N/A. Idempotency: N/A.
#### PARTNER_UI_SA_PARTNER_MODULE_017 — BLOCKED (candidate; application-review UI not deployed)
**Candidate TC** (not yet in the plan). **Design:** PN004 — Reject partner application.
**Intent:** From the SA partner-application review, reject a Pending application (with a reason) → the application moves to Rejected and the applicant is notified.
**Block reason:** No **Reject / Decline** control exists on this build (verified live 2026-08-03). A Pending partner's **Partner actions** menu offers **only "Approve Partner"**; the Directory row has no action control; a whole-page keyword scan finds no Reject/Decline. This is the partner-application **FSM review UI**, which is **not deployed on staging** (same gap as _004/_005/_006). Unblock when the application-review UI (with Reject) ships.
#### PARTNER_UI_SA_PARTNER_MODULE_018 — BLOCKED (candidate; activation-invite UI not deployed)
**Candidate TC** (not yet in the plan). **Design:** PN005 — Resend expired activation invite.
**Intent:** For a partner/user whose activation invite has expired, resend the activation invite from the SA side → a fresh invite/activation email is sent.
**Block reason:** No **Resend / Invite / Activation** surface exists on this build (verified live 2026-08-03, Pending **and** Approved partner + Members tab). The Members tab creates a portal user by **setting a password directly** ("Share these credentials with the partner") — there is no email-invite / activation-link flow, hence no "expired invite" state to resend, and no Resend control anywhere. Unblock when an activation-invite (email) flow with a Resend action is deployed.
#### PARTNER_UI_SA_PARTNER_MODULE_019 — BLOCKED (candidate; application-review UI not deployed)
**Candidate TC** (not yet in the plan). **Design:** PN027 — Request additional information from applicant.
**Intent:** From the SA partner-application review, request more information from a Pending applicant → the application enters an "info requested" state and the applicant is prompted.
**Block reason:** No **Request info / Additional information / More info** control exists on this build (verified live 2026-08-03). As with _017, a Pending partner's actions menu offers only "Approve Partner" and the whole-page keyword scan finds no request-info wording. Part of the same undeployed application-review FSM UI. Unblock when the review UI (with Request-info) ships.
### UI · SECURITY_COMPLIANCE

Cross-cutting security/compliance TCs — mostly SA-side / multi-partner / behavioural, so not directly buildable on the current partner-portal setup.
- PARTNER_UI_SECURITY_COMPLIANCE_001 — BLOCKED (Security: deny cross-partner data access — needs ≥2 partner fixtures + a defined cross-access attempt surface; the portal already scopes to the logged-in partner but there is no set-up to attempt viewing another partner's data)
- PARTNER_UI_SECURITY_COMPLIANCE_002 — BLOCKED (Security: audit — SA-action activity-log entry visible; the partner portal has no audit log (6-item nav), the Audit Log is SA-side (stgsa); needs an SA action + the log)
- PARTNER_UI_SECURITY_COMPLIANCE_003 — CANDIDATE (Security: deal-registration prospect data minimization). The one TC touching an existing partner surface — the register wizard requests a known field set (company name, domain, country, headcount, logo URL + contact name/email/phone/title). Buildable as an assertion that the requested field set ⊆ an allowed policy list — **needs the PRD-defined allowlist** of permitted prospect fields to assert against (not blocked by missing UI, blocked by a missing spec).
- PARTNER_UI_SECURITY_COMPLIANCE_004 — BLOCKED (Compliance: SA impersonation → "pending legal decision" placeholder; the impersonation/legal-placeholder feature is not implemented on this build)
### UI · TRAINING

**Whole module BLOCKED — not deployed on the partner portal** (re-verified live 2026-07-30, thorough probe: clean login + long wait). The partner nav has 6 items — Dashboard, Deals, Commissions, Directory, Resources, My Apps — with **no "Training"**; `/training`, `/certifications`, `/learning` do **not render** a `<main>`. The training / certification experience these TCs describe is not built/exposed (certification data exists SA-side — the SA partner-detail Members tab has a CERTIFICATE column — but there is no partner-facing Training page). Unblock when the Training module is deployed + certification fixture data exists.
- PARTNER_UI_TRAINING_001 — BLOCKED (view Training page: certifications + progress + locked/unlocked modules — module not deployed)
- PARTNER_UI_TRAINING_002 — BLOCKED (certification completed → status updates: module not deployed)
- PARTNER_UI_TRAINING_003 — BLOCKED (continue in-progress learning path → current module opens: module not deployed)

## 2. API

### API · AUTH_ACCESS_CONTROL

> Partner auth flows. Sessions minted self-contained from the SA side
> (`utils.partner_portal`). Auth endpoints (`/partner/auth/*`) return tokens + `/me`
> identity at the TOP LEVEL (no `data` wrapper). Not resource-creates → no
> duplicate-create idempotency; each TC embeds its own negative (rejection/invalidation).

#### PARTNER_API_AUTH_ACCESS_CONTROL_001
**Test Description:** Valid partner JWT authorizes a partner-scoped request.
**Setup (precondition):**
1. SA creates a partner.
2. SA approves the partner (pending → active).
3. SA invites a partner user (returns email + tempPassword).
4. Log in as that user → obtain a partner JWT.
**Test Steps:**
1. GET /partner/auth/me with the partner JWT.
   → Expected: 200, identity (userId + email) returned.
**Expected (overall):** A valid partner JWT authorizes partner-scoped requests.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_AUTH_ACCESS_CONTROL_002
**Test Description:** Non-partner / missing token on the partner API is unauthorized.
**Test Steps:**
1. GET /partner/auth/me with no token → 401.
2. GET /partner/auth/me with a non-partner (SA admin) token → 401.
**Expected (overall):** Missing / non-partner tokens are rejected (401).
**Note:** PASSED — verified 2026-06-25. (Approximates "tenant JWT" with the SA admin token — a non-partner token.) No sa-plans dependency.

#### PARTNER_API_AUTH_ACCESS_CONTROL_003
**Test Description:** Cross-partner access — a partner JWT cannot read another partner's deal (tenant isolation).
**Setup (precondition):**
1. Mint partner A (SA create → approve → invite → login) and register a deal for A; capture its id.
2. Mint partner B (separate partner, same SA-mint flow).
**Test Steps:**
1. Partner B calls GET /partner/portal/deals/{A_deal_id}.
   → Expected: refused with **404** (preferred — hides existence) or **403** — never 400 — and A's deal is NOT in the body.
**Expected (overall):** A partner cannot access another partner's deal — refused, no data leak.
**Note:** PASSED — verified 2026-07-23. Rule-5 cross-entity case. BE now returns **404** for cross-partner access (hides the resource's existence); the earlier gap (400 mislabel) is fixed. Tenant isolation holds (no data leak). Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_AUTH_ACCESS_CONTROL_004
**Note (BLOCKED):** Enforce partner MFA policy — a protected action must require MFA for the mandated scope (PRD §9.1: `PARTNER_ORG_ADMIN` role and/or Advanced/Premier tier). BLOCKED on a product decision: OQ-14 is unresolved — the MFA axis conflicts between PRD §9.1 (tier-based, Advanced+) and sa-portal-architecture §14.8 (role-based, `PARTNER_ORG_ADMIN`); until Renil decides which is authoritative, the expected result (who/which action must be MFA-gated) is undefined, so no assertion can be written. Also MFA enforcement is gated on Auth Hardening Phase 0 (PRs #633–641 must land before live auth). BE-side MFA endpoints already exist (partner: /v1/partner/auth/mfa/setup, /totp/enroll, /email-otp/send, /verify, /disable; sa-auth: /two-factors/otp, /sign-in/verify-otp) — so it is NOT endpoint-blocked. When unblocked, building also needs a deterministic OTP/TOTP (a fixed secret or a test-only bypass) from BE to complete the challenge in automation.

#### PARTNER_API_AUTH_ACCESS_CONTROL_005
**Note (BLOCKED):** MSP scope guard (PRD §9.2): an MSP partner accessing a managed tenant's payroll/salary/health data must be forbidden (403). No API surface in the Partner Platform to exercise it — payroll data lives in a separate HR/tenant service (the core product's Payroll module), outside sa-partners-api/sa-auth-api/connectors-api (grep of all 3 live specs → 0 payroll/salary endpoints, re-verified 2026-07-22). Also needs an MSP partner + a managed tenant, and MSP tenant provisioning is itself blocked (CLIENT_HEALTH_MSP_006). Unblock when a payroll surface + MSP scope are reachable from this domain.

#### PARTNER_API_AUTH_ACCESS_CONTROL_006
**Note (BLOCKED):** MSP scope guard (PRD §9.2: "Export data ❌"): an MSP partner exporting a managed tenant's employee records must be forbidden. No API surface in the Partner Platform to exercise it — there is no employee-export endpoint here (the only export is `/v1/sa/audit-logs/export`, i.e. the SA audit log, unrelated); employee records live in a separate HR/tenant service. Same dependency as _005 (needs MSP partner + managed tenant, itself blocked). Unblock when an employee-export surface + MSP scope are reachable from this domain.

#### PARTNER_API_AUTH_ACCESS_CONTROL_007
**Test Description:** Valid refresh token issues a new access token (no re-login).
**Setup (precondition):** SA create → approve → invite → login a partner user; capture the access + refresh tokens.
**Test Steps:**
1. POST /partner/auth/refresh with the captured refresh token.
   → Expected: 200, a new accessToken (different from the original).
2. The new access token authorizes GET /partner/auth/me.
   → Expected: 200.
3. POST /partner/auth/refresh with an invalid refresh token.
   → Expected: 401.
**Expected (overall):** Refresh mints a working new access token; invalid refresh rejected.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_AUTH_ACCESS_CONTROL_008
**Test Description:** Logout invalidates the refresh token.
**Setup (precondition):** SA create → approve → invite → login a partner user; capture the access + refresh tokens (session active).
**Test Steps:**
1. POST /partner/auth/logout with the access token.
   → Expected: 200/204.
2. POST /partner/auth/refresh with the (now-invalidated) refresh token.
   → Expected: 401.
**Expected (overall):** After logout the refresh token can no longer mint an access token.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_AUTH_ACCESS_CONTROL_009
**Test Description:** Change password updates credentials (new works, old fails).
**Setup (precondition):** SA create → approve → invite → login a partner user; capture the access token (session active).
**Test Steps:**
1. POST /partner/auth/change-password with a WRONG currentPassword.
   → Expected: 401 ("Current password is incorrect").
2. POST /partner/auth/change-password with the correct currentPassword.
   → Expected: 200/204.
3. Log in with the NEW password.
   → Expected: 200/201 + accessToken.
4. Log in with the OLD password.
   → Expected: 401.
**Expected (overall):** Password change rejects a wrong current; new credentials work, old are rejected.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.
### API · DEAL_REGISTRATION_PIPELINE

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_001
**Test Description:** Happy-path deal registration on POST /v1/sa/deals — valid payload creates a 'registered' deal with a protection window.
**Setup (precondition):** SA creates a partner; pick a published billing plan; build the deal payload (all fields).
**Test Steps:**
1. POST /v1/sa/deals with all fields (partnerId, planId, dealType='referral', prospect*, ACV, closeDate, notes) → register the deal.
   → Expected: request sent.
2. Verify the deal is accepted + persisted.
   → Expected: HTTP 201 (envelope statusCode 200); success message; server-assigned _id.
3. Verify EVERY submitted field is stored (no silent mutation).
   → Expected: all fields echoed; expectedCloseDate preserves the requested date.
4. Verify lifecycle.
   → Expected: status 'registered', protectionExpiresAt set, conflictStatus 'none'.
5. GET /v1/sa/deals/{id} (persistence).
   → Expected: same deal returned, status 'registered'.
**Teardown:** delete the parent partner (deals have no delete endpoint).
**Expected (overall):** Deal registered with all fields persisted exactly, protection window opened, retrievable.
**Note:** PASSED — full-param echo-check + lifecycle + persistence (rule-6).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_002
**Test Description:** Register a reseller deal — billing model 'reseller' is stored.
**Setup (precondition):** SA creates a partner; pick a published billing plan; build a deal payload with dealType='reseller'.
**Test Steps:**
1. POST /v1/sa/deals (register the reseller deal).
   → Expected: accepted (HTTP 201, envelope statusCode 200) + server-assigned _id.
2. Verify billing model stored + fields echoed.
   → Expected: stored dealType == 'reseller'; all other fields echoed unchanged; expectedCloseDate date preserved.
3. Verify lifecycle + retrievable (GET /v1/sa/deals/{id}).
   → Expected: status 'registered', protectionExpiresAt set; fetched deal keeps dealType 'reseller'.
**Teardown:** delete the parent partner.
**Expected (overall):** Reseller deal registered; dealType='reseller' IS the stored billing model (no separate field).
**Note:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_003
**Test Description:** Register a co-sell deal — co-sell metadata is stored.
**Setup (precondition):** SA creates a partner; pick a published billing plan; build a deal payload with dealType='co_sell'.
**Test Steps:**
1. POST /v1/sa/deals (register the co-sell deal).
   → Expected: accepted (HTTP 201, envelope statusCode 200) + server-assigned _id.
2. Verify co-sell metadata stored + fields echoed.
   → Expected: stored dealType == 'co_sell'; all other fields echoed unchanged; expectedCloseDate date preserved.
3. Verify lifecycle + retrievable (GET /v1/sa/deals/{id}).
   → Expected: status 'registered', protectionExpiresAt set; fetched deal keeps dealType 'co_sell'.
**Teardown:** delete the parent partner.
**Expected (overall):** Co-sell deal registered; dealType='co_sell' IS the stored metadata. The 70/30 split is computed downstream (_011, blocked) — out of scope here.
**Note:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_004
**Test Description:** Deal protection: a second partner registering the same prospect is flagged as a conflict.
**Setup (precondition):** SA creates two partners; pick a published billing plan; build one shared prospect identity (name + email) used by both.
**Test Steps:**
1. Partner 1 registers the deal first.
   → Expected: deal A accepted, conflictStatus 'none' (no prior deal).
2. Partner 2 registers the SAME prospect.
   → Expected: HTTP 201 (deal B still created, not rejected); conflictStatus 'flagged'; conflictingDealIds includes deal A's id.
3. GET /v1/sa/deals/{id} on deal B.
   → Expected: conflictStatus still 'flagged' (persisted).
**Teardown:** delete both partners.
**Expected (overall):** Cross-partner same-prospect deal is created but flagged against the first deal (queued for conflict resolution).
**Note:** PASSED. Distinct from the SAME partner re-registering the same prospect → hard 400 duplicate (_022).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_005
**Intent:** CRON — protection expiry with recent activity → auto-extend the protection window once.
**Note (BLOCKED):** No API surface. This is a scheduled background job (CRON) — protection auto-extension fires on the server's timer when a deal shows recent activity near expiry. There is no endpoint to trigger it on demand and no deterministic way to fast-forward the clock from a test, so the effect cannot be observed within a test run. Revisit if BE exposes a manual "run job" / time-travel hook. (P1 / Critical in the plan.)

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_006
**Intent:** CRON — protection expiry WITHOUT recent activity → the deal expires.
**Note (BLOCKED):** Time-driven CRON job (protection-expiry sweep). When the protection window (tier-based: 60d Select / 90d Advanced / 120d Premier) elapses with NO recent activity, the deal must transition to 'expired'. No on-demand job-trigger endpoint and no test clock on staging → the expiry window cannot be fast-forwarded and the sweep cannot be run on demand, so the transition can't be observed. Unblock when BE exposes a manual "run protection-expiry job" trigger or a test clock / backdating of protectionExpiresAt.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_007
**Intent:** CRON — a deal already auto-extended once must NOT be auto-extended a second time (cap enforced).
**Note (BLOCKED):** Time-driven CRON job. Verifying "no second auto-extend" needs a deal that was already auto-extended once (the outcome of _005) AND a second expiry cycle to elapse — both require the scheduled protection-expiry job to run + clock control to reach the second expiry, neither of which exists on staging. Depends on _005. Unblock when BE exposes a manual job trigger or a test clock / backdating.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_008
**Test Description:** Approve a registered deal (POST /v1/sa/deals/{id}/approve): status → approved, reviewer stamped; rate + rate-table version expected.
**Setup (precondition):** SA creates a partner; register a deal; confirm status 'registered'.
**Test Steps:**
1. Approve the registered deal (reviewNotes='QA-AUTO approve').
   → Expected: accepted (HTTP 201, envelope statusCode 200); status 'approved'.
2. Verify the reviewer is stamped.
   → Expected: reviewedAt + reviewedBy present.
3. Verify rate + rate-table version are stamped (per plan).
   → Expected: rate + rateTableVersion present in the response. **Currently FAILS** — neither is exposed.
**Teardown:** delete the parent partner.
**Expected (overall):** Deal approved + reviewer stamped; rate / rate-table-version stamping pending BE.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap: rate/rateTableVersion are NOT in the deal API response and no commission is created at approve. Confirm with BE: stamped internally (not serialized) / different stage (deal win) / unimplemented.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_009
**Test Description:** Resolve a flagged deal conflict (POST /v1/sa/deals/{id}/resolve-conflict): decision + reasoning are stamped and immutable.
**Setup (precondition):** SA creates two partners; both register the SAME prospect so the second deal (deal B) is 'flagged'.
**Test Steps:**
1. Resolve the conflict (decision='resolved_for_partner', reasoning) — decision + reasoning are stamped.
   → Expected: HTTP 201 (envelope statusCode 200); conflictStatus='resolved_for_partner'; conflictResolution{decision, reasoning, resolvedBy, resolvedAt} stamped and matches what was sent.
2. Immutability: a second resolve with a different decision/reasoning.
   → Expected: rejected (4xx); message explains the deal is no longer in FLAGGED conflict state.
3. Re-read GET /v1/sa/deals/{id}.
   → Expected: decision + reasoning are still the original (unchanged) — immutable.
**Teardown:** delete both partners.
**Expected (overall):** Conflict resolved once; decision + reasoning are immutable.
**Note:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_010
**Test Description:** Approving a deal emits a partner.deal.approved event (the CRM-sync trigger).
**Setup (precondition):** SA creates a partner; register a deal (status 'registered').
**Test Steps:**
1. Approve the deal.
   → Expected: status 'approved'.
2. Verify a 'deal approved' event is published to the audit log (GET /v1/sa/audit-logs, retry up to 3× for eventual consistency).
   → Expected: an event whose action mentions deal + approve references this deal id, and its `after.status == 'approved'` (records the registered→approved transition).
**Teardown:** delete the parent partner.
**Expected (overall):** Deal-approved event is published. CRM owner/stage update is a downstream service (connectors/CRM Integration), out of scope.
**Note:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_011
**Note (BLOCKED):** Not automated — was mislabeled PASSED/Auto=YES (false-green), corrected to BLOCKED. The co-sell 70/30 split is computed DOWNSTREAM; at register time the deal record carries no split field (verified via _003) and there is no API to read the computed split, so the 70/30 default cannot be asserted. Same dependency family as _012. Unblock when BE exposes the computed split (or a split-calc API).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_012
**Note (BLOCKED):** Depends on the co-sell split-calculation engine (feature _011), which is downstream and not exposed as an API — there is no endpoint to submit a co-sell split override, so the "override at/below $100K ACV is not accepted" rule cannot be exercised (threshold is ABOVE $100K ACV). Unblock when BE exposes the split-override API.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_013
**Test Description:** Resolving the FLAGGED deal FOR its partner (decision=resolved_for_partner, citing the prospect's confirmation) makes that deal the winner and automatically flips the conflicting deal to the loser; both keep status 'registered'.
**Setup (precondition):** SA creates two partners; both register the SAME prospect (name+email) → deal A (first) + deal B (second, flagged).
**Test Steps:**
1. Resolve the flagged deal B FOR its partner (decision='resolved_for_partner', reasoning cites prospect confirmation).
   → Expected: HTTP 201 (envelope statusCode 200); deal B conflictStatus='resolved_for_partner'; conflictResolution recorded.
2. Check the conflicting deal A (GET by id) — auto-flipped to the loser.
   → Expected: deal A conflictStatus='resolved_against_partner'.
3. Re-read the winner deal B (GET by id) — outcome persists.
   → Expected: deal B still 'resolved_for_partner' and status 'registered'.
**Teardown:** delete both partners.
**Expected (overall):** the confirmed partner wins the conflict and the other deal is flipped to the loser.
**Note:** PASSED. Decision/reasoning immutability is covered by _009; negative resolve inputs by _029.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_014
**Note (BLOCKED):** No distinct API surface. resolve-conflict (POST /v1/sa/deals/{id}/resolve-conflict) is an SA-manual decision (enum resolved_for_partner|resolved_against_partner); it accepts no "prospect unreachable" signal and applies no automatic "first-registered-wins" tiebreaker. The only executable path (SA manually resolving for the earlier deal) is mechanically identical to _013 → nothing distinct to assert. Unblock if BE implements an automatic tiebreaker; otherwise covered by _013.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_015
**Note (BLOCKED):** Depends on tenant-provisioning + commission infrastructure not reachable from this test domain. Verifying "no registration → no attribution/commission" requires POST /internal/tenants/provision (internal-only), reading tenant.attribution.partnerId == null, asserting no partner_commissions row, and confirming no blazeup.partner.commission.earned event — none exposed to QA here. Negative companion of PARTNER_API_006 (§3 Scenario I). Unblock when the provisioning endpoint + commission/event verification become available.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_016
**Test Description:** SA manually extends a registered deal's protection window (POST /v1/sa/deals/{id}/extend-protection, body addedDays + reasoning).
**Setup (precondition):** SA creates a partner; pick a published plan; register a deal and capture its current protectionExpiresAt (old expiry).
**Test Steps:**
1. SA extends the protection window (addedDays=30 + reasoning).
   → Expected: accepted (HTTP 201, envelope statusCode 200); message confirms the extension.
2. Verify the window moved later by the requested days.
   → Expected: new protectionExpiresAt > old; delta is EXACTLY 30 days; deal stays 'registered'.
3. Verify the new window persists (GET /v1/sa/deals/{id}).
   → Expected: persisted protectionExpiresAt == the extended value.
**Teardown:** delete the parent partner.
**Expected (overall):** SA manual extension pushes the protection window out by exactly the requested days.
**Note:** PASSED. Window extends by exactly addedDays from the OLD expiry (e.g. +30d: 2026-08-29 → 2026-09-28). Plan frames this as a queued partner request, but the implemented endpoint is a DIRECT SA extension (applied immediately) — confirm with BE whether a separate queued partner-request flow is also expected.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_017
**Note (BLOCKED):** Needs a 90-day clock staging can't provide. "Re-registering a conflict-lost prospect is accepted after 90 days (when no close exists)" requires a conflict-lost deal whose loss is 90+ days old; createdAt/lostAt are server-assigned and cannot be backdated, and there is no test clock/fast-forward. The negative companion ("reject re-registration BEFORE 90 days") IS buildable now as a separate TC. Unblock when BE provides a test clock or backdating.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_018
**Test Description:** SA marks an approved deal as won (POST /v1/sa/deals/{id}/win, WinDealDto = tenant-provisioning intake): status → 'won', actualAcvCents + intake stored, and a partner.deal.won event is emitted (tenant provisioning + commission are downstream/async).
**Setup (precondition):** SA creates a partner; register a deal; approve it (status 'approved'); build the win intake (companyWebsite, industry, admin*, tenantDomain, region, billingCycle, actualAcvCents…).
**Test Steps:**
1. Mark the approved deal as won (capture tenant-provisioning intake).
   → Expected: accepted (HTTP 201, envelope statusCode 200); status 'won'; confirm message.
2. Verify the won deal stores actualAcvCents + the submitted intake fields.
   → Expected: actualAcvCents echoed; companyWebsite/industry/adminFirstName/adminLastName/tenantDomain stored as sent.
3. Verify a 'partner.deal.won' audit event is emitted (approved → won).
   → Expected: an audit entry (action 'partner.deal.won') for this deal with after.status == 'won'.
4. Verify the won status persists (GET /v1/sa/deals/{id}).
   → Expected: status 'won', actualAcvCents persisted.
**Teardown:** delete the parent partner.
**Expected (overall):** An approved deal transitions to 'won' with the intake stored and a won-event emitted; tenant provisioning + commission are downstream (async — the commission does not appear synchronously in /v1/sa/commissions), out of scope here.
**Note:** PASSED. Approve now requires `planId` (ApproveDealDto changed — client auto-resolves it). Win response message: "Deal marked as won; tenant provisioning kicked off". Negative/illegal-state counterpart is _034.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_019
**Test Description:** SA marks an approved deal as lost (POST /v1/sa/deals/{id}/lose). Losing requires the deal to be 'approved' first.
**Setup (precondition):** SA creates a partner; pick a plan; register a deal and approve it (status 'approved').
**Test Steps:**
1. Mark the deal as lost (notes).
   → Expected: accepted (HTTP 201, envelope statusCode 200); status becomes 'lost'.
2. Verify the lost status persists (GET /v1/sa/deals/{id}).
   → Expected: fetched deal status still 'lost'.
**Teardown:** delete the parent partner.
**Expected (overall):** An approved deal transitions to 'lost' (partner notification is downstream, out of scope).
**Note:** PASSED. Negative/illegal-state counterpart is _032.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_020
**Test Description:** SA retrieves a single deal by id (GET /v1/sa/deals/{id}) — full record.
**Setup (precondition):** SA creates a partner; pick a plan; register a deal and capture its id.
**Test Steps:**
1. GET the deal by id.
   → Expected: HTTP 200 (envelope statusCode 200); the returned id matches the requested deal.
2. Verify the full record.
   → Expected: required fields present (partnerId, dealType, prospectName, prospectCountry, estimatedAcvCents, status, protectionExpiresAt, conflictStatus); status 'registered'; no sensitive field (password/token/secret) is leaked.
**Teardown:** delete the parent partner.
**Expected (overall):** Get-by-id returns the full, correct deal record with no sensitive leak.
**Note:** PASSED. Negative (ghost/malformed id) counterpart is _031.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_021
**Test Description:** Negative counterpart of register (_001): every invalid/incomplete payload must be rejected with 4xx + a descriptive message and create no deal. All cases run (failures collected) so one gap never hides the others.
**Setup (precondition):** SA creates a partner; pick a published plan (valid baseline payload). FK-absence proof (rule 3): GET the ghost planId 'no-such-plan-qa' and assert it returns 4xx (genuinely absent) before using it below.
**Test Steps:** (each case = one POST /v1/sa/deals with the baseline payload mutated; expected 4xx + message hint)
1. Missing partnerId → 4xx, message mentions "partner".
2. Missing dealType → "dealtype must be one of".
3. Invalid dealType ('wholesale') → "dealtype must be one of".
4. Missing prospectName → "prospectname".
5. Missing prospectCountry → "prospectcountry".
6. Invalid prospectEmail ('not-an-email') → "must be an email".
7. Missing estimatedAcvCents → "estimatedacvcents".
8. Negative ACV (-100) → "must not be less than".
9. Missing expectedCloseDate → "iso 8601".
10. Bad date format ('31-12-2026') → "iso 8601".
11. Ghost partnerId (000000000000000000000000) → "not found".
12. Ghost planId ('no-such-plan-qa', verified absent above) → **404**, message mentions "plan".
**Teardown:** delete the parent partner (removes any deal accidentally created by the planId gap).
**Expected (overall):** Every invalid register payload is rejected with a clear message and no deal is created; planId should be validated against the catalog.
**Note:** PASSED — verified 2026-07-23. BE fixed the gap (case 12): a non-existent planId is now rejected with **404** (was accepted 201). All 12 cases pass. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_022
**Test Description:** Idempotency/duplicate counterpart of _001: the SAME partner registering the SAME prospect twice is rejected (no second deal).
**Setup (precondition):** SA creates one partner; pick a published plan; build a unique prospect identity reused for both register calls.
**Test Steps:**
1. First registration by the partner succeeds.
   → Expected: HTTP 201, server-assigned id, conflictStatus 'none'.
2. The SAME partner re-registers the SAME prospect (name+email).
   → Expected: HTTP 400, message contains "already exists".
3. Verify no second deal was created (inspect the rejected response body).
   → Expected: no deal id (_id/id) in the body — hard reject, not the flagged path.
**Teardown:** delete the parent partner.
**Expected (overall):** Same-partner duplicate is a hard 400 reject; distinct from _004 (a DIFFERENT partner → 201 + conflictStatus 'flagged').
**Note:** PASSED.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_028
**Test Description:** Negative counterpart of _008 (approve): three illegal approve targets, each rejected with its own code + a clear message (never silently succeed). All cases run (failures collected).
**Setup (precondition):** SA creates a partner; register a deal and approve it (status 'approved') so the illegal-transition case has a target.
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/approve)
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → **404** Not Found, message "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Already-approved deal (illegal transition) → **400** 'cannot transition' (409 Conflict would be more precise, but 400 is accepted).
**Teardown:** delete the parent partner.
**Expected (overall):** Non-existent id → 404; malformed id → 400; illegal transition → 400/409. Never 5xx.
**Note:** PASSED — verified 2026-07-23. BE fixed the ghost-id gap (case 1): a well-formed non-existent id now returns **404** "not found" (was 400). All 3 cases pass. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_029
**Test Description:** Negative counterpart of _009 (resolve-conflict): six invalid inputs, each rejected with its own code + a clear message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner; register a deal (status 'registered', conflictStatus 'none' — a non-flagged target).
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/resolve-conflict)
1. Invalid decision enum ('whatever') → **400** 'decision must be one of'.
2. Missing decision → **400** 'decision must be one of'.
3. Missing reasoning → **400** message mentions "reasoning".
4. Malformed id ('not-an-id') → **400** 'invalid id'.
5. Non-flagged deal (illegal state) → **400** message mentions "flagged" (409 Conflict would be more precise, but 400 is accepted).
6. Ghost id (well-formed but non-existent, 000000000000000000000000) → **404** Not Found, message "not found".
**Teardown:** delete the parent partner.
**Expected (overall):** Validation/format/state errors → 400; non-existent id → 404. Never 5xx.
**Note:** PASSED — verified 2026-07-23. BE fixed the ghost-id gap (case 6): a well-formed non-existent id now returns **404** "not found" (was 400). All 6 cases pass. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_030
**Test Description:** Negative counterpart of _016 (extend-protection): eight invalid inputs, each rejected with its own code + a clear message. BE validates the body BEFORE the deal lookup, so field cases are self-proving on a ghost id (no real deal needed). All cases run (failures collected).
**Setup (precondition):** none — cases target a ghost/malformed id directly (body validation fires first; no sa-plans dependency).
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/extend-protection)
1. Missing addedDays → **400** message "addeddays".
2. Missing reasoning → **400** message "reasoning".
3. addedDays = 0 → **400** "less than 1".
4. Negative addedDays → **400** "less than 1".
5. addedDays over max (181) → **400** "greater than 180".
6. Non-numeric addedDays ('abc') → **400** message "addeddays".
7. Malformed id ('not-an-id') → **400** "invalid id".
8. Ghost deal id (valid body, well-formed but non-existent) → **404** Not Found, message "not found".
**Expected (overall):** Body-validation / boundary / format / malformed → 400; non-existent id → 404. Never 5xx. Spec constraint: addedDays ∈ 1..180; reasoning required + non-empty.
**Note:** PASSED — verified 2026-07-23. BE fixed the ghost-id gap (case 8): a well-formed non-existent id now returns **404** "not found" (was 400). All 8 cases pass. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_031
**Test Description:** Negative counterpart of _020 (get-by-id): two distinct rejection semantics — a malformed id is a bad request (400), a ghost id is a missing resource (404). Self-proving; GET → no idempotency concern. All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/deals/{id}; expected code + message hint, never 5xx)
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → **404** Not Found, message mentions "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message mentions "invalid id".
**Expected (overall):** A malformed id → 400; a well-formed but non-existent id → 404. Never 5xx, no record returned.
**Note:** PASSED — verified 2026-07-23. BE fixed the ghost-id gap (case 1): a well-formed non-existent id now returns **404** "not found" (was 400, status contradicting the message). Both cases pass. This was the root-cause TC for the systemic ghost→404 gap. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_032
**Test Description:** Negative counterpart of _019 (lose): three illegal lose targets, each rejected with its own code + a clear message (never 5xx). All cases run (failures collected).
**Setup (precondition):** SA creates a partner; register a deal (status 'registered', NOT approved — lose requires 'approved').
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/lose)
1. Registered deal (illegal transition — not approved) → **400** 'cannot transition' (409 Conflict would be more precise, but 400 is accepted here).
2. Ghost id (well-formed but non-existent, 000000000000000000000000) → **404** Not Found, message "not found".
3. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Teardown:** delete the parent partner.
**Expected (overall):** Illegal transition → 400/409; malformed id → 400; non-existent id → 404. Never 5xx.
**Note:** PASSED — verified 2026-07-23. BE fixed the ghost-id gap (case 2): a well-formed non-existent id now returns **404** "not found" (was 400). All 3 cases pass. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_033
**Test Description:** Idempotency counterpart of _016 (extend-protection): a repeat extension is ADDITIVE, not a no-op or a cap.
**Setup (precondition):** SA creates a partner; pick a plan; register a deal and capture its protectionExpiresAt (exp0).
**Test Steps:**
1. First extend (+30 days).
   → Expected: exp1 == exp0 + 30d.
2. Second extend (+30 days) — repeat behaviour.
   → Expected: HTTP 200; exp2 == exp1 + 30d (stacks from the current expiry); deal stays 'registered'.
3. Verify the total window persists (GET /v1/sa/deals/{id}).
   → Expected: persisted window == exp0 + 60d (2×addedDays).
**Teardown:** delete the parent partner.
**Expected (overall):** extend-protection is a parameterized mutating action — repeats are additive by design (not an idempotent no-op, not capped). Each call is also recorded in protectionExtensions[].
**Note:** PASSED. Probed per rule 8 (mutating action ≠ POST-create): behaviour is additive (exp0 +30 → +30 = +60). BE stamps each extension in protectionExtensions[] (extendedBy/at, previous/newExpiresAt, addedDays, trigger, reasoning).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_034
**Test Description:** Negative counterpart of _018 (win): illegal transitions + bad ids are rejected with the correct code; the DTO's required intake fields should be enforced too. All cases run (failures collected).
**Setup (precondition):** SA creates a partner; a fresh approved deal is built per required-field case (a successful win consumes the deal).
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/win)
1. Missing companyWebsite → expected **400** (required). **Currently FAILS** — BE returns 201 (won).
2. Missing industry → expected **400**. **Currently FAILS** — BE returns 201.
3. Missing adminFirstName → expected **400**. **Currently FAILS** — BE returns 201.
4. Missing adminLastName → expected **400**. **Currently FAILS** — BE returns 201.
5. Win a non-approved (registered) deal → **400** 'cannot transition'.
6. Ghost deal id (well-formed, absent) → **404** 'not found'. (Win correctly returns 404 here.)
7. Malformed deal id ('not-an-id') → **400** 'invalid id'.
8. Re-win an already-won deal → **400** 'cannot transition from won to won' (repeat rejected; mutating action, not a create).
**Teardown:** delete the parent partner.
**Expected (overall):** Missing required intake → 400; non-approved/already-won → 400; ghost id → 404; malformed id → 400.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (cases 1–4): WinDealDto declares companyWebsite/industry/adminFirstName/adminLastName as required, but the BE accepts a win with any/all missing (even an empty body → 201, deal won) — required-intake validation is not enforced. Cases 5–8 are correct (note: win returns 404 for a ghost id, unlike other SA endpoints). Confirm with BE.

### API · DEAL_APPROVAL_QUEUE

#### PARTNER_API_DEAL_APPROVAL_QUEUE_001
**Test Description:** SA rejects a queued (registered) deal from the approval queue (POST /v1/sa/deals/{id}/reject, body reviewNotes).
**Setup (precondition):** SA creates a partner; pick a plan; register a deal (status 'registered' = queued for review).
**Test Steps:**
1. Reject the deal with a reason (reviewNotes).
   → Expected: accepted (HTTP 201, envelope statusCode 200); status becomes 'rejected'.
2. Verify the rejection persists (GET /v1/sa/deals/{id}).
   → Expected: fetched deal status still 'rejected'.
**Teardown:** delete the parent partner.
**Expected (overall):** A registered deal is rejected and stays rejected.
**Note:** PASSED. Negative/illegal-state counterpart is _011.

#### PARTNER_API_DEAL_APPROVAL_QUEUE_011
**Test Description:** Negative counterpart of _001 (reject): three illegal reject targets, each rejected with its own code + a clear message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner; register a deal and reject it (status 'rejected') so the illegal-transition case has a target.
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/reject)
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → **404** Not Found, message "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Already-rejected deal (illegal transition) → **400** 'cannot transition' (409 Conflict would be more precise, but 400 is accepted).
**Teardown:** delete the parent partner.
**Expected (overall):** Non-existent id → 404; malformed id → 400; illegal transition → 400/409. Never 5xx.
**Note:** PASSED — verified 2026-07-23. BE fixed the ghost-id gap (case 1): a well-formed non-existent id now returns **404** "not found" (was 400). All 3 cases pass. Stale `be_gap` marker to be removed from code; Bug_Tracker entry can be closed.

### API · DEAL_COLLABORATION

#### PARTNER_API_DEAL_COLLABORATION_001
**Note (BLOCKED):** PRD §4.5 / §8.5 specifies a per-deal **SHARED NOTES thread** — partner (on stgpartners) and the BlazeUp SA rep (on stgsa) both add notes to the SAME deal, each note recording the author (actor) + timestamp, append-only (see the §4.5 "SHARED NOTES" mock: "Jamie Walsh 1 May …" / "Sarah Chen 2 May …"). PRD §8.5 puts the write on the partner side: `PATCH /v1/partner/deals/:id (notes, docs)`. NOT built on staging: (a) the partner-portal deal is **GET-only** (`GET /v1/partner/portal/deals/{id}` — no PATCH), so a partner cannot add a note; (b) the SA side (`PATCH /v1/sa/deals/{id}`) only **overwrites one flat `notes` string** — no per-note actor/timestamp, no append, no shared thread. So the shared-notes collaboration feature does not exist yet. Do NOT re-scope to "SA overwrites a flat notes string" and call it collaboration (that is a different, lesser feature and would misrepresent the test). Unblock when BE ships the shared-notes thread (actor + timestamp, append, partner + SA writers).

#### PARTNER_API_DEAL_COLLABORATION_002
**Note (BLOCKED):** PRD §4.5 shows a per-deal **DOCUMENTS** area ("[Upload]" + a document list) and §8.5 folds it into `PATCH /v1/partner/deals/:id (notes, docs)`. NOT built on staging: the partner-portal deal is GET-only, the SA `UpdateDealDto` has no `documents` field, and PATCH with a `documents` payload is rejected ("No editable fields provided") — there is no endpoint to upload, list, or download deal documents. Unblock when BE exposes a deal-documents surface.

### API · PIPELINE_MANAGEMENT

#### PARTNER_API_PIPELINE_MANAGEMENT_001
**Test Description:** A partner lists its deals (GET /partner/portal/deals) — only its OWN deals are returned (scoped).
**Setup (precondition):** Mint a partner-portal session (SA creates → approves → invites the partner user → logs in for a partner JWT); the partner registers one deal via the portal.
**Test Steps:**
1. GET the partner's own deals list (GET /partner/portal/deals?limit=20).
   → Expected: HTTP 200; `data` is a non-empty list.
2. Verify the registered deal appears AND the list is scoped to the caller.
   → Expected: the registered deal id is in the list AND every row's partnerId == the caller's partner (no cross-partner leakage).
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** The own-deals list is correctly scoped to the authenticated partner.
**Note:** PASSED. Negative (invalid filter/pagination) counterpart is _011.

#### PARTNER_API_PIPELINE_MANAGEMENT_002
**Test Description:** A partner filters its deals list by status (GET /partner/portal/deals?status=registered).
**Setup (precondition):** Mint a partner-portal session; the partner registers one deal (status 'registered').
**Test Steps:**
1. Filter the own-deals list by status=registered (GET /partner/portal/deals?limit=20&status=registered).
   → Expected: HTTP 200; non-empty; every returned deal has status 'registered' AND the freshly-registered deal is included.
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** The status filter is applied correctly.
**Note:** PASSED. Valid deal-status enum: registered, approved, in_progress, won, lost, expired, rejected.

#### PARTNER_API_PIPELINE_MANAGEMENT_011
**Test Description:** Negative counterpart of _001/_002: an invalid filter / oversized pagination is validated by the BE and rejected with 4xx + a clear message (never 5xx). All cases run (failures collected).
**Setup (precondition):** Mint a partner-portal session.
**Test Steps:** (each case = one GET /partner/portal/deals with an invalid query)
1. status=bogus (out-of-enum) → **400**, message mentions "status".
2. limit=999999 (over max) → **400**, message mentions "limit".
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Invalid filter/pagination is rejected (4xx), never 5xx.
**Note:** PASSED. BE validates both (returns 400) — not lenient.
### API · TENANT_PROVISIONING_ATTRIBUTION

> Note: this section's TC ids group several features (close→provision→commission→attribution). Per the user's decision the grouping is kept as-is for now; some rows really belong to co-sell / commissions / CRM.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_001
**Note (BLOCKED):** Co-sell split accept/lock endpoint POST /v1/partner/deals/:id/cosell-split-accept not in dev build. (Mis-grouped — really a co-sell case.) Unblock when BE ships it.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_002
**Note (BLOCKED):** Depends on the deal win/close flow (DEAL_018, deferred) + downstream tenant-provisioning & commission/event surfaces not reachable from this domain. Unblock when win is safely runnable + those surfaces are exposed.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_003
**Note (BLOCKED):** Depends on win/close + downstream billing/invoice ("reseller close → invoice targets the reseller"). Unblock when win + billing verification are available.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_004
**Note (BLOCKED):** Depends on win/close + a pre-provisioned tenant + billing line-items downstream. Unblock when expansion-close + billing verification are exposed.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_005
**Note (BLOCKED):** Commission-calc engine is downstream with no API to read the computed commission ("expansion NN → full rate"). Same family as COMMISSIONS_PAYOUTS_001. Unblock when BE exposes computed commissions.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_006
**Note (BLOCKED):** Same as _005 — commission-calc downstream, no read API ("expansion EN → lower rate"). Unblock when BE exposes computed commissions.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_007
**Note (BLOCKED):** Depends on the deal-win flow (DEAL_018, deferred) + a downstream CRM connector to verify "deal won → CRM closes won with tenant id". Unblock when win is safely runnable.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_008
**Note (BLOCKED):** Needs a provisioned tenant (post-win) to inspect tenant.attribution permanent partner fields — downstream surface not reachable here. Unblock when the tenant/attribution read surface is exposed.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_009
**Note (BLOCKED):** No exposed API for an SA tenant-attribution override with two-eye (dual) approval + history. Unblock when BE exposes the attribution-override endpoint.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_010
**Note (BLOCKED):** Co-sell split lock-after-accept endpoint POST /v1/partner/deals/:id/cosell-split-accept not in dev build. Same endpoint as _001. Unblock when BE ships it.

#### PARTNER_API_TENANT_PROVISIONING_ATTRIBUTION_011
**Note (NOT_STARTED — redundant / cross-ref):** "Validate invalid expectedCloseDate → 400" is already exercised by **DEAL_REGISTRATION_PIPELINE_021** (its bad-date case: `expectedCloseDate` not ISO-8601 → 400, and missing expectedCloseDate → 400). _021 currently PASSES, so this validation is covered. NOT blocked — there is simply no distinct assertion to add if built standalone. Do NOT build a duplicate; treat as covered by _021. (If a standalone line is ever needed, point it at the same POST /v1/sa/deals date validation.)
### API · REFERRAL_ATTRIBUTION

#### PARTNER_API_REFERRAL_ATTRIBUTION_001
**Note (BLOCKED):** Referral-attribution endpoints (GET/POST /v1/partner/referral-links) absent from the deployed spec (confirmed 2026-06-30: 0 referral paths); the 30-day Redis TTL also needs clock control. Unblock when BE ships the referral-links API + a test clock.

#### PARTNER_API_REFERRAL_ATTRIBUTION_002
**Note (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_003
**Note (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_004
**Note (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

### API · CLIENT_HEALTH_MSP

> All BLOCKED — the My Clients / Client Health / MSP module (`/v1/partner/clients/*`) is absent from the deployed spec (confirmed 2026-06-30: sa-partners-api = 68 paths, 0 /client* paths). Unblock when BE ships the module.

#### PARTNER_API_CLIENT_HEALTH_MSP_001
**Note (BLOCKED):** GET /v1/partner/clients (My Clients — post-close tenants) not implemented.

#### PARTNER_API_CLIENT_HEALTH_MSP_002
**Note (BLOCKED):** GET /v1/partner/clients/:tenantId/health (usage/renewal/ticket metrics) not implemented.

#### PARTNER_API_CLIENT_HEALTH_MSP_003
**Note (BLOCKED):** GET /v1/partner/clients/:tenantId/tickets (no MSP consent → count + severity only) not implemented. Pairs with _004.

#### PARTNER_API_CLIENT_HEALTH_MSP_004
**Note (BLOCKED):** GET /v1/partner/clients/:tenantId/tickets (with MSP consent → full ticket content) not implemented. Pairs with _003.

#### PARTNER_API_CLIENT_HEALTH_MSP_005
**Note (BLOCKED):** PATCH MSP consent under /v1/partner/clients/* (revoke → content access stops immediately) not implemented.

#### PARTNER_API_CLIENT_HEALTH_MSP_006
**Note (BLOCKED):** POST MSP tenant provision under /v1/partner/clients/* (creates a partner_managed tenant) not implemented.

#### PARTNER_API_CLIENT_HEALTH_MSP_007
**Note (BLOCKED):** MSP handoff/transfer under /v1/partner/clients/* (preserve old history + emit event) not implemented.

#### PARTNER_API_CLIENT_HEALTH_MSP_008
**Note (BLOCKED):** MSP tier qualification (total managed ARR) under /v1/partner/clients/* not implemented; also a downstream calc.

#### PARTNER_API_CLIENT_HEALTH_MSP_009
**Note (BLOCKED):** MSP consent grant/revoke audit under /v1/partner/clients/* (event with actor + timestamps, immediate access change) not implemented.
### API · COMMISSIONS_PAYOUTS

> Spec (confirmed 2026-06-30): commission endpoints EXIST (/v1/sa/commissions + /approve /mark-paid /dispute /clawback, /v1/partner/portal/commissions + /summary /dispute, /v1/sa/rate-table). ABSENT: waiver, spiff, approve-payout, payout/banking. Most lifecycle TCs still need a commission record, which is only created by the deferred win pipeline (DEAL_018). Only _002 and _006 are buildable now.

#### PARTNER_API_COMMISSIONS_PAYOUTS_001
**Note (BLOCKED):** Downstream commission-calc ("renewal EE → lowest rate"); needs the win→commission pipeline (deferred) and there's no API to read the computed rate. Unblock when a commission can be created + its rate is readable.

#### PARTNER_API_COMMISSIONS_PAYOUTS_002
**Test Description:** SA lists the commission ledger: GET /sa-partners-api/v1/sa/commissions returns a paginated, filterable, well-formed ledger.
**Test Steps:**
1. GET /v1/sa/commissions (page=1, limit=5).
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}.
2. Verify pagination.
   → Expected: returned page size ≤ requested limit (5).
3. Verify each entry's schema + no sensitive leak (data-dependent).
   → Expected: each entry carries an id and a valid status enum (earned/pending_approval/approved/paid/disputed/clawback/cancelled); no password/token/secret key. WARN-skips if the ledger is empty.
4. Verify a status filter returns only matching entries (data-dependent).
   → Expected: status=<first entry's status> returns only that status. WARN-skips if empty.
**Expected (overall):** Commission-ledger list returns a correct, paginated, filterable, non-sensitive envelope.
**Note:** PASSED. Read-only (no setup/cleanup). Commission rows are created downstream on deal-win (DEAL_018, deferred), so on staging the ledger is legitimately empty → steps 3–4 WARN-skip; the list contract still holds. Negative (invalid filter/pagination) counterpart is _017.

#### PARTNER_API_COMMISSIONS_PAYOUTS_003
**Note (BLOCKED, positive):** POST /v1/partner/portal/commissions/{id}/dispute exists, but disputing needs a real commission {id} (deferred win pipeline). The negative (dispute a ghost id → 4xx) is buildable now. Unblock when a commission record can be created.

#### PARTNER_API_COMMISSIONS_PAYOUTS_004
**Note (BLOCKED):** Product-failure waiver POST /v1/partner/commissions/:id/waiver absent from the spec (2026-06-30). Unblock when BE ships the waiver endpoint.

#### PARTNER_API_COMMISSIONS_PAYOUTS_005
**Note (BLOCKED):** Waiver decision / final-outcome event endpoint absent (no waiver path, 2026-06-30). Pairs with _004/_012.

#### PARTNER_API_COMMISSIONS_PAYOUTS_006
**Test Description:** SA upserts a commission rate (POST /sa-partners-api/v1/sa/rate-table): the new rate is stored in place and the prior value is kept under previousRate (a one-level version trail); no duplicate row is created.
**Setup (precondition):** GET the rate table; pick an EXISTING combo (tier, dealType, commissionType) and capture its original rate + clawbackWindowDays. Register a teardown that RESTORES the original rate (there is no DELETE endpoint, so the test never creates a new combo).
**Test Steps:**
1. Upsert the SAME combo with a new rate.
   → Expected: accepted (HTTP 201, envelope statusCode 200); confirm message.
2. Verify the new rate is stored + the prior value is kept under previousRate (version trail).
   → Expected: stored rate == new rate; previousRate.rate == the original rate; the combo (tier/dealType/commissionType) is unchanged.
3. Verify GET reflects the new rate AND the combo is still exactly ONE row (in-place, no duplicate).
   → Expected: one matching row with the new rate and the same _id.
4. Repeat the upsert with a 2nd new rate (mutating action — probe the repeat behavior).
   → Expected: in-place update — still one row; rate == 2nd value; previousRate advances to the 1st value (not a duplicate create).
**Teardown:** restore the combo's original rate.
**Expected (overall):** Rate upsert stores the new rate in place, versions the prior value via previousRate, and never duplicates the combo.
**Note:** PASSED. Endpoint is POST /v1/sa/rate-table (plan said "PUT /internal/commission/rates" — method PUT→POST, path renamed). rate constraint 0..1. The "cached" (Redis invalidation) side is internal / not API-observable (see _014). Mutating upsert → no separate duplicate-create idempotency TC (repeat is in-place, verified in step 4). Negative counterpart is _018.

#### PARTNER_API_COMMISSIONS_PAYOUTS_007
**Note (BLOCKED):** Two-approver "approve over threshold" needs /v1/sa/commissions/{id}/approve-payout (dual approval), absent from the spec — only a single POST /{id}/approve exists. Also needs a commission record.

#### PARTNER_API_COMMISSIONS_PAYOUTS_008
**Note (BLOCKED):** Referral-attribution endpoints absent (0 referral paths, 2026-06-30) + 40-day TTL needs clock control. Same root as REFERRAL_ATTRIBUTION_003.

#### PARTNER_API_COMMISSIONS_PAYOUTS_009
**Note (BLOCKED):** Referral-link endpoints absent (0 referral paths, 2026-06-30). "Referral-link signup → notification + commission trigger" needs the referral path.

#### PARTNER_API_COMMISSIONS_PAYOUTS_010
**Note (BLOCKED):** POST /v1/sa/commissions/{id}/clawback exists, but a clawback needs an existing commission (deferred win pipeline) + 12-month timing control.

#### PARTNER_API_COMMISSIONS_PAYOUTS_011
**Note (BLOCKED):** Needs a reseller commission record + a churn event (both downstream/unavailable) to assert "reseller churn → NO clawback".

#### PARTNER_API_COMMISSIONS_PAYOUTS_012
**Note (BLOCKED):** Waiver SLA/decision + ledger-credit endpoint absent (no waiver path, 2026-06-30). Pairs with _004/_005.

#### PARTNER_API_COMMISSIONS_PAYOUTS_013
**Note (BLOCKED):** SPIFF programme POST /internal/commission/spiff absent from the spec (0 spiff paths, 2026-06-30).

#### PARTNER_API_COMMISSIONS_PAYOUTS_014
**Note (BLOCKED):** POST /v1/sa/rate-table exists (the update), but "Redis cached rates invalidated" is an internal side-effect with no API to observe. Re-scope to "update persists + reflected on next read" (overlaps _006), or keep blocked for the literal cache-invalidation assertion.

#### PARTNER_API_COMMISSIONS_PAYOUTS_015
**Note (BLOCKED):** "Pack vs channel partner ledgers stay separate" needs existing commissions for both partner types (deferred win pipeline). The list endpoint exists; the data doesn't.

#### PARTNER_API_COMMISSIONS_PAYOUTS_016
**Note (BLOCKED):** "Payout banking details encrypted at rest" (CSFLE) is an internal storage property with no API to confirm; no payout/banking endpoint in the commissions area (banking lives on partner.payoutAccounts). Verify via DB/infra review, not API.

#### PARTNER_API_COMMISSIONS_PAYOUTS_017
**Test Description:** Negative counterpart of _002 (commission ledger): invalid filter/pagination is rejected with the correct code (never 5xx). All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/commissions with the param under test)
1. Bad status enum ('bogus') → **400** 'status must be one of'.
2. Malformed partnerId ('not-an-id') → **400** 'partnerId must be a mongodb id'.
3. page=0 → **400** 'skip must be a non-negative integer'.
4. page=-1 → **400** 'skip must be a non-negative integer'.
5. limit over max (999999) → **400** 'limit must not exceed 100'.
6. limit=0 → **200** (leniently defaulted — observed, never 5xx).
**Expected (overall):** Validated invalid filter/pagination → 400; limit=0 defaults gracefully; never 5xx.
**Note:** PASSED. New negative line paired with _002 (read-only GET → no idempotency TC). limit=0 is leniently defaulted (200) — a weak-validation note to confirm with BE.

#### PARTNER_API_COMMISSIONS_PAYOUTS_018
**Test Description:** Negative counterpart of _006 (rate upsert): invalid input is rejected with 400 + a field-level message BEFORE any write (no combo created/mutated). All cases run (failures collected).
**Test Steps:** (each case = one POST /v1/sa/rate-table with the field under test broken)
1. Invalid tier enum ('platinum') → **400** 'tier must be one of'.
2. Invalid dealType enum ('wholesale') → **400** 'dealType must be one of'.
3. Invalid commissionType enum ('bogus') → **400** 'commissionType must be one of'.
4. Missing tier → **400** 'tier must be one of'.
5. Missing dealType → **400** 'dealType must be one of'.
6. Missing commissionType → **400** 'commissionType must be one of'.
7. Missing rate → **400** message mentions "rate must".
8. Negative rate (-0.1) → **400** 'rate must not be less than 0'.
9. Rate over 1 (1.5) → **400** 'rate must not be greater than 1'.
10. Non-numeric rate ('abc') → **400** 'rate must be a number'.
**Expected (overall):** Every invalid rate upsert is rejected with 400 and nothing is persisted (rate must be 0..1). No teardown needed (no write).
**Note:** PASSED. New negative line paired with _006.
### API · PARTNER_ACCOUNT_MANAGEMENT

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001
**Test Description:** Read-only contract check on GET /v1/sa/partners: returns 200 with the envelope (statusCode/data/total/message) and honours pagination.
**Setup (precondition):** authenticated SA client; request the first page with limit=5.
**Test Steps:**
1. GET /v1/sa/partners?page=1&limit=5.
   → Expected: request sent (HTTP 200 asserted in the client).
2. Verify the partner-list API contract.
   → Expected: statusCode 200; `data` is a list; `total` ≥ 0; `message` present; returned page size ≤ requested limit (5).
3. Verify data integrity + SA filtering (data-dependent).
   → Expected: each partner is a non-empty object with a unique id; WARN-skips if staging has 0 partners.
4. Verify SA isolation / no cross-partner leakage.
   → Expected: SA-scoped directory only; WARN-skips when no data (deep cross-partner audit applies once multi-partner data exists).
**Expected (overall):** Partner list returns a valid paginated envelope, SA-scoped.
**Note:** PASSED. Steps 3–4 are data-dependent (staging often has 0 seeded partners → WARN-skip); negative pagination counterpart is _011.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002
**Test Description:** CRUD create on POST /v1/sa/partners with required name/email/type.
**Setup (precondition):** build a unique partner payload (name/email/type='channel'); cleanup (DELETE) is registered right after creation.
**Test Steps:**
1. POST /v1/sa/partners (create the partner).
   → Expected: request sent.
2. Verify the create-partner contract (accepted + persisted).
   → Expected: HTTP 201 (envelope statusCode 200); success message; server-assigned _id and a generated `code` (PAR-xxxxxx).
3. Verify the created record matches the request.
   → Expected: stored name/email/type == sent (no silent mutation).
4. Verify the new partner starts in 'pending' status.
   → Expected: status == 'pending' (awaits SA activation).
5. Verify the partner is retrievable (GET /v1/sa/partners/{id}).
   → Expected: same partner returned, still 'pending'.
**Teardown:** delete the created partner.
**Expected (overall):** Pending partner created, persisted, retrievable.
**Note:** PASSED. Negative (invalid fields) counterpart is _012; duplicate (same email) is _021.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003
**Test Description:** State transition on POST /v1/sa/partners/{id}/approve: pending -> active with approval event.
**Setup (precondition):** SA creates a PENDING partner (assert it starts 'pending').
**Test Steps:**
1. POST /v1/sa/partners/{id}/approve.
   → Expected: request sent.
2. Verify the approve call is accepted.
   → Expected: HTTP 201 (envelope statusCode 200); success message; acts on the same partner id.
3. Verify status flipped to 'active' and the approval event is recorded.
   → Expected: status 'active'; approvedAt set; approvedBy present.
4. Verify the active status persisted (GET /v1/sa/partners/{id}).
   → Expected: fetched partner status 'active'.
**Teardown:** delete the partner.
**Expected (overall):** Pending partner approved to active with approval metadata; downstream activation-user is event-driven (out of scope). Negative/illegal-state counterpart is _013.
**Note:** PASSED.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004
**Test Description:** Decline/suspend a partner via POST /v1/sa/partners/{id}/deactivate (the only partner action carrying a reason); reason is mandatory and audit-logged.
**Setup (precondition):** SA creates a PENDING partner; build a unique decline reason (findable in the audit log).
**Test Steps:**
1. Decline the partner WITH a reason.
   → Expected: accepted; status leaves pending/active (→ 'suspended').
2. Verify the decline reason is recorded in the audit log (GET /v1/sa/audit-logs, retry up to 3× for eventual consistency).
   → Expected: an audit entry contains the unique reason.
3. Enforce mandatory reason: decline three fresh partners with an absent / empty / whitespace-only reason.
   → Expected: each rejected with 400/422 (reason mandatory + non-empty).
**Teardown:** delete the created partners.
**Expected (overall):** Decline works, the reason is audit-logged, and a mandatory non-empty reason is enforced.
**Note:** PASSED. The plan calls this "PATCH decline"; BE exposes no dedicated decline endpoint, so POST /deactivate (carries the reason) is exercised. BE enforces the mandatory non-empty reason (was a known gap, fixed by BE). Negative-id counterpart is _014.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005
**Test Description:** Tier change on POST /v1/sa/partners/{id}/upgrade-tier updates the stored tier AND emits a partner.tier.changed event (before/after) — the portal/analytics refresh signal. Covers both upgrade and downgrade.
**Setup (precondition):** SA creates a partner (assert tier defaults to 'registered').
**Test Steps:**
1. Upgrade through all tiers: registered→select→advanced→premier (three upgrade-tier calls, each with a reason).
   → Expected: each HTTP 200; stored tier becomes select, then advanced, then premier.
2. Verify the upgrade event is recorded with before/after + reason.
   → Expected: a partner.tier.changed event for advanced→premier (before='advanced', after='premier') carrying the change reason.
3. Downgrade premier→select emits an event.
   → Expected: HTTP 200, tier 'select'; a partner.tier.changed event records before='premier', after='select'.
4. Verify the final tier persisted (GET /v1/sa/partners/{id}).
   → Expected: fetched tier == 'select'.
**Teardown:** delete the partner.
**Expected (overall):** Tier changes (up and down) update the stored tier and publish a before/after event; portal/analytics refresh is a downstream consumer (out of scope).
**Note:** PASSED. Negative (invalid tier / same tier / bad id) counterpart is _015.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_006
**Test Description:** Reseller sell-price enforcement / data-minimization: a reseller sets its own price to the end client, and BlazeUp must NOT store that price. Registering a reseller deal with end-client pricing fields must not persist them.
**Setup (precondition):** SA creates a partner; pick a plan; build a RESELLER deal payload that injects end-client pricing fields (endClientPrice, sellPrice, resellerMarginCents — none defined on CreateDealDto).
**Test Steps:**
1. Register the reseller deal (with the end-client pricing fields).
   → Expected: accepted (HTTP 201, envelope statusCode 200) + server-assigned id; dealType == 'reseller'. The BE accepts + strips (does not reject).
2. Verify the create response stores NONE of the end-client-price fields.
   → Expected: endClientPrice / sellPrice / resellerMarginCents absent from the stored deal.
3. Verify a follow-up GET confirms the end-client price is not stored.
   → Expected: GET /v1/sa/deals/{id} returns none of those fields.
**Teardown:** delete the parent partner.
**Expected (overall):** The reseller's end-client price is not persisted (enforced / data-minimized) — the requirement is precisely that BlazeUp does NOT store it.
**Note:** PASSED. Confirmed the requirement "end-client price is not stored": CreateDealDto has no such field and the BE strips the unknown fields on register (accepts 201, drops them). Same enforcement mechanism as SECURITY_COMPLIANCE_002 (unknown fields stripped). This is the REGISTER-path check; the UPDATE/PATCH-path counterpart is the negative _016. Happy-path reseller register is DEAL_REGISTRATION_PIPELINE_002; idempotency N/A (duplicate register is _022).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_007
**Note (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] This is a scheduled background JOB (quarterly tier recalculation), not an API endpoint. No manual-trigger endpoint exists in any service to invoke it on demand, so it cannot be exercised via API automation. Belongs to BE unit/integration tests (or needs a QA-only trigger endpoint). Note: manual tier change IS covered by _005 (POST /upgrade-tier); this TC is specifically the automated quarterly job. Confirm with BE whether a trigger endpoint can be exposed.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_008
**Note (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Depends on the quarterly tier-calculation job (_007): the "downgrade grace quarter" rule (partner keeps current-tier benefits during the grace period) is applied by that scheduled job, not a callable endpoint. No API to set the clock/quarter or trigger the grace evaluation → not API-automatable. BE unit/integration test territory. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_009
**Note (BLOCKED):** [BLOCKED — NO API 2026-06-17] No endpoint or field for PSM (Partner Success Manager) allocation or ARR thresholds in any of the 11 service specs (only unrelated carryForwardPolicy in setting-api). The "$1.5M ARR → dedicated PSM" rule is a calculation not exposed via API → not automatable now. Confirm with product/BE where this logic lives (likely a job/internal calc).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010
**Test Description:** Grant a certification (POST /v1/sa/partner-users/{userId}/certifications) = certification earned; emits partner.certification.granted.
**Setup (precondition):** SA creates a partner + invites a portal user (capture userId).
**Test Steps:**
1. Grant the certification (sales_certified, score=95) — certification earned.
   → Expected: HTTP 200 (envelope statusCode 200); status 'active'; earnedAt + expiresAt set; certificationType echoed.
2. Verify the cert appears in the partner's certification list (GET /v1/sa/partners/{partnerId}/certifications).
   → Expected: the granted cert appears and belongs to the invited user.
3. Verify a 'partner.certification.granted' event is recorded (GET /v1/sa/audit-logs, retry up to 3×).
   → Expected: an event records the cert type for that user.
**Teardown:** delete the parent partner.
**Expected (overall):** Certification earned, listed, and event published; tier re-evaluation is downstream (out of scope).
**Note:** PASSED. Negative (invalid input) counterpart is _020; re-grant duplicate is _022.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011
**Test Description:** Negative counterpart of _001 (GET list): invalid pagination is validated by the BE and rejected with 4xx (never 5xx). All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/partners with invalid pagination)
1. page=0 → **4xx** (rejected), never 5xx.
2. page=-1 → **4xx** (rejected), never 5xx.
3. limit=-5 → **4xx** (rejected), never 5xx.
4. limit=999999 (over max) → **4xx** (rejected), never 5xx.
5. page=abc (non-numeric) → **4xx** (rejected), never 5xx.
**Expected (overall):** Every invalid pagination param is rejected with 4xx and never crashes the endpoint (5xx).
**Note:** PASSED. BE returns 400 for all (page=0/-1 was previously an HTTP 500 crash — fixed by BE). Tightened from "never-5xx only" to assert 4xx now that BE validates.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012
**Test Description:** Negative counterpart of _002 (create): every invalid/incomplete payload is rejected with 400 + a field-level error naming the offending field, and creates NO record. All cases run (failures collected).
**Test Steps:** (each case = one POST /v1/sa/partners with the field under test broken)
1. Missing name → **400**, error mentions "name", no record.
2. Missing email → **400**, error mentions "email", no record.
3. Missing type → **400**, error mentions "type", no record.
4. Malformed email ('not-an-email') → **400**, error mentions "email", no record.
5. Empty name ('') → **400**, error mentions "name", no record.
6. Invalid type enum ('foobar') → **400**, error mentions "type", no record.
**Expected (overall):** Every invalid create payload is rejected with 400, a field-level message, and no record persisted.
**Note:** PASSED.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013
**Test Description:** Negative counterpart of _003 (approve): three illegal approve targets, each rejected with its own code + a clear message. All cases run (failures collected).
**Setup (precondition):** SA creates + approves a partner so it is already 'active' (target for the illegal-transition case).
**Test Steps:** (each case = one POST /v1/sa/partners/{id}/approve)
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Already-active partner (illegal transition) → **400** 'cannot be approved' (409 Conflict would be more precise, but 400 is accepted).
**Teardown:** delete the partner.
**Expected (overall):** Non-existent id → 404; malformed id → 400; illegal transition → 400/409. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent partner id returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Cases 2 & 3 are correct. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014
**Test Description:** Negative counterpart of _004 (deactivate): invalid id rejected with the correct code; a repeat deactivate is idempotent. All invalid-id cases run (failures collected).
**Test Steps:** (cases 1–2 = POST /v1/sa/partners/{id}/deactivate on a bad id)
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Idempotency: create a partner, deactivate it, then deactivate again.
   → Expected: never 5xx; stays 'suspended' (idempotent no-op, currently 201).
**Teardown:** delete the created partners.
**Expected (overall):** Non-existent id → 404; malformed id → 400; repeat deactivate is an idempotent no-op (never 5xx).
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent partner id returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Case 2 and the idempotency observation are correct. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015
**Test Description:** Negative counterpart of _005 (tier change): six invalid inputs, each rejected with its own code + a clear message (no event emitted). All cases run (failures collected).
**Setup (precondition):** SA creates a partner (tier 'registered') as the valid-id target.
**Test Steps:** (each case = one POST /v1/sa/partners/{id}/upgrade-tier)
1. Invalid tier enum ('silver') → **400** 'tier must be one of'.
2. Empty tier ('') → **400** 'tier must be one of'.
3. Missing tier (no field) → **400** 'tier must be one of'.
4. Same tier (already at 'registered') → **400** 'already at tier'.
5. Malformed id ('not-an-id') → **400** 'invalid id'.
6. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
**Teardown:** delete the partner.
**Expected (overall):** Validation / same-tier / malformed → 400; non-existent id → 404. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 6): a well-formed non-existent partner id returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Cases 1–5 are correct. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_016
**Test Description:** Negative counterpart of _006 (same enforcement — BlazeUp does not store the reseller's end-client price) via the UPDATE/PATCH entry point: the end-client price cannot be SET on an open reseller deal.
**Setup (precondition):** SA creates a partner; pick a plan; register a RESELLER deal (open / editable).
**Test Steps:**
1. Update the deal with a valid editable field (notes) + end-client price fields (PATCH /v1/sa/deals/{id}).
   → Expected: HTTP 200; the valid field (notes) is applied; endClientPrice/sellPrice/resellerMarginCents are stripped (not persisted).
2. Update with ONLY end-client price fields (no editable field).
   → Expected: HTTP 400 "No editable fields provided" — the end-client price is not a recognized editable field.
3. Verify via GET.
   → Expected: the notes update persisted; no end-client price fields stored.
**Teardown:** delete the parent partner.
**Expected (overall):** The reseller's end-client price cannot be set via update — stripped when mixed with a valid field, rejected (400) when sent alone. Never persisted.
**Note:** PASSED. Negative/update-path counterpart of _006 (register path). UpdateDealDto's editable whitelist (dealType/prospectEmail/prospectPhone/estimatedAcvCents/planId/expectedCloseDate/notes/wonTenantId) has no end-client price field, so it is stripped or the update is rejected.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_017
**Note (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] This is a scheduled background JOB (quarterly tier recalculation), not an API endpoint. No manual-trigger endpoint exists in any service to invoke it on demand, so it cannot be exercised via API automation. Belongs to BE unit/integration tests (or needs a QA-only trigger endpoint). Note: manual tier change IS covered by _005 (POST /upgrade-tier); this TC is specifically the automated quarterly job. Confirm with BE whether a trigger endpoint can be exposed.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_018
**Note (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Depends on the quarterly tier-calculation job (_007): the "downgrade grace quarter" rule (partner keeps current-tier benefits during the grace period) is applied by that scheduled job, not a callable endpoint. No API to set the clock/quarter or trigger the grace evaluation → not API-automatable. BE unit/integration test territory. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_019
**Note (BLOCKED):** [BLOCKED — NO API 2026-06-17] No endpoint or field for PSM (Partner Success Manager) allocation or ARR thresholds in any of the 11 service specs (only unrelated carryForwardPolicy in setting-api). The "$1.5M ARR → dedicated PSM" rule is a calculation not exposed via API → not automatable now. Confirm with product/BE where this logic lives (likely a job/internal calc).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020
**Test Description:** Negative counterpart of _010 (grant certification): four invalid inputs, each rejected with its own code + a clear message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner + invites a portal user (capture the valid userId).
**Test Steps:** (each case = one POST /v1/sa/partner-users/{userId}/certifications)
1. Invalid cert type ('ninja') → **400** 'certificationType must be one of'.
2. Missing cert type → **400** 'certificationType must be one of'.
3. Malformed userId ('not-an-id') → **400** 'invalid id'.
4. Ghost userId (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400 ("User 000… not found").
**Teardown:** delete the parent partner.
**Expected (overall):** Validation / malformed → 400; non-existent userId → 404. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 4): a well-formed non-existent userId returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Cases 1–3 are correct. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_021
**Test Description:** Idempotency/duplicate counterpart of _002 (create): creating a partner with the same email twice is rejected (no second account).
**Setup (precondition):** SA creates a partner with a unique email (the payload is reused for the duplicate attempt).
**Test Steps:**
1. Re-create with the SAME email → 400 duplicate.
   → Expected: HTTP 400, message contains "already exists".
2. Verify no second account was created (inspect the rejected response body).
   → Expected: no new partner id (or same id) — no duplicate account.
**Teardown:** delete the created partner.
**Expected (overall):** Same-email duplicate is a hard 400 reject; no duplicate partner account.
**Note:** PASSED.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_022
**Test Description:** Idempotency/duplicate counterpart of _010 (certification earned): re-granting the same certification type to the same user must not create a duplicate (renew or 409).
**Setup (precondition):** SA creates a partner + invites a portal user (capture userId).
**Test Steps:**
1. Grant 'sales_certified' (first time).
   → Expected: cert 'active'.
2. Re-grant the SAME certification type.
   → Expected: a defined outcome — renew (2xx) or reject (409).
3. Verify the user does NOT end up with a duplicate active cert (list the partner's certifications).
   → Expected: exactly 1 'sales_certified' cert. **Currently FAILS** — the list shows 2.
**Teardown:** delete the parent partner.
**Expected (overall):** Re-grant must not duplicate an active cert of the same type.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker BUG-001). Gap: re-grant returns 201 and creates a SECOND active cert (list shows 2). BE should renew or reject (409). Confirm with BE.

### API · PARTNER_USERS

#### PARTNER_API_PARTNER_USERS_001
**Test Description:** SA lists portal users for a partner: GET /sa-partners-api/v1/sa/partner-users?partnerId= returns the user list with roles.
**Setup (precondition):** SA creates a partner + invites a portal user (capture userId).
**Test Steps:**
1. GET partner-users filtered by partnerId (limit=20).
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}.
2. Verify the invited user appears with role + status, and the list is scoped.
   → Expected: the user is present with role + status + email; every row's partnerId == the requested partner.
3. Verify no sensitive field is leaked.
   → Expected: no password/token/secret/tempPassword key in any list row (invite carries tempPassword; the list must not).
**Teardown:** delete the parent partner.
**Expected (overall):** Partner-scoped user list with roles/status, no credential leak.
**Note:** PASSED. Negative (invalid pagination/filter) counterpart is _011.

#### PARTNER_API_PARTNER_USERS_002
**Test Description:** SA invites a partner-portal user: POST /sa-partners-api/v1/sa/partner-users creates the user with a role.
**Setup (precondition):** SA creates a partner; build an invite payload (partnerId + email + firstName + lastName + role='sales').
**Test Steps:**
1. Invite the portal user.
   → Expected: HTTP 201 (envelope statusCode 200); server-assigned userId.
2. Verify every submitted field is stored (no silent mutation).
   → Expected: partnerId/email/firstName/lastName/role echoed as sent.
3. Verify the user is usable (active + temp credential for hand-off).
   → Expected: status 'active' + a tempPassword issued.
4. Verify the user is retrievable in the partner's list.
   → Expected: the user appears in GET partner-users?partnerId.
**Teardown:** delete the parent partner.
**Expected (overall):** Invite creates a usable partner-portal user with the chosen role.
**Note:** PASSED. TC↔BE: plan says "email sent + PENDING user", but BE creates an ACTIVE user + returns tempPassword (temp-password onboarding) — confirm with BE which model is intended. Negative (invalid fields) counterpart is _012; duplicate (same email) is _013.

#### PARTNER_API_PARTNER_USERS_003
**Test Description:** SA resets a partner-portal user's password: POST /sa-partners-api/v1/sa/partner-users/{userId}/reset-password issues a fresh credential.
**Setup (precondition):** SA creates a partner + invites a user (capture the invite tempPassword as the baseline).
**Test Steps:**
1. Reset the user's password.
   → Expected: HTTP 200; confirm message; response references the same userId.
2. Verify a fresh credential is issued.
   → Expected: a new tempPassword, different from the invite one.
3. Verify reset is repeatable (mutating action, not one-shot).
   → Expected: a second reset also returns 200.
**Teardown:** delete the parent partner.
**Expected (overall):** Reset issues a fresh hand-off credential and is a repeatable mutating action.
**Note:** PASSED. TC↔BE: plan says "reset LINK sent", but BE returns a new tempPassword (temp-password model) — confirm with BE. Idempotency: reset is not a create — repeating it is valid, so no duplicate-create TC. Negative (invalid id) counterpart is _014.

#### PARTNER_API_PARTNER_USERS_011
**Test Description:** Negative counterpart of _001 (list partner-users): invalid pagination/filter handled with the correct code — validated cases 4xx, a ghost filter 200-empty, lenient params default gracefully — never 5xx. All cases run (failures collected).
**Test Steps:** (each = one GET /v1/sa/partner-users with the param under test)
1. page=0 → **400** 'skip must be a non-negative integer'.
2. page=-1 → **400** 'skip must be a non-negative integer'.
3. limit over max (999999) → **400** 'limit must not exceed 100'.
4. Malformed partnerId ('not-an-id') → **400** 'partnerId must be a mongodb id'.
5. Ghost partnerId (well-formed but non-existent, used as a FILTER) → **200** with an empty list (a filter that matches nothing, not a 404).
6. Lenient params (limit=0 / non-numeric page / unknown sort) → **200** (silently defaulted), must still never 5xx.
**Expected (overall):** Validated invalid input → 4xx; a ghost filter → 200-empty; lenient params default gracefully; never 5xx.
**Note:** PASSED. WEAK-VALIDATION note to confirm with BE: unlike the audit-log list (which 400s these), limit=0 / non-numeric page / unknown sort are silently defaulted (200) instead of rejected. (Ghost partnerId here is a query FILTER → 200-empty is correct, distinct from a ghost PATH id → 404.)

#### PARTNER_API_PARTNER_USERS_012
**Test Description:** Negative counterpart of _002 (invite): eight invalid/incomplete payloads, each rejected with 400 + a descriptive message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner (valid baseline invite payload, role='admin').
**Test Steps:** (each case = one POST /v1/sa/partner-users with the field under test broken)
1. Missing email → **400** 'email must be an email'.
2. Missing firstName → **400** message mentions "firstname".
3. Missing lastName → **400** message mentions "lastname".
4. Missing partnerId → **400** 'partnerId must be a mongodb id'.
5. Invalid role enum ('bogus') → **400** 'role must be one of'.
6. Invalid email ('not-an-email') → **400** 'email must be an email'.
7. Ghost partnerId (well-formed but non-existent, sent as a BODY FK) → **400** 'Partner … not found'.
8. Malformed partnerId ('not-an-id') → **400** 'mongodb id'.
**Teardown:** delete the parent partner.
**Expected (overall):** Every invalid invite payload is rejected with 400 + a field/clear message; no user created.
**Note:** PASSED. Case 7 (ghost partnerId) is a BODY foreign-key reference, so 400 is accepted (unlike a ghost PATH id → 404); it is self-proving (endpoint returns "Partner … not found").

#### PARTNER_API_PARTNER_USERS_013
**Test Description:** Idempotency/duplicate counterpart of _002 (invite): inviting the same email twice must not create a duplicate user.
**Setup (precondition):** SA creates a partner + invites a user (email E); the same payload is reused for the re-invite.
**Test Steps:**
1. Re-invite the SAME email E.
   → Expected: a defined outcome — reject (409) OR idempotent (no new user).
2. Verify the partner does NOT end up with a duplicate-email user (list the partner's users).
   → Expected: exactly 1 user for email E.
**Teardown:** delete the parent partner.
**Expected (overall):** Re-invite must not create a duplicate-email user (email is the login identity).
**Note:** PASSED — verified 2026-07-23. BE fixed the duplicate-invite gap: re-inviting the same email no longer creates a second user (list shows exactly 1). Stale `be_gap` marker to be removed from code; Bug_Tracker BUG-004 can be closed.

#### PARTNER_API_PARTNER_USERS_014
**Test Description:** Negative counterpart of _003 (reset password): invalid id is rejected with the correct code (never 5xx). Self-proving; all cases run (failures collected).
**Test Steps:** (each case = one POST /v1/sa/partner-users/{userId}/reset-password)
1. Ghost userId (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400 ("User 000… not found").
2. Malformed userId ('not-an-id') → **400** Bad Request, message "invalid id".
**Expected (overall):** Non-existent userId → 404; malformed userId → 400; never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent userId returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Case 2 is correct. Confirm with BE.
### API · TERRITORIES

#### PARTNER_API_TERRITORIES_001
**Test Description:** SA assigns a territory to a partner: POST /sa-partners-api/v1/sa/territories saves it with effective dates.
**Setup (precondition):** SA creates a partner; build a territory payload (partnerId + label + countries=[US,CA] + exclusivityType='preferred' + effective dates).
**Test Steps:**
1. Assign the territory.
   → Expected: HTTP 201 (envelope statusCode 200/201); server-assigned id; confirm message.
2. Verify every submitted field is stored (incl. effective dates).
   → Expected: partnerId/label/countries/exclusivityType echoed; exclusivityStartDate/EndDate preserved.
3. Verify retrievable via GET by id.
   → Expected: same territory returned.
**Teardown:** delete the territory + the parent partner.
**Expected (overall):** Territory assignment persisted with fields + effective dates, retrievable by id.
**Note:** PASSED. exclusivityType ∈ exclusive/preferred/open; countries are ISO 3166-1 alpha-2. Negative (invalid fields) counterpart is _011; exclusive-conflict is _012.

#### PARTNER_API_TERRITORIES_002
**Test Description:** SA lists territories with filters: GET /sa-partners-api/v1/sa/territories (paginated, scoped, filterable).
**Setup (precondition):** SA creates a partner + assigns one territory (countries=[US], exclusivityType='preferred').
**Test Steps:**
1. GET territories filtered by partnerId (limit=20).
   → Expected: HTTP 200; envelope {statusCode, data[], total} (no message field for this list).
2. Verify the assigned territory appears, scoped, with schema.
   → Expected: present with label/countries/exclusivityType; every row's partnerId == the requested partner.
3. Filter by exclusivityType=preferred.
   → Expected: only 'preferred' rows returned.
**Teardown:** delete the territory + the parent partner.
**Expected (overall):** Partner-scoped territory list, well-formed and filterable.
**Note:** PASSED. Territory list envelope has no `message` field (unlike other lists). Negative (invalid filter/pagination) counterpart is _013.

#### PARTNER_API_TERRITORIES_003
**Test Description:** SA retrieves a single territory by id: GET /sa-partners-api/v1/sa/territories/{id}.
**Setup (precondition):** SA creates a partner + assigns one territory (countries=[US]); capture its id.
**Test Steps:**
1. GET the territory by id.
   → Expected: HTTP 200; id matches; partnerId/label/countries/exclusivityType present.
**Teardown:** delete the territory + the parent partner.
**Expected (overall):** Get-by-id returns the full territory.
**Note:** PASSED. Negative (invalid id) counterpart is _014.

#### PARTNER_API_TERRITORIES_004
**Test Description:** SA removes a territory assignment: DELETE /sa-partners-api/v1/sa/territories/{id}.
**Setup (precondition):** SA creates a partner + assigns one territory (countries=[US]); capture its id.
**Test Steps:**
1. Delete the territory.
   → Expected: HTTP 200/204 (delete succeeds).
2. Verify the territory is no longer retrievable (GET by id).
   → Expected: GET returns 4xx not-found.
**Teardown:** delete the parent partner.
**Expected (overall):** Delete removes the territory; it is no longer retrievable.
**Note:** PASSED. Negative (invalid/already-removed) counterpart is _015.

#### PARTNER_API_TERRITORIES_011
**Test Description:** Negative counterpart of _001 (assign): eight invalid/incomplete payloads, each rejected with 400 + a descriptive message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner (valid baseline territory payload).
**Test Steps:** (each case = one POST /v1/sa/territories with the field under test broken)
1. Missing partnerId → **400** 'partnerId must be a mongodb id'.
2. Missing label → **400** message mentions "label".
3. Missing countries → **400** message mentions "countries".
4. Invalid exclusivityType ('bogus') → **400** 'exclusivityType must be one of'.
5. Invalid country code ('ZZ') → **400** message mentions "iso31661".
6. Bad start date ('31-12-2026') → **400** 'iso 8601'.
7. Ghost partnerId (well-formed but non-existent, sent as a BODY FK) → **400** 'Partner … not found'.
8. Malformed partnerId ('not-an-id') → **400** 'mongodb id'.
**Teardown:** delete the parent partner.
**Expected (overall):** Every invalid assign is rejected with 400 + a field/clear message; no territory created.
**Note:** PASSED. Case 7 (ghost partnerId) is a BODY foreign-key reference, so 400 is accepted (unlike a ghost PATH id → 404); self-proving.

#### PARTNER_API_TERRITORIES_012
**Test Description:** Exclusive territory conflict (duplicate/conflict counterpart of _001): a 2nd partner cannot take a country already held exclusively.
**Setup (precondition):** SA creates two partners (p1, p2); pick an uncommon country code (IS) to minimise collisions.
**Test Steps:**
1. Partner 1 takes an EXCLUSIVE territory on the country.
   → Expected: HTTP 201, territory created (country was free).
2. Partner 2 assigns an EXCLUSIVE territory on the SAME country.
   → Expected: 4xx; message contains "exclusive" + "conflict".
3. Verify no territory was created for partner 2 (inspect the rejected response).
   → Expected: no territory id in the body.
**Teardown:** delete the territory + both partners.
**Expected (overall):** Cross-partner exclusive overlap is rejected; same-partner overlap is allowed by design.
**Note:** PASSED. BE enforces exclusive cross-partner conflict.

#### PARTNER_API_TERRITORIES_013
**Test Description:** Negative counterpart of _002 (list): five invalid filter/pagination inputs, each rejected with 400 + a clear message (this endpoint validates strictly — no lenient defaulting; never 5xx). All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/territories with an invalid query)
1. Bad exclusivityType ('bogus') → **400** 'exclusivityType must be one of'.
2. Bad country ('ZZ') → **400** message mentions "iso31661".
3. limit over max (999999) → **400** 'must not exceed'.
4. page=0 → **400** 'non-negative'.
5. Malformed partnerId ('not-an-id') → **400** 'mongodb id'.
**Expected (overall):** Every invalid filter/pagination rejected with 400; never 5xx.
**Note:** PASSED. This endpoint validates strictly (no lenient defaulting, unlike partner-users list _011).

#### PARTNER_API_TERRITORIES_014
**Test Description:** Negative counterpart of _003 (get by id): invalid id rejected with the correct code (never 5xx). Self-proving; all cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/territories/{id})
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400 ("Territory 000… not found").
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Expected (overall):** Non-existent id → 404; malformed id → 400; never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent id returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Case 2 is correct. Confirm with BE.

#### PARTNER_API_TERRITORIES_015
**Test Description:** Negative counterpart of _004 (delete): invalid/already-removed rejected with the correct code. All cases run (failures collected).
**Setup (precondition):** SA creates a partner + assigns one territory (target for the already-removed case).
**Test Steps:** (each case = one DELETE /v1/sa/territories/{id})
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Already-removed territory (delete it, then delete again) → expected **404** Not Found (target no longer exists). **Currently FAILS** — BE returns 400 ("Territory … not found").
**Teardown:** delete the parent partner.
**Expected (overall):** Non-existent / already-removed target → 404; malformed id → 400. (Already-removed documents delete's repeat behavior; mutating action, not a duplicate-create.)
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (cases 1 & 3): a not-found target returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Case 2 (malformed) is correct. Confirm with BE.
### API · CERTIFICATIONS_SA

#### PARTNER_API_CERTIFICATIONS_SA_001
**Note (CROSS-REF):** Grant a certification is already covered by PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010 (certification earned: granted + listed + event + tier re-evaluation), with _020 (grant invalid input) and _022 (re-grant idempotency, fail-by-design). Not re-implemented here to avoid a duplicate test. If a standalone CERTIFICATIONS_SA_001 is required, point it at the same POST /v1/sa/partner-users/{userId}/certifications endpoint.

#### PARTNER_API_CERTIFICATIONS_SA_002
**Test Description:** SA revokes a partner certification: DELETE /sa-partners-api/v1/sa/partner-users/{userId}/certifications/{type} (body reason) soft-revokes it.
**Setup (precondition):** SA creates a partner + invites a user + grants an active sales_certified cert.
**Test Steps:**
1. Revoke the certification (with a reason).
   → Expected: HTTP 200; confirm message; status='revoked'.
2. Verify the cert shows as revoked in the partner's cert list (soft-revoke).
   → Expected: the cert record remains with status='revoked' (not hard-removed).
**Teardown:** delete the parent partner.
**Expected (overall):** Revoke soft-removes the cert (status='revoked'), kept in the list.
**Note:** PASSED. TC↔BE: plan says "certification removed", BE soft-revokes (status='revoked', record kept) — confirm BE. Negative (invalid input/state) counterpart is _012.

#### PARTNER_API_CERTIFICATIONS_SA_003
**Test Description:** SA lists a partner team's certifications: GET /sa-partners-api/v1/sa/partners/{partnerId}/certifications.
**Setup (precondition):** SA creates a partner + invites a user + grants a sales_certified cert.
**Test Steps:**
1. GET partner certifications (limit=20).
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}.
2. Verify the granted cert appears with schema, scoped to the partner.
   → Expected: cert present with certificationType/status/userId/earnedAt/expiresAt; every row's partnerId == the requested partner.
3. Filter by status=active.
   → Expected: only active certs returned.
**Teardown:** delete the parent partner.
**Expected (overall):** Partner-scoped cert list, well-formed and filterable.
**Note:** PASSED. Filters: status ∈ active/expired/revoked; certificationType enum; expiringWithinDays. Negative (invalid filter/pagination) counterpart is _013.

#### PARTNER_API_CERTIFICATIONS_SA_004
**Test Description:** SA lists certifications expiring soon: GET /sa-partners-api/v1/sa/certifications?expiringWithinDays=N.
**Test Steps:**
1. GET /sa/certifications?expiringWithinDays=30.
   → Expected: HTTP 200; envelope {statusCode, data[], total, message}; every returned cert expires within 30 days (an empty result is acceptable — WARN-skip).
2. expiringWithinDays max boundary (365) is accepted.
   → Expected: HTTP 200.
**Expected (overall):** Expiring-cert list returns a well-formed envelope; the expiringWithinDays window is bounded 1..365.
**Note:** PASSED. Confirm BE: the SA-wide list returns total=0 even when active certs exist (visible via the per-partner list _003) — possible scoping/index difference; the filter semantic is asserted on whatever is returned, the empty case is WARN-skipped. Negative (invalid filter/pagination) counterpart is _014.

#### PARTNER_API_CERTIFICATIONS_SA_012
**Test Description:** Negative counterpart of _002 (revoke): five invalid input/state cases, each rejected with its own code + a clear message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner + invites a user + grants an active sales_certified cert.
**Test Steps:** (each case = one DELETE /v1/sa/partner-users/{userId}/certifications/{type})
1. Missing reason → **400** 'reason should not be empty'.
2. Cert not held ('hr_specialist', valid user without it) → expected **404** Not Found ('Active … not found'). **Currently FAILS** — BE returns 400.
3. Ghost userId (well-formed but non-existent) → expected **404** Not Found ('User … not found'). **Currently FAILS** — BE returns 400.
4. Malformed userId ('not-an-id') → **400** 'invalid id'.
5. Already-revoked cert (revoke, then revoke again) → expected **404** Not Found (no active cert). **Currently FAILS** — BE returns 400.
**Teardown:** delete the parent partner.
**Expected (overall):** Missing reason / malformed id → 400; every not-found target → 404. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (cases 2, 3, 5): a not-found target returns **400** ("not found") instead of **404** — same root cause as the deals get-by-id gap. Cases 1 & 4 are correct. Confirm with BE.

#### PARTNER_API_CERTIFICATIONS_SA_013
**Test Description:** Negative counterpart of _003 (list certs by partner): invalid filter/pagination handled with the correct code — validated cases 4xx, a ghost partner scope 200-empty — never 5xx. All cases run (failures collected).
**Setup (precondition):** SA creates a partner (baseline).
**Test Steps:** (each = one GET /v1/sa/partners/{partnerId}/certifications with the param under test)
1. Bad status enum ('bogus') → **400** 'status must be one of'.
2. Bad certificationType enum ('bogus') → **400** 'certificationType must be one of'.
3. limit over max (999999) → **400** 'must not exceed 100'.
4. Malformed partnerId ('not-an-id') → **400** 'invalid id'.
5. Ghost partnerId (well-formed but non-existent, used as the list SCOPE) → **200** with an empty list (a scope that matches nothing, not a 404).
6. page=0 → **400** 'non-negative' (rejected; never 5xx).
**Expected (overall):** Validated invalid filter/pagination → 4xx; a ghost partner scope → 200-empty; never 5xx.
**Note:** PASSED. Ghost partnerId here is the list SCOPE → 200-empty is accepted (distinct from a ghost PATH id in a get/revoke → 404). page=0 is rejected (400), not lenient.

#### PARTNER_API_CERTIFICATIONS_SA_014
**Test Description:** Negative counterpart of _004 (SA cert list): seven invalid filter/pagination inputs, each rejected with 400 + a clear message (never 5xx). All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/certifications with an invalid query)
1. Bad status enum ('bogus') → **400** 'status must be one of'.
2. Bad certificationType enum ('bogus') → **400** 'certificationType must be one of'.
3. expiringWithinDays = 0 → **400** 'must not be less than 1'.
4. expiringWithinDays negative → **400** 'must not be less than 1'.
5. expiringWithinDays > 365 (366) → **400** 'must not be greater than 365'.
6. limit over max (999999) → **400** 'limit must not exceed 100'.
7. page=0 → **400** 'non-negative'.
**Expected (overall):** Every invalid filter/pagination rejected with 400; never 5xx. expiringWithinDays bounded 1..365.
**Note:** PASSED.
### API · TEAM_REFERRAL_LINKS

#### PARTNER_API_TEAM_REFERRAL_LINKS_001
**Note (BLOCKED):** Referral endpoints absent from the deployed spec (confirmed 2026-06-30: 0 referral paths). GET /v1/partner/referral-links not implemented. Unblock when BE ships the referral-links API.

#### PARTNER_API_TEAM_REFERRAL_LINKS_002
**Note (BLOCKED):** Referral endpoints absent (0 referral paths, 2026-06-30). POST /v1/partner/referral-links (create campaign tracking link) not implemented.

### API · RESOURCES_SANDBOX

#### PARTNER_API_RESOURCES_SANDBOX_001
**Note (BLOCKED):** Sandbox endpoints absent from the deployed spec (confirmed 2026-06-30: 0 sandbox paths). No API to request a sandbox reset / apply a profile. Unblock when BE ships the sandbox module.

#### PARTNER_API_RESOURCES_SANDBOX_002
**Note (BLOCKED):** Sandbox endpoints absent (0 sandbox paths, 2026-06-30); also a scheduled CRON (weekly auto-reset, default off). No API to trigger/observe. Unblock when BE ships sandbox + a job trigger.

#### PARTNER_API_RESOURCES_SANDBOX_003
**Note (BLOCKED):** Sandbox endpoints absent (0 sandbox paths, 2026-06-30). No API to run a profile reseed (SMB/Mid-market/Enterprise) or assert the ≤5-min completion.
### API · DASHBOARD_DATA

#### PARTNER_API_DASHBOARD_DATA_001
**Test Description:** Partner dashboard stats: GET /sa-partners-api/v1/partner/portal/dashboard returns the KPI schema (partner JWT).
**Setup (precondition):** Mint a partner-portal session (SA creates + approves a partner, invites a user, logs in as that user → partner JWT).
**Test Steps:**
1. GET the partner dashboard.
   → Expected: HTTP 200; envelope {statusCode, data{}, message}; `data` is a non-empty object.
2. Verify the KPI schema + no sensitive leak.
   → Expected: `data` has 'partner' (tier/status/openDealsCount), 'deals', 'commissions' sections; no password/token/secret/credential key.
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Partner dashboard returns the well-formed KPI schema with no credential leak.
**Note:** PASSED. PARTNER-PORTAL endpoint (needs a partner JWT, not the SA token; SA token → 401). No invalid-input negative (no params); 401 auth belongs to Auth & Access Control. Idempotency: GET read-only → N/A.
### API · CRM_INTEGRATION

> All BLOCKED — downstream CRM connector (events are consumed by the connectors/CRM service, not reachable from this domain). The API-observable events are covered by DEAL_010 / AUDIT_LOG_*; the CRM-side effects are out of scope here. Unblock when CRM verification is exposed to QA.

#### PARTNER_API_CRM_INTEGRATION_001
**Note (BLOCKED):** "Deal registered → dogfood CRM opportunity created." CRM side not reachable.

#### PARTNER_API_CRM_INTEGRATION_002
**Note (BLOCKED):** "Deal protection extended → CRM opportunity meta updated." CRM side not reachable.

#### PARTNER_API_CRM_INTEGRATION_003
**Note (BLOCKED):** "Deal lost → CRM Close Lost + close reason." CRM side not reachable.

#### PARTNER_API_CRM_INTEGRATION_004
**Note (BLOCKED):** "Deal expired → CRM mark stale + SA task." Depends on the expiry CRON + the CRM connector, neither reachable.

#### PARTNER_API_CRM_INTEGRATION_005
**Note (BLOCKED):** "client.health_alert → CRM task." Depends on the MSP/client-health module (also absent) + the CRM connector.

### API · EVENT_ARCHITECTURE

#### PARTNER_API_EVENT_ARCHITECTURE_001
**Note (BLOCKED):** Kafka envelope/metadata is an internal event-bus property with no API to inspect it directly. Event presence is partially observable via the SA audit log (DEAL_010 / AUDIT_LOG_*), but the literal "Kafka standard envelope" assertion isn't API-verifiable. Re-scope to the audit-log envelope, or verify via BE/infra.
### API · PARTNER_PORTAL

> All partner-portal endpoints need a PARTNER JWT (not the SA token). The session is
> minted self-contained from the SA side via `utils.partner_portal.mint_partner_session`
> (create + approve partner, invite user, partner login). All read endpoints are GET
> (read-only → idempotency N/A). No sa-plans dependency except _002 (deal detail).

#### PARTNER_API_PARTNER_PORTAL_001
**Test Description:** Partner retrieves its own account profile: GET /partner/portal/profile.
**Setup (precondition):** Mint a partner-portal session (partner JWT).
**Test Steps:**
1. GET own profile.
   → Expected: HTTP 200; `data` is the logged-in partner's account (id==own, code/email/tier/status present); no password/token/secret/credential key.
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Own profile returned, no credential leak.
**Note:** PASSED. No params (no input-negative; 401 → Auth feature). GET → idempotency N/A.

#### PARTNER_API_PARTNER_PORTAL_002
**Test Description:** Partner retrieves its own deal by id: GET /partner/portal/deals/{id} — full record.
**Setup (precondition):** Mint a partner-portal session; the partner registers a deal via POST /partner/portal/deals; capture its id.
**Test Steps:**
1. GET the own deal by id.
   → Expected: HTTP 200; the returned id matches; partnerId == the logged-in partner; dealType/prospectName/status present.
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** A partner can read the full record of its own deal.
**Note:** PASSED. Negative (invalid id) counterpart is _012.

#### PARTNER_API_PARTNER_PORTAL_003
**Test Description:** Partner retrieves its own certifications: GET /partner/portal/certifications.
**Setup (precondition):** Mint a partner-portal session; SA grants a sales_certified cert to the partner user.
**Test Steps:**
1. GET own certifications.
   → Expected: HTTP 200; `data` is a non-empty list.
2. Verify the granted cert appears with the right schema.
   → Expected: the granted cert is present with status + earnedAt + expiresAt.
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Own certs listed with the right schema.
**Note:** PASSED. Negative (invalid filter) counterpart is _013.

#### PARTNER_API_PARTNER_PORTAL_004
**Test Description:** Partner retrieves its own commission summary: GET /partner/portal/commissions/summary.
**Setup (precondition):** Mint a partner-portal session.
**Test Steps:**
1. GET own commission summary.
   → Expected: HTTP 200; totalEarnedCents/totalPendingCents/totalPaidCents are non-negative ints (+ clawbackExposureCents).
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Earned/pending/paid totals returned.
**Note:** PASSED. No params (no input-negative); GET → idempotency N/A.

#### PARTNER_API_PARTNER_PORTAL_005
**Test Description:** Partner retrieves its own assigned territories: GET /partner/portal/territories.
**Setup (precondition):** Mint a partner-portal session; SA assigns a territory (countries=[DE]) to the partner.
**Test Steps:**
1. GET own territories.
   → Expected: HTTP 200; `data` is a non-empty list; the assigned territory appears and every row is scoped to the partner (partnerId == own).
**Teardown:** close the portal session; delete the territory + partner.
**Expected (overall):** Own territories returned, scoped.
**Note:** PASSED. No params (no input-negative); GET → idempotency N/A.

#### PARTNER_API_PARTNER_PORTAL_006
**Test Description:** Partner retrieves its own tier commission rates: GET /partner/portal/rates.
**Setup (precondition):** Mint a partner-portal session.
**Test Steps:**
1. GET own commission rates.
   → Expected: HTTP 200; `data` is a well-formed list of tier rates (may be empty for the registered tier — WARN-skip).
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Tier-specific rates returned as a list.
**Note:** PASSED. Rates list is empty for a registered-tier partner on staging (still a well-formed list). No params (no input-negative); GET → idempotency N/A.
#### PARTNER_API_PARTNER_PORTAL_012
**Test Description:** Negative counterpart of _002 (own deal by id): a ghost / malformed deal id is rejected with the correct code. All cases run (failures collected).
**Setup (precondition):** Mint a partner-portal session.
**Test Steps:** (each case = one GET /partner/portal/deals/{id})
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → **404** Not Found, message "not found".
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Non-existent id → 404; malformed id → 400; never 5xx.
**Note:** PASSED. Notable: this partner-portal endpoint correctly returns **404** for a ghost id — unlike the SA-side get-by-id endpoints which return 400 (the systemic gap tracked in Bug_Tracker BUG-006…019). The test pins the correct 404 so a regression would be caught.

#### PARTNER_API_PARTNER_PORTAL_013
**Test Description:** Negative counterpart of _003 (own certs): three invalid filters, each rejected with 400 + a clear message (never 5xx). All cases run (failures collected).
**Setup (precondition):** Mint a partner-portal session.
**Test Steps:** (each case = one GET /partner/portal/certifications with an invalid filter)
1. Bad status enum ('bogus') → **400** 'status must be one of'.
2. Bad certificationType enum ('bogus') → **400** 'certificationType must be one of'.
3. limit over max (999999) → **400** 'must not exceed'.
**Teardown:** close the portal session; delete the partner.
**Expected (overall):** Invalid cert filter rejected with 400; never 5xx.
**Note:** PASSED.

### API · SECURITY_COMPLIANCE

#### PARTNER_API_SECURITY_COMPLIANCE_001
**Test Description:** Every SA action writes a well-formed, correlated audit entry: performing a reason-carrying SA action produces a GET /v1/sa/audit-logs entry that carries actor + action + reasoning + correlationId (+ a resource reference), leaking no sensitive field.
**Setup (precondition):** SA creates a partner (the action target); build a unique tier-change reason.
**Test Steps:**
1. Perform a reason-carrying SA action: change the partner's tier to 'select' with a reason.
   → Expected: HTTP 200; tier == 'select'.
2. Verify the action wrote an audit entry (GET /v1/sa/audit-logs, retry up to 3× for eventual consistency).
   → Expected: an entry whose action mentions "tier" references this partner.
3. Verify the entry carries the governance fields.
   → Expected: actor (with a type, e.g. 'sa-staff'); action (non-empty string); correlationId (a UUID); reasoning captured (after.reason == the supplied reason); resource.id references the acted-on partner; no password/token/secret key.
**Teardown:** delete the parent partner.
**Expected (overall):** An SA action is fully audited — actor, action, reasoning, and a correlation ID — with a resource reference and no sensitive leak.
**Note:** PASSED. Reasoning is captured under `after.reason` for reason-carrying actions (tier change / deactivate / resolve). No invalid-input negative (side-effect verification; audit-log query negatives are AUDIT_LOG_005). Idempotency N/A (side-effect, not a create). Complements DEAL_010 (event published) / ACCOUNT_MANAGEMENT_004 (decline reason audit-logged).

#### PARTNER_API_SECURITY_COMPLIANCE_002
**Test Description:** Prospect data minimization: registering a deal with extra, unnecessary PII (SSN, date of birth, national id, passport — fields the CreateDealDto does not define) must NOT persist them.
**Setup (precondition):** SA creates a partner; pick a plan; build a deal payload that injects unnecessary PII fields (prospectSsn, prospectDateOfBirth, prospectNationalId, prospectPassportNumber).
**Test Steps:**
1. Register the deal (with the unnecessary PII fields).
   → Expected: accepted (HTTP 201, envelope statusCode 200) + server-assigned id — the BE accepts + strips (does not reject).
2. Verify the create response persists NONE of the unnecessary PII fields.
   → Expected: prospectSsn / prospectDateOfBirth / prospectNationalId / prospectPassportNumber absent from the stored deal.
3. Verify a follow-up GET confirms the PII is not stored.
   → Expected: GET /v1/sa/deals/{id} returns none of those fields.
**Teardown:** delete the parent partner.
**Expected (overall):** Unnecessary PII is not persisted (data minimization) — the "not persisted" branch of "rejected or not persisted".
**Note:** PASSED. BE STRIPS unknown fields silently (accepts 201, drops them) rather than rejecting with 400 — both satisfy the requirement; if a stricter policy wants a 400 on unknown fields, confirm with BE. This security check IS the unwanted-input scenario (no separate negative); happy-path register is _001 of DEAL_REGISTRATION_PIPELINE. Idempotency N/A.

#### PARTNER_API_SECURITY_COMPLIANCE_003
**Note (BLOCKED):** Data residency (UAE regional storage) is an infra/region property with no API to confirm where data is stored. Verify via infra/DB review, not API.
### API · AUDIT_LOG

#### PARTNER_API_AUDIT_LOG_001
**Test Description:** SA lists audit log entries: GET /sa-partners-api/v1/sa/audit-logs returns a paginated, filterable, well-formed audit trail.
**Test Steps:**
1. GET audit-logs (page=1, limit=5).
   → Expected: HTTP 200, envelope {statusCode, data[], total, message}.
2. Check pagination.
   → Expected: returned page size ≤ limit.
3. Check each entry's schema + no sensitive leak.
   → Expected: id/action/category/severity/createdAt present with right types; actor/resource are objects; no password/token/secret keys.
4. Filter by category (taken from the first entry).
   → Expected: only entries of that category are returned.
**Expected (overall):** Audit-log list returns a correct, paginated, filterable envelope with well-formed, non-sensitive entries.
**Note:** PASSED — verified 2026-06-25. Read-only (no setup/cleanup, no sa-plans dependency).

#### PARTNER_API_AUDIT_LOG_002
**Test Description:** SA retrieves audit-log KPI stats: GET /sa-partners-api/v1/sa/audit-logs/stats returns 24h counters + chain integrity.
**Test Steps:**
1. GET audit-logs/stats.
   → Expected: HTTP 200, envelope {statusCode, data{}, message}.
2. Check KPI fields + types.
   → Expected: totalEvents24h/criticalEvents24h/warnings24h/uniqueActors24h are non-negative ints; chainIntegrityPct is a 0..100 percentage.
3. Check internal consistency.
   → Expected: critical/warnings/uniqueActors counts never exceed totalEvents24h.
**Expected (overall):** Stats endpoint returns well-typed, internally-consistent 24h KPIs.
**Note:** PASSED — verified 2026-06-25. Read-only, no params (so no invalid-input negative), no sa-plans dependency.

#### PARTNER_API_AUDIT_LOG_003
**Test Description:** SA exports the audit log as JSON or CSV: GET /sa-partners-api/v1/sa/audit-logs/export returns a downloadable file (capped at 10000 rows).
**Test Steps:**
1. Export format=json.
   → Expected: 200, content-type application/json, body is a JSON array; ≤10000 rows; each row has _id/action/category/severity/createdAt.
2. Export format=csv.
   → Expected: 200, content-type text/csv, header row carries audit columns.
3. No format param.
   → Expected: 200, defaults to CSV.
**Expected (overall):** Audit-log export returns a well-formed JSON or CSV file (default CSV), within the 10000-row cap.
**Note:** PASSED — verified 2026-06-25. format enum [csv, json], default csv. No sa-plans dependency.

#### PARTNER_API_AUDIT_LOG_004
**Test Description:** SA retrieves a single audit-log entry by id: GET /sa-partners-api/v1/sa/audit-logs/{id} returns the full entry.
**Test Steps:**
1. List with limit=1 to pick a real entry id.
   → Expected: an entry with an _id (skip if the log is empty).
2. GET audit-logs/{id}.
   → Expected: 200; data._id matches; action/category/severity/createdAt present; actor/resource are objects; no sensitive key.
**Expected (overall):** Get-by-id returns the full, well-formed entry with no sensitive leak.
**Note:** PASSED — verified 2026-06-25. Read-only, no sa-plans dependency.

#### PARTNER_API_AUDIT_LOG_005
**Test Description:** Negative counterpart of _001 (audit-log list): eleven invalid pagination/filter inputs each rejected with 400 (never 5xx), plus a logically-empty-but-valid range handled gracefully. All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/audit-logs with the param under test)
1. page=0 → **400** 'page must not be less than 1'.
2. page=-1 → **400** 'page must not be less than 1'.
3. limit=0 → **400** 'limit must not be less than 1'.
4. limit=-5 → **400** 'limit must not be less than 1'.
5. limit over max (999999) → **400** 'limit must not be greater than 100'.
6. page non-numeric ('abc') → **400** 'page must be an integer'.
7. Invalid severity ('bogus') → **400** 'severity must be one of'.
8. Invalid category ('bogus') → **400** 'category must be one of'.
9. Invalid actorType ('bogus') → **400** 'actorType must be one of'.
10. Bad dateFrom ('31-12-2026') → **400** 'dateFrom must be a valid ISO…'.
11. Bad dateTo ('not-a-date') → **400** 'dateTo must be a valid ISO…'.
12. Empty-but-valid range (dateFrom > dateTo) → handled gracefully (< 500; 200 empty, not an error).
**Expected (overall):** Every invalid pagination/filter → 400 (never 5xx); a valid empty range returns gracefully.
**Note:** PASSED. Enums: severity ∈ info/warning/critical; category ∈ SA_AUDIT_*; actorType ∈ sa-staff/impersonation/…

#### PARTNER_API_AUDIT_LOG_006
**Test Description:** Negative counterpart of _003 (audit-log export): seven invalid format/filter inputs, each rejected with 400 + a clear message (never 5xx). All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/audit-logs/export with the param under test)
1. Bogus format ('bogus') → **400** 'format must be one of'.
2. Invalid severity ('bogus') → **400** 'severity must be one of'.
3. Invalid category ('bogus') → **400** 'category must be one of'.
4. Invalid actorType ('bogus') → **400** 'actorType must be one of'.
5. Invalid retentionClass ('bogus') → **400** 'retentionClass must be one of'.
6. Bad dateFrom ('31-12-2026') → **400** 'dateFrom must be a valid ISO…'.
7. Bad dateTo ('not-a-date') → **400** 'dateTo must be a valid ISO…'.
**Expected (overall):** Every invalid export format/filter is rejected with 400 (never 5xx).
**Note:** PASSED. retentionClass enum ∈ standard/extended/permanent; format enum ∈ csv/json.
#### PARTNER_API_AUDIT_LOG_007
**Test Description:** Negative of _004 (get audit entry by id): invalid id is rejected (4xx, never 5xx).
**Test Steps:**
1. GET audit-logs/{ghost id}.
   → Expected: 404 'Audit log entry ... not found'.
2. GET audit-logs/{malformed id}.
   → Expected: 400 'Invalid id'.
**Expected (overall):** Non-existent id → 404, malformed id → 400; never 5xx.
**Note:** PASSED — verified 2026-06-25. Self-proving (endpoint returns not-found), no setup needed, no sa-plans dependency.

