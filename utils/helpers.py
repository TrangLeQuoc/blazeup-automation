"""General test helpers."""

import pytest


def require_credentials(email: str | None, password: str | None) -> tuple[str, str]:
    """Return credentials or skip the test with a clear message if not configured."""

    if not email or not password:
        pytest.skip("TEST_EMAIL and TEST_PASSWORD must be set in .env to run this test")
    return email, password
