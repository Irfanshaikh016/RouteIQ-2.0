"""
RouteIQ 2.0 - Vehicle Schemas (Phase 2)
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class VehicleBase(BaseModel):
    vehicle_name: str = Field(..., min_length=2, max_length=128, description="Identifier name, e.g. NER Fleet Hauler #1")
    vehicle_type: str = Field(..., min_length=2, max_length=64, description="Type: Heavy Truck, Light Commercial, 4x4 Hill Van")
    registration_number: str = Field(..., min_length=2, max_length=64, description="License / registration plate")
    capacity: float = Field(..., ge=0.0, description="Payload capacity weight/volume metric")
    capacity_unit: str = Field(default="kg", max_length=32, description="Unit: kg, tonnes, cubic_m")
    status: VehicleStatus = Field(default=VehicleStatus.AVAILABLE)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    vehicle_name: Optional[str] = Field(None, min_length=2, max_length=128)
    vehicle_type: Optional[str] = Field(None, min_length=2, max_length=64)
    registration_number: Optional[str] = Field(None, min_length=2, max_length=64)
    capacity: Optional[float] = Field(None, ge=0.0)
    capacity_unit: Optional[str] = Field(None, max_length=32)
    status: Optional[VehicleStatus] = None


class VehicleResponse(VehicleBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
