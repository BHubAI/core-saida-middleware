from fastapi.testclient import TestClient
from models.rpa import RPAEventLog, RPAEventTypes
from service.rpa import rpa_services
from sqlmodel import select


def test_start_rpa_endpoint(client: TestClient, mocker, db_session):
    mock_post = mocker.patch("service.rpa.rpa_services.requests.post")
    mock_post.return_value.json.return_value = {"message": "RPA started"}
    mock_post.return_value.status_code = 200

    process_data = {"process_id": "1234567890"}

    response = client.post("/api/melius/start-rpa", json={"process_data": process_data})

    assert response.status_code == 200
    assert response.json() == {"message": "RPA started"}


def test_start_rpa_service(db_session, mocker):
    mock_post = mocker.patch("service.rpa.rpa_services.requests.post")
    mock_post.return_value.json.return_value = {"message": "RPA started"}
    mock_post.return_value.status_code = 200

    process_data = {"process_id": "1234567890"}

    response = rpa_services.start_melius_rpa(process_data, db_session)
    db_session.commit()

    assert response == {"message": "RPA started"}

    stmt = select(RPAEventLog)
    rpa_event_log = db_session.execute(stmt).scalar_one()

    assert rpa_event_log is not None
    assert rpa_event_log.process_id == process_data["process_id"]
    assert rpa_event_log.event_type == RPAEventTypes.START
