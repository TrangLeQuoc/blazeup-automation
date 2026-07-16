#!/usr/bin/env python3
"""Health-check for BlazeUp backend services.

Probes each service's /health endpoint against API_BASE_URL.

Usage:
    python -m runner.blazeup.health
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

if __name__ == "__main__":
    from config.settings import get_settings
    from utils.health_check import check_services, discover_services, extra_services

    # Extra services (monitored even without an API client) come from
    # config/blazeup/config.yaml → `services:`. Auto-discovered ones added on top.
    settings = get_settings()
    services = discover_services("blazeup") | set(extra_services("blazeup"))
    sys.exit(check_services("blazeup", str(settings.api_base_url), services))
