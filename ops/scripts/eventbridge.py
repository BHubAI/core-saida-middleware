import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


logger = logging.getLogger(__name__)


class EventBridgeService:
    def __init__(self):
        self.client = boto3.client("scheduler")
        self.schedule_group = "process-schedules"
        self.target_url = settings.API_URL  # You'll need to add this to your settings

    def create_schedule(
        self, schedule_name: str, cron_expression: str, process_key: str
    ) -> dict[str, Any]:
        """Create an EventBridge schedule for a process."""
        try:
            response = self.client.create_schedule(
                Name=schedule_name,
                GroupName=self.schedule_group,
                ScheduleExpression=f"cron({cron_expression})",
                FlexibleTimeWindow={"Mode": "OFF"},
                Target={
                    "Arn": self.target_url,
                    "RoleArn": settings.AWS_ROLE_ARN,  # You'll need to add this to your settings
                    "HttpTarget": {
                        "Path": "/api/process/start-process",
                        "Port": "8000",
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
