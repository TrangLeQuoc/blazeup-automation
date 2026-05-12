"""Attendance API client and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from api.base_client import BaseClient


class ClockInResponse(BaseModel):
    """Clock-in response payload."""

    model_config = ConfigDict(extra="allow")

    timestamp: datetime | str
    status: str | None = None
    location: str | None = None


class ClockOutResponse(BaseModel):
    """Clock-out response payload."""

    model_config = ConfigDict(extra="allow")

    timestamp: datetime | str | None = None
    duration: str | int | float
    status: str | None = None


class AttendanceEntry(BaseModel):
    """Single attendance history row."""

    model_config = ConfigDict(extra="allow")

    date: str
    clock_in: datetime | str | None = None
    clock_out: datetime | str | None = None
    duration: str | int | float | None = None
    location: str | None = None


class AttendanceHistoryResponse(BaseModel):
    """Attendance history response."""

    model_config = ConfigDict(extra="allow")

    data: list[AttendanceEntry] | None = None
    items: list[AttendanceEntry] | None = None

    @property
    def records(self) -> list[AttendanceEntry]:
        """Return normalized history records."""

        return self.data or self.items or []


class TodayAttendanceResponse(BaseModel):
    """Current-day attendance status response."""

    model_config = ConfigDict(extra="allow")

    status: str
    clock_in: datetime | str | None = None
    clock_out: datetime | str | None = None
    location: str | None = None


class AttendanceClient(BaseClient):
    """Client for attendance and time endpoints."""

    async def clock_in(self, location: str = "Office", expected_status: int | tuple[int, ...] = 200) -> ClockInResponse:
        """Clock in at the requested location."""

        return await self.post(
            "/attendance/clock-in",
            json={"location": location},
            expected_status=expected_status,
            schema=ClockInResponse,
        )

    async def clock_out(self, expected_status: int | tuple[int, ...] = 200) -> ClockOutResponse:
        """Clock out the current user."""

        return await self.post(
            "/attendance/clock-out",
            expected_status=expected_status,
            schema=ClockOutResponse,
        )

    async def history(self, expected_status: int = 200) -> AttendanceHistoryResponse:
        """Return attendance history."""

        return await self.get(
            "/attendance/history",
            expected_status=expected_status,
            schema=AttendanceHistoryResponse,
        )

    async def today(self, expected_status: int = 200) -> TodayAttendanceResponse:
        """Return today's attendance state."""

        return await self.get(
            "/attendance/today",
            expected_status=expected_status,
            schema=TodayAttendanceResponse,
        )

