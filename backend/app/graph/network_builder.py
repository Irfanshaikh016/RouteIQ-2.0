"""
RouteIQ 2.0 - NetworkX Road Network Graph Builder (Phase 3)
Builds, caches, and manages the in-memory directed spatial graph (nx.DiGraph)
used for topological analysis and foundational graph queries.
"""
import threading
from typing import Any, Dict, List, Optional
import networkx as nx
from app.repositories.store import DataStore, get_store


class RoadNetworkGraphManager:
    """
    Thread-safe manager for constructing and caching the NetworkX DiGraph
    representation of the physical road infrastructure.
    """

    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or get_store()
        self._graph: Optional[nx.DiGraph] = None
        self._lock = threading.Lock()

    def invalidate_cache(self) -> None:
        """Forces subsequent calls to rebuild the graph from storage."""
        with self._lock:
            self._graph = None

    def build_graph_from_entities(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> nx.DiGraph:
        """Constructs an nx.DiGraph directly from provided node and edge dictionaries."""
        G = nx.DiGraph()

        for n in nodes:
            nid = n["id"]
            G.add_node(
                nid,
                osm_id=n.get("osm_id"),
                latitude=float(n["latitude"]),
                longitude=float(n["longitude"]),
                elevation_m=n.get("elevation_m"),
                metadata=n.get("metadata", {}),
            )

        for e in edges:
            u = e["source_node_id"]
            v = e["target_node_id"]
            length_m = float(e.get("length_meters", 0.0))

            G.add_edge(
                u,
                v,
                edge_id=e["id"],
                osm_way_id=e.get("osm_way_id"),
                road_name=e.get("road_name"),
                road_type=e.get("road_type", "unclassified"),
                length_meters=length_m,
                weight=length_m,
                max_speed_kph=e.get("max_speed_kph"),
                oneway=e.get("oneway", False),
                metadata=e.get("metadata", {}),
            )

        return G

    def get_graph(self, force_rebuild: bool = False) -> nx.DiGraph:
        """
        Returns cached DiGraph, constructing it from current DataStore state
        if not yet cached or force_rebuild is True.
        """
        with self._lock:
            if self._graph is None or force_rebuild:
                nodes = self.store.get_all_road_nodes()
                edges = self.store.get_all_road_edges()
                self._graph = self.build_graph_from_entities(nodes, edges)
            return self._graph


# Global singleton instance
_graph_manager = RoadNetworkGraphManager()


def get_graph_manager() -> RoadNetworkGraphManager:
    """Returns the global RoadNetworkGraphManager singleton."""
    return _graph_manager
