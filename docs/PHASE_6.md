# RouteIQ 2.0 — Phase 6: Live Telemetry, Dynamic Weather Intelligence & OR-Tools Fleet Optimization

## 1. Executive Summary

Phase 6 elevates the RouteIQ 2.0 platform from a single-origin/single-destination point-to-point pathfinder into an **enterprise-grade dynamic multi-vehicle fleet optimization and dispatch platform**.

Tailored specifically for the rugged geography, monsoon vulnerabilities, and infrastructure bottlenecks of India's North Eastern Region (NER), Phase 6 delivers:
- **Live Vehicle Telemetry**: GPS ingestion, WebSocket real-time updates, deterministic freshness tracking (`LIVE` < 5m, `STALE` 5–60m, `OFFLINE` > 60m), and strict multi-tenant isolation.
- **Dynamic Weather & Hazard Intelligence**: Meteorological observations, active hazard lifecycles with TTL/expiry, dynamic road restrictions (`OPEN`, `SLOW`, `RESTRICTED`, `CLOSED`), and dynamic edge impedance calculation without mutating the shared NetworkX road network graph.
- **Google OR-Tools Fleet Optimization**:
  - Capacitated Vehicle Routing Problem (CVRP) enforcing vehicle payload capacities.
  - Vehicle Routing Problem with Time Windows (VRP-TW) enforcing customer delivery time-windows and service durations.
  - Multi-profile neutral fleet comparison (`fastest`, `safest`, `balanced`) without subjective ranking bias.
  - Infeasibility Diagnostic Engine explaining root causes (`DELIVERY_EXCEEDS_MAX_CAPACITY`, `INSUFFICIENT_CAPACITY`, `NO_FEASIBLE_TIME_WINDOW`).
- **Controlled Dynamic Re-Optimization**: Event-driven fleet re-routing upon vehicle breakdown, emergency road closure, or order cancellation with a 10-second debounce window.
- **Operations Console Integration**: Leaflet-based multi-vehicle dispatch map with distinct vehicle palette (`#06b6d4`, `#a855f7`, `#10b981`, `#f59e0b`), stop sequence badges, live freshness halos, and dynamic road closure overlays.

---

## 2. Architecture Overview

```
                                      +---------------------------------------------+
                                      |            Next.js 16 Operations Console     |
                                      |        (DispatchPanel, TelemetryDrawer,     |
                                      |          OptimizationResultCard, Map)       |
                                      +----------------------+----------------------+
                                                             |
                                                             | HTTP REST / WebSockets
                                                             v
+-------------------------------------------------------------------------------------------------------------------------+
|                                               FastAPI Backend (RouteIQ 2.0)                                             |
|                                                                                                                         |
|   +-----------------------+     +-----------------------+     +------------------------+     +-----------------------+   |
|   |   Telemetry Engine    |     |    Weather & Hazard   |     |   OR-Tools Optimizer   |     | Dispatch Orchestrator |   |
|   |  (/api/v1/telemetry)  |     |   (/api/v1/weather)   |     | (/api/v1/optimization) |     |  (/api/v1/dispatch)   |   |
|   | - State Evaluator     |     | - Hazard Lifecycle    |     | - Travel Matrix Gen    |     | - Event Triggering    |   |
|   | - Freshness Machine   |     | - Road Restrictions   |     | - CVRP Solver          |     | - Debounce Engine     |   |
|   | - Multi-tenant Check  |     | - Dynamic Cost Eval   |     | - VRP-TW Solver        |     | - Re-routing Pipe     |   |
|   +-----------+-----------+     +-----------+-----------+     +-----------+------------+     +-----------+-----------+   |
|               |                             |                             |                              |              |
|               +-----------------------------+-----------------------------+------------------------------+              |
|                                             |                                                                           |
|                                             v                                                                           |
|                             +-------------------------------+                                                           |
|                             | Phase 4 Dijkstra Pathfinder   | (Base Road Network & Edge Distance/Time/Risk Computation) |
|                             +---------------+---------------+                                                           |
|                                             |                                                                           |
|                                             v                                                                           |
|                             +-------------------------------+                                                           |
|                             | Immutable NetworkX Base Graph | (Protected against runtime edge mutation)                 |
|                             +---------------+---------------+                                                           |
|                                             |                                                                           |
+---------------------------------------------+---------------------------------------------------------------------------+
                                              |
                                              v
                             +---------------------------------+
                             | PostgreSQL / PostGIS Persistence|
                             |  - vehicle_telemetry            |
                             |  - weather_observations         |
                             |  - hazard_events                |
                             |  - road_restrictions            |
                             |  - optimization_runs            |
                             +---------------------------------+
```

---

## 3. Subsystem Breakdown

| Subsystem | Core Module | Responsibilities |
|---|---|---|
| **Telemetry** | `app.telemetry` | GPS ingestion, validation, freshness classification (`LIVE`, `STALE`, `OFFLINE`), tenant scoping, WebSocket stream. |
| **Weather & Hazards** | `app.weather` | Rainfall, temperature, and soil moisture tracking; active hazard tracking with TTL; road restrictions (`OPEN`, `SLOW`, `RESTRICTED`, `CLOSED`); dynamic edge impedance evaluation. |
| **OR-Tools Optimization** | `app.optimization` | Travel matrix generator, vehicle capacity constraints, customer time windows, dwell time accounting, solver orchestration, multi-profile comparison, infeasibility diagnostics. |
| **Dispatch Orchestration** | `app.dispatch` | State aggregation, disruption triggers (breakdown, closure, cancellation), 10-second debounce window, automatic re-optimization. |
| **Operations Console** | `frontend/src/components/dispatch` | Dispatch tab, depot selector, vehicle/delivery checklist, solution metrics, payload utilization bar, stop timeline, telemetry drawer. |

---

## 4. Verification & Test Metrics

- **Backend Test Suite**: 72 passed, 0 failed across 14 test suites in `backend/tests/`.
  - Baseline tests (Phases 1–5): 47 passing.
  - New Phase 6 tests: 25 passing (`test_telemetry.py`, `test_weather_hazard.py`, `test_dynamic_routing.py`, `test_cvrp.py`, `test_vrptw.py`, `test_reoptimization.py`, `test_security_phase6.py`).
- **Frontend Static Build**: Clean Next.js 16.3.4 Turbopack compilation (`npm run build`, 10/10 static pages, 0 TypeScript errors).
- **Tenant Isolation**: 100% verified across vehicle telemetry, optimization runs, and dispatch states.
