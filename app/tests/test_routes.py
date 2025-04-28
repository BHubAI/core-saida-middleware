from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.api.v1.melius.webhook.httpx.post", new_callable=AsyncMock)
def test_melius_webhook(mock_post: AsyncMock, client: TestClient):
    mock_post.return_value.status_code = 204

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

    assert response.status_code == 200
    assert response.json() == {"message": "Melius webhook received"}
