import asyncio
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config
from db.session import get_session
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import setup_logger


class SQSSubscriber:
    """Subscriber for processing messages from SQS queue."""

    def __init__(self, queue_name: str):
        self.logger = setup_logger(__name__)
        self.queue_name = queue_name
        self.sqs_client = self._get_sqs_client()
        self.queue_url = self._get_queue_url()
        self.running = False
        self.poll_interval = 5  # seconds
        self.db_session = None
        self.logger.info(f"Initialized SQS subscriber for queue: {queue_name}")

    def _get_sqs_client(self):
        """Get SQS client with LocalStack configuration."""
        self.logger.debug("Creating SQS client with LocalStack configuration")
        endpoint_url = settings.AWS_ENDPOINT_URL

        return boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(
                retries={"max_attempts": 5, "mode": "adaptive"},
                connect_timeout=10,
                read_timeout=30,
                max_pool_connections=10,
            ),
        )

    def _get_queue_url(self) -> str:
        """Get queue URL from queue name."""
        try:
            self.logger.debug(f"Getting queue URL for queue: {self.queue_name}")
            response = self.sqs_client.get_queue_url(QueueName=self.queue_name)
            queue_url = response["QueueUrl"]
            self.logger.debug(f"Queue URL: {queue_url}")
            return queue_url
        except Exception as e:
            self.logger.error(f"Error getting queue URL: {str(e)}")
            raise

    async def process_message(self, message: Dict[str, Any], db_session: Session) -> None:
        """Not implemented"""
        self.logger.info(f"Empty process_message method: {message}")
        pass

    async def delete_message(self, receipt_handle: str) -> None:
        """Delete a message from the queue after successful processing."""
        try:
            self.logger.info(f"Deleting message with receipt handle: {receipt_handle}")
            self.sqs_client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
            self.logger.info("Message deleted successfully")
        except Exception as e:
            self.logger.error(f"Error deleting message: {str(e)}")
            raise

    async def receive_messages(self) -> Optional[list]:
        """Receive messages from the queue."""
        try:
            self.logger.debug("Receiving messages from queue")
            # Use a shorter wait time to avoid long timeouts
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5,  # Reduced from 20 to avoid long timeouts
                AttributeNames=["All"],
                MessageAttributeNames=["All"],
            )
            messages = response.get("Messages", [])
            if messages:
                self.logger.info(f"Received {len(messages)} messages")
            return messages
        except Exception as e:
            self.logger.error(f"Error receiving messages: {str(e)}")
            # Add a small delay before retrying to avoid hammering the server
            await asyncio.sleep(2)
            return None

    async def start(self) -> None:
        """Start the subscriber."""
        self.running = True
        self.logger.info(f"Starting subscriber for queue: {self.queue_name}")

        while self.running:
            try:
                messages = await self.receive_messages()

                if not messages:
                    self.logger.debug(f"No messages received, sleeping for {self.poll_interval} seconds")
                    await asyncio.sleep(self.poll_interval)
                    continue

                for message in messages:
                    try:
                        self.logger.info(f"Processing message: {message.get('MessageId')}")
                        for db_session in get_session():
                            await self.process_message(message, db_session)
                            db_session.commit()
                            await self.delete_message(message["ReceiptHandle"])
                    except Exception as e:
                        self.logger.error(f"Error handling message: {str(e)}")
                        # Continue processing other messages
                        continue

            except Exception as e:
                self.logger.error(f"Error in message processing loop: {str(e)}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the subscriber."""
        self.logger.info("Stopping subscriber...")
        self.running = False
