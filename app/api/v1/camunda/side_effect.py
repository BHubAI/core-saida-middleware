import logging

from api.base.endpoints import BaseEndpoint
from db.session import get_session
from fastapi import Depends
from fastapi.responses import JSONResponse
from schemas.camunda_schema import Event
from sqlmodel import Session


logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/api/side-effect"

LOG_EVENT_ROUTE = "/log-event"


class SideEffectEndpoint(BaseEndpoint):
    """Side effect endpoint"""

    def __init__(self):
        super().__init__(tags=["side_effect"], prefix=ROUTE_PREFIX)

        @self.router.post(LOG_EVENT_ROUTE)
        async def log_event(event: Event | None = None, db: Session = Depends(get_session)):
            """Log event"""
            logger.info(f"Logging event: {event or 'Empty event'}")

            return JSONResponse(content={"message": "Event logged"})
