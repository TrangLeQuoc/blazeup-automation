# API Change Log — blazeup

## 2026-07-16 13:10 · workflow-api
- 🟢 ADDED   GET /workflow-api/common/countries
- 🟢 ADDED   GET /workflow-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   GET /workflow-api/common/countries/{countryId}/currency
- 🟢 ADDED   GET /workflow-api/common/countries/{countryId}/states
- 🟢 ADDED   GET /workflow-api/common/currencies
- 🟢 ADDED   GET /workflow-api/instances/{instanceId}/context
- 🟢 ADDED   PATCH /workflow-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   PATCH /workflow-api/common/countries/{countryId}/currency
- 🟢 ADDED   POST /workflow-api/instances/{instanceId}/steps/{stepKey}/complete
- 🟢 ADDED   POST /workflow-api/instances/{instanceId}/steps/{stepKey}/fail
- 🟢 ADDED   POST /workflow-api/instances/{instanceId}/steps/{stepKey}/signal
- 🟢 ADDED   POST /workflow-api/instances/{instanceId}/steps/{stepKey}/submit
- 🔴 REMOVED GET /workflow-api/audit-logs
- 🔴 REMOVED GET /workflow-api/audit-logs/{resourceId}
- 🔴 REMOVED POST /workflow-api/audit-logs
- 🔴 REMOVED POST /workflow-api/instances/{instanceId}/steps/{stepId}/signal
- 🔴 REMOVED POST /workflow-api/instances/{instanceId}/steps/{stepId}/submit

## 2026-07-16 13:10 · setting-api
- 🟢 ADDED   GET /setting-api/cross-entity-authority
- 🟢 ADDED   GET /setting-api/cross-entity-authority/group-roles
- 🟢 ADDED   PATCH /setting-api/cross-entity-authority/{id}/revoke
- 🟢 ADDED   POST /setting-api/cross-entity-authority

## 2026-07-16 13:10 · sa-tenants-api
- 🟢 ADDED   GET /sa-tenants-api/common/countries
- 🟢 ADDED   GET /sa-tenants-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   GET /sa-tenants-api/common/countries/{countryId}/currency
- 🟢 ADDED   GET /sa-tenants-api/common/countries/{countryId}/states
- 🟢 ADDED   GET /sa-tenants-api/common/currencies
- 🟢 ADDED   GET /sa-tenants-api/common/document-template-keys
- 🟢 ADDED   GET /sa-tenants-api/common/form-template-keys
- 🟢 ADDED   GET /sa-tenants-api/common/modules
- 🟢 ADDED   GET /sa-tenants-api/common/trigger-events
- 🟢 ADDED   GET /sa-tenants-api/tenants/check-domain
- 🟢 ADDED   GET /sa-tenants-api/tenants/{id}/blazey-usage
- 🟢 ADDED   GET /sa-tenants-api/tenants/{id}/overview
- 🟢 ADDED   GET /sa-tenants-api/tenants/{id}/support-stats
- 🟢 ADDED   GET /sa-tenants-api/tenants/{id}/support-tickets
- 🟢 ADDED   GET /sa-tenants-api/tenants/{id}/usage
- 🟢 ADDED   PATCH /sa-tenants-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   PATCH /sa-tenants-api/common/countries/{countryId}/currency
- 🟢 ADDED   POST /sa-tenants-api/tenants/{id}/provision/retry

## 2026-07-16 13:10 · sa-plans-api
- 🟢 ADDED   GET /sa-plans-api/common/countries
- 🟢 ADDED   GET /sa-plans-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   GET /sa-plans-api/common/countries/{countryId}/currency
- 🟢 ADDED   GET /sa-plans-api/common/countries/{countryId}/states
- 🟢 ADDED   GET /sa-plans-api/common/currencies
- 🟢 ADDED   GET /sa-plans-api/common/document-template-keys
- 🟢 ADDED   GET /sa-plans-api/common/form-template-keys
- 🟢 ADDED   GET /sa-plans-api/common/modules
- 🟢 ADDED   GET /sa-plans-api/common/trigger-events
- 🟢 ADDED   PATCH /sa-plans-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   PATCH /sa-plans-api/common/countries/{countryId}/currency

