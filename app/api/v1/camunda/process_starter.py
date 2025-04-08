from api.base.endpoints import BaseEndpoint
from api.deps import DDLogger
from core.exceptions import ObjectNotFound
from db.session import DBSession
from schemas.camunda_schema import ProcessKeyRequest
from service import camunda
from service.camunda.base import CamundaProcess


ROUTE_PREFIX = "/api/process-starter"


class ProcessStarterEndpoint(BaseEndpoint):
    """Process starter endpoint"""

    def __init__(self):
        super().__init__(tags=["process_starter"], prefix=ROUTE_PREFIX)

        @self.router.post("")
        async def start_process(
            request: ProcessKeyRequest, logger: DDLogger, db_session: DBSession
        ):
            """Start process"""
            logger.info(f"Starting process with key: {request.process_key}")

            if not hasattr(camunda, request.process_key):
                raise ObjectNotFound(f"Process {request.process_key} not found")

            process: CamundaProcess = getattr(camunda, request.process_key)(
                db_session=db_session, logger=logger
            )
            process.start_process()
