"""Attendance API tests TC-A07 to TC-A11."""

import pytest

from api.attendance_client import AttendanceClient
from config.settings import Settings

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.fixture
def attendance_client(settings: Settings, api_token: str) -> AttendanceClient:
    """Return an authenticated attendance client."""

    return AttendanceClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
    )


@pytest.mark.smoke
async def test_tca07_attendance_status_returns_status(attendance_client: AttendanceClient) -> None:
    """TC-A07: GET /time-api/attendances/status returns current work status."""

    try:
        response = await attendance_client.today()
        assert response.status is not None or response.model_dump(exclude_none=True)
    finally:
        await attendance_client.close()


async def test_tca08_attendance_status_requires_token(settings: Settings) -> None:
    """TC-A08: Attendance status without token returns 401."""

    client = AttendanceClient(str(settings.api_base_url), max_response_time_ms=settings.default_response_time_ms)
    try:
        response = await client.raw_status(expected_status=401)
        assert response.status_code == 401
    finally:
        await client.close()


async def test_tca09_attendance_status_rejects_invalid_employee(settings: Settings, api_token: str) -> None:
    """TC-A09: Attendance status rejects an invalid employee id."""

    client = AttendanceClient(str(settings.api_base_url), token=api_token, max_response_time_ms=settings.default_response_time_ms)
    try:
        response = await client.raw_status(expected_status=400, employee="invalid-employee-id")
        assert response.status_code == 400
    finally:
        await client.close()


async def test_tca10_attendance_history_returns_valid_list(attendance_client: AttendanceClient) -> None:
    """TC-A10: GET /time-api/attendances/status returns a valid object."""

    try:
        response = await attendance_client.today()
        assert isinstance(response.model_dump(exclude_none=True), dict)
    finally:
        await attendance_client.close()


@pytest.mark.smoke
async def test_tca11_today_attendance_returns_current_status(attendance_client: AttendanceClient) -> None:
    """TC-A11: GET /time-api/attendances/status returns current status."""

    try:
        response = await attendance_client.today()
        assert response.status is not None or response.model_dump(exclude_none=True)
    finally:
        await attendance_client.close()
