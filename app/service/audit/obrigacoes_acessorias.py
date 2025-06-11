import csv
from datetime import datetime
from io import StringIO
from typing import Dict, List

import numpy as np
from fastapi import UploadFile

from app.api.deps import DBSession
from app.models.audit import HistoricoObrigacoes


def import_desvio_from_file(uoloaded_file: UploadFile, db_session: DBSession) -> List[Dict]:
    """
    Import desvio data from CSV file and save to database

    Args:
        file_content: CSV file content as string
        db_session: Database session

    Returns:
        List of imported records
    """
    csv_file = StringIO(uoloaded_file.file.read().decode("utf-8"))
    csv_reader = csv.DictReader(csv_file)

    imported_records = []
    for row in csv_reader:
        competencia_str = row.get("competencia")

        if not all([row.get("cnpj"), row.get("competencia"), row.get("tipo_obrigacao")]):
            raise ValueError(f"Missing values in row {row}")

        if not competencia_str:
            raise ValueError(f"Missing competencia in row {row}")

        month, year = competencia_str.split("/")
        competencia = datetime.strptime(f"{year}-{month.zfill(2)}-01", "%Y-%m-%d")

        desvio = HistoricoObrigacoes(
            cnpj=row.get("cnpj"),  # type: ignore
            competencia=competencia,
            tipo_obrigacao=row.get("tipo_obrigacao"),  # type: ignore
            valor=row.get("valor"),  # type: ignore
        )
        db_session.add(desvio)
        imported_records.append(row)

    db_session.commit()
    return imported_records


def calcula_desvio_obrigacao(cnpj: str, tipo_obrigacao: str, current_value: float, db_session: DBSession):
    """
    Verifica o desvio padrão de um valor em relação a uma lista de valores históricos.

    Args:
        cnpj: CNPJ do cliente
        tipo_obrigacao: Tipo de obrigação
        current_value: Valor atual da obrigação
        db_session: Sessão do banco de dados

    Returns:
        Numero de desvios padrão do valor atual em relação aos valores históricos
    """

    # Busca o valor da obrigação no banco de dados
    historico = db_session.query(HistoricoObrigacoes).filter(
        HistoricoObrigacoes.cnpj == cnpj, HistoricoObrigacoes.tipo_obrigacao == tipo_obrigacao
    )

    if not historico:
        raise ValueError(f"Obrigacao not found for cnpj {cnpj} and tipo_obrigacao {tipo_obrigacao}")

    values = [valor.valor for valor in historico]
    desvio = np.std(values)

    diff = abs(current_value - np.mean(values))

    num_desvios = diff / desvio if desvio != 0 else 0

    return num_desvios
