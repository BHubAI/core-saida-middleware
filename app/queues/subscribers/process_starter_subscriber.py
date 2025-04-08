import json
from typing import Any, Dict

from core.logging_config import get_logger
from queues.subscribers.sqs import SQSSubscriber


logger = get_logger(__name__)


class ProcessStarterSubscriber(SQSSubscriber):
    """Custom implementation of the process starter subscriber."""

    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process a message from the queue.

        This method should be customized according to your business logic.
        """
        try:
            message_body = json.loads(message["Body"])
            logger.info(f"ProcessStarterSubscriber processing message: {message_body}")

            # Add your custom processing logic here
            # For example:
            # 1. Extract data from message
            # 2. Validate the data
            # 3. Start a process based on the data
            # 4. Update the database
            # 5. Send notifications

            logger.info("ProcessStarterSubscriber processing completed successfully")
        except Exception as e:
            logger.error(f"Error in ProcessStarterSubscriber: {str(e)}")
            raise
