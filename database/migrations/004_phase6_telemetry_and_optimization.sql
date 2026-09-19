-- =============================================================================
-- RouteIQ 2.0 - Phase 6 Migration: Live Telemetry, Weather & Fleet Optimization
-- =============================================================================

-- 1. Vehicle Telemetry Table
CREATE TABLE IF NOT EXISTS vehicle_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    latitude NUMERIC(10, 6) NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude NUMERIC(10, 6) NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    speed NUMERIC(6, 2) NOT NULL CHECK (speed >= 0.0),
    heading NUMERIC(5, 2) CHECK (heading >= 0.0 AND heading <= 360.0),
    ignition_status BOOLEAN DEFAULT true,
    battery_level NUMERIC(5, 2),
    accuracy NUMERIC(6, 2),
    source VARCHAR(64) NOT NULL DEFAULT 'SIMULATED_TEST',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_org_veh_time 
    ON vehicle_telemetry(organization_id, vehicle_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_veh_time 
    ON vehicle_telemetry(vehicle_id, timestamp DESC);

-- 2. Weather Observations Table
CREATE TABLE IF NOT EXISTS weather_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    rainfall_mm NUMERIC(6, 2) DEFAULT 0.0,
    temperature_c NUMERIC(4, 1),
    wind_speed_kmh NUMERIC(5, 2),
    visibility_km NUMERIC(5, 2),
    soil_moisture_pct NUMERIC(5, 2),
    source VARCHAR(64) NOT NULL DEFAULT 'STATIC_PROVIDER',
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_observations(observed_at DESC);

-- 3. Hazard Events Table
CREATE TABLE IF NOT EXISTS hazard_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hazard_type VARCHAR(64) NOT NULL,
    severity NUMERIC(4, 3) NOT NULL CHECK (severity >= 0.0 AND severity <= 1.0),
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    radius_meters NUMERIC(8, 2) DEFAULT 1000.0,
    description TEXT,
    source VARCHAR(64) NOT NULL DEFAULT 'MODELED_HEURISTIC',
    confidence NUMERIC(4, 3) DEFAULT 1.0,
    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hazard_expiry ON hazard_events(expires_at DESC);

-- 4. Dynamic Road Restrictions Table (Infrastructure Level / Shared)
CREATE TABLE IF NOT EXISTS road_restrictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    road_edge_id VARCHAR(128),
    road_name VARCHAR(255),
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'SLOW', 'RESTRICTED', 'CLOSED')),
    speed_multiplier NUMERIC(4, 2) DEFAULT 1.0,
    reason TEXT,
    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_restrictions_edge ON road_restrictions(road_edge_id, status);

-- 5. Optimization Runs Table (Tenant Scoped)
CREATE TABLE IF NOT EXISTS optimization_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    problem_type VARCHAR(32) NOT NULL CHECK (problem_type IN ('CVRP', 'VRPTW')),
    profile VARCHAR(32) NOT NULL DEFAULT 'balanced',
    depot_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    vehicle_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    delivery_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'COMPLETED',
    total_distance_km NUMERIC(10, 2),
    total_duration_minutes NUMERIC(10, 2),
    total_cost NUMERIC(12, 4),
    total_risk NUMERIC(6, 4),
    vehicles_used INT DEFAULT 0,
    served_deliveries_count INT DEFAULT 0,
    unserved_deliveries JSONB DEFAULT '[]'::jsonb,
    routes_payload JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_optimization_org ON optimization_runs(organization_id, created_at DESC);
