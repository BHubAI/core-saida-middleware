"""Fechamento Folha Familias 3, 4 e 5"""

import csv
import datetime
import json
from io import StringIO

from core.config import settings
from helpers import s3_utils
from service.camunda.base import CamundaProcessStarter


# from service.camunda.enums import RegimeTributario


class FechamentoFolha3Process(CamundaProcessStarter):
    INCLUDED_CNPJS = ["41541243000114", "54284214000166"]

    def __init__(self, *args, **kwargs):
        super().__init__("fechamento_folha_dp_3", *args, **kwargs)
        self.s3_file_path = "dp/fechamento-folha/folha-elegiveis.csv"

    def is_eligible(self, customer_data: dict):
        return True

    def ano_corrente(self):
        return datetime.datetime.now().year

    def get_mes_competencia(self):
        """Se dia do mês menor que 10, retorna mês anterior, se maior ou igual a 10, retorna mês atual"""
        if datetime.datetime.now().day < 10:
            return datetime.datetime.now().month - 1
        return datetime.datetime.now().month - 1  # TODO fix this, forcando mes anterior porque rodamos com atraso

    def mes_corrente_ptbr(self):
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

        mes_competencia = self.get_mes_competencia()
        return meses[mes_competencia]

    def mes_ano_ptbr(self):
        return f"{self.mes_corrente_ptbr()}/{self.ano_corrente()}"

    def get_upload_url(self):
        # TODO: Mover para variaveis de ambiente
        if settings.ENV == "dev":
            return "https://task-manager.cexp-dev.bhub.ai/upload-url"
        return "https://task-manager.bhub.ai/upload-url"

    def get_hr_pay_day(self, customer_data: dict):
        if customer_data["Data de pagamento de folha (tratado)"] == "n/a":
            return "30"
        return customer_data["Data de pagamento de folha (tratado)"]

    def get_hr_pay_day_type(self, customer_data: dict):
        if customer_data["útil ou corrido"] == "útil":
            return "dia útil"
        return "NTH_WORK_DAY"

    def get_process_content(self):
        """Load process content from s3 object"""
        process_data = s3_utils.get_object(settings.CORE_SAIDA_BUCKET_NAME, self.s3_file_path)

        csv_file = StringIO(process_data)
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if row["cnpj"] in self.INCLUDED_CNPJS:
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
                        "company_tax_type": "SIMPLES NACIONAL",  # RegimeTributario.get_by_name(customer_data["company_tax_type"]),  # noqa E501
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
                "value": "SIMPLES NACIONAL",  # RegimeTributario.get_by_name(customer_data["company_tax_type"]),
                "type": "string",
            },
            "competencia": {
                "value": "04/2025",
                "type": "string",
            },
            "cliente_possui_movimento_folha": {
                "value": True,  # if customer_data["Tipo de folha (tratado)"] != "sem movimento" else False,
                "type": "boolean",
            },
            "cliente_elegibilidade": {
                "value": "valido" if self.is_eligible(customer_data) else "invalido",
                "type": "string",
            },
            "assignee": {
                "value": "",  # customer_data["analista responsável"],
                "type": "string",
            },
            # "tem_movimento_folha": {
            #     "value": True if customer_data["Tipo de folha (tratado)"] != "sem movimento" else False,
            #     "type": "boolean",
            # },
            # "tem_contribuicao": {
            #     "value": "no",
            #     "type": "string",
            # },
            "envia_notificacao": {
                "value": "no" if customer_data["customer_profile"] == "FAMILY_5" else "yes",
                "type": "string",
            },
            "mes_ano": {
                "value": self.mes_ano_ptbr(),
                "type": "string",
            },
            "cnpj_escritorio": {
                "value": customer_data["CNPJ DO ESCRITÓRIO (procuração)"],
                "type": "string",
            },
            "erp_operado": {
                "value": customer_data["ERP_OPERADO"],
                "type": "string",
            },
            "upload_url": {
                "value": self.get_upload_url(),
                "type": "string",
            },
            "caminho_gdocs": {
                "value": f"/Reports de fechamento/{self.ano_corrente()}/DP/Impostos/{self.mes_corrente_ptbr()}/",
                "type": "string",
            },
            "start_rpa_url": {
                "value": f"{settings.CORE_APP_URL}/api/melius/start-rpa",
                "type": "string",
            },
        }


fechamento_folha_3 = FechamentoFolha3Process
