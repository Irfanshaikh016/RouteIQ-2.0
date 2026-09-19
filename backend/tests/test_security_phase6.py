"""
RouteIQ 2.0 - Phase 6 Security & Multi-Tenant Isolation Tests
Verifies that telemetry, optimization runs, dispatch states, and administrative controls
are strictly isolated by organization_id and RBAC roles.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.repositories.store import get_store


@pytest.fixture
def multi_org_setup():
    store = get_store()
    store.clear()

    # Org Alpha
    org_a = store.create_organization(name="Alpha Logistics")
    user_a = store.create_user(
        organization_id=org_a["id"],
        email="manager@alpha.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Alpha Manager",
        role="manager",
    )
    token_a = create_access_token(subject=user_a["id"], org_id=org_a["id"], role="manager")

    veh_a = store.create_vehicle(
        organization_id=org_a["id"],
        vehicle_name="Alpha Heavy Truck",
        vehicle_type="truck",
        registration_number="AS-01-AA-1111",
        capacity=5000.0,
        status="available",
    )

    # Org Beta
    org_b = store.create_organization(name="Beta Logistics")
    user_b_operator = store.create_user(
        organization_id=org_b["id"],
        email="operator@beta.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Beta Operator",
        role="operator",  # Operator role: can view and dispatch, cannot create hazard/restrictions
    )
    token_b_op = create_access_token(subject=user_b_operator["id"], org_id=org_b["id"], role="operator")

    veh_b = store.create_vehicle(
        organization_id=org_b["id"],
        vehicle_name="Beta Delivery Van",
        vehicle_type="van",
        registration_number="AS-01-BB-2222",
        capacity=1500.0,
        status="available",
    )

    return {
        "client": TestClient(app),
        "token_a": token_a,
        "token_b_op": token_b_op,
        "org_a": org_a,
        "org_b": org_b,
        "veh_a": veh_a,
        "veh_b": veh_b,
    }


def test_cross_tenant_telemetry_access_blocked(multi_org_setup):
    c = multi_org_setup["client"]
    headers_b = {"Authorization": f"Bearer {multi_org_setup['token_b_op']}"}
    veh_a_id = multi_org_setup["veh_a"]["id"]

    # Beta user cannot query Alpha's vehicle telemetry
    res = c.get(f"/api/v1/telemetry/vehicles/{veh_a_id}", headers=headers_b)
    assert res.status_code == 403

    # Beta user cannot ingest telemetry for Alpha's vehicle
    res_ingest = c.post(
        "/api/v1/telemetry",
        json={"vehicle_id": veh_a_id, "latitude": 26.14, "longitude": 91.73, "speed": 40.0},
        headers=headers_b,
    )
    assert res_ingest.status_code == 403


def test_cross_tenant_optimization_isolation(multi_org_setup):
    c = multi_org_setup["client"]
    headers_a = {"Authorization": f"Bearer {multi_org_setup['token_a']}"}
    headers_b = {"Authorization": f"Bearer {multi_org_setup['token_b_op']}"}
    veh_a_id = multi_org_setup["veh_a"]["id"]

    # 1. Alpha runs CVRP optimization
    payload = {
        "problem_type": "CVRP",
        "profile": "fastest",
        "depot_lat": 26.1445,
        "depot_lon": 91.7362,
        "vehicles": [{"vehicle_id": veh_a_id, "capacity": 5000.0}],
        "deliveries": [
            {"delivery_id": "d-1", "latitude": 26.1500, "longitude": 91.7800, "demand": 300.0}
        ],
    }
    res_opt = c.post("/api/v1/optimization/cvrp", json=payload, headers=headers_a)
    assert res_opt.status_code == 200
    opt_id = res_opt.json()["optimization_id"]

    # 2. Beta attempts to access Alpha's optimization run -> 404 (not found in Beta's org scope)
    res_cross = c.get(f"/api/v1/optimization/{opt_id}", headers=headers_b)
    assert res_cross.status_code == 404


def test_rbac_restriction_creation_requires_manager_or_admin(multi_org_setup):
    c = multi_org_setup["client"]
    headers_b_op = {"Authorization": f"Bearer {multi_org_setup['token_b_op']}"}

    # Operator role tries to create a road restriction -> 403 Forbidden
    payload = {
        "road_edge_id": "NH-37-ALPHA",
        "status": "CLOSED",
        "reason": "Unauthorized closure attempt",
    }
    res = c.post("/api/v1/weather/restrictions", json=payload, headers=headers_b_op)
    assert res.status_code == 403

    # Operator role tries to create a hazard event -> 403 Forbidden
    hazard_payload = {
        "hazard_type": "flood",
        "severity": 0.5,
        "latitude": 26.14,
        "longitude": 91.73,
        "expires_at": "2026-10-01T00:00:00Z",
    }
    res_hazard = c.post("/api/v1/weather/hazards", json=hazard_payload, headers=headers_b_op)
    assert res_hazard.status_code == 403
