"""
RouteIQ 2.0 - Multi-Objective Pathfinding Engine (Phase 4)
Performs weighted shortest-path discovery using NetworkX on directed spatial graphs.
Thread-safe: dynamically computes profile-weighted edge costs without mutating graph state.
"""
from typing import Any, Callable, Dict, List, Optional
import networkx as nx
from app.routing.cost_model import calculate_edge_cost
from app.routing.exceptions import GraphUnavailableError, NoRouteFoundError
from app.routing.profiles import get_profile
from app.routing.risk_model import HazardProvider, get_default_hazard_provider


def make_edge_weight_evaluator(
    G: nx.DiGraph,
    weights: Dict[str, float],
    hazard_provider: Optional[HazardProvider] = None,
) -> Callable[[Any, Any, Dict[str, Any]], float]:
    """
    Creates a dynamic weight function (u, v, edge_attrs) -> float
    for use in NetworkX shortest_path / dijkstra_path algorithms.
    Guarantees thread-safety without in-place mutation of the shared DiGraph.
    """
    provider = hazard_provider or get_default_hazard_provider()

    def weight_func(u: Any, v: Any, edge_attrs: Dict[str, Any]) -> float:
        u_attrs = G.nodes.get(u, {})
        v_attrs = G.nodes.get(v, {})
        cost, _, _, _ = calculate_edge_cost(
            u_attrs=u_attrs,
            v_attrs=v_attrs,
            edge_attrs=edge_attrs,
            weights=weights,
            hazard_provider=provider,
        )
        return cost

    return weight_func


def find_optimal_path(
    G: nx.DiGraph,
    source_node_id: str,
    target_node_id: str,
    profile_name: str = "balanced",
    hazard_provider: Optional[HazardProvider] = None,
) -> List[str]:
    """
    Finds optimal sequence of node IDs from source to target respecting edge directionality
    and profile-specific multi-objective cost optimization.
    Raises:
        GraphUnavailableError: if graph has 0 nodes
        NoRouteFoundError: if source or target node is missing or no path exists
    """
    if G.number_of_nodes() == 0:
        raise GraphUnavailableError("The road network graph is empty. Please ingest OSM road data first.")

    if not G.has_node(source_node_id):
        raise NoRouteFoundError(f"Origin node '{source_node_id}' does not exist in the road graph.")

    if not G.has_node(target_node_id):
        raise NoRouteFoundError(f"Destination node '{target_node_id}' does not exist in the road graph.")

    if source_node_id == target_node_id:
        return [source_node_id]

    profile = get_profile(profile_name)
    weights = profile["weights"]
    evaluator = make_edge_weight_evaluator(G, weights, hazard_provider)

    try:
        path = nx.dijkstra_path(G, source=source_node_id, target=target_node_id, weight=evaluator)
        return path
    except nx.NetworkXNoPath:
        raise NoRouteFoundError(
            f"No traversable road path exists between origin node '{source_node_id}' "
            f"and destination node '{target_node_id}' under profile '{profile_name}'."
        )
    except nx.NodeNotFound as e:
        raise NoRouteFoundError(f"Graph node lookup failed: {str(e)}")
