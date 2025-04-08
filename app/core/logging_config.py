import logging
import sys

from core.config import settings


def configure_logging() -> None:
    """
    Configure logging for the application.

    This function sets up logging to ensure logs appear in the uvicorn console
    when running in Docker.
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Set the log level from settings
    root_logger.setLevel(settings.LOG_LEVEL)

    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)

    # Create a formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Set the formatter for the console handler
    console_handler.setFormatter(formatter)

    # Add the console handler to the root logger if it doesn't already have it
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(console_handler)

    # Configure uvicorn access logger
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(settings.LOG_LEVEL)

    # Configure uvicorn error logger
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(settings.LOG_LEVEL)

    # Configure fastapi logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(settings.LOG_LEVEL)

    # Log the configuration
    logging.info("Logging configured with level: %s", settings.LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
