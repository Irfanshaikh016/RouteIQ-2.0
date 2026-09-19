"""
RouteIQ 2.0 - Dispatch Orchestration & Re-Optimization Endpoints (Phase 6)
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_org_id, require_role
from app.dispatch.schemas import (
    DispatchStateResponse,
    ReoptimizationResponse,
    ReoptimizationTriggerRequest,
)
from app.dispatch.service import DispatchService, get_dispatch_service

router = APIRouter()


@router.get("/state", response_model=DispatchStateResponse)
async def get_dispatch_state(
    org_id: str = Depends(get_current_org_id),
    service: DispatchService = Depends(get_dispatch_service),
) -> DispatchStateResponse:
    """Retrieves holistic real-time dispatch state for the authenticated organization."""
    return service.get_dispatch_state(org_id)


@router.post("/reoptimize", response_model=ReoptimizationResponse)
async def trigger_reoptimization(
    payload: ReoptimizationTriggerRequest,
    org_id: str = Depends(get_current_org_id),
    _=Depends(require_role(["admin", "manager", "operator"])),
    service: DispatchService = Depends(get_dispatch_service),
) -> ReoptimizationResponse:
    """
    Triggers controlled, debounced fleet re-optimization upon disruptions
    (vehicle breakdown, emergency road closure, delivery cancellation).
    """
    try:
        return service.reoptimize(org_id, payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Re-optimization failed: {str(e)}",
        )


@router.get("/routes")
async def get_active_dispatch_routes(
    org_id: str = Depends(get_current_org_id),
    service: DispatchService = Depends(get_dispatch_service),
) -> List[Dict[str, Any]]:
    """Retrieves active vehicle dispatch routes generated from the latest optimization run."""
    return service.get_routes(org_id)
