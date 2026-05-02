from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения, загружается из переменных окружения и .env."""

    app_name: str = "Интернет-магазин одежды"
    database_url: str = "sqlite:///./clothing_sales.db"
    secret_key: str = "change-me-in-production-please-use-long-random-string"
    session_max_age: int = 60 * 60 * 24 * 7  # 7 дней

    uploads_dir: Path = Path("uploads")
    receipts_dir: Path = Path("receipts")
    max_image_size_bytes: int = 5 * 1024 * 1024  # 5 МБ
    allowed_image_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.receipts_dir.mkdir(parents=True, exist_ok=True)
