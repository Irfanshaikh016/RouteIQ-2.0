# RouteIQ 2.0 — North Eastern Region Logistics Intelligence

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3+-black?style=flat&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Supabase](https://img.shields.io/badge/Supabase-Ready-3ECF8E?style=flat&logo=supabase)](https://supabase.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**RouteIQ 2.0** is an enterprise-grade, cognitive, graph-aware route and logistics intelligence platform engineered specifically for the extreme geography, monsoonal weather, and infrastructure bottlenecks of India's North Eastern Region (NER) — covering Assam, Meghalaya, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura, and Sikkim.

Traditional routing services minimize distance or travel duration using static heuristics. In the NER, the shortest path is frequently vulnerable to sudden landslides, flood inundation, road collapses, and bottleneck bridges. RouteIQ 2.0 re-architects logistics dispatch into a dynamic, hazard-resilient decision engine.

---

## 🏛️ System Architecture Overview

```mermaid
graph TD
    A[Next.js 16 Client / Dashboard] -->|HTTP / REST| B[FastAPI Backend API]
    B -->|asyncpg / SQL| C[(PostgreSQL / Supabase)]
    B -->|Pydantic Settings| D[Config Layer & Safety]
    B -->|Health Diagnostics| E[/health Endpoint]
    A -->|Live Status Polling| E
```

### Core Architecture Layers:
1. **Frontend App**: Next.js 16 (App Router, React 19, TypeScript, Tailwind CSS) providing an interactive operations console and real-time connectivity status.
2. **Backend API**: FastAPI asynchronously serving health diagnostics, modular database connectivity, and REST endpoints.
3. **Database Layer**: Modular access layer supporting both local PostgreSQL (via `asyncpg`) and Supabase Cloud.
4. **Resilience & Safety**: Zero hardcoded secrets, strict `.env` isolation, and graceful degradation in decoupled mode.

---

## 🚀 Phase 1 Foundation Deliverables (Completed)
- [x] **FastAPI Backend**: Lifespan management, structured logging, CORS configuration, and modular routing.
- [x] **Health Check Diagnostics**: Direct `/health` and `/api/v1/health` verifying service uptime, version, and database connectivity.
- [x] **Modular Database Layer**: `database/schema.sql` defining `nodes`, `edges`, `hazard_reports`, and `system_health_pings`.
- [x] **Next.js Frontend**: RouteIQ 2.0 dark-mode dashboard with live backend latency counter and database health breakdown.
- [x] **Automated Testing**: Pytest backend suite and Next.js static production build.
- [x] **Documentation**: Complete system architecture, developer setup guide, and product requirements.

## 🔐 Phase 2 Authentication & Core Logistics Data (Completed)
- [x] **JWT & Bcrypt Security**: Password hashing with salted bcrypt and HMAC-SHA256 JWT tokens with 24h expiration.
- [x] **Multi-Tenant Organizations**: Tenant boundary enforcement (`organization_id`) for complete cross-org isolation.
- [x] **Role-Based Access Control**: `admin`, `manager`, and `operator` permissions hierarchy.
- [x] **Vehicle Management**: Fleet tracking with capacities, capacity units, operational status, and unique registration plates.
- [x] **Location Management**: Depots and facility stops with strict geographic coordinate bounds (-90 to 90 lat, -180 to 180 lon).
- [x] **Delivery Orders**: Consignment dispatching with pickup/delivery location references, weight/volume metrics, priority levels, and chronological time windows (`start <= end`).
- [x] **Frontend Management Pages**: Interactive Next.js 16 pages for `/login`, `/register`, `/dashboard`, `/vehicles`, `/locations`, and `/deliveries`.
- [x] **Cross-Tenant Security Tests**: Automated verification proving Organization A cannot access, edit, or delete Organization B assets.
- [x] **Database Migrations**: SQL migration `002_phase2_auth_and_logistics.sql` and Python runner `database/migrate.py`.

## 🗺️ Phase 3 Road Network Graph & OSM Ingestion (Completed)
- [x] **PostGIS Spatial Database Schema**: Migration `003_phase3_road_network.sql` defining `road_nodes` (Point 4326) and `road_edges` (LineString 4326) with GIST spatial indexing.
- [x] **Strategic NER Transport Corridors**: Cataloged 7 primary highway lifelines across 8 NER states (NH-06, NH-27, NH-29/02, NH-08, NH-306, NH-15/415, NH-10) with exact waypoint coordinates and elevations.
- [x] **OpenStreetMap (OSM) Ingestion Engine**: XML/JSON Overpass parser, pure-Python Haversine distance calculator, drivable highway tag filtering, and oneway directionality resolution.
- [x] **NetworkX Spatial Graph Layer**: Thread-safe `nx.DiGraph` builder and cache manager with automatic cache invalidation upon ingestion.
- [x] **Topological Integrity Validation**: Validator auditing coordinate bounds, non-negative lengths, isolated nodes, dead-ends, and connected component ratios.
- [x] **Spatial REST APIs**: `/api/v1/road-network/corridors`, `/stats`, `/health`, `/nodes`, `/edges`, and admin-protected `/ingest`.
- [x] **Render Cloud Deployment**: Declarative service blueprint `render.yaml`.
- [x] **Automated Test Suite**: 30/30 backend tests passing (100% pass rate).

## ⚡ Phase 4 Multi-Objective Routing Optimization (Completed)
- [x] **Modular Routing Subsystem**: `backend/app/routing/` providing cost models, risk heuristics, speed fallbacks, and NetworkX pathfinding.
- [x] **Centralized Routing Profiles**: `fastest`, `safest`, and `balanced` with normalized multi-criteria objective weights.
- [x] **Normalized Edge Cost Formulation**: Multi-objective impedance combining distance, transit time, terrain difficulty, and monsoon hazard penalties.
- [x] **Deterministic Hazard Framework**: Modular `HazardProvider` evaluating floodplains, landslide slope gradients, monsoon surface degradation, and terrain elevation deltas.
- [x] **Thread-Safe Graph Pathfinding**: Dijkstra shortest path with dynamic weight functions without mutating shared graph state.
- [x] **Spatial Nearest-Node Resolution**: High-performance coordinate snapping with bounding-box optimization.
- [x] **Multi-Profile Comparison Engine**: Side-by-side evaluation of fastest, safest, and balanced routes without ranking or winner bias.
- [x] **Routing REST Endpoints**: `/api/v1/routing/route`, `/profiles`, `/health`, and `/compare`.
- [x] **Automated Test Suite**: 44/44 backend tests passing (100% pass rate).

---

## 📁 Repository Structure

```text
RouteIQ-2.0/
├── .planning/               # GSD roadmaps, requirements, and phase plans
├── backend/                 # FastAPI Python backend service
│   ├── app/
│   │   ├── api/v1/          # Versioned API endpoints (auth, logistics, road-network, routing)
│   │   ├── core/            # Pydantic Settings, JWT security & dependencies
│   │   ├── db/              # Modular database session & health checks
│   │   ├── graph/           # NetworkX graph manager, OSM parser, corridors, validation
│   │   ├── repositories/    # Multi-tenant data store & road network repository
│   │   ├── routing/         # Multi-objective routing engine, profiles, cost & risk models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Pytest automated test suite (44/44 passing)
│   │   └── fixtures/        # Sample NER OSM XML test fixture
│   ├── requirements.txt     # Backend dependencies
│   └── .env.example         # Backend environment template
├── database/                # Database schemas and migrations
│   ├── migrations/          # Versioned SQL migrations (001, 002, 003)
│   ├── migrate.py           # Database migration runner script

│   └── schema.sql           # Canonical PostgreSQL / PostGIS schema
├── docs/                    # Complete system documentation suite
├── frontend/                # Next.js 16 TypeScript frontend console
├── render.yaml              # Render cloud infrastructure blueprint
└── README.md
```


---

## ⚡ Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 15+ (local) or a free Supabase project

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
API Documentation will be accessible at: `http://localhost:8000/docs`  
Health Check endpoint: `http://localhost:8000/health`

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
Open `http://localhost:3000` to view the RouteIQ 2.0 console.

### 3. Run Automated Tests
```bash
# Backend tests
python -m pytest backend/tests -v

# Frontend build check
cd frontend && npm run build
```

---

## 🗺️ Progressive Roadmap

| Phase | Milestone | Focus |
|---|---|---|
| **Phase 1** | **Project Foundation** | Full-stack scaffolding, `/health` endpoint, DB connectivity, automated test suite, and docs. |
| **Phase 2** | **Road Network Graph & Ingestion** | PostGIS node/edge schema, OSM ingestion, NetworkX graph representation of NER corridors. |
| **Phase 3** | **Risk Assessment & Hazard Engine** | Rainfall and landslide vulnerability index, dynamic edge weight computation. |
| **Phase 4** | **Multi-Objective Routing Engine** | Multi-criteria graph algorithms (Fastest, Safest, Balanced routes). |
| **Phase 5** | **Interactive GIS Dashboard** | Live map visualization, corridor hazard overlays, and fleet dispatch console. |

---

## 🔒 Security & Quality Standards
- Zero hardcoded credentials or API keys.
- All environment files (`.env`) are excluded by `.gitignore`.
- Graceful degradation: The application boots cleanly even if the database is offline or not yet provisioned.
