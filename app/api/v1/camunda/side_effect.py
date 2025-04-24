import logging

from api.base.endpoints import BaseEndpoint
from api.deps import DBSession
from fastapi.responses import JSONResponse
from schemas.camunda_schema import Event


logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/api/side-effect"

LOG_EVENT_ROUTE = "/log-event"


class SideEffectEndpoint(BaseEndpoint):
    """Side effect endpoint"""

    def __init__(self):
        super().__init__(tags=["Side Effect"], prefix=ROUTE_PREFIX)

        @self.router.post(LOG_EVENT_ROUTE)
        async def log_event(event: Event, db_session: DBSession):
            """Log event"""
            logger.info(f"Logging event: {event or 'Empty event'}")

            db_session.add(event)
            db_session.commit()

            return JSONResponse(content={"message": "Event logged"})
