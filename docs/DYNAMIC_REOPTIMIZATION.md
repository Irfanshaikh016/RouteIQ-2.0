# RouteIQ 2.0 — Controlled Dynamic Re-Optimization Pipeline (Phase 6)

## 1. Overview

Operational disruptions (vehicle breakdowns on hill corridors, monsoon landslides severing highways, emergency order cancellations) are standard operating conditions in the North Eastern Region.

RouteIQ 2.0 provides a controlled, debounced dynamic re-optimization pipeline that modifies fleet state and re-solves dispatch assignments without cascading re-routing churn.

## 2. Event Trigger Types

The `POST /api/v1/dispatch/reoptimize` endpoint accepts structured operational disruption events:

| Trigger Type | Handled Disruption | Operational Action |
|---|---|---|
| `VEHICLE_BREAKDOWN` | Mechanical breakdown, puncture, alternator failure | Marks affected vehicle as `maintenance`. Re-assigns pending stops to remaining fleet vehicles. |
| `ROAD_CLOSURE` | Landslide, flash flood inundation, bridge failure | Imposes immediate `CLOSED` road restriction on affected edge. Reroutes all active trips via alternative corridors. |
| `DELIVERY_CANCELLATION` | Customer order cancelled or postponed | Transitions delivery to `cancelled`. Removes stop from active routes and recalculates schedules. |
| `MAJOR_HAZARD` | Emergency meteorological/hazard warning | Registers high-severity hazard polygon. Re-evaluates risk on intersecting paths. |

## 3. Debouncing & Churn Prevention

To protect solver resources and prevent disruptive re-routing oscillations during active operations:
- A minimum interval of **10.0 seconds** is enforced per organization.
- Rapid duplicate or near-simultaneous disruption events within the 10-second window are safely coalesced:
  ```json
  {
    "trigger_type": "VEHICLE_BREAKDOWN",
    "reoptimization_performed": false,
    "message": "Debounced: Re-optimization was already executed within the last 10.0 seconds."
  }
  ```
- Guarantees solver stability under heavy event streams.
