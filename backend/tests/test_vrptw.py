"""
RouteIQ 2.0 - Vehicle Routing Problem with Time Windows (VRP-TW) Tests (Phase 6)
Tests OR-Tools VRP-TW solving, customer time windows, service durations, and schedule generation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.repositories.store import get_store


@pytest.fixture
def vrptw_setup():
    store = get_store()
    store.clear()

    org = store.create_organization(name="Meghalaya Express Deliveries")
    user = store.create_user(
        organization_id=org["id"],
        email="scheduler@meghalayaexpress.in",
        password_hash=hash_password("Pass#2026"),
        full_name="VRP Scheduler",
        role="manager",
    )
    token = create_access_token(subject=user["id"], org_id=org["id"], role="manager")

    return {
        "client": TestClient(app),
        "headers": {"Authorization": f"Bearer {token}"},
        "org": org,
    }


def test_feasible_vrptw_with_service_duration(vrptw_setup):
    c = vrptw_setup["client"]
    headers = vrptw_setup["headers"]

    payload = {
        "problem_type": "VRPTW",
        "profile": "fastest",
        "depot_lat": 26.1445,
        "depot_lon": 91.7362,
        "vehicles": [
            {"vehicle_id": "v-1", "vehicle_name": "Express Van 1", "capacity": 2500.0},
        ],
        "deliveries": [
            {
                "delivery_id": "d-morning",
                "latitude": 26.1500,
                "longitude": 91.7500,
                "demand": 300.0,
                "time_window_start_minutes": 10,
                "time_window_end_minutes": 120,
                "service_duration_minutes": 15,
            },
            {
                "delivery_id": "d-afternoon",
                "latitude": 26.1700,
                "longitude": 91.7600,
                "demand": 400.0,
                "time_window_start_minutes": 60,
                "time_window_end_minutes": 240,
                "service_duration_minutes": 20,
            },
        ],
    }

    res = c.post("/api/v1/optimization/vrptw", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["problem_type"] == "VRPTW"
    assert data["served_deliveries_count"] == 2
    assert len(data["routes"]) == 1

    route = data["routes"][0]
    stops = route["stops"]
    assert len(stops) >= 3  # Depot, 2 deliveries, Depot

    # Verify stop time schedules are monotonic
    for i in range(len(stops) - 1):
        assert stops[i]["departure_time_minutes"] <= stops[i + 1]["arrival_time_minutes"]


def test_infeasible_time_window_conflict(vrptw_setup):
    c = vrptw_setup["client"]
    headers = vrptw_setup["headers"]

    # Delivery deadline is 1 minute from depot, but travel takes > 5 minutes
    payload = {
        "problem_type": "VRPTW",
        "profile": "fastest",
        "depot_lat": 26.1445,
        "depot_lon": 91.7362,
        "vehicles": [
            {"vehicle_id": "v-1", "vehicle_name": "Van 1", "capacity": 2000.0},
        ],
        "deliveries": [
            {
                "delivery_id": "d-impossible",
                "latitude": 26.1900,
                "longitude": 91.8500,
                "demand": 200.0,
                "time_window_start_minutes": 0,
                "time_window_end_minutes": 1,  # Impossible deadline
                "service_duration_minutes": 10,
            },
        ],
    }

    res = c.post("/api/v1/optimization/vrptw", json=payload, headers=headers)
    assert res.status_code in (409, 422)
