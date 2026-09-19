"""
RouteIQ 2.0 - Vehicle Telemetry Provider Abstraction (Phase 6)
Defines provider interface for GPS ingestion and deterministic simulated fixtures.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.telemetry.schemas import TelemetryIngestRequest, VehicleTelemetryResponse
from app.telemetry.state import calculate_freshness
from app.repositories.store import get_store


class TelemetryProvider(ABC):
    """Abstract interface for GPS/device telemetry ingestion and retrieval."""

    @abstractmethod
    def ingest_telemetry(self, org_id: str, req: TelemetryIngestRequest) -> VehicleTelemetryResponse:
        pass

    @abstractmethod
    def get_latest_telemetry(self, org_id: str, vehicle_id: str) -> Optional[VehicleTelemetryResponse]:
        pass

    @abstractmethod
    def get_fleet_telemetry(self, org_id: str) -> List[VehicleTelemetryResponse]:
        pass


class SimulatedTelemetryProvider(TelemetryProvider):
    """
    Deterministic telemetry provider used for tests, local development, and offline demonstrations.
    CRITICAL: Always tags records with source='SIMULATED_TEST' to guarantee zero data fabrication.
    """

    def __init__(self):
        self.store = get_store()

    def ingest_telemetry(self, org_id: str, req: TelemetryIngestRequest) -> VehicleTelemetryResponse:
        record = self.store.record_telemetry(
            organization_id=org_id,
            vehicle_id=req.vehicle_id,
            timestamp=req.timestamp,
            latitude=req.latitude,
            longitude=req.longitude,
            speed=req.speed,
            heading=req.heading,
            ignition_status=req.ignition_status,
            battery_level=req.battery_level,
            accuracy=req.accuracy,
            source=req.source if req.source != "LIVE_GPS" else "SIMULATED_TEST",
            metadata=req.metadata,
        )
        freshness = calculate_freshness(record["timestamp"])
        return VehicleTelemetryResponse(**record, freshness=freshness)

    def get_latest_telemetry(self, org_id: str, vehicle_id: str) -> Optional[VehicleTelemetryResponse]:
        rec = self.store.get_latest_telemetry(org_id, vehicle_id)
        if not rec:
            return None
        freshness = calculate_freshness(rec["timestamp"])
        return VehicleTelemetryResponse(**rec, freshness=freshness)

    def get_fleet_telemetry(self, org_id: str) -> List[VehicleTelemetryResponse]:
        records = self.store.get_fleet_telemetry(org_id)
        now = datetime.now(timezone.utc)
        result = []
        for r in records:
            freshness = calculate_freshness(r["timestamp"], now)
            result.append(VehicleTelemetryResponse(**r, freshness=freshness))
        return result


# Singleton instance
_default_provider: Optional[TelemetryProvider] = None


def get_telemetry_provider() -> TelemetryProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = SimulatedTelemetryProvider()
    return _default_provider
