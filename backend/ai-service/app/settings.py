from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = Field(default="ai-service", alias="AI_SERVICE_NAME")
    service_version: str = Field(default="1.0.0", alias="AI_SERVICE_VERSION")
    service_mode: str = Field(default="mock", alias="AI_SERVICE_MODE")
    shared_token: str = Field(default="", alias="AI_SERVICE_SHARED_TOKEN")


@lru_cache
def get_settings() -> Settings:
    return Settings()
