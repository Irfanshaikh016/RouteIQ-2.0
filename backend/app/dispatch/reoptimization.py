"""
RouteIQ 2.0 - Controlled Dynamic Re-Optimization Pipeline (Phase 6)
Executes event-driven, debounced fleet re-optimization upon operational disruptions
(breakdowns, road closures, severe hazards, cancellations).
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.dispatch.schemas import (
    ReoptimizationResponse,
    ReoptimizationTriggerRequest,
    ReoptimizationTriggerType,
)
from app.optimization.schemas import (
    DeliveryItem,
    OptimizationProblemType,
    OptimizationRequest,
    OptimizationResponse,
    VehicleItem,
)
from app.optimization.solver import OptimizationService, get_optimization_service
from app.repositories.store import DataStore, get_store
from app.weather.schemas import RoadRestrictionCreateRequest, RoadRestrictionStatus
from app.weather.service import WeatherService, get_weather_service

logger = logging.getLogger("routeiq.dispatch.reopt")

# Debounce tracking per organization: maps org_id -> last reoptimization timestamp
_last_reopt_timestamps: Dict[str, datetime] = {}
DEBOUNCE_MIN_INTERVAL_SECONDS = 10.0


class ReoptimizationEngine:
    def __init__(
        self,
        store: Optional[DataStore] = None,
        optimization_service: Optional[OptimizationService] = None,
        weather_service: Optional[WeatherService] = None,
    ):
        self.store = store or get_store()
        self.optimization_service = optimization_service or get_optimization_service()
        self.weather_service = weather_service or get_weather_service()

    def process_trigger(
        self,
        org_id: str,
        req: ReoptimizationTriggerRequest,
    ) -> ReoptimizationResponse:
        """
        Validates the event, adjusts fleet or infrastructure state, debounces rapid triggers,
        and re-runs OR-Tools fleet optimization to restore operational continuity.
        """
        now = datetime.now(timezone.utc)
        last_time = _last_reopt_timestamps.get(org_id)

        # 1. Debounce check
        if last_time and (now - last_time).total_seconds() < DEBOUNCE_MIN_INTERVAL_SECONDS:
            logger.info(f"Re-optimization for org '{org_id}' debounced (rapid trigger within {DEBOUNCE_MIN_INTERVAL_SECONDS}s)")
            return ReoptimizationResponse(
                trigger_type=req.trigger_type.value,
                reoptimization_performed=False,
                message=f"Debounced: Re-optimization was already executed within the last {DEBOUNCE_MIN_INTERVAL_SECONDS} seconds.",
                affected_vehicle_id=req.affected_vehicle_id,
                affected_road_edge_id=req.affected_road_edge_id,
            )

        logger.info(f"Executing controlled re-optimization for org '{org_id}' on event {req.trigger_type.value}: {req.reason}")

        # 2. Apply Event State Mutations
        if req.trigger_type == ReoptimizationTriggerType.VEHICLE_BREAKDOWN and req.affected_vehicle_id:
            # Mark vehicle as maintenance / stopped
            veh = self.store.vehicles.get(req.affected_vehicle_id)
            if veh and veh.get("organization_id") == org_id:
                veh["status"] = "maintenance"
                logger.info(f"Marked broken down vehicle '{req.affected_vehicle_id}' as maintenance.")

        elif req.trigger_type == ReoptimizationTriggerType.ROAD_CLOSURE and req.affected_road_edge_id:
            # Impose immediate road closure restriction
            self.weather_service.set_road_restriction(
                RoadRestrictionCreateRequest(
                    road_edge_id=req.affected_road_edge_id,
                    status=RoadRestrictionStatus.CLOSED,
                    speed_multiplier=0.0,
                    reason=f"Emergency closure: {req.reason}",
                )
            )
            logger.info(f"Imposed road closure on edge '{req.affected_road_edge_id}'.")

        elif req.trigger_type == ReoptimizationTriggerType.DELIVERY_CANCELLATION and req.affected_delivery_id:
            deliv = self.store.deliveries.get(req.affected_delivery_id)
            if deliv and deliv.get("organization_id") == org_id:
                deliv["status"] = "cancelled"
                logger.info(f"Marked cancelled delivery '{req.affected_delivery_id}' as cancelled.")

        # 3. Assemble Current Fleet & Deliveries for Organization
        available_vehicles = [
            v for v in self.store.vehicles.values()
            if v.get("organization_id") == org_id and v.get("status") == "available"
        ]
        pending_deliveries = [
            d for d in self.store.deliveries.values()
            if d.get("organization_id") == org_id and d.get("status") in ("pending", "assigned")
        ]

        if not available_vehicles or not pending_deliveries:
            _last_reopt_timestamps[org_id] = now
            return ReoptimizationResponse(
                trigger_type=req.trigger_type.value,
                reoptimization_performed=False,
                message="No re-optimization performed: insufficient available vehicles or pending deliveries.",
                affected_vehicle_id=req.affected_vehicle_id,
                affected_road_edge_id=req.affected_road_edge_id,
            )

        # 4. Resolve Depot Location
        depot_lat = 26.1158  # Default Guwahati
        depot_lon = 91.8210
        if req.depot_location_id:
            loc = self.store.locations.get(req.depot_location_id)
            if loc:
                depot_lat = float(loc.get("latitude", 26.1158))
                depot_lon = float(loc.get("longitude", 91.8210))

        # 5. Build Re-Optimization Request
        delivery_items = []
        for d in pending_deliveries:
            loc = self.store.locations.get(d.get("delivery_location_id")) if d.get("delivery_location_id") else None
            lat = float(loc["latitude"]) if loc else float(d.get("dest_lat") or 25.5788)
            lon = float(loc["longitude"]) if loc else float(d.get("dest_lng") or 91.8933)
            weight = float(d.get("package_weight") or 50.0)
            delivery_items.append(
                DeliveryItem(
                    delivery_id=d["id"],
                    latitude=lat,
                    longitude=lon,
                    demand=weight,
                    service_duration_minutes=15,
                )
            )

        opt_req = OptimizationRequest(
            depot_location_id=req.depot_location_id,
            depot_lat=depot_lat,
            depot_lon=depot_lon,
            problem_type=OptimizationProblemType.CVRP,
            profile=req.profile,
            vehicles=[
                VehicleItem(
                    vehicle_id=v["id"],
                    capacity=float(v.get("capacity", 1000.0)),
                    vehicle_name=v.get("vehicle_name"),
                )
                for v in available_vehicles
            ],
            deliveries=delivery_items,
        )

        # 6. Execute OR-Tools Re-Optimization
        updated_result = self.optimization_service.optimize(org_id, opt_req)
        _last_reopt_timestamps[org_id] = now

        return ReoptimizationResponse(
            trigger_type=req.trigger_type.value,
            reoptimization_performed=True,
            message=f"Re-optimization successfully completed: {updated_result.vehicles_used} vehicles deployed.",
            affected_vehicle_id=req.affected_vehicle_id,
            affected_road_edge_id=req.affected_road_edge_id,
            updated_optimization=updated_result,
        )
