"""
RouteIQ 2.0 - Vehicle Telemetry State & Freshness Manager (Phase 6)
Tracks live vehicle positions and computes real-time freshness states.
"""
from datetime import datetime, timezone
from typing import Optional
from app.telemetry.schemas import TelemetryFreshness

LIVE_THRESHOLD_SECONDS = 300.0   # 5 minutes
STALE_THRESHOLD_SECONDS = 3600.0 # 60 minutes


def calculate_freshness(
    telemetry_time: Optional[datetime],
    current_time: Optional[datetime] = None,
) -> TelemetryFreshness:
    """
    Computes deterministic freshness status based on timestamp age:
    - LIVE:    Age < 5 minutes (300s)
    - STALE:   5 minutes <= Age <= 60 minutes (3600s)
    - OFFLINE: Age > 60 minutes or no telemetry available
    """
    if telemetry_time is None:
        return TelemetryFreshness.OFFLINE

    now = current_time or datetime.now(timezone.utc)
    # Ensure tz-awareness
    if telemetry_time.tzinfo is None:
        telemetry_time = telemetry_time.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age_seconds = (now - telemetry_time).total_seconds()

    if age_seconds < 0:
        # Clocks slightly out of sync or telemetry from near future
        return TelemetryFreshness.LIVE
    elif age_seconds < LIVE_THRESHOLD_SECONDS:
        return TelemetryFreshness.LIVE
    elif age_seconds <= STALE_THRESHOLD_SECONDS:
        return TelemetryFreshness.STALE
    else:
        return TelemetryFreshness.OFFLINE
