# RouteIQ 2.0 — PostGIS Spatial Database Specification

## 1. PostGIS Foundation

RouteIQ 2.0 uses PostgreSQL 15+ with the **PostGIS** spatial extension enabled (`CREATE EXTENSION IF NOT EXISTS postgis;`). PostGIS provides native spatial data types (`geometry(Point, 4326)` and `geometry(LineString, 4326)`) and high-performance R-tree bounding-box indexing via **GIST (Generalized Search Tree)** indexes.

---

## 2. Table Definitions

### Road Nodes (`road_nodes`)
Represents physical road junctions, milestones, and geometry vertices:

```sql
CREATE TABLE IF NOT EXISTS road_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    osm_id BIGINT UNIQUE,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    elevation_m DOUBLE PRECISION,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    geom geometry(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_road_nodes_osm_id ON road_nodes(osm_id);
CREATE INDEX IF NOT EXISTS idx_road_nodes_lat_lon ON road_nodes(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_road_nodes_geom ON road_nodes USING GIST(geom);
```

### Road Edges (`road_edges`)
Represents physical road segments connecting two nodes:

```sql
CREATE TABLE IF NOT EXISTS road_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    osm_way_id BIGINT,
    source_node_id UUID NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
    road_name VARCHAR(128),
    road_type VARCHAR(64) NOT NULL,
    length_meters DOUBLE PRECISION NOT NULL CHECK (length_meters >= 0.0),
    max_speed_kph DOUBLE PRECISION,
    oneway BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    geom geometry(LineString, 4326),
    CONSTRAINT uq_road_edge_source_target_way UNIQUE (osm_way_id, source_node_id, target_node_id)
);

CREATE INDEX IF NOT EXISTS idx_road_edges_source ON road_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_road_edges_target ON road_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_road_edges_type ON road_edges(road_type);
CREATE INDEX IF NOT EXISTS idx_road_edges_way_id ON road_edges(osm_way_id);
CREATE INDEX IF NOT EXISTS idx_road_edges_geom ON road_edges USING GIST(geom);
```

---

## 3. Spatial Query Patterns

### Bounding Box Intersection
```sql
-- Find all road segments intersecting a bounding box (e.g. Guwahati metro area)
SELECT * FROM road_edges
WHERE geom && ST_MakeEnvelope(91.50, 26.00, 92.00, 26.30, 4326);
```

### Distance Calculation
```sql
-- Great circle distance between two points in meters
SELECT ST_DistanceSphere(
    ST_SetSRID(ST_MakePoint(91.8210, 26.1158), 4326),
    ST_SetSRID(ST_MakePoint(91.8933, 25.5788), 4326)
) AS distance_meters;
```

---

## 4. Supabase & Local PostgreSQL Compatibility

1. **Supabase Cloud**: PostGIS is available out-of-the-box on Supabase instances. The conditional migration block safely checks `pg_extension` and adds geometry columns without error.
2. **Local PostgreSQL**: Standard `postgresql-contrib` and `postgis` packages enable full geometry and GIST features.
3. **In-Memory Offline Store**: For unit test isolation and offline execution on development machines without a running Postgres daemon, the Python datastore (`DataStore`) implements pure-Python coordinate bounds and great-circle Haversine math.
