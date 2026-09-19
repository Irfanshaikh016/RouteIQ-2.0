"""
RouteIQ 2.0 - Core Route Service & Node Resolver (Phase 4)
Orchestrates coordinate validation, nearest road-node spatial lookup,
pathfinding execution, route reconstruction, metrics aggregation, and GeoJSON formatting.
"""
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple
from app.graph.network_builder import RoadNetworkGraphManager, get_graph_manager
from app.graph.osm_ingestion import haversine_distance
from app.repositories.store import DataStore, get_store
from app.routing.cost_model import calculate_edge_cost
from app.routing.exceptions import (
    GraphUnavailableError,
    NearestNodeNotFoundError,
    NoRouteFoundError,
)
from app.routing.geometry import build_geojson_linestring, extract_route_coordinates
from app.routing.pathfinder import find_optimal_path
from app.routing.profiles import get_profile, get_supported_profile_names
from app.routing.risk_model import HazardProvider, get_default_hazard_provider
from app.routing.schemas import (
    Coordinate,
    GeoJSONGeometry,
    RouteCostBreakdown,
    RouteEdgeResponse,
    RouteMetrics,
    RouteNodeResponse,
    RouteRequest,
    RouteResponse,
    RouteRiskBreakdown,
)
from app.routing.validators import validate_coordinates, validate_profile_name


