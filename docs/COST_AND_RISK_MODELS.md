# RouteIQ 2.0 — Edge Cost & Risk Assessment Models

## 1. Multi-Objective Edge Cost Formulation

Every directed road segment $(u \to v)$ in the NetworkX graph is evaluated dynamically during pathfinding using a normalized impedance function:

$$\text{cost}(u, v) = w_{\text{dist}} \cdot c_{\text{dist}} + w_{\text{time}} \cdot c_{\text{time}} + w_{\text{risk}} \cdot c_{\text{risk}} + w_{\text{terrain}} \cdot c_{\text{terrain}}$$

### Normalization Components
To ensure no single criterion unintentionally dominates the others, each component is normalized:
- **Distance Component ($c_{\text{dist}}$)**:
  $$c_{\text{dist}} = \frac{\text{length\_meters}}{1000.0} \quad (\text{length in kilometers})$$
- **Time Component ($c_{\text{time}}$)**:
  $$c_{\text{time}} = \frac{\text{travel\_time\_seconds}}{60.0} \quad (\text{duration in minutes})$$
- **Risk Component ($c_{\text{risk}}$)**:
  $$c_{\text{risk}} = r_{\text{overall}} \times c_{\text{time}} \times 2.5$$
  *(Scales hazard penalty proportionally to the duration of exposure on that segment)*
- **Terrain Component ($c_{\text{terrain}}$)**:
  $$c_{\text{terrain}} = r_{\text{terrain}} \times c_{\text{time}} \times 2.0$$

All costs are guaranteed strictly positive ($\text{cost} \ge 0.0001$) to satisfy Dijkstra convergence criteria.

---

## 2. Speed Estimation & Fallback Matrix

Travel time is calculated from segment length and estimated travel speed:

$$\text{travel\_time\_seconds} = \frac{\text{length\_meters}}{\text{speed\_mps}}$$

When OpenStreetMap data contains an explicit `maxspeed` tag, it is converted to km/h and used directly. When missing or invalid, the engine applies documented regional fallback speeds:

| Road Classification | Tagged Fallback Speed (km/h) | Operational Rationale |
|---|---|---|
| `motorway` | 90.0 km/h | Divided expressway sections |
| `trunk` | 60.0 km/h | Major national highways (NH-06, NH-27, NH-29) |
| `primary` | 50.0 km/h | State highways and arterial roads |
| `secondary` | 40.0 km/h | Inter-district valley roads |
| `tertiary` | 30.0 km/h | Rural connectors |
| `unclassified` | 25.0 km/h | Rural unpaved / PMGSY roads |
| `residential` | 20.0 km/h | Urban neighborhood streets |
| `service` | 15.0 km/h | Logistics hub alleys |
| `default` | 30.0 km/h | Fallback for unspecified classifications |

*Note: Speeds represent static baseline commercial logistics estimates, not live traffic sensor telemetry.*

---

## 3. Pluggable Hazard Provider Architecture

The risk model is encapsulated behind the abstract `HazardProvider` interface:

```python
class HazardProvider(ABC):
    @abstractmethod
    def calculate_risk(
        self,
        u_attrs: Dict[str, Any],
        v_attrs: Dict[str, Any],
        edge_attrs: Dict[str, Any],
    ) -> Dict[str, float]:
        pass
```

This modularity allows seamless future replacement by `LiveWeatherHazardProvider`, `SatelliteHazardProvider`, or `MLHazardProvider` without modifying the pathfinder or cost model.

---

## 4. Deterministic Baseline Risk Heuristics (`StaticHazardProvider`)

In Phase 4, the default implementation is `StaticHazardProvider`:

### 1. Monsoon Surface Degradation Table
| Road Surface Tag | Degradation Penalty ($r_{\text{surface}}$) | Monsoon Behavior |
|---|---|---|
| `asphalt` / `concrete` | 0.05 – 0.06 | High drainage resistance |
| `paved` | 0.08 | Standard paved surface |
| `cobblestone` / `sett` | 0.25 – 0.35 | Traction loss when wet |
| `compacted` / `gravel` | 0.45 – 0.55 | Severe rutting, loose stone hazards |
| `unpaved` / `dirt` | 0.75 – 0.85 | Heavy mudding, vehicle bogging |
| `mud` | 0.98 | Impassable for heavy freight |
| Unknown default | 0.25 | Conservative baseline estimate |

### 2. Terrain & Slope Penalty ($r_{\text{terrain}}$)
Calculated from elevation delta $\Delta h = |h_v - h_u|$ and segment length:
$$\text{grade} = \frac{\Delta h}{\text{length\_meters}}$$
$$\text{grade\_risk} = \min\left(\frac{\text{grade}}{0.12}, 1.0\right) \quad (12\% \text{ slope = maximum hazard})$$
$$\text{altitude\_factor} = \min\left(\frac{\max(h_u, h_v) - 500}{1500}, 1.0\right)$$
$$r_{\text{terrain}} = 0.6 \cdot \text{grade\_risk} + 0.4 \cdot \text{altitude\_factor}$$

### 3. Landslide Susceptibility ($r_{\text{landslide}}$)
$$r_{\text{landslide}} = \min(0.5 \cdot \text{grade\_risk} + 0.3 \cdot \text{altitude\_factor} + 0.2 \cdot r_{\text{surface}}, 1.0)$$

### 4. Floodplain Vulnerability ($r_{\text{flood}}$)
Low-lying alluvial river basins ($\le 65\text{m}$, e.g. Brahmaputra floodplain):
- Secondary / rural roads: $0.60$
- Arterial trunk roads: $0.30$
- High elevations ($> 120\text{m}$): $0.05$

### 5. Composite Overall Risk ($r_{\text{overall}}$)
$$r_{\text{overall}} = 0.25 \cdot r_{\text{flood}} + 0.30 \cdot r_{\text{landslide}} + 0.20 \cdot r_{\text{monsoon}} + 0.15 \cdot r_{\text{terrain}} + 0.10 \cdot r_{\text{surface}}$$

*All risk scores are bounded strictly in $[0.0, 1.0]$.*
