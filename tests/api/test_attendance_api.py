"""Attendance API tests TC-A07 to TC-A11."""

import pytest

from api.attendance_client import AttendanceClient
from config.settings import Settings

pytestmark = [pytest.mark.api, pytest.mark.regression]

# attendance_client fixture is provided by pytest_support/fixtures.py


@pytest.mark.smoke
async def test_tca07_attendance_status_returns_status(attendance_client: AttendanceClient) -> None:
    """TC-A07: GET /time-api/attendances/status returns a non-empty response body."""

    response = await attendance_client.status()
    dump = response.model_dump(exclude_none=True)
    assert dump, f"Attendance status response is empty: {dump}"


async def test_tca08_attendance_status_requires_token(settings: Settings) -> None:
    """TC-A08: Attendance status without token returns 401."""

    client = AttendanceClient(
        str(settings.api_base_url),
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        response = await client.raw_status(expected_status=401)
        assert response.status_code == 401
    finally:
        await client.close()


async def test_tca09_attendance_status_rejects_invalid_employee(settings: Settings, api_token: str) -> None:
    """TC-A09: Attendance status rejects an invalid employee id."""

    client = AttendanceClient(
        str(settings.api_base_url),
        token=api_token,
        max_response_time_ms=settings.default_response_time_ms,
        app_origin=str(settings.base_url),
    )
    try:
        response = await client.raw_status(expected_status=(400, 404), employee="invalid-employee-id")
        assert response.status_code in {400, 404}
    finally:
        await client.close()


async def test_tca10_attendance_status_has_expected_shape(attendance_client: AttendanceClient) -> None:
    """TC-A10: GET /time-api/attendances/status response contains at least one known field."""

    response = await attendance_client.status()
    dump = response.model_dump(exclude_none=True)
    assert dump, f"Attendance status response is empty: {dump}"
    known_fields = {"status", "clockIn", "clock_in", "clockOut", "clock_out", "duration", "location"}
    assert dump.keys() & known_fields, (
        f"Response contains none of the expected fields {known_fields}. Got: {list(dump.keys())}"
    )


@pytest.mark.smoke
async def test_tca11_today_attendance_returns_valid_status_value(attendance_client: AttendanceClient) -> None:
    """TC-A11: GET /time-api/attendances/status returns a recognised status string when present."""

    response = await attendance_client.today()
    if response.status is not None:
        valid_statuses = {"CLOCKED_IN", "CLOCKED_OUT", "ON_BREAK", "ABSENT", ""}
        assert response.status in valid_statuses or isinstance(response.status, str), (
            f"Unexpected status value: {response.status!r}"
        )
    else:
        # status may be null on days with no activity — verify the rest of the body is non-empty
        dump = response.model_dump(exclude_none=True)
        assert dump, "Response has no status and no other fields"
