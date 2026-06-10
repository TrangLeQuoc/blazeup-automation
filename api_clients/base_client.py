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
        app_origin: str | None = None,
    ) -> None:
        # Trailing slash ensures httpx appends endpoint paths correctly
        # when base_url contains a sub-path (e.g. https://host/api/v1/).
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self.max_response_time_ms = max_response_time_ms
        self.app_origin = (app_origin or base_url).rstrip("/")
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

        # Strip leading "/" so the endpoint is always relative to base_url.
        # httpx treats a leading "/" as an absolute path (RFC 3986), which
        # would drop any path prefix in base_url (e.g. /api/v1).
        endpoint = endpoint.lstrip("/")

        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Origin", self.app_origin)
        headers.setdefault("Referer", f"{self.app_origin}/")
        headers.setdefault("X-PLATFORM", "WEB")
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        # Log the outgoing request at DEBUG level (body masked for sensitive keys)
        json_body = kwargs.get("json") or kwargs.get("data")
        if json_body and isinstance(json_body, dict):
            masked = {
                k: (
                    "***"
                    if any(s in k.lower() for s in ("password", "token", "secret", "key", "pwd"))
                    else v
                )
                for k, v in json_body.items()
            }
            logger.debug("--> {} {}  body={}", method.upper(), endpoint, masked)
        else:
            logger.debug("--> {} {}", method.upper(), endpoint)

        response: httpx.Response | None = None
        for attempt in range(1, 4):
            started = time.perf_counter()
            try:
                response = await self._client.request(method, endpoint, headers=headers, **kwargs)
            except httpx.TransportError:
                logger.warning(
                    "{} {} transport error on attempt {}/3", method.upper(), endpoint, attempt
                )
                if attempt == 3:
                    raise
                await asyncio.sleep(attempt)
                continue
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            response.extensions["elapsed_ms"] = elapsed_ms
            logger.info(
                "{} {} | {} ({}ms)", method.upper(), endpoint, response.status_code, elapsed_ms
            )

            if response.status_code < 500 or attempt == 3:
                break
            await asyncio.sleep(attempt)

        if response is None:
            raise RuntimeError("HTTP request did not produce a response")

        elapsed_ms = response.extensions["elapsed_ms"]
        if elapsed_ms >= self.max_response_time_ms:
            logger.warning(
                "SLOW: {} {} took {}ms (limit {}ms)",
                method.upper(),
                endpoint,
                elapsed_ms,
                self.max_response_time_ms,
            )
        if expected_status is not None:
            allowed = (expected_status,) if isinstance(expected_status, int) else expected_status
            assert response.status_code in allowed, (
                f"Expected status {allowed}, got {response.status_code}: {response.text}"
            )
        if schema is not None:
            payload = response.json()
            if isinstance(payload, dict) and "data" in payload:
                payload = payload["data"]
            return schema.model_validate(payload)
        return response

    async def get(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a GET request."""

        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a POST request."""

        return await self.request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a PUT request (full-resource replace)."""

        return await self.request("PUT", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a PATCH request (partial update)."""

        return await self.request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> httpx.Response | SchemaT:
        """Send a DELETE request."""

        return await self.request("DELETE", endpoint, **kwargs)
