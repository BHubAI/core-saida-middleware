import csv
import json
from io import StringIO
from typing import Any, Dict

from helpers import s3_utils
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
            process_data = s3_utils.get_object("fechamento-folha", "folha_pagamento.csv")

            csv_file = StringIO(process_data)
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                # TODO REMOVE this hard coded
                row["regime"] = "NATIONAL_SIMPLE"
                await start_process(process_key, row, db_session, self.logger)
        except Exception as e:
            self.logger.error(f"Error in ProcessStarterSubscriber: {str(e)}")
            raise
