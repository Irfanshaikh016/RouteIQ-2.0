"""
RouteIQ 2.0 - Routing Input Validators (Phase 4)
Provides validation rules for geographic bounds, search thresholds, and profile names.
"""
from typing import Set
from app.routing.exceptions import InvalidCoordinateError, UnsupportedProfileError


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validates that latitude and longitude conform to standard WGS84 bounds."""
    if not isinstance(latitude, (int, float)) or not (-90.0 <= latitude <= 90.0):
        raise InvalidCoordinateError(f"Latitude {latitude} must be a number between -90.0 and +90.0.")
    if not isinstance(longitude, (int, float)) or not (-180.0 <= longitude <= 180.0):
        raise InvalidCoordinateError(f"Longitude {longitude} must be a number between -180.0 and +180.0.")


def validate_profile_name(profile_name: str, supported_profiles: Set[str]) -> str:
    """Validates that requested profile is recognized, returning normalized lowercase name."""
    normalized = profile_name.strip().lower()
    if normalized not in supported_profiles:
        raise UnsupportedProfileError(
            f"Unsupported routing profile '{profile_name}'. Available profiles: {', '.join(sorted(supported_profiles))}"
        )
    return normalized
