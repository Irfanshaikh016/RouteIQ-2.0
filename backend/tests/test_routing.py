"""
RouteIQ 2.0 - Phase 4 Multi-Objective Routing Optimization Tests
Tests coordinate validation, nearest-node resolver, speed fallbacks, risk heuristics,
NetworkX multi-objective pathfinding, profile weighting, oneway enforcement,
GeoJSON LineString formatting, and REST API endpoints.
"""
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token, hash_password
from app.graph.network_builder import get_graph_manager
from app.graph.osm_ingestion import OSMIngestionPipeline
from app.repositories.store import get_store
from app.routing.cost_model import calculate_edge_cost, get_estimated_speed_kph
from app.routing.exceptions import (
    InvalidCoordinateError,
    NearestNodeNotFoundError,
    NoRouteFoundError,
    UnsupportedProfileError,
)
from app.routing.geometry import build_geojson_linestring
from app.routing.pathfinder import find_optimal_path
from app.routing.profiles import get_profile, list_profiles
from app.routing.risk_model import get_default_hazard_provider
from app.routing.route_service import RouteService, get_route_service
from app.routing.schemas import Coordinate, RouteRequest
from app.routing.validators import validate_coordinates, validate_profile_name

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "sample_ner_osm.xml"
)


@pytest.fixture(autouse=True)
def setup_test_state():
    """Sets up clean store, ingests sample NER OSM fixture, and clears caches."""
    store = get_store()
    store.clear()
    graph_manager = get_graph_manager()
    graph_manager.invalidate_cache()

    # Ingest baseline NER corridor fixture
    pipeline = OSMIngestionPipeline(store=store)
    pipeline.ingest_file(FIXTURE_PATH)
    graph_manager.invalidate_cache()

    yield

    store.clear()
    graph_manager.invalidate_cache()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_auth():
    """Sets up test organization and authenticated user tokens."""
    store = get_store()
    org = store.create_organization(name="NER Freight Logistics")
    user = store.create_user(
        organization_id=org["id"],
        email="dispatcher@nerfreight.in",
        password_hash=hash_password("DispatchSecure2026!"),
        full_name="Fleet Dispatcher",
        role="operator",
    )
    token = create_access_token(
        subject=user["id"], org_id=org["id"], role="operator"
    )
    return {
        "org": org,
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


# ==============================================================================
# Unit Tests: Validators & Profiles
# ==============================================================================
def test_coordinate_validation():
    """Verifies coordinate boundary checks."""
    validate_coordinates(26.1445, 91.7362)
    validate_coordinates(-90.0, -180.0)
    validate_coordinates(90.0, 180.0)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(95.0, 91.7)

    with pytest.raises(InvalidCoordinateError):
        validate_coordinates(26.1, 195.0)


def test_profile_weight_normalization():
    """Verifies all routing profiles have normalized weights summing to 1.0."""
    profiles = list_profiles()
    assert len(profiles) >= 3

    for p in profiles:
        weights = p["weights"]
        total_w = sum(weights.values())
        assert abs(total_w - 1.0) < 1e-4, f"Profile {p['name']} weights do not sum to 1.0"
        assert p["name"] in ("fastest", "safest", "balanced")

    # Unsupported profile raises error
    with pytest.raises(UnsupportedProfileError):
        get_profile("non_existent_profile")


# ==============================================================================
# Unit Tests: Speed Fallbacks & Cost Model
# ==============================================================================
def test_speed_fallbacks_and_time_estimation():
    """Verifies tagged speeds and fallback speeds by road class."""
    # Tagged speed limit takes precedence
    assert get_estimated_speed_kph("trunk", max_speed_kph=80.0) == 80.0
    # Fallback speeds by classification
    assert get_estimated_speed_kph("motorway") == 90.0
    assert get_estimated_speed_kph("trunk") == 60.0
    assert get_estimated_speed_kph("primary") == 50.0
    assert get_estimated_speed_kph("residential") == 20.0
    assert get_estimated_speed_kph("unknown_class") == 30.0


def test_edge_cost_and_risk_heuristics():
    """Verifies edge cost calculation and risk breakdown output."""
    hazard_provider = get_default_hazard_provider()
    u_attrs = {"latitude": 26.1158, "longitude": 91.8210, "elevation_m": 55.0}
    v_attrs = {"latitude": 25.5788, "longitude": 91.8933, "elevation_m": 1525.0}
    edge_attrs = {
        "road_type": "trunk",
        "length_meters": 60000.0,
        "max_speed_kph": 60.0,
        "metadata": {"surface": "asphalt"},
    }

    profile = get_profile("balanced")
    total_cost, cost_dict, risk_dict, time_s = calculate_edge_cost(
        u_attrs=u_attrs,
        v_attrs=v_attrs,
        edge_attrs=edge_attrs,
        weights=profile["weights"],
        hazard_provider=hazard_provider,
    )

    assert total_cost > 0.0
    assert cost_dict["total_cost"] == total_cost
    assert 0.0 <= risk_dict["overall_risk"] <= 1.0
    assert 0.0 <= risk_dict["terrain_risk"] <= 1.0
    # High elevation delta (1525m - 55m = 1470m) should register elevation difficulty
    assert risk_dict["terrain_risk"] > 0.0


# ==============================================================================
# Unit Tests: Nearest Node Resolver & Pathfinding
# ==============================================================================
def test_nearest_node_resolver():
    """Verifies coordinate snapping to closest road network node."""
    route_service = get_route_service()

    # Exact Khanapara coordinate (node 1001: 26.1158, 91.8210)
    node, dist = route_service.find_nearest_node(26.1158, 91.8210)
    assert node["osm_id"] == 1001
    assert dist < 1.0  # within 1 meter

    # Coordinate outside search radius (e.g. South Pole)
    with pytest.raises(NearestNodeNotFoundError):
        route_service.find_nearest_node(-85.0, 0.0, max_distance_km=10.0)


def test_pathfinding_and_directionality():
    """Verifies multi-objective path discovery and oneway street enforcement."""
    store = get_store()
    manager = get_graph_manager()
    G = manager.get_graph()

    khanapara_id = store.get_road_node_by_osm_id(1001)["id"]
    shillong_id = store.get_road_node_by_osm_id(1006)["id"]
    police_bazar_id = store.get_road_node_by_osm_id(1007)["id"]

    # 1. Path from Guwahati (Khanapara) to Shillong Center
    path = find_optimal_path(G, khanapara_id, shillong_id, profile_name="fastest")
    assert len(path) >= 3
    assert path[0] == khanapara_id
    assert path[-1] == shillong_id

    # 2. Forward oneway street traversal (Shillong Center -> Police Bazar)
    fwd_path = find_optimal_path(G, shillong_id, police_bazar_id, profile_name="balanced")
    assert fwd_path == [shillong_id, police_bazar_id]

    # 3. Reverse oneway street traversal (Police Bazar -> Shillong Center) must fail
    with pytest.raises(NoRouteFoundError):
        find_optimal_path(G, police_bazar_id, shillong_id, profile_name="balanced")


def test_geojson_linestring_formatting():
    """Verifies GeoJSON format adheres to [longitude, latitude] ordering."""
    coords = [[91.8210, 26.1158], [91.8933, 25.5788]]
    geo = build_geojson_linestring(coords)
    assert geo["type"] == "LineString"
    assert geo["coordinates"] == coords
    # Check [lon, lat] ordering: lon > 90, lat < 30
    assert geo["coordinates"][0][0] > 90.0
    assert geo["coordinates"][0][1] < 30.0


# ==============================================================================
# Integration Tests: Route Calculation Endpoints
# ==============================================================================
def test_unauthenticated_routing_rejected(client):
    """Verifies routing endpoints require valid JWT authentication."""
    payload = {
        "origin": {"latitude": 26.1158, "longitude": 91.8210},
        "destination": {"latitude": 25.5788, "longitude": 91.8933},
        "profile": "balanced",
    }
    assert client.post("/api/v1/routing/route", json=payload).status_code == 401
    assert client.get("/api/v1/routing/profiles").status_code == 401
    assert client.get("/api/v1/routing/health").status_code == 401
    assert client.post("/api/v1/routing/compare", json=payload).status_code == 401


def test_get_routing_profiles_api(client, test_auth):
    """Verifies GET /api/v1/routing/profiles returns all 3 profiles."""
    res = client.get("/api/v1/routing/profiles", headers=test_auth["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 3
    names = {p["name"] for p in data["profiles"]}
    assert "fastest" in names
    assert "safest" in names
    assert "balanced" in names


def test_get_routing_health_api(client, test_auth):
    """Verifies GET /api/v1/routing/health returns healthy status."""
    res = client.get("/api/v1/routing/health", headers=test_auth["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["graph_available"] is True
    assert data["total_nodes"] == 10
    assert data["total_edges"] == 17
    assert "fastest" in data["profiles_loaded"]


def test_calculate_route_api_success(client, test_auth):
    """Verifies POST /api/v1/routing/route returns complete route response."""
    payload = {
        "origin": {"latitude": 26.1158, "longitude": 91.8210},     # Guwahati Khanapara
        "destination": {"latitude": 25.5788, "longitude": 91.8933},# Shillong Center
        "profile": "fastest",
    }
    res = client.post("/api/v1/routing/route", json=payload, headers=test_auth["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["profile"] == "fastest"
    assert "route_id" in data
    assert data["metrics"]["distance_km"] > 50.0
    assert data["metrics"]["estimated_time_minutes"] > 0.0
    assert len(data["nodes"]) >= 3
    assert len(data["edges"]) >= 2
    assert data["geometry"]["type"] == "LineString"
    assert len(data["geometry"]["coordinates"]) == len(data["nodes"])

    # Verify edge details have cost and risk breakdowns
    first_edge = data["edges"][0]
    assert "cost_breakdown" in first_edge
    assert "risk_breakdown" in first_edge
    assert first_edge["cost_breakdown"]["total_cost"] > 0


def test_calculate_route_invalid_coordinates(client, test_auth):
    """Verifies 400 Bad Request on invalid coordinate ranges."""
    payload = {
        "origin": {"latitude": 99.0, "longitude": 91.8210},
        "destination": {"latitude": 25.5788, "longitude": 91.8933},
        "profile": "balanced",
    }
    res = client.post("/api/v1/routing/route", json=payload, headers=test_auth["headers"])
    assert res.status_code == 422 or res.status_code == 400


def test_calculate_route_unsupported_profile(client, test_auth):
    """Verifies 400 Bad Request on unrecognized profile name."""
    payload = {
        "origin": {"latitude": 26.1158, "longitude": 91.8210},
        "destination": {"latitude": 25.5788, "longitude": 91.8933},
        "profile": "unsupported_profile_mode",
    }
    res = client.post("/api/v1/routing/route", json=payload, headers=test_auth["headers"])
    assert res.status_code == 400
    assert "Unsupported routing profile" in res.json()["detail"]


def test_compare_routes_api(client, test_auth):
    """Verifies POST /api/v1/routing/compare evaluates all 3 profiles without winner bias."""
    payload = {
        "origin": {"latitude": 26.1158, "longitude": 91.8210},
        "destination": {"latitude": 25.5788, "longitude": 91.8933},
    }
    res = client.post("/api/v1/routing/compare", json=payload, headers=test_auth["headers"])
    assert res.status_code == 200
    data = res.json()

    assert "routes" in data
    assert len(data["routes"]) == 3
    profiles_returned = {r["profile"] for r in data["routes"]}
    assert profiles_returned == {"fastest", "safest", "balanced"}

    for r in data["routes"]:
        assert r["metrics"]["distance_km"] > 0
        assert r["metrics"]["estimated_time_minutes"] > 0
        assert r["geometry"]["type"] == "LineString"
