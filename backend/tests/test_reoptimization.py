"""
RouteIQ 2.0 - Dispatch Orchestration & Controlled Re-Optimization Tests (Phase 6)
Tests dynamic event triggers (vehicle breakdown, road closure, cancellation),
debouncing mechanism, and state queries.
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.repositories.store import get_store


@pytest.fixture
def dispatch_setup():
    store = get_store()
    store.clear()

    org = store.create_organization(name="Barak Valley Transporters")
    user = store.create_user(
        organization_id=org["id"],
        email="dispatcher@barakvalley.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Barak Valley Dispatcher",
        role="manager",
    )
    token = create_access_token(subject=user["id"], org_id=org["id"], role="manager")

    # Add 2 vehicles
    veh1 = store.create_vehicle(
        organization_id=org["id"],
        vehicle_name="Silchar Express 1",
        vehicle_type="truck",
        registration_number="AS-11-T-5001",
        capacity=3000.0,
        status="available",
    )
    veh2 = store.create_vehicle(
        organization_id=org["id"],
        vehicle_name="Silchar Express 2",
        vehicle_type="van",
        registration_number="AS-11-V-5002",
        capacity=1500.0,
        status="available",
    )

    # Create locations
    loc_pickup = store.create_location(
        organization_id=org["id"],
        name="Silchar Hub",
        address_line="Station Road",
        city="Silchar",
        state="Assam",
        postal_code="788001",
        latitude=24.8333,
        longitude=92.7789,
    )
    loc_dest1 = store.create_location(
        organization_id=org["id"],
        name="Civil Hospital Silchar",
        address_line="Hospital Road",
        city="Silchar",
        state="Assam",
        postal_code="788005",
        latitude=24.8250,
        longitude=92.7950,
    )
    loc_dest2 = store.create_location(
        organization_id=org["id"],
        name="Assam University Campus",
        address_line="Dargakona",
        city="Silchar",
        state="Assam",
        postal_code="788011",
        latitude=24.7800,
        longitude=92.7500,
    )

    # Add 2 deliveries
    deliv1 = store.create_delivery(
        organization_id=org["id"],
        reference_number="DEL-SIL-001",
        pickup_location_id=loc_pickup["id"],
        delivery_location_id=loc_dest1["id"],
        package_weight=200.0,
        status="pending",
    )
    deliv2 = store.create_delivery(
        organization_id=org["id"],
        reference_number="DEL-SIL-002",
        pickup_location_id=loc_pickup["id"],
        delivery_location_id=loc_dest2["id"],
        package_weight=150.0,
        status="pending",
    )

    return {
        "client": TestClient(app),
        "headers": {"Authorization": f"Bearer {token}"},
        "org": org,
        "veh1": veh1,
        "veh2": veh2,
        "deliv1": deliv1,
        "deliv2": deliv2,
    }


def test_get_dispatch_state(dispatch_setup):
    c = dispatch_setup["client"]
    headers = dispatch_setup["headers"]

    res = c.get("/api/v1/dispatch/state", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["organization_id"] == dispatch_setup["org"]["id"]
    assert data["active_vehicles_count"] == 2
    assert data["active_deliveries_count"] == 2


def test_vehicle_breakdown_trigger_and_debounce(dispatch_setup):
    c = dispatch_setup["client"]
    headers = dispatch_setup["headers"]
    veh1_id = dispatch_setup["veh1"]["id"]

    # Trigger 1: Vehicle Breakdown
    payload = {
        "trigger_type": "VEHICLE_BREAKDOWN",
        "affected_vehicle_id": veh1_id,
        "reason": "Alternator failure on NH-37",
        "profile": "fastest",
    }
    res = c.post("/api/v1/dispatch/reoptimize", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["reoptimization_performed"] is True
    assert data["affected_vehicle_id"] == veh1_id

    # Check that veh1 was transitioned to maintenance
    store = get_store()
    assert store.vehicles[veh1_id]["status"] == "maintenance"

    # Rapid Trigger 2: Immediate duplicate trigger should be DEBOUNCED
    res_rapid = c.post("/api/v1/dispatch/reoptimize", json=payload, headers=headers)
    assert res_rapid.status_code == 200
    rapid_data = res_rapid.json()
    assert rapid_data["reoptimization_performed"] is False
    assert "Debounced" in rapid_data["message"]


def test_delivery_cancellation_trigger(dispatch_setup):
    c = dispatch_setup["client"]
    headers = dispatch_setup["headers"]
    deliv2_id = dispatch_setup["deliv2"]["id"]

    # Sleep or reset last debounce timestamp for org
    from app.dispatch.reoptimization import _last_reopt_timestamps
    _last_reopt_timestamps.pop(dispatch_setup["org"]["id"], None)

    payload = {
        "trigger_type": "DELIVERY_CANCELLATION",
        "affected_delivery_id": deliv2_id,
        "reason": "Customer requested order postponement",
    }
    res = c.post("/api/v1/dispatch/reoptimize", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["reoptimization_performed"] is True

    # Verify delivery marked cancelled in store
    store = get_store()
    assert store.deliveries[deliv2_id]["status"] == "cancelled"
