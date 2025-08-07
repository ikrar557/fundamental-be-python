from loguru import logger
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

logger.add(sys.stdout, format=LOG_FORMAT, level="INFO")

logger.add(
    LOG_DIR / "application.log",
    format=LOG_FORMAT,
    level="INFO",
    rotation="00:00",
    retention="7 days",
    enqueue=True,
)

logger.add(
    LOG_DIR / "error.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="00:00",
    retention="7 days",
    enqueue=True,
)
