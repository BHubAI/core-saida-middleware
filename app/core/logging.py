import logging
from functools import lru_cache

from core.config import settings
from core.logging_config import get_logger
from datadog.dogstatsd.base import DogStatsd


# Initialize the Datadog statsd client
statsd = DogStatsd(host=settings.DD_AGENT_HOST, port=settings.DD_AGENT_PORT)


class DatadogHandler(logging.Handler):
    """Custom logging handler that sends logs to Datadog."""

    def emit(self, record):
        try:
            msg = self.format(record)
            statsd.event(
                title=record.levelname,
                message=msg,
                alert_type=record.levelname.lower(),
                tags=[
                    f"env:{settings.DD_ENV}",
                    f"service:{settings.DD_SERVICE}",
                    f"version:{settings.DD_VERSION}",
                ],
            )
        except Exception:
            self.handleError(record)


@lru_cache(maxsize=1)
def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with Datadog integration.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = get_logger(name)
    logger.setLevel(settings.LOG_LEVEL)

    # Only add Datadog handler in non-dev environments
    if settings.DD_ENV != "dev":
        # Create a handler that sends logs to Datadog
        dd_handler = DatadogHandler()
        dd_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        # Add the handler to the logger if it doesn't already have it
        if not any(isinstance(h, DatadogHandler) for h in logger.handlers):
            logger.addHandler(dd_handler)

    return logger
