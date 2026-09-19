"""
RouteIQ 2.0 - Telemetry Ingestion & Fleet State Service (Phase 6)
Enforces multi-tenant scoping and orchestrates vehicle state tracking.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.telemetry.exceptions import (
    CrossTenantTelemetryError,
    InvalidTelemetryError,
    VehicleNotFoundError,
)
from app.telemetry.providers import TelemetryProvider, get_telemetry_provider
from app.telemetry.repository import TelemetryRepository
from app.telemetry.schemas import (
    FleetTelemetrySummary,
    TelemetryFreshness,
    TelemetryHealthResponse,
    TelemetryIngestRequest,
    VehicleStateResponse,
    VehicleTelemetryResponse,
)
from app.telemetry.state import calculate_freshness

logger = logging.getLogger("routeiq.telemetry")


class TelemetryService:
    def __init__(
        self,
        repository: Optional[TelemetryRepository] = None,
        provider: Optional[TelemetryProvider] = None,
    ):
        self.repository = repository or TelemetryRepository()
        self.provider = provider or get_telemetry_provider()

    def ingest_telemetry(self, organization_id: str, req: TelemetryIngestRequest) -> VehicleTelemetryResponse:
        """Ingests a telemetry ping from a vehicle with tenant boundary validation."""
        vehicle = self.repository.get_vehicle(req.vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle '{req.vehicle_id}' does not exist.")

        if vehicle.get("organization_id") != organization_id:
            logger.warning(
                f"Cross-tenant telemetry ingestion attempt: user org '{organization_id}' "
                f"tried to send telemetry for vehicle '{req.vehicle_id}' belonging to org '{vehicle.get('organization_id')}'"
            )
            raise CrossTenantTelemetryError("Access forbidden: vehicle belongs to another organization.")

        # Ingest and track in store
        telemetry = self.provider.ingest_telemetry(organization_id, req)
        logger.info(f"Ingested telemetry for vehicle '{req.vehicle_id}' (speed: {req.speed} km/h, freshness: {telemetry.freshness})")
        return telemetry

    def get_vehicle_state(self, organization_id: str, vehicle_id: str) -> VehicleStateResponse:
        """Retrieves real-time vehicle state including latest GPS fix and freshness."""
        vehicle = self.repository.get_vehicle(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle '{vehicle_id}' does not exist.")

        if vehicle.get("organization_id") != organization_id:
            raise CrossTenantTelemetryError("Access forbidden: vehicle belongs to another organization.")

        latest_tel = self.provider.get_latest_telemetry(organization_id, vehicle_id)
        freshness = latest_tel.freshness if latest_tel else TelemetryFreshness.OFFLINE

        return VehicleStateResponse(
            vehicle_id=vehicle["id"],
            organization_id=organization_id,
            vehicle_name=vehicle.get("vehicle_name", "Vehicle"),
            registration_number=vehicle.get("registration_number", ""),
            vehicle_type=vehicle.get("vehicle_type", "truck"),
            capacity=float(vehicle.get("capacity", 1000.0)),
            capacity_unit=vehicle.get("capacity_unit", "kg"),
            status=vehicle.get("status", "available"),
            freshness=freshness,
            latest_telemetry=latest_tel,
            current_load=0.0,
            assigned_route_id=None,
        )

    def get_fleet_state(self, organization_id: str) -> FleetTelemetrySummary:
        """Aggregates fleet status and telemetry freshness for the entire organization."""
        vehicles = self.repository.list_vehicles(organization_id)
        states: List[VehicleStateResponse] = []
        live_c = 0
        stale_c = 0
        offline_c = 0

        for v in vehicles:
            vid = v["id"]
            latest_tel = self.provider.get_latest_telemetry(organization_id, vid)
            freshness = latest_tel.freshness if latest_tel else TelemetryFreshness.OFFLINE

            if freshness == TelemetryFreshness.LIVE:
                live_c += 1
            elif freshness == TelemetryFreshness.STALE:
                stale_c += 1
            else:
                offline_c += 1

            states.append(
                VehicleStateResponse(
                    vehicle_id=vid,
                    organization_id=organization_id,
                    vehicle_name=v.get("vehicle_name", "Vehicle"),
                    registration_number=v.get("registration_number", ""),
                    vehicle_type=v.get("vehicle_type", "truck"),
                    capacity=float(v.get("capacity", 1000.0)),
                    capacity_unit=v.get("capacity_unit", "kg"),
                    status=v.get("status", "available"),
                    freshness=freshness,
                    latest_telemetry=latest_tel,
                    current_load=0.0,
                    assigned_route_id=None,
                )
            )

        return FleetTelemetrySummary(
            organization_id=organization_id,
            total_vehicles=len(vehicles),
            live_count=live_c,
            stale_count=stale_c,
            offline_count=offline_c,
            vehicles=states,
        )

    def get_health(self) -> TelemetryHealthResponse:
        total = self.repository.count_telemetry()
        return TelemetryHealthResponse(
            status="operational",
            service="vehicle-telemetry",
            ingestion_available=True,
            total_ingested_records=total,
            last_telemetry_timestamp=datetime.now(timezone.utc) if total > 0 else None,
        )


_default_service: Optional[TelemetryService] = None


def get_telemetry_service() -> TelemetryService:
    global _default_service
    if _default_service is None:
        _default_service = TelemetryService()
    return _default_service
