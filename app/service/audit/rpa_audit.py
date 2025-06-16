import csv
import datetime
from io import StringIO

from app.api.deps import DBSession
from app.models.rpa import RPAEventLog, RPAEventTypes


def _to_csv(data: list[list[str]]) -> str:
    output = StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerows(data)
    csv_content = output.getvalue()
    output.close()
    return csv_content


def get_rpa_audit_data(db_session: DBSession):
    # Last Week Data
    event_logs = (
        db_session.query(RPAEventLog)
        .filter(RPAEventLog.created_at >= datetime.datetime.now() - datetime.timedelta(days=7))
        .filter(RPAEventLog.event_type.in_([RPAEventTypes.START, RPAEventTypes.FINISH]))
        .order_by(RPAEventLog.created_at.desc())
        .all()
    )

    audit_data = [
        [
            "process_id",
            "event_type",
            "event_source",
            "base_origem",
            "nome_cliente",
            "cnpj",
            "tipo_tarefa",
            "tarefa_rpa",
            "created_at",
        ]
    ]

    for log in event_logs:
        audit_data.append(log.model_dump_as_csv())

    return _to_csv(audit_data)


def get_rpa_errors(db_session: DBSession):
    event_logs = (
        db_session.query(RPAEventLog)
        .filter(RPAEventLog.created_at >= datetime.datetime.now() - datetime.timedelta(days=7))
        .filter(RPAEventLog.event_type.in_([RPAEventTypes.START_ERROR, RPAEventTypes.FINISH_WITH_ERROR]))
        .order_by(RPAEventLog.created_at.desc())
        .all()
    )

    audit_data = [
        [
            "process_id",
            "event_type",
            "event_source",
            "error",
            "response_content",
            "created_at",
        ]
    ]

    for log in event_logs:
        audit_data.append(log.model_dump_as_csv())

    return _to_csv(audit_data)
