import secrets

import httpx
import requests
from api.deps import DBSession
from app.schemas.rpa_schema import CamundaRequest, MeliusWebhookRequest
from core.config import settings
from core.exceptions import RPAException
from core.logging import setup_logger
from models.rpa import RPAEventLog, RPAEventTypes, RPASource


logger = setup_logger(__name__)


def start_melius_rpa(process_data: dict, db_session: DBSession):
    try:
        process_data["token"] = settings.MELIUS_RPA_TOKEN
        logger.info(f"Starting Melius RPA with process data: {process_data}")

        process_data["urlRetorno"] = settings.MELIUS_RPA_CALLBACK_URL
        process_data["tokenRetorno"] = secrets.token_hex(16)
        MELIUS_URL = "http://hml.api.integracoes-rpa-v1.melius.software"
        url = f"{MELIUS_URL}/envia-tarefa-rpa"

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


async def handle_webhook_request(request: MeliusWebhookRequest):
    """
    Webhook para receber update dos RPAs da Melius.

    - Recebe o payload do webhook
    - Processa o payload
    - Envia o payload para o Camunda
    """

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

    await httpx.post(
        f"{settings.CAMUNDA_ENGINE_URL}/message",
        json=camunda_request.model_dump(by_alias=True),
    )

    return {"message": "Melius webhook received"}