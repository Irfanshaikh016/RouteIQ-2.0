-- ==============================================================================
-- RouteIQ 2.0 — Migration 003: PostGIS Spatial Road Network (Phase 3)
-- Compatible with PostgreSQL 15+ and Supabase with PostGIS
-- ==============================================================================

-- 1. Enable PostGIS Extension if available
CREATE EXTENSION IF NOT EXISTS postgis;

-- ------------------------------------------------------------------------------
-- 2. Road Nodes Table (Physical Geographic Graph Vertices)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS road_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    osm_id BIGINT UNIQUE,                                     -- Original OpenStreetMap node ID
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    elevation_m DOUBLE PRECISION,                             -- Elevation in meters (vital for mountain corridors)
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Spatial and attribute indexes for road_nodes
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

-- ------------------------------------------------------------------------------
-- 3. Road Edges Table (Physical Geographic Road Segments)
-- ------------------------------------------------------------------------------
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

-- Attribute indexes for road_edges
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
