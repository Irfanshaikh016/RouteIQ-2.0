"""
RouteIQ 2.0 - Phase 3 Road Network Graph & OSM Ingestion Tests
Tests PostGIS data models, deterministic OSM ingestion, NetworkX graph layer,
graph statistics, validation heuristics, and REST API endpoints.
"""
import os
import pytest
from fastapi.testclient import TestClient
import networkx as nx

from app.main import app
from app.core.security import create_access_token, hash_password
from app.graph.corridors import get_corridor, list_corridors
from app.graph.network_builder import RoadNetworkGraphManager, get_graph_manager
from app.graph.osm_ingestion import OSMIngestionPipeline, haversine_distance, parse_max_speed
from app.graph.statistics import calculate_graph_statistics
from app.graph.validator import validate_road_network
from app.repositories.store import get_store

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "sample_ner_osm.xml"
)


@pytest.fixture(autouse=True)
def clean_store():
    """Ensures clean datastore and graph state before each test."""
    store = get_store()
    store.clear()
    graph_manager = get_graph_manager()
    graph_manager.invalidate_cache()
    yield
    store.clear()
    graph_manager.invalidate_cache()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_users():
    """Sets up an organization with admin and operator users."""
    store = get_store()
    org = store.create_organization(name="NER Logistics Hub")
    admin = store.create_user(
        organization_id=org["id"],
        email="admin@nerlogistics.in",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin User",
        role="admin",
    )
    operator = store.create_user(
        organization_id=org["id"],
        email="operator@nerlogistics.in",
        password_hash=hash_password("OperatorPass123!"),
        full_name="Operator User",
        role="operator",
    )
    admin_token = create_access_token(
        subject=admin["id"], org_id=org["id"], role="admin"
    )
    operator_token = create_access_token(
        subject=operator["id"], org_id=org["id"], role="operator"
    )
    return {
        "org": org,
        "admin": admin,
        "operator": operator,
        "admin_token": admin_token,
        "operator_token": operator_token,
    }


# ==============================================================================
# Unit Tests: Geodesic Calculations & Speed Parser
# ==============================================================================
def test_haversine_distance_accuracy():
    """Verifies pure-Python Haversine distance matches expected geodesic distances."""
    # Guwahati (Khanapara) to Shillong: ~60.5 km geodesic distance
    dist = haversine_distance(26.1158, 91.8210, 25.5788, 91.8933)
    assert 59000 <= dist <= 62000, f"Expected ~60km, got {dist}m"

    # Identical points should return 0.0
    assert haversine_distance(26.1158, 91.8210, 26.1158, 91.8210) == 0.0


def test_parse_max_speed():
    """Verifies speed string parsing for various OSM tag variations."""
    assert parse_max_speed("80 km/h") == 80.0
    assert parse_max_speed("60") == 60.0
    assert parse_max_speed("45.5 km/h") == 45.5
    assert round(parse_max_speed("50 mph"), 1) == 80.5
    assert parse_max_speed(None) is None
    assert parse_max_speed("none") is None


# ==============================================================================
# Unit Tests: NER Corridors Specification
# ==============================================================================
def test_ner_corridors_registry():
    """Verifies all 7 NER strategic corridors are defined with complete metadata."""
    corridors = list_corridors()
    assert len(corridors) >= 7

    nh6 = get_corridor("guwahati-shillong-silchar")
    assert nh6 is not None
    assert nh6["national_highway"] == "NH-06"
    assert "Assam" in nh6["states_covered"]
    assert "Meghalaya" in nh6["states_covered"]
    assert len(nh6["intermediate_waypoints"]) >= 5

    # Check waypoint elevations
    shillong_wp = [w for w in nh6["intermediate_waypoints"] if "Shillong" in w["name"]][0]
    assert shillong_wp["elevation_m"] == 1525.0

    assert get_corridor("non-existent-corridor") is None


