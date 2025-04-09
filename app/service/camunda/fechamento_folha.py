"""Fechamento Folha Familias 3, 4 e 5"""

import json

from models.camunda import ProcessEventLog, ProcessEventTypes
from service.camunda.base import CamundaProcessStarter
from service.camunda.enums import RegimeTributario


class FechamentoFolha3Process(CamundaProcessStarter):
    def __init__(self, *args, **kwargs):
        super().__init__("fechamento_folha_dp_3", *args, **kwargs)

    def is_eligible(self):
        """Check if current customer is eligible to start this process.
        TODO: Implement this to check if current customer is on the correct family.
        return self.process_data["customer_profile"] in ["FAMILIY_3", "FAMILIY_4", "FAMILIY_5"]
        """
        return True

    def audit_event(self):
        """Audit event"""
        audit_data = {
            "customer_id": self.process_data["customer_id"],
            "codigo_dominio": "1234567890",
            "competencia": "03/2025",
        }

        self.db_session.add(
            ProcessEventLog(
                process_key=self.process_key,
                event_type=ProcessEventTypes.START,
                event_data=audit_data,
            )
        )

    def get_process_variables(self):
        return {
            "customer": {
                "value": json.dumps(
                    {
                        "trading_name": self.process_data["company"],
                        "cnpj": self.process_data["cnpj"],
                        "origem": self.process_data["origin_cnpj"],
                        "operational_status": {
                            "hr_pay_day": 5,
                            "accounting_dominio_code": "1234567890",
                        },
                        "customer_profile": self.process_data["customer_profile"],
                        "company_tax_type": RegimeTributario.get_by_name(
                            self.process_data["regime"]
                        ),
                        "customer_id": self.process_data["customer_id"],
                        "assignee": self.process_data["operacao_responsavel"],
                    }
                ),
                "type": "json",
            },
            "deadline": {
                "value": "2025-03-25",
                "type": "string",
            },
            "competencia": {
                "value": "2025-03",
                "type": "string",
            },
            "cliente_possui_movimento_folha": {
                "value": "Com Movimento",
                "type": "string",
            },
            "data_fechamento_folha": {
                "value": "2025-03-25",
                "type": "string",
            },
            "cliente_elegibilidade": {
                "value": "valido",
                "type": "string",
            },
            "assignee": {
                "value": "rafael.nunes@bhub.ai",
                "type": "string",
            },
            "tem_movimento_folha": {
                "value": True,
                "type": "boolean",
            },
        }


fechamento_folha_3 = FechamentoFolha3Process
