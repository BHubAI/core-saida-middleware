import secrets

import requests
from api.deps import DBSession
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

        response = requests.post(f"{settings.MELIUS_RPA_URL}/envia-tarefa-rpa", json=process_data)
        response.raise_for_status()

        db_session.add(
            RPAEventLog(
                process_id=process_data.get("process_id", ""),
                event_type=RPAEventTypes.START,
                event_source=RPASource.MELIUS,
                event_data=process_data,
            )
        )

        return {"success": True}
        # return response.json()
    except Exception as e:
        logger.error(f"Error starting Melius RPA: {e}")
        raise RPAException(str(e))
