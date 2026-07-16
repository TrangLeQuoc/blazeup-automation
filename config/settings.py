"""Runtime settings loaded from environment variables and .env files."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_env_file() -> Path:
    """Return the single merged-domain .env (``config/blazeup/.env``).

    The suite used to be split per domain (blazeup_admin / blazeup_partner), but
    the two share one API gateway, so they are merged into a single ``blazeup``
    domain. The SA/admin actor and the partner actor are distinguished by
    ``ADMIN_*`` / ``PARTNER_*`` keys inside this one file — not separate files.
    """
    return _PROJECT_ROOT / "config" / "blazeup" / ".env"


class Settings(BaseSettings):
    """Typed configuration for UI, API, browser, and report settings."""

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required — set in config/blazeup/.env (see .env.example). The API gateway
    # is shared; the UI origin + credentials differ per actor (SA vs partner).
    # No default on purpose: a missing .env should fail fast.
    api_base_url: AnyHttpUrl = Field(..., description="API root, e.g. https://api.stg.blazeup.ai")
    admin_base_url: AnyHttpUrl = Field(..., description="SA UI root, e.g. https://stgsa.blazeup.ai")
    admin_email: str | None = Field(default=None)
    admin_password: str | None = Field(default=None)
    # Partner actor — optional (only needed for direct partner-login tests; the
    # current partner-portal tests mint a throwaway partner from the SA side).
    partner_base_url: AnyHttpUrl | None = Field(
        default=None, description="Partner portal UI root, e.g. https://stgpartners.blazeup.ai"
    )
    partner_email: str | None = Field(default=None)
    partner_password: str | None = Field(default=None)
    headless: bool = Field(default=True)
    browser: Literal["chromium", "firefox", "webkit"] = Field(default="chromium")
    slow_mo: int = Field(default=0, ge=0)
    default_response_time_ms: int = Field(default=30000, gt=0)
    viewport_width: int = Field(default=1440, gt=0)
    viewport_height: int = Field(default=900, gt=0)

    # ── AI failure-triage (utils/ai_triage.py) ──────────────────────────────
    # Provider-agnostic by design: switch backends via AI_PROVIDER. Only the
    # selected provider's key is required. Keys live in the gitignored .env.
    ai_provider: Literal["gemini", "groq", "ollama"] = Field(default="gemini")
    ai_model: str = Field(default="gemini-2.0-flash")
    gemini_api_key: str | None = Field(default=None)
    groq_api_key: str | None = Field(default=None)
    ollama_base_url: AnyHttpUrl = Field(default="http://localhost:11434")

    # ── Back-compat aliases ──────────────────────────────────────────────────
    # Most code drives the SA/admin actor, so the generic names resolve to the
    # admin_* values. Partner-scoped code uses the partner_* fields explicitly.
    @property
    def base_url(self) -> AnyHttpUrl:
        return self.admin_base_url

    @property
    def test_email(self) -> str | None:
        return self.admin_email

    @property
    def test_password(self) -> str | None:
        return self.admin_password

    @model_validator(mode="after")
    def _check_url_confusion(self) -> "Settings":
        """Fail fast when api_base_url is accidentally identical to a UI origin.

        Catches the copy-paste mistake where a *_BASE_URL and API_BASE_URL are
        set to the exact same value in .env, which would cause all API calls to
        hit the UI server and return HTML instead of JSON. API and UI may
        legitimately share a hostname with different paths — only an exact
        full-URL match is rejected.
        """
        api = str(self.api_base_url).rstrip("/")
        for name, url in (
            ("admin_base_url", self.admin_base_url),
            ("partner_base_url", self.partner_base_url),
        ):
            if url is not None and str(url).rstrip("/") == api:
                raise ValueError(
                    f"api_base_url is identical to {name} ({url}). "
                    "API_BASE_URL must point to the API root, not a UI root."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance for the test session."""

    return Settings()
