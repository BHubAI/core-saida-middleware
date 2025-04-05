from api.base.endpoints import BaseEndpoint
from api.deps import Logger
from api.v1.camunda.process_starter import ProcessStarterEndpoint
from api.v1.camunda.side_effect import SideEffectEndpoint
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, PlainTextResponse


class Routers:
    def __init__(self):
        self.endpoints: list[BaseEndpoint] = [SideEffectEndpoint(), ProcessStarterEndpoint()]

    def get_routers(self):
        for endpoint in self.endpoints:
            yield endpoint.get_router()


def register_routes(app: FastAPI):
    api_routers = Routers()

    @app.get("/robots.txt")
    def robots():
        return PlainTextResponse("User-agent: *\nDisallow: /")

    @app.get("/health")
    def health_check(logger: Logger) -> JSONResponse:
        logger.info("Health check requested")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})

    for router in api_routers.get_routers():
        app.include_router(router)
