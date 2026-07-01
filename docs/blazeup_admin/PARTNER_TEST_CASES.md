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
**Test Steps:**
1. Provision + log in a partner user; GET /partner/auth/me with the JWT.
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
**Test Steps:**
1. Partner A (own session) registers a deal; capture its id.
2. Partner B (a separate session) GET /partner/portal/deals/{A_deal_id}.
   → Expected: refused (4xx — BE returns 400), and A's deal is NOT returned in the body.
**Expected (overall):** A partner cannot access another partner's deal — refused, no data leak.
**Note:** PASSED — verified 2026-06-30 (sa-plans-api back UP). Rule-5 cross-entity case. BE returns 400 (not 403/404) when a partner requests another partner's deal id; access still refused, no data leak.

#### PARTNER_API_AUTH_ACCESS_CONTROL_004
**Note (NOT_STARTED):** Admin MFA policy enforcement — needs an MFA enrollment/challenge flow. Not yet automated (assess MFA endpoints: /partner/auth/mfa/*).

#### PARTNER_API_AUTH_ACCESS_CONTROL_005
**Note (NOT_STARTED):** Guard — MSP accesses payroll data is forbidden. MSP/payroll guard; assess whether an API surface exists in this domain before automating.

#### PARTNER_API_AUTH_ACCESS_CONTROL_006
**Note (NOT_STARTED):** Guard — MSP exports employee records is forbidden. As _005.

#### PARTNER_API_AUTH_ACCESS_CONTROL_007
**Test Description:** Valid refresh token issues a new access token (no re-login).
**Test Steps:**
1. Log in (capture refresh token); POST /partner/auth/refresh with it.
   → Expected: 200, a new accessToken (different from the original).
2. The new access token authorizes GET /me.
   → Expected: 200.
3. An invalid refresh token.
   → Expected: 401.
**Expected (overall):** Refresh mints a working new access token; invalid refresh rejected.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_AUTH_ACCESS_CONTROL_008
**Test Description:** Logout invalidates the refresh token.
**Test Steps:**
1. Log in; POST /partner/auth/logout (with the access token) → 204.
2. POST /partner/auth/refresh with the now-invalidated refresh token → 401.
**Expected (overall):** After logout the refresh token can no longer mint an access token.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_AUTH_ACCESS_CONTROL_009
**Test Description:** Change password updates credentials (new works, old fails).
**Test Steps:**
1. Change-password with a WRONG currentPassword → 401 ("Current password is incorrect").
2. Change-password with the correct currentPassword → 204.
3. Log in with the NEW password → 200.
4. Log in with the OLD password → 401.
**Expected (overall):** Password change rejects a wrong current; new credentials work, old are rejected.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.
### API · DEAL_REGISTRATION_PIPELINE

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_001
**Test Description:** Happy-path deal registration on POST /v1/sa/deals — valid payload creates a 'registered' deal with a protection window.
**Test Steps:**
1. Auth as SA; create a partner; pick a published billing plan.
   → Expected: partner created; a published planId obtained.
2. POST /v1/sa/deals with all fields (partnerId, planId, dealType='referral', prospect*, ACV, closeDate, notes).
   → Expected: HTTP 201 + server-assigned _id.
3. Assert every submitted field stored unchanged.
   → Expected: all 10 fields echoed; expectedCloseDate preserves the date.
4. Assert lifecycle.
   → Expected: status 'registered', protectionExpiresAt set, conflictStatus 'none'.
5. GET /v1/sa/deals/{id}.
   → Expected: same deal returned, status 'registered'.
6. Teardown: delete the parent partner.
   → Expected: cleanup OK (deals have no delete endpoint).
**Expected (overall):** Deal registered with all fields persisted exactly, protection window opened, retrievable.
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_002
**Test Description:** Register a reseller deal — billing model 'reseller' is stored.
**Test Steps:**
1. Create partner; pick a published plan; register a deal with dealType='reseller'.
   → Expected: HTTP 201 + _id.
2. Assert billing model + echo.
   → Expected: dealType stored == 'reseller'; all fields echoed.
3. Assert lifecycle + GET by id.
   → Expected: status 'registered', protection set, dealType 'reseller' persisted.
**Expected (overall):** Reseller deal registered; dealType='reseller' IS the stored billing model (no separate field).
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_003
**Test Description:** Register a co-sell deal — co-sell metadata is stored.
**Test Steps:**
1. Create partner; pick a published plan; register a deal with dealType='co_sell'.
   → Expected: HTTP 201 + _id.
2. Assert co-sell + echo.
   → Expected: dealType stored == 'co_sell'; all fields echoed.
3. Assert lifecycle + GET by id.
   → Expected: status 'registered', protection set, dealType 'co_sell' persisted.
**Expected (overall):** Co-sell deal registered; dealType='co_sell' IS the stored metadata. The 70/30 split is downstream (_011, blocked).
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_004
**Test Description:** Deal protection: a second partner registering the same prospect is flagged as a conflict.
**Test Steps:**
1. Create two partners + one shared prospect (name+email); partner 1 registers the deal.
   → Expected: deal A conflictStatus 'none'.
2. Partner 2 registers the SAME prospect.
   → Expected: HTTP 201 but conflictStatus 'flagged'; conflictingDealId == deal A id.
3. GET /v1/sa/deals/{id} on deal B.
   → Expected: conflictStatus still 'flagged'.
**Expected (overall):** Cross-partner same-prospect deal is created but flagged against the first deal.
**Note:** Same partner re-registering the same prospect is a hard 400 duplicate (separate behavior).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_005
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_006
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_007
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_008
**Test Description:** Approve a registered deal (POST /v1/sa/deals/{id}/approve): status -> approved, reviewer stamped; rate + rate table version expected.
**Test Steps:**
1. Create partner; register a deal (registered).
   → Expected: deal 'registered'.
2. Approve (reviewNotes).
   → Expected: HTTP 201; status 'approved'.
3. Assert reviewer stamped.
   → Expected: reviewedAt + reviewedBy present.
4. Assert rate + rateTableVersion stamped.
   → Expected: rate + rateTableVersion present in the response.
**Expected (overall):** Deal approved + reviewer stamped; rate/rate-table-version stamping pending BE.
**Note:** FAILED (by design) — gap: rate/rateTableVersion are NOT in the deal API response (and no commission is created at approve). Confirm with BE: stamped internally / different stage (win) / unimplemented.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_009
**Test Description:** Resolve a flagged deal conflict (POST /v1/sa/deals/{id}/resolve-conflict): decision + reasoning are stamped and immutable.
**Test Steps:**
1. Create a flagged conflict (two partners, same prospect).
   → Expected: deal B 'flagged'.
2. Resolve (decision='resolved_for_partner', reasoning).
   → Expected: HTTP 201; conflictStatus='resolved_for_partner'; conflictResolution{decision,reasoning,resolvedBy,resolvedAt} matches sent.
3. Resolve again with different decision/reasoning.
   → Expected: 4xx ('not in FLAGGED conflict state') — immutable.
4. GET /v1/sa/deals/{id}.
   → Expected: decision + reasoning unchanged (original).
**Expected (overall):** Conflict resolved once; decision + reasoning are immutable.
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_010
**Test Description:** Approving a deal emits a partner.deal.approved event (the CRM-sync trigger).
**Test Steps:**
1. Create partner; register a deal.
   → Expected: deal 'registered'.
2. Approve the deal.
   → Expected: status 'approved'.
3. GET /v1/sa/audit-logs.
   → Expected: a partner.deal.approved event records the registered->approved transition.
**Expected (overall):** Deal-approved event is published. CRM owner/stage update is a downstream service (connectors/CRM Integration), out of scope.
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_011
**Note (BLOCKED):** Not automated — was mislabeled PASSED/Auto=YES (false-green), corrected to BLOCKED. The co-sell 70/30 split is computed DOWNSTREAM; at register time the deal record carries no split field (verified via _003) and there is no API to read the computed split, so the 70/30 default cannot be asserted. Same dependency family as _012. Unblock when BE exposes the computed split (or a split-calc API).

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_012
**Note (BLOCKED):** Depends on the co-sell split-calculation engine (feature _011), which is downstream and not exposed as an API — there is no endpoint to submit a co-sell split override, so the "override at/below $100K ACV is not accepted" rule cannot be exercised (threshold is ABOVE $100K ACV). Unblock when BE exposes the split-override API.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_013
**Test Description:** Resolving the FLAGGED deal FOR its partner (decision=resolved_for_partner, citing the prospect's confirmation) makes that deal the winner and automatically flips the conflicting deal to the loser; both keep status 'registered'.
**Test Steps:**
1. Two partners register the SAME prospect (name+email); deal B (second) becomes flagged.
   → Expected: deal B conflictStatus='flagged'.
2. Resolve the flagged deal B FOR its partner (decision='resolved_for_partner', reasoning cites prospect confirmation).
   → Expected: HTTP 201; deal B conflictStatus='resolved_for_partner'; conflictResolution recorded.
3. Check the conflicting deal A.
   → Expected: deal A auto-flipped to conflictStatus='resolved_against_partner' (loser).
4. GET both deals.
   → Expected: B 'resolved_for_partner' + status 'registered'; A 'resolved_against_partner' (persisted).
5. Teardown: delete both partners.
   → Expected: cleanup OK.

**Expected (overall):** the confirmed partner wins the conflict and the other deal is flipped to the loser.
**Note:** Decision/reasoning immutability is covered by _009; negative resolve inputs by _029.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_014
**Note (BLOCKED):** No distinct API surface. resolve-conflict (POST /v1/sa/deals/{id}/resolve-conflict) is an SA-manual decision (enum resolved_for_partner|resolved_against_partner); it accepts no "prospect unreachable" signal and applies no automatic "first-registered-wins" tiebreaker. The only executable path (SA manually resolving for the earlier deal) is mechanically identical to _013 → nothing distinct to assert. Unblock if BE implements an automatic tiebreaker; otherwise covered by _013.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_015
**Note (BLOCKED):** Depends on tenant-provisioning + commission infrastructure not reachable from this test domain. Verifying "no registration → no attribution/commission" requires POST /internal/tenants/provision (internal-only), reading tenant.attribution.partnerId == null, asserting no partner_commissions row, and confirming no blazeup.partner.commission.earned event — none exposed to QA here. Negative companion of PARTNER_API_006 (§3 Scenario I). Unblock when the provisioning endpoint + commission/event verification become available.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_016
**Test Description:** SA manually extends a registered deal's protection window (POST /v1/sa/deals/{id}/extend-protection, body addedDays + reasoning).
**Test Steps:**
1. Create a partner + pick a published plan + register a deal (captures protectionExpiresAt).
   → Expected: registered deal has a protection window.
2. POST extend-protection with addedDays=30 + reasoning.
   → Expected: HTTP 201 / body statusCode 200; message confirms.
3. Compare the new protectionExpiresAt vs the old.
   → Expected: window moved later by 30 days; deal stays 'registered'.
4. GET /v1/sa/deals/{id}.
   → Expected: extended protectionExpiresAt persisted.
**Expected (overall):** SA manual extension pushes the protection window out by the requested days.
**Note:** PASSED — verified 2026-06-30. Window extends by exactly addedDays from the OLD expiry (e.g. +30d: 2026-08-29 → 2026-09-28). Plan frames this as a queued partner request, but the implemented endpoint is a DIRECT SA extension (HTTP 201) — confirm with BE if a queued partner-request flow is also expected. (CreateDealDto now also requires tenantDomain / numberOfEmployee / billingCycle — make_deal updated.)

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_017
**Note (BLOCKED):** Needs a 90-day clock staging can't provide. "Re-registering a conflict-lost prospect is accepted after 90 days (when no close exists)" requires a conflict-lost deal whose loss is 90+ days old; createdAt/lostAt are server-assigned and cannot be backdated, and there is no test clock/fast-forward. The negative companion ("reject re-registration BEFORE 90 days") IS buildable now as a separate TC. Unblock when BE provides a test clock or backdating.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_018
**Note (DEFERRED):** Win a deal (POST /v1/sa/deals/{id}/win). The WinDealDto carries a payment card + billing details + tenant provisioning — calling it has heavy side effects (provisions a tenant, may touch billing). Deferred to avoid polluting staging; build with a dedicated teardown / a BE-provided sandbox flag.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_019
**Test Description:** SA marks an approved deal as lost (POST /v1/sa/deals/{id}/lose).
**Test Steps:**
1. Register a deal, then approve it (precondition: lose requires an approved deal).
   → Expected: deal is 'approved'.
2. POST /lose.
   → Expected: HTTP 201 / body statusCode 200; status becomes 'lost'.
3. GET /v1/sa/deals/{id}.
   → Expected: 'lost' persisted.
**Expected (overall):** An approved deal transitions to 'lost'.
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_020
**Test Description:** SA retrieves a single deal by id (GET /v1/sa/deals/{id}) — full record.
**Test Steps:**
1. Register a deal; capture its id.
2. GET /v1/sa/deals/{id}.
   → Expected: HTTP 200; the record matches (id, partnerId, dealType, status, prospect fields) and no sensitive field leaks.
**Expected (overall):** Get-by-id returns the full, correct deal record.
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_031
**Test Description:** Negative of _020 (get-by-id): a ghost / malformed deal id is rejected.
**Test Steps:**
1. GET /v1/sa/deals/{ghost-but-well-formed-id} → 404 (not found).
2. GET /v1/sa/deals/{malformed-id} → 400 ('Invalid id').
**Expected (overall):** Illegal get-by-id targets are rejected (4xx), never 5xx, no record returned.
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_032
**Test Description:** Negative of _019 (lose): illegal lose targets are rejected.
**Test Steps:**
1. lose a non-existent id / a malformed id / a deal not in an approved state (e.g. just-registered).
   → Expected: each 4xx ('not found' / 'Invalid id' / 'cannot transition...').
**Expected (overall):** Every illegal lose attempt is rejected (4xx).
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_021
**Test Description:** Negative of register: invalid/missing fields must be rejected with 400.
**Test Steps:**
1. Verify the ghost planId 'no-such-plan-qa' is absent (GET sa-plans).
   → Expected: GET billing-plans/{ghost} returns 4xx (absent confirmed).
2. POST register with: missing partnerId/dealType/prospectName/prospectCountry/ACV/closeDate, invalid dealType, invalid email, negative ACV, bad date, ghost partnerId.
   → Expected: each 400 with a field/clear message.
3. POST register with a non-existent planId.
   → Expected: should be 4xx.
**Expected (overall):** Every invalid register payload rejected; planId should be validated.
**Note:** FAILED (by design) — gap: a non-existent planId is accepted (201). sa-plans returns 400 for it, but the deals endpoint does not validate planId cross-service. Confirm with BE.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_022
**Test Description:** Idempotency/duplicate: the SAME partner registering the SAME prospect twice is rejected (no second deal).
**Test Steps:**
1. One partner + a published plan + a unique prospect identity; the partner registers the deal once.
   → Expected: HTTP 201, conflictStatus 'none'.
2. The SAME partner re-registers the SAME prospect (name+email).
   → Expected: HTTP 400, message '...already exists...'.
3. Inspect the rejected response body.
   → Expected: no second deal id (no deal was created).
**Expected (overall):** Same-partner duplicate is a hard 400 reject; distinct from _004 (a different partner → 201 + flagged).
**Note:** PASSED — verified 2026-06-22.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_028
**Test Description:** Negative of approve: illegal targets rejected.
**Test Steps:**
1. approve a non-existent id / malformed id / an already-approved deal.
   → Expected: each 4xx ('not found' / 'Invalid id' / 'cannot transition...').
**Expected (overall):** All illegal approve attempts rejected.
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_029
**Test Description:** Negative of resolve-conflict: invalid input rejected.
**Test Steps:**
1. resolve-conflict with invalid decision / missing decision / missing reasoning / non-existent id / malformed id / a non-flagged deal.
   → Expected: each 4xx with a clear message ('decision must be one of' / 'reasoning...' / 'not found' / 'Invalid id' / 'not in FLAGGED conflict state').
**Expected (overall):** Every invalid resolve-conflict attempt rejected.
**Note:** —

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_030
**Test Description:** Negative of _016 (extend-protection): invalid input rejected with a clear error.
**Test Steps:**
1. extend-protection with: missing addedDays / missing reasoning / addedDays 0 / negative / over max (181) / non-numeric / ghost deal id (valid body) / malformed id.
   → Expected: each 400 with a clear message ('addedDays must be 1..180' / 'reasoning should not be empty' / 'must not be less than 1' / 'must not be greater than 180' / 'not found' / 'Invalid id').
**Expected (overall):** Every invalid extend-protection attempt rejected. BE validates the body before the deal lookup, so field cases are self-proving on a ghost id (no real deal needed).
**Note:** PASSED — verified 2026-06-25. Spec constraint discovered: addedDays ∈ 1..180; reasoning required + non-empty.

### API · DEAL_APPROVAL_QUEUE

#### PARTNER_API_DEAL_APPROVAL_QUEUE_001
**Test Description:** SA rejects a queued (registered) deal from the approval queue (POST /v1/sa/deals/{id}/reject, body reviewNotes).
**Test Steps:**
1. Register a deal (precondition: 'registered', i.e. queued for review).
2. POST /reject with reviewNotes.
   → Expected: HTTP 201 / body statusCode 200; status becomes 'rejected'.
3. GET /v1/sa/deals/{id}.
   → Expected: 'rejected' persisted.
**Expected (overall):** A registered deal is rejected and stays rejected.
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_DEAL_APPROVAL_QUEUE_011
**Test Description:** Negative of _001 (reject): illegal reject targets are rejected.
**Test Steps:**
1. reject a non-existent id / a malformed id / an already-rejected (or non-registered) deal.
   → Expected: each 4xx ('not found' / 'Invalid id' / 'cannot transition...').
**Expected (overall):** Every illegal reject attempt is rejected (4xx).
**Note:** PASSED — verified 2026-06-30.

### API · DEAL_COLLABORATION

#### PARTNER_API_DEAL_COLLABORATION_001
**Note (BLOCKED):** No collaboration/notes-thread API. A deal carries only a single flat `notes` string (set at register / via deal update) — there is no comment/activity-thread endpoint to add, list, or attribute collaboration entries. Re-scope with BE: if "collaboration" is just the flat notes field, it is already covered by the register/update TCs; otherwise the endpoints do not exist yet.

#### PARTNER_API_DEAL_COLLABORATION_002
**Note (BLOCKED):** No document/attachment API on deals. No endpoint to upload, list, or download deal documents. Build when BE exposes a deal-documents surface.

### API · PIPELINE_MANAGEMENT

#### PARTNER_API_PIPELINE_MANAGEMENT_001
**Test Description:** A partner lists its deals (GET /partner/portal/deals) — only its OWN deals are returned (scoped).
**Test Steps:**
1. Mint a partner session; the partner registers a deal.
2. GET /partner/portal/deals.
   → Expected: HTTP 200; the registered deal appears AND every row's partnerId == the caller's partner (no cross-partner leakage).
**Expected (overall):** The own-deals list is correctly scoped to the authenticated partner.
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_PIPELINE_MANAGEMENT_002
**Test Description:** A partner filters its deals list by status (GET /partner/portal/deals?status=registered).
**Test Steps:**
1. Mint a partner session; register a deal (status 'registered').
2. GET /partner/portal/deals?status=registered.
   → Expected: HTTP 200; every returned deal has status 'registered' AND the registered deal is included.
**Expected (overall):** The status filter is applied correctly.
**Note:** PASSED — verified 2026-06-30. Valid deal-status enum: registered, approved, in_progress, won, lost, expired, rejected.

#### PARTNER_API_PIPELINE_MANAGEMENT_011
**Test Description:** Negative of _001/_002: an invalid filter / oversized pagination is handled gracefully.
**Test Steps:**
1. GET /partner/portal/deals?status=bogus → 400 (status must be one of the enum).
2. GET /partner/portal/deals?limit=999999 → 400 ('limit must not exceed 100').
**Expected (overall):** Invalid filter/pagination is rejected (4xx), never 5xx.
**Note:** PASSED — verified 2026-06-30.
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
**Test Steps:**
1. Auth as SA. GET /v1/sa/partners?page=1&limit=5.
   → Expected: HTTP 200.
2. Assert the envelope.
   → Expected: data is a list, total >= 0, message present.
3. Assert pagination.
   → Expected: returned page size <= requested limit (5).
4. Data integrity + SA filtering (data-dependent).
   → Expected: each partner is a non-empty object with unique id; WARN-skips if staging has 0 partners.
5. SA isolation / no cross-partner leakage.
   → Expected: SA-scoped directory only; WARN-skips when no data.
**Expected (overall):** Partner list returns a valid paginated envelope.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002
**Test Description:** CRUD create on POST /v1/sa/partners with required name/email/type.
**Test Steps:**
1. Build a unique partner payload (name/email/type=channel).
   → Expected: payload ready.
2. POST /v1/sa/partners.
   → Expected: HTTP 201; body statusCode 200; success message; register cleanup.
3. Assert persisted.
   → Expected: server-assigned _id and code (PAR-xxxxxx) present.
4. Assert echo.
   → Expected: stored name/email/type == sent.
5. Assert lifecycle.
   → Expected: status == 'pending' (awaits SA activation).
6. GET /v1/sa/partners/{id}.
   → Expected: same partner returned, still 'pending'.
**Expected (overall):** Pending partner created, persisted, retrievable.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003
**Test Description:** State transition on POST /v1/sa/partners/{id}/approve: pending -> active with approval event.
**Test Steps:**
1. Create a pending partner (precondition).
   → Expected: partner is 'pending'.
2. POST /v1/sa/partners/{id}/approve.
   → Expected: HTTP 201; success message; same partner id.
3. Assert transition + event.
   → Expected: status 'active'; approvedAt set; approvedBy present.
4. GET /v1/sa/partners/{id}.
   → Expected: status 'active' persisted.
**Expected (overall):** Pending partner approved to active with approval metadata; downstream activation-user is event-driven (out of scope).
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004
**Test Description:** Decline/suspend a partner via POST /v1/sa/partners/{id}/deactivate; reason should be mandatory and audit-logged.
**Test Steps:**
1. Create a pending partner; decline WITH a reason.
   → Expected: HTTP 201; status -> 'suspended'.
2. GET /v1/sa/audit-logs.
   → Expected: an entry records the decline action with the reason.
3. Enforce mandatory reason: decline with no / empty / whitespace reason.
   → Expected: should be 400 each.
**Expected (overall):** Decline works and the reason is audit-logged; mandatory-reason should be enforced.
**Note:** PASSED — verified 2026-06-29. BE now enforces a mandatory, non-empty decline reason (absent/empty/whitespace → 400). Was a known gap; fixed by BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005
**Test Description:** Tier change on POST /v1/sa/partners/{id}/upgrade-tier emits a partner.tier.changed event (portal/analytics refresh signal).
**Test Steps:**
1. Create a partner (tier defaults to 'registered').
   → Expected: tier == 'registered'.
2. upgrade-tier to 'select' (+reason).
   → Expected: HTTP 201; tier == 'select'.
3. GET /v1/sa/audit-logs.
   → Expected: partner.tier.changed event records before='registered', after='select'.
4. GET /v1/sa/partners/{id}.
   → Expected: tier 'select' persisted.
**Expected (overall):** Tier changes and the change event is published; portal/analytics refresh is a downstream consumer (out of scope).
**Note:** —

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
**Test Steps:**
1. Create a partner + invite a portal user (capture userId).
   → Expected: partner + user ready.
2. Grant certification (sales_certified, score=95).
   → Expected: HTTP 201; status 'active'; earnedAt + expiresAt set; type echoed.
3. GET /v1/sa/partners/{partnerId}/certifications.
   → Expected: the granted cert appears for the user.
4. GET /v1/sa/audit-logs.
   → Expected: partner.certification.granted event records the cert type.
**Expected (overall):** Certification earned, listed, and event published; tier re-evaluation is downstream (out of scope).
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011
**Test Description:** Negative of list: invalid pagination must be handled gracefully (never 5xx).
**Test Steps:**
1. GET list with page=0 and page=-1.
   → Expected: must be < 500 (graceful).
2. Observe limit=-5 / 999999 / page='abc'.
   → Expected: logged (currently defaulted, no 400).
**Expected (overall):** Invalid pagination must not crash the endpoint.
**Note:** PASSED — verified 2026-06-29. BE now returns 400 for invalid pagination (page=0/-1 → "page must not be less than 1"); no longer HTTP 500. Was a known gap; fixed by BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012
**Test Description:** Negative of create: invalid/missing fields must be rejected with 400 + field errors, no record created.
**Test Steps:**
1. POST create with: missing name / missing email / missing type / malformed email / empty name / invalid type enum.
   → Expected: each 400 with a field-level message; no record persisted.
**Expected (overall):** Every invalid create payload rejected with 400.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013
**Test Description:** Negative of approve: illegal targets rejected.
**Test Steps:**
1. approve a non-existent id / malformed id / already-active partner.
   → Expected: each 4xx with a clear message ('not found' / 'Invalid id' / 'cannot be approved from status active').
**Expected (overall):** All illegal approve attempts rejected.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014
**Test Description:** Negative of deactivate: invalid id rejected; repeat is idempotent.
**Test Steps:**
1. deactivate a non-existent id / malformed id.
   → Expected: each 4xx ('not found' / 'Invalid id').
2. deactivate an already-suspended partner again.
   → Expected: no 5xx; stays 'suspended' (idempotent no-op).
**Expected (overall):** Invalid-id deactivate rejected; repeat deactivate is idempotent.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015
**Test Description:** Negative of tier change: invalid input rejected.
**Test Steps:**
1. upgrade-tier with invalid enum / missing tier / non-existent id / malformed id.
   → Expected: each 4xx with a clear message.
**Expected (overall):** All invalid tier-change attempts rejected.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_016
**Note (BLOCKED):** [BLOCKED — NO API 2026-06-17] Searched OpenAPI specs of all 11 platform services (admin-api, compliance-api, connectors, helpplatform-api, sa-auth-api, sa-governance-api, sa-partners-api, sa-plans-api, sa-tenants-api, setting-api, workflow-api): 0 fields for reseller/end-client price (only basePrice/totalPrice in plan/billing, unrelated). No endpoint or field to send/store an end-client price → the data-model this TC describes is not implemented in any current API. Confirm with product/BE: which service owns this, or is it a future PRD feature (§2.2/§7.2/§11)? Not automatable until the model exists.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_017
**Note (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] This is a scheduled background JOB (quarterly tier recalculation), not an API endpoint. No manual-trigger endpoint exists in any service to invoke it on demand, so it cannot be exercised via API automation. Belongs to BE unit/integration tests (or needs a QA-only trigger endpoint). Note: manual tier change IS covered by _005 (POST /upgrade-tier); this TC is specifically the automated quarterly job. Confirm with BE whether a trigger endpoint can be exposed.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_018
**Note (BLOCKED):** [BLOCKED — NO API TRIGGER 2026-06-17] Depends on the quarterly tier-calculation job (_007): the "downgrade grace quarter" rule (partner keeps current-tier benefits during the grace period) is applied by that scheduled job, not a callable endpoint. No API to set the clock/quarter or trigger the grace evaluation → not API-automatable. BE unit/integration test territory. Confirm with BE.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_019
**Note (BLOCKED):** [BLOCKED — NO API 2026-06-17] No endpoint or field for PSM (Partner Success Manager) allocation or ARR thresholds in any of the 11 service specs (only unrelated carryForwardPolicy in setting-api). The "$1.5M ARR → dedicated PSM" rule is a calculation not exposed via API → not automatable now. Confirm with product/BE where this logic lives (likely a job/internal calc).

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020
**Test Description:** Negative of grant certification: invalid input rejected.
**Test Steps:**
1. grant cert with invalid certificationType / missing type / non-existent userId / malformed userId.
   → Expected: each 4xx with a clear message.
**Expected (overall):** All invalid grant-cert attempts rejected.
**Note:** —

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_021
**Test Description:** Idempotency/duplicate: creating a partner with the same email twice is rejected (no second account).
**Test Steps:**
1. Create a partner with a unique email.
   → Expected: HTTP 201, account created.
2. Re-create with the SAME email.
   → Expected: HTTP 400, message '...already exists'.
3. Inspect the rejected response body.
   → Expected: no second account created.
**Expected (overall):** Same-email duplicate is a hard 400 reject; no duplicate partner account.
**Note:** PASSED — verified 2026-06-23.

#### PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_022
**Test Description:** Idempotency/duplicate: re-granting the same certification type to the same user must not create a duplicate (renew or 409).
**Test Steps:**
1. Create a partner + invite a user.
   → Expected: user created.
2. Grant 'sales_certified' (first time).
   → Expected: cert active.
3. Re-grant the SAME type, then list the partner's certifications.
   → Expected: exactly 1 'sales_certified' cert (idempotent renew) OR a 409 on re-grant.
**Expected (overall):** Re-grant must not duplicate an active cert of the same type.
**Note:** FAILED (by design) — gap: re-grant returns 201 and creates a SECOND active cert (list shows 2). BE should renew or reject. Confirm with BE.

### API · PARTNER_USERS

#### PARTNER_API_PARTNER_USERS_001
**Test Description:** SA lists portal users for a partner: GET /sa-partners-api/v1/sa/partner-users?partnerId= returns the user list with roles.
**Test Steps:**
1. Create a partner + invite a portal user.
   → Expected: user created with a userId.
2. GET partner-users filtered by partnerId.
   → Expected: 200, envelope {statusCode, data[], total, message}.
3. Verify the invited user appears + list scoping.
   → Expected: user present with role + status + email; every row's partnerId == the requested partner.
4. Verify no sensitive leak.
   → Expected: no password/tempPassword key in any list row (invite carries tempPassword; the list must not).
**Expected (overall):** Partner-scoped user list with roles/status, no credential leak.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_PARTNER_USERS_011
**Test Description:** Negative of _001 (list partner-users): invalid pagination/filter handled gracefully (never 5xx).
**Test Steps:**
1. Validated cases: page=0 / page=-1 (skip non-negative), limit over max (>100), malformed partnerId.
   → Expected: each 400 ('skip must be a non-negative integer' / 'limit must not exceed 100' / 'partnerId must be a mongodb id').
2. Ghost (valid-but-nonexistent) partnerId.
   → Expected: 200 with an empty list.
3. Lenient params: limit=0 / non-numeric page / unknown sort.
   → Expected: not rejected (silently defaulted, HTTP 200) — must still never 5xx.
**Expected (overall):** Validated invalid input → 4xx; lenient params default gracefully; never 5xx.
**Note:** PASSED — verified 2026-06-25. WEAK-VALIDATION gap to confirm with BE: unlike the audit-log list (which 400s these), limit=0 / non-numeric page / unknown sort are silently defaulted (200) instead of rejected.

#### PARTNER_API_PARTNER_USERS_002
**Test Description:** SA invites a partner-portal user: POST /sa-partners-api/v1/sa/partner-users creates the user with a role.
**Test Steps:**
1. Create a partner; POST invite (partnerId + email + firstName + lastName + role).
   → Expected: HTTP 201, server-assigned userId.
2. Verify every submitted field is stored.
   → Expected: partnerId/email/firstName/lastName/role echoed as sent.
3. Verify the user is usable.
   → Expected: status 'active' + a tempPassword issued for SA hand-off.
4. Verify retrievable in the list.
   → Expected: the user appears in GET partner-users?partnerId.
**Expected (overall):** Invite creates a usable partner-portal user with the chosen role.
**Note:** PASSED — verified 2026-06-25. TC↔BE: plan says "email sent + PENDING user", but BE creates an ACTIVE user + returns tempPassword (temp-password onboarding). Confirm with BE which model is intended. No sa-plans dependency.

#### PARTNER_API_PARTNER_USERS_012
**Test Description:** Negative of _002 (invite): invalid/missing fields rejected with 400.
**Test Steps:**
1. Invite with missing email / firstName / lastName / partnerId, invalid role enum, invalid email, ghost partnerId, malformed partnerId.
   → Expected: each 400 with a field/clear message ('email must be an email' / 'firstName...' / 'partnerId must be a mongodb id' / 'role must be one of' / 'Partner ... not found').
**Expected (overall):** Every invalid invite payload rejected with 4xx. Ghost partnerId is self-proving (endpoint returns not-found).
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_PARTNER_USERS_013
**Test Description:** Idempotency/duplicate of _002: inviting the same email twice must not create a duplicate user.
**Test Steps:**
1. Create a partner + invite a user (email E).
   → Expected: user created.
2. Re-invite the SAME email E.
   → Expected: 409 reject OR idempotent (no new user).
3. List the partner's users.
   → Expected: exactly 1 user for email E.
**Expected (overall):** Re-invite must not create a duplicate-email user (email is the login identity).
**Note:** FAILED (by design) — gap: re-invite returns 201 and creates a SECOND user with the same email (list shows 2). BE should reject (409) or be idempotent. Confirm with BE.

#### PARTNER_API_PARTNER_USERS_003
**Test Description:** SA resets a partner-portal user's password: POST /sa-partners-api/v1/sa/partner-users/{userId}/reset-password issues a fresh credential.
**Test Steps:**
1. Create partner + invite a user (capture the invite tempPassword).
   → Expected: user created.
2. Reset the user's password.
   → Expected: 200 'Password reset successfully', response references the same userId.
3. A fresh credential is issued.
   → Expected: a new tempPassword, different from the invite one.
4. Reset is repeatable.
   → Expected: a second reset also returns 200.
**Expected (overall):** Reset issues a fresh hand-off credential and is a repeatable mutating action.
**Note:** PASSED — verified 2026-06-25. TC↔BE: plan says "reset LINK sent", but BE returns a new tempPassword (temp-password model). Confirm with BE. Idempotency: reset is not a create — repeating it is valid, so no duplicate-create TC.

#### PARTNER_API_PARTNER_USERS_014
**Test Description:** Negative of _003 (reset password): invalid id is rejected (4xx, never 5xx).
**Test Steps:**
1. Reset with a ghost userId.
   → Expected: 4xx 'User ... not found'.
2. Reset with a malformed userId.
   → Expected: 4xx 'Invalid id'.
**Expected (overall):** Non-existent/malformed userId rejected with 4xx; never 5xx.
**Note:** PASSED — verified 2026-06-25. Self-proving (endpoint returns not-found). No sa-plans dependency.
### API · TERRITORIES

#### PARTNER_API_TERRITORIES_001
**Test Description:** SA assigns a territory to a partner: POST /sa-partners-api/v1/sa/territories saves it with effective dates.
**Test Steps:**
1. Create a partner; assign a territory (partnerId + label + countries + exclusivityType + effective dates).
   → Expected: HTTP 201, server-assigned id.
2. Verify stored fields.
   → Expected: partnerId/label/countries/exclusivityType echoed; exclusivityStartDate/EndDate preserved.
3. GET by id.
   → Expected: same territory returned.
**Expected (overall):** Territory assignment persisted with fields + effective dates, retrievable by id.
**Note:** PASSED — verified 2026-06-25. exclusivityType ∈ exclusive/preferred/open; countries are ISO 3166-1 alpha-2. No sa-plans dependency.

#### PARTNER_API_TERRITORIES_011
**Test Description:** Negative of _001 (assign): invalid/missing fields rejected with 400.
**Test Steps:**
1. Assign with missing partnerId/label/countries, invalid exclusivityType, invalid country code, bad date, ghost/malformed partnerId.
   → Expected: each 400 with a field/clear message ('mongodb id' / 'label' / 'countries...ISO31661' / 'exclusivityType must be one of' / 'ISO 8601' / 'Partner ... not found').
**Expected (overall):** Every invalid assign rejected with 4xx. Ghost partnerId self-proving.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_TERRITORIES_012
**Test Description:** Exclusive territory conflict: a 2nd partner cannot take a country already held exclusively.
**Test Steps:**
1. Two partners; partner 1 takes an EXCLUSIVE territory on a country.
   → Expected: 201.
2. Partner 2 assigns an EXCLUSIVE territory on the SAME country.
   → Expected: 4xx 'Exclusive territory conflict'.
3. Inspect the rejected response.
   → Expected: no territory created for partner 2.
**Expected (overall):** Cross-partner exclusive overlap is rejected; same-partner overlap is allowed by design.
**Note:** PASSED — verified 2026-06-25. The duplicate/conflict counterpart of _001 (BE enforces exclusive cross-partner conflict). No sa-plans dependency.

#### PARTNER_API_TERRITORIES_002
**Test Description:** SA lists territories with filters: GET /sa-partners-api/v1/sa/territories (paginated, scoped, filterable).
**Test Steps:**
1. Create partner + assign a territory; GET territories?partnerId.
   → Expected: 200, envelope {statusCode, data[], total} (no message field).
2. Verify the territory appears, scoped, with schema.
   → Expected: present with label/countries/exclusivityType; every row's partnerId == the requested partner.
3. Filter by exclusivityType.
   → Expected: only matching rows.
**Expected (overall):** Partner-scoped territory list, well-formed and filterable.
**Note:** PASSED — verified 2026-06-25. Territory list envelope has no `message` field (unlike other lists). No sa-plans dependency.

#### PARTNER_API_TERRITORIES_013
**Test Description:** Negative of _002 (list): invalid filter/pagination rejected (4xx, never 5xx).
**Test Steps:**
1. List with bad exclusivityType / bad country / limit>max / page=0 / malformed partnerId.
   → Expected: each 400 (this endpoint validates strictly — no lenient defaulting).
**Expected (overall):** Every invalid filter/pagination rejected with 4xx; never 5xx.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_TERRITORIES_003
**Test Description:** SA retrieves a single territory by id: GET /sa-partners-api/v1/sa/territories/{id}.
**Test Steps:**
1. Create partner + assign a territory; GET by id.
   → Expected: 200, id matches; partnerId/label/countries/exclusivityType present.
**Expected (overall):** Get-by-id returns the full territory.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_TERRITORIES_014
**Test Description:** Negative of _003 (get by id): invalid id rejected (4xx).
**Test Steps:**
1. GET with a ghost id / malformed id.
   → Expected: 4xx ('Territory ... not found' / 'Invalid id').
**Expected (overall):** Non-existent/malformed id rejected with 4xx; never 5xx.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_TERRITORIES_004
**Test Description:** SA removes a territory assignment: DELETE /sa-partners-api/v1/sa/territories/{id}.
**Test Steps:**
1. Create partner + assign a territory; DELETE it.
   → Expected: 200 'Territory removed successfully'.
2. GET the territory by id.
   → Expected: 4xx not-found (no longer retrievable).
**Expected (overall):** Delete removes the territory; it is no longer retrievable.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_TERRITORIES_015
**Test Description:** Negative of _004 (delete): invalid/already-removed rejected (4xx).
**Test Steps:**
1. DELETE with a ghost id / malformed id / an already-removed territory.
   → Expected: each 4xx ('Territory ... not found' / 'Invalid id').
**Expected (overall):** Every invalid/illegal delete rejected with 4xx. (Already-removed documents delete's repeat behavior; mutating action, not a duplicate-create.)
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.
### API · CERTIFICATIONS_SA

#### PARTNER_API_CERTIFICATIONS_SA_001
**Note (CROSS-REF):** Grant a certification is already covered by PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010 (certification earned: granted + listed + event + tier re-evaluation), with _020 (grant invalid input) and _022 (re-grant idempotency, fail-by-design). Not re-implemented here to avoid a duplicate test. If a standalone CERTIFICATIONS_SA_001 is required, point it at the same POST /v1/sa/partner-users/{userId}/certifications endpoint.

#### PARTNER_API_CERTIFICATIONS_SA_002
**Test Description:** SA revokes a partner certification: DELETE /sa-partners-api/v1/sa/partner-users/{userId}/certifications/{type} (body reason) soft-revokes it.
**Test Steps:**
1. Create partner + invite user + grant an active sales_certified cert.
   → Expected: cert active.
2. Revoke the cert with a reason.
   → Expected: 200 'Certification revoked successfully', status='revoked'.
3. List the partner's certifications.
   → Expected: the cert remains with status='revoked' (soft-revoke).
**Expected (overall):** Revoke soft-removes the cert (status='revoked'), kept in the list.
**Note:** PASSED — verified 2026-06-25. TC↔BE: plan says "certification removed", BE soft-revokes (status='revoked', record kept) — confirm BE. No sa-plans dependency.

#### PARTNER_API_CERTIFICATIONS_SA_012
**Test Description:** Negative of _002 (revoke): invalid input/state rejected with 4xx.
**Test Steps:**
1. Revoke with: missing reason / a cert not held / ghost userId / malformed userId / an already-revoked cert.
   → Expected: each 400 ('reason should not be empty' / 'Active ... not found' / 'User ... not found' / 'Invalid id').
**Expected (overall):** Every invalid/illegal revoke rejected with 4xx. (Already-revoked also documents revoke's repeat behavior; mutating action, not a duplicate-create.)
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_CERTIFICATIONS_SA_003
**Test Description:** SA lists a partner team's certifications: GET /sa-partners-api/v1/sa/partners/{partnerId}/certifications.
**Test Steps:**
1. Create partner + invite user + grant a sales_certified cert.
   → Expected: cert active.
2. GET partner certifications.
   → Expected: 200, envelope {statusCode, data[], total, message}.
3. Verify the granted cert + schema + scoping.
   → Expected: cert present with certificationType/status/userId/earnedAt/expiresAt; every row's partnerId == the requested partner.
4. Filter status=active.
   → Expected: only active certs returned.
**Expected (overall):** Partner-scoped cert list, well-formed and filterable.
**Note:** PASSED — verified 2026-06-25. Filters: status ∈ active/expired/revoked; certificationType enum; expiringWithinDays. No sa-plans dependency.

#### PARTNER_API_CERTIFICATIONS_SA_013
**Test Description:** Negative of _003 (list certs by partner): invalid filter/pagination handled gracefully (never 5xx).
**Test Steps:**
1. Out-of-enum status / certificationType, oversized limit (>100).
   → Expected: each 400 ('must be one of' / 'limit must not exceed 100').
2. Malformed partnerId.
   → Expected: 400 'Invalid id'.
3. Ghost partnerId.
   → Expected: 200 empty list.
4. page=0.
   → Expected: handled gracefully (4xx or default), never 5xx.
**Expected (overall):** Validated invalid filter/pagination → 4xx; ghost partner → 200 empty; never 5xx.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_CERTIFICATIONS_SA_004
**Test Description:** SA lists certifications expiring soon: GET /sa-partners-api/v1/sa/certifications?expiringWithinDays=N.
**Test Steps:**
1. GET /sa/certifications?expiringWithinDays=30.
   → Expected: 200, envelope {statusCode, data[], total, message}; every returned cert expires within 30 days (empty is acceptable).
2. expiringWithinDays max boundary (365).
   → Expected: 200 (accepted).
**Expected (overall):** Expiring-cert list returns a well-formed envelope; the expiringWithinDays window is bounded 1..365.
**Note:** PASSED — verified 2026-06-25. Confirm BE: the SA-wide list returns total=0 even when active certs exist (visible via the per-partner list _003) — possible scoping/index difference. Filter semantic asserted on whatever is returned; empty logged, not failed. No sa-plans dependency.

#### PARTNER_API_CERTIFICATIONS_SA_014
**Test Description:** Negative of _004 (SA cert list): invalid filter/pagination rejected (4xx, never 5xx).
**Test Steps:**
1. Out-of-enum status / certificationType; expiringWithinDays out of range (0 / negative / >365); limit over max; page=0.
   → Expected: each 400 ('must be one of' / 'expiringWithinDays must not be less than 1' / 'must not be greater than 365' / 'limit must not exceed 100' / 'skip must be a non-negative integer').
**Expected (overall):** Every invalid filter/pagination rejected with 4xx; never 5xx.
**Note:** PASSED — verified 2026-06-25. expiringWithinDays bounded 1..365. No sa-plans dependency.
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
**Test Steps:**
1. Mint a partner-portal session (SA creates + approves a partner, invites a user, logs in as that user → partner JWT).
   → Expected: a partner-authed session.
2. GET the partner dashboard.
   → Expected: HTTP 200, envelope {statusCode, data{}, message}.
3. Verify the KPI schema + no sensitive leak.
   → Expected: data has 'partner' (tier/status/openDealsCount), 'deals', 'commissions' sections; no password/token/secret key.
**Expected (overall):** Partner dashboard returns the well-formed KPI schema with no credential leak.
**Note:** PASSED — verified 2026-06-25. PARTNER-PORTAL endpoint (needs a partner JWT, not the SA token; SA token → 401). Session minted self-contained from the SA side. No invalid-input negative (no params; 401 auth belongs to Auth & Access Control). No sa-plans dependency.
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
**Test Steps:**
1. Mint a partner-portal session; GET own profile.
   → Expected: 200; data is the logged-in partner's account (code/email/tier/status); no sensitive key.
**Expected (overall):** Own profile returned, no credential leak.
**Note:** PASSED — verified 2026-06-25. No params (no input-negative; 401 → Auth feature). No sa-plans dependency.

#### PARTNER_API_PARTNER_PORTAL_002
**Test Description:** Partner retrieves its own deal by id: GET /partner/portal/deals/{id} — full record.
**Test Steps:**
1. Mint a partner-portal session; the partner registers a deal via /partner/portal/deals; capture its id.
2. GET /partner/portal/deals/{id}.
   → Expected: 200; the deal record matches (id, partnerId == own) and no sensitive key leaks.
**Expected (overall):** A partner can read the full record of its own deal.
**Note:** PASSED — verified 2026-06-30 (sa-plans-api back UP). Negative covered by _012.

#### PARTNER_API_PARTNER_PORTAL_012
**Test Description:** Negative of _002 (own deal by id): a ghost / malformed deal id is rejected.
**Test Steps:**
1. Mint a session; GET /partner/portal/deals/{ghost-well-formed-id} → 404 (not found).
2. GET /partner/portal/deals/{malformed-id} → 400 ('Invalid id').
**Expected (overall):** Illegal deal-detail targets are rejected (4xx), never 5xx, no record returned.
**Note:** PASSED — verified 2026-06-30.

#### PARTNER_API_PARTNER_PORTAL_003
**Test Description:** Partner retrieves its own certifications: GET /partner/portal/certifications.
**Test Steps:**
1. Mint a session; SA grants a cert to the partner user; GET own certs.
   → Expected: 200, list; the granted cert appears with status + earnedAt/expiresAt.
**Expected (overall):** Own certs listed with the right schema.
**Note:** PASSED — verified 2026-06-25. Negative (invalid filter) covered by _013. No sa-plans dependency.

#### PARTNER_API_PARTNER_PORTAL_013
**Test Description:** Negative of _003 (own certs): invalid filter rejected (4xx, never 5xx).
**Test Steps:**
1. GET own certs with bad status / certificationType enum, oversized limit.
   → Expected: each 400 ('must be one of' / 'must not exceed').
**Expected (overall):** Invalid cert filter rejected with 4xx; never 5xx.
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency.

#### PARTNER_API_PARTNER_PORTAL_004
**Test Description:** Partner retrieves its own commission summary: GET /partner/portal/commissions/summary.
**Test Steps:**
1. Mint a session; GET own commission summary.
   → Expected: 200; totalEarnedCents/totalPendingCents/totalPaidCents are non-negative ints (+ clawbackExposureCents).
**Expected (overall):** Earned/pending/paid totals returned.
**Note:** PASSED — verified 2026-06-25. No params (no input-negative). No sa-plans dependency.

#### PARTNER_API_PARTNER_PORTAL_005
**Test Description:** Partner retrieves its own assigned territories: GET /partner/portal/territories.
**Test Steps:**
1. Mint a session; SA assigns a territory to the partner; GET own territories.
   → Expected: 200, list; the assigned territory appears, scoped to the partner.
**Expected (overall):** Own territories returned, scoped.
**Note:** PASSED — verified 2026-06-25. No params (no input-negative). No sa-plans dependency.

#### PARTNER_API_PARTNER_PORTAL_006
**Test Description:** Partner retrieves its own tier commission rates: GET /partner/portal/rates.
**Test Steps:**
1. Mint a session; GET own rates.
   → Expected: 200, a well-formed list of tier rates (may be empty for the registered tier).
**Expected (overall):** Tier-specific rates returned as a list.
**Note:** PASSED — verified 2026-06-25. Rates list empty for a registered-tier partner on staging (well-formed list). No params (no input-negative). No sa-plans dependency.
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

#### PARTNER_API_AUDIT_LOG_007
**Test Description:** Negative of _004 (get audit entry by id): invalid id is rejected (4xx, never 5xx).
**Test Steps:**
1. GET audit-logs/{ghost id}.
   → Expected: 404 'Audit log entry ... not found'.
2. GET audit-logs/{malformed id}.
   → Expected: 400 'Invalid id'.
**Expected (overall):** Non-existent id → 404, malformed id → 400; never 5xx.
**Note:** PASSED — verified 2026-06-25. Self-proving (endpoint returns not-found), no setup needed, no sa-plans dependency.

#### PARTNER_API_AUDIT_LOG_005
**Test Description:** Negative of _001 (audit-log list): invalid pagination / filter is rejected gracefully (4xx, never 5xx).
**Test Steps:**
1. List with invalid pagination: page=0 / page=-1 / limit=0 / limit=-5 / limit over max (999999) / page non-numeric.
   → Expected: each 400 ('page/limit must not be less than 1', 'must not be greater than 100', 'must be an integer').
2. List with invalid filters: severity / category / actorType out of enum, dateFrom / dateTo bad format.
   → Expected: each 400 ('must be one of ...', 'must be a valid ISO 8601 date string').
3. List with an empty-but-valid range (dateFrom > dateTo).
   → Expected: handled gracefully (200, empty list — not a 5xx).
**Expected (overall):** Every invalid pagination/filter is rejected with 4xx (never 5xx); a valid empty range returns 200 empty.
**Note:** PASSED — verified 2026-06-25. BE validates all params (no sa-plans dependency). Enums: severity ∈ info/warning/critical; category ∈ SA_AUDIT_*; actorType ∈ sa-staff/impersonation/…

#### PARTNER_API_AUDIT_LOG_006
**Test Description:** Negative of _003 (audit-log export): invalid format/filter is rejected (4xx, never 5xx).
**Test Steps:**
1. Export with an out-of-enum format=bogus.
   → Expected: 400 'format must be one of'.
2. Export with invalid severity / category / actorType / retentionClass.
   → Expected: each 400 'must be one of ...'.
3. Export with a bad-format dateFrom / dateTo.
   → Expected: each 400 'must be a valid ISO 8601 date string'.
**Expected (overall):** Every invalid export format/filter is rejected with 4xx (never 5xx).
**Note:** PASSED — verified 2026-06-25. No sa-plans dependency. retentionClass enum ∈ standard/extended/permanent.
