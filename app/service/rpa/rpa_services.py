import secrets

import httpx
import requests
from api.deps import DBSession
from core.config import settings
from core.exceptions import RPAException
from core.logging import setup_logger
from models.rpa import RPAEventLog, RPAEventTypes, RPASource
from sqlalchemy import select

from app.schemas.rpa_schema import CamundaRequest, MeliusWebhookRequest


logger = setup_logger(__name__)


def start_melius_rpa(process_data: dict, db_session: DBSession):
    try:
        process_data["token"] = settings.MELIUS_RPA_TOKEN
        logger.info(f"Starting Melius RPA with process data: {process_data}")

        process_data["urlRetorno"] = f"{settings.CORE_APP_URL}/api/melius/webhook"  # Link do webhook

        process_data["tokenRetorno"] = secrets.token_hex(16)
        url = f"{settings.MELIUS_RPA_URL}/envia-tarefa-rpa"

        logger.info(f"Sending request to Melius RPA with url: {url} and process data: {process_data}")
        response = requests.post(url, json=process_data)
        response.raise_for_status()

        db_session.add(
            RPAEventLog(
                process_id=process_data.get("process_id", ""),
                event_type=RPAEventTypes.START,
                event_source=RPASource.MELIUS,
                event_data=process_data,
            )
        )

        return response.json()
    except Exception as e:
        logger.error(f"Error starting Melius RPA: {e}")
        raise RPAException(str(e))


def handle_webhook_request(request: MeliusWebhookRequest, db_session: DBSession):
    """
    Webhook para receber update dos RPAs da Melius.

    - Recebe o payload do webhook
    - Processa o payload
    - Envia o payload para o Camunda
    """
    stmt = select(RPAEventLog).where(
        RPAEventLog.event_type == RPAEventTypes.START,
        RPAEventLog.process_id == request.id_tarefa_cliente,
        RPAEventLog.event_data.op("->>")("tokenRetorno") == request.token_retorno,
    )
    rpa_event_log_start = db_session.execute(stmt).scalar_one_or_none()

    if not rpa_event_log_start:
        raise RPAException("Token inválido ou tarefa não encontrada")

    camunda_request = CamundaRequest(
        message_name=f"retorno:{request.tipo_tarefa_rpa}",
        process_variables={
            "statusTarefaRpa": {
                "value": request.status_tarefa_rpa,
                "type": "integer",
            },
            "arquivosGerados": {
                "value": [
                    {
                        "url": arquivo.url,
                        "nomeArquivo": arquivo.nome_arquivo,
                    }
                    for arquivo in request.arquivos_gerados
                ],
            },
        },
        process_instance_id=request.id_tarefa_cliente,
    )

    response = httpx.post(
        f"{settings.CAMUNDA_ENGINE_URL}/message",
        json=camunda_request.model_dump(by_alias=True),
    )
    response.raise_for_status()

    db_session.add(
        RPAEventLog(
            process_id=request.id_tarefa_cliente,
            event_type=RPAEventTypes.FINISH,
            event_source=RPASource.MELIUS,
            event_data=rpa_event_log_start.event_data,
        )
    )

    return {"message": "Webhook Melius processado com sucesso"}
