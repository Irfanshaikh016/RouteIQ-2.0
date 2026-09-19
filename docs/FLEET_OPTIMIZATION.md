# RouteIQ 2.0 — Fleet Optimization Architecture (Phase 6)

## 1. Overview

Fleet optimization in RouteIQ 2.0 solves the combinatorial multi-stop, multi-vehicle distribution problem using Google OR-Tools while leveraging the Phase 4 Dijkstra pathfinder for detailed road network navigation.

## 2. Separation of Concerns: OR-Tools vs Phase 4 Dijkstra

| Dimension | Google OR-Tools (`app.optimization`) | Phase 4 Pathfinder (`app.routing`) |
|---|---|---|
| **Role** | Combinatorial vehicle assignment, stop sequencing, and delivery scheduling. | Ground-truth road pathfinding between any two coordinate nodes. |
| **Problem Domain** | NP-hard Vehicle Routing Problem (CVRP, VRP-TW). | Shortest/safest path across PostGIS & OSM road graph. |
| **Input** | Distance, duration, risk, and cost $N \times N$ matrices. | Origin $(lat, lon)$ and destination $(lat, lon)$. |
| **Output** | Vehicle-stop assignments, arrival/departure timelines, payload profiles. | Detailed GeoJSON LineString road geometry and turn-by-turn edges. |

## 3. Distance, Duration & Risk Matrix Generation

For $N$ stops (depot at index 0, customer deliveries at $1 \dots N$):
1. Node pairs $(i, j)$ are evaluated through the Phase 4 pathfinder using the active cost profile (`fastest`, `safest`, `balanced`).
2. Exact road network distances ($km$), travel times ($minutes$), composite risks, and multi-objective costs are extracted.
3. If road graph nodes are unavailable, fallback geodesic Haversine distance with terrain speed heuristics is applied.
4. Matrix caching ensures sub-second matrix generation across repeated optimization iterations.

## 4. Scaled Integer Cost Modeling

Because Google OR-Tools `RoutingModel` operates with integer-valued arc costs and cumul variables:
- Multi-objective edge costs are multiplied by $100$ and rounded to integers.
- Durations are evaluated in integer minutes ($\lceil t_{\text{min}} \rceil$).
- Vehicle payload demands and capacities are scaled to kilograms.
- Upon solution retrieval, all values are decoded back to exact floating-point metrics for presentation.
