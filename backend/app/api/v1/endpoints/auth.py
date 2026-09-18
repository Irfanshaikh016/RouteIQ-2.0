"""
RouteIQ 2.0 - Authentication Endpoints (Phase 2)
Handles registration, login, logout, and token retrieval.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.store import DataStore, get_store
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    store: DataStore = Depends(get_store),
) -> TokenResponse:
    """
    Registers a new user and organization.
    Returns access token and user metadata.
    """
    existing_user = store.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Create new Organization
    org = store.create_organization(
        name=payload.organization_name,
        description=f"Primary organization for {payload.full_name}",
    )

    # Hash password safely
    pwd_hash = hash_password(payload.password)

    # Create User with specified role (default Admin for initial registrant)
    role_val = payload.role.value if payload.role else "admin"
    user = store.create_user(
        organization_id=org["id"],
        email=payload.email,
        password_hash=pwd_hash,
        full_name=payload.full_name,
        role=role_val,
    )

    # Generate JWT
    token = create_access_token(
        subject=user["id"],
        org_id=org["id"],
        role=user["role"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user["id"],
        organization_id=org["id"],
        role=user["role"],
        email=user["email"],
        full_name=user["full_name"],
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    store: DataStore = Depends(get_store),
) -> TokenResponse:
    """
    Authenticates user with email and password.
    Returns signed JWT access token.
    """
    user = store.get_user_by_email(payload.email)
    # Generic failure message to prevent email enumeration
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently suspended or inactive.",
        )

    token = create_access_token(
        subject=user["id"],
        org_id=user["organization_id"],
        role=user["role"],
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user["id"],
        organization_id=user["organization_id"],
        role=user["role"],
        email=user["email"],
        full_name=user["full_name"],
    )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    """
    Logs out the authenticated user.
    Stateless JWT logout acknowledges session termination.
    """
    return {"message": "Successfully logged out. Client should discard token."}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    """Returns the authenticated user's profile details."""
    return UserResponse.model_validate(current_user)
