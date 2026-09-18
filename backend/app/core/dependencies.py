"""
RouteIQ 2.0 - Core FastAPI Dependencies (Phase 2)
Provides authentication verification, role-based authorization (RBAC),
and organization tenant scoping.
"""
from typing import Any, Callable, Dict, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.repositories.store import DataStore, get_store

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    store: DataStore = Depends(get_store),
) -> Dict[str, Any]:
    """
    Validates JWT token from Authorization header and returns current authenticated user.
    Raises HTTP 401 if invalid, expired, or user not found/inactive.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_org_id(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> str:
    """Returns the authenticated user's organization_id for strict tenant isolation."""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any organization",
        )
    return str(org_id)


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Factory creating a dependency that enforces RBAC on endpoints.
    e.g. Depends(require_role(["admin", "manager"]))
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "operator")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {', '.join(allowed_roles)} (current: {user_role})",
            )
        return current_user

    return role_checker
