"""Central registry mapping numeric TC IDs to pytest nodes.  (AUTO-GENERATED — do not edit)

TC ID Encoding
--------------
New-style  :  {type}{project}{module:02d}{section:02d}{seq:02d}
              type 1=UI / 0=API   project 1=partner 2=admin
              module/section are per-domain. The project digit keeps IDs unique
              across projects even when they share a module name.

Legacy     :  1001-1999 = UI demo   1-99 = API demo   (legacy demo suite)

Traceability
------------
tc_string  links each registry entry back to the TestcaseId column in
Partner_Platform_Test_Plan.xlsx.  Empty string for legacy demo tests.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TestCase:
    """Metadata for a single automation test case."""

    tc_id:     int
    tc_string: str                        # Excel TestcaseId  e.g. PARTNER_UI_DASHBOARD_001
    type:      Literal["api", "ui"]
    module:    str
    title:     str
    test_path: str
    test_func: str
    markers:   list[str] = field(default_factory=list)
    priority:  Literal["P1", "P2", "P3"] = "P2"

    @property
    def node_id(self) -> str:
        return f"{self.test_path}::{self.test_func}"


TC_REGISTRY: dict[int, TestCase] = {
    2060101: TestCase(2060101, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_001", "api", "partner", "GET internal partners list - SA filters are applied.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_001", ['api', 'regression'], "P2"),
    2060102: TestCase(2060102, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002", "api", "partner", "POST create internal partner - a pending account is created.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_002", ['api', 'regression'], "P2"),
    2060103: TestCase(2060103, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_003", "api", "partner", "POST partner approve - activation + approval event are created.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_003", ['api', 'regression'], "P2"),
    2060104: TestCase(2060104, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_004", "api", "partner", "partner application decline - mandatory reason is audit logged.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_004", ['api', 'regression'], "P2"),
    2060105: TestCase(2060105, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_005", "api", "partner", "tier changed event - published so portal/analytics can refresh.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_005", ['api', 'regression'], "P2"),
    2060110: TestCase(2060110, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_010", "api", "partner", "certification earned - granted, listed, and event published.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_010", ['api', 'regression'], "P2"),
    2060111: TestCase(2060111, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_011", "api", "partner", "list with invalid pagination - graceful 4xx, never 5xx.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_011", ['api', 'regression'], "P2"),
    2060112: TestCase(2060112, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_012", "api", "partner", "create with invalid/missing fields - 400 + field errors.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_012", ['api', 'regression'], "P2"),
    2060113: TestCase(2060113, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_013", "api", "partner", "approve invalid/illegal-state - rejected with a clear error.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_013", ['api', 'regression'], "P2"),
    2060114: TestCase(2060114, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_014", "api", "partner", "deactivate invalid id - rejected; repeat is idempotent.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_014", ['api', 'regression'], "P2"),
    2060115: TestCase(2060115, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_015", "api", "partner", "change tier with invalid input - rejected with a clear error.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_015", ['api', 'regression'], "P2"),
    2060120: TestCase(2060120, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_020", "api", "partner", "grant certification invalid input - rejected with a clear error.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_020", ['api', 'regression'], "P2"),
    2060121: TestCase(2060121, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_021", "api", "partner", "duplicate partner (same email) - rejected, no second account.", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_021", ['api', 'regression'], "P2"),
    2060122: TestCase(2060122, "PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_022", "api", "partner", "re-grant same certification - must not duplicate (idempotent or 409).", "tests/blazeup_admin/api/partner/test_sa_partners.py", "test_partner_api_partner_account_management_022", ['api', 'regression', 'be_gap'], "P2"),
    2060201: TestCase(2060201, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_001", "api", "partner", "register a partner deal - deal is created (registered).", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_001", ['api', 'regression'], "P2"),
    2060202: TestCase(2060202, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_002", "api", "partner", "register reseller deal - billing model 'reseller' is stored.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_002", ['api', 'regression'], "P2"),
    2060203: TestCase(2060203, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_003", "api", "partner", "register co-sell deal - co-sell metadata is stored.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_003", ['api', 'regression'], "P2"),
    2060204: TestCase(2060204, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_004", "api", "partner", "register deal for an existing prospect - conflict raised.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_004", ['api', 'regression'], "P2"),
    2060208: TestCase(2060208, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_008", "api", "partner", "internal deal approve - approved + rate/rate-table version stamped.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_008", ['api', 'regression', 'be_gap'], "P2"),
    2060209: TestCase(2060209, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_009", "api", "partner", "resolve conflict - decision and reasoning are immutable.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_009", ['api', 'regression'], "P2"),
    2060210: TestCase(2060210, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_010", "api", "partner", "deal approved event - published (CRM sync is downstream).", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_010", ['api', 'regression'], "P2"),
    2060213: TestCase(2060213, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_013", "api", "partner", "resolve conflict (prospect confirmation) - confirmed partner wins.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_013", ['api', 'regression'], "P2"),
    2060216: TestCase(2060216, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_016", "api", "partner", "extend deal protection (SA manual action) - window pushed out + reasoning recorded.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_016", ['api', 'regression'], "P2"),
    2060219: TestCase(2060219, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_019", "api", "partner", "SA marks an approved deal as lost - status 'lost'.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_019", ['api', 'regression'], "P2"),
    2060220: TestCase(2060220, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_020", "api", "partner", "SA retrieves a single deal by id - full record returned.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_020", ['api', 'regression'], "P2"),
    2060221: TestCase(2060221, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_021", "api", "partner", "register deal invalid/missing fields - rejected with 400.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_021", ['api', 'regression', 'be_gap'], "P2"),
    2060222: TestCase(2060222, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_022", "api", "partner", "duplicate deal by the SAME partner - rejected, no second deal.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_022", ['api', 'regression'], "P2"),
    2060228: TestCase(2060228, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_028", "api", "partner", "approve invalid/illegal-state deal - rejected with a clear error.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_028", ['api', 'regression'], "P2"),
    2060229: TestCase(2060229, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_029", "api", "partner", "resolve-conflict invalid input - rejected with a clear error.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_029", ['api', 'regression'], "P2"),
    2060230: TestCase(2060230, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_030", "api", "partner", "extend-protection invalid input - rejected with a clear error.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_030", ['api', 'regression'], "P2"),
    2060231: TestCase(2060231, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_031", "api", "partner", "get deal by invalid id - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_031", ['api', 'regression'], "P2"),
    2060232: TestCase(2060232, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_032", "api", "partner", "lose deal invalid/illegal-state - rejected (4xx).", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_032", ['api', 'regression'], "P2"),
    2060233: TestCase(2060233, "PARTNER_API_DEAL_REGISTRATION_PIPELINE_033", "api", "partner", "extend-protection repeat is ADDITIVE (idempotency probe).", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_registration_pipeline_033", ['api', 'regression'], "P2"),
    2060401: TestCase(2060401, "PARTNER_API_TERRITORIES_001", "api", "partner", "SA assigns a territory to a partner - saved with fields + effective dates.", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_001", ['api', 'regression'], "P2"),
    2060402: TestCase(2060402, "PARTNER_API_TERRITORIES_002", "api", "partner", "SA lists territories with filters - paginated, scoped, filterable.", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_002", ['api', 'regression'], "P2"),
    2060403: TestCase(2060403, "PARTNER_API_TERRITORIES_003", "api", "partner", "SA retrieves a single territory by id - full detail.", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_003", ['api', 'regression'], "P2"),
    2060404: TestCase(2060404, "PARTNER_API_TERRITORIES_004", "api", "partner", "SA removes a territory assignment - removed and no longer retrievable.", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_004", ['api', 'regression'], "P2"),
    2060411: TestCase(2060411, "PARTNER_API_TERRITORIES_011", "api", "partner", "assign territory invalid/missing fields - rejected with 400.", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_011", ['api', 'regression'], "P2"),
    2060412: TestCase(2060412, "PARTNER_API_TERRITORIES_012", "api", "partner", "exclusive territory conflict - a 2nd partner can't take a held exclusive country.", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_012", ['api', 'regression'], "P2"),
    2060413: TestCase(2060413, "PARTNER_API_TERRITORIES_013", "api", "partner", "list territories invalid filter/pagination - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_013", ['api', 'regression'], "P2"),
    2060414: TestCase(2060414, "PARTNER_API_TERRITORIES_014", "api", "partner", "get territory with invalid id - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_014", ['api', 'regression'], "P2"),
    2060415: TestCase(2060415, "PARTNER_API_TERRITORIES_015", "api", "partner", "delete territory invalid/already-removed - rejected (4xx).", "tests/blazeup_admin/api/partner/test_sa_territories.py", "test_partner_api_territories_015", ['api', 'regression'], "P2"),
    2060502: TestCase(2060502, "PARTNER_API_CERTIFICATIONS_SA_002", "api", "partner", "SA revokes a partner certification - cert becomes 'revoked'.", "tests/blazeup_admin/api/partner/test_sa_certifications.py", "test_partner_api_certifications_sa_002", ['api', 'regression'], "P2"),
    2060503: TestCase(2060503, "PARTNER_API_CERTIFICATIONS_SA_003", "api", "partner", "SA lists a partner team's certifications - well-formed, filterable, scoped.", "tests/blazeup_admin/api/partner/test_sa_certifications.py", "test_partner_api_certifications_sa_003", ['api', 'regression'], "P2"),
    2060504: TestCase(2060504, "PARTNER_API_CERTIFICATIONS_SA_004", "api", "partner", "SA lists certifications expiring soon - expiringWithinDays filter.", "tests/blazeup_admin/api/partner/test_sa_certifications.py", "test_partner_api_certifications_sa_004", ['api', 'regression'], "P2"),
    2060512: TestCase(2060512, "PARTNER_API_CERTIFICATIONS_SA_012", "api", "partner", "revoke certification invalid input/state - rejected with 4xx.", "tests/blazeup_admin/api/partner/test_sa_certifications.py", "test_partner_api_certifications_sa_012", ['api', 'regression'], "P2"),
    2060513: TestCase(2060513, "PARTNER_API_CERTIFICATIONS_SA_013", "api", "partner", "list partner certifications invalid filter/pagination - graceful, never 5xx.", "tests/blazeup_admin/api/partner/test_sa_certifications.py", "test_partner_api_certifications_sa_013", ['api', 'regression'], "P2"),
    2060514: TestCase(2060514, "PARTNER_API_CERTIFICATIONS_SA_014", "api", "partner", "list SA certifications invalid filter/pagination - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_certifications.py", "test_partner_api_certifications_sa_014", ['api', 'regression'], "P2"),
    2060601: TestCase(2060601, "PARTNER_API_AUDIT_LOG_001", "api", "partner", "SA lists audit log entries - paginated, filterable, well-formed.", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_001", ['api', 'regression'], "P2"),
    2060602: TestCase(2060602, "PARTNER_API_AUDIT_LOG_002", "api", "partner", "SA retrieves audit-log KPI stats - 24h counts + chain integrity.", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_002", ['api', 'regression'], "P2"),
    2060603: TestCase(2060603, "PARTNER_API_AUDIT_LOG_003", "api", "partner", "SA exports the audit log as JSON or CSV (within the 10k-row cap).", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_003", ['api', 'regression'], "P2"),
    2060604: TestCase(2060604, "PARTNER_API_AUDIT_LOG_004", "api", "partner", "SA retrieves a single audit-log entry by id - full detail.", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_004", ['api', 'regression'], "P2"),
    2060605: TestCase(2060605, "PARTNER_API_AUDIT_LOG_005", "api", "partner", "list audit logs with invalid pagination/filter - graceful 4xx, never 5xx.", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_005", ['api', 'regression'], "P2"),
    2060606: TestCase(2060606, "PARTNER_API_AUDIT_LOG_006", "api", "partner", "export with invalid format/filter - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_006", ['api', 'regression'], "P2"),
    2060607: TestCase(2060607, "PARTNER_API_AUDIT_LOG_007", "api", "partner", "get audit entry with invalid id - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_audit_logs.py", "test_partner_api_audit_log_007", ['api', 'regression'], "P2"),
    2060701: TestCase(2060701, "PARTNER_API_PARTNER_USERS_001", "api", "partner", "SA lists portal users for a partner - users with roles, no secret leak.", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_001", ['api', 'regression'], "P2"),
    2060702: TestCase(2060702, "PARTNER_API_PARTNER_USERS_002", "api", "partner", "SA invites a partner-portal user - user created with role + hand-off credential.", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_002", ['api', 'regression'], "P2"),
    2060703: TestCase(2060703, "PARTNER_API_PARTNER_USERS_003", "api", "partner", "SA resets a partner-portal user's password - fresh credential, repeatable.", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_003", ['api', 'regression'], "P2"),
    2060711: TestCase(2060711, "PARTNER_API_PARTNER_USERS_011", "api", "partner", "list partner-users invalid pagination/filter - graceful, never 5xx.", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_011", ['api', 'regression'], "P2"),
    2060712: TestCase(2060712, "PARTNER_API_PARTNER_USERS_012", "api", "partner", "invite partner-user invalid/missing fields - rejected with 400.", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_012", ['api', 'regression'], "P2"),
    2060713: TestCase(2060713, "PARTNER_API_PARTNER_USERS_013", "api", "partner", "invite the same email twice - must not create a duplicate user.", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_013", ['api', 'regression', 'be_gap'], "P2"),
    2060714: TestCase(2060714, "PARTNER_API_PARTNER_USERS_014", "api", "partner", "reset password with invalid id - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_partner_users.py", "test_partner_api_partner_users_014", ['api', 'regression'], "P2"),
    2060801: TestCase(2060801, "PARTNER_API_DASHBOARD_DATA_001", "api", "partner", "partner dashboard stats - KPI schema is returned.", "tests/blazeup_admin/api/partner/test_sa_dashboard_data.py", "test_partner_api_dashboard_data_001", ['api', 'regression'], "P2"),
    2060901: TestCase(2060901, "PARTNER_API_PARTNER_PORTAL_001", "api", "partner", "partner gets its own account profile - details returned.", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_001", ['api', 'regression'], "P2"),
    2060902: TestCase(2060902, "PARTNER_API_PARTNER_PORTAL_002", "api", "partner", "partner retrieves its own deal by id - full record.", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_002", ['api', 'regression'], "P2"),
    2060903: TestCase(2060903, "PARTNER_API_PARTNER_PORTAL_003", "api", "partner", "partner gets its own certifications - active certs listed.", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_003", ['api', 'regression'], "P2"),
    2060904: TestCase(2060904, "PARTNER_API_PARTNER_PORTAL_004", "api", "partner", "partner gets its own commission summary - earned/pending/paid totals.", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_004", ['api', 'regression'], "P2"),
    2060905: TestCase(2060905, "PARTNER_API_PARTNER_PORTAL_005", "api", "partner", "partner gets its own assigned territories - territory list returned.", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_005", ['api', 'regression'], "P2"),
    2060906: TestCase(2060906, "PARTNER_API_PARTNER_PORTAL_006", "api", "partner", "partner gets its own tier commission rates - tier rates returned.", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_006", ['api', 'regression'], "P2"),
    2060912: TestCase(2060912, "PARTNER_API_PARTNER_PORTAL_012", "api", "partner", "get own deal with invalid id - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_012", ['api', 'regression'], "P2"),
    2060913: TestCase(2060913, "PARTNER_API_PARTNER_PORTAL_013", "api", "partner", "own certifications with invalid filter - rejected (4xx, never 5xx).", "tests/blazeup_admin/api/partner/test_sa_partner_portal.py", "test_partner_api_partner_portal_013", ['api', 'regression'], "P2"),
    2061001: TestCase(2061001, "PARTNER_API_AUTH_ACCESS_CONTROL_001", "api", "partner", "valid partner JWT - a partner-scoped request succeeds.", "tests/blazeup_admin/api/partner/test_sa_auth_access_control.py", "test_partner_api_auth_access_control_001", ['api', 'regression'], "P2"),
    2061002: TestCase(2061002, "PARTNER_API_AUTH_ACCESS_CONTROL_002", "api", "partner", "non-partner / missing token on the partner API - 401.", "tests/blazeup_admin/api/partner/test_sa_auth_access_control.py", "test_partner_api_auth_access_control_002", ['api', 'regression'], "P2"),
    2061003: TestCase(2061003, "PARTNER_API_AUTH_ACCESS_CONTROL_003", "api", "partner", "cross-partner access - a partner cannot read another's deal.", "tests/blazeup_admin/api/partner/test_sa_auth_access_control.py", "test_partner_api_auth_access_control_003", ['api', 'regression'], "P2"),
    2061007: TestCase(2061007, "PARTNER_API_AUTH_ACCESS_CONTROL_007", "api", "partner", "valid refresh token - a new access token is issued.", "tests/blazeup_admin/api/partner/test_sa_auth_access_control.py", "test_partner_api_auth_access_control_007", ['api', 'regression'], "P2"),
    2061008: TestCase(2061008, "PARTNER_API_AUTH_ACCESS_CONTROL_008", "api", "partner", "logout - the refresh token is invalidated.", "tests/blazeup_admin/api/partner/test_sa_auth_access_control.py", "test_partner_api_auth_access_control_008", ['api', 'regression'], "P2"),
    2061009: TestCase(2061009, "PARTNER_API_AUTH_ACCESS_CONTROL_009", "api", "partner", "change password - new credentials work, old fail.", "tests/blazeup_admin/api/partner/test_sa_auth_access_control.py", "test_partner_api_auth_access_control_009", ['api', 'regression'], "P2"),
    2061101: TestCase(2061101, "PARTNER_API_DEAL_APPROVAL_QUEUE_001", "api", "partner", "SA rejects a registered deal - rejection persisted.", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_approval_queue_001", ['api', 'regression'], "P2"),
    2061111: TestCase(2061111, "PARTNER_API_DEAL_APPROVAL_QUEUE_011", "api", "partner", "reject invalid/illegal-state deal - rejected (4xx).", "tests/blazeup_admin/api/partner/test_sa_deals.py", "test_partner_api_deal_approval_queue_011", ['api', 'regression'], "P2"),
    2061201: TestCase(2061201, "PARTNER_API_PIPELINE_MANAGEMENT_001", "api", "partner", "partner lists deals - only its OWN deals are returned.", "tests/blazeup_admin/api/partner/test_sa_pipeline_management.py", "test_partner_api_pipeline_management_001", ['api', 'regression'], "P2"),
    2061202: TestCase(2061202, "PARTNER_API_PIPELINE_MANAGEMENT_002", "api", "partner", "partner lists deals with a status filter - filter applied.", "tests/blazeup_admin/api/partner/test_sa_pipeline_management.py", "test_partner_api_pipeline_management_002", ['api', 'regression'], "P2"),
    2061211: TestCase(2061211, "PARTNER_API_PIPELINE_MANAGEMENT_011", "api", "partner", "deals list invalid filter/pagination - graceful, never 5xx.", "tests/blazeup_admin/api/partner/test_sa_pipeline_management.py", "test_partner_api_pipeline_management_011", ['api', 'regression'], "P2"),
    12010101: TestCase(12010101, "SHELL_UI_LOAD_TIME_PAGE_001", "ui", "shell", "every SA Dashboard page loads within budget (navigated via URL).", "tests/blazeup_admin/ui/shell/test_load_time.py", "test_shell_ui_load_time_page_001", ['ui', 'regression'], "P2"),
    12010102: TestCase(12010102, "SHELL_UI_LOAD_TIME_PAGE_002", "ui", "shell", "every SA Dashboard page loads within budget (navigated via NAV).", "tests/blazeup_admin/ui/shell/test_load_time.py", "test_shell_ui_load_time_page_002", ['ui', 'regression'], "P2"),
    12010201: TestCase(12010201, "SHELL_UI_PAGE_LOADS_001", "ui", "shell", "every page loads via direct URL (no MFE fetch error).", "tests/blazeup_admin/ui/shell/test_page_loads.py", "test_shell_ui_page_loads_001", ['ui', 'smoke'], "P2"),
    12010202: TestCase(12010202, "SHELL_UI_PAGE_LOADS_002", "ui", "shell", "every page loads via sidebar NAV click (no MFE fetch error).", "tests/blazeup_admin/ui/shell/test_page_loads.py", "test_shell_ui_page_loads_002", ['ui', 'regression'], "P2"),
    12020101: TestCase(12020101, "DASHBOARD_UI_VISIBLE_001", "ui", "dashboard", "Dashboard shows KPI cards + System Health panel (navigated via URL).", "tests/blazeup_admin/ui/dashboard/test_dashboard.py", "test_dashboard_ui_visible_001", ['ui', 'regression'], "P2"),
}


def get_tc(tc_id: int) -> TestCase:
    if tc_id not in TC_REGISTRY:
        raise KeyError(f"TC {tc_id} does not exist in the registry")
    return TC_REGISTRY[tc_id]


def validate_registry() -> None:
    """Verify that all registered test functions exist (optional utility)."""
    for tc in TC_REGISTRY.values():
        path = Path(tc.test_path)
        if not path.exists():
            print(f"Warning: Test file {tc.test_path} missing for TC {tc.tc_id}")


def list_by_module(module: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]


def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]
