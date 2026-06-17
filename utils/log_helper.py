"""Step-based logging helpers for BlazeUp automation tests.

Provides context managers that emit structured STEP log entries and
capture failures with elapsed time — integrated with both loguru (terminal
+ file) and Allure reports.

Usage in async tests (most common)::

    from utils.log_helper import async_step

    async def test_tca01_login(settings, auth_client):
        email, password = require_credentials(...)

        async with async_step("Step 1: Login with valid credentials", email=email):
            response = await auth_client.login(email, password)

        async with async_step("Step 2: Verify bearer token is present"):
            assert response.bearer_token

Usage in sync helpers::

    from utils.log_helper import step

    with step("Step A: Prepare payload", count=5):
        data = build_payload(count=5)

Log levels registered by this module
-------------------------------------
Level    | No | Terminal colour
---------|----|-----------------
STEP     | 21 | cyan bold
START    | 22 | blue bold
PASSED   | 23 | green bold
FAILED   | 24 | red bold
FINISH   | 26 | blue bold

These complement loguru built-ins (INFO=20, SUCCESS=25, WARNING=30, ERROR=40).
"""

import time
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any

import pytest
from loguru import logger

try:
    import allure

    _allure_step = allure.step
except ImportError:  # allure-pytest not installed — degrade to a no-op context

    def _allure_step(_name: str):  # type: ignore[misc]
        from contextlib import nullcontext

        return nullcontext()


# ---------------------------------------------------------------------------
# Register custom log levels once at import time.
# Built-in levels: TRACE=5, DEBUG=10, INFO=20, SUCCESS=25, WARNING=30, ERROR=40
# ---------------------------------------------------------------------------
_CUSTOM_LEVELS: list[tuple[str, int, str, str]] = [
    ("STEP", 21, "<cyan><bold>", ">>"),
    ("START", 22, "<blue><bold>", ">>"),
    ("PASSED", 23, "<green><bold>", "OK"),
    ("FAILED", 24, "<red><bold>", "!!"),
    ("FINISH", 26, "<blue><bold>", "<<"),
]

for _level_name, _level_no, _level_color, _level_icon in _CUSTOM_LEVELS:
    # TypeError = level already registered in this process; ignore on re-import.
    with suppress(TypeError):
        logger.level(_level_name, no=_level_no, color=_level_color, icon=_level_icon)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _fmt_params(params: dict[str, Any]) -> str:
    """Format keyword params as a readable string, masking sensitive keys.

    Sensitive key patterns: password, token, secret, key, pwd.
    """
    if not params:
        return ""
    parts: list[str] = []
    for k, v in params.items():
        if any(s in k.lower() for s in ("password", "token", "secret", "key", "pwd")):
            parts.append(f"{k}=***")
        else:
            parts.append(f"{k}={v!r}")
    return "  [" + ", ".join(parts) + "]"


def ordinal(n: int) -> str:
    """Return the English ordinal for a positive int: 1 -> '1st', 2 -> '2nd', ...

    Used to label each page in a looping test ("Check page 1st: Dashboard ...")
    so the run log reads as an ordered checklist rather than repeated identical
    lines. Handles the 11th/12th/13th special case.
    """
    suffix = "th" if 10 <= (n % 100) <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# ---------------------------------------------------------------------------
# Public context managers
# ---------------------------------------------------------------------------


@contextmanager
def step(name: str, **params: Any) -> Generator[None]:
    """Sync context manager that logs a named test step.

    Emits a STEP-level entry on start.  On failure, emits an ERROR with the
    elapsed time and exception details before re-raising.

    Args:
        name:     Human-readable step description (shown in logs and Allure).
        **params: Optional key=value data appended to the log line.
                  Keys matching ``password``, ``token``, ``secret``, ``key``,
                  or ``pwd`` are automatically masked as ``***``.

    Example::

        with step("Step 1: Build test payload", record_count=100):
            payload = generate_payload(100)
    """
    param_str = _fmt_params(params)
    start = time.perf_counter()
    logger.log("STEP", "{}{}", name, param_str)
    with _allure_step(name):
        try:
            yield
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "  FAIL | {} ({}ms) -- {}: {}",
                name,
                elapsed_ms,
                type(exc).__name__,
                exc,
            )
            raise


@asynccontextmanager
async def async_step(name: str, **params: Any) -> AsyncGenerator[None]:
    """Async context manager that logs a named test step.

    Emits a STEP-level entry on start.  On failure, emits an ERROR with the
    elapsed time and exception details before re-raising.

    Args:
        name:     Human-readable step description (shown in logs and Allure).
        **params: Optional key=value data appended to the log line.
                  Keys matching ``password``, ``token``, ``secret``, ``key``,
                  or ``pwd`` are automatically masked as ``***``.

    Example::

        async with async_step("Step 1: Login", email=email):
            response = await client.login(email, password)
    """
    param_str = _fmt_params(params)
    start = time.perf_counter()
    logger.log("STEP", "{}{}", name, param_str)
    with _allure_step(name):
        try:
            yield
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "  FAIL | {} ({}ms) -- {}: {}",
                name,
                elapsed_ms,
                type(exc).__name__,
                exc,
            )
            raise


# ---------------------------------------------------------------------------
# Multi-item test verdict
# ---------------------------------------------------------------------------


def finalize_checks(
    request: Any,
    failures: list[str],
    total: int,
    *,
    unit: str = "pages",
) -> None:
    """Emit a single per-TC verdict and fail the test when any check failed.

    Use at the end of a test that checks many items in one loop (e.g. all 15
    SA Dashboard pages).  The pattern is::

        failures: list[str] = []
        for section in PAGES:
            logger.log("STEP", "Check page [{}]", section)
            ok = await do_one_check(section)          # never raises — caught here
            if ok:
                logger.info("page [{}] PASSED", section)
            else:
                logger.error("page [{}] FAILED — <reason>", section)
                failures.append(section)
        finalize_checks(request, failures, len(PAGES))

    Why this instead of ``@pytest.mark.parametrize``: one test function then maps
    to exactly ONE test case (one START/FINISH banner, one verdict) instead of N
    look-alike runs.  All items are still checked even if an early one fails
    (soft-collect), and the verdict names exactly which ones failed.

    The verdict string is stored on ``request.node._tc_detail`` so the
    ``tc_logger`` fixture can append it to the PASSED/FAILED banner shown right
    before FINISH.
    """
    if failures:
        detail = f"{len(failures)}/{total} {unit} failed: {', '.join(failures)}"
    else:
        detail = f"all {total} {unit} passed"

    node = getattr(request, "node", None)
    if node is not None:
        node._tc_detail = detail

    if failures:
        pytest.fail(detail, pytrace=False)
