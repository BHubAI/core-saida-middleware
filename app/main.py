import asyncio
from contextlib import asynccontextmanager

from api import routes
from core.config import settings
from core.exceptions import CoreSaidaOrchestratorException, ObjectNotFound, RPAException
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
async def lifespan_subscribers(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""

    logger.info("Starting up...")
    add_postgresql_extension()

    logger.info("Starting SQS subscriber...")
    subscribers = []
    attempts = 0
    while True:
        try:
            pstart_subscriber = ProcessStarterSubscriber(queue_name="process_starter.fifo")

            # We need to keep a reference to the task to prevent it from being garbage collected
            pstart_subscriber_task = asyncio.create_task(pstart_subscriber.start())  # noqa F841: Assigned not used
            logger.info(f"SQS subscriber task created: {pstart_subscriber}")
            subscribers.append(pstart_subscriber)
            break
        except Exception as e:
            logger.error(f"Error creating SQS subscriber task: {e}")
            await asyncio.sleep(3)
            attempts += 1
            if attempts > 10:
                logger.error("Failed to create SQS subscriber task after 10 attempts")
                break

    yield

    logger.info("Shutting down...")
    for subscriber in subscribers:
        await subscriber.stop()
        logger.info("SQS subscriber stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""

    logger.info("Starting up...")
    logger.info(f"MELIUS RPA URL {settings.MELIUS_RPA_URL} | TOKEN {settings.MELIUS_RPA_TOKEN}")
    add_postgresql_extension()

    yield

    logger.info("Shutting down...")


def create_service() -> FastAPI:
    app = FastAPI(
        title="core-saida-orchestrator",
        description="Core Saida Orchestrator",
        version=settings.VERSION,
        openapi_url=f"/{settings.VERSION}/openapi.json",
        lifespan=lifespan,
    )
    routes.register_routes(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})

    @app.exception_handler(ObjectNotFound)
    async def object_not_found_exception_handler(request: Request, exc: ObjectNotFound):
        error_msg = str(exc)
        logger.error(f"Object not found: {error_msg}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": error_msg})

    @app.exception_handler(CoreSaidaOrchestratorException)
    async def core_saida_orchestrator_exception_handler(request: Request, exc: CoreSaidaOrchestratorException):
        error_msg = str(exc)
        logger.error(f"Core Saida Orchestrator error: {error_msg}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": error_msg})

    @app.exception_handler(RPAException)
    async def rpa_exception_handler(request: Request, exc: RPAException):
        error_msg = str(exc)
        logger.error(f"RPA error: {error_msg}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": error_msg})

    return app


app = create_service()
