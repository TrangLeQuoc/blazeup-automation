"""Backend services for the blazeup_admin domain — single source of truth.

Used by both the health-check (``health.py``) and the Swagger drift detector
(``swagger_check.py``) so the monitored-service list is defined in ONE place.

Auto-discovery (``utils.health_check.discover_services``) still finds services
referenced by API client code; this list adds services to track even when no
API client references them yet. Keep it in sync with the live platform.
"""

SERVICES: list[str] = [
    "admin-api",
    "compliance-api",
    "connectors",
    "helpplatform-api",
    "sa-auth-api",
    "sa-governance-api",
    "sa-partners-api",
    "sa-plans-api",
    "sa-tenants-api",
    "setting-api",
    "workflow-api",
]
