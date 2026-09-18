-- ==============================================================================
-- RouteIQ 2.0 — Migration 002: Authentication & Core Logistics Data (Phase 2)
-- Compatible with PostgreSQL 15+ and Supabase
-- ==============================================================================

-- Enable UUID extension if not already available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Organizations Table
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
-- 2. Users Table (Multi-tenant with RBAC)
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
-- 3. Vehicles Table (Fleet Assets)
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
-- 4. Locations Table (Logistics Facilities, Hubs & Address Stops)
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
-- 5. Deliveries Table (Orders & Consignments)
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
