"""
RouteIQ 2.0 - Dispatch Orchestration Service (Phase 6)
Integrates vehicle telemetry, weather hazards, active routes, and re-optimization triggers.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.dispatch.reoptimization import ReoptimizationEngine
from app.dispatch.schemas import (
    DispatchStateResponse,
    ReoptimizationResponse,
    ReoptimizationTriggerRequest,
)
from app.optimization.solver import OptimizationService, get_optimization_service
from app.repositories.store import DataStore, get_store
from app.weather.service import WeatherService, get_weather_service

logger = logging.getLogger("routeiq.dispatch")


class DispatchService:
    def __init__(
        self,
        store: Optional[DataStore] = None,
        optimization_service: Optional[OptimizationService] = None,
        weather_service: Optional[WeatherService] = None,
        reoptimization_engine: Optional[ReoptimizationEngine] = None,
    ):
        self.store = store or get_store()
        self.optimization_service = optimization_service or get_optimization_service()
        self.weather_service = weather_service or get_weather_service()
        self.reopt_engine = reoptimization_engine or ReoptimizationEngine(
            store=self.store,
            optimization_service=self.optimization_service,
            weather_service=self.weather_service,
        )

    def get_dispatch_state(self, org_id: str) -> DispatchStateResponse:
        """Assembles holistic real-time dispatch state for the operational dashboard."""
        org_vehicles = [v for v in self.store.vehicles.values() if v.get("organization_id") == org_id]
        org_deliveries = [d for d in self.store.deliveries.values() if d.get("organization_id") == org_id]
        active_hazards = self.weather_service.get_active_hazards()
        active_restrictions = self.weather_service.get_road_restrictions()
        latest_runs = self.optimization_service.list_runs(org_id, limit=1)
        last_opt = latest_runs[0] if latest_runs else None

        return DispatchStateResponse(
            organization_id=org_id,
            active_vehicles_count=len(org_vehicles),
            active_deliveries_count=len(org_deliveries),
            active_hazards_count=len(active_hazards),
            active_road_restrictions_count=len(active_restrictions),
            last_optimization=last_opt,
            timestamp=datetime.now(timezone.utc),
        )

    def reoptimize(self, org_id: str, req: ReoptimizationTriggerRequest) -> ReoptimizationResponse:
        return self.reopt_engine.process_trigger(org_id, req)

    def get_routes(self, org_id: str) -> List[Dict[str, Any]]:
        runs = self.optimization_service.list_runs(org_id, limit=1)
        if not runs:
            return []
        return runs[0].get("routes_payload", [])


_default_dispatch_service: Optional[DispatchService] = None


def get_dispatch_service() -> DispatchService:
    global _default_dispatch_service
    if _default_dispatch_service is None:
        _default_dispatch_service = DispatchService()
    return _default_dispatch_service
