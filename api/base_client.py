"""Base HTTP client with retries, timing assertions, and schema validation."""

import asyncio
import time
from typing import Any, TypeVar

import httpx
from loguru import logger
from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class BaseClient:
    """Reusable async API client for BlazeUp HRMS endpoints."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 30.0,
        max_response_time_ms: int = 2000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.max_response_time_ms = max_response_time_ms
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""

        await self._client.aclose()

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        expected_status: int | tuple[int, ...] | None = None,
        schema: type[SchemaT] | None = None,
        **kwargs: Any,
    ) -> httpx.Response | SchemaT:
        """Send a request, retry 5xx responses, validate timing and optional schema."""

        headers = dict(kwargs.pop("headers", {}) or {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        response: httpx.Response | None = None
        for attempt in range(1, 4):
            started = time.perf_counter()
            response = await self._client.request(method, endpoint, headers=headers, **kwargs)
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            response.extensions["elapsed_ms"] = elapsed_ms
            logger.info("{} {} -> {} ({}ms)", method.upper(), endpoint, response.status_code, elapsed_ms)

            if response.status_code < 500 or attempt == 3:
                break
            await asyncio.sleep(attempt)

        if response is None:
            raise RuntimeError("HTTP request did not produce a response")

        assert response.extensions["elapsed_ms"] < self.max_response_time_ms, (
            f"Response time {response.extensions['elapsed_ms']}ms exceeded "
            f"{self.max_response_time_ms}ms"
        )
        if expected_status is not None:
            allowed = (expected_status,) if isinstance(expected_status, int) else expected_status
            assert response.status_code in allowed, (
                f"Expected status {allowed}, got {response.status_code}: {response.text}"
            )
        if schema is not None:
            return schema.model_validate(response.json())
        return response

    async def get(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a GET request."""

        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a POST request."""

        return await self.request("POST", endpoint, **kwargs)

