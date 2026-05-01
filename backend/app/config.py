from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения, загружается из переменных окружения и .env."""

    app_name: str = "Интернет-магазин одежды"
    database_url: str = "sqlite:///./clothing_sales.db"
    secret_key: str = "change-me-in-production-please-use-long-random-string"
    session_max_age: int = 60 * 60 * 24 * 7  # 7 дней

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
