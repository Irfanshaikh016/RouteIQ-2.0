"""
RouteIQ 2.0 - Weather & Hazard Subsystem Exceptions (Phase 6)
"""


class WeatherHazardError(Exception):
    """Base exception for weather and hazard subsystem."""
    pass


class InvalidHazardDataError(WeatherHazardError):
    """Raised when hazard event coordinates or parameters are invalid."""
    pass


class ExpiredHazardError(WeatherHazardError):
    """Raised when attempting to operate on an expired hazard record."""
    pass
