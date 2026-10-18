import os
import sys

from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.DB.models import Base

# .env не обязателен: в Docker и CI те же переменные приходят из окружения.
config = dotenv_values(".env")

_DEFAULT_HOST = "db"


def _database_url() -> str:
    """Собрать URL для SQLAlchemy из окружения (или из .env)."""
    url = os.getenv("POSTGRESS_URL") or config.get("POSTGRESS_URL")
    if not url:
        raise RuntimeError(
            "POSTGRESS_URL не задан. Скопируйте .env.example в .env "
            "или передайте переменную окружения POSTGRESS_URL."
        )

    # Имя сервиса в docker-compose — "db"; DB_HOST позволяет переопределить хост.
    host = os.getenv("DB_HOST") or config.get("DB_HOST") or _DEFAULT_HOST
    return url.replace("@db", f"@{host}")


if "pytest" in sys.modules:
    # Тесты всегда идут на in-memory SQLite: внешняя БД для них не нужна.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(_database_url(), echo=True, pool_pre_ping=True)

Base.metadata.create_all(bind=engine)
