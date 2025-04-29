from api.base.endpoints import BaseEndpoint
from api.deps import DBSession, DDLogger
from schemas.rpa_schema import MeliusProcessRequest, MeliusWebhookRequest
from service.rpa.rpa_services import handle_webhook_request, start_melius_rpa


ROUTE_PREFIX = "/api/melius"


class MeliusEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["Melius"], prefix=ROUTE_PREFIX)

        @self.router.post("/start-rpa")
        async def start_rpa(melius_request: MeliusProcessRequest, db_session: DBSession, logger: DDLogger):
            try:
                logger.info(f"Received request with process_data: {melius_request.process_data}")
                melius_response = start_melius_rpa(melius_request.process_data, db_session)
                return melius_response
            except Exception as e:
                logger.error(f"Error starting Melius RPA: {e}")
                raise e

        @self.router.post("/webhook")
        async def melius_webhook(request: MeliusWebhookRequest, logger: DDLogger):
            try:
                logger.info(f"Received request with process_data: {request.model_dump()}")
                response = await handle_webhook_request(request)
                return response

            except Exception as e:
                logger.error(f"Erro ao processar Webhook Melius: {e}")
                raise e
