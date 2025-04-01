import json
import logging

import requests
from core.config import settings


logger = logging.getLogger(__name__)


class BaseCamundaProcess:
    """Base class for Camunda processes"""

    def __init__(self, process_key: str):
        self.process_key = process_key

    def start_process(self, variables: dict):
        current_env = settings.ENV

        if current_env == "prod":
            logger.info(
                f"Starting process {self.process_key} with variables {variables} in PRODUCTION"
            )
            self.start_production_process()
        else:
            logger.info(
                f"Starting process {self.process_key} with variables {variables} in {current_env}"
            )
            self.start_dev_process()

    def start_production_process(self):
        """Start a process in production"""
        logger.info(f"Starting process {self.process_key} in PRODUCTION")

    def start_dev_process(self):
        """Start a process in Camunda dev environment"""
        logger.info(f"Starting process {self.process_key} in Camunda DEV")
        url = f"{settings.CAMUNDA_URL}/process-definition/key/{self.process_key}/start"
        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(
            url,
            headers=headers,
            json=self.get_process_variables(),
            auth=(settings.CAMUNDA_USERNAME, settings.CAMUNDA_PASSWORD),
        )

        response.raise_for_status()
        logger.info(f"Process {self.process_key} started in Camunda DEV")

    def get_process_variables(self, process_instance_id: str):
        """Get process variables"""
        logger.info(
            f"Empty process variables for {self.process_key} with process instance id {process_instance_id}"
        )
        return {}


class FechamentoFolha3Process(BaseCamundaProcess):
    """Fechamento folha 3 process"""

    def __init__(self):
        super().__init__("fechamento_folha_dp_3")

    def get_process_variables(self, process_instance_id: str):
        """Get process variables"""
        return {
            "variables": {
                "customer": {
                    "value": json.dumps(
                        {
                            "trading_name": "Empresa Teste Cockpit",
                            "cnpj": "60701190000104",
                            "operational_status": {
                                "hr_pay_day": 5,
                                "accounting_dominio_code": "1234567890",
                            },
                            "customer_profile": "FAMILY_3",
                            "company_tax_type": "NATIONAL_SIMPLE",
                        }
                    ),
                    "type": "json",
                },
                "deadline": {"value": "2025-03-25", "type": "string"},
                "competencia": {"value": "2025-03", "type": "string"},
                "regime_tributario": {"value": "SIMPLES_NACIONAL", "type": "string"},
                "cliente_possui_movimento_folha": {"value": "Com Movimento", "type": "string"},
                "data_fechamento_folha": {"value": "2025-03-25", "type": "string"},
                "cliente_elegibilidade": {"value": "valido", "type": "string"},
                "assignee": {"value": "rafael.nunes@bhub.ai", "type": "string"},
                "tem_movimento_folha": {"value": True, "type": "boolean"},
            }
        }


fechamento_folha_3 = FechamentoFolha3Process()
