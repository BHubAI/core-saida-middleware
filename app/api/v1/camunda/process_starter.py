import logging

import fastapi
from api.base.endpoints import BaseEndpoint
from core.exceptions import ObjectNotFound
from db.session import get_session
from schemas.camunda_schema import ProcessKeyRequest
from service import camunda
from sqlmodel import Session


logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/api/process-starter"


class ProcessStarterEndpoint(BaseEndpoint):
    """Process starter endpoint"""

    def __init__(self):
        super().__init__(tags=["process_starter"], prefix=ROUTE_PREFIX)

        @self.router.post("/")
        async def start_process(
            request: ProcessKeyRequest, db: Session = fastapi.Depends(get_session)
        ):
            """Start process"""
            logger.info(f"Starting process with key: {request.process_key}")

            if not hasattr(camunda, request.process_key):
                raise ObjectNotFound(f"Process {request.process_key} not found")

            process = getattr(camunda, request.process_key)
            process.start_process()
