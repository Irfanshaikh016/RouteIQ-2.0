# RouteIQ 2.0 — Routing & Optimization REST API Reference

## 1. Overview

All routing endpoints are mounted under `/api/v1/routing` and require valid JWT bearer authentication in the `Authorization` header:

```http
Authorization: Bearer <jwt_access_token>
```

---

## 2. Calculate Route

### `POST /api/v1/routing/route`

Computes an optimal path between geographic coordinates under a specified multi-objective profile.

#### Request Payload
```json
{
  "origin": {
    "latitude": 26.1158,
    "longitude": 91.8210
  },
  "destination": {
    "latitude": 25.5788,
    "longitude": 91.8933
  },
  "profile": "fastest",
  "max_nearest_distance_km": 50.0
}
```

#### Success Response (`200 OK`)
```json
{
  "route_id": "7b7a8d54-b529-445a-8b89-1ea84b5feae8",
  "profile": "fastest",
  "origin": {
    "latitude": 26.1158,
    "longitude": 91.821
  },
  "destination": {
    "latitude": 25.5788,
    "longitude": 91.8933
  },
  "metrics": {
    "distance_km": 68.42,
    "estimated_time_minutes": 68.42,
    "objective_score": 68.42,
    "risk_score": 0.2845,
    "terrain_score": 0.312
  },
  "nodes": [
    {
      "sequence": 1,
      "node_id": "184ff106-9e96-4fa2-9d32-d17e57c617b0",
      "osm_id": 1001,
      "latitude": 26.1158,
      "longitude": 91.821,
      "elevation_m": 55.0
    }
  ],
  "edges": [
    {
      "sequence": 1,
      "edge_id": "5fa2327a-5fe8-4ce6-a790-a299d65154ee",
      "osm_way_id": 2001,
      "source_node_id": "184ff106-9e96-4fa2-9d32-d17e57c617b0",
      "target_node_id": "8bb56d20-4e38-4e8c-8f4b-70c8aa11d82c",
      "road_name": "NH 6 (Guwahati - Nongpoh)",
      "road_type": "trunk",
      "length_meters": 5120.4,
      "estimated_time_seconds": 230.4,
      "cost_breakdown": {
        "distance_cost": 1.024,
        "time_cost": 2.304,
        "risk_cost": 0.352,
        "terrain_cost": 0.125,
        "total_cost": 3.805
      },
      "risk_breakdown": {
        "flood_risk": 0.3,
        "landslide_risk": 0.15,
        "monsoon_risk": 0.22,
        "terrain_risk": 0.18,
        "surface_risk": 0.08,
        "overall_risk": 0.21
      }
    }
  ],
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [91.821, 26.1158],
      [91.868, 26.098]
    ]
  },
  "optimization_metadata": {
    "profile": "fastest",
    "weights": {
      "distance_weight": 0.2,
      "time_weight": 0.6,
      "risk_weight": 0.1,
      "terrain_weight": 0.1
    },
    "segments_count": 5,
    "nodes_count": 6,
    "source_snapped_node_id": "184ff106-9e96-4fa2-9d32-d17e57c617b0",
    "target_snapped_node_id": "2b9cecf3-2e21-4f9e-990a-a5f1e16f3964"
  }
}
```

---

## 3. Compare Routing Profiles

### `POST /api/v1/routing/compare`

Evaluates identical endpoints across all three profiles (`fastest`, `safest`, `balanced`).

#### Request Payload
```json
{
  "origin": {
    "latitude": 26.1158,
    "longitude": 91.8210
  },
  "destination": {
    "latitude": 25.5788,
    "longitude": 91.8933
  }
}
```

#### Success Response (`200 OK`)
```json
{
  "origin": { "latitude": 26.1158, "longitude": 91.821 },
  "destination": { "latitude": 25.5788, "longitude": 91.8933 },
  "routes": [
    { "profile": "fastest", "...": "..." },
    { "profile": "safest", "...": "..." },
    { "profile": "balanced", "...": "..." }
  ]
}
```

---

## 4. List Routing Profiles

### `GET /api/v1/routing/profiles`

Returns catalog of available profiles and objective weights.

#### Success Response (`200 OK`)
```json
{
  "total": 3,
  "profiles": [
    {
      "name": "fastest",
      "description": "Optimizes primarily for minimized transit duration along high-speed corridors.",
      "weights": {
        "distance_weight": 0.2,
        "time_weight": 0.6,
        "risk_weight": 0.1,
        "terrain_weight": 0.1
      },
      "trade_offs": "May select high-elevation mountain segments or rainfall-prone stretches if they offer higher posted speeds."
    },
    {
      "name": "safest",
      "description": "Prioritizes hazard avoidance, minimizing exposure to landslides, steep slopes, and flood plains.",
      "weights": {
        "distance_weight": 0.1,
        "time_weight": 0.1,
        "risk_weight": 0.5,
        "terrain_weight": 0.3
      },
      "trade_offs": "Accepts higher cumulative distance and travel duration in order to detour around vulnerable terrain."
    },
    {
      "name": "balanced",
      "description": "Pragmatic multi-objective equilibrium balancing delivery schedule efficiency with corridor safety.",
      "weights": {
        "distance_weight": 0.25,
        "time_weight": 0.35,
        "risk_weight": 0.25,
        "terrain_weight": 0.15
      },
      "trade_offs": "Avoids severe hazard bottlenecks while maintaining competitive commercial freight delivery times."
    }
  ]
}
```

---

## 5. Routing Engine Health Check

### `GET /api/v1/routing/health`

#### Success Response (`200 OK`)
```json
{
  "status": "healthy",
  "engine_version": "2.0.0",
  "graph_available": true,
  "total_nodes": 10,
  "total_edges": 17,
  "profiles_loaded": ["fastest", "safest", "balanced"]
}
```

---

## 6. Error Codes

| Status Code | Error Meaning | Common Cause |
|---|---|---|
| `400 Bad Request` | Invalid input | Latitude/longitude out of range or unsupported profile name |
| `401 Unauthorized` | Missing / invalid credentials | Missing or expired `Bearer <token>` |
| `404 Not Found` | Unreachable endpoint | Coordinates > 50km from any road node, or disconnected graph |
| `503 Service Unavailable` | Engine uninitialized | Road graph is empty; OSM network data has not been ingested |