## 2026-07-16 13:10 · sa-partners-api
- 🟢 ADDED   GET /sa-partners-api/common/countries
- 🟢 ADDED   GET /sa-partners-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   GET /sa-partners-api/common/countries/{countryId}/currency
- 🟢 ADDED   GET /sa-partners-api/common/countries/{countryId}/states
- 🟢 ADDED   GET /sa-partners-api/common/document-template-keys
- 🟢 ADDED   GET /sa-partners-api/common/form-template-keys
- 🟢 ADDED   GET /sa-partners-api/common/modules
- 🟢 ADDED   GET /sa-partners-api/common/trigger-events
- 🟢 ADDED   GET /sa-partners-api/v1/partner/portal/countries
- 🟢 ADDED   GET /sa-partners-api/v1/partner/portal/modules
- 🟢 ADDED   PATCH /sa-partners-api/common/countries/{countryId}/calling-phone
- 🟢 ADDED   PATCH /sa-partners-api/common/countries/{countryId}/currency
- 🟢 ADDED   POST /sa-partners-api/v1/sa/admin/migrations/partner-account-code-index
- 🟡 CHANGED POST /sa-partners-api/v1/sa/deals/{id}/approve
    · responses: +['200']
- 🟡 CHANGED POST /sa-partners-api/v1/sa/deals/{id}/extend-protection
    · responses: +['200']
- 🟡 CHANGED POST /sa-partners-api/v1/sa/deals/{id}/lose
    · responses: +['200']
- 🟡 CHANGED POST /sa-partners-api/v1/sa/deals/{id}/reject
    · responses: +['200']
- 🟡 CHANGED POST /sa-partners-api/v1/sa/deals/{id}/resolve-conflict
    · responses: +['200']
- 🟡 CHANGED POST /sa-partners-api/v1/sa/deals/{id}/win
    · responses: +['200']

