"""
RouteIQ 2.0 - Dispatch & Re-Optimization Schemas (Phase 6)
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.optimization.schemas import OptimizationResponse


class ReoptimizationTriggerType(str, Enum):
    VEHICLE_BREAKDOWN = "VEHICLE_BREAKDOWN"
    ROAD_CLOSURE = "ROAD_CLOSURE"
    MAJOR_HAZARD = "MAJOR_HAZARD"
    DELIVERY_CANCELLATION = "DELIVERY_CANCELLATION"
    NEW_DELIVERY = "NEW_DELIVERY"
    SIGNIFICANT_DELAY = "SIGNIFICANT_DELAY"


class ReoptimizationTriggerRequest(BaseModel):
    trigger_type: ReoptimizationTriggerType
    depot_location_id: Optional[str] = None
    affected_vehicle_id: Optional[str] = None
    affected_road_edge_id: Optional[str] = None
    affected_delivery_id: Optional[str] = None
    reason: str = Field(..., description="Operational reason triggering re-optimization")
    profile: str = "balanced"


class DispatchStateResponse(BaseModel):
    organization_id: str
    active_vehicles_count: int
    active_deliveries_count: int
    active_hazards_count: int
    active_road_restrictions_count: int
    last_optimization: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReoptimizationResponse(BaseModel):
    trigger_type: str
    reoptimization_performed: bool
    message: str
    affected_vehicle_id: Optional[str] = None
    affected_road_edge_id: Optional[str] = None
    updated_optimization: Optional[OptimizationResponse] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
