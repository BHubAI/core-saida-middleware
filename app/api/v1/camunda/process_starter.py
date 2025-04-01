import logging

from api.base.endpoints import BaseEndpoint
from core.exceptions import ObjectNotFound
from service import camunda


logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/api/process-starter"


class ProcessStarterEndpoint(BaseEndpoint):
    """Process starter endpoint"""

    def __init__(self):
        super().__init__(tags=["process_starter"], prefix=ROUTE_PREFIX)

        @self.router.post("/")
        async def start_process(self, process_key: str):
            """Start a process"""
            logger.info("Starting process")
            process_name = "fechamento_folha_3"

            process = getattr(camunda, process_name, None)
            if process is None:
                logger.error(f"Process {process_name} not found")
                raise ObjectNotFound()

            process.start_process({})
            return {"message": "Process started"}
