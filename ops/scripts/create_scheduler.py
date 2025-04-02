import json
import logging
import os
from pathlib import Path
from typing import Any

import boto3
import requests
from botocore.exceptions import ClientError
from requests_aws4auth import AWS4Auth


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventBridgeService:
    def __init__(self):
        self.client = boto3.client("scheduler")
        self.schedule_group = "process-schedules"
        self.target_url = os.getenv("CORE_APP_URL")
        # Get AWS account ID and region from the current credentials
        sts = boto3.client("sts")
        self.account_id = sts.get_caller_identity()["Account"]
        self.region = self.client.meta.region_name

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
                    "Arn": f"arn:aws:scheduler:{self.region}:{self.account_id}:aws-sdk:http",
                    "RoleArn": os.getenv("AWS_EVENTBRIDGE_ROLE_ARN"),
                    "Input": json.dumps(
                        {
                            "url": self.target_url,
                            "path": "/api/process/start-process",
                            "port": 80,
                            "method": "POST",
                            "headers": {"Content-Type": "application/json"},
                            "body": {"process_key": process_key},
                        }
                    ),
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


AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
SERVICE = "scheduler"

# Autenticação
auth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, SERVICE)


def create_http_scheduler():
    url = f"https://scheduler.{AWS_REGION}.amazonaws.com/schedules"

    headers = {
        "Content-Type": "application/json",
        "X-Amz-Target": "Amazon.EventBridge.CreateSchedule",
    }

    payload = {
        "Name": "meu-http-post",
        "ScheduleExpression": "cron(0/5 * * * ? *)",  # 12h UTC
        "Target": {
            "Arn": "https://api.seu-endpoint.com/webhook",
            "RoleArn": f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/EventBridge-HTTP-Role",
            "Input": json.dumps({"process_key": "fechamento_folha_dp_3"}),  # Body do POST
            "HttpParameters": {"HeaderParameters": {"Content-Type": "application/json"}},
            "RetryPolicy": {"MaximumRetryAttempts": 3},
        },
        "FlexibleTimeWindow": {"Mode": "OFF"},
    }

    response = requests.post(url, auth=auth, headers=headers, data=json.dumps(payload))

    print(response.content)

    if response.status_code == 200:
        print("Agendamento criado com sucesso!")
    else:
        print(f"Erro: {response.status_code} - {response.text}")


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


def main_http_scheduler():
    create_http_scheduler()


if __name__ == "__main__":
    main_http_scheduler()
