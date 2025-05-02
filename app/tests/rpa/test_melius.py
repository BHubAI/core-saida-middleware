from unittest.mock import MagicMock, patch

import pytest
from core.config import settings
from fastapi.testclient import TestClient
from httpx import Request, Response, codes
from models.rpa import RPAEventLog, RPAEventTypes, RPASource
from schemas.rpa_schema import MeliusWebhookRequest
from service.rpa import rpa_services
from sqlalchemy import func
from sqlmodel import select


def test_start_rpa_endpoint(client: TestClient, mocker, db_session):
    mock_post = mocker.patch("service.rpa.rpa_services.httpx.post")
    mock_post.return_value.json.return_value = {"message": "RPA started"}
    mock_post.return_value.status_code = codes.OK

    process_data = {"idTarefaCliente": "1234567890"}

    response = client.post("/api/melius/start-rpa", json={"process_data": process_data})
    db_session.commit()

    assert response.status_code == codes.OK
    assert response.json() == {"message": "RPA started"}

    stmt = select(RPAEventLog)
    rpa_event_log = db_session.execute(stmt).scalar_one()

    assert rpa_event_log is not None
    assert rpa_event_log.process_id == process_data["idTarefaCliente"]
    assert rpa_event_log.event_type == RPAEventTypes.START


@patch("service.rpa.rpa_services.httpx.post")
def test_handle_webhook_request(mock_post: MagicMock, db_session, override_envvars):
    settings.CAMUNDA_USERNAME = "admin"
    settings.CAMUNDA_PASSWORD = "admin"
    id_tarefa_cliente = "29c16b26-2213-11f0-a8ae-129143b339f3"
    db_session.add(
        RPAEventLog(
            process_id=id_tarefa_cliente,
            event_type=RPAEventTypes.START,
            event_source=RPASource.MELIUS,
            event_data={
                "tipoTarefaRpa": "traDctf",
                "tokenRetorno": "token",
            },
        )
    )
    mock_post.return_value = Response(
        status_code=codes.NO_CONTENT, request=Request("POST", "http://localhost:8080/engine-rest/message")
    )

    webhook_request = {
        "idTarefaCliente": id_tarefa_cliente,
        "tipoTarefaRpa": "traDctf",
        "statusTarefaRpa": 1,
        "arquivosGerados": [
            {"url": "http://example.com/file1.txt", "nomeArquivo": "file1.txt"},
            {"url": "http://example.com/file2.txt", "nomeArquivo": "file2.txt"},
        ],
        "tokenRetorno": "token",
    }
    response = rpa_services.handle_webhook_request(MeliusWebhookRequest.model_validate(webhook_request), db_session)

    expected_camunda_request = {
        "messageName": "result_rpa_traDctf",
        "processVariables": {
            "result_rpa_traDctf": {
                "value": {
                    "status_tarefa_rpa": 1,
                    "mensagem_retorno": None,
                    "arquivos_gerados": [
                        {"url": "http://example.com/file1.txt", "nome_arquivo": "file1.txt"},
                        {"url": "http://example.com/file2.txt", "nome_arquivo": "file2.txt"},
                    ],
                }
            }
        },
        "processInstanceId": "29c16b26-2213-11f0-a8ae-129143b339f3",
    }

    mock_post.assert_called_once_with(
        f"{settings.CAMUNDA_ENGINE_URL}/message",
        json=expected_camunda_request,
        headers={"Content-Type": "application/json", "Authorization": "Basic admin:admin"},
    )

    stmt = (
        select(RPAEventLog)
        .where(
            RPAEventLog.event_type == RPAEventTypes.FINISH,
            RPAEventLog.process_id == id_tarefa_cliente,
            RPAEventLog.event_data.op("->>")("tokenRetorno") == "token",
        )
        .with_only_columns(func.count())
    )
    rpa_event_log_count = db_session.execute(stmt).scalar()
    assert rpa_event_log_count == 1

    assert response == {"message": "Webhook Melius recebido com sucesso"}


