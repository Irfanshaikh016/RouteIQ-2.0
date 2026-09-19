# RouteIQ 2.0 — Vehicle Telemetry Architecture (Phase 6)

## 1. Overview

The vehicle telemetry subsystem ingests, validates, caches, and streams real-time geolocation and operational telemetry fixes from fleet vehicles operating throughout the North Eastern Region.

## 2. Ingestion & Validation Pipeline

Telemetry fixes are received via:
- **HTTP REST Endpoint**: `POST /api/v1/telemetry`
- **WebSocket Streaming**: `/api/v1/telemetry/ws?token=<JWT>`

### Validation Rules
1. **Latitude & Longitude**: Must fall within valid geographic bounds ($-90 \le \text{lat} \le 90$, $-180 \le \text{lon} \le 180$).
2. **Speed**: Must be non-negative ($\ge 0$ km/h).
3. **Heading**: If provided, clamped to $[0, 360]$ degrees.
4. **Battery Level**: If provided, clamped to $[0, 100]$ percent.
5. **Tenant Ownership**: The target `vehicle_id` must exist and belong to the caller's `organization_id`. Cross-tenant ingestion is rejected with HTTP 403 Forbidden.

## 3. Freshness State Machine

Vehicle state freshness is evaluated deterministically using UTC timestamps relative to the latest observation:

```
                  t_delta < 5 min
              +--------------------+
              |        LIVE        | (Active real-time tracking)
              +---------+----------+
                        |
                        | 5 min <= t_delta <= 60 min
                        v
              +--------------------+
              |       STALE        | (Degraded / signal loss)
              +---------+----------+
                        |
                        | t_delta > 60 min OR no pings
                        v
              +--------------------+
              |      OFFLINE       | (Out of service / disconnected)
              +--------------------+
```

### Visual Representation in Operations Console
- **LIVE**: Pulsating emerald green halo ring (`#10b981`).
- **STALE**: Static amber warning ring (`#f59e0b`).
- **OFFLINE**: Dim slate ring (`#64748b`).

## 4. In-Memory Caching & PostGIS Schema

For real-time queries (`GET /api/v1/telemetry/fleet`), fixes are cached in `latest_vehicle_telemetry[vehicle_id]`, eliminating database overhead on sub-second queries.

Historical telemetry is archived in the PostgreSQL/PostGIS database table `vehicle_telemetry`:
```sql
CREATE TABLE IF NOT EXISTS vehicle_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326),
    speed DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    heading DOUBLE PRECISION,
    ignition_status BOOLEAN DEFAULT TRUE,
    battery_level DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    source VARCHAR(64) NOT NULL DEFAULT 'SIMULATED_TEST',
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_telemetry_veh_org ON vehicle_telemetry(vehicle_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_geom ON vehicle_telemetry USING GIST(geom);
```

## 5. Provenance & Synthetic Data Policy
External hardware sensor unavailability is handled strictly:
- No telemetry data is fabricated as genuine hardware fixes.
- Test fixtures and synthetic telemetry are explicitly stamped with `source: 'SIMULATED_TEST'`.
