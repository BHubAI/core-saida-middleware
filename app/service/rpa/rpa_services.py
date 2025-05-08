import secrets

import httpx
from api.deps import DBSession
from core.config import settings
from core.exceptions import RPAException
from core.logging import setup_logger
from models.rpa import RPAEventLog, RPAEventTypes, RPASource
from schemas.rpa_schema import CamundaRequest, MeliusWebhookRequest
from sqlalchemy import select


logger = setup_logger(__name__)


def start_melius_rpa(process_data: dict, db_session: DBSession):
    try:
        process_data["token"] = settings.MELIUS_RPA_TOKEN
        logger.info(f"Starting Melius RPA with process data: {process_data}")

        process_data["urlRetorno"] = f"{settings.CORE_APP_URL}/api/melius/webhook"  # Link do webhook

        process_data["tokenRetorno"] = secrets.token_hex(16)
        url = f"{settings.MELIUS_RPA_URL}/envia-tarefa-rpa"

        response = httpx.post(url, json=process_data)
        response.raise_for_status()

        logger.info(f"Response from Melius RPA: {response.json()}")
        content = response.json()
        id_task = content.get("idTarefaRpa")

        process_data["idTarefaRPA"] = id_task

        db_session.add(
            RPAEventLog(
                process_id=process_data.get("idTarefaCliente", ""),
                event_type=RPAEventTypes.START,
                event_source=RPASource.MELIUS,
                event_data=process_data,
            )
        )

        return content
    except httpx.HTTPStatusError as e:
        logger.error(f"Error starting Melius RPA: {e} | Content: {e.response.content}")
        db_session.add(
            RPAEventLog(
                process_id=process_data.get("idTarefaCliente", ""),
                event_type=RPAEventTypes.START_ERROR,
                event_source=RPASource.MELIUS,
                event_data={
                    "error": str(e),
                    "response_content": e.response.content.decode(),
                    "process_data_request": process_data,
                },
            )
        )
        db_session.commit()
        raise RPAException(str(e))
    except Exception as e:
        logger.error(f"Error starting Melius RPA: {e}")
        db_session.add(
            RPAEventLog(
                process_id=process_data.get("idTarefaCliente", ""),
                event_type=RPAEventTypes.START_ERROR,
                event_source=RPASource.MELIUS,
                event_data={"error": str(e), "process_data_request": process_data},
            )
        )
        db_session.commit()
        raise RPAException(str(e))


def _make_camunda_request(url, params: dict):
    headers = {
        "Content-Type": "application/json",
    }

    if settings.ENV == "prod":
        headers["X-API-Key"] = f"{settings.CAMUNDA_API_TOKEN}"
        response = httpx.post(url, json=params, headers=headers)
    else:
        auth = httpx.BasicAuth(settings.CAMUNDA_USERNAME, settings.CAMUNDA_PASSWORD)
        response = httpx.post(url, json=params, headers=headers, auth=auth)

    response.raise_for_status()

    return response


def handle_webhook_request(request: MeliusWebhookRequest, db_session: DBSession):
    """
    Webhook para receber update dos RPAs da Melius.

    - Recebe o payload do webhook
    - Processa o payload
    - Envia o payload para o Camunda
    """
    stmt = (
        select(RPAEventLog)
        .where(
            RPAEventLog.process_id == request.id_tarefa_cliente,
            RPAEventLog.event_data.op("->>")("tokenRetorno") == request.token_retorno,  # type: ignore
        )
        .order_by(RPAEventLog.created_at.desc())
    )

    rpa_event_logs = db_session.execute(stmt).scalars().all()

    if not rpa_event_logs or rpa_event_logs[0].event_type != RPAEventTypes.START:
        raise RPAException("Token inválido ou tarefa não encontrada")

    logger.info(f"Received Melius Webhook request with process_data: {request.model_dump()}")
    try:
        message_name = f"result_rpa_{rpa_event_logs[0].event_data['tipoTarefaRpa']}"
        camunda_request = CamundaRequest(
            message_name=message_name,
            process_variables={
                message_name: {
                    "value": request.model_dump(include=["status_tarefa_rpa", "mensagem_retorno", "arquivos_gerados"]),  # type: ignore
                },
            },
            process_instance_id=request.id_tarefa_cliente,
        )

        _make_camunda_request(
            f"{settings.CAMUNDA_ENGINE_URL}/message",
            camunda_request.model_dump(by_alias=True),
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Error sending request to Camunda: {e} | Content: {e.response.content}")
        db_session.add(
            RPAEventLog(
                process_id=request.id_tarefa_cliente,
                event_type=RPAEventTypes.FINISH_WITH_ERROR,
                event_source=RPASource.MELIUS,
                event_data={
                    "error": str(e),
                    "response_content": e.response.content.decode(),
                    "camunda_request": camunda_request.model_dump(by_alias=True),
                    **rpa_event_logs[0].event_data,
                },
            )
        )
    except Exception as e:
        logger.error(f"Error processing Melius request: {e} ")
        db_session.add(
            RPAEventLog(
                process_id=request.id_tarefa_cliente,
                event_type=RPAEventTypes.FINISH_WITH_ERROR,
                event_source=RPASource.MELIUS,
                event_data={
                    "error": str(e),
                    "response_content": str(e),
                    "camunda_request": camunda_request.model_dump(by_alias=True),
                    **rpa_event_logs[0].event_data,
                },
            )
        )
    else:
        db_session.add(
            RPAEventLog(
                process_id=request.id_tarefa_cliente,
                event_type=RPAEventTypes.FINISH,
                event_source=RPASource.MELIUS,
                event_data=rpa_event_logs[0].event_data,
            )
        )

    return {"message": "Webhook Melius recebido com sucesso"}
