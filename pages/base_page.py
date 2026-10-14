"""Base Playwright page object with retry-friendly actions."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from loguru import logger
from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

T = TypeVar("T")


class BasePage:
    """Common UI operations shared by all page objects."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    async def goto(self, path: str = "") -> None:
        """Navigate to an application path."""

        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        logger.log("STEP", "Navigate  {}", url)
        try:
            await self.page.goto(url, wait_until="commit", timeout=60_000)
        except PlaywrightTimeoutError:
            if self.page.url.rstrip("/") != url.rstrip("/"):
                raise
            logger.warning("Navigation timed out after URL commit; continuing with element waits")

    async def wait_for_element(
        self, selector: str, timeout: int = 10_000, label: str | None = None
    ) -> Locator:
        """Wait for an element to become visible and return its locator."""

        locator = self.page.locator(selector).first
        desc = label or self._selector_id(selector)
        logger.debug("Waiting for element [{}]", desc)
        # wait_for has its own retry/poll loop — do not wrap in _retry to avoid multiplying timeouts
        await locator.wait_for(state="visible", timeout=timeout)
        return locator

    async def click(self, selector: str, timeout: int = 10_000, label: str | None = None) -> None:
        """Click an element after waiting for it to be visible."""

        locator = await self.wait_for_element(selector, timeout=timeout, label=label)
        desc = label or self._selector_id(selector)
        logger.log("STEP", "Click  [{}]", desc)
        logger.debug("Click selector: {}", selector)
        await self._retry(lambda: locator.click(timeout=timeout))

    async def fill(
        self, selector: str, value: str, timeout: int = 10_000, label: str | None = None
    ) -> None:
        """Fill an input-like element."""

        locator = await self.wait_for_element(selector, timeout=timeout, label=label)
        desc = label or self._selector_id(selector)
        masked_value = (
            "***"
            if "password" in (label or "").lower() or "password" in selector.lower()
            else value
        )
        logger.log("STEP", "Fill  [{}] = {}", desc, masked_value)
        # Use the MASKED value here too — never log a raw password/secret, even at DEBUG.
        logger.debug("Fill selector: {} | Value: {}", selector, masked_value)
        await self._retry(lambda: locator.fill(value, timeout=timeout))

    # ── Locator-level actions that LOG what they do ─────────────────────────────
    # Page objects mostly build Locators (get_by_role, dialog-scoped, .first) rather than
    # selector strings, and a bare `locator.fill(...)` leaves no trace in the run log — the
    # log then reads "[2/3] fill Deal info" with no hint of which field got which value.
    # These three put every interaction on the log as `Fill [Field] = value`,
    # `Click [Button]`, `Select [Field] = <the option actually picked>`.
    _SECRET_WORDS = ("password", "secret", "token", "otp", "2fa")

    def _mask(self, label: str, value: str) -> str:
        return "***" if any(w in label.lower() for w in self._SECRET_WORDS) else value

    async def fill_in(
        self, locator: Locator, value: str, label: str, *, blur: bool = False
    ) -> None:
        """Fill *locator* with *value*, logging ``Fill [label] = value`` (secrets masked)."""
        logger.log("STEP", "Fill  [{}] = {}", label, self._mask(label, value))
        await locator.fill(value)
        if blur:
            await locator.blur()

    async def click_on(self, locator: Locator, label: str, **kwargs) -> None:
        """Click *locator*, logging ``Click [label]``."""
        logger.log("STEP", "Click  [{}]", label)
        await locator.click(**kwargs)

    async def choose(self, trigger: Locator, option: Locator, field: str) -> str:
        """Open a dropdown (*trigger*) and pick *option*; log + return the picked text.

        Reads the option's text BEFORE clicking, so even "pick the first option" logs the
        real value (``Select [Plan] = Starter Plan (v6)``) instead of an anonymous click.
        """
        await trigger.click()
        await option.wait_for(state="visible")
        picked = " ".join((await option.inner_text()).split())
        logger.log("STEP", "Select  [{}] = {}", field, picked)
        await option.click()
        return picked

    async def get_text(self, selector: str, timeout: int = 10_000) -> str:
        """Return normalized visible text from an element."""

        desc = self._selector_id(selector)
        logger.log("STEP", "Read text  [{}]", desc)
        locator = await self.wait_for_element(selector, timeout=timeout, label=desc)
        text = await self._retry(lambda: locator.inner_text(timeout=timeout))
        return " ".join(text.split())

    async def _retry(
        self,
        action: Callable[[], Awaitable[T]],
        retries: int = 3,
        delay_ms: int = 500,
    ) -> T:
        """Retry a Playwright action (click, fill, inner_text) on transient timeout errors."""

        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                return await action()
            except PlaywrightTimeoutError as exc:
                last_error = exc
                logger.warning("Playwright action timed out on attempt {}/{}", attempt, retries)
                if attempt < retries:
                    await self.page.wait_for_timeout(delay_ms)
        if last_error is not None:
            raise last_error
        raise RuntimeError("Retry action failed without an exception")

    @staticmethod
    def _selector_id(selector: str) -> str:
        """Return a readable snippet of the selector for logs."""
        clean = " ".join(selector.split())
        if len(clean) <= 40:
            return clean
        return f"{clean[:20]}...{clean[-17:]}"
