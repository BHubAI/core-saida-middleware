from api.base.endpoints import BaseEndpoint
from api.deps import DDLogger
from db.session import DBSession
from helpers import s3_utils
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

        @self.router.get("/s3-object")
        async def get_s3_object(object_path: str, logger: DDLogger, db_session: DBSession):
            return s3_utils.get_object("core-saida-dp", object_path)
