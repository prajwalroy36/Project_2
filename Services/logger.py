import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from Core.config import settings

# ---------------------------------------------------------
# Log Directory
# ---------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "application.log"

# ---------------------------------------------------------
# Logger
# ---------------------------------------------------------

logger = logging.getLogger("order_operations")

if not logger.handlers:

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.setLevel(settings.LOG_LEVEL)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file)

    logger.propagate = False


# ---------------------------------------------------------
# Structured Logging Helpers
# ---------------------------------------------------------

def log_order_event(
    *,
    order_id: str,
    db_id: int,
    stage: str,
    status: str,
    message: str,
) -> None:

    logger.info(
        f"[ORDER={order_id}] "
        f"[DB={db_id}] "
        f"[{stage}] "
        f"[{status}] "
        f"{message}"
    )


def log_system_event(
    *,
    component: str,
    status: str,
    message: str,
) -> None:

    logger.info(
        f"[SYSTEM] "
        f"[{component}] "
        f"[{status}] "
        f"{message}"
    )


def log_error(
    *,
    component: str,
    message: str,
) -> None:

    logger.exception(
        f"[ERROR] "
        f"[{component}] "
        f"{message}"
    )