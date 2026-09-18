"""
RouteIQ 2.0 - Road Network Graph Statistics Service (Phase 3)
Calculates spatial and topological metrics across the regional road graph.
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional
import networkx as nx


def calculate_graph_statistics(G: nx.DiGraph) -> Dict[str, Any]:
    """
    Computes summary metrics for a NetworkX DiGraph road network.
    """
    total_nodes = G.number_of_nodes()
    total_edges = G.number_of_edges()

    if total_nodes == 0:
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "total_length_km": 0.0,
            "weakly_connected_components": 0,
            "strongly_connected_components": 0,
            "largest_component_nodes": 0,
            "largest_component_ratio": 0.0,
            "road_type_distribution": [],
            "bounding_box": None,
        }

    # Bounding box calculation
    lats = [attrs["latitude"] for _, attrs in G.nodes(data=True) if "latitude" in attrs]
    lons = [attrs["longitude"] for _, attrs in G.nodes(data=True) if "longitude" in attrs]

    bounding_box = None
    if lats and lons:
        bounding_box = {
            "min_lat": round(min(lats), 6),
            "max_lat": round(max(lats), 6),
            "min_lon": round(min(lons), 6),
            "max_lon": round(max(lons), 6),
        }

    # Road type distribution & length calculation
    type_counts: Dict[str, int] = defaultdict(int)
    type_lengths_m: Dict[str, float] = defaultdict(float)
    total_length_m = 0.0

    for _, _, attrs in G.edges(data=True):
        rtype = attrs.get("road_type", "unclassified")
        length = float(attrs.get("length_meters", 0.0))
        type_counts[rtype] += 1
        type_lengths_m[rtype] += length
        total_length_m += length

    road_type_distribution = [
        {
            "road_type": rtype,
            "count": count,
            "total_length_km": round(type_lengths_m[rtype] / 1000.0, 2),
        }
        for rtype, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    # Connectivity metrics
    weak_components = list(nx.weakly_connected_components(G))
    strong_components = list(nx.strongly_connected_components(G))

    num_weak = len(weak_components)
    num_strong = len(strong_components)

    largest_weak_size = max(len(c) for c in weak_components) if weak_components else 0
    largest_ratio = (largest_weak_size / total_nodes) if total_nodes > 0 else 0.0

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "total_length_km": round(total_length_m / 1000.0, 2),
        "weakly_connected_components": num_weak,
        "strongly_connected_components": num_strong,
        "largest_component_nodes": largest_weak_size,
        "largest_component_ratio": round(largest_ratio, 4),
        "road_type_distribution": road_type_distribution,
        "bounding_box": bounding_box,
    }
