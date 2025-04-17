import json
from typing import Any, Dict

from queues.subscribers.sqs import SQSSubscriber
from service.camunda.base import start_process
from sqlalchemy.orm import Session


class ProcessStarterSubscriber(SQSSubscriber):
    """Custom implementation of the process starter subscriber."""

    async def process_message(self, message: Dict[str, Any], db_session: Session) -> None:
        """Process a message from the queue.
        Args:
            message: The message to process.
        """
        try:
            process_key = json.loads(message["Body"])["process_key"]

            await start_process(process_key, db_session, self.logger)
        except Exception as e:
            self.logger.error(f"Error in ProcessStarterSubscriber: {str(e)}")
            raise
