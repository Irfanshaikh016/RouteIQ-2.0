# RouteIQ 2.0 — Routing Profiles Specification

## 1. Overview

In India's North Eastern Region (NER), optimizing routes strictly for the shortest geodesic distance is often disastrous due to extreme terrain variations, flash flooding, and monsoon-triggered landslides. RouteIQ 2.0 formalizes multi-objective optimization through three deterministic **Routing Profiles**:

1. **Fastest (`fastest`)**
2. **Safest (`safest`)**
3. **Balanced (`balanced`)**

All profile configurations and weights are centralized in `backend/app/routing/profiles.py`.

---

## 2. Objective Weights Matrix

Each profile allocates normalized weights across four fundamental criteria ($w_{\text{dist}} + w_{\text{time}} + w_{\text{risk}} + w_{\text{terrain}} = 1.0$):

| Profile | Distance Weight ($w_{\text{dist}}$) | Time Weight ($w_{\text{time}}$) | Hazard Risk Weight ($w_{\text{risk}}$) | Terrain Difficulty Weight ($w_{\text{terrain}}$) | Primary Operational Role |
|---|---|---|---|---|---|
| **`fastest`** | 0.20 | **0.60** | 0.10 | 0.10 | Urgent emergency dispatch, perishable cargo, time-critical logistics |
| **`safest`** | 0.10 | 0.10 | **0.50** | **0.30** | Hazardous freight, heavy articulated vehicles, peak monsoon transit |
| **`balanced`** | 0.25 | 0.35 | 0.25 | 0.15 | Standard commercial freight, scheduled inter-state linehauls |

---

## 3. Profile Characteristics & Trade-Offs

### 1. Fastest (`fastest`)
- **Objective**: Minimize total estimated transit duration by favoring higher-speed national highway corridors (`trunk`, `motorway`).
- **Trade-Off**: May route through steep escarpment roads or high-rainfall sections if they offer higher posted speeds and wider lanes.

### 2. Safest (`safest`)
- **Objective**: Minimize cumulative exposure to natural hazards, unpaved surfaces, steep mountain grades, and river valley floodplains.
- **Trade-Off**: May accept significantly higher cumulative distance and travel duration to detour around vulnerable mountain sections and unpaved shortcuts.

### 3. Balanced (`balanced`)
- **Objective**: Multi-objective equilibrium that maintains schedule adherence while actively mitigating severe hazard corridors.
- **Trade-Off**: Selects the optimal commercial compromise, avoiding high-risk rural shortcuts while preventing excessively long detours.

---

## 4. Multi-Profile Comparison Policy

The comparison endpoint (`POST /api/v1/routing/compare`) evaluates all three profiles side-by-side for identical origin and destination coordinates.

**Strict Neutrality Policy**:
- The API presents all three route solutions neutrally.
- It does **not** rank routes or declare a "best route", "recommended route", or "winner".
- The selection between speed, safety, and operational balance is the operational prerogative of the logistics fleet dispatcher.
