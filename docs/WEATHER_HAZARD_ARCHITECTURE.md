# RouteIQ 2.0 — Dynamic Weather & Hazard Intelligence Architecture (Phase 6)

## 1. Overview

In India's North Eastern Region, monsoonal flash floods, hillside landslides, and severe waterlogging frequently sever primary highway arteries (such as NH-06, NH-27, and NH-37). The dynamic weather and hazard subsystem injects real-time road conditions and environmental restrictions into the routing engine while preserving graph immutability.

## 2. Weather Observations & Providers

The system uses an extensible provider architecture:
- `WeatherProvider` (Abstract Base Class): Defines `get_weather(lat, lon)` and `get_hazards()`.
- `StaticWeatherProvider`: Default production fallback providing deterministic, documented meteorological fixtures for key NER coordinates (Guwahati, Shillong, Silchar, Jorhat, Dibrugarh).
- All modeled heuristic risks are labeled `source: "MODELED_HEURISTIC"`.

## 3. Hazard Lifecycle & Expiration (TTL)

Hazards are transient events governed by strict temporal validity:
- **Registration**: `POST /api/v1/weather/hazards`
- **Fields**: `hazard_type`, `severity` ($0.0 \dots 1.0$), `latitude`, `longitude`, `radius_meters`, `starts_at`, `expires_at`.
- **Automatic Pruning**:
  Queries for active hazards evaluate:
  $$\text{starts\_at} \le t_{\text{current}} \le \text{expires\_at}$$
  Expired hazards are disregarded during routing cost calculations.

## 4. Road Restrictions

Infrastructure-level road restrictions apply to specific edges in the road graph:

| Status | Behavior in Routing Engine | Cost Multiplier |
|---|---|---|
| `OPEN` | Unrestricted transit. | $1.0\times$ |
| `SLOW` | Transit permitted at reduced speed limit due to waterlogging or debris. | Travel time increased by $\frac{1}{\text{speed\_multiplier}}$ |
| `RESTRICTED` | Vehicle weight or class limits imposed. | Penalized traversal |
| `CLOSED` | Road completely impassable due to major landslide or bridge collapse. | Avoided with infinite impedance ($10^8$) |

## 5. Dynamic Cost Evaluation & Graph Immutability

To prevent race conditions, memory leaks, and corrupting shared spatial indices during concurrent multi-tenant routing, the underlying NetworkX road network graph is **never mutated**:

1. Base road lengths, gradient, and surface attributes remain unchanged in the graph.
2. During pathfinding, edge traversal cost is calculated dynamically in `calculate_dynamic_edge_cost()`:
   - Evaluates active restrictions for edge `id` from the datastore.
   - If `status == CLOSED`: Returns `CLOSED_ROAD_IMPEDANCE = 100000000.0`.
   - If `status == SLOW`: Adjusts speed by `speed_multiplier`.
   - Checks proximity to active localized hazards and applies composite risk penalty.
3. Thread safety and graph immutability are guaranteed.
