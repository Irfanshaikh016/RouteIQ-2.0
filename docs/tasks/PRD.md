# RouteIQ 2.0 — Product Requirements Document (PRD)

## 1. Executive Summary
**RouteIQ 2.0** is an enterprise-grade, cognitive, graph-aware route and logistics intelligence platform tailored specifically for the extreme geography, monsoonal weather, and infrastructure bottlenecks of India's North Eastern Region (NER) — encompassing Assam, Meghalaya, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura, and Sikkim.

Traditional routing services minimize distance or travel duration using static heuristics. In the NER, the shortest path is often fragile: vulnerable to sudden landslides, flood inundation, road collapses, and bottleneck bridges. RouteIQ 2.0 replaces static routing with a continuously-learning dynamic graph decision engine that balances transit speed, terrain fragility, hazard probability, operational cost, and vehicle constraints.

---

## 2. Target Users & Stakeholders
1. **Regional Logistics & Fleet Operators**: Dispatchers, transport managers, and trucking companies moving essential goods, perishables, and construction materials across hilly corridors.
2. **Disaster Management & Emergency Services**: State disaster response teams (SDRF / NDRF) requiring safe, passable routes for relief distribution during monsoon emergencies.
3. **Infrastructure & Highway Authorities**: Engineers and regional monitors tracking road damage, vulnerable choke points, and passability.

---

## 3. Core Capabilities & System Modules

### Module 1: Regional Transport Graph Engine
- Attributed directed graph representation of key NER transit corridors (e.g., Guwahati–Shillong–Silchar, Siliguri Corridor, Dimapur–Kohima–Imphal, Agartala corridor).
- Edge attributes: length, road grade/elevation profile, surface quality, bridge load limits, historical hazard frequency, and dynamic risk index.

### Module 2: Multi-Factor Risk & Hazard Intelligence
- Spatio-temporal evaluation of environmental hazards:
  - Precipitation and flash flood risks
  - Slope instability and landslide probability
  - Road blockage and construction disruptions
- Edge weight adjustment: Risk is continuously integrated into edge impedance.

### Module 3: Multi-Objective Routing Optimization
- Multi-criteria route generation:
  - **Fastest**: Minimal travel duration when conditions are stable.
  - **Safest**: Maximum avoidance of fragile, landslide-prone, or flooded segments.
  - **Balanced / Eco**: Optimal trade-off between fuel efficiency, road quality, and safety margin.

### Module 4: Operations Console & GIS Dashboard
- High-performance web interface providing live corridor monitoring, route comparison, risk heatmaps, and manual or automated incident logging.

---

## 4. Phase-by-Phase Roadmap

| Phase | Title | Focus / Scope | Status |
|---|---|---|---|
| **Phase 1** | **Project Foundation** | Full-stack scaffolding (Next.js + FastAPI), DB connectivity, `/health` endpoint, live ping, test suite, architecture & setup docs. | **Active** |
| **Phase 2** | **Road Network Graph & Ingestion** | PostGIS road graph schema, node/edge seeds for NER corridors, NetworkX graph representation, routing primitives. | Planned |
| **Phase 3** | **Risk Assessment & Hazard Engine** | Hazard scoring algorithms, rainfall/terrain vulnerability indices, dynamic edge weight computation. | Planned |
| **Phase 4** | **Multi-Objective Routing Engine** | Fast / Safe / Balanced routing algorithms, alternative route generation, turn-by-turn waypoint generation. | Planned |
| **Phase 5** | **GIS Dashboard & Real-Time Console** | Map visualization, interactive routing UI, corridor status monitors, and incident reporting. | Planned |

---

## 5. Non-Functional & Quality Requirements
- **Reliability & Resilience**: Graceful degradation when network links or upstream services drop.
- **Security**: Strict separation of secrets, zero hardcoded credentials, CORS isolation, and environment-based configuration.
- **Performance**: Sub-200ms response time for health checks and API status queries.
- **Maintainability**: High test coverage, comprehensive architectural documentation, typed interfaces across frontend and backend.
