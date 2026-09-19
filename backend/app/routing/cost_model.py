"""
RouteIQ 2.0 - Edge Cost Model & Speed Estimation (Phase 4)
Calculates multi-criteria routing costs combining normalized distance,
estimated travel time, terrain difficulty, and hazard risk based on profile weights.
"""
from typing import Any, Dict, Optional, Tuple
from app.routing.risk_model import HazardProvider, get_default_hazard_provider

# Fallback commercial logistics speeds (km/h) across the North Eastern Region
FALLBACK_ESTIMATED_SPEEDS_KPH: Dict[str, float] = {
    "motorway": 90.0,
    "trunk": 60.0,       # Standard four-lane / two-lane national highways (NH-06, NH-27)
    "primary": 50.0,     # State highways and major arterial connections
    "secondary": 40.0,   # Inter-district and valley corridors
    "tertiary": 30.0,    # Rural town connectors
    "unclassified": 25.0,# Paved / semi-paved rural links
    "residential": 20.0, # Urban access streets
    "service": 15.0,     # Depot / facility access alleys
    "motorway_link": 50.0,
    "trunk_link": 45.0,
    "primary_link": 35.0,
    "secondary_link": 25.0,
    "tertiary_link": 20.0,
    "default": 30.0,
}


def get_estimated_speed_kph(road_type: str, max_speed_kph: Optional[float] = None) -> float:
    """
    Returns estimated travel speed in km/h.
    Uses OSM tagged speed limit if available and valid; otherwise applies
    documented static regional fallback speeds by highway classification.
    """
    if max_speed_kph is not None and 5.0 <= max_speed_kph <= 130.0:
        return float(max_speed_kph)
    return FALLBACK_ESTIMATED_SPEEDS_KPH.get(
        road_type.lower(), FALLBACK_ESTIMATED_SPEEDS_KPH["default"]
    )


def calculate_edge_cost(
    u_attrs: Dict[str, Any],
    v_attrs: Dict[str, Any],
    edge_attrs: Dict[str, Any],
    weights: Dict[str, float],
    hazard_provider: Optional[HazardProvider] = None,
) -> Tuple[float, Dict[str, float], Dict[str, float], float]:
    """
    Calculates composite multi-objective edge routing cost.
    Returns:
        (total_cost, cost_breakdown, risk_breakdown, estimated_time_seconds)
    """
    hazard_provider = hazard_provider or get_default_hazard_provider()
    length_m = max(float(edge_attrs.get("length_meters", 10.0)), 1.0)
    road_type = edge_attrs.get("road_type", "unclassified")
    max_speed = edge_attrs.get("max_speed_kph")

    # 1. Travel time calculation
    speed_kph = get_estimated_speed_kph(road_type, max_speed)
    speed_mps = max(speed_kph * (1000.0 / 3600.0), 1.0)
    time_seconds = length_m / speed_mps
    time_minutes = time_seconds / 60.0

    # 2. Risk breakdown evaluation
    risk_breakdown = hazard_provider.calculate_risk(u_attrs, v_attrs, edge_attrs)
    overall_risk = risk_breakdown["overall_risk"]
    terrain_risk = risk_breakdown["terrain_risk"]

    # 3. Normalized dimensionless cost components
    # Distance in kilometers
    norm_dist = length_m / 1000.0
    # Time in minutes
    norm_time = time_minutes
    # Risk penalty scaled proportional to traversal time
    norm_risk = overall_risk * time_minutes * 2.5
    # Terrain penalty scaled proportional to slope and elevation exposure
    norm_terrain = terrain_risk * time_minutes * 2.0

    w_dist = weights.get("distance_weight", 0.25)
    w_time = weights.get("time_weight", 0.35)
    w_risk = weights.get("risk_weight", 0.25)
    w_terrain = weights.get("terrain_weight", 0.15)

    dist_cost = round(w_dist * norm_dist, 4)
    time_cost = round(w_time * norm_time, 4)
    risk_cost = round(w_risk * norm_risk, 4)
    terrain_cost = round(w_terrain * norm_terrain, 4)

    total_cost = round(dist_cost + time_cost + risk_cost + terrain_cost, 4)
    # Ensure positive cost for Dijkstra / A*
    total_cost = max(total_cost, 0.0001)

    cost_breakdown = {
        "distance_cost": dist_cost,
        "time_cost": time_cost,
        "risk_cost": risk_cost,
        "terrain_cost": terrain_cost,
        "total_cost": total_cost,
    }

    return total_cost, cost_breakdown, risk_breakdown, time_seconds
