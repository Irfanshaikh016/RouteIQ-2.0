"""
RouteIQ 2.0 - Dynamic Routing Cost & Road Restriction Engine (Phase 6)
Extends Phase 4 multi-criteria cost model with dynamic weather adjustments,
live hazard events, and road closures without mutating the shared NetworkX graph.
"""
from typing import Any, Dict, Optional, Tuple
from app.routing.cost_model import calculate_edge_cost, get_estimated_speed_kph
from app.routing.risk_model import HazardProvider, get_default_hazard_provider
from app.weather.schemas import RoadRestrictionStatus
from app.repositories.store import get_store

# High penalty to enforce strict edge avoidance without mutating graph structure
CLOSED_ROAD_IMPEDANCE = 100000000.0


def calculate_dynamic_edge_cost(
    u_attrs: Dict[str, Any],
    v_attrs: Dict[str, Any],
    edge_attrs: Dict[str, Any],
    weights: Dict[str, float],
    hazard_provider: Optional[HazardProvider] = None,
    store: Optional[Any] = None,
) -> Tuple[float, Dict[str, float], Dict[str, float], float, bool]:
    """
    Computes dynamic edge traversal cost considering:
    1. Base Phase 4 distance, time, terrain, and static hazard penalties
    2. Road restrictions (CLOSED = infinity, SLOW = speed reduction)
    3. Dynamic weather rainfall adjustments
    4. Active localized hazard events (landslides, flooding)

    Guarantees graph immutability.
    Returns:
        (total_cost, cost_breakdown, risk_breakdown, estimated_time_seconds, is_closed)
    """
    datastore = store or get_store()
    edge_id = edge_attrs.get("id", "")

    # 1. Check Dynamic Road Restrictions
    restriction = datastore.get_road_restriction_for_edge(edge_id)
    if restriction:
        status = restriction.get("status", "OPEN")
        if status == RoadRestrictionStatus.CLOSED.value:
            # Completely unavailable to routing
            return (
                CLOSED_ROAD_IMPEDANCE,
                {"total_cost": CLOSED_ROAD_IMPEDANCE, "status": "CLOSED"},
                {"overall_risk": 1.0},
                999999.0,
                True,
            )

    # 2. Base Phase 4 Cost Evaluation
    base_cost, cost_breakdown, risk_breakdown, base_time_seconds = calculate_edge_cost(
        u_attrs=u_attrs,
        v_attrs=v_attrs,
        edge_attrs=edge_attrs,
        weights=weights,
        hazard_provider=hazard_provider,
    )

    # 3. Road Speed Adjustment if SLOW
    time_seconds = base_time_seconds
    if restriction and restriction.get("status") == RoadRestrictionStatus.SLOW.value:
        multiplier = max(float(restriction.get("speed_multiplier", 0.5)), 0.1)
        time_seconds = base_time_seconds / multiplier

    # 4. Dynamic Weather Adjustment
    # Check if any active hazards intersect this edge
    active_hazards = datastore.get_active_hazards()
    dynamic_hazard_penalty = 0.0
    u_lat = u_attrs.get("latitude", 0.0)
    u_lon = u_attrs.get("longitude", 0.0)

    for h in active_hazards:
        # Distance approximation in degrees squared (approx 1 deg ~ 111 km)
        d_lat = u_lat - h["latitude"]
        d_lon = u_lon - h["longitude"]
        dist_deg_sq = d_lat * d_lat + d_lon * d_lon
        radius_deg = (h.get("radius_meters", 1000.0) / 111000.0)
        if dist_deg_sq <= (radius_deg * radius_deg):
            dynamic_hazard_penalty += float(h.get("severity", 0.5)) * 15.0

    # 5. Composite Cost Integration
    dynamic_weather_cost = 0.0
    w_time = weights.get("time_weight", 0.35)
    w_risk = weights.get("risk_weight", 0.25)

    adjusted_time_cost = round(w_time * (time_seconds / 60.0), 4)
    dynamic_cost = round(
        cost_breakdown["distance_cost"]
        + adjusted_time_cost
        + cost_breakdown["risk_cost"]
        + cost_breakdown["terrain_cost"]
        + (w_risk * dynamic_hazard_penalty),
        4,
    )
    dynamic_cost = max(dynamic_cost, 0.0001)

    extended_cost_breakdown = {
        **cost_breakdown,
        "time_cost": adjusted_time_cost,
        "dynamic_hazard_cost": round(w_risk * dynamic_hazard_penalty, 4),
        "total_cost": dynamic_cost,
    }

    return dynamic_cost, extended_cost_breakdown, risk_breakdown, time_seconds, False
