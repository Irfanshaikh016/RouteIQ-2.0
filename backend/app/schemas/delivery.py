"""
RouteIQ 2.0 - Delivery Schemas (Phase 2)
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DeliveryPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryBase(BaseModel):
    reference_number: str = Field(..., min_length=2, max_length=64, description="Unique shipment tracking / reference ID")
    pickup_location_id: str = Field(..., description="ID of pickup location")
    delivery_location_id: str = Field(..., description="ID of destination location")
    priority: DeliveryPriority = Field(default=DeliveryPriority.NORMAL)
    status: DeliveryStatus = Field(default=DeliveryStatus.PENDING)
    package_weight: float = Field(default=0.0, ge=0.0, description="Package weight in kg")
    package_volume: float = Field(default=0.0, ge=0.0, description="Package volume in m3")
    requested_delivery_date: Optional[date] = None
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_time_window(self) -> "DeliveryBase":
        if self.time_window_start and self.time_window_end:
            if self.time_window_start > self.time_window_end:
                raise ValueError("time_window_start must be before or equal to time_window_end")
        return self


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryUpdate(BaseModel):
    reference_number: Optional[str] = Field(None, min_length=2, max_length=64)
    pickup_location_id: Optional[str] = None
    delivery_location_id: Optional[str] = None
    priority: Optional[DeliveryPriority] = None
    status: Optional[DeliveryStatus] = None
    package_weight: Optional[float] = Field(None, ge=0.0)
    package_volume: Optional[float] = Field(None, ge=0.0)
    requested_delivery_date: Optional[date] = None
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_time_window(self) -> "DeliveryUpdate":
        if self.time_window_start and self.time_window_end:
            if self.time_window_start > self.time_window_end:
                raise ValueError("time_window_start must be before or equal to time_window_end")
        return self


class DeliveryResponse(DeliveryBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
