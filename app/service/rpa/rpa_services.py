import secrets
import uuid

import boto3
import httpx
from sqlalchemy import select

from app.api.deps import DBSession
from app.core.config import settings
from app.core.exceptions import RPAException
from app.core.logging import setup_logger
from app.models.rpa import RPAEventLog, RPAEventTypes, RPASource
from app.schemas.rpa_schema import CamundaRequest, MeliusWebhookRequest


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
        process_data["idRequisicao"] = content.get("idRequisicao", "")

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
        raise RPAException(str(e.response.content.decode()))
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

    if settings.ENV == "production":
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
    - Envia mensagem para fila SQS para ser processada pelo worker
    """
    stmt = (
        select(RPAEventLog)
        .where(
            RPAEventLog.process_id == request.id_tarefa_cliente,
            RPAEventLog.event_data.op("->>")("tokenRetorno") == request.token_retorno,  # type: ignore
        )
        .order_by(RPAEventLog.created_at.desc())
    )

    rpa_event_logs = db_session.execute(stmt).scalars().first()

    if not rpa_event_logs or rpa_event_logs[0].event_type != RPAEventTypes.START:
        raise RPAException("Token inválido ou tarefa não encontrada")

    logger.info(f"Received Melius Webhook request with process_data: {request.model_dump()}")

    db_session.add(
        RPAEventLog(
            process_id=request.id_tarefa_cliente,
            event_type=RPAEventTypes.FINISH,
            event_source=RPASource.MELIUS,
            event_data=request.model_dump(),
        )
    )

    # Envia mensagem para fila SQS para ser processada pelo worker
    sqs_client = boto3.client("sqs", region_name=settings.AWS_REGION)
    queue_url = sqs_client.get_queue_url(QueueName=settings.QUEUE_RPA_RESULT)["QueueUrl"]
    message_id = str(uuid.uuid4())

    message_body = {
        "process_id": request.id_tarefa_cliente,
        "event_type": RPAEventTypes.FINISH,
        "event_source": RPASource.MELIUS,
        "event_data": request.model_dump(),
        "message_name": rpa_event_logs[0].event_data["tipoTarefaRpa"],
    }
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=message_body,
        MessageGroupId=message_id,
        MessageDeduplicationId=message_id,
    )

    logger.info(f"Message sent to SQS: {message_id}")

    return {"message": "Webhook Melius recebido com sucesso"}


def handle_rpa_result_message(message: dict, db_session: DBSession):
    """
    Processa a mensagem da fila SQS para ser processada pelo worker
    """
    logger.info(f"Received RPA result message: {message}")

    try:
        message_name = message["message_name"]
        camunda_request = CamundaRequest(
            message_name=message_name,
            process_variables={
                message_name: {
                    "value": message["event_data"],
                },
            },
            process_instance_id=message["process_id"],
        )

        _make_camunda_request(
            f"{settings.CAMUNDA_ENGINE_URL}/message",
            camunda_request.model_dump(by_alias=True),
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Error sending request to Camunda: {e} | Content: {e.response.content}")
        db_session.add(
            RPAEventLog(
                process_id=message["process_id"],
                event_type=RPAEventTypes.FINISH_WITH_ERROR,
                event_source=RPASource.MELIUS,
                event_data={
                    "error": str(e),
                    "response_content": e.response.content.decode(),
                    "camunda_request": camunda_request.model_dump(by_alias=True),
                    **message["event_data"],
                },
            )
        )
    except Exception as e:
        logger.error(f"Error processing Melius request: {e} ")
        db_session.add(
            RPAEventLog(
                process_id=message["process_id"],
                event_type=RPAEventTypes.FINISH_WITH_ERROR,
                event_source=RPASource.MELIUS,
                event_data={
                    "error": str(e),
                    "response_content": str(e),
                    "camunda_request": camunda_request.model_dump(by_alias=True),
                    **message["event_data"],
                },
            )
        )
