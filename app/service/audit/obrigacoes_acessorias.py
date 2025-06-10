import csv
from datetime import datetime
from io import StringIO
from typing import Dict, List

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
        )
        db_session.add(desvio)
        imported_records.append(row)

    db_session.commit()
    return imported_records
