"""
RouteIQ 2.0 - Weather & Dynamic Hazard Service (Phase 6)
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.weather.providers import WeatherProvider, get_weather_provider
from app.weather.schemas import (
    HazardCreateRequest,
    HazardEvent,
    RoadRestriction,
    RoadRestrictionCreateRequest,
    WeatherHealthResponse,
    WeatherObservation,
)
from app.repositories.store import DataStore, get_store

logger = logging.getLogger("routeiq.weather")


class WeatherService:
    def __init__(
        self,
        store: Optional[DataStore] = None,
        provider: Optional[WeatherProvider] = None,
    ):
        self.store = store or get_store()
        self.provider = provider or get_weather_provider()

    def get_weather_at_location(self, latitude: float, longitude: float) -> WeatherObservation:
        return self.provider.get_current_conditions(latitude, longitude)

    def create_hazard(self, req: HazardCreateRequest) -> HazardEvent:
        now = datetime.now(timezone.utc)
        record = self.store.create_hazard_event(
            hazard_type=req.hazard_type,
            severity=req.severity,
            latitude=req.latitude,
            longitude=req.longitude,
            radius_meters=req.radius_meters,
            description=req.description,
            source=req.source,
            confidence=req.confidence,
            starts_at=req.starts_at or now,
            expires_at=req.expires_at,
        )
        logger.info(f"Created hazard event '{record['id']}' ({req.hazard_type}, severity={req.severity})")
        return HazardEvent(**record, is_active=True)

    def get_active_hazards(self) -> List[HazardEvent]:
        now = datetime.now(timezone.utc)
        hazards = self.store.get_active_hazards(now)
        return [HazardEvent(**h, is_active=True) for h in hazards]

    def set_road_restriction(self, req: RoadRestrictionCreateRequest) -> RoadRestriction:
        now = datetime.now(timezone.utc)
        record = self.store.set_road_restriction(
            road_edge_id=req.road_edge_id,
            status=req.status.value,
            speed_multiplier=req.speed_multiplier,
            reason=req.reason,
            road_name=req.road_name,
            starts_at=req.starts_at or now,
            expires_at=req.expires_at,
        )
        logger.info(f"Set road restriction on edge '{req.road_edge_id}': {req.status.value}")
        return RoadRestriction(**record)

    def get_road_restrictions(self) -> List[RoadRestriction]:
        records = self.store.get_road_restrictions()
        return [RoadRestriction(**r) for r in records]

    def get_health(self) -> WeatherHealthResponse:
        hazards = self.get_active_hazards()
        restrictions = self.get_road_restrictions()
        return WeatherHealthResponse(
            status="operational",
            provider="StaticWeatherProvider",
            provider_reachable=True,
            active_hazards_count=len(hazards),
            active_restrictions_count=len(restrictions),
            last_update_timestamp=datetime.now(timezone.utc),
        )


_default_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    global _default_weather_service
    if _default_weather_service is None:
        _default_weather_service = WeatherService()
    return _default_weather_service
