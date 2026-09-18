"""
RouteIQ 2.0 - User Management Endpoints (Phase 2)
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.repositories.store import DataStore, get_store
from app.schemas.auth import UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Returns profile of currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    payload: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    store: DataStore = Depends(get_store),
) -> UserResponse:
    """Updates profile of currently authenticated user."""
    updated = store.update_user(
        user_id=current_user["id"],
        full_name=payload.full_name,
        role=payload.role.value if payload.role else None,
        is_active=payload.is_active,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(updated)
