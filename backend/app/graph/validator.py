"""
RouteIQ 2.0 - Road Network Graph Integrity Validator (Phase 3)
Audits topological consistency, referential integrity, coordinate validity,
and connectivity characteristics of the spatial graph.
"""
from typing import Any, Dict, List, Optional
import networkx as nx


def validate_road_network(G: nx.DiGraph) -> Dict[str, Any]:
    """
    Performs comprehensive validation of a NetworkX DiGraph road network.
    Returns:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "metrics": Dict[str, Any]
        }
    """
    errors: List[str] = []
    warnings: List[str] = []

    total_nodes = G.number_of_nodes()
    total_edges = G.number_of_edges()

    if total_nodes == 0:
        return {
            "is_valid": True,
            "errors": [],
            "warnings": ["Road network is currently empty (0 nodes, 0 edges)."],
            "metrics": {
                "total_nodes": 0,
                "total_edges": 0,
                "weakly_connected_components": 0,
                "strongly_connected_components": 0,
                "isolated_nodes": 0,
                "dead_ends": 0,
            },
        }

    # 1. Node coordinate sanity
    for node_id, attrs in G.nodes(data=True):
        lat = attrs.get("latitude")
        lon = attrs.get("longitude")
        if lat is None or lon is None:
            errors.append(f"Node {node_id} is missing coordinates.")
        else:
            if not (-90.0 <= lat <= 90.0):
                errors.append(f"Node {node_id} latitude {lat} out of range [-90, 90].")
            if not (-180.0 <= lon <= 180.0):
                errors.append(f"Node {node_id} longitude {lon} out of range [-180, 180].")

    # 2. Edge length and self-loop checks
    self_loop_count = 0
    negative_length_count = 0
    for u, v, attrs in G.edges(data=True):
        if u == v:
            self_loop_count += 1
        length = attrs.get("length_meters", 0.0)
        if length < 0:
            negative_length_count += 1

    if self_loop_count > 0:
        warnings.append(f"Detected {self_loop_count} self-loop edges in network.")
    if negative_length_count > 0:
        errors.append(f"Detected {negative_length_count} edges with negative length.")

    # 3. Connectivity analysis
    isolated_nodes = [n for n, d in G.degree() if d == 0]
    dead_ends = [n for n in G.nodes() if G.in_degree(n) == 0 or G.out_degree(n) == 0]

    if isolated_nodes:
        warnings.append(f"Found {len(isolated_nodes)} isolated node(s) with degree 0.")

    weak_components = list(nx.weakly_connected_components(G))
    num_weak_components = len(weak_components)

    strong_components = list(nx.strongly_connected_components(G))
    num_strong_components = len(strong_components)

    largest_weak_size = max(len(c) for c in weak_components) if weak_components else 0
    largest_ratio = (largest_weak_size / total_nodes) if total_nodes > 0 else 0.0

    if num_weak_components > 1:
        warnings.append(
            f"Graph consists of {num_weak_components} disconnected components. "
            f"Largest component contains {largest_weak_size}/{total_nodes} nodes ({largest_ratio:.1%})."
        )

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "weakly_connected_components": num_weak_components,
            "strongly_connected_components": num_strong_components,
            "largest_component_nodes": largest_weak_size,
            "largest_component_ratio": round(largest_ratio, 4),
            "isolated_nodes": len(isolated_nodes),
            "dead_ends": len(dead_ends),
        },
    }
