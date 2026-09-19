# RouteIQ 2.0 — Logistics Operations Console User Guide

## 1. Overview & Interface Layout

The RouteIQ 2.0 Operations Console is an integrated command center designed for dispatchers, fleet managers, and supply chain analysts operating in India's North Eastern Region.

```
+-------------------------------------------------------------------------------+
| RouteIQ 2.0 Header    | Org: Assam Logistics | Role: Manager | Fleet KPIs     |
+-----------------------+-------------------------------------------------------+
|  [Tab Navigation]     |                                                       |
|  - ⚡ Plan Route      |               Interactive Leaflet GIS Map             |
|  - 📊 Metrics/Compare |               (CartoDB Dark Matter)                   |
|  - 🔍 Explainability  |               8 Toggleable GIS Layers                 |
|  - 🏢 Assets          |               Zoom, NER View, Layer Dropdown, Legend  |
|                       |                                                       |
|  [Active Tab Body]    |                                                       |
|  (Inputs, Profiles,   |                                                       |
|   Cards, Accordion)   |                                                       |
|                       |                                                       |
+-----------------------+-------------------------------------------------------+
```

---

## 2. Operating Procedures

### 2.1 Planning a Route
1. Navigate to `/dashboard` and select the **Plan Route** tab.
2. Enter the origin coordinates (Latitude & Longitude) or click **Regional Hub Presets** to select from 10 major NER cities (Guwahati, Shillong, Silchar, Dimapur, Kohima, Imphal, Agartala, Aizawl, Itanagar, Gangtok).
3. Enter the destination coordinates.
4. Select your optimization objective:
   - **Fastest**: Prioritizes lowest transit time.
   - **Safest**: Avoids high-hazard monsoon corridors, flood-prone valleys, and steep slopes.
   - **Balanced**: Standard harmonic trade-off between speed and hazard risk.
5. Click **Calculate Optimal Route**. The console will render the illuminated route path on the map and automatically transition to the **Metrics** view.

### 2.2 Comparing Profiles Side-by-Side
1. In the **Plan Route** tab, configure the desired origin and destination.
2. Click **Compare 3 Profiles**.
3. The system executes simultaneous evaluations for `Fastest`, `Safest`, and `Balanced`.
4. The map displays the primary route alongside dashed alternate trajectories.
5. The **Metrics** tab populates a neutral, side-by-side comparative table showing distance, duration, objective score, risk score, and terrain penalty for each profile without biased winner classifications.

### 2.3 Inspecting Segment Explainability
1. Once a route is active, switch to the **Explain** tab (`🔍 Segment Explainability`).
2. The list displays all traversed road edges with their road classification and distance.
3. Click any segment to expand its cost and modeled risk breakdown:
   - **Cost Factors**: Distance cost, Time cost, Risk cost, Terrain cost.
   - **Hazard Factors**: Flood risk, Landslide risk, Monsoon risk, Terrain roughness, Surface condition.
4. The corresponding segment on the Leaflet map illuminates in rose (`#f43f5e`) for spatial clarity.

### 2.4 Exploring Strategic Corridors
1. In the sidebar under **NER Strategic Corridors**, click any corridor (e.g. `NH-06 Shillong - Silchar Lifeline`).
2. The **Corridor Detail Modal** opens, displaying:
   - Highway designation and states covered.
   - Total approximate length.
   - Strategic terrain and risk notes.
   - Waypoint breakdown with elevation in meters Above Sea Level (ASL).
3. Click **Set as Origin & Destination** to automatically populate the route planner with the corridor's start and end coordinates.
