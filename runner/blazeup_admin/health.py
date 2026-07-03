#!/usr/bin/env python3
"""Health-check for blazeup_admin (SA) backend services.

Probes each service's /health endpoint against THIS domain's API_BASE_URL.

Usage:
    python -m runner.blazeup_admin.health
"""

import os
import sys
from pathlib import Path

# Set domain BEFORE importing settings so the correct .env (API_BASE_URL) loads.
os.environ.setdefault("BLAZEUP_DOMAIN", "blazeup_admin")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

if __name__ == "__main__":
    from config.settings import get_settings
    from utils.health_check import check_services, discover_services, extra_services

    # Extra services (monitored even without an API client) come from
    # config/blazeup_admin/config.yaml → `services:`. Auto-discovered ones added on top.
    settings = get_settings()
    services = discover_services("blazeup_admin") | set(extra_services("blazeup_admin"))
    sys.exit(check_services("blazeup_admin", str(settings.api_base_url), services))
