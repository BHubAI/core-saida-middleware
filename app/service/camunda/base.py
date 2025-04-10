import logging

import requests
from core.config import settings
from core.exceptions import ObjectNotFound
from db.session import DBSession
from service import camunda


class CamundaProcessStarter:
    """Base class for Camunda processes"""

    def __init__(
        self, process_key: str, process_data: dict, db_session: DBSession, logger: logging.Logger
    ):
        self.process_key = process_key
        self.process_data = process_data
        self.db_session = db_session
        self.logger = logger

    def is_eligible(self):
        """Check if current customer is eligible to start this process"""
        return True

    def start_process(self):
        current_env = settings.ENV

        if not self.is_eligible():
            self.logger.info(
                f"Customer {self.process_data['customer_id']} is not eligible to start process {self.process_key}"
            )
            return

        if current_env == "prod":
            self.logger.info(f"Starting process {self.process_key} in PRODUCTION")
            self.start_production_process()
        else:
            self.logger.info(f"Starting process {self.process_key} in {current_env}")
            self.start_dev_process()

    def start_production_process(self):
        """Start a process in production"""
        self.logger.info(f"Starting process {self.process_key} in PRODUCTION")

    def get_business_key(self):
        """Get the business key for the process"""
        # TODO: Implement this to get a real business key
        return self.process_key

    def audit_event(self):
        pass

    def start_dev_process(self):
        """Start a process in Camunda dev environment"""
        self.logger.info(f"Starting process {self.process_key} in Camunda DEV")
        url = f"{settings.CAMUNDA_ENGINE_URL}/process-definition/key/{self.process_key}/start"
        headers = {
            "Content-Type": "application/json",
        }
        variables = self.get_process_variables()

        payload = {
            "variables": variables,
            "businessKey": self.get_business_key(),
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            auth=(settings.CAMUNDA_USERNAME, settings.CAMUNDA_PASSWORD),
        )

        response.raise_for_status()

        self.audit_event()
        self.logger.info(f"Process {self.process_key} started in Camunda DEV")

    def get_process_variables(self):
        """Get process variables"""
        self.logger.info(f"Empty process variables for {self.process_key}")
        return {}


async def start_process(
    process_key: str, data: dict, db_session: DBSession, logger: logging.Logger
):
    """Start process"""
    logger.info(f"Starting process with key: {process_key}")

    if not hasattr(camunda, process_key):
        raise ObjectNotFound(f"Process {process_key} not found")

    process: CamundaProcessStarter = getattr(camunda, process_key)(
        process_data=data, db_session=db_session, logger=logger
    )
    process.start_process()
