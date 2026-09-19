"""
RouteIQ 2.0 - Unified Fleet Optimization Service (Phase 6)
Orchestrates CVRP and VRP-TW solving, multi-profile comparison, and persistence.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import ortools

from app.optimization.cvrp import solve_cvrp
from app.optimization.vrptw import solve_vrptw
from app.optimization.schemas import (
    OptimizationComparisonResponse,
    OptimizationHealthResponse,
    OptimizationProblemType,
    OptimizationRequest,
    OptimizationResponse,
)
from app.repositories.store import DataStore, get_store

logger = logging.getLogger("routeiq.optimization")


class OptimizationService:
    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or get_store()

    def optimize(self, org_id: str, req: OptimizationRequest) -> OptimizationResponse:
        """
        Executes multi-vehicle fleet optimization using Google OR-Tools.
        Supports CVRP (capacity) and VRP-TW (capacity + time windows).
        """
        logger.info(
            f"Executing {req.problem_type.value} fleet optimization for org '{org_id}' "
            f"({len(req.vehicles)} vehicles, {len(req.deliveries)} deliveries, profile: {req.profile})"
        )

        if req.problem_type == OptimizationProblemType.VRPTW:
            result = solve_vrptw(req, org_id)
        else:
            result = solve_cvrp(req, org_id)

        # Persist run in store scoped to tenant
        self.store.create_optimization_run(
            organization_id=org_id,
            problem_type=result.problem_type,
            profile=result.profile,
            depot_location_id=req.depot_location_id or "depot",
            vehicle_ids=[v.vehicle_id for v in req.vehicles],
            delivery_ids=[d.delivery_id for d in req.deliveries],
            status=result.status,
            total_distance_km=result.total_distance_km,
            total_duration_minutes=result.total_duration_minutes,
            total_cost=result.total_cost,
            total_risk=result.total_risk,
            vehicles_used=result.vehicles_used,
            served_deliveries_count=result.served_deliveries_count,
            unserved_deliveries=[u.model_dump() for u in result.unserved_deliveries],
            routes_payload=[r.model_dump() for r in result.routes],
        )

        logger.info(
            f"Optimization '{result.optimization_id}' completed: {result.vehicles_used} vehicles used, "
            f"{result.total_distance_km} km total, {result.served_deliveries_count}/{result.total_deliveries} deliveries served"
        )
        return result

    def compare_profiles(self, org_id: str, req: OptimizationRequest) -> OptimizationComparisonResponse:
        """
        Evaluates fastest, safest, and balanced fleet solutions side-by-side.
        Guarantees zero ranking or winner bias.
        """
        profiles = ["fastest", "safest", "balanced"]
        runs: Dict[str, OptimizationResponse] = {}

        for p in profiles:
            p_req = req.model_copy(update={"profile": p})
            if p_req.problem_type == OptimizationProblemType.VRPTW:
                runs[p] = solve_vrptw(p_req, org_id)
            else:
                runs[p] = solve_cvrp(p_req, org_id)

        return OptimizationComparisonResponse(
            depot_lat=req.depot_lat,
            depot_lon=req.depot_lon,
            profiles=runs,
        )

    def get_run(self, org_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        return self.store.get_optimization_run(org_id, run_id)

    def list_runs(self, org_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self.store.list_optimization_runs(org_id, limit)

    def get_health(self) -> OptimizationHealthResponse:
        return OptimizationHealthResponse(
            status="operational",
            ortools_available=True,
            ortools_version=ortools.__version__,
            supported_problem_types=["CVRP", "VRPTW"],
        )


_default_optimization_service: Optional[OptimizationService] = None


def get_optimization_service() -> OptimizationService:
    global _default_optimization_service
    if _default_optimization_service is None:
        _default_optimization_service = OptimizationService()
    return _default_optimization_service
