"""
RouteIQ 2.0 - Telemetry Subsystem Exceptions (Phase 6)
"""


class TelemetryError(Exception):
    """Base exception for telemetry errors."""
    pass


class InvalidTelemetryError(TelemetryError):
    """Raised when telemetry payload contains invalid coordinates, speeds, or malformed timestamps."""
    pass


class VehicleNotFoundError(TelemetryError):
    """Raised when the specified vehicle does not exist."""
    pass


class CrossTenantTelemetryError(TelemetryError):
    """Raised when attempting to access or ingest telemetry across organization boundaries."""
    pass
