"""
RouteIQ 2.0 - Phase 5 GIS Operations Console Integration Tests
Tests the full lifecycle of APIs consumed by the GIS dashboard:
- Tenant-isolated assets (vehicles, locations, deliveries)
- Road network corridors and edges
- Multi-objective route calculation & multi-profile comparison
- GeoJSON LineString geometry and edge explainability payloads
- Strict cross-tenant isolation in the GIS console context
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.graph.network_builder import get_graph_manager
from app.graph.osm_ingestion import OSMIngestionPipeline
from app.repositories.store import get_store

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "sample_ner_osm.xml"
)


@pytest.fixture(autouse=True)
def setup_gis_state():
    """Sets up clean store, ingests sample NER OSM fixture, and clears caches."""
    store = get_store()
    store.clear()
    graph_manager = get_graph_manager()
    graph_manager.invalidate_cache()

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
def org_a_auth():
    store = get_store()
    org = store.create_organization(name="Assam Logistics Corp")
    user = store.create_user(
        organization_id=org["id"],
        email="manager@assam-logistics.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Assam Manager",
        role="manager",
    )
    token = create_access_token(subject=user["id"], org_id=org["id"], role="manager")
    return {
        "org_id": org["id"],
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def org_b_auth():
    store = get_store()
    org = store.create_organization(name="Meghalaya Logistics Corp")
    user = store.create_user(
        organization_id=org["id"],
        email="manager@meghalaya-logistics.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Meghalaya Manager",
        role="manager",
    )
    token = create_access_token(subject=user["id"], org_id=org["id"], role="manager")
    return {
        "org_id": org["id"],
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def test_gis_dashboard_data_aggregation(client, org_a_auth):
    """Verify that all GIS dashboard dependencies resolve cleanly for an authenticated session."""
    headers = org_a_auth["headers"]

    # 1. Fetch Corridors for map layer
    corr_res = client.get("/api/v1/road-network/corridors", headers=headers)
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["total"] >= 7
    assert len(corr_data["corridors"]) >= 7

    # 2. Fetch Routing Health for operational status
    health_res = client.get("/api/v1/routing/health", headers=headers)
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["graph_available"] is True
    assert health_data["total_nodes"] > 0

    # 3. Calculate Route (Guwahati to Shillong)
    route_req = {
        "origin": {"latitude": 26.1158, "longitude": 91.8210},
        "destination": {"latitude": 25.5788, "longitude": 91.8933},
        "profile": "balanced",
    }
    route_res = client.post("/api/v1/routing/route", json=route_req, headers=headers)
    assert route_res.status_code == 200
    route_data = route_res.json()

    # Validate GeoJSON LineString format required by Leaflet
    assert "geometry" in route_data
    assert route_data["geometry"]["type"] == "LineString"
    assert len(route_data["geometry"]["coordinates"]) >= 2

    # Validate metrics cards required by RouteMetricsPanel
    assert "metrics" in route_data
    assert route_data["metrics"]["distance_km"] > 0
    assert route_data["metrics"]["estimated_time_minutes"] > 0
    assert "objective_score" in route_data["metrics"]

    # Validate edge explainability required by RouteSegmentInspector
    assert "edges" in route_data
    assert len(route_data["edges"]) >= 1
    for edge in route_data["edges"]:
        assert "cost_breakdown" in edge
        assert "risk_breakdown" in edge
        assert "distance_cost" in edge["cost_breakdown"]
        assert "overall_risk" in edge["risk_breakdown"]


def test_gis_profile_comparison_endpoint(client, org_a_auth):
    """Verify multi-profile comparison for side-by-side neutral analysis."""
    headers = org_a_auth["headers"]

    compare_req = {
        "origin": {"latitude": 26.1158, "longitude": 91.8210},
        "destination": {"latitude": 25.5788, "longitude": 91.8933},
    }
    res = client.post("/api/v1/routing/compare", json=compare_req, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "routes" in data
    assert len(data["routes"]) == 3

    profiles = {r["profile"] for r in data["routes"]}
    assert profiles == {"fastest", "safest", "balanced"}


def test_gis_tenant_isolation(client, org_a_auth, org_b_auth):
    """Verify that tenant vehicles and deliveries in the console never leak across tenants."""
    headers_a = org_a_auth["headers"]
    headers_b = org_b_auth["headers"]

    # Create vehicle in Org A
    veh_payload = {
        "vehicle_name": "Org A Console Express",
        "vehicle_type": "truck",
        "registration_number": "AS-01-GIS-9999",
        "capacity": 5000.0,
        "status": "available",
    }
    create_res = client.post("/api/v1/vehicles", json=veh_payload, headers=headers_a)
    assert create_res.status_code == 201
    veh_id = create_res.json()["id"]

    # Org A console sees the vehicle
    list_a = client.get("/api/v1/vehicles", headers=headers_a)
    assert list_a.status_code == 200
    ids_a = [v["id"] for v in list_a.json()]
    assert veh_id in ids_a

    # Org B console CANNOT see Org A's vehicle on their map
    list_b = client.get("/api/v1/vehicles", headers=headers_b)
    assert list_b.status_code == 200
    ids_b = [v["id"] for v in list_b.json()]
    assert veh_id not in ids_b
