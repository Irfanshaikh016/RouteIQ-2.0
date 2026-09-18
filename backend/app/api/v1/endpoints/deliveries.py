"""
RouteIQ 2.0 - Delivery Management Endpoints (Phase 2)
Provides full CRUD for delivery orders, time windows, and package metrics
with strict tenant isolation and location integrity checks.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_org_id, require_role
from app.repositories.store import DataStore, get_store
from app.schemas.delivery import DeliveryCreate, DeliveryResponse, DeliveryUpdate

router = APIRouter()


@router.post("", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
    payload: DeliveryCreate,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager", "operator"])),
    store: DataStore = Depends(get_store),
) -> DeliveryResponse:
    """Creates a new delivery order. Validates location existence and tenant ownership."""
    try:
        delivery = store.create_delivery(
            organization_id=org_id,
            reference_number=payload.reference_number,
            pickup_location_id=payload.pickup_location_id,
            delivery_location_id=payload.delivery_location_id,
            priority=payload.priority.value,
            status=payload.status.value,
            package_weight=payload.package_weight,
            package_volume=payload.package_volume,
            requested_delivery_date=payload.requested_delivery_date,
            time_window_start=payload.time_window_start,
            time_window_end=payload.time_window_end,
            notes=payload.notes,
        )
        return DeliveryResponse.model_validate(delivery)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[DeliveryResponse])
async def list_deliveries(
    org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> List[DeliveryResponse]:
    """Lists all deliveries belonging exclusively to the user's organization."""
    deliveries = store.list_deliveries(org_id)
    return [DeliveryResponse.model_validate(d) for d in deliveries]


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(
    delivery_id: str,
    org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> DeliveryResponse:
    """Retrieves a single delivery by ID. Prevents cross-organization inspection."""
    delivery = store.get_delivery(org_id, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found in your organization.",
        )
    return DeliveryResponse.model_validate(delivery)


@router.patch("/{delivery_id}", response_model=DeliveryResponse)
async def update_delivery(
    delivery_id: str,
    payload: DeliveryUpdate,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager", "operator"])),
    store: DataStore = Depends(get_store),
) -> DeliveryResponse:
    """Updates delivery attributes. Blocks cross-organization modification."""
    try:
        updated = store.update_delivery(
            organization_id=org_id,
            delivery_id=delivery_id,
            reference_number=payload.reference_number,
            pickup_location_id=payload.pickup_location_id,
            delivery_location_id=payload.delivery_location_id,
            priority=payload.priority.value if payload.priority else None,
            status=payload.status.value if payload.status else None,
            package_weight=payload.package_weight,
            package_volume=payload.package_volume,
            requested_delivery_date=payload.requested_delivery_date,
            time_window_start=payload.time_window_start,
            time_window_end=payload.time_window_end,
            notes=payload.notes,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Delivery not found in your organization.",
            )
        return DeliveryResponse.model_validate(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{delivery_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_delivery(
    delivery_id: str,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager"])),
    store: DataStore = Depends(get_store),
):
    """Deletes or cancels a delivery order. Blocks cross-organization deletion."""
    deleted = store.delete_delivery(org_id, delivery_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found in your organization.",
        )
