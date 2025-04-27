from api.base.endpoints import BaseEndpoint
from api.deps import DBSession, DDLogger
from schemas.camunda_schema import ProcessKeyRequest
from service.camunda.base import start_process


ROUTE_PREFIX = "/api/process-message"


class ProcessMessageEndpoint(BaseEndpoint):
    """Process message endpoint"""

    def __init__(self):
        super().__init__(tags=["Process Message"], prefix=ROUTE_PREFIX)

        @self.router.post("/start")
        async def start_camunda_process(request: ProcessKeyRequest, logger: DDLogger, db_session: DBSession):
            await start_process(request.process_key, db_session, logger)
