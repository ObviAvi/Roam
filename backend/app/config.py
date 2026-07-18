from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), "../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vocal_bridge_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("VOCAL_BRIDGE_API_KEY", "VOCAL_BRIDE_API_KEY"),
    )
    sabre_api_key: str = ""
    mapbox_token: str = ""
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    gemini_model: str = "gemini-2.5-flash"
    sabre_base_url: str = "https://api.cert.platform.sabre.com"
    vocal_bridge_url: str = "https://vocalbridgeai.com"
    vocal_bridge_agent_id: str = ""
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
