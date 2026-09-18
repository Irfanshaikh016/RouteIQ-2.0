# RouteIQ 2.0 — Database Schema & Data Models

## 1. Relational Entity Relationship (ER) Model

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ USERS : contains
    ORGANIZATIONS ||--o{ VEHICLES : owns
    ORGANIZATIONS ||--o{ LOCATIONS : operates
    ORGANIZATIONS ||--o{ DELIVERIES : dispatches
    LOCATIONS ||--o{ DELIVERIES : "origin (pickup)"
    LOCATIONS ||--o{ DELIVERIES : "destination"

    ORGANIZATIONS {
        uuid id PK
        varchar name
        text description
        timestamp created_at
        timestamp updated_at
    }

    USERS {
        uuid id PK
        uuid organization_id FK
        varchar email UK
        varchar password_hash
        varchar full_name
        varchar role
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    VEHICLES {
        uuid id PK
        uuid organization_id FK
        varchar vehicle_name
        varchar vehicle_type
        varchar registration_number
        float capacity
        varchar capacity_unit
        varchar status
        timestamp created_at
        timestamp updated_at
    }

    LOCATIONS {
        uuid id PK
        uuid organization_id FK
        varchar name
        text address_line
        varchar city
        varchar state
        varchar postal_code
        float latitude
        float longitude
        timestamp created_at
        timestamp updated_at
    }

    DELIVERIES {
        uuid id PK
        uuid organization_id FK
        varchar reference_number
        uuid pickup_location_id FK
        uuid delivery_location_id FK
        varchar priority
        varchar status
        float package_weight
        float package_volume
        date requested_delivery_date
        timestamp time_window_start
        timestamp time_window_end
        text notes
        timestamp created_at
        timestamp updated_at
    }
```

---

## 2. Table Specifications & Constraints

### 2.1 `organizations`
- `id`: UUID (Primary Key, default `gen_random_uuid()`).
- `name`: VARCHAR(128) NOT NULL. Business entity name.
- `description`: TEXT. Optional description.

### 2.2 `users`
- `id`: UUID (Primary Key).
- `organization_id`: UUID REFERENCES `organizations(id)` ON DELETE CASCADE.
- `email`: VARCHAR(255) UNIQUE NOT NULL.
- `password_hash`: VARCHAR(255) NOT NULL (Bcrypt).
- `full_name`: VARCHAR(128) NOT NULL.
- `role`: VARCHAR(32) CHECK (`role IN ('admin', 'manager', 'operator')`).
- `is_active`: BOOLEAN DEFAULT TRUE.

### 2.3 `vehicles`
- `id`: UUID (Primary Key).
- `organization_id`: UUID REFERENCES `organizations(id)` ON DELETE CASCADE.
- `vehicle_name`: VARCHAR(128) NOT NULL.
- `vehicle_type`: VARCHAR(64) NOT NULL.
- `registration_number`: VARCHAR(64) NOT NULL.
- `capacity`: DOUBLE PRECISION CHECK (`capacity >= 0`).
- `capacity_unit`: VARCHAR(32) DEFAULT `'kg'`.
- `status`: VARCHAR(32) CHECK (`status IN ('available', 'assigned', 'inactive', 'maintenance')`).
- Unique Constraint: `(organization_id, registration_number)` prevents registration collisions within an organization.

### 2.4 `locations`
- `id`: UUID (Primary Key).
- `organization_id`: UUID REFERENCES `organizations(id)` ON DELETE CASCADE.
- `name`: VARCHAR(128) NOT NULL.
- `address_line`: TEXT.
- `city`: VARCHAR(64) NOT NULL.
- `state`: VARCHAR(64) NOT NULL.
- `postal_code`: VARCHAR(32).
- `latitude`: DOUBLE PRECISION CHECK (`latitude >= -90.0 AND latitude <= 90.0`).
- `longitude`: DOUBLE PRECISION CHECK (`longitude >= -180.0 AND longitude <= 180.0`).

### 2.5 `deliveries`
- `id`: UUID (Primary Key).
- `organization_id`: UUID REFERENCES `organizations(id)` ON DELETE CASCADE.
- `reference_number`: VARCHAR(64) NOT NULL.
- `pickup_location_id`: UUID REFERENCES `locations(id)` ON DELETE RESTRICT.
- `delivery_location_id`: UUID REFERENCES `locations(id)` ON DELETE RESTRICT.
- `priority`: VARCHAR(32) CHECK (`priority IN ('low', 'normal', 'high', 'urgent')`).
- `status`: VARCHAR(32) CHECK (`status IN ('pending', 'assigned', 'in_transit', 'delivered', 'cancelled')`).
- `package_weight`: DOUBLE PRECISION CHECK (`package_weight >= 0.0`).
- `package_volume`: DOUBLE PRECISION CHECK (`package_volume >= 0.0`).
- `time_window_start` / `time_window_end`: TIMESTAMPTZ.
- Constraint: `time_window_start <= time_window_end`.
- Unique Constraint: `(organization_id, reference_number)`.

---

## 3. Database Migration Management

All database schema evolutions are stored as tracked SQL scripts inside `database/migrations/`:
- `001_phase1_foundation.sql`: Core road nodes, edges, hazard reports, health pings.
- `002_phase2_auth_and_logistics.sql`: Organizations, users, vehicles, locations, deliveries.

### Running Migrations
Use the built-in migration runner:
```bash
# Check status of migrations
python database/migrate.py --status

# Apply pending migrations
python database/migrate.py

# Dry-run verification
python database/migrate.py --verify
```
Migrations are tracked in the PostgreSQL table `schema_migrations`.
