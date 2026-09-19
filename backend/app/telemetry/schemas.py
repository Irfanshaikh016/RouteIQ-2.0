"""
RouteIQ 2.0 - Vehicle Telemetry Pydantic Schemas (Phase 6)
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TelemetryFreshness(str, Enum):
    LIVE = "LIVE"        # < 5 minutes old
    STALE = "STALE"      # 5 to 60 minutes old
    OFFLINE = "OFFLINE"  # > 60 minutes old or no telemetry


class VehicleOperationalStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    STOPPED = "stopped"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class TelemetryIngestRequest(BaseModel):
    vehicle_id: str = Field(..., description="Target vehicle UUID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float = Field(..., description="GPS latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., description="GPS longitude in decimal degrees (-180 to 180)")
    speed: float = Field(..., description="Current speed in km/h (>= 0)")
    heading: Optional[float] = Field(None, description="Compass heading 0-360 degrees")
    ignition_status: bool = Field(True, description="True if vehicle ignition is on")
    battery_level: Optional[float] = Field(None, description="Battery percentage 0-100")
    accuracy: Optional[float] = Field(None, description="GPS horizontal accuracy in meters")
    source: str = Field("SIMULATED_TEST", description="Telemetry source label ('LIVE_GPS', 'SIMULATED_TEST')")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional device telemetry payload")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90.0 and 90.0 degrees")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180.0 and 180.0 degrees")
        return v

    @field_validator("speed")
    @classmethod
    def validate_speed(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError("Speed cannot be negative")
        return v

    @field_validator("heading")
    @classmethod
    def validate_heading(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 360.0):
            raise ValueError("Heading must be between 0.0 and 360.0 degrees")
        return v


class VehicleTelemetryResponse(BaseModel):
    id: str
    organization_id: str
    vehicle_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float
    heading: Optional[float] = None
    ignition_status: bool = True
    battery_level: Optional[float] = None
    accuracy: Optional[float] = None
    source: str = "SIMULATED_TEST"
    freshness: TelemetryFreshness = TelemetryFreshness.LIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class VehicleStateResponse(BaseModel):
    vehicle_id: str
    organization_id: str
    vehicle_name: str
    registration_number: str
    vehicle_type: str
    capacity: float
    capacity_unit: str
    status: str
    freshness: TelemetryFreshness
    latest_telemetry: Optional[VehicleTelemetryResponse] = None
    current_load: float = 0.0
    assigned_route_id: Optional[str] = None


class FleetTelemetrySummary(BaseModel):
    organization_id: str
    total_vehicles: int
    live_count: int
    stale_count: int
    offline_count: int
    vehicles: List[VehicleStateResponse]


class TelemetryHealthResponse(BaseModel):
    status: str = "operational"
    service: str = "vehicle-telemetry"
    ingestion_available: bool = True
    total_ingested_records: int
    last_telemetry_timestamp: Optional[datetime] = None
