"""
RouteIQ 2.0 - Road Network & Graph Spatial Endpoints (Phase 3)
Provides REST endpoints for querying topological graph statistics,
network health diagnostics, NER regional corridors, spatial nodes & edges,
and admin-protected OSM ingestion.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.dependencies import get_current_user, require_role
from app.graph.corridors import get_corridor, list_corridors
from app.graph.network_builder import RoadNetworkGraphManager, get_graph_manager
from app.graph.osm_ingestion import OSMIngestionPipeline
from app.graph.statistics import calculate_graph_statistics
from app.graph.validator import validate_road_network
from app.repositories.store import DataStore, get_store
from app.schemas.road_network import (
    BoundingBox,
    CorridorListResponse,
    CorridorResponse,
    IngestOSMRequest,
    IngestOSMResponse,
    NetworkHealthResponse,
    NetworkStatsResponse,
    RoadEdgeListResponse,
    RoadEdgeResponse,
    RoadNodeListResponse,
    RoadNodeResponse,
    RoadTypeStats,
)

router = APIRouter()


@router.get("/corridors", response_model=CorridorListResponse)
async def get_all_corridors(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CorridorListResponse:
    """Lists all designated North Eastern Region (NER) strategic road corridors."""
    corridors = list_corridors()
    return CorridorListResponse(
        total=len(corridors),
        corridors=[CorridorResponse.model_validate(c) for c in corridors],
    )


@router.get("/corridors/{corridor_id}", response_model=CorridorResponse)
async def get_corridor_by_id(
    corridor_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CorridorResponse:
    """Retrieves detailed routing and waypoint profile for a specific NER corridor."""
    corridor = get_corridor(corridor_id)
    if not corridor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Corridor '{corridor_id}' not found.",
        )
    return CorridorResponse.model_validate(corridor)


@router.get("/stats", response_model=NetworkStatsResponse)
async def get_network_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    graph_manager: RoadNetworkGraphManager = Depends(get_graph_manager),
) -> NetworkStatsResponse:
    """
    Returns comprehensive spatial and topological statistics for the road graph,
    including node/edge counts, road class distribution, component connectivity,
    and geographic bounding box.
    """
    G = graph_manager.get_graph()
    stats = calculate_graph_statistics(G)

    bbox = None
    if stats["bounding_box"]:
        bbox = BoundingBox(**stats["bounding_box"])

    return NetworkStatsResponse(
        total_nodes=stats["total_nodes"],
        total_edges=stats["total_edges"],
        total_length_km=stats["total_length_km"],
        weakly_connected_components=stats["weakly_connected_components"],
        strongly_connected_components=stats["strongly_connected_components"],
        largest_component_nodes=stats["largest_component_nodes"],
        largest_component_ratio=stats["largest_component_ratio"],
        road_type_distribution=[RoadTypeStats(**item) for item in stats["road_type_distribution"]],
        bounding_box=bbox,
    )


@router.get("/health", response_model=NetworkHealthResponse)
async def get_network_health(
    current_user: Dict[str, Any] = Depends(get_current_user),
    graph_manager: RoadNetworkGraphManager = Depends(get_graph_manager),
) -> NetworkHealthResponse:
    """
    Evaluates topological health, connectivity, dead-ends, and integrity
    diagnostics of the current road network graph.
    """
    G = graph_manager.get_graph()
    report = validate_road_network(G)
    metrics = report["metrics"]

    total_nodes = metrics["total_nodes"]
    total_edges = metrics["total_edges"]

    if total_nodes == 0:
        health_status = "empty"
    elif report["is_valid"] and metrics["weakly_connected_components"] <= 1:
        health_status = "healthy"
    else:
        health_status = "degraded"

    is_connected = (metrics["weakly_connected_components"] == 1) if total_nodes > 0 else False

    return NetworkHealthResponse(
        status=health_status,
        total_nodes=total_nodes,
        total_edges=total_edges,
        is_connected=is_connected,
        isolated_nodes=metrics["isolated_nodes"],
        dead_ends=metrics["dead_ends"],
        warnings=report["warnings"] + report["errors"],
    )


@router.get("/nodes", response_model=RoadNodeListResponse)
async def list_road_nodes(
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    store: DataStore = Depends(get_store),
) -> RoadNodeListResponse:
    """Returns paginated spatial road nodes, optionally filtered by bounding box."""
    nodes, total = store.list_road_nodes(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
        offset=offset,
    )
    return RoadNodeListResponse(
        total=total,
        limit=limit,
        offset=offset,
        nodes=[RoadNodeResponse.model_validate(n) for n in nodes],
    )


@router.get("/edges", response_model=RoadEdgeListResponse)
async def list_road_edges(
    road_type: Optional[str] = Query(None, description="Filter by classification: trunk, primary, etc."),
    min_lat: Optional[float] = Query(None, ge=-90.0, le=90.0),
    max_lat: Optional[float] = Query(None, ge=-90.0, le=90.0),
    min_lon: Optional[float] = Query(None, ge=-180.0, le=180.0),
    max_lon: Optional[float] = Query(None, ge=-180.0, le=180.0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    store: DataStore = Depends(get_store),
) -> RoadEdgeListResponse:
    """Returns paginated road edges, optionally filtered by classification and bounding box."""
    edges, total = store.list_road_edges(
        road_type=road_type,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        limit=limit,
        offset=offset,
    )
    return RoadEdgeListResponse(
        total=total,
        limit=limit,
        offset=offset,
        edges=[RoadEdgeResponse.model_validate(e) for e in edges],
    )


@router.post("/ingest", response_model=IngestOSMResponse, status_code=status.HTTP_201_CREATED)
async def ingest_osm_network(
    payload: IngestOSMRequest,
    current_user: Dict[str, Any] = Depends(require_role(["admin"])),
    store: DataStore = Depends(get_store),
    graph_manager: RoadNetworkGraphManager = Depends(get_graph_manager),
) -> IngestOSMResponse:
    """
    Admin-only endpoint to ingest OpenStreetMap (OSM) XML data into the road network.
    Accepts raw XML string payload or server-side XML fixture file path.
    """
    if not payload.xml_data and not payload.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'xml_data' or 'file_path' must be provided for ingestion.",
        )

    pipeline = OSMIngestionPipeline(store=store)

    try:
        if payload.xml_data:
            result = pipeline.ingest_xml_string(payload.xml_data)
        else:
            result = pipeline.ingest_file(payload.file_path)  # type: ignore

        # Invalidate in-memory graph cache to reflect newly ingested segments
        graph_manager.invalidate_cache()

        return IngestOSMResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OSM Ingestion failed: {str(e)}",
        )
