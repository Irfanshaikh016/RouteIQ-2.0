"""
RouteIQ 2.0 - Road Network & Graph Schemas (Phase 3)
Physical spatial graph schemas for nodes, edges, corridors, statistics, and OSM ingestion.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    min_lat: float = Field(..., description="Minimum latitude")
    max_lat: float = Field(..., description="Maximum latitude")
    min_lon: float = Field(..., description="Minimum longitude")
    max_lon: float = Field(..., description="Maximum longitude")


# ------------------------------------------------------------------------------
# Road Nodes
# ------------------------------------------------------------------------------
class RoadNodeBase(BaseModel):
    osm_id: Optional[int] = Field(None, description="OpenStreetMap node ID if ingested")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)")
    elevation_m: Optional[float] = Field(None, description="Elevation in meters (crucial for NER mountain corridors)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary OSM or terrain metadata tags")


class RoadNodeCreate(RoadNodeBase):
    pass


class RoadNodeResponse(RoadNodeBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadNodeListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    nodes: List[RoadNodeResponse]


# ------------------------------------------------------------------------------
# Road Edges
# ------------------------------------------------------------------------------
class RoadEdgeBase(BaseModel):
    osm_way_id: Optional[int] = Field(None, description="OpenStreetMap way ID if ingested")
    source_node_id: str = Field(..., description="UUID of source road node")
    target_node_id: str = Field(..., description="UUID of target road node")
    road_name: Optional[str] = Field(None, max_length=128, description="Road designation or name, e.g. NH 6")
    road_type: str = Field(..., max_length=64, description="Classification: trunk, primary, secondary, tertiary, etc.")
    length_meters: float = Field(..., ge=0.0, description="Geodesic length of segment in meters")
    max_speed_kph: Optional[float] = Field(None, ge=0.0, description="Speed limit in km/h")
    oneway: bool = Field(False, description="True if one-way traffic direction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="OSM tags and lane metadata")


class RoadEdgeCreate(RoadEdgeBase):
    pass


class RoadEdgeResponse(RoadEdgeBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadEdgeListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    edges: List[RoadEdgeResponse]


# ------------------------------------------------------------------------------
# Regional Corridors
# ------------------------------------------------------------------------------
class CorridorWaypoint(BaseModel):
    name: str
    latitude: float
    longitude: float
    state: str
    elevation_m: Optional[float] = None


class CorridorResponse(BaseModel):
    id: str
    name: str
    national_highway: str
    states_covered: List[str]
    start_point: str
    end_point: str
    intermediate_waypoints: List[CorridorWaypoint]
    approximate_length_km: float
    terrain_type: str
    strategic_notes: str


class CorridorListResponse(BaseModel):
    total: int
    corridors: List[CorridorResponse]


# ------------------------------------------------------------------------------
# Statistics and Health Diagnostics
# ------------------------------------------------------------------------------
class RoadTypeStats(BaseModel):
    road_type: str
    count: int
    total_length_km: float


class NetworkStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    total_length_km: float
    weakly_connected_components: int
    strongly_connected_components: int
    largest_component_nodes: int
    largest_component_ratio: float
    road_type_distribution: List[RoadTypeStats]
    bounding_box: Optional[BoundingBox] = None


class GraphValidationReport(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]


class NetworkHealthResponse(BaseModel):
    status: str = Field(..., description="healthy | degraded | empty")
    total_nodes: int
    total_edges: int
    is_connected: bool
    isolated_nodes: int
    dead_ends: int
    warnings: List[str]


# ------------------------------------------------------------------------------
# Ingestion Request / Response
# ------------------------------------------------------------------------------
class IngestOSMRequest(BaseModel):
    xml_data: Optional[str] = Field(None, description="Raw OSM XML content string")
    file_path: Optional[str] = Field(None, description="Server-side relative or absolute XML fixture path")
    corridor_id: Optional[str] = Field(None, description="Corridor identifier tag if filtering to specific corridor")


class IngestOSMResponse(BaseModel):
    success: bool
    nodes_ingested: int
    edges_ingested: int
    total_length_km: float
    time_taken_seconds: float
    message: str
