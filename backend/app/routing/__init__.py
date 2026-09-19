"""
RouteIQ 2.0 - Routing & Multi-Objective Optimization Package (Phase 4)
Provides multi-criteria pathfinding, cost and risk modeling, speed estimation,
routing profiles, and route comparison for the North Eastern Region.
"""
from app.routing.cost_model import calculate_edge_cost, get_estimated_speed_kph
from app.routing.exceptions import (
    GraphUnavailableError,
    InvalidCoordinateError,
    NearestNodeNotFoundError,
    NoRouteFoundError,
    RoutingError,
    UnsupportedProfileError,
)
from app.routing.geometry import build_geojson_linestring, extract_route_coordinates
from app.routing.optimizer import RouteOptimizer, get_route_optimizer
from app.routing.pathfinder import find_optimal_path
from app.routing.profiles import (
    ROUTING_PROFILES,
    get_profile,
    get_supported_profile_names,
    list_profiles,
)
from app.routing.risk_model import (
    HazardProvider,
    StaticHazardProvider,
    get_default_hazard_provider,
)
from app.routing.route_service import RouteService, get_route_service
from app.routing.schemas import (
    Coordinate,
    GeoJSONGeometry,
    RouteComparisonResponse,
    RouteCostBreakdown,
    RouteEdgeResponse,
    RouteMetrics,
    RouteNodeResponse,
    RouteProfileInfo,
    RouteRequest,
    RouteResponse,
    RouteRiskBreakdown,
    RoutingHealthResponse,
    RoutingProfilesResponse,
)

__all__ = [
    "RoutingError",
    "InvalidCoordinateError",
    "UnsupportedProfileError",
    "GraphUnavailableError",
    "NearestNodeNotFoundError",
    "NoRouteFoundError",
    "Coordinate",
    "RouteRequest",
    "RouteCostBreakdown",
    "RouteRiskBreakdown",
    "RouteNodeResponse",
    "RouteEdgeResponse",
    "RouteMetrics",
    "GeoJSONGeometry",
    "RouteProfileInfo",
    "RouteResponse",
    "RoutingProfilesResponse",
    "RoutingHealthResponse",
    "RouteComparisonResponse",
    "ROUTING_PROFILES",
    "get_profile",
    "list_profiles",
    "get_supported_profile_names",
    "HazardProvider",
    "StaticHazardProvider",
    "get_default_hazard_provider",
    "calculate_edge_cost",
    "get_estimated_speed_kph",
    "build_geojson_linestring",
    "extract_route_coordinates",
    "find_optimal_path",
    "RouteService",
    "get_route_service",
    "RouteOptimizer",
    "get_route_optimizer",
]
