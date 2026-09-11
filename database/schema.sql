-- ==============================================================================
-- RouteIQ 2.0 — Core Database Schema
-- Compatible with PostgreSQL 15+ and Supabase (PostGIS optional/ready)
-- ==============================================================================

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Nodes Table (Hubs, Junctions, Checkpoints, Cities)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL,                -- e.g. "GAU_01" for Guwahati Hub
    name VARCHAR(128) NOT NULL,                      -- e.g. "Guwahati Central Logistics Hub"
    state VARCHAR(64) NOT NULL,                      -- e.g. "Assam", "Meghalaya"
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION,                    -- Elevation in meters
    node_type VARCHAR(32) DEFAULT 'junction',        -- 'hub', 'junction', 'border_post', 'checkpoint'
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nodes_state ON nodes(state);
CREATE INDEX IF NOT EXISTS idx_nodes_lat_lon ON nodes(latitude, longitude);

-- ------------------------------------------------------------------------------
-- 2. Edges Table (Road Segments / Corridors Connecting Nodes)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL,                -- e.g. "NH06_GAU_SHL"
    name VARCHAR(128) NOT NULL,                      -- e.g. "Guwahati to Shillong (NH 6)"
    source_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE RESTRICT,
    target_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE RESTRICT,
    distance_km DOUBLE PRECISION NOT NULL CHECK (distance_km > 0),
    base_duration_min DOUBLE PRECISION NOT NULL CHECK (base_duration_min > 0),
    terrain_type VARCHAR(32) DEFAULT 'hilly',        -- 'plains', 'hilly', 'mountainous', 'valley'
    surface_quality VARCHAR(32) DEFAULT 'paved',     -- 'paved', 'gravel', 'damaged', 'under_construction'
    max_weight_tonnes DOUBLE PRECISION DEFAULT 40.0,
    base_risk_score DOUBLE PRECISION DEFAULT 0.10 CHECK (base_risk_score >= 0.0 AND base_risk_score <= 1.0),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_active ON edges(is_active);

-- ------------------------------------------------------------------------------
-- 3. Hazard Reports Table (Dynamic incidents: landslides, washouts, floods)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hazard_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edge_id UUID REFERENCES edges(id) ON DELETE SET NULL,
    hazard_type VARCHAR(32) NOT NULL,                -- 'landslide', 'flash_flood', 'road_block', 'bridge_failure'
    severity VARCHAR(16) NOT NULL,                   -- 'low', 'medium', 'high', 'critical'
    description TEXT,
    reported_latitude DOUBLE PRECISION,
    reported_longitude DOUBLE PRECISION,
    is_active BOOLEAN DEFAULT TRUE,
    source VARCHAR(32) DEFAULT 'field_report',       -- 'field_report', 'sensor', 'satellite', 'crowdsource'
    reported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_hazards_edge ON hazard_reports(edge_id);
CREATE INDEX IF NOT EXISTS idx_hazards_active ON hazard_reports(is_active);

-- ------------------------------------------------------------------------------
-- 4. Connectivity Ping / System Audit Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_health_pings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(64) NOT NULL DEFAULT 'routeiq-backend',
    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
    checked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Seed an initial health ping entry
INSERT INTO system_health_pings (service_name, status)
VALUES ('routeiq-backend', 'initialized')
ON CONFLICT DO NOTHING;
