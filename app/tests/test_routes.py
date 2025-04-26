from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health(monkeypatch: MagicMock):
    monkeypatch.setenv("POSTGRES_USER", "test")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test")
    monkeypatch.setenv("POSTGRES_DB", "test")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_melius_webhook():
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
    assert response.status_code == 200
    assert response.json() == {
        "message": "Melius webhook received",
        "camunda_request": {
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
        },
    }
