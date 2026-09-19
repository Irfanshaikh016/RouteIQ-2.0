"""
RouteIQ 2.0 - Capacitated Vehicle Routing Problem (CVRP) Tests (Phase 6)
Tests OR-Tools CVRP solving, capacity constraint enforcement, multi-vehicle routing,
and infeasibility diagnostic engine.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.repositories.store import get_store


@pytest.fixture
def cvrp_setup():
    store = get_store()
    store.clear()

    org = store.create_organization(name="Assam Freight & Logistics")
    user = store.create_user(
        organization_id=org["id"],
        email="planner@assamfreight.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Fleet Route Planner",
        role="manager",
    )
    token = create_access_token(subject=user["id"], org_id=org["id"], role="manager")

    return {
        "client": TestClient(app),
        "headers": {"Authorization": f"Bearer {token}"},
        "org": org,
    }


def test_feasible_cvrp_multi_vehicle(cvrp_setup):
    c = cvrp_setup["client"]
    headers = cvrp_setup["headers"]

    payload = {
        "problem_type": "CVRP",
        "profile": "fastest",
        "depot_lat": 26.1445,
        "depot_lon": 91.7362,
        "vehicles": [
            {"vehicle_id": "v-1", "vehicle_name": "Tata 407", "capacity": 2000.0},
            {"vehicle_id": "v-2", "vehicle_name": "Mahindra Bolero Maxi", "capacity": 1200.0},
        ],
        "deliveries": [
            {"delivery_id": "d-1", "latitude": 26.1500, "longitude": 91.7800, "demand": 500.0},
            {"delivery_id": "d-2", "latitude": 26.1200, "longitude": 91.8000, "demand": 800.0},
            {"delivery_id": "d-3", "latitude": 26.1750, "longitude": 91.7450, "demand": 700.0},
            {"delivery_id": "d-4", "latitude": 26.1550, "longitude": 91.6700, "demand": 600.0},
        ],
    }

    res = c.post("/api/v1/optimization/cvrp", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["problem_type"] == "CVRP"
    assert data["total_deliveries"] == 4
    assert data["served_deliveries_count"] == 4
    assert len(data["routes"]) >= 1

    # Verify vehicle capacity was not violated on any assigned route
    total_assigned_demand = 0.0
    for r in data["routes"]:
        assert r["peak_load"] <= r["capacity"]
        total_assigned_demand += r["peak_load"]
    assert total_assigned_demand == 2600.0


def test_infeasible_cvrp_excessive_demand(cvrp_setup):
    c = cvrp_setup["client"]
    headers = cvrp_setup["headers"]

    # Total fleet capacity = 1000 kg, total demand = 2500 kg
    payload = {
        "problem_type": "CVRP",
        "profile": "balanced",
        "depot_lat": 26.1445,
        "depot_lon": 91.7362,
        "vehicles": [
            {"vehicle_id": "v-small", "vehicle_name": "Small Van", "capacity": 1000.0},
        ],
        "deliveries": [
            {"delivery_id": "d-heavy-1", "latitude": 26.1500, "longitude": 91.7800, "demand": 1500.0},
            {"delivery_id": "d-heavy-2", "latitude": 26.1750, "longitude": 91.7450, "demand": 1000.0},
        ],
    }

    res = c.post("/api/v1/optimization/cvrp", json=payload, headers=headers)
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert "reason" in detail
    assert "DELIVERY_EXCEEDS_MAX_CAPACITY" in detail["reason"] or "INSUFFICIENT_CAPACITY" in detail["reason"]


def test_optimization_neutral_profile_comparison(cvrp_setup):
    c = cvrp_setup["client"]
    headers = cvrp_setup["headers"]

    payload = {
        "problem_type": "CVRP",
        "profile": "balanced",
        "depot_lat": 26.1445,
        "depot_lon": 91.7362,
        "vehicles": [
            {"vehicle_id": "v-1", "vehicle_name": "Fleet Truck 1", "capacity": 3000.0},
        ],
        "deliveries": [
            {"delivery_id": "d-1", "latitude": 26.1500, "longitude": 91.7800, "demand": 400.0},
            {"delivery_id": "d-2", "latitude": 26.1750, "longitude": 91.7450, "demand": 600.0},
        ],
    }

    res = c.post("/api/v1/optimization/compare", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "fastest" in data["profiles"]
    assert "safest" in data["profiles"]
    assert "balanced" in data["profiles"]
    # Verify no ranking or biased winner declared
    assert "winner" not in data
    assert "ranking" not in data
