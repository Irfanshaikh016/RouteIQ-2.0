# RouteIQ 2.0 — Project Context

## Overview
**RouteIQ 2.0** is a cognitive, graph-aware, self-learning route and logistics intelligence platform specifically engineered for the North Eastern Region (NER) of India. 

Conventional route optimization tools prioritize distance or transit speed, which fails in high-risk, terrain-sensitive geographies where the shortest road is frequently the most fragile (prone to landslides, flash floods, road washouts, and severe monsoon conditions). RouteIQ 2.0 models the regional transportation network as a dynamic, attributed graph with continuously learning edge weights.

## Technology Stack
- **Frontend**: Next.js 14+ (App Router), React, TypeScript, Tailwind CSS
- **Backend**: Python 3.14, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy / asyncpg, Supabase Client
- **Database**: Supabase / PostgreSQL (PostGIS-ready)
- **Intelligence & Planning (Future Phases)**: NetworkX, PyTorch Geometric (GNNs), Spatio-Temporal Transformers, NSGA-II / OR-Tools (Multi-Objective Optimization)
- **Deployment**: Vercel (Frontend), Containerized / Cloud VM (Backend)

## Architecture Principles
1. **Separation of Concerns**: Clean separation between ingestion, data layer, graph modeling, optimization, API services, and client dashboards.
2. **Resilience First**: Graceful degradation when network links, live data feeds, or database connections experience latency or disconnection.
3. **Strict Secrets & Config**: No credentials committed to version control; 12-factor configuration via validated environment variables.
4. **Production-Ready**: Type safety across the stack, automated testing, structured logging, and thorough documentation.