# ==============================================================================
# Unit Tests: OSM Ingestion Pipeline
# ==============================================================================
def test_osm_ingestion_from_fixture():
    """Verifies parsing and ingestion of sample NER OSM XML fixture."""
    store = get_store()
    pipeline = OSMIngestionPipeline(store=store)

    assert os.path.exists(FIXTURE_PATH), f"Fixture not found at {FIXTURE_PATH}"
    result = pipeline.ingest_file(FIXTURE_PATH)

    assert result["success"] is True
    assert result["nodes_ingested"] == 10
    # Way 2001 (3 segments * 2 bidir = 6) + Way 2002 (2 segments * 2 bidir = 4) +
    # Way 2003 (1 segment oneway = 1) + Way 2004 (1 segment * 2 bidir = 2) +
    # Way 2005 (2 segments * 2 bidir = 4) = 17 directed edges
    assert result["edges_ingested"] == 17
    assert result["total_length_km"] > 0.0

    # Verify nodes in store
    guwahati_node = store.get_road_node_by_osm_id(1001)
    assert guwahati_node is not None
    assert guwahati_node["latitude"] == 26.1158
    assert guwahati_node["longitude"] == 91.8210
    assert guwahati_node["elevation_m"] == 55.0

    shillong_node = store.get_road_node_by_osm_id(1006)
    assert shillong_node is not None
    assert shillong_node["elevation_m"] == 1525.0


def test_osm_ingestion_idempotence():
    """Verifies re-ingesting duplicate nodes does not create redundant records."""
    store = get_store()
    pipeline = OSMIngestionPipeline(store=store)

    res1 = pipeline.ingest_file(FIXTURE_PATH)
    initial_node_count = len(store.road_nodes)

    # Ingest again
    res2 = pipeline.ingest_file(FIXTURE_PATH)
    assert len(store.road_nodes) == initial_node_count
    assert res2["nodes_ingested"] == 10


# ==============================================================================
# Unit Tests: NetworkX Graph Layer & Validation
# ==============================================================================
def test_networkx_graph_construction_and_directionality():
    """Verifies DiGraph construction, edge weights, and one-way constraints."""
    store = get_store()
    pipeline = OSMIngestionPipeline(store=store)
    pipeline.ingest_file(FIXTURE_PATH)

    manager = get_graph_manager()
    G = manager.get_graph(force_rebuild=True)

    assert isinstance(G, nx.DiGraph)
    assert G.number_of_nodes() == 10
    assert G.number_of_edges() == 17

    # Check node attributes
    shillong_id = store.get_road_node_by_osm_id(1006)["id"]
    police_bazar_id = store.get_road_node_by_osm_id(1007)["id"]

    assert G.nodes[shillong_id]["elevation_m"] == 1525.0

    # Shillong -> Police Bazar was oneway="yes" (Way 2003)
    assert G.has_edge(shillong_id, police_bazar_id)
    assert not G.has_edge(police_bazar_id, shillong_id), "Reverse edge should not exist for oneway road"

    # Bidirectional segment (Shillong to Upper Shillong)
    upper_shillong_id = store.get_road_node_by_osm_id(1008)["id"]
    assert G.has_edge(shillong_id, upper_shillong_id)
    assert G.has_edge(upper_shillong_id, shillong_id)


def test_graph_validation_and_statistics():
    """Verifies topology validation heuristics and statistical computation."""
    store = get_store()
    pipeline = OSMIngestionPipeline(store=store)
    pipeline.ingest_file(FIXTURE_PATH)

    manager = get_graph_manager()
    G = manager.get_graph(force_rebuild=True)

    # Validation
    report = validate_road_network(G)
    assert report["is_valid"] is True
    assert len(report["errors"]) == 0
    assert report["metrics"]["total_nodes"] == 10
    assert report["metrics"]["total_edges"] == 17
    assert report["metrics"]["weakly_connected_components"] == 1

    # Statistics
    stats = calculate_graph_statistics(G)
    assert stats["total_nodes"] == 10
    assert stats["total_edges"] == 17
    assert stats["total_length_km"] > 0
    assert stats["largest_component_ratio"] == 1.0

    # Bounding Box should encompass Guwahati and Silchar
    bbox = stats["bounding_box"]
    assert bbox is not None
    assert bbox["min_lat"] <= 24.9  # Silchar latitude
    assert bbox["max_lat"] >= 26.1  # Guwahati latitude
    assert bbox["min_lon"] >= 91.5
    assert bbox["max_lon"] <= 93.0

    # Road type distribution should contain 'trunk', 'primary', 'secondary'
    road_types = {item["road_type"] for item in stats["road_type_distribution"]}
    assert "trunk" in road_types
    assert "primary" in road_types
    assert "secondary" in road_types


