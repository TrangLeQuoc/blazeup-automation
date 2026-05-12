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
async def test_tca07_clock_in_returns_timestamp(attendance_client: AttendanceClient) -> None:
    """TC-A07: POST /attendance/clock-in returns 200 and timestamp."""

    try:
        response = await attendance_client.clock_in(location="Office", expected_status=200)
        assert response.timestamp
    finally:
        await attendance_client.close()


async def test_tca08_clock_in_twice_returns_409(settings: Settings, api_token: str) -> None:
    """TC-A08: Clocking in twice returns 409 Conflict."""

    client = AttendanceClient(str(settings.api_base_url), token=api_token, max_response_time_ms=settings.default_response_time_ms)
    try:
        first = await client.post("/attendance/clock-in", json={"location": "Office"}, expected_status=(200, 409))
        second = await client.post("/attendance/clock-in", json={"location": "Office"}, expected_status=409)
        assert second.status_code == 409
        assert first
    finally:
        await client.close()


async def test_tca09_clock_out_returns_duration(settings: Settings, api_token: str) -> None:
    """TC-A09: POST /attendance/clock-out returns duration."""

    client = AttendanceClient(str(settings.api_base_url), token=api_token, max_response_time_ms=settings.default_response_time_ms)
    try:
        await client.post("/attendance/clock-in", json={"location": "Office"}, expected_status=(200, 409))
        response = await client.clock_out(expected_status=200)
        assert response.duration is not None
    finally:
        await client.close()


async def test_tca10_attendance_history_returns_valid_list(attendance_client: AttendanceClient) -> None:
    """TC-A10: GET /attendance/history returns valid list format."""

    try:
        response = await attendance_client.history()
        assert isinstance(response.records, list)
    finally:
        await attendance_client.close()


@pytest.mark.smoke
async def test_tca11_today_attendance_returns_current_status(attendance_client: AttendanceClient) -> None:
    """TC-A11: GET /attendance/today returns current status."""

    try:
        response = await attendance_client.today()
        assert response.status
    finally:
        await attendance_client.close()