## 2026-07-16 13:10 · sa-auth-api
- 🟢 ADDED   DELETE /sa-auth-api/abac/aliases/{alias}/unassign-user
- 🟢 ADDED   DELETE /sa-auth-api/abac/aliases/{id}
- 🟢 ADDED   DELETE /sa-auth-api/abac/attribute-definitions/{id}
- 🟢 ADDED   DELETE /sa-auth-api/abac/components/{id}
- 🟢 ADDED   DELETE /sa-auth-api/abac/grants/{id}
- 🟢 ADDED   DELETE /sa-auth-api/abac/modules/{id}
- 🟢 ADDED   DELETE /sa-auth-api/abac/policies/{id}
- 🟢 ADDED   DELETE /sa-auth-api/abac/policies/{policyId}/unassign-user/{userId}
- 🟢 ADDED   GET /sa-auth-api/abac-sync/flow-bundle
- 🟢 ADDED   GET /sa-auth-api/abac-sync/snapshot
- 🟢 ADDED   GET /sa-auth-api/abac-sync/sync-rbac/debug
- 🟢 ADDED   GET /sa-auth-api/abac-sync/sync-rbac/fe-modules
- 🟢 ADDED   GET /sa-auth-api/abac/aliases
- 🟢 ADDED   GET /sa-auth-api/abac/aliases/{alias}
- 🟢 ADDED   GET /sa-auth-api/abac/aliases/{alias}/policies
- 🟢 ADDED   GET /sa-auth-api/abac/aliases/{alias}/users
- 🟢 ADDED   GET /sa-auth-api/abac/attribute-definitions
- 🟢 ADDED   GET /sa-auth-api/abac/attribute-definitions/usage
- 🟢 ADDED   GET /sa-auth-api/abac/components
- 🟢 ADDED   GET /sa-auth-api/abac/departments
- 🟢 ADDED   GET /sa-auth-api/abac/enums
- 🟢 ADDED   GET /sa-auth-api/abac/fe-modules
- 🟢 ADDED   GET /sa-auth-api/abac/grants
- 🟢 ADDED   GET /sa-auth-api/abac/grants/alias-counts
- 🟢 ADDED   GET /sa-auth-api/abac/grants/counts
- 🟢 ADDED   GET /sa-auth-api/abac/import-template
- 🟢 ADDED   GET /sa-auth-api/abac/locations
- 🟢 ADDED   GET /sa-auth-api/abac/modules
- 🟢 ADDED   GET /sa-auth-api/abac/my-modules
- 🟢 ADDED   GET /sa-auth-api/abac/my-permissions
- 🟢 ADDED   GET /sa-auth-api/abac/platforms
- 🟢 ADDED   GET /sa-auth-api/abac/policies
- 🟢 ADDED   GET /sa-auth-api/abac/policies/by-user/{userId}
- 🟢 ADDED   GET /sa-auth-api/abac/routes
- 🟢 ADDED   GET /sa-auth-api/abac/sign-in-platforms
- 🟢 ADDED   GET /sa-auth-api/abac/user-abac
- 🟢 ADDED   GET /sa-auth-api/abac/user-aliases/{userId}
- 🟢 ADDED   GET /sa-auth-api/abac/users
- 🟢 ADDED   PATCH /sa-auth-api/abac/aliases/{id}
- 🟢 ADDED   PATCH /sa-auth-api/abac/attribute-definitions/{id}
- 🟢 ADDED   PATCH /sa-auth-api/abac/components/{id}
- 🟢 ADDED   PATCH /sa-auth-api/abac/modules/{id}
- 🟢 ADDED   PATCH /sa-auth-api/abac/policies/{id}
- 🟢 ADDED   POST /sa-auth-api/abac-sync/analyze
- 🟢 ADDED   POST /sa-auth-api/abac-sync/stubs
- 🟢 ADDED   POST /sa-auth-api/abac-sync/sync
- 🟢 ADDED   POST /sa-auth-api/abac-sync/sync-rbac
- 🟢 ADDED   POST /sa-auth-api/abac-sync/sync-user
- 🟢 ADDED   POST /sa-auth-api/abac-sync/sync-user-abac
- 🟢 ADDED   POST /sa-auth-api/abac/aliases
- 🟢 ADDED   POST /sa-auth-api/abac/aliases/{alias}/assign-user
- 🟢 ADDED   POST /sa-auth-api/abac/attribute-definitions
- 🟢 ADDED   POST /sa-auth-api/abac/check-access
- 🟢 ADDED   POST /sa-auth-api/abac/components
- 🟢 ADDED   POST /sa-auth-api/abac/cross-check
- 🟢 ADDED   POST /sa-auth-api/abac/grants
- 🟢 ADDED   POST /sa-auth-api/abac/import
- 🟢 ADDED   POST /sa-auth-api/abac/import/file
- 🟢 ADDED   POST /sa-auth-api/abac/modules
- 🟢 ADDED   POST /sa-auth-api/abac/policies
- 🟢 ADDED   POST /sa-auth-api/abac/policies/{policyId}/assign-user/{userId}
- 🟢 ADDED   POST /sa-auth-api/abac/rebuild-user
- 🟢 ADDED   POST /sa-auth-api/abac/sync-user-claim
- 🔴 REMOVED DELETE /sa-auth-api/dev/abac/aliases/{alias}/unassign-user/{userId}
- 🔴 REMOVED DELETE /sa-auth-api/dev/abac/aliases/{id}
- 🔴 REMOVED DELETE /sa-auth-api/dev/abac/attribute-definitions/{id}
- 🔴 REMOVED DELETE /sa-auth-api/dev/abac/grants/{id}
- 🔴 REMOVED DELETE /sa-auth-api/dev/abac/policies/{id}
- 🔴 REMOVED DELETE /sa-auth-api/dev/abac/policies/{policyId}/unassign-user/{userId}
- 🔴 REMOVED GET /sa-auth-api/dev/abac/aliases
- 🔴 REMOVED GET /sa-auth-api/dev/abac/aliases/{alias}
- 🔴 REMOVED GET /sa-auth-api/dev/abac/aliases/{alias}/policies
- 🔴 REMOVED GET /sa-auth-api/dev/abac/aliases/{alias}/users
- 🔴 REMOVED GET /sa-auth-api/dev/abac/attribute-definitions
- 🔴 REMOVED GET /sa-auth-api/dev/abac/attribute-definitions/usage
- 🔴 REMOVED GET /sa-auth-api/dev/abac/departments
- 🔴 REMOVED GET /sa-auth-api/dev/abac/fe-modules
- 🔴 REMOVED GET /sa-auth-api/dev/abac/flow-bundle
- 🔴 REMOVED GET /sa-auth-api/dev/abac/grants
- 🔴 REMOVED GET /sa-auth-api/dev/abac/grants/alias-counts
- 🔴 REMOVED GET /sa-auth-api/dev/abac/grants/counts
- 🔴 REMOVED GET /sa-auth-api/dev/abac/locations
- 🔴 REMOVED GET /sa-auth-api/dev/abac/my-modules
- 🔴 REMOVED GET /sa-auth-api/dev/abac/my-modules-keys
- 🔴 REMOVED GET /sa-auth-api/dev/abac/my-permissions
- 🔴 REMOVED GET /sa-auth-api/dev/abac/my-permissions-keys
- 🔴 REMOVED GET /sa-auth-api/dev/abac/platforms
- 🔴 REMOVED GET /sa-auth-api/dev/abac/policies
- 🔴 REMOVED GET /sa-auth-api/dev/abac/policies/by-user/{userId}
- 🔴 REMOVED GET /sa-auth-api/dev/abac/sign-in-platforms
- 🔴 REMOVED GET /sa-auth-api/dev/abac/snapshot
- 🔴 REMOVED GET /sa-auth-api/dev/abac/sync-rbac/debug
- 🔴 REMOVED GET /sa-auth-api/dev/abac/user-aliases/{userId}
- 🔴 REMOVED GET /sa-auth-api/dev/abac/users
- 🔴 REMOVED PATCH /sa-auth-api/dev/abac/aliases/{id}
- 🔴 REMOVED PATCH /sa-auth-api/dev/abac/attribute-definitions/{id}
- 🔴 REMOVED PATCH /sa-auth-api/dev/abac/policies/{id}
- 🔴 REMOVED POST /sa-auth-api/abac/sync
- 🔴 REMOVED POST /sa-auth-api/dev/abac/aliases
- 🔴 REMOVED POST /sa-auth-api/dev/abac/aliases/{alias}/assign-user/{userId}
- 🔴 REMOVED POST /sa-auth-api/dev/abac/analyze
- 🔴 REMOVED POST /sa-auth-api/dev/abac/attribute-definitions
- 🔴 REMOVED POST /sa-auth-api/dev/abac/check-access
- 🔴 REMOVED POST /sa-auth-api/dev/abac/grants
- 🔴 REMOVED POST /sa-auth-api/dev/abac/policies
- 🔴 REMOVED POST /sa-auth-api/dev/abac/policies/{policyId}/assign-user/{userId}
- 🔴 REMOVED POST /sa-auth-api/dev/abac/sign-in
- 🔴 REMOVED POST /sa-auth-api/dev/abac/stubs
- 🔴 REMOVED POST /sa-auth-api/dev/abac/sync-rbac
- 🔴 REMOVED POST /sa-auth-api/dev/abac/sync-user
- 🔴 REMOVED POST /sa-auth-api/dev/abac/sync-user-abac
- 🔴 REMOVED POST /sa-auth-api/dev/abac/test-token
- 🔴 REMOVED POST /sa-auth-api/m/sign-in
- 🔴 REMOVED POST /sa-auth-api/otp/request
- 🔴 REMOVED POST /sa-auth-api/otp/verify
- 🔴 REMOVED POST /sa-auth-api/sign-in

