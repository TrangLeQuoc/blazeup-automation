"""General test helpers."""

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return an empty dict when it has no content."""

    with Path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def require_credentials(email: str | None, password: str | None) -> tuple[str, str]:
    """Return credentials or raise a clear skip-friendly error."""

    if not email or not password:
        raise RuntimeError("TEST_EMAIL and TEST_PASSWORD must be configured in .env")
    return email, password

