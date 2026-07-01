"""General test helpers."""

import pytest


def blocked_reason(exc: BaseException) -> str:
    """Classify a precondition/auth failure into a short BLOCKED reason.

    A failure to establish a precondition (shared login, minted partner session,
    a required service) is an ENVIRONMENT problem, not a defect in the feature
    under test — callers report it as BLOCKED (skip message prefixed ``BLOCKED:``),
    never FAILED. This only builds the human-readable reason string.
    """
    text = str(exc)
    low = text.lower()
    first = text.splitlines()[0][:160] if text else ""
    if any(s in low for s in ("502", "503", "504", "bad gateway", "service unavailable")):
        return f"service unavailable (5xx): {first}"
    if any(s in low for s in ("connect", "timeout", "max retries", "getaddrinfo", "unreachable")):
        return f"service unreachable: {first}"
    if "invalid credentials" in low or "got 401" in low or "unauthorized" in low:
        return f"auth rejected (credentials/env): {first}"
    return f"precondition failed: {first}"


def require_credentials(email: str | None, password: str | None) -> tuple[str, str]:
    """Return credentials or skip the test with a clear message if not configured."""

    if not email or not password:
        pytest.skip("TEST_EMAIL and TEST_PASSWORD must be set in .env to run this test")
    return email, password
