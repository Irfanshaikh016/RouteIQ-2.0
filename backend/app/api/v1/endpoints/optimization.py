"""
RouteIQ 2.0 - Fleet Optimization Endpoints (Phase 6)
Provides OR-Tools CVRP, VRP-TW, and multi-profile fleet comparisons with tenant isolation.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_org_id
from app.optimization.exceptions import (
    InfeasibleOptimizationError,
    InfeasibleTimeWindowError,
    OptimizationEngineError,
)
from app.optimization.schemas import (
    OptimizationComparisonResponse,
    OptimizationHealthResponse,
    OptimizationProblemType,
    OptimizationRequest,
    OptimizationResponse,
)
from app.optimization.solver import OptimizationService, get_optimization_service

router = APIRouter()


@router.post("/cvrp", response_model=OptimizationResponse)
async def optimize_cvrp(
    payload: OptimizationRequest,
    org_id: str = Depends(get_current_org_id),
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationResponse:
    """
    Executes Capacitated Vehicle Routing Problem (CVRP) optimization.
    Distributes deliveries among available fleet vehicles without exceeding payload capacities.
    """
    payload.problem_type = OptimizationProblemType.CVRP
    try:
        return service.optimize(org_id, payload)
    except InfeasibleOptimizationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(e), "reason": e.reason, "details": e.details},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Optimization failed: {str(e)}",
        )


@router.post("/vrptw", response_model=OptimizationResponse)
async def optimize_vrptw(
    payload: OptimizationRequest,
    org_id: str = Depends(get_current_org_id),
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationResponse:
    """
    Executes Vehicle Routing Problem with Time Windows (VRP-TW) optimization.
    Enforces payload capacities and delivery time-window schedules.
    """
    payload.problem_type = OptimizationProblemType.VRPTW
    try:
        return service.optimize(org_id, payload)
    except InfeasibleTimeWindowError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "reason": e.reason, "details": e.details},
        )
    except InfeasibleOptimizationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(e), "reason": e.reason, "details": e.details},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Optimization failed: {str(e)}",
        )


@router.post("/compare", response_model=OptimizationComparisonResponse)
async def compare_optimization_profiles(
    payload: OptimizationRequest,
    org_id: str = Depends(get_current_org_id),
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationComparisonResponse:
    """
    Evaluates fastest, safest, and balanced fleet solutions side-by-side.
    Provides neutral metrics without subjective winner rankings.
    """
    try:
        return service.compare_profiles(org_id, payload)
    except InfeasibleOptimizationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(e), "reason": e.reason, "details": e.details},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Optimization comparison failed: {str(e)}",
        )


@router.get("/health", response_model=OptimizationHealthResponse)
async def get_optimization_health(
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationHealthResponse:
    """Reports Google OR-Tools availability, solver version, and supported problem types."""
    return service.get_health()


@router.get("/{optimization_id}")
async def get_optimization_run(
    optimization_id: str,
    org_id: str = Depends(get_current_org_id),
    service: OptimizationService = Depends(get_optimization_service),
) -> Dict[str, Any]:
    """Retrieves previous optimization run for the organization."""
    run = service.get_run(org_id, optimization_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization run '{optimization_id}' not found.",
        )
    return run
