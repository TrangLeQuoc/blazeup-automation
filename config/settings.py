"""Runtime settings loaded from environment variables and .env files."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for UI, API, browser, and report settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: AnyHttpUrl = Field(default="https://stgsa.blazeup.ai")
    api_base_url: AnyHttpUrl = Field(default="https://api.stg.blazeup.ai")
    test_email: str | None = Field(default=None)
    test_password: str | None = Field(default=None)
    headless: bool = Field(default=True)
    browser: Literal["chromium", "firefox", "webkit"] = Field(default="chromium")
    slow_mo: int = Field(default=0, ge=0)
    allure_results_dir: str = Field(default="allure-results")
    default_response_time_ms: int = Field(default=30000, gt=0)
    viewport_width: int = Field(default=1440, gt=0)
    viewport_height: int = Field(default=900, gt=0)

    @model_validator(mode="after")
    def _check_url_confusion(self) -> "Settings":
        """Fail fast when api_base_url is accidentally identical to base_url.

        Catches the copy-paste mistake where both BASE_URL and API_BASE_URL
        are set to the exact same value in .env, which would cause all API
        calls to hit the UI server and return HTML instead of JSON.

        Note: API and UI may legitimately share the same hostname with
        different paths (e.g. base_url=https://app.example.com and
        api_base_url=https://app.example.com/api/v1) — that is allowed.
        Only an exact full-URL match is rejected.
        """
        if str(self.base_url).rstrip("/") == str(self.api_base_url).rstrip("/"):
            raise ValueError(
                f"api_base_url is identical to base_url ({self.base_url}). "
                "API_BASE_URL must point to the API root, not the UI root. "
                "Example: API_BASE_URL=https://app.example.com/api/v1"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance for the test session."""

    return Settings()