@patch("service.rpa.rpa_services.httpx.post")
def test_handle_webhook_request_invalid_token(mock_post: MagicMock, db_session):
    id_tarefa_cliente = "29c16b26-2213-11f0-a8ae-129143b339f3"
    db_session.add(
        RPAEventLog(
            process_id=id_tarefa_cliente,
            event_type=RPAEventTypes.START,
            event_source=RPASource.MELIUS,
            event_data={
                "tipoTarefaRpa": "traDctf",
                "tokenRetorno": "token",
            },
        )
    )

    webhook_request = {
        "idTarefaCliente": id_tarefa_cliente,
        "tipoTarefaRpa": "traDctf",
        "statusTarefaRpa": 1,
        "arquivosGerados": [
            {"url": "http://example.com/file1.txt", "nomeArquivo": "file1.txt"},
            {"url": "http://example.com/file2.txt", "nomeArquivo": "file2.txt"},
        ],
        "tokenRetorno": "invalid-token",
    }

    with pytest.raises(rpa_services.RPAException):
        rpa_services.handle_webhook_request(MeliusWebhookRequest.model_validate(webhook_request), db_session)

    mock_post.assert_not_called()

    stmt = (
        select(RPAEventLog)
        .where(
            RPAEventLog.event_type == RPAEventTypes.FINISH,
            RPAEventLog.process_id == id_tarefa_cliente,
            RPAEventLog.event_data.op("->>")("tokenRetorno") == "token",
        )
        .with_only_columns(func.count())
    )
    rpa_event_log_count = db_session.execute(stmt).scalar()
    assert rpa_event_log_count == 0


@patch("service.rpa.rpa_services.httpx.post")
def test_handle_webhook_request_duplicate_request(mock_post: MagicMock, db_session):
    id_tarefa_cliente = "29c16b26-2213-11f0-a8ae-129143b339f3"
    db_session.add(
        RPAEventLog(
            process_id=id_tarefa_cliente,
            event_type=RPAEventTypes.START,
            event_source=RPASource.MELIUS,
            event_data={
                "tipoTarefaRpa": "traDctf",
                "tokenRetorno": "token",
            },
        )
    )
    db_session.add(
        RPAEventLog(
            process_id=id_tarefa_cliente,
            event_type=RPAEventTypes.FINISH,
            event_source=RPASource.MELIUS,
            event_data={
                "tipoTarefaRpa": "traDctf",
                "tokenRetorno": "token",
            },
        )
    )

    webhook_request = {
        "idTarefaCliente": id_tarefa_cliente,
        "tipoTarefaRpa": "traDctf",
        "statusTarefaRpa": 1,
        "arquivosGerados": [
            {"url": "http://example.com/file1.txt", "nomeArquivo": "file1.txt"},
            {"url": "http://example.com/file2.txt", "nomeArquivo": "file2.txt"},
        ],
        "tokenRetorno": "token",
    }

    with pytest.raises(rpa_services.RPAException):
        rpa_services.handle_webhook_request(MeliusWebhookRequest.model_validate(webhook_request), db_session)

    mock_post.assert_not_called()

    stmt = (
        select(RPAEventLog)
        .where(
            RPAEventLog.event_type == RPAEventTypes.FINISH,
            RPAEventLog.process_id == id_tarefa_cliente,
            RPAEventLog.event_data.op("->>")("tokenRetorno") == "token",
        )
        .with_only_columns(func.count())
    )
    rpa_event_log_count = db_session.execute(stmt).scalar()
    assert rpa_event_log_count == 1


@patch("service.rpa.rpa_services.httpx.post")
def test_handle_melius_webhook_post_error(mock_post: MagicMock, db_session):
    id_tarefa_cliente = "29c16b26-2213-11f0-a8ae-129143b339f3"
    db_session.add(
        RPAEventLog(
            process_id=id_tarefa_cliente,
            event_type=RPAEventTypes.START,
            event_source=RPASource.MELIUS,
            event_data={
                "tipoTarefaRpa": "traDctf",
                "tokenRetorno": "token",
            },
        )
    )
    mock_post.return_value = Response(
        status_code=codes.INTERNAL_SERVER_ERROR,
        request=Request("POST", "http://localhost:8080/engine-rest/message"),
    )

    webhook_request = {
        "idTarefaCliente": "29c16b26-2213-11f0-a8ae-129143b339f3",
        "tipoTarefaRpa": "traDctf",
        "statusTarefaRpa": 1,
        "arquivosGerados": [
            {"url": "http://example.com/file1.txt", "nomeArquivo": "file1.txt"},
            {"url": "http://example.com/file2.txt", "nomeArquivo": "file2.txt"},
        ],
        "tokenRetorno": "token",
    }

    response = rpa_services.handle_webhook_request(MeliusWebhookRequest.model_validate(webhook_request), db_session)

    stmt = (
        select(RPAEventLog)
        .where(
            RPAEventLog.event_type == RPAEventTypes.FINISH_WITH_ERROR,
            RPAEventLog.process_id == id_tarefa_cliente,
            RPAEventLog.event_data.op("->>")("tokenRetorno") == "token",
        )
        .with_only_columns(func.count())
    )
    rpa_event_log_count = db_session.execute(stmt).scalar()
    assert rpa_event_log_count == 1

    assert response == {"message": "Webhook Melius recebido com sucesso"}
