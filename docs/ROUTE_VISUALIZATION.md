# RouteIQ 2.0 — Route Visualization & Explainability

## 1. GeoJSON LineString Standardization

The RouteIQ 2.0 backend produces standardized GeoJSON `LineString` structures from the underlying PostGIS geometries and NetworkX node sequences:

```json
{
  "type": "LineString",
  "coordinates": [
    [91.8210, 26.1158],
    [91.8797, 25.9034],
    [91.8933, 25.5788]
  ]
}
```

### Visual Rendering Pipeline
1. **Coordinate Inversion**: GeoJSON `[lon, lat]` tuples are parsed into Leaflet `[lat, lon]` pairs.
2. **Double-Polyline Rendering**:
   - **Glow Background**: Rendered at `weight: 8` with `opacity: 0.25` in the profile's primary color.
   - **Crisp Foreground**: Rendered at `weight: 4` with `opacity: 0.95` for precise highway tracing.
3. **Viewport Auto-Fitting**: On route calculation, `map.fitBounds(polyline.getBounds(), { padding: [50, 50] })` smoothly pans and zooms the camera to fit the path.
4. **Endpoint Anchors**: High-contrast HTML/SVG div-icons mark Origin (green `A`) and Destination (red `B`).

---

## 2. Multi-Profile Neutral Comparison

When executing `POST /api/v1/routing/compare`, the console evaluates all three optimization profiles:

```
+------------------+---------------+-------------------+-----------------+
| Profile          | Distance (km) | Est Duration (m)  | Modeled Risk    |
+------------------+---------------+-------------------+-----------------+
| Fastest          | 99.0 km       | 108 min           | 0.18            |
| Safest           | 104.2 km      | 124 min           | 0.07            |
| Balanced         | 101.5 km      | 114 min           | 0.12            |
+------------------+---------------+-------------------+-----------------+
```

### Neutrality Guarantee
- No algorithmically declared "winner" badge.
- Every profile displays raw, unadulterated metrics.
- Dispatchers make informed trade-offs based on operational priorities (e.g. urgent medical supplies vs heavy bulk cargo during monsoons).

---

## 3. Explainability Architecture

Every traversed edge in a route carries complete mathematical explainability:

```json
{
  "edge_id": "edge_ghy_nong",
  "road_name": "NH-06 (GS Road North)",
  "road_type": "trunk",
  "length_meters": 52000.0,
  "estimated_time_seconds": 3120,
  "cost_breakdown": {
    "distance_cost": 52.0,
    "time_cost": 52.0,
    "risk_cost": 10.4,
    "terrain_cost": 8.2,
    "total_cost": 122.6
  },
  "risk_breakdown": {
    "flood_risk": 0.12,
    "landslide_risk": 0.08,
    "monsoon_risk": 0.20,
    "terrain_risk": 0.15,
    "surface_risk": 0.05,
    "overall_risk": 0.12
  }
}
```

The user can click any segment in the **Explain** tab to inspect these granular values, providing complete transparency into why the Dijkstra algorithm selected a particular highway corridor.
