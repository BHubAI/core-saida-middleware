import logging

import requests
from core.config import settings


logger = logging.getLogger(__name__)


class CamundaProcess:
    """Base class for Camunda processes"""

    def __init__(self, process_key: str):
        self.process_key = process_key

    def start_process(self):
        current_env = settings.ENV

        if current_env == "prod":
            logger.info(f"Starting process {self.process_key} in PRODUCTION")
            self.start_production_process()
        else:
            logger.info(f"Starting process {self.process_key} in {current_env}")
            self.start_dev_process()

    def start_production_process(self):
        """Start a process in production"""
        logger.info(f"Starting process {self.process_key} in PRODUCTION")

    def get_business_key(self):
        """Get the business key for the process"""
        # TODO: Implement this to get a real business key
        return self.process_key

    def start_dev_process(self):
        """Start a process in Camunda dev environment"""
        logger.info(f"Starting process {self.process_key} in Camunda DEV")
        url = f"{settings.CAMUNDA_ENGINE_URL}/process-definition/key/{self.process_key}/start"
        headers = {
            "Content-Type": "application/json",
        }
        variables = self.get_process_variables()
        variables["business_key"] = self.get_business_key()

        payload = {
            "variables": variables,
        }
        # TODO Use httpx and async request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            auth=(settings.CAMUNDA_USERNAME, settings.CAMUNDA_PASSWORD),
        )

        response.raise_for_status()
        logger.info(f"Process {self.process_key} started in Camunda DEV")

    def get_process_variables(self):
        """Get process variables"""
        logger.info(f"Empty process variables for {self.process_key}")
        return {}
