#!/usr/bin/env python3
"""Swagger drift detector for blazeup_admin services.

Usage:
    python -m runner.blazeup_admin.swagger_check          # compare → show drift
    python -m runner.blazeup_admin.swagger_check --save   # save baseline + CHANGELOG
"""

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("BLAZEUP_DOMAIN", "blazeup_admin")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

if __name__ == "__main__":
    from config.settings import get_settings
    from utils.health_check import discover_services, extra_services
    from utils.swagger_check import check_swagger

    parser = argparse.ArgumentParser(description="Swagger drift detector (blazeup_admin).")
    parser.add_argument(
        "--save", action="store_true", help="Save current spec as baseline + append CHANGELOG."
    )
    args = parser.parse_args()

    # Extra services to track come from config/blazeup_admin/config.yaml → `services:`.
    settings = get_settings()
    services = discover_services("blazeup_admin") | set(extra_services("blazeup_admin"))
    sys.exit(check_swagger("blazeup_admin", str(settings.api_base_url), services, save=args.save))