# ==============================================================================
# API Integration Tests
# ==============================================================================
def test_unauthenticated_road_network_endpoints_rejected(client):
    """Verifies all road network endpoints require valid authentication."""
    assert client.get("/api/v1/road-network/corridors").status_code == 401
    assert client.get("/api/v1/road-network/stats").status_code == 401
    assert client.get("/api/v1/road-network/health").status_code == 401
    assert client.get("/api/v1/road-network/nodes").status_code == 401
    assert client.get("/api/v1/road-network/edges").status_code == 401
    assert client.post("/api/v1/road-network/ingest", json={"file_path": FIXTURE_PATH}).status_code == 401


def test_corridors_api(client, test_users):
    """Verifies GET /corridors and GET /corridors/{id} with authenticated user."""
    headers = {"Authorization": f"Bearer {test_users['operator_token']}"}

    # List all corridors
    res = client.get("/api/v1/road-network/corridors", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 7
    assert any(c["id"] == "guwahati-shillong-silchar" for c in data["corridors"])

    # Get single corridor
    res_single = client.get(
        "/api/v1/road-network/corridors/guwahati-shillong-silchar", headers=headers
    )
    assert res_single.status_code == 200
    corridor = res_single.json()
    assert corridor["national_highway"] == "NH-06"
    assert len(corridor["intermediate_waypoints"]) >= 5

    # 404 for unknown corridor
    res_404 = client.get(
        "/api/v1/road-network/corridors/unknown-corridor-xyz", headers=headers
    )
    assert res_404.status_code == 404


def test_admin_osm_ingestion_and_rbac(client, test_users):
    """Verifies only admin can trigger OSM ingestion and operator is rejected with 403."""
    operator_headers = {"Authorization": f"Bearer {test_users['operator_token']}"}
    admin_headers = {"Authorization": f"Bearer {test_users['admin_token']}"}

    # Operator should be rejected with 403
    res_op = client.post(
        "/api/v1/road-network/ingest",
        json={"file_path": FIXTURE_PATH},
        headers=operator_headers,
    )
    assert res_op.status_code == 403

    # Admin should succeed
    res_admin = client.post(
        "/api/v1/road-network/ingest",
        json={"file_path": FIXTURE_PATH},
        headers=admin_headers,
    )
    assert res_admin.status_code == 201
    data = res_admin.json()
    assert data["success"] is True
    assert data["nodes_ingested"] == 10
    assert data["edges_ingested"] == 17


def test_stats_health_and_query_endpoints(client, test_users):
    """Verifies stats, health, nodes, and edges endpoints after ingestion."""
    admin_headers = {"Authorization": f"Bearer {test_users['admin_token']}"}

    # Ingest fixture
    client.post(
        "/api/v1/road-network/ingest",
        json={"file_path": FIXTURE_PATH},
        headers=admin_headers,
    )

    # Check stats
    stats_res = client.get("/api/v1/road-network/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_nodes"] == 10
    assert stats["total_edges"] == 17
    assert stats["bounding_box"] is not None

    # Check health
    health_res = client.get("/api/v1/road-network/health", headers=admin_headers)
    assert health_res.status_code == 200
    health = health_res.json()
    assert health["status"] == "healthy"
    assert health["is_connected"] is True

    # List nodes with bounding box filter (Shillong area ~25.5 to 25.6)
    nodes_res = client.get(
        "/api/v1/road-network/nodes?min_lat=25.5&max_lat=25.6",
        headers=admin_headers,
    )
    assert nodes_res.status_code == 200
    nodes_data = nodes_res.json()
    assert nodes_data["total"] >= 2

    # List edges filtered by road_type=trunk
    edges_res = client.get(
        "/api/v1/road-network/edges?road_type=trunk",
        headers=admin_headers,
    )
    assert edges_res.status_code == 200
    edges_data = edges_res.json()
    assert edges_data["total"] > 0
    assert all(e["road_type"] == "trunk" for e in edges_data["edges"])
