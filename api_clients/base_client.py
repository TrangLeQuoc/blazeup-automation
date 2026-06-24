"""Base HTTP client with retries, timing assertions, and schema validation."""

import asyncio
import json as _json
import time
from contextlib import suppress
from typing import Any, TypeVar

import httpx
from loguru import logger
from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)

# Substrings whose values are masked anywhere in a logged body (request OR
# response) so secrets never reach the console/log file.
_SENSITIVE_KEYS = (
    "password",
    "token",
    "secret",
    "key",
    "pwd",
    "authorization",
    "credential",
)

# Max characters of a payload/response printed inline. Long list responses are
# truncated (with a "+N chars" marker) so the log stays readable.
_BODY_PREVIEW_LIMIT = 1000

# HTTP methods that are safe to retry: a retry can never create a duplicate
# resource. POST/PATCH are deliberately excluded — retrying them after a 5xx
# (or a post-send transport error, where the server may already have committed)
# can double-create data. In this suite that surfaces as false deal conflicts
# (a second identical deal flags itself against the first). Non-idempotent calls
# therefore run exactly once and fail fast.
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE", "OPTIONS"})


def _mask(obj: Any) -> Any:
    """Recursively replace values of sensitive-looking keys with ``***``."""
    if isinstance(obj, dict):
        return {
            k: ("***" if any(s in str(k).lower() for s in _SENSITIVE_KEYS) else _mask(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_mask(v) for v in obj]
    return obj


def _preview(obj: Any, limit: int = _BODY_PREVIEW_LIMIT) -> str:
    """Mask, JSON-serialize and truncate an object for one-line logging."""
    try:
        text = _json.dumps(_mask(obj), ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(obj)
    if len(text) > limit:
        return f"{text[:limit]}… (+{len(text) - limit} chars)"
    return text


def _response_preview(response: httpx.Response, limit: int = _BODY_PREVIEW_LIMIT) -> str:
    """Best-effort readable preview of a response body (JSON masked, else text)."""
    if "json" in response.headers.get("content-type", "").lower():
        try:
            return _preview(response.json(), limit)
        except ValueError:
            pass
    text = response.text or "<empty>"
    return f"{text[:limit]}… (+{len(text) - limit} chars)" if len(text) > limit else text


try:
    import allure

    _ALLURE_JSON = allure.attachment_type.JSON
    _ALLURE_TEXT = allure.attachment_type.TEXT
except ImportError:  # allure-pytest not installed — attachments become no-ops
    allure = None  # type: ignore[assignment]


def _attach(name: str, obj: Any) -> None:
    """Attach a masked, pretty-printed object to the current Allure step.

    No-op when allure isn't installed or when no test/step context is active,
    so it is always safe to call from the client.
    """
    if allure is None:
        return
    try:
        body = _json.dumps(_mask(obj), ensure_ascii=False, indent=2, default=str)
        allure.attach(body, name=name, attachment_type=_ALLURE_JSON)
    except Exception:  # noqa: BLE001 — reporting must never break the request
        with suppress(Exception):
            allure.attach(str(obj), name=name, attachment_type=_ALLURE_TEXT)


def _attach_response(name: str, response: httpx.Response) -> None:
    """Attach a response body to the current Allure step (JSON when possible)."""
    if allure is None:
        return
    if "json" in response.headers.get("content-type", "").lower():
        with suppress(ValueError):
            _attach(name, response.json())
            return
    with suppress(Exception):
        allure.attach(response.text or "<empty>", name=name, attachment_type=_ALLURE_TEXT)


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
        """Send a request, assert response time + optional status/schema.

        5xx responses (and transport errors) are retried up to 3 times — but only
        for idempotent methods (see ``_IDEMPOTENT_METHODS``). POST/PATCH run once
        and fail fast, so a retry can never double-create a resource.

        Raises ``AssertionError`` when the round-trip exceeds
        ``max_response_time_ms`` (the response-time SLA), or when the status is
        not in ``expected_status``.
        """

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

        # Log the outgoing request (payload + query params), masked & truncated,
        # so every API call is self-explanatory in the run log.
        req_parts: list[str] = []
        body = kwargs.get("json", kwargs.get("data"))
        if body is not None:
            req_parts.append(f"payload={_preview(body)}")
        if kwargs.get("params"):
            req_parts.append(f"params={_preview(kwargs['params'])}")
        suffix = f"  {' '.join(req_parts)}" if req_parts else ""
        logger.info("→ {} {}{}", method.upper(), endpoint, suffix)

        # Attach the request to the current Allure step (full, masked) so it is
        # viewable inside the report, not only in the console log.
        if body is not None or kwargs.get("params"):
            req_doc = {"method": method.upper(), "endpoint": endpoint}
            if body is not None:
                req_doc["payload"] = body
            if kwargs.get("params"):
                req_doc["params"] = kwargs["params"]
            _attach(f"→ {method.upper()} {endpoint} (request)", req_doc)

        # Idempotent methods retry on 5xx/transport errors; POST/PATCH run once
        # so a retry can never double-create a resource.
        max_attempts = 3 if method.upper() in _IDEMPOTENT_METHODS else 1

        response: httpx.Response | None = None
        for attempt in range(1, max_attempts + 1):
            started = time.perf_counter()
            try:
                response = await self._client.request(method, endpoint, headers=headers, **kwargs)
            except httpx.TransportError:
                logger.warning(
                    "{} {} transport error on attempt {}/{}",
                    method.upper(),
                    endpoint,
                    attempt,
                    max_attempts,
                )
                if attempt == max_attempts:
                    raise
                await asyncio.sleep(attempt)
                continue
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            response.extensions["elapsed_ms"] = elapsed_ms
            logger.info(
                "← {} {} | {} ({}ms)", method.upper(), endpoint, response.status_code, elapsed_ms
            )

            if response.status_code < 500 or attempt == max_attempts:
                break
            await asyncio.sleep(attempt)

        if response is None:
            raise RuntimeError("HTTP request did not produce a response")

        # Echo the response body (masked + truncated) so the result is visible.
        logger.info("  resp={}", _response_preview(response))
        _attach_response(
            f"← {method.upper()} {endpoint} | {response.status_code} (response)", response
        )

        elapsed_ms = response.extensions["elapsed_ms"]
        too_slow = elapsed_ms >= self.max_response_time_ms
        if too_slow:
            # Greppable marker for the log timeline / AI triage; the assertion
            # below is what actually fails the call.
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
        # Response-time SLA: a functionally-correct response that exceeds the
        # per-client limit still fails the call. Checked after the status
        # assertion so a wrong status surfaces first; setup-only calls (e.g.
        # login) raise the limit instead of disabling the check.
        assert not too_slow, (
            f"response time {elapsed_ms}ms exceeded limit {self.max_response_time_ms}ms "
            f"for {method.upper()} {endpoint}"
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
