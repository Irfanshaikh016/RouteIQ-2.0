"""
RouteIQ 2.0 - Organization Endpoints (Phase 2)
Manages company/organization settings with strict authorization.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_org_id, get_current_user, require_role
from app.repositories.store import DataStore, get_store
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate

router = APIRouter()


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
    store: DataStore = Depends(get_store),
) -> OrganizationResponse:
    """Creates a new organization (Admin only)."""
    org = store.create_organization(
        name=payload.name,
        description=payload.description,
    )
    return OrganizationResponse.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> OrganizationResponse:
    """Retrieves organization details. Blocks cross-organization inspection."""
    if org_id != user_org_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot access other organizations' records.",
        )
    org = store.get_organization(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return OrganizationResponse.model_validate(org)


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
    user_org_id: str = Depends(get_current_org_id),
    store: DataStore = Depends(get_store),
) -> OrganizationResponse:
    """Updates organization profile. Restricted to Admin of the organization."""
    if org_id != user_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: cannot modify other organizations.",
        )
    org = store.update_organization(
        org_id=org_id,
        name=payload.name,
        description=payload.description,
    )
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return OrganizationResponse.model_validate(org)
