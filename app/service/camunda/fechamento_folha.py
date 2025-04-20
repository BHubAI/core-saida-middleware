"""Fechamento Folha Familias 3, 4 e 5"""

import csv
import datetime
import json
from io import StringIO

from helpers import s3_utils
from models.camunda import ProcessEventLog, ProcessEventTypes
from service.camunda.base import CamundaProcessStarter
from service.camunda.enums import RegimeTributario


class FechamentoFolha3Process(CamundaProcessStarter):
    def __init__(self, *args, **kwargs):
        super().__init__("fechamento_folha_dp_3", *args, **kwargs)

    def is_eligible(self, customer_data: dict):
        return customer_data["Tipo de folha"] != "sem movimento"

    def audit_event(self, customer_data: dict):
        """Audit event"""
        audit_data = {
            "customer_id": customer_data["ID"],
            "cnpj": customer_data["cnpj"],
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

    def get_process_content(self):
        """Load process content from s3 object"""
        process_data = s3_utils.get_object("core-saida", "/dp/fechamento-folha/folha-elegiveis.csv")

        csv_file = StringIO(process_data)
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            yield row

    def get_process_variables(self, customer_data: dict):
        return {
            "customer": {
                "value": json.dumps(
                    {
                        "trading_name": customer_data["company"],
                        "ID": customer_data["id"],
                        "cnpj": customer_data["cnpj"],
                        "origem": customer_data["origin_cnpj"],
                        "customer_profile": customer_data["customer_profile"],
                        "company_tax_type": RegimeTributario.get_by_name(customer_data["company_tax_type"]),
                        "codigo_dominio": customer_data["COD Dominio"],
                    }
                ),
                "type": "json",
            },
            "deadline": {
                "value": "2025-03-25",
                "type": "string",
            },
            "competencia": {
                "value": datetime.datetime.now().strftime("%m/%Y"),
                "type": "string",
            },
            "cliente_possui_movimento_folha": {
                "value": True if customer_data["Tipo de folha"] != "sem movimento" else False,
                "type": "boolean",
            },
            "data_fechamento_folha": {
                "value": "2025-03-25",
                "type": "string",
            },
            "cliente_elegibilidade": {
                "value": "valido" if self.is_eligible(customer_data) else "invalido",
                "type": "string",
            },
            "assignee": {
                "value": "rafael.nunes@bhub.ai",  # customer_data["Analista_dp"],
                "type": "string",
            },
            "tem_movimento_folha": {
                "value": True if customer_data["Tipo de folha"] != "sem movimento" else False,
                "type": "boolean",
            },
            "tem_contribuicao": {
                "value": "no",
                "type": "string",
            },
            "envia_notificacao": {
                "value": "no" if customer_data["customer_profile"] == "FAMILY_5" else "yes",
                "type": "string",
            },
        }


fechamento_folha_3 = FechamentoFolha3Process
