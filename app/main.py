import asyncio
from contextlib import asynccontextmanager

from api import routes
from core.config import settings
from core.exceptions import CoreSaidaOrchestratorException, ObjectNotFound
from core.logging_config import configure_logging, get_logger
from db.session import add_postgresql_extension
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from queues.subscribers.process_starter_subscriber import ProcessStarterSubscriber


# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""

    logger.info("Starting up...")
    add_postgresql_extension()

    logger.info("Starting SQS subscriber...")
    try:
        subscriber = ProcessStarterSubscriber(queue_name="process_starter_queue.fifo")
        # We need to keep a reference to the task to prevent it from being garbage collected
        subscriber_task = asyncio.create_task(subscriber.start())
        logger.info(f"SQS subscriber task created: {subscriber_task}")
    except Exception as e:
        logger.error(f"Error creating SQS subscriber task: {e}")
        subscriber = None

    yield

    logger.info("Shutting down...")
    if subscriber:
        await subscriber.stop()
        logger.info("SQS subscriber stopped")


def create_service() -> FastAPI:
    app = FastAPI(
        title="core-saida-orchestrator",
        description="Cire Saida Orchestrator",
        version=settings.VERSION,
        openapi_url=f"/{settings.VERSION}/openapi.json",
        lifespan=lifespan,
    )
    routes.register_routes(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()}
        )

    @app.exception_handler(ObjectNotFound)
    async def object_not_found_exception_handler(request: Request, exc: ObjectNotFound):
        error_msg = str(exc)
        logger.error(f"Object not found: {error_msg}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": error_msg})

    @app.exception_handler(CoreSaidaOrchestratorException)
    async def core_saida_orchestrator_exception_handler(
        request: Request, exc: CoreSaidaOrchestratorException
    ):
        error_msg = str(exc)
        logger.error(f"Core Saida Orchestrator error: {error_msg}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": error_msg}
        )

    return app


app = create_service()
