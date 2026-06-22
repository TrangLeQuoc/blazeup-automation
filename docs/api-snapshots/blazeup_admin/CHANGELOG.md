# API Change Log — blazeup_admin

## 2026-06-19 10:24 · workflow-api
- 🟢 ADDED   GET /workflow-api/sa/platform-templates/workflow/health
- 🟢 ADDED   GET /workflow-api/sa/platform-templates/workflow/health/templates
- 🟢 ADDED   GET /workflow-api/sa/platform-templates/workflow/{templateId}/adoption-stats
- 🟢 ADDED   POST /workflow-api/sa/platform-templates/workflow/{templateId}/mark-mandatory
- 🟢 ADDED   POST /workflow-api/sa/platform-templates/workflow/{templateId}/retract
- 🟢 ADDED   POST /workflow-api/templates/{templateId}/dismiss-new

## 2026-06-18 15:31 · sa-partners-api
- 🟢 ADDED   POST /sa-partners-api/v1/partner/auth/mfa/email-otp/send
- 🟢 ADDED   POST /sa-partners-api/v1/partner/auth/mfa/totp/enroll
- 🟢 ADDED   POST /sa-partners-api/v1/partner/auth/mfa/totp/setup
- 🟢 ADDED   POST /sa-partners-api/v1/partner/auth/mfa/verify
- 🟢 ADDED   POST /sa-partners-api/v1/sa/partner-users/{userId}/unlock
- 🟡 CHANGED GET /sa-partners-api/v1/sa/partners
    · (spec changed)

## 2026-06-17 11:21 · workflow-api
- baseline (71 endpoints)

## 2026-06-17 11:21 · setting-api
- baseline (101 endpoints)

## 2026-06-17 11:21 · sa-tenants-api
- baseline (63 endpoints)

## 2026-06-17 11:21 · sa-plans-api
- baseline (16 endpoints)

## 2026-06-17 11:21 · sa-governance-api
- baseline (43 endpoints)

## 2026-06-17 11:21 · sa-auth-api
- 🟡 CHANGED POST /sa-auth-api/internal/permissions/import
    · params: +['prune']

## 2026-06-17 11:21 · helpplatform-api
- baseline (37 endpoints)

## 2026-06-17 11:21 · connectors
- baseline (271 endpoints)

## 2026-06-17 11:21 · compliance-api
- baseline (66 endpoints)

## 2026-06-17 11:21 · admin-api
- baseline (213 endpoints)

## 2026-06-12 16:53 · sa-partners-api
- baseline (69 endpoints)

## 2026-06-12 16:53 · sa-auth-api
- baseline (207 endpoints)

