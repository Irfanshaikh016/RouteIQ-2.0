"""
Health check endpoint for RouteIQ 2.0.
Verifies service uptime, environment status, and database connectivity.
"""
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.db.session import check_database_health

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: str
    database: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Returns HTTP 200 with service diagnostic info and live database connectivity.
    """
    db_status = await check_database_health()
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
    )
