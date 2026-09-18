"""
RouteIQ 2.0 - Vehicle Management Endpoints (Phase 2)
Provides full CRUD for fleet assets with strict multi-tenant organization isolation.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_org_id, require_role
from app.repositories.store import DataStore, get_store
from app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate

router = APIRouter()


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreate,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager"])),
    store: DataStore = Depends(get_store),
) -> VehicleResponse:
    """Creates a new vehicle asset within the authenticated organization."""
    try:
        vehicle = store.create_vehicle(
            organization_id=org_id,
            vehicle_name=payload.vehicle_name,
            vehicle_type=payload.vehicle_type,
            registration_number=payload.registration_number,
            capacity=payload.capacity,
            capacity_unit=payload.capacity_unit,
            status=payload.status.value,
        )
        return VehicleResponse.model_validate(vehicle)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(
    org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> List[VehicleResponse]:
    """Lists all vehicles belonging exclusively to the user's organization."""
    vehicles = store.list_vehicles(org_id)
    return [VehicleResponse.model_validate(v) for v in vehicles]


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: str,
    org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> VehicleResponse:
    """Retrieves a single vehicle by ID. Prevents cross-organization access."""
    vehicle = store.get_vehicle(org_id, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found in your organization.",
        )
    return VehicleResponse.model_validate(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager"])),
    store: DataStore = Depends(get_store),
) -> VehicleResponse:
    """Updates vehicle attributes. Blocks cross-organization modification."""
    try:
        updated = store.update_vehicle(
            organization_id=org_id,
            vehicle_id=vehicle_id,
            vehicle_name=payload.vehicle_name,
            vehicle_type=payload.vehicle_type,
            registration_number=payload.registration_number,
            capacity=payload.capacity,
            capacity_unit=payload.capacity_unit,
            status=payload.status.value if payload.status else None,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found in your organization.",
            )
        return VehicleResponse.model_validate(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager"])),
    store: DataStore = Depends(get_store),
):
    """Deletes a vehicle asset. Blocks cross-organization deletion."""
    deleted = store.delete_vehicle(org_id, vehicle_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found in your organization.",
        )
