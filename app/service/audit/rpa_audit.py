import datetime

from api.deps import DBSession
from models.rpa import RPAEventLog


def get_rpa_audit_data(db_session: DBSession):
    # Last Week Data
    event_logs = (
        db_session.query(RPAEventLog)
        .filter(RPAEventLog.created_at >= datetime.datetime.now() - datetime.timedelta(days=7))
        .order_by(RPAEventLog.created_at.desc())
        .all()
    )

    audit_data_header = [
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

    audit_data = [log.model_dump_as_csv() for log in event_logs]

    audit_data.insert(0, audit_data_header)

    return audit_data
