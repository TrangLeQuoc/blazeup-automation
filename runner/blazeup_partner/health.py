#!/usr/bin/env python3
"""Health-check for blazeup_partner backend services.

Probes each service's /health endpoint against THIS domain's API_BASE_URL.
If the partner API ever moves to its own host, only this domain's .env changes —
the engine and other domains are untouched.

Usage:
    python -m runner.blazeup_partner.health
"""

import os
import sys
from pathlib import Path

# Set domain BEFORE importing settings so the correct .env (API_BASE_URL) loads.
os.environ.setdefault("BLAZEUP_DOMAIN", "blazeup_partner")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Services to monitor even if no API client exists for them yet.
EXTRA_SERVICES: list[str] = ["sa-partners-api"]


if __name__ == "__main__":
    from config.settings import get_settings
    from utils.health_check import check_services, discover_services

    settings = get_settings()
    services = discover_services("blazeup_partner") | set(EXTRA_SERVICES)
    sys.exit(check_services("blazeup_partner", str(settings.api_base_url), services))
