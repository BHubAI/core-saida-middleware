from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.audit.rpa_audit import RPAAuditoriaEndpoint
from app.api.base.endpoints import BaseEndpoint
from app.api.camunda.process_starter import ProcessMessageEndpoint
from app.api.camunda.side_effect import SideEffectEndpoint
from app.api.deps import DDLogger
from app.api.rpa.melius import MeliusEndpoint


class Routers:
    def __init__(self):
        self.endpoints: list[BaseEndpoint] = [
            SideEffectEndpoint(),
            ProcessMessageEndpoint(),
            MeliusEndpoint(),
            RPAAuditoriaEndpoint(),
        ]

    def get_routers(self):
        for endpoint in self.endpoints:
            yield endpoint.get_router()


def register_routes(app: FastAPI):
    api_routers = Routers()

    @app.get("/robots.txt")
    def robots():
        return PlainTextResponse("User-agent: *\nDisallow: /")

    @app.get("/health")
    def health_check(logger: DDLogger) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})

    for router in api_routers.get_routers():
        app.include_router(router)
