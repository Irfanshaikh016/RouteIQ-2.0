"""
RouteIQ 2.0 - Travel Cost & Duration Matrix Generator (Phase 6)
Builds symmetric/asymmetric distance, duration, and multi-criteria cost matrices
between depot and customer delivery locations using the Phase 4 road graph.
"""
from typing import Any, Dict, List, Optional, Tuple
import math
from app.graph.network_builder import get_graph_manager
from app.graph.osm_ingestion import haversine_distance
from app.routing.pathfinder import find_optimal_path
from app.routing.route_service import get_route_service
from app.routing.schemas import Coordinate
from app.weather.risk import calculate_dynamic_edge_cost
from app.routing.profiles import get_profile
from app.repositories.store import get_store

# LRU / In-memory matrix cache
_matrix_cache: Dict[Tuple[float, float, float, float, str], Dict[str, float]] = {}


def get_point_to_point_metrics(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    profile_name: str = "balanced",
) -> Dict[str, float]:
    """
    Computes distance, duration, and profile-weighted cost between two coordinates.
    Uses Phase 4 graph pathfinder where available; falls back to Haversine with
    regional winding factor (1.35x) and terrain speed adjustment.
    """
    key = (round(lat1, 5), round(lon1, 5), round(lat2, 5), round(lon2, 5), profile_name)
    if key in _matrix_cache:
        return _matrix_cache[key]

    # If identical coordinates
    if abs(lat1 - lat2) < 0.0001 and abs(lon1 - lon2) < 0.0001:
        res = {"distance_km": 0.0, "duration_minutes": 0.0, "cost": 0.0, "risk": 0.0}
        _matrix_cache[key] = res
        return res

    route_service = get_route_service()
    store = get_store()
    G = route_service.graph_manager.get_graph()

    # Try graph-aware route calculation
    if G is not None and G.number_of_nodes() > 0:
        try:
            route_res = route_service.calculate_route(
                origin=Coordinate(latitude=lat1, longitude=lon1),
                destination=Coordinate(latitude=lat2, longitude=lon2),
                profile_name=profile_name,
            )
            res = {
                "distance_km": route_res.metrics.distance_km,
                "duration_minutes": route_res.metrics.estimated_time_minutes,
                "cost": route_res.metrics.objective_score,
                "risk": route_res.metrics.risk_score,
            }
            _matrix_cache[key] = res
            return res
        except Exception:
            # Fallback to high-accuracy Haversine with NER terrain winding penalty
            pass

    # Haversine fallback with realistic NER mountain terrain winding multiplier
    dist_m = haversine_distance(lat1, lon1, lat2, lon2)
    road_dist_m = dist_m * 1.35  # Mountain road detour index
    dist_km = road_dist_m / 1000.0

    # Average regional commercial speed: ~40 km/h
    avg_speed_kph = 40.0
    if profile_name == "fastest":
        avg_speed_kph = 45.0
    elif profile_name == "safest":
        avg_speed_kph = 35.0

    duration_minutes = (dist_km / avg_speed_kph) * 60.0
    cost = dist_km * 0.4 + duration_minutes * 0.6
    risk = 0.15

    res = {
        "distance_km": round(dist_km, 2),
        "duration_minutes": round(duration_minutes, 1),
        "cost": round(cost, 2),
        "risk": round(risk, 2),
    }
    _matrix_cache[key] = res
    return res


def build_travel_matrices(
    depot_lat: float,
    depot_lon: float,
    locations: List[Tuple[float, float]],
    profile_name: str = "balanced",
) -> Dict[str, Any]:
    """
    Builds (N+1) x (N+1) matrix for OR-Tools:
    Index 0 is depot, indices 1..N are customer delivery locations.
    Returns:
        {
            "cost_matrix": List[List[int]],        # Scaled integer matrix for OR-Tools
            "duration_matrix": List[List[int]],    # Integer minutes matrix
            "distance_matrix": List[List[float]],  # Kilometers matrix
            "risk_matrix": List[List[float]],
            "raw_cost_matrix": List[List[float]],
        }
    """
    all_points = [(depot_lat, depot_lon)] + locations
    n = len(all_points)

    cost_matrix = [[0 for _ in range(n)] for _ in range(n)]
    duration_matrix = [[0 for _ in range(n)] for _ in range(n)]
    distance_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    risk_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    raw_cost_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            metrics = get_point_to_point_metrics(
                all_points[i][0],
                all_points[i][1],
                all_points[j][0],
                all_points[j][1],
                profile_name=profile_name,
            )
            # OR-Tools requires integer costs; scale by 100 for precision
            cost_matrix[i][j] = int(round(metrics["cost"] * 100))
            duration_matrix[i][j] = int(math.ceil(metrics["duration_minutes"]))
            distance_matrix[i][j] = metrics["distance_km"]
            risk_matrix[i][j] = metrics["risk"]
            raw_cost_matrix[i][j] = metrics["cost"]

    return {
        "cost_matrix": cost_matrix,
        "duration_matrix": duration_matrix,
        "distance_matrix": distance_matrix,
        "risk_matrix": risk_matrix,
        "raw_cost_matrix": raw_cost_matrix,
    }
