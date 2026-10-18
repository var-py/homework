"""Конфигурация gunicorn для production-контейнера (см. Dockerfile)."""

import os

bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
workers = int(os.getenv("WEB_WORKERS", "2"))
accesslog = "-"
errorlog = "-"
timeout = int(os.getenv("WEB_TIMEOUT", "60"))

# Приложение импортируется один раз в master-процессе: таблицы создаются
# (Base.metadata.create_all) без гонки между воркерами.
preload_app = True


def post_fork(server, worker):
    """Каждый воркер получает собственный пул соединений SQLAlchemy."""
    from app.DB.session import engine

    engine.dispose(close=False)
