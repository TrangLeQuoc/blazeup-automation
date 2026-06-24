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
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals | Default partner/BlazeUp quota credit split.

#### PARTNER_API_DEAL_REGISTRATION_PIPELINE_012
**Note (BLOCKED):** [PATH 2026-05-27] SA: /internal/deals → /v1/sa/deals | Threshold is above $100K ACV.

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

- PARTNER_API_DEAL_REGISTRATION_PIPELINE_014
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_015
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_016
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_017
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_018
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_019
- PARTNER_API_DEAL_REGISTRATION_PIPELINE_020
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
**Note (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_003
**Note (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

#### PARTNER_API_REFERRAL_ATTRIBUTION_004
**Note (BLOCKED):** [API pending 2026-05-27] GET/POST /v1/partner/referral-links — referral attribution endpoints not yet in dev build

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
**Note:** FAILED (by design) — known gap: the API accepts a decline with no/blank reason (returns 201). Confirm with BE whether reason must be mandatory.

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
**Note:** FAILED (by design) — APP BUG: page=0 and page=-1 return HTTP 500. Confirm with BE (should be 400).

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
