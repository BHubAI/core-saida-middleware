import logging
from typing import Annotated, Optional

from core.logging import setup_logger
from fastapi import Depends


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
