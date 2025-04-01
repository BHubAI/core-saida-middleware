import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from api import routes
from core.config import settings
from core.exceptions import ObjectNotFound, CoreSaidaOrchestratorException
from db.session import add_postgresql_extension


logger = logging.getLogger(__name__)

def on_startup() -> None:
    # add_postgresql_extension()
    logger.info("FastAPI app running...")

def create_service() -> FastAPI:
    tags_metadata = [
        {
            "name": "health",
            "description": "Health check for api",
        }
    ]

    app = FastAPI(
        title="core-saida-orchestrator",
        description="Cire Saida Orchestrator",
        version=settings.VERSION,
        openapi_url=f"/{settings.VERSION}/openapi.json",
        openapi_tags=tags_metadata,
    )
    routes.register_routes(app)

    app.add_middleware(CORSMiddleware, allow_origins=["*"])

    app.add_event_handler("startup", on_startup)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # TODO: log exception
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})

    @app.exception_handler(ObjectNotFound)
    async def object_not_found_exception_handler(request: Request, exc: ObjectNotFound):
        # TODO: log exception
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.errors()})

    @app.exception_handler(CoreSaidaOrchestratorException)
    async def core_saida_orchestrator_exception_handler(request: Request, exc: CoreSaidaOrchestratorException):
        # TODO: log exception
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": exc.errors()})

    return app

app = create_service()