## 2026-07-16 13:10 · helpplatform-api
- 🟢 ADDED   GET /helpplatform-api/modules

## 2026-07-16 13:10 · connectors-api
- baseline (160 endpoints)

## 2026-07-16 13:10 · admin-api
- 🟢 ADDED   GET /admin-api/approval-flows-v3/module-bindings/{module}
- 🟡 CHANGED DELETE /admin-api/approval-flows-v3/module-bindings/{module}
    · params: +['campusId']
- 🟡 CHANGED GET /admin-api/approval-admin-v3/active
    · params: +['campusId', 'module']
- 🟡 CHANGED GET /admin-api/approvals-v3
    · params: +['campusId', 'module']

# API Change Log — blazeup_admin

## 2026-07-01 15:36 · workflow-api
- 🟢 ADDED   GET /workflow-api/common/document-template-keys
- 🟢 ADDED   GET /workflow-api/common/form-template-keys
- 🟢 ADDED   GET /workflow-api/common/modules
- 🟢 ADDED   GET /workflow-api/common/trigger-events
- 🔴 REMOVED GET /workflow-api/templates/module/{templateKey}

## 2026-07-01 15:36 · setting-api
- 🟡 CHANGED GET /setting-api/companies
    · params: +['companyId']
- 🟡 CHANGED GET /setting-api/companies/tree
    · params: +['companyId']
- 🟡 CHANGED GET /setting-api/internal/platform-companies
    · params: +['companyId']

## 2026-07-01 15:36 · sa-tenants-api
- 🟢 ADDED   GET /sa-tenants-api/tenants/regions

## 2026-07-01 15:36 · sa-partners-api
- 🟢 ADDED   GET /sa-partners-api/v1/partner/portal/check-domain
- 🟢 ADDED   GET /sa-partners-api/v1/partner/portal/plans
- 🟢 ADDED   GET /sa-partners-api/v1/partner/portal/plans/{planId}
- 🟢 ADDED   PATCH /sa-partners-api/v1/sa/deals/{id}
- 🟢 ADDED   POST /sa-partners-api/v1/partner/auth/mfa/disable
- 🟢 ADDED   POST /sa-partners-api/v1/partner/auth/mfa/setup
- 🔴 REMOVED POST /sa-partners-api/v1/partner/auth/mfa/totp/setup

