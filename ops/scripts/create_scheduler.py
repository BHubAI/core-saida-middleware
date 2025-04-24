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
        self.client = boto3.client("events")
        self.region = os.getenv("AWS_REGION")
        sts = boto3.client("sts")
        self.account_id = sts.get_caller_identity()["Account"]

    def rule_exists(self, rule_name: str) -> bool:
        """Check if a rule with the given name exists."""
        try:
            self.client.describe_rule(Name=rule_name)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            raise

    def create_rule(self, rule_name: str, cron_expression: str, process_key: str) -> dict[str, Any]:
        """Create an EventBridge rule for a process."""
        try:
            if self.rule_exists(rule_name):
                logger.info(f"Rule {rule_name} already exists, skipping creation")
                return {"message": "Rule already exists"}

            # Create the rule
            self.client.put_rule(
                Name=rule_name,
                ScheduleExpression=f"cron({cron_expression})",
                State="ENABLED",
                Description=f"Rule to trigger process {process_key}",
            )

            # Add the target (Lambda function)
            response = self.client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        "Id": f"{rule_name}-target",
                        "Arn": f"arn:aws:lambda:{self.region}:{self.account_id}:function:StartOrchestratorProcess",
                        "Input": json.dumps(
                            {
                                "url": f"{os.getenv('CORE_APP_URL')}/api/process-starter",
                                # "api_key": os.getenv("CORE_APPAPI_KEY"),
                                "process_key": process_key,
                            }
                        ),
                    }
                ],
            )
            logger.info(f"Created rule {rule_name} for process {process_key}")
            return response
        except ClientError as e:
            logger.error(f"Error creating rule {rule_name}: {str(e)}")
            raise

    def create_rules_from_json(self, schedules_file: str) -> None:
        """Create EventBridge rules from a JSON file."""
        try:
            with open(schedules_file, "r") as f:
                schedules = json.load(f)

            for schedule in schedules.get("process_start", []):
                rule_name = f"process-{schedule['process_key']}-rule"
                self.create_rule(
                    rule_name=rule_name,
                    cron_expression=schedule["cron"],
                    process_key=schedule["process_key"],
                )
        except Exception as e:
            logger.error(f"Error creating rules from {schedules_file}: {str(e)}")
            raise


def main():
    """Initialize AWS EventBridge rules from schedules.json"""
    try:
        schedules_file = Path(__file__).parent.parent / "schedules.json"
        eventbridge_service = EventBridgeService()
        eventbridge_service.create_rules_from_json(str(schedules_file))
        logger.info("Successfully created all rules")
    except Exception as e:
        logger.error(f"Failed to create rules: {str(e)}")
        raise


if __name__ == "__main__":
    main()
