"""
RouteIQ 2.0 - Weather, Hazards & Road Restrictions Schemas (Phase 6)
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RoadRestrictionStatus(str, Enum):
    OPEN = "OPEN"
    SLOW = "SLOW"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"


class WeatherObservation(BaseModel):
    id: Optional[str] = None
    latitude: float
    longitude: float
    rainfall_mm: float = 0.0
    temperature_c: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    visibility_km: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    source: str = "STATIC_PROVIDER"
    observed_at: datetime


class HazardEvent(BaseModel):
    id: str
    hazard_type: str
    severity: float = Field(..., ge=0.0, le=1.0)
    latitude: float
    longitude: float
    radius_meters: float = 1000.0
    description: Optional[str] = None
    source: str = "MODELED_HEURISTIC"
    confidence: float = 1.0
    starts_at: datetime
    expires_at: datetime
    is_active: bool = True


class HazardCreateRequest(BaseModel):
    hazard_type: str = Field(..., description="e.g. 'flood', 'landslide', 'storm', 'rockfall'")
    severity: float = Field(..., ge=0.0, le=1.0, description="Hazard severity score 0.0 (negligible) to 1.0 (extreme)")
    latitude: float
    longitude: float
    radius_meters: float = Field(1000.0, ge=10.0, le=50000.0)
    description: Optional[str] = None
    source: str = Field("MODELED_HEURISTIC", description="Data source label")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    starts_at: Optional[datetime] = None
    expires_at: datetime

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v


class RoadRestriction(BaseModel):
    id: str
    road_edge_id: str
    road_name: Optional[str] = None
    status: RoadRestrictionStatus = RoadRestrictionStatus.OPEN
    speed_multiplier: float = Field(1.0, ge=0.0, le=1.0, description="0.0 for CLOSED, 0.2-0.8 for SLOW")
    reason: Optional[str] = None
    starts_at: datetime
    expires_at: Optional[datetime] = None


class RoadRestrictionCreateRequest(BaseModel):
    road_edge_id: str
    road_name: Optional[str] = None
    status: RoadRestrictionStatus = RoadRestrictionStatus.CLOSED
    speed_multiplier: float = Field(1.0, ge=0.0, le=1.0)
    reason: Optional[str] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class WeatherHealthResponse(BaseModel):
    status: str = "operational"
    provider: str = "StaticWeatherProvider"
    provider_reachable: bool = True
    active_hazards_count: int
    active_restrictions_count: int
    last_update_timestamp: datetime
