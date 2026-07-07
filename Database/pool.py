# Database/pool.py
from contextlib import contextmanager
from typing import Generator

from psycopg import Connection
from psycopg_pool import ConnectionPool

from Core.config import settings
from Services.logger import log_system_event

_pool: ConnectionPool | None = None


def init_pool() -> None:
    global _pool
    if _pool is not None:
        return

    _pool = ConnectionPool(
        conninfo=settings.DATABASE_URL,
        min_size=settings.DB_POOL_MIN,
        max_size=settings.DB_POOL_MAX,
        open=True,
    )
    log_system_event(
        component="DATABASE",
        status="POOL_READY",
        message=f"Connection pool opened (min={settings.DB_POOL_MIN}, max={settings.DB_POOL_MAX}).",
    )


def close_pool() -> None:
    global _pool
    if _pool is None:
        return

    _pool.close()
    _pool = None
    log_system_event(
        component="DATABASE",
        status="POOL_CLOSED",
        message="Connection pool closed.",
    )


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    if _pool is None:
        init_pool()

    assert _pool is not None
    with _pool.connection() as conn:
        yield conn


def check_db_connection() -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return True
    except Exception:
        return False
