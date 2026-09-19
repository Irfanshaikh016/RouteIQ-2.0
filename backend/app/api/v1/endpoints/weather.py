"""
RouteIQ 2.0 - Weather, Hazards & Road Restriction Endpoints (Phase 6)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.dependencies import get_current_org_id, require_role
from app.weather.schemas import (
    HazardCreateRequest,
    HazardEvent,
    RoadRestriction,
    RoadRestrictionCreateRequest,
    WeatherHealthResponse,
    WeatherObservation,
)
from app.weather.service import WeatherService, get_weather_service

router = APIRouter()


@router.get("/health", response_model=WeatherHealthResponse)
async def get_weather_health(
    service: WeatherService = Depends(get_weather_service),
) -> WeatherHealthResponse:
    """Weather and hazard provider health diagnostics."""
    return service.get_health()


@router.get("/current", response_model=WeatherObservation)
async def get_current_weather(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    service: WeatherService = Depends(get_weather_service),
) -> WeatherObservation:
    """Retrieves meteorological observations for specified coordinates."""
    return service.get_weather_at_location(latitude, longitude)


@router.get("/hazards", response_model=List[HazardEvent])
async def list_active_hazards(
    service: WeatherService = Depends(get_weather_service),
) -> List[HazardEvent]:
    """Retrieves all currently active, unexpired hazard events (flood, landslide, storm)."""
    return service.get_active_hazards()


@router.post("/hazards", response_model=HazardEvent, status_code=status.HTTP_201_CREATED)
async def create_hazard_event(
    payload: HazardCreateRequest,
    _=Depends(require_role(["admin", "manager"])),
    service: WeatherService = Depends(get_weather_service),
) -> HazardEvent:
    """Registers an active hazard event impacting road corridors."""
    try:
        return service.create_hazard(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/restrictions", response_model=List[RoadRestriction])
async def list_road_restrictions(
    service: WeatherService = Depends(get_weather_service),
) -> List[RoadRestriction]:
    """Retrieves all infrastructure-level road restrictions (CLOSED, SLOW)."""
    return service.get_road_restrictions()


@router.post("/restrictions", response_model=RoadRestriction, status_code=status.HTTP_201_CREATED)
async def set_road_restriction(
    payload: RoadRestrictionCreateRequest,
    _=Depends(require_role(["admin", "manager"])),
    service: WeatherService = Depends(get_weather_service),
) -> RoadRestriction:
    """Imposes a road restriction or closure on a road edge."""
    try:
        return service.set_road_restriction(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
