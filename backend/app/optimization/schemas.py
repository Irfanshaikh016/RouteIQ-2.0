"""
RouteIQ 2.0 - Fleet Optimization Schemas (Phase 6)
Pydantic contracts for CVRP, VRP-TW, and multi-vehicle dispatch.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class OptimizationProblemType(str, Enum):
    CVRP = "CVRP"
    VRPTW = "VRPTW"


class DeliveryItem(BaseModel):
    delivery_id: str
    location_id: Optional[str] = None
    latitude: float
    longitude: float
    demand: float = Field(..., ge=0.0, description="Package weight or volumetric demand")
    time_window_start_minutes: Optional[int] = Field(None, ge=0, description="Minutes from departure")
    time_window_end_minutes: Optional[int] = Field(None, ge=0, description="Latest arrival in minutes")
    service_duration_minutes: int = Field(15, ge=0, description="Stop dwell / unloading time in minutes")
    priority: str = "normal"

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Longitude must be between -180 and 180")
        return v


class VehicleItem(BaseModel):
    vehicle_id: str
    capacity: float = Field(..., gt=0.0, description="Payload capacity in kg")
    vehicle_name: Optional[str] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None


class OptimizationRequest(BaseModel):
    depot_location_id: Optional[str] = None
    depot_lat: float
    depot_lon: float
    problem_type: OptimizationProblemType = OptimizationProblemType.CVRP
    profile: str = "balanced"
    vehicles: List[VehicleItem] = Field(..., min_length=1)
    deliveries: List[DeliveryItem] = Field(..., min_length=1)

    @field_validator("depot_lat")
    @classmethod
    def validate_depot_lat(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("Depot latitude must be between -90 and 90")
        return v

    @field_validator("depot_lon")
    @classmethod
    def validate_depot_lon(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("Depot longitude must be between -180 and 180")
        return v


class OptimizationStop(BaseModel):
    sequence: int
    is_depot: bool = False
    delivery_id: Optional[str] = None
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    arrival_time_minutes: float
    departure_time_minutes: float
    waiting_time_minutes: float = 0.0
    load_after_stop: float
    time_window: Optional[List[int]] = None
    status: str = "on_time"


class OptimizationVehicleRoute(BaseModel):
    vehicle_id: str
    vehicle_name: Optional[str] = None
    total_distance_km: float
    total_duration_minutes: float
    total_cost: float
    total_risk: float
    capacity: float
    peak_load: float
    capacity_utilization_pct: float
    stops: List[OptimizationStop]
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON LineString


class UnservedDeliveryDetail(BaseModel):
    delivery_id: str
    reason: str
    constraint: str


class OptimizationResponse(BaseModel):
    optimization_id: str
    problem_type: str
    profile: str
    status: str
    vehicles_used: int
    total_distance_km: float
    total_duration_minutes: float
    total_cost: float
    total_risk: float
    total_deliveries: int
    served_deliveries_count: int
    unserved_deliveries: List[UnservedDeliveryDetail] = Field(default_factory=list)
    routes: List[OptimizationVehicleRoute]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OptimizationComparisonResponse(BaseModel):
    depot_lat: float
    depot_lon: float
    profiles: Dict[str, OptimizationResponse]


class OptimizationHealthResponse(BaseModel):
    status: str = "operational"
    ortools_available: bool = True
    ortools_version: str
    supported_problem_types: List[str] = ["CVRP", "VRPTW"]
