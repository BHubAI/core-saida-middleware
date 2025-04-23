"""Fechamento Folha Familias 3, 4 e 5"""

import csv
import datetime
import json
from io import StringIO

from core.config import settings
from helpers import s3_utils
from models.camunda import ProcessEventLog, ProcessEventTypes
from service.camunda.base import CamundaProcessStarter
from service.camunda.enums import RegimeTributario


class FechamentoFolha3Process(CamundaProcessStarter):
    def __init__(self, *args, **kwargs):
        super().__init__("fechamento_folha_dp_3", *args, **kwargs)
        self.s3_file_path = "/dp/fechamento-folha/folha-elegiveis.csv"

    def is_eligible(self, customer_data: dict):
        return True

    def mes_ano_ptbr(self):
        meses = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }

        return f"{meses[datetime.datetime.now().month]}/{datetime.datetime.now().year}"

    def get_upload_url(self):
        if settings.ENV == "dev":
            return "https://task-manager.cexp-dev.bhub.ai/upload-url"
        return "https://task-manager.bhub.ai/upload-url"

    def audit_event(self, process_id: str, event_type: ProcessEventTypes, process_data: dict):
        """Audit event"""
        self.db_session.add(
            ProcessEventLog(
                process_id=process_id,
                event_type=event_type,
                event_data=process_data,
            )
        )
        self.db_session.commit()

    def get_process_content(self):
        """Load process content from s3 object"""
        process_data = s3_utils.get_object("core-saida", self.s3_file_path)

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
                        "ID": customer_data["ID"],
                        "cnpj": customer_data["cnpj"],
                        "origem": customer_data["origin_cnpj"],
                        "customer_profile": customer_data["customer_profile"],
                        "company_tax_type": RegimeTributario.get_by_name(customer_data["company_tax_type"]),
                        "codigo_dominio": customer_data["COD Dominio"],
                    }
                ),
                "type": "json",
            },
            "customer_guid": {
                "value": customer_data["ID"],
                "type": "string",
            },
            "regime_tributario": {
                "value": RegimeTributario.get_by_name(customer_data["company_tax_type"]),
                "type": "string",
            },
            "deadline": {
                "value": "2025-03-25",
                "type": "string",
            },
            "competencia": {
                "value": datetime.datetime.now().strftime("%Y-%m"),
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
            "mes_ano": {
                "value": self.mes_ano_ptbr(),
                "type": "string",
            },
            "upload_url": {
                "value": self.get_upload_url(),
                "type": "string",
            },
        }


fechamento_folha_3 = FechamentoFolha3Process
