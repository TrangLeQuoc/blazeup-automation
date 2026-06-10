"""Attendance API client and response schemas."""

import base64
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from api_clients.base_client import BaseClient


class AttendanceStatusResponse(BaseModel):
    """Current attendance status response."""

    model_config = ConfigDict(extra="allow")

    status: str | None = None
    timestamp: datetime | str | None = None
    clock_in: datetime | str | None = None
    clock_out: datetime | str | None = None
    duration: str | int | float | None = None
    location: str | None = None


class AttendanceClient(BaseClient):
    """Client for attendance and time endpoints."""

    def _employee_params(self) -> dict[str, str]:
        """Return employee query params encoded in the BlazeUp access token."""

        if not self.token:
            return {}
        try:
            payload_part = self.token.split(".")[1]
            padded = payload_part + "=" * (-len(payload_part) % 4)
            payload: dict[str, Any] = json.loads(base64.urlsafe_b64decode(padded))
        except (IndexError, ValueError, json.JSONDecodeError):
            return {}

        employee = payload.get("employee")
        if isinstance(employee, dict):
            employee_id = employee.get("_id") or employee.get("id")
        else:
            employee_id = employee
        return {"employee": str(employee_id)} if employee_id else {}

    async def status(self, expected_status: int = 200) -> AttendanceStatusResponse:
        """Return the current attendance/work status."""

        response = await self.get(
            "/time-api/attendances/status",
            params=self._employee_params(),
            expected_status=expected_status,
        )
        payload = response.json()
        return AttendanceStatusResponse.model_validate(payload.get("data", payload))

    async def raw_status(self, expected_status: int | tuple[int, ...] = 200, **params: Any) -> Any:
        """Return the raw attendance status response for negative tests."""

        request_params = self._employee_params()
        request_params.update(
            {key: str(value) for key, value in params.items() if value is not None}
        )
        return await self.get(
            "/time-api/attendances/status",
            params=request_params,
            expected_status=expected_status,
        )

    async def today(self, expected_status: int = 200) -> AttendanceStatusResponse:
        """Return today's attendance state."""

        return await self.status(expected_status=expected_status)
