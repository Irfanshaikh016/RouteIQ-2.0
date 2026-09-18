"""
RouteIQ 2.0 - Location Management Endpoints (Phase 2)
Provides full CRUD for depots, delivery stops, and hubs with strict tenant isolation.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_org_id, require_role
from app.repositories.store import DataStore, get_store
from app.schemas.location import LocationCreate, LocationResponse, LocationUpdate

router = APIRouter()


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationCreate,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager", "operator"])),
    store: DataStore = Depends(get_store),
) -> LocationResponse:
    """Creates a new logistics facility or address point."""
    location = store.create_location(
        organization_id=org_id,
        name=payload.name,
        address_line=payload.address_line,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    return LocationResponse.model_validate(location)


@router.get("", response_model=List[LocationResponse])
async def list_locations(
    org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> List[LocationResponse]:
    """Lists all locations belonging exclusively to the user's organization."""
    locations = store.list_locations(org_id)
    return [LocationResponse.model_validate(loc) for loc in locations]


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> LocationResponse:
    """Retrieves a single location by ID. Prevents cross-organization access."""
    location = store.get_location(org_id, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found in your organization.",
        )
    return LocationResponse.model_validate(location)


@router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: str,
    payload: LocationUpdate,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager"])),
    store: DataStore = Depends(get_store),
) -> LocationResponse:
    """Updates location attributes. Blocks cross-organization modification."""
    updated = store.update_location(
        organization_id=org_id,
        location_id=location_id,
        name=payload.name,
        address_line=payload.address_line,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found in your organization.",
        )
    return LocationResponse.model_validate(updated)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: str,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager"])),
    store: DataStore = Depends(get_store),
):
    """Deletes a location. Blocks deletion if active deliveries reference it."""
    try:
        deleted = store.delete_location(org_id, location_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found in your organization.",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
