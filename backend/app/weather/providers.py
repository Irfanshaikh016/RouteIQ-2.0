"""
RouteIQ 2.0 - Weather & Hazard Provider Abstraction (Phase 6)
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional
from app.weather.schemas import HazardEvent, WeatherObservation
from app.repositories.store import get_store


class WeatherProvider(ABC):
    @abstractmethod
    def get_current_conditions(self, latitude: float, longitude: float) -> WeatherObservation:
        pass

    @abstractmethod
    def get_active_hazards(self) -> List[HazardEvent]:
        pass


class StaticWeatherProvider(WeatherProvider):
    """
    Deterministic static provider for development, testing, and offline deployments.
    Labels data clearly as 'STATIC_PROVIDER' to guarantee zero data fabrication.
    """

    def __init__(self):
        self.store = get_store()

    def get_current_conditions(self, latitude: float, longitude: float) -> WeatherObservation:
        # Provide deterministic conditions based on NER geography
        now = datetime.now(timezone.utc)
        return WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            rainfall_mm=2.5,
            temperature_c=24.0,
            wind_speed_kmh=12.0,
            visibility_km=8.5,
            soil_moisture_pct=65.0,
            source="STATIC_PROVIDER",
            observed_at=now,
        )

    def get_active_hazards(self) -> List[HazardEvent]:
        now = datetime.now(timezone.utc)
        active = self.store.get_active_hazards(now)
        return [HazardEvent(**h, is_active=True) for h in active]


_default_weather_provider: Optional[WeatherProvider] = None


def get_weather_provider() -> WeatherProvider:
    global _default_weather_provider
    if _default_weather_provider is None:
        _default_weather_provider = StaticWeatherProvider()
    return _default_weather_provider
