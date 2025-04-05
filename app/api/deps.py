import logging
from typing import Annotated, Optional

from core.config import settings
from core.logging import setup_logger
from fastapi import Depends
from redis import Redis


def get_redis_url() -> str:
    # Default values if not in settings
    redis_host = getattr(settings, "REDIS_HOST", "localhost")
    redis_port = getattr(settings, "REDIS_PORT", "6379")
    return f"redis://{redis_host}:{redis_port}"


def get_redis_client() -> Redis:
    redis = Redis.from_url(
        get_redis_url(),
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )
    return redis


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Dependency function to get a configured Datadog logger.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(name or __name__)


# Type alias for easier injection in FastAPI endpoints
DDLogger = Annotated[logging.Logger, Depends(get_logger)]
