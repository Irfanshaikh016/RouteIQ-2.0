"""
RouteIQ 2.0 - Telemetry Repository (Phase 6)
"""
from typing import Any, Dict, List, Optional
from app.repositories.store import DataStore, get_store


class TelemetryRepository:
    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or get_store()

    def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        return self.store.vehicles.get(vehicle_id)

    def list_vehicles(self, organization_id: str) -> List[Dict[str, Any]]:
        return self.store.list_vehicles(organization_id)

    def count_telemetry(self) -> int:
        return len(self.store.vehicle_telemetry)
