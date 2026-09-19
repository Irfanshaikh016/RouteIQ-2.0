"""
RouteIQ 2.0 - Routing & Optimization REST Endpoints (Phase 4)
Provides endpoints for single-profile multi-objective route calculation,
route comparison, routing profile specifications, and engine health diagnostics.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.graph.network_builder import RoadNetworkGraphManager, get_graph_manager
from app.routing.exceptions import (
    GraphUnavailableError,
    InvalidCoordinateError,
    NearestNodeNotFoundError,
    NoRouteFoundError,
    UnsupportedProfileError,
)
from app.routing.optimizer import RouteOptimizer, get_route_optimizer
from app.routing.profiles import list_profiles
from app.routing.route_service import RouteService, get_route_service
from app.routing.schemas import (
    RouteComparisonResponse,
    RouteProfileInfo,
    RouteRequest,
    RouteResponse,
    RoutingHealthResponse,
    RoutingProfilesResponse,
)

router = APIRouter()


@router.post("/route", response_model=RouteResponse, status_code=status.HTTP_200_OK)
async def calculate_route(
    payload: RouteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    route_service: RouteService = Depends(get_route_service),
) -> RouteResponse:
    """
    Computes a multi-objective optimized route between origin and destination coordinates
    under the requested optimization profile (fastest, safest, or balanced).
    """
    try:
        route = route_service.calculate_route(payload)
        return route
    except InvalidCoordinateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UnsupportedProfileError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NearestNodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NoRouteFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except GraphUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route calculation failed: {str(e)}",
        )


@router.get("/profiles", response_model=RoutingProfilesResponse)
async def get_routing_profiles(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> RoutingProfilesResponse:
    """
    Retrieves available multi-objective routing profiles, objective weights,
    and trade-off characteristics.
    """
    profiles = list_profiles()
    return RoutingProfilesResponse(
        total=len(profiles),
        profiles=[RouteProfileInfo(**p) for p in profiles],
    )


@router.get("/health", response_model=RoutingHealthResponse)
async def get_routing_health(
    current_user: Dict[str, Any] = Depends(get_current_user),
    graph_manager: RoadNetworkGraphManager = Depends(get_graph_manager),
) -> RoutingHealthResponse:
    """
    Returns the readiness state and graph statistics of the routing optimization engine.
    """
    G = graph_manager.get_graph()
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    if num_nodes == 0:
        health_status = "empty"
    elif num_edges > 0:
        health_status = "healthy"
    else:
        health_status = "degraded"

    profiles = list_profiles()
    profile_names = [p["name"] for p in profiles]

    return RoutingHealthResponse(
        status=health_status,
        engine_version=settings.VERSION,
        graph_available=num_nodes > 0,
        total_nodes=num_nodes,
        total_edges=num_edges,
        profiles_loaded=profile_names,
    )


@router.post("/compare", response_model=RouteComparisonResponse)
async def compare_routes(
    payload: RouteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    optimizer: RouteOptimizer = Depends(get_route_optimizer),
) -> RouteComparisonResponse:
    """
    Calculates alternative routes across fastest, safest, and balanced profiles
    for identical origin and destination endpoints without ranking or recommendation bias.
    """
    try:
        routes = optimizer.compare_routes(
            origin=payload.origin,
            destination=payload.destination,
            profiles=["fastest", "safest", "balanced"],
            max_nearest_distance_km=payload.max_nearest_distance_km,
        )
        if not routes:
            raise NoRouteFoundError("No valid route could be constructed across any profile.")
        return RouteComparisonResponse(
            origin=payload.origin,
            destination=payload.destination,
            routes=routes,
        )
    except InvalidCoordinateError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NearestNodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NoRouteFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except GraphUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route comparison failed: {str(e)}",
        )
