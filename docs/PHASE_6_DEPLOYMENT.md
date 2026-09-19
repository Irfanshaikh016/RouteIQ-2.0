# RouteIQ 2.0 — Phase 6 Deployment & Configuration Guide

## 1. Prerequisites

- Python $\ge$ 3.11 with `ortools>=9.8.0`, `networkx>=3.0`, `fastapi`, `uvicorn`.
- Node.js $\ge$ 20 with Next.js 16 (Turbopack).
- PostgreSQL $\ge$ 15 with PostGIS $\ge$ 3.3 (or Supabase).

## 2. Database Migration

Apply SQL migration `004_phase6_telemetry_and_optimization.sql`:
```bash
psql "$DATABASE_URL" -f database/migrations/004_phase6_telemetry_and_optimization.sql
```

The migration defines:
- `vehicle_telemetry`: GPS coordinates, speed, heading, battery, ignition status, PostGIS geometry.
- `weather_observations`: Meteorological data (rainfall, temperature, wind, soil moisture).
- `hazard_events`: Active hazard polygons, severity, spatial radius, temporal expiry (TTL).
- `road_restrictions`: Edge-level closures, speed reduction multipliers, start and expiration timestamps.
- `optimization_runs`: Stored OR-Tools solutions, vehicles used, stop sequence timelines, unserved diagnostics.

## 3. Environment Variables

Add to `backend/.env`:
```bash
# Phase 6 Configuration
ORTOOLS_TIME_LIMIT_SECONDS=30
TELEMETRY_FRESH_MINUTES=5
TELEMETRY_STALE_MINUTES=60
REOPTIMIZATION_DEBOUNCE_SECONDS=10.0
WEATHER_PROVIDER=static
```

Add to `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 4. Health Check Endpoints

Verify operational status:
```bash
# Telemetry Subsystem
curl -s http://localhost:8000/api/v1/telemetry/health | jq

# Weather & Hazards Subsystem
curl -s http://localhost:8000/api/v1/weather/health | jq

# Google OR-Tools Optimization Engine
curl -s http://localhost:8000/api/v1/optimization/health | jq
```
All endpoints return `status: "operational"` with live telemetry, active hazard, and solver metrics.
