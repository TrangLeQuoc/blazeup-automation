# Partner Platform — Test Plan (Automation)

> Generated from the test plan. NOT_STARTED test cases show the name only; BLOCKED show the block reason; PASSED/FAILED show full description, steps (with expected per step), overall expected, and notes.

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
**Note:** FAILED (by design / be_gap). Rule-5 cross-entity case. BE returns **400** for cross-partner access, but it should be **404** (preferred, to hide the resource's existence) or **403** — 400 mislabels a valid request as malformed. Test tightened to assert 403/404 + marked `be_gap` until BE fixes. Tenant isolation itself holds (no data leak).

#### PARTNER_API_AUTH_ACCESS_CONTROL_004
**Note (NOT_STARTED):** Admin MFA policy enforcement — needs an MFA enrollment/challenge flow. Not yet automated (assess MFA endpoints: /partner/auth/mfa/*).

#### PARTNER_API_AUTH_ACCESS_CONTROL_005
**Note (NOT_STARTED):** Guard — MSP accesses payroll data is forbidden. MSP/payroll guard; assess whether an API surface exists in this domain before automating.

#### PARTNER_API_AUTH_ACCESS_CONTROL_006
**Note (NOT_STARTED):** Guard — MSP exports employee records is forbidden. As _005.

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
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_007
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

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
**Note (DEFERRED):** Win a deal (POST /v1/sa/deals/{id}/win). The WinDealDto carries a payment card + billing details + tenant provisioning — calling it has heavy side effects (provisions a tenant, may touch billing). Deferred to avoid polluting staging; build with a dedicated teardown / a BE-provided sandbox flag.

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
12. Ghost planId ('no-such-plan-qa', verified absent above) → expected "plan" rejection. **Currently FAILS** — accepted (HTTP 201).
**Teardown:** delete the parent partner (removes any deal accidentally created by the planId gap).
**Expected (overall):** Every invalid register payload is rejected with a clear message and no deal is created; planId should be validated against the catalog.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate). Gap (case 12): a non-existent planId is accepted (201). sa-plans returns 4xx for that id, but the deals endpoint does not validate planId cross-service. Confirm with BE.

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
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Already-approved deal (illegal transition) → **400** 'cannot transition' (409 Conflict would be more precise, but 400 is accepted).
**Teardown:** delete the parent partner.
**Expected (overall):** Non-existent id → 404; malformed id → 400; illegal transition → 400/409. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent id returns **400** ("not found") instead of **404** — same root cause as _031. Cases 2 & 3 are correct. Confirm with BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_029
**Test Description:** Negative counterpart of _009 (resolve-conflict): six invalid inputs, each rejected with its own code + a clear message. All cases run (failures collected).
**Setup (precondition):** SA creates a partner; register a deal (status 'registered', conflictStatus 'none' — a non-flagged target).
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/resolve-conflict)
1. Invalid decision enum ('whatever') → **400** 'decision must be one of'.
2. Missing decision → **400** 'decision must be one of'.
3. Missing reasoning → **400** message mentions "reasoning".
4. Malformed id ('not-an-id') → **400** 'invalid id'.
5. Non-flagged deal (illegal state) → **400** message mentions "flagged" (409 Conflict would be more precise, but 400 is accepted).
6. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
**Teardown:** delete the parent partner.
**Expected (overall):** Validation/format/state errors → 400; non-existent id → 404. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 6): a well-formed non-existent id returns **400** ("not found") instead of **404** — same root cause as _031. Cases 1–5 are correct. Confirm with BE.

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
8. Ghost deal id (valid body, well-formed but non-existent) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
**Expected (overall):** Body-validation / boundary / format / malformed → 400; non-existent id → 404. Never 5xx. Spec constraint: addedDays ∈ 1..180; reasoning required + non-empty.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 8): a well-formed non-existent id returns **400** ("not found") instead of **404** — same root cause as _031. Cases 1–7 are correct. Confirm with BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_031
**Test Description:** Negative counterpart of _020 (get-by-id): two distinct rejection semantics — a malformed id is a bad request (400), a ghost id is a missing resource (404). Self-proving; GET → no idempotency concern. All cases run (failures collected).
**Test Steps:** (each case = one GET /v1/sa/deals/{id}; expected code + message hint, never 5xx)
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message mentions "not found". **Currently FAILS** — BE returns 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message mentions "invalid id".
**Expected (overall):** A malformed id → 400; a well-formed but non-existent id → 404. Never 5xx, no record returned.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent id returns **400** with message "not found" — status contradicts the message; correct REST is **404 Not Found**. The malformed-id case (400) is correct. Confirm with BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_032
**Test Description:** Negative counterpart of _019 (lose): three illegal lose targets, each rejected with its own code + a clear message (never 5xx). All cases run (failures collected).
**Setup (precondition):** SA creates a partner; register a deal (status 'registered', NOT approved — lose requires 'approved').
**Test Steps:** (each case = one POST /v1/sa/deals/{id}/lose)
1. Registered deal (illegal transition — not approved) → **400** 'cannot transition' (409 Conflict would be more precise, but 400 is accepted here).
2. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
3. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
**Teardown:** delete the parent partner.
**Expected (overall):** Illegal transition → 400/409; malformed id → 400; non-existent id → 404. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 2): a well-formed non-existent id returns **400** ("not found") instead of **404** — same root cause as _031. Cases 1 & 3 are correct. Confirm with BE.

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
1. Ghost id (well-formed but non-existent, 000000000000000000000000) → expected **404** Not Found, message "not found". **Currently FAILS** — BE returns 400.
2. Malformed id ('not-an-id') → **400** Bad Request, message "invalid id".
3. Already-rejected deal (illegal transition) → **400** 'cannot transition' (409 Conflict would be more precise, but 400 is accepted).
**Teardown:** delete the parent partner.
**Expected (overall):** Non-existent id → 404; malformed id → 400; illegal transition → 400/409. Never 5xx.
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker). Gap (case 1): a well-formed non-existent id returns **400** ("not found") instead of **404** — same root cause as _031. Cases 2 & 3 are correct. Confirm with BE.

### API · DEAL_COLLABORATION

#### PARTNER_API_DEAL_COLLABORATION_001
**Note (BLOCKED):** No collaboration/notes-thread API. A deal carries only a single flat `notes` string (set at register / via deal update) — there is no comment/activity-thread endpoint to add, list, or attribute collaboration entries. Re-scope with BE: if "collaboration" is just the flat notes field, it is already covered by the register/update TCs; otherwise the endpoints do not exist yet.

#### PARTNER_API_DEAL_COLLABORATION_002
**Note (BLOCKED):** No document/attachment API on deals. No endpoint to upload, list, or download deal documents. Build when BE exposes a deal-documents surface.

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
**Note (redundant):** "Invalid expectedCloseDate → 400" is already covered by DEAL_REGISTRATION_PIPELINE_021 (step 2e). Not blocked; no distinct coverage if built standalone.
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
**Note (NOT_STARTED — buildable now):** GET /v1/partner/portal/commissions (commission ledger/history) exists; can assert list schema + partner scoping (passes even when empty). Next build candidate. Distinct from PARTNER_PORTAL_004 (commissions/summary, PASSED).

#### PARTNER_API_COMMISSIONS_PAYOUTS_003
**Note (BLOCKED, positive):** POST /v1/partner/portal/commissions/{id}/dispute exists, but disputing needs a real commission {id} (deferred win pipeline). The negative (dispute a ghost id → 4xx) is buildable now. Unblock when a commission record can be created.

#### PARTNER_API_COMMISSIONS_PAYOUTS_004
**Note (BLOCKED):** Product-failure waiver POST /v1/partner/commissions/:id/waiver absent from the spec (2026-06-30). Unblock when BE ships the waiver endpoint.

#### PARTNER_API_COMMISSIONS_PAYOUTS_005
**Note (BLOCKED):** Waiver decision / final-outcome event endpoint absent (no waiver path, 2026-06-30). Pairs with _004/_012.

#### PARTNER_API_COMMISSIONS_PAYOUTS_006
**Note (NOT_STARTED — buildable now):** Rate-table endpoint exists as POST /v1/sa/rate-table (TC says PUT /internal/commission/rates — method PUT→POST, path renamed). Can create a new version + assert it persists. The "cached" (Redis invalidation) side is internal/not API-observable (see _014).

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
**Note (BLOCKED):** [BLOCKED — NO API 2026-06-17] Searched OpenAPI specs of all 11 platform services (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 fields for reseller/end-client price (only basePrice/totalPrice in plan/billing, unrelated). No endpoint or field to send/store an end-client price → the data-model this TC describes is not implemented in any current API. Confirm with product/BE: which service owns this, or is it a future PRD feature (§2.2/§7.2/§11)? Not automatable until the model exists.

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
**Note (BLOCKED):** [BLOCKED — NO API 2026-06-17] Searched OpenAPI specs of all 11 platform services (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 fields for reseller/end-client price (only basePrice/totalPrice in plan/billing, unrelated). No endpoint or field to send/store an end-client price → the data-model this TC describes is not implemented in any current API. Confirm with product/BE: which service owns this, or is it a future PRD feature (§2.2/§7.2/§11)? Not automatable until the model exists.

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
   → Expected: exactly 1 user for email E. **Currently FAILS** — the list shows 2.
**Teardown:** delete the parent partner.
**Expected (overall):** Re-invite must not create a duplicate-email user (email is the login identity).
**Note:** FAILED (by design / `be_gap`, excluded from merge gate; tracked in Bug_Tracker BUG-004). Gap: re-invite returns 201 and creates a SECOND user with the same email (list shows 2). BE should reject (409) or be idempotent. Confirm with BE.

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
**Note (NOT_STARTED — buildable):** Audit-log endpoints exist: perform an SA action (approve/deactivate) then GET /v1/sa/audit-logs and assert the entry carries actor + action + reasoning + correlationId. Partially covered by DEAL_010 / ACCOUNT_MANAGEMENT_004; a dedicated envelope-completeness TC is buildable.

#### PARTNER_API_SECURITY_COMPLIANCE_002
**Note (BLOCKED):** No API/rule to assert prospect data-minimization (unnecessary PII rejected / not persisted). No endpoint enforces or exposes a PII-minimization rule to test against. Confirm with BE where this is enforced.

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

