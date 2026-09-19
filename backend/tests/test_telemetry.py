"""
RouteIQ 2.0 - Vehicle Telemetry Subsystem Tests (Phase 6)
Tests GPS ingestion, validation, freshness states (LIVE, STALE, OFFLINE),
fleet aggregation, and multi-tenant scoping.
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.repositories.store import get_store
from app.telemetry.schemas import TelemetryFreshness
from app.telemetry.state import calculate_freshness


@pytest.fixture
def telemetry_setup():
    store = get_store()
    store.clear()

    # Create Org A with 2 vehicles
    org_a = store.create_organization(name="Assam Roadways")
    user_a = store.create_user(
        organization_id=org_a["id"],
        email="dispatcher@assamroadways.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Assam Dispatcher",
        role="manager",
    )
    token_a = create_access_token(subject=user_a["id"], org_id=org_a["id"], role="manager")

    veh_a1 = store.create_vehicle(
        organization_id=org_a["id"],
        vehicle_name="Assam Freightliner 1",
        vehicle_type="truck",
        registration_number="AS-01-T-1001",
        capacity=5000.0,
        status="available",
    )
    veh_a2 = store.create_vehicle(
        organization_id=org_a["id"],
        vehicle_name="Assam Freightliner 2",
        vehicle_type="truck",
        registration_number="AS-01-T-1002",
        capacity=3000.0,
        status="available",
    )

    # Create Org B with 1 vehicle
    org_b = store.create_organization(name="Meghalaya Logistics")
    user_b = store.create_user(
        organization_id=org_b["id"],
        email="manager@meghalayalogistics.in",
        password_hash=hash_password("Pass#2026"),
        full_name="Meghalaya Manager",
        role="manager",
    )
    token_b = create_access_token(subject=user_b["id"], org_id=org_b["id"], role="manager")

    veh_b1 = store.create_vehicle(
        organization_id=org_b["id"],
        vehicle_name="Meghalaya Van 1",
        vehicle_type="van",
        registration_number="ML-05-V-2001",
        capacity=1500.0,
        status="available",
    )

    return {
        "client": TestClient(app),
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "org_a": org_a,
        "org_b": org_b,
        "veh_a1": veh_a1,
        "veh_a2": veh_a2,
        "veh_b1": veh_b1,
    }


def test_telemetry_freshness_logic():
    now = datetime.now(timezone.utc)
    # < 5 minutes -> LIVE
    t_live = now - timedelta(minutes=2)
    assert calculate_freshness(t_live, now) == TelemetryFreshness.LIVE

    # 5-60 minutes -> STALE
    t_stale = now - timedelta(minutes=15)
    assert calculate_freshness(t_stale, now) == TelemetryFreshness.STALE

    # > 60 minutes -> OFFLINE
    t_offline = now - timedelta(minutes=90)
    assert calculate_freshness(t_offline, now) == TelemetryFreshness.OFFLINE

    # None -> OFFLINE
    assert calculate_freshness(None, now) == TelemetryFreshness.OFFLINE


def test_valid_telemetry_ingestion(telemetry_setup):
    c = telemetry_setup["client"]
    headers = telemetry_setup["headers_a"]
    veh_id = telemetry_setup["veh_a1"]["id"]

    now = datetime.now(timezone.utc)
    payload = {
        "vehicle_id": veh_id,
        "timestamp": now.isoformat(),
        "latitude": 26.1445,
        "longitude": 91.7362,
        "speed": 45.5,
        "heading": 180.0,
        "ignition_status": True,
        "battery_level": 88.0,
        "accuracy": 4.2,
        "source": "SIMULATED_TEST",
    }
    res = c.post("/api/v1/telemetry", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["vehicle_id"] == veh_id
    assert data["latitude"] == 26.1445
    assert data["longitude"] == 91.7362
    assert data["speed"] == 45.5
    assert data["freshness"] == "LIVE"
    assert data["source"] == "SIMULATED_TEST"


def test_telemetry_validation_rejects_invalid_inputs(telemetry_setup):
    c = telemetry_setup["client"]
    headers = telemetry_setup["headers_a"]
    veh_id = telemetry_setup["veh_a1"]["id"]

    # Invalid latitude > 90
    res1 = c.post(
        "/api/v1/telemetry",
        json={"vehicle_id": veh_id, "latitude": 95.0, "longitude": 91.73, "speed": 40.0},
        headers=headers,
    )
    assert res1.status_code in (400, 422)

    # Invalid longitude < -180
    res2 = c.post(
        "/api/v1/telemetry",
        json={"vehicle_id": veh_id, "latitude": 26.14, "longitude": -195.0, "speed": 40.0},
        headers=headers,
    )
    assert res2.status_code in (400, 422)

    # Negative speed
    res3 = c.post(
        "/api/v1/telemetry",
        json={"vehicle_id": veh_id, "latitude": 26.14, "longitude": 91.73, "speed": -10.0},
        headers=headers,
    )
    assert res3.status_code in (400, 422)


def test_vehicle_telemetry_lookup_and_fleet_summary(telemetry_setup):
    c = telemetry_setup["client"]
    headers = telemetry_setup["headers_a"]
    veh_a1_id = telemetry_setup["veh_a1"]["id"]
    veh_a2_id = telemetry_setup["veh_a2"]["id"]

    # Ingest for veh_a1 (LIVE)
    now = datetime.now(timezone.utc)
    c.post(
        "/api/v1/telemetry",
        json={"vehicle_id": veh_a1_id, "latitude": 26.14, "longitude": 91.73, "speed": 50.0},
        headers=headers,
    )

    # Ingest for veh_a2 (STALE: 20 minutes ago)
    t_stale = now - timedelta(minutes=20)
    c.post(
        "/api/v1/telemetry",
        json={"vehicle_id": veh_a2_id, "timestamp": t_stale.isoformat(), "latitude": 26.15, "longitude": 91.74, "speed": 0.0},
        headers=headers,
    )

    # Lookup single vehicle state
    res_v1 = c.get(f"/api/v1/telemetry/vehicles/{veh_a1_id}", headers=headers)
    assert res_v1.status_code == 200
    assert res_v1.json()["freshness"] == "LIVE"
    assert res_v1.json()["latest_telemetry"]["speed"] == 50.0

    res_v2 = c.get(f"/api/v1/telemetry/vehicles/{veh_a2_id}", headers=headers)
    assert res_v2.status_code == 200
    assert res_v2.json()["freshness"] == "STALE"

    # Fleet summary
    res_fleet = c.get("/api/v1/telemetry/fleet", headers=headers)
    assert res_fleet.status_code == 200
    data = res_fleet.json()
    assert data["total_vehicles"] == 2
    assert data["live_count"] == 1
    assert data["stale_count"] == 1
    assert data["offline_count"] == 0


def test_cross_tenant_telemetry_isolation(telemetry_setup):
    c = telemetry_setup["client"]
    headers_b = telemetry_setup["headers_b"]
    veh_a1_id = telemetry_setup["veh_a1"]["id"]

    # Org B user attempts to ingest telemetry for Org A's vehicle -> 403 Forbidden
    payload = {"vehicle_id": veh_a1_id, "latitude": 26.14, "longitude": 91.73, "speed": 30.0}
    res_ingest = c.post("/api/v1/telemetry", json=payload, headers=headers_b)
    assert res_ingest.status_code == 403

    # Org B user attempts to read telemetry of Org A's vehicle -> 403 Forbidden
    res_read = c.get(f"/api/v1/telemetry/vehicles/{veh_a1_id}", headers=headers_b)
    assert res_read.status_code == 403


def test_telemetry_health_endpoint(telemetry_setup):
    c = telemetry_setup["client"]
    res = c.get("/api/v1/telemetry/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert data["ingestion_available"] is True
