from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from httpx import Request, Response, codes
from models.rpa import RPAEventLog, RPAEventTypes
from service.rpa import rpa_services
from sqlmodel import select


def test_start_rpa_endpoint(client: TestClient, mocker, db_session):
    mock_post = mocker.patch("service.rpa.rpa_services.requests.post")
    mock_post.return_value.json.return_value = {"message": "RPA started"}
    mock_post.return_value.status_code = codes.OK

    process_data = {"process_id": "1234567890"}

    response = client.post("/api/melius/start-rpa", json={"process_data": process_data})

    assert response.status_code == codes.OK
    assert response.json() == {"message": "RPA started"}


def test_start_rpa_service(db_session, mocker):
    mock_post = mocker.patch("service.rpa.rpa_services.requests.post")
    mock_post.return_value.json.return_value = {"message": "RPA started"}
    mock_post.return_value.status_code = codes.OK

    process_data = {"process_id": "1234567890"}

    response = rpa_services.start_melius_rpa(process_data, db_session)
    db_session.commit()

    assert response == {"message": "RPA started"}

    stmt = select(RPAEventLog)
    rpa_event_log = db_session.execute(stmt).scalar_one()

    assert rpa_event_log is not None
    assert rpa_event_log.process_id == process_data["process_id"]
    assert rpa_event_log.event_type == RPAEventTypes.START


@patch("service.rpa.rpa_services.httpx.post")
def test_melius_webhook(mock_post: MagicMock, client: TestClient, db_session):
    mock_post.return_value = Response(
        status_code=codes.NO_CONTENT,
        request=Request("POST", "http://localhost:8080/engine-rest/message")
    )

    webhook_request = {
        "idTarefaCliente": "29c16b26-2213-11f0-a8ae-129143b339f3",
        "tipoTarefaRpa": "traDctf",
        "statusTarefaRpa": 1,
        "arquivosGerados": [
            {"url": "http://example.com/file1.txt", "nomeArquivo": "file1.txt"},
            {"url": "http://example.com/file2.txt", "nomeArquivo": "file2.txt"},
        ],
    }
    response = client.post("/api/melius/webhook", json=webhook_request)

    expected_camunda_request = {
        "messageName": "retorno:traDctf",
        "processVariables": {
            "statusTarefaRpa": {"value": 1, "type": "integer"},
            "arquivosGerados": {
                "value": [
                    {"url": "http://example.com/file1.txt", "nomeArquivo": "file1.txt"},
                    {"url": "http://example.com/file2.txt", "nomeArquivo": "file2.txt"},
                ]
            },
        },
        "processInstanceId": "29c16b26-2213-11f0-a8ae-129143b339f3",
    }
    mock_post.assert_called_once_with(
        "http://localhost:8080/engine-rest/message",
        json=expected_camunda_request,
    )

    assert response.status_code == codes.OK
    assert response.json() == {"message": "Webhook Melius processado com sucesso"}


@patch("service.rpa.rpa_services.httpx.post")
def test_melius_webhook_error(mock_post: MagicMock, client: TestClient):
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
    }
    response = client.post("/api/melius/webhook", json=webhook_request)

    assert response.status_code == codes.INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Erro ao processar Webhook Melius"}