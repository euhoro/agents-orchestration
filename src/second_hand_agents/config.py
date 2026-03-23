from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SECOND_HAND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Second-Hand Agents"
    environment: Literal["dev", "test", "prod"] = "dev"
    mode: Literal["demo", "live"] = "demo"
    region: Literal["US"] = "US"
    top_k: int = 10
    max_candidates: int = 12
    resale_fee_rate: float = 0.13
    safety_discount: float = 0.82
    use_llm_agents: bool = False
    model_name: str = "openai:gpt-5.2-mini"
    request_timeout_seconds: float = 8.0
    enabled_source_marketplaces: list[str] = Field(default_factory=lambda: ["demo_curated"])
    enabled_resale_marketplaces: list[str] = Field(default_factory=lambda: ["demo_resale"])
    ebay_client_id: str | None = None
    ebay_client_secret: str | None = None
    ebay_environment: Literal["sandbox", "production"] = "production"
    ebay_scope: str = "https://api.ebay.com/oauth/api_scope"

    @property
    def live_mode_enabled(self) -> bool:
        return self.mode == "live"

    @property
    def ebay_base_url(self) -> str:
        if self.ebay_environment == "sandbox":
            return "https://api.sandbox.ebay.com"
        return "https://api.ebay.com"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
