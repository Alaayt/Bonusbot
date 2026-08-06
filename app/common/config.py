from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    database_url: str = "sqlite+aiosqlite:///./data/bonusbot.db"
    redis_url: str = "redis://localhost:6379/0"

    webhook_url: str = ""
    webhook_secret: str = ""

    admin_ids: str = ""
    manager_telegram: str = ""

    affiliate_registration_url: str = ""
    app_download_url: str = ""
    promo_code: str = "VIP10IQ"

    default_language: str = "ar"
    timezone: str = "UTC"
    log_level: str = "INFO"

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
