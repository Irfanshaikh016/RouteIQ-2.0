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

## 🚀 Phase 1 Foundation Deliverables

- [x] **FastAPI Backend**: Lifespan management, structured logging, CORS configuration, and modular routing.
- [x] **Health Check Diagnostics**: Direct `/health` and `/api/v1/health` verifying service uptime, version, and database connectivity.
- [x] **Modular Database Layer**: `database/schema.sql` defining `nodes`, `edges`, `hazard_reports`, and `system_health_pings`.
- [x] **Next.js Frontend**: RouteIQ 2.0 dark-mode dashboard with live backend latency counter and database health breakdown.
- [x] **Automated Testing**: pytest backend suite and Next.js static production build.
- [x] **Documentation**: Complete system architecture, developer setup guide, and product requirements.

---

## 📁 Repository Structure

```text
RouteIQ-2.0/
├── .planning/               # GSD roadmaps, requirements, and phase plans
├── backend/                 # FastAPI Python backend service
│   ├── app/
│   │   ├── api/v1/          # Versioned API endpoints (health)
│   │   ├── core/            # Pydantic Settings & environment config
│   │   ├── db/              # Modular database session & health checks
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/               # Pytest automated test suite
│   ├── requirements.txt     # Backend dependencies
│   └── .env.example         # Backend environment template
├── database/                # Database schemas and migrations
│   └── schema.sql           # Core PostgreSQL / Supabase schema
├── docs/                    # Architecture, setup, and PRD documentation
│   ├── architecture.md      # Detailed system architecture
│   ├── setup.md             # Developer environment setup
│   └── tasks/               # PRD, progress logs, and phase specifications
└── frontend/                # Next.js 16 TypeScript frontend
    ├── src/
    │   ├── app/             # App router pages & layouts
    │   ├── components/      # UI widgets (ConnectivityStatus, Header, Cards)
    │   └── lib/             # Typed API client
    ├── package.json         # Frontend dependencies & scripts
    └── .env.example         # Frontend environment template
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
