"""
RouteIQ 2.0 - Multi-Objective Routing Schemas (Phase 4)
Defines strongly typed Pydantic models for routing requests, responses,
multi-criteria metrics, risk/cost breakdowns, and GeoJSON geometries.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)")


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    profile: str = Field(default="balanced", description="Optimization profile: 'fastest', 'safest', or 'balanced'")
    max_nearest_distance_km: float = Field(
        default=50.0,
        ge=0.1,
        le=500.0,
        description="Maximum search radius to snap coordinates to road network node (km)",
    )


class RouteCostBreakdown(BaseModel):
    distance_cost: float = Field(..., description="Normalized distance penalty")
    time_cost: float = Field(..., description="Normalized estimated travel time penalty")
    risk_cost: float = Field(..., description="Normalized composite hazard risk penalty")
    terrain_cost: float = Field(..., description="Normalized terrain elevation/slope penalty")
    total_cost: float = Field(..., description="Weighted composite routing cost")


class RouteRiskBreakdown(BaseModel):
    flood_risk: float = Field(..., ge=0.0, le=1.0, description="Modeled flood vulnerability index [0, 1]")
    landslide_risk: float = Field(..., ge=0.0, le=1.0, description="Modeled landslide susceptibility index [0, 1]")
    monsoon_risk: float = Field(..., ge=0.0, le=1.0, description="Modeled monsoon season exposure index [0, 1]")
    terrain_risk: float = Field(..., ge=0.0, le=1.0, description="Modeled terrain elevation/grade index [0, 1]")
    surface_risk: float = Field(..., ge=0.0, le=1.0, description="Modeled road surface degradation index [0, 1]")
    overall_risk: float = Field(..., ge=0.0, le=1.0, description="Composite weighted risk score [0, 1]")


class RouteNodeResponse(BaseModel):
    sequence: int = Field(..., description="1-based index in the path sequence")
    node_id: str = Field(..., description="Database UUID of the road node")
    osm_id: Optional[int] = Field(None, description="OpenStreetMap node ID if ingested")
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class RouteEdgeResponse(BaseModel):
    sequence: int = Field(..., description="1-based index of the edge in the route")
    edge_id: str = Field(..., description="Database UUID of the road edge")
    osm_way_id: Optional[int] = None
    source_node_id: str
    target_node_id: str
    road_name: Optional[str] = None
    road_type: str
    length_meters: float
    estimated_time_seconds: float
    cost_breakdown: RouteCostBreakdown
    risk_breakdown: RouteRiskBreakdown

    model_config = ConfigDict(from_attributes=True)


class RouteMetrics(BaseModel):
    distance_km: float = Field(..., description="Cumulative route length in kilometers")
    estimated_time_minutes: float = Field(..., description="Estimated travel time in minutes")
    objective_score: float = Field(..., description="Total multi-objective optimization score")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Average route risk score [0, 1]")
    terrain_score: float = Field(..., ge=0.0, le=1.0, description="Average terrain difficulty score [0, 1]")


class GeoJSONGeometry(BaseModel):
    type: str = Field(default="LineString", description="GeoJSON geometry type")
    coordinates: List[List[float]] = Field(
        ...,
        description="Array of [longitude, latitude] coordinates in traversal order",
    )


class RouteProfileInfo(BaseModel):
    name: str = Field(..., description="Profile identifier: fastest | safest | balanced")
    description: str
    weights: Dict[str, float] = Field(..., description="Normalized objective criteria weights")
    trade_offs: str


class RouteResponse(BaseModel):
    route_id: str
    profile: str
    origin: Coordinate
    destination: Coordinate
    metrics: RouteMetrics
    nodes: List[RouteNodeResponse]
    edges: List[RouteEdgeResponse]
    geometry: GeoJSONGeometry
    optimization_metadata: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class RoutingProfilesResponse(BaseModel):
    total: int
    profiles: List[RouteProfileInfo]


class RoutingHealthResponse(BaseModel):
    status: str = Field(..., description="healthy | degraded | empty")
    engine_version: str
    graph_available: bool
    total_nodes: int
    total_edges: int
    profiles_loaded: List[str]


class RouteComparisonResponse(BaseModel):
    origin: Coordinate
    destination: Coordinate
    routes: List[RouteResponse]
