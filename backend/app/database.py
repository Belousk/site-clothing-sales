from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)


if settings.database_url.startswith("sqlite"):
    # SQLite по умолчанию знает lower() только для ASCII. Регистрируем
    # Python-овский str.lower(), чтобы поиск был регистронезависимым для
    # кириллицы и других не-ASCII символов.
    @event.listens_for(Engine, "connect")
    def _register_unicode_lower(dbapi_connection, connection_record):  # noqa: ARG001
        try:
            dbapi_connection.create_function(
                "lower", 1, lambda x: x.lower() if isinstance(x, str) else x, deterministic=True
            )
        except TypeError:
            # старые версии sqlite3 без аргумента deterministic
            dbapi_connection.create_function(
                "lower", 1, lambda x: x.lower() if isinstance(x, str) else x
            )
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""


def get_db():
    """Зависимость FastAPI: создаёт сессию БД на запрос."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создаёт таблицы при первом запуске. Используется как dev-миграция."""
    from . import models  # noqa: F401  гарантируем регистрацию моделей

    Base.metadata.create_all(bind=engine)
