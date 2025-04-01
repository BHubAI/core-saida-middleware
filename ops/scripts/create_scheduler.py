import json
import logging
import os
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventBridgeService:
    def __init__(self):
        self.client = boto3.client("scheduler")
        self.schedule_group = "process-schedules"
        self.target_url = os.getenv("CORE_APP_URL")

    def schedule_exists(self, schedule_name: str) -> bool:
        """Check if a schedule with the given name exists."""
        try:
            self.client.get_schedule(GroupName=self.schedule_group, Name=schedule_name)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            raise

    def create_schedule(
        self, schedule_name: str, cron_expression: str, process_key: str
    ) -> dict[str, Any]:
        """Create an EventBridge schedule for a process."""
        try:
            if self.schedule_exists(schedule_name):
                logger.info(f"Schedule {schedule_name} already exists, skipping creation")
                return {"message": "Schedule already exists"}

            response = self.client.create_schedule(
                Name=schedule_name,
                GroupName=self.schedule_group,
                ScheduleExpression=f"cron({cron_expression})",
                FlexibleTimeWindow={"Mode": "OFF"},
                Target={
                    "Arn": self.target_url,
                    "RoleArn": os.getenv("AWS_EVENTBRIDGE_ROLE_ARN"),
                    "HttpTarget": {
                        "Path": "/api/process/start-process",
                        "Port": "80",
                        "Method": "POST",
                        "Headers": [{"Key": "Content-Type", "Value": "application/json"}],
                        "Body": json.dumps({"process_key": process_key}),
                    },
                },
                State="ENABLED",
            )
            logger.info(f"Created schedule {schedule_name} for process {process_key}")
            return response
        except ClientError as e:
            logger.error(f"Error creating schedule {schedule_name}: {str(e)}")
            raise

    def create_schedules_from_json(self, schedules_file: str) -> None:
        """Create EventBridge schedules from a JSON file."""
        try:
            with open(schedules_file, "r") as f:
                schedules = json.load(f)

            for schedule in schedules.get("process_start", []):
                schedule_name = f"process-{schedule['process_key']}-schedule"
                self.create_schedule(
                    schedule_name=schedule_name,
                    cron_expression=schedule["cron"],
                    process_key=schedule["process_key"],
                )
        except Exception as e:
            logger.error(f"Error creating schedules from {schedules_file}: {str(e)}")
            raise


def main():
    """Initialize AWS EventBridge schedules from schedules.json"""
    try:
        schedules_file = Path(__file__).parent.parent / "schedules.json"
        eventbridge_service = EventBridgeService()
        eventbridge_service.create_schedules_from_json(str(schedules_file))
        logger.info("Successfully created all schedules")
    except Exception as e:
        logger.error(f"Failed to create schedules: {str(e)}")
        raise


if __name__ == "__main__":
    main()