## 2026-07-01 15:36 · helpplatform-api
- 🟢 ADDED   GET /helpplatform-api/internal/debug/cron-jobs
- 🟢 ADDED   POST /helpplatform-api/internal/debug/scheduled-publish/trigger

## 2026-07-01 15:36 · connectors
- 🟢 ADDED   DELETE /connectors/connectors/accounting/{provider}/invoices/{id}
- 🟢 ADDED   GET /connectors/connectors/accounting/{provider}/customers
- 🟢 ADDED   GET /connectors/connectors/accounting/{provider}/customers/{id}
- 🟢 ADDED   GET /connectors/connectors/accounting/{provider}/invoices
- 🟢 ADDED   GET /connectors/connectors/accounting/{provider}/invoices/{id}
- 🟢 ADDED   GET /connectors/connectors/accounting/{provider}/projects
- 🟢 ADDED   GET /connectors/connectors/accounting/{provider}/projects/{id}
- 🟢 ADDED   GET /connectors/health/deep
- 🟢 ADDED   PATCH /connectors/connectors/accounting/{provider}/customers/{id}
- 🟢 ADDED   PATCH /connectors/connectors/accounting/{provider}/invoices/{id}
- 🟢 ADDED   POST /connectors/connectors/accounting/{provider}/customers
- 🟢 ADDED   POST /connectors/connectors/accounting/{provider}/invoices
- 🔴 REMOVED DELETE /connectors/accounting/{provider}/invoices/{id}
- 🔴 REMOVED DELETE /connectors/connections/{id}
- 🔴 REMOVED DELETE /connectors/crm/{connectionId}/contacts/{id}
- 🔴 REMOVED DELETE /connectors/identity/calendar/{connectionId}/events/{eventId}
- 🔴 REMOVED DELETE /connectors/identity/helpdesk/{connectionId}/tickets/{ticketRef}
- 🔴 REMOVED DELETE /connectors/identity/mail-monitor/{connectionId}/{monitorId}
- 🔴 REMOVED DELETE /connectors/identity/mail/{connectionId}/messages/{messageId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/meetings/{connectionId}/{meetingId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/messages/{messageId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/messages/{messageId}/reactions/{reactionType}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/groups/{groupId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/groups/{groupId}/members/{userId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/{teamId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/members/{membershipId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/messages/{messageId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/messages/{messageId}/reactions/{reactionType}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/members/{membershipId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/webhooks/subscriptions/{subscriptionId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/{connectionId}/drives/webhooks/{subscriptionId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/permissions/{permissionId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/{connectionId}/planner/tasks/{taskId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/{connectionId}/users/{msUserId}
- 🔴 REMOVED DELETE /connectors/identity/ms_graph/{connectionId}/users/{msUserId}/hard
- 🔴 REMOVED DELETE /connectors/identity/multi-tenant/connections/{connectionId}
- 🔴 REMOVED DELETE /connectors/identity/{connectionId}/users/{id}
- 🔴 REMOVED DELETE /connectors/identity/{connectionId}/users/{id}/db
- 🔴 REMOVED DELETE /connectors/identity/{connectionId}/users/{id}/fully
- 🔴 REMOVED DELETE /connectors/sync-configs/{id}
- 🔴 REMOVED GET /connectors/accounting/{provider}/customers
- 🔴 REMOVED GET /connectors/accounting/{provider}/customers/{id}
- 🔴 REMOVED GET /connectors/accounting/{provider}/invoices
- 🔴 REMOVED GET /connectors/accounting/{provider}/invoices/{id}
- 🔴 REMOVED GET /connectors/accounting/{provider}/projects
- 🔴 REMOVED GET /connectors/accounting/{provider}/projects/{id}
- 🔴 REMOVED GET /connectors/connections
- 🔴 REMOVED GET /connectors/connections/{id}
- 🔴 REMOVED GET /connectors/crm/{connectionId}/contacts
- 🔴 REMOVED GET /connectors/crm/{connectionId}/contacts/{id}
- 🔴 REMOVED GET /connectors/devops/{connectionId}/contributor-stats
- 🔴 REMOVED GET /connectors/devops/{connectionId}/pull-requests
- 🔴 REMOVED GET /connectors/devops/{connectionId}/pull-requests/{number}
- 🔴 REMOVED GET /connectors/identity/ai/{connectionId}/analyses
- 🔴 REMOVED GET /connectors/identity/ai/{connectionId}/analyses/stats
- 🔴 REMOVED GET /connectors/identity/ai/{connectionId}/analyses/{id}
- 🔴 REMOVED GET /connectors/identity/calendar/{connectionId}/events
- 🔴 REMOVED GET /connectors/identity/calendar/{connectionId}/events/{eventId}
- 🔴 REMOVED GET /connectors/identity/helpdesk/{connectionId}/tickets
- 🔴 REMOVED GET /connectors/identity/helpdesk/{connectionId}/tickets/customer/{customerEmail}
- 🔴 REMOVED GET /connectors/identity/helpdesk/{connectionId}/tickets/stats
- 🔴 REMOVED GET /connectors/identity/helpdesk/{connectionId}/tickets/{ticketRef}
- 🔴 REMOVED GET /connectors/identity/mail-monitor/{connectionId}
- 🔴 REMOVED GET /connectors/identity/mail-stream/monitors
- 🔴 REMOVED GET /connectors/identity/mail-stream/status
- 🔴 REMOVED GET /connectors/identity/mail/{connectionId}/conversations
- 🔴 REMOVED GET /connectors/identity/mail/{connectionId}/messages
- 🔴 REMOVED GET /connectors/identity/mail/{connectionId}/messages/{messageId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/meetings/{connectionId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/meetings/{connectionId}/{meetingId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/oauth/callback
- 🔴 REMOVED GET /connectors/identity/ms_graph/oauth/done
- 🔴 REMOVED GET /connectors/identity/ms_graph/oauth/status
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/chats
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/members
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/messages
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/groups/{groupId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/groups/{groupId}/members
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/joined
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/messages
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/messages/{messageId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/search/messages
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/status/{teamId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/{teamId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/members
- 🔴 REMOVED GET /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/members
- 🔴 REMOVED GET /connectors/identity/ms_graph/webhooks/notify
- 🔴 REMOVED GET /connectors/identity/ms_graph/webhooks/subscriptions/{connectionId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/webhooks
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/download
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/permissions
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/thumbnails
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/versions
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/search
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/meetings/{meetingId}/recordings
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/meetings/{meetingId}/transcript/ai
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/meetings/{meetingId}/transcripts
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/meetings/{meetingId}/transcripts/{transcriptId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/onedrive/me
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/onedrive/recent
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/onedrive/shared-with-me
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/onedrive/users/{userId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/groups/{groupId}/plans
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/plans/{planId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/plans/{planId}/buckets
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/plans/{planId}/tasks
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/tasks/me
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/tasks/{taskId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/planner/tasks/{taskId}/details
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/reports/active-users
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/reports/mail
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/reports/onedrive
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/reports/sharepoint
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/reports/teams
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/search
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/search/files
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/search/messages
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/search/people
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/sharepoint/files/cached
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/sites
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/sites/root
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/sites/{siteId}
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/sites/{siteId}/drives
- 🔴 REMOVED GET /connectors/identity/ms_graph/{connectionId}/users/{msUserId}
- 🔴 REMOVED GET /connectors/identity/multi-tenant/auth/callback
- 🔴 REMOVED GET /connectors/identity/multi-tenant/connections
- 🔴 REMOVED GET /connectors/identity/multi-tenant/connections/{connectionId}
- 🔴 REMOVED GET /connectors/identity/multi-tenant/invite/pending
- 🔴 REMOVED GET /connectors/identity/multi-tenant/invite/{connectionId}/status
- 🔴 REMOVED GET /connectors/identity/multi-tenant/stats
- 🔴 REMOVED GET /connectors/identity/teams/{connectionId}/chats
- 🔴 REMOVED GET /connectors/identity/teams/{connectionId}/chats/{chatId}/messages
- 🔴 REMOVED GET /connectors/identity/teams/{connectionId}/messages
- 🔴 REMOVED GET /connectors/identity/teams/{connectionId}/messages/{messageId}
- 🔴 REMOVED GET /connectors/identity/{connectionId}/audit-logs/{userId}
- 🔴 REMOVED GET /connectors/identity/{connectionId}/licenses
- 🔴 REMOVED GET /connectors/identity/{connectionId}/offboarding-jobs
- 🔴 REMOVED GET /connectors/identity/{connectionId}/users
- 🔴 REMOVED GET /connectors/identity/{connectionId}/users/{id}
- 🔴 REMOVED GET /connectors/internal/connector-catalogue
- 🔴 REMOVED GET /connectors/internal/connector-catalogue/{provider}
- 🔴 REMOVED GET /connectors/sa/connectors/catalog
- 🔴 REMOVED GET /connectors/sa/connectors/catalog-debug
- 🔴 REMOVED GET /connectors/sa/connectors/catalog/templates
- 🔴 REMOVED GET /connectors/sa/connectors/catalog/{provider}
- 🔴 REMOVED GET /connectors/sa/connectors/catalog/{provider}/audit
- 🔴 REMOVED GET /connectors/sync-configs
- 🔴 REMOVED GET /connectors/sync-configs/{id}
- 🔴 REMOVED GET /connectors/sync-configs/{id}/runs
- 🔴 REMOVED GET /connectors/v1/connectors/installs
- 🔴 REMOVED GET /connectors/v1/connectors/installs/{installId}
- 🔴 REMOVED GET /connectors/v1/connectors/marketplace
- 🔴 REMOVED GET /connectors/v1/connectors/marketplace/{provider}
- 🔴 REMOVED PATCH /connectors/accounting/{provider}/customers/{id}
- 🔴 REMOVED PATCH /connectors/accounting/{provider}/invoices/{id}
- 🔴 REMOVED PATCH /connectors/connections/{id}
- 🔴 REMOVED PATCH /connectors/crm/{connectionId}/contacts/bulk
- 🔴 REMOVED PATCH /connectors/crm/{connectionId}/contacts/{id}
- 🔴 REMOVED PATCH /connectors/identity/ai/{connectionId}/analyses/{id}/dismiss
- 🔴 REMOVED PATCH /connectors/identity/ai/{connectionId}/analyses/{id}/human
- 🔴 REMOVED PATCH /connectors/identity/calendar/{connectionId}/events/{eventId}
- 🔴 REMOVED PATCH /connectors/identity/helpdesk/{connectionId}/tickets/{ticketRef}
- 🔴 REMOVED PATCH /connectors/identity/helpdesk/{connectionId}/tickets/{ticketRef}/resolve
- 🔴 REMOVED PATCH /connectors/identity/mail-monitor/{connectionId}/{monitorId}
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/meetings/{connectionId}/{meetingId}
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/messages/{messageId}
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/teams/{connectionId}/{teamId}
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/messages/{messageId}
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/members/{membershipId}/role
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/move
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/rename
- 🔴 REMOVED PATCH /connectors/identity/ms_graph/{connectionId}/planner/tasks/{taskId}
- 🔴 REMOVED PATCH /connectors/identity/{connectionId}/users/{id}
- 🔴 REMOVED PATCH /connectors/sa/connectors/catalog/{provider}
- 🔴 REMOVED PATCH /connectors/sync-configs/{id}
- 🔴 REMOVED POST /connectors/accounting/{provider}/customers
- 🔴 REMOVED POST /connectors/accounting/{provider}/invoices
- 🔴 REMOVED POST /connectors/connections
- 🔴 REMOVED POST /connectors/credentials/service-account
- 🔴 REMOVED POST /connectors/crm/{connectionId}/contacts
- 🔴 REMOVED POST /connectors/crm/{connectionId}/contacts/bulk
- 🔴 REMOVED POST /connectors/identity/ai/{connectionId}/analyses/{id}/retry
- 🔴 REMOVED POST /connectors/identity/ai/{connectionId}/analyze
- 🔴 REMOVED POST /connectors/identity/calendar/{connectionId}/events
- 🔴 REMOVED POST /connectors/identity/helpdesk/{connectionId}/tickets
- 🔴 REMOVED POST /connectors/identity/mail-monitor/{connectionId}
- 🔴 REMOVED POST /connectors/identity/mail-monitor/{connectionId}/parse-subaddress
- 🔴 REMOVED POST /connectors/identity/mail-monitor/{connectionId}/{monitorId}/poll
- 🔴 REMOVED POST /connectors/identity/mail-monitor/{connectionId}/{monitorId}/reply-to-stamp
- 🔴 REMOVED POST /connectors/identity/mail-stream/poll
- 🔴 REMOVED POST /connectors/identity/mail-stream/renew
- 🔴 REMOVED POST /connectors/identity/mail/{connectionId}/drafts
- 🔴 REMOVED POST /connectors/identity/mail/{connectionId}/drafts/{messageId}/send
- 🔴 REMOVED POST /connectors/identity/mail/{connectionId}/messages
- 🔴 REMOVED POST /connectors/identity/mail/{connectionId}/messages/{messageId}/forward
- 🔴 REMOVED POST /connectors/identity/mail/{connectionId}/messages/{messageId}/reply
- 🔴 REMOVED POST /connectors/identity/ms_graph/meetings/{connectionId}
- 🔴 REMOVED POST /connectors/identity/ms_graph/meetings/{connectionId}/{meetingId}/cancel
- 🔴 REMOVED POST /connectors/identity/ms_graph/oauth/disconnect
- 🔴 REMOVED POST /connectors/identity/ms_graph/oauth/initiate
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/channel
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/chats
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/members
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/messages
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/chats/{chatId}/messages/{messageId}/reactions
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/groups
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/groups/{groupId}/members
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/members
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/messages
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/status/{teamId}/resolve
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/team
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/members
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/messages/{messageId}/reactions
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/channels/{channelId}/messages/{messageId}/replies
- 🔴 REMOVED POST /connectors/identity/ms_graph/teams/{connectionId}/{teamId}/invite-guest
- 🔴 REMOVED POST /connectors/identity/ms_graph/webhooks/notify
- 🔴 REMOVED POST /connectors/identity/ms_graph/webhooks/subscriptions
- 🔴 REMOVED POST /connectors/identity/ms_graph/webhooks/subscriptions/{subscriptionId}/renew
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/adaptive-cards/approval
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/adaptive-cards/chat/{chatId}
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/adaptive-cards/notification
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/adaptive-cards/teams/{teamId}/channels/{channelId}
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/copy
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/permissions
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/preview
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/share
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/files/{itemId}/versions/{versionId}/restore
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/folders
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/sync
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/upload
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/upload-session
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/drives/{driveId}/webhooks
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/planner/plans
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/planner/plans/{planId}/buckets
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/planner/tasks
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/planner/tasks/bulk
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/users
- 🔴 REMOVED POST /connectors/identity/ms_graph/{connectionId}/users/invite
- 🔴 REMOVED POST /connectors/identity/multi-tenant/auth/initiate
- 🔴 REMOVED POST /connectors/identity/multi-tenant/invite
- 🔴 REMOVED POST /connectors/identity/teams/{connectionId}/channel
- 🔴 REMOVED POST /connectors/identity/teams/{connectionId}/chats/{chatId}/messages
- 🔴 REMOVED POST /connectors/identity/teams/{connectionId}/members
- 🔴 REMOVED POST /connectors/identity/teams/{connectionId}/messages
- 🔴 REMOVED POST /connectors/identity/teams/{connectionId}/team
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users/{userId}/assign-license
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users/{userId}/disable
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users/{userId}/enable
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users/{userId}/reset-password
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users/{userId}/revoke-sessions
- 🔴 REMOVED POST /connectors/identity/{connectionId}/users/{userId}/tap
- 🔴 REMOVED POST /connectors/internal/credentials/oauth/install-config
- 🔴 REMOVED POST /connectors/internal/credentials/oauth/test/start
- 🔴 REMOVED POST /connectors/internal/credentials/upsert
- 🔴 REMOVED POST /connectors/internal/test-invoke
- 🔴 REMOVED POST /connectors/sa/connectors/catalog
- 🔴 REMOVED POST /connectors/sa/connectors/catalog/{provider}/transitions
- 🔴 REMOVED POST /connectors/sync-configs
- 🔴 REMOVED POST /connectors/sync-configs/{id}/pause
- 🔴 REMOVED POST /connectors/sync-configs/{id}/resume
- 🔴 REMOVED POST /connectors/sync-configs/{id}/trigger
- 🔴 REMOVED POST /connectors/v1/connectors/installs
- 🔴 REMOVED POST /connectors/v1/connectors/installs/{installId}/actions

## 2026-07-01 15:36 · admin-api
- 🟢 ADDED   DELETE /admin-api/delegations-v3/{id}
- 🟢 ADDED   GET /admin-api/approvals-v3
- 🟢 ADDED   GET /admin-api/delegations-v3/history
- 🟢 ADDED   PATCH /admin-api/delegations-v3/{id}
- 🟢 ADDED   POST /admin-api/approval-admin-v3/{requestId}/steps/{stepId}/sla
- 🟢 ADDED   POST /admin-api/approvals-v3/action
- 🟢 ADDED   POST /admin-api/approvals-v3/trigger
- 🟢 ADDED   POST /admin-api/delegations-v3
- 🔴 REMOVED POST /admin-api/approval-admin-v3/{requestId}/steps/{stepId}/sla/pause
- 🔴 REMOVED POST /admin-api/approval-admin-v3/{requestId}/steps/{stepId}/sla/resume
- 🔴 REMOVED POST /admin-api/approval-flows-v3/{id}/publish

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

