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

-- ==============================================================================
-- Phase 2: Authentication & Core Logistics Data Tables
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 5. Organizations Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);

-- ------------------------------------------------------------------------------
-- 6. Users Table (Multi-tenant with RBAC)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'operator' CHECK (role IN ('admin', 'manager', 'operator')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ------------------------------------------------------------------------------
-- 7. Vehicles Table (Fleet Assets)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    vehicle_name VARCHAR(128) NOT NULL,
    vehicle_type VARCHAR(64) NOT NULL,
    registration_number VARCHAR(64) NOT NULL,
    capacity DOUBLE PRECISION NOT NULL CHECK (capacity >= 0),
    capacity_unit VARCHAR(32) DEFAULT 'kg',
    status VARCHAR(32) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'assigned', 'inactive', 'maintenance')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_org_vehicle_reg UNIQUE (organization_id, registration_number)
);

CREATE INDEX IF NOT EXISTS idx_vehicles_org_id ON vehicles(organization_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);

-- ------------------------------------------------------------------------------
-- 8. Locations Table (Depots, Hubs & Address Stops)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    address_line TEXT,
    city VARCHAR(64) NOT NULL,
    state VARCHAR(64) NOT NULL,
    postal_code VARCHAR(32),
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_locations_org_id ON locations(organization_id);
CREATE INDEX IF NOT EXISTS idx_locations_city_state ON locations(city, state);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);

-- ------------------------------------------------------------------------------
-- 9. Deliveries Table (Shipment Orders)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    reference_number VARCHAR(64) NOT NULL,
    pickup_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE RESTRICT,
    delivery_location_id UUID NOT NULL REFERENCES locations(id) ON DELETE RESTRICT,
    priority VARCHAR(32) NOT NULL DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_transit', 'delivered', 'cancelled')),
    package_weight DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (package_weight >= 0.0),
    package_volume DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (package_volume >= 0.0),
    requested_delivery_date DATE,
    time_window_start TIMESTAMPTZ,
    time_window_end TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_org_delivery_ref UNIQUE (organization_id, reference_number),
    CONSTRAINT chk_delivery_time_window CHECK (
        time_window_start IS NULL OR
        time_window_end IS NULL OR
        time_window_start <= time_window_end
    )
);

CREATE INDEX IF NOT EXISTS idx_deliveries_org_id ON deliveries(organization_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_deliveries_pickup ON deliveries(pickup_location_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_destination ON deliveries(delivery_location_id);

-- ==============================================================================
-- 10. Road Nodes Table (Physical Geographic Graph Vertices - Phase 3)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS road_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    osm_id BIGINT UNIQUE,                                     -- Original OpenStreetMap node ID
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    elevation_m DOUBLE PRECISION,                             -- Elevation in meters (vital for mountain corridors)
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_road_nodes_osm_id ON road_nodes(osm_id);
CREATE INDEX IF NOT EXISTS idx_road_nodes_lat_lon ON road_nodes(latitude, longitude);

-- Conditional PostGIS geometry column and GIST index
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='road_nodes' AND column_name='geom'
        ) THEN
            ALTER TABLE road_nodes ADD COLUMN geom geometry(Point, 4326);
            CREATE INDEX IF NOT EXISTS idx_road_nodes_geom ON road_nodes USING GIST(geom);
        END IF;
    END IF;
END $$;

-- ==============================================================================
-- 11. Road Edges Table (Physical Geographic Road Segments - Phase 3)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS road_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    osm_way_id BIGINT,                                        -- Original OpenStreetMap way ID
    source_node_id UUID NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
    road_name VARCHAR(128),                                   -- e.g. "NH 6 (Guwahati - Shillong Highway)"
    road_type VARCHAR(64) NOT NULL,                           -- 'trunk', 'primary', 'secondary', 'tertiary', etc.
    length_meters DOUBLE PRECISION NOT NULL CHECK (length_meters >= 0.0),
    max_speed_kph DOUBLE PRECISION,                           -- Speed limit if tagged in OSM
    oneway BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_road_edge_source_target_way UNIQUE (osm_way_id, source_node_id, target_node_id)
);

CREATE INDEX IF NOT EXISTS idx_road_edges_source ON road_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_road_edges_target ON road_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_road_edges_type ON road_edges(road_type);
CREATE INDEX IF NOT EXISTS idx_road_edges_way_id ON road_edges(osm_way_id);

-- Conditional PostGIS LineString geometry column and GIST index
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='road_edges' AND column_name='geom'
        ) THEN
            ALTER TABLE road_edges ADD COLUMN geom geometry(LineString, 4326);
            CREATE INDEX IF NOT EXISTS idx_road_edges_geom ON road_edges USING GIST(geom);
        END IF;
    END IF;
END $$;


