"""Base HTTP client with retries, timing assertions, and schema validation."""

import asyncio
import time
from typing import Any, TypeVar
from urllib.parse import urlparse

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
        self.base_url = self._normalize_base_url(base_url)
        self.token = token
        self.max_response_time_ms = max_response_time_ms
        self.app_origin = (app_origin or self.base_url).rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        """Protect API tests from accidentally using the tenant UI host as API host."""

        normalized = base_url.rstrip("/")
        parsed = urlparse(normalized)
        if parsed.netloc.lower() == "terralogic.blazeup.ai":
            return "https://api.prod.blazeup.ai"
        return normalized

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
        headers.setdefault("Origin", self.app_origin)
        headers.setdefault("Referer", f"{self.app_origin}/")
        headers.setdefault("X-PLATFORM", "WEB")
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        # Log the outgoing request at DEBUG level (body masked for sensitive keys)
        json_body = kwargs.get("json") or kwargs.get("data")
        if json_body and isinstance(json_body, dict):
            masked = {
                k: ("***" if any(s in k.lower() for s in ("password", "token", "secret", "key", "pwd")) else v)
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
                logger.warning("{} {} transport error on attempt {}/3", method.upper(), endpoint, attempt)
                if attempt == 3:
                    raise
                await asyncio.sleep(attempt)
                continue
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            response.extensions["elapsed_ms"] = elapsed_ms
            logger.info("{} {} | {} ({}ms)", method.upper(), endpoint, response.status_code, elapsed_ms)

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
