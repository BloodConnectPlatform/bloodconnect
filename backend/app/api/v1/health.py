from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns the status of the API and its database connection.",
    status_code=status.HTTP_200_OK,
)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "connected"
    error_msg = None
    http_status = status.HTTP_200_OK

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        error_msg = str(e)
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    payload = {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": None if settings.is_production else error_msg,
    }

    return JSONResponse(status_code=http_status, content=payload)
