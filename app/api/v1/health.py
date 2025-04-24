from api.deps import DDLogger
from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
async def health_check(logger: DDLogger):
    """
    Health check endpoint.

    Args:
        logger: Injected Datadog logger

    Returns:
        dict: Health status
    """
    logger.info("Health check requested")
    return {"status": "ok"}