class RouteService:
    """
    High-level routing coordinator that maps input coordinates to graph nodes,
    solves multi-objective paths, and constructs complete route responses.
    """

    def __init__(
        self,
        store: Optional[DataStore] = None,
        graph_manager: Optional[RoadNetworkGraphManager] = None,
        hazard_provider: Optional[HazardProvider] = None,
    ):
        self.store = store or get_store()
        self.graph_manager = graph_manager or get_graph_manager()
        self.hazard_provider = hazard_provider or get_default_hazard_provider()

    def find_nearest_node(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 50.0,
    ) -> Tuple[Dict[str, Any], float]:
        """
        Locates nearest road network node to given coordinates within max_distance_km.
        Uses spatial bounding box filtering for performance, falling back to all nodes.
        Returns: (node_dict, distance_in_meters).
        """
        # Estimate bounding box in degrees
        delta_lat = max_distance_km / 111.0
        cos_lat = max(math.cos(math.radians(latitude)), 0.1)
        delta_lon = max_distance_km / (111.0 * cos_lat)

        min_lat = latitude - delta_lat
        max_lat = latitude + delta_lat
        min_lon = longitude - delta_lon
        max_lon = longitude + delta_lon

        candidate_nodes, _ = self.store.list_road_nodes(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            limit=1000,
        )

        if not candidate_nodes:
            # Fall back to all nodes if bounding box had zero nodes
            candidate_nodes = self.store.get_all_road_nodes()

        if not candidate_nodes:
            raise GraphUnavailableError(
                "No road network nodes exist in storage. Ingest an OSM road network first."
            )

        best_node = None
        best_dist = float("inf")

        for n in candidate_nodes:
            d = haversine_distance(latitude, longitude, float(n["latitude"]), float(n["longitude"]))
            if d < best_dist:
                best_dist = d
                best_node = n

        max_meters = max_distance_km * 1000.0
        if best_node is None or best_dist > max_meters:
            raise NearestNodeNotFoundError(
                f"No road node found within {max_distance_km} km of coordinate ({latitude}, {longitude}). "
                f"Closest node was {round(best_dist / 1000.0, 1)} km away."
            )

        return best_node, best_dist

    def calculate_route(self, request: RouteRequest) -> RouteResponse:
        """
        Executes end-to-end multi-objective route optimization.
        """
        # 1. Validate coordinates and profile
        validate_coordinates(request.origin.latitude, request.origin.longitude)
        validate_coordinates(request.destination.latitude, request.destination.longitude)
        profile_name = validate_profile_name(request.profile, get_supported_profile_names())

        # 2. Get road graph
        G = self.graph_manager.get_graph()
        if G.number_of_nodes() == 0:
            raise GraphUnavailableError("Road network graph is empty. Please ingest road data first.")

        # 3. Resolve nearest origin and destination nodes
        src_node, _ = self.find_nearest_node(
            request.origin.latitude,
            request.origin.longitude,
            max_distance_km=request.max_nearest_distance_km,
        )
        dst_node, _ = self.find_nearest_node(
            request.destination.latitude,
            request.destination.longitude,
            max_distance_km=request.max_nearest_distance_km,
        )

        # 4. Pathfinding
        path_node_ids = find_optimal_path(
            G=G,
            source_node_id=src_node["id"],
            target_node_id=dst_node["id"],
            profile_name=profile_name,
            hazard_provider=self.hazard_provider,
        )

        # 5. Reconstruct sequence of nodes
        route_nodes: List[RouteNodeResponse] = []
        node_dicts: List[Dict[str, Any]] = []

        for seq, nid in enumerate(path_node_ids, start=1):
            n_data = G.nodes.get(nid, {})
            node_dict = {
                "id": nid,
                "osm_id": n_data.get("osm_id"),
                "latitude": float(n_data.get("latitude", 0.0)),
                "longitude": float(n_data.get("longitude", 0.0)),
                "elevation_m": n_data.get("elevation_m"),
            }
            node_dicts.append(node_dict)
            route_nodes.append(
                RouteNodeResponse(
                    sequence=seq,
                    node_id=nid,
                    osm_id=n_data.get("osm_id"),
                    latitude=float(n_data.get("latitude", 0.0)),
                    longitude=float(n_data.get("longitude", 0.0)),
                    elevation_m=n_data.get("elevation_m"),
                )
            )

        # 6. Reconstruct sequence of edges & compute edge costs
        profile = get_profile(profile_name)
        weights = profile["weights"]
        route_edges: List[RouteEdgeResponse] = []

        total_length_m = 0.0
        total_time_s = 0.0
        total_objective_score = 0.0
        risk_scores: List[float] = []
        terrain_scores: List[float] = []

        for i in range(len(path_node_ids) - 1):
            u = path_node_ids[i]
            v = path_node_ids[i + 1]
            edge_attrs = G.get_edge_data(u, v, default={})
            u_attrs = G.nodes.get(u, {})
            v_attrs = G.nodes.get(v, {})

            total_cost, cost_dict, risk_dict, time_s = calculate_edge_cost(
                u_attrs=u_attrs,
                v_attrs=v_attrs,
                edge_attrs=edge_attrs,
                weights=weights,
                hazard_provider=self.hazard_provider,
            )

            length_m = float(edge_attrs.get("length_meters", 0.0))
            total_length_m += length_m
            total_time_s += time_s
            total_objective_score += total_cost
            risk_scores.append(risk_dict["overall_risk"])
            terrain_scores.append(risk_dict["terrain_risk"])

            edge_resp = RouteEdgeResponse(
                sequence=i + 1,
                edge_id=edge_attrs.get("edge_id", str(uuid.uuid4())),
                osm_way_id=edge_attrs.get("osm_way_id"),
                source_node_id=u,
                target_node_id=v,
                road_name=edge_attrs.get("road_name"),
                road_type=edge_attrs.get("road_type", "unclassified"),
                length_meters=round(length_m, 2),
                estimated_time_seconds=round(time_s, 2),
                cost_breakdown=RouteCostBreakdown(**cost_dict),
                risk_breakdown=RouteRiskBreakdown(**risk_dict),
            )
            route_edges.append(edge_resp)

        # 7. Aggregate summary metrics
        avg_risk = round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else 0.0
        avg_terrain = round(sum(terrain_scores) / len(terrain_scores), 4) if terrain_scores else 0.0

        metrics = RouteMetrics(
            distance_km=round(total_length_m / 1000.0, 2),
            estimated_time_minutes=round(total_time_s / 60.0, 2),
            objective_score=round(total_objective_score, 4),
            risk_score=avg_risk,
            terrain_score=avg_terrain,
        )

        # 8. Generate GeoJSON LineString
        coordinates = extract_route_coordinates(node_dicts)
        geometry = GeoJSONGeometry(
            type="LineString",
            coordinates=coordinates,
        )

        return RouteResponse(
            route_id=str(uuid.uuid4()),
            profile=profile_name,
            origin=request.origin,
            destination=request.destination,
            metrics=metrics,
            nodes=route_nodes,
            edges=route_edges,
            geometry=geometry,
            optimization_metadata={
                "profile": profile_name,
                "weights": weights,
                "segments_count": len(route_edges),
                "nodes_count": len(route_nodes),
                "source_snapped_node_id": src_node["id"],
                "target_snapped_node_id": dst_node["id"],
            },
        )


# Global singleton instance
_route_service = RouteService()


def get_route_service() -> RouteService:
    """Returns global RouteService instance."""
    return _route_service
