import datetime
import logging

import requests
from api.deps import DBSession
from core.config import settings
from core.exceptions import ObjectNotFound
from models.camunda import ProcessEventLog, ProcessEventTypes
from service import camunda


class CamundaProcessStarter:
    """Base class para processos Camunda"""

    def __init__(self, process_key: str, db_session: DBSession, logger: logging.Logger):
        self.process_key = process_key
        self.db_session = db_session
        self.logger = logger

    def is_eligible(self, customer_data: dict):
        """Verifica se o cliente atual é elegível para iniciar este processo"""
        return True

    def get_process_content(self):
        """Retorna o conteúdo do processo"""
        raise NotImplementedError("This method should be implemented to return the process content")

    def start_process(self):
        current_env = settings.ENV

        process_content = self.get_process_content()
        for customer_data in process_content:
            self.logger.info(f"Starting process {self.process_key} for customer {customer_data['cnpj']}")
            try:
                if not self.is_eligible(customer_data):
                    skip_message = (
                        f"Customer {customer_data['cnpj']} is not eligible to start process {self.process_key}"
                    )
                    self.logger.info(skip_message)
                    self.audit_event(customer_data["cnpj"], ProcessEventTypes.SKIPPED, {"message": skip_message})
                    continue

                if current_env == "prod":
                    self.start_production_process(customer_data)
                else:
                    self.start_dev_process(customer_data)

                self.db_session.commit()
            except Exception as e:
                self.logger.error(
                    f"Error starting process {self.process_key} for customer {customer_data['cnpj']}: {e}"
                )
                self.db_session.rollback()
                self.db_session.add(
                    ProcessEventLog(
                        process_id=self.process_key,
                        event_type=ProcessEventTypes.START_ERROR,
                        event_data=customer_data,
                        created_at=datetime.datetime.now(),
                    )
                )

    def get_business_key(self, customer_data: dict):
        """Usa o process_key como business key por padrão.
        Sobreescreva este método caso queira criar um business key único para seu processo.
        """
        return self.process_key

    def audit_event(self, process_id: str, event_type: ProcessEventTypes, process_data: dict):
        """Audit event"""
        self.db_session.add(
            ProcessEventLog(
                process_id=process_id,
                event_type=event_type,
                event_data=process_data,
                created_at=datetime.datetime.now(),
            )
        )
        self.db_session.commit()

    def start_production_process(self, customer_data: dict):
        """Inicia o processo em PROD"""
        url = f"{settings.CAMUNDA_ENGINE_URL}/process-definition/key/{self.process_key}/start"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": settings.CAMUNDA_API_TOKEN,
        }
        variables = self.get_process_variables(customer_data)

        payload = {
            "variables": variables,
            "businessKey": self.get_business_key(customer_data),
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()

        process_id = response.json()["id"]

        self.audit_event(process_id, ProcessEventTypes.START, payload)

        self.logger.info(
            f"Process {self.process_key} started in Camunda PRODUCTION for customer {customer_data['cnpj']}"
        )

    def start_dev_process(self, customer_data: dict):
        """Inicia o processo em DEV"""
        url = f"{settings.CAMUNDA_ENGINE_URL}/process-definition/key/{self.process_key}/start"
        headers = {
            "Content-Type": "application/json",
        }
        variables = self.get_process_variables(customer_data)

        payload = {
            "variables": variables,
            "businessKey": self.get_business_key(customer_data),
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            auth=(settings.CAMUNDA_USERNAME, settings.CAMUNDA_PASSWORD),
        )

        response.raise_for_status()

        process_id = response.json()["id"]

        self.audit_event(process_id, ProcessEventTypes.START, payload)

        self.logger.info(f"Process {self.process_key} started in Camunda DEV for customer {customer_data['cnpj']}")

    def get_process_variables(self, data: dict):
        """Retorna as variaveis do processo"""
        self.logger.info(f"Empty process variables for {self.process_key}")
        return {}


async def start_process(process_key: str, db_session: DBSession, logger: logging.Logger):
    """Inicia um processo por sua chave"""
    logger.info(f"Starting process with key: {process_key}")
    try:
        if not hasattr(camunda, process_key):
            raise ObjectNotFound(f"Process {process_key} not found")

        process: CamundaProcessStarter = getattr(camunda, process_key)(db_session=db_session, logger=logger)
        process.start_process()
    except Exception as e:
        logger.error(f"Error starting process {process_key}: {e}")
