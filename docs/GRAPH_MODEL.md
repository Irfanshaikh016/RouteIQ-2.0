# RouteIQ 2.0 — NetworkX Spatial Graph Model & Topology

## 1. Network Representation

RouteIQ 2.0 uses **NetworkX** (`networkx.DiGraph`) as its in-memory spatial graph abstraction. Every road node is a graph vertex, and every directed road segment is a weighted directed edge.

```python
import networkx as nx

G = nx.DiGraph()
```

---

## 2. Graph Node & Edge Attributes

### Node Attributes
Each node in `G.nodes[node_id]` stores:
- `node_id` (str): UUID corresponding to `road_nodes.id`
- `osm_id` (Optional[int]): OpenStreetMap node ID
- `latitude` (float): WGS84 decimal degrees `[-90.0, 90.0]`
- `longitude` (float): WGS84 decimal degrees `[-180.0, 180.0]`
- `elevation_m` (Optional[float]): Altitude above sea level in meters
- `metadata` (dict): Raw OSM tags (place, junction, amenity, etc.)

### Edge Attributes
Each directed edge `G[u][v]` stores:
- `edge_id` (str): UUID corresponding to `road_edges.id`
- `osm_way_id` (Optional[int]): OpenStreetMap way ID
- `road_name` (Optional[str]): Road designation (e.g. "NH 6")
- `road_type` (str): Highway classification (`trunk`, `primary`, etc.)
- `length_meters` (float): Geodesic distance in meters
- `weight` (float): Default routing cost (initialized to `length_meters`)
- `max_speed_kph` (Optional[float]): Speed limit in km/h
- `oneway` (bool): True if restricted to forward traversal
- `metadata` (dict): Lanes, surface, and bridge/tunnel tags

---

## 3. Thread-Safe Graph Manager & Caching

The `RoadNetworkGraphManager` in `app/graph/network_builder.py` provides a thread-safe singleton that caches the constructed `nx.DiGraph`:

```python
class RoadNetworkGraphManager:
    def __init__(self, store: Optional[DataStore] = None):
        self.store = store or get_store()
        self._graph: Optional[nx.DiGraph] = None
        self._lock = threading.Lock()

    def invalidate_cache(self) -> None:
        with self._lock:
            self._graph = None

    def get_graph(self, force_rebuild: bool = False) -> nx.DiGraph:
        with self._lock:
            if self._graph is None or force_rebuild:
                nodes = self.store.get_all_road_nodes()
                edges = self.store.get_all_road_edges()
                self._graph = self.build_graph_from_entities(nodes, edges)
            return self._graph
```

When an admin ingests new OSM data via `POST /api/v1/road-network/ingest`, the pipeline automatically invokes `invalidate_cache()`, ensuring downstream queries immediately reflect new infrastructure without restarting the backend process.

---

## 4. Graph Topology Validation Heuristics

The graph validator (`app/graph/validator.py`) runs topological integrity checks:

1. **Coordinate Validity**: Verifies latitude is within `[-90, 90]` and longitude within `[-180, 180]`.
2. **Negative Edge Detection**: Rejects any edge with `length_meters < 0.0`.
3. **Self-Loop Identification**: Flags edges where source node equals target node (`u == v`).
4. **Disconnected Component Analysis**:
   - Computes weakly connected components (`nx.weakly_connected_components`).
   - Computes strongly connected components (`nx.strongly_connected_components`).
   - Calculates the ratio of nodes in the largest connected component.
5. **Dead-End & Isolated Node Auditing**:
   - Identifies isolated nodes (`degree == 0`).
   - Identifies dead-ends (`in_degree == 0` or `out_degree == 0`).

---

## 5. Statistical Diagnostics

The statistics engine (`app/graph/statistics.py`) aggregates:
- Total road vertices and directed edges.
- Total network length in kilometers.
- Road type breakdown with segment counts and cumulative distance per road classification.
- Regional bounding box (`min_lat`, `max_lat`, `min_lon`, `max_lon`).
- Component connectivity percentages.
