# RouteIQ 2.0 — Scoped Requirements

## Phase 1 Requirements (Current: Project Foundation)
- [x] **P1-REQ-01**: Verify workspace and initialize Git repository with comprehensive `.gitignore`.
- [x] **P1-REQ-02**: Protect environment variables and provide `.env.example` templates for root, backend, and frontend.
- [ ] **P1-REQ-03**: Set up FastAPI backend with modular architecture (`app/core`, `app/api/v1`, `app/db`).
- [ ] **P1-REQ-04**: Implement `GET /health` endpoint reporting service health and database connection status.
- [ ] **P1-REQ-05**: Configure Supabase and PostgreSQL database connectivity with connection resilience.
- [ ] **P1-REQ-06**: Define initial PostgreSQL database schema (`nodes`, `edges`, `hazard_reports`) in `database/schema.sql`.
- [ ] **P1-REQ-07**: Initialize Next.js 14+ frontend with TypeScript and Tailwind CSS.
- [ ] **P1-REQ-08**: Build RouteIQ application shell with system overview and live backend ping component.
- [ ] **P1-REQ-09**: Connect frontend to backend via typed API client.
- [ ] **P1-REQ-10**: Add automated backend tests using pytest and verify frontend build.
- [ ] **P1-REQ-11**: Author architecture (`docs/architecture.md`) and setup (`docs/setup.md`) documentation.
- [ ] **P1-REQ-12**: Maintain progress tracking in `docs/tasks/progress.txt` and specifications in `docs/tasks/PRD.md`.

## Future Phase Requirements (Preview)
- **Phase 2**: Ingestion pipeline & dynamic road graph modeling (OSM / PostGIS data, NetworkX graph representation).
- **Phase 3**: Spatio-temporal risk modeling (hazard indices, rainfall impact, terrain fragility).
- **Phase 4**: Multi-objective routing engine (Pareto-optimal safety vs. time vs. cost trade-offs).
- **Phase 5**: GIS dashboard & real-time monitoring map with interactive incident reporting.
