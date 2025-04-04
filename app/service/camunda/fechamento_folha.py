"""Fechamento Folha Familias 3, 4 e 5"""

import json

from service.camunda.base import CamundaProcess


class FechamentoFolha3Process(CamundaProcess):
    def __init__(self):
        super().__init__("fechamento_folha_dp_3")

    def get_process_variables(self):
        """Get process variables"""
        return {
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


fechamento_folha_3 = FechamentoFolha3Process()
