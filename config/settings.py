"""Runtime settings loaded from environment variables and .env files."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for UI, API, browser, and report settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: AnyHttpUrl = Field(default="https://terralogic.blazeup.ai")
    api_base_url: AnyHttpUrl = Field(default="https://terralogic.blazeup.ai/api/v1")
    test_email: str | None = Field(default=None)
    test_password: str | None = Field(default=None)
    headless: bool = Field(default=True)
    browser: Literal["chromium", "firefox", "webkit"] = Field(default="chromium")
    slow_mo: int = Field(default=0, ge=0)
    allure_results_dir: str = Field(default="allure-results")
    default_response_time_ms: int = Field(default=2000, gt=0)
    viewport_width: int = Field(default=1440, gt=0)
    viewport_height: int = Field(default=900, gt=0)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance for the test session."""

    return Settings()

