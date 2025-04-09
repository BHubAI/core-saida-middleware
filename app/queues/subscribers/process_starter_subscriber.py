import json
from typing import Any, Dict

from core.logging_config import get_logger
from queues.subscribers.sqs import SQSSubscriber
from service.camunda.base import start_process


logger = get_logger(__name__)


class ProcessStarterSubscriber(SQSSubscriber):
    """Custom implementation of the process starter subscriber."""

    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process a message from the queue.
        Args:
            message: The message to process.
        """
        try:
            message_body = json.loads(message["Body"])
            logger.info(f"ProcessStarterSubscriber processing message: {message_body}")
            # TODO: Should open session with database here and close after message is processed
            await start_process(message_body["process_key"], self.db_session, self.logger)
        except Exception as e:
            logger.error(f"Error in ProcessStarterSubscriber: {str(e)}")
            raise
