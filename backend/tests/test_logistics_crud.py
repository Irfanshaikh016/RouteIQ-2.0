"""
RouteIQ 2.0 - Phase 2 Logistics CRUD & Validation Tests
Tests Vehicles, Locations, and Deliveries operations, constraints, and boundaries.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.store import get_store


@pytest.fixture
def client_and_auth():
    store = get_store()
    store.clear()
    c = TestClient(app)

    reg_payload = {
        "email": "ops@northeast-logistics.in",
        "password": "PasswordNER#2026",
        "full_name": "Lalit Kalita",
        "organization_name": "NER Mountain Freight",
        "role": "admin",
    }
    res = c.post("/api/v1/auth/register", json=reg_payload)
    data = res.json()
    token = data["access_token"]
    org_id = data["organization_id"]
    headers = {"Authorization": f"Bearer {token}"}
    return c, headers, org_id


# ------------------------------------------------------------------------------
# Vehicle Tests
# ------------------------------------------------------------------------------
def test_vehicle_crud_lifecycle(client_and_auth):
    client, headers, _ = client_and_auth

    # 1. Create Vehicle
    create_payload = {
        "vehicle_name": "Guwahati Heavy Hauler 1",
        "vehicle_type": "Heavy Commercial (16-Wheeler)",
        "registration_number": "AS-01-AB-1234",
        "capacity": 25000.0,
        "capacity_unit": "kg",
        "status": "available",
    }
    create_res = client.post("/api/v1/vehicles", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    veh_data = create_res.json()
    veh_id = veh_data["id"]
    assert veh_data["registration_number"] == "AS-01-AB-1234"
    assert veh_data["capacity"] == 25000.0

    # 2. Duplicate registration in same org rejected
    dup_res = client.post("/api/v1/vehicles", json=create_payload, headers=headers)
    assert dup_res.status_code == 400

    # 3. Read Vehicle
    get_res = client.get(f"/api/v1/vehicles/{veh_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["vehicle_name"] == "Guwahati Heavy Hauler 1"

    # 4. List Vehicles
    list_res = client.get("/api/v1/vehicles", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 5. Update Vehicle
    update_res = client.patch(
        f"/api/v1/vehicles/{veh_id}",
        json={"status": "maintenance", "capacity": 26000.0},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "maintenance"
    assert update_res.json()["capacity"] == 26000.0

    # 6. Delete Vehicle
    del_res = client.delete(f"/api/v1/vehicles/{veh_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify deleted
    verify_del = client.get(f"/api/v1/vehicles/{veh_id}", headers=headers)
    assert verify_del.status_code == 404


def test_vehicle_capacity_validation_negative(client_and_auth):
    client, headers, _ = client_and_auth
    invalid_payload = {
        "vehicle_name": "Invalid Capacity Truck",
        "vehicle_type": "Van",
        "registration_number": "ML-05-C-5555",
        "capacity": -100.0,  # Negative capacity must be rejected by Pydantic
    }
    res = client.post("/api/v1/vehicles", json=invalid_payload, headers=headers)
    assert res.status_code == 422


# ------------------------------------------------------------------------------
# Location Tests & Coordinate Bounds
# ------------------------------------------------------------------------------
def test_location_crud_and_coordinate_validation(client_and_auth):
    client, headers, _ = client_and_auth

    # 1. Valid location (Guwahati Inland Container Depot)
    loc_payload = {
        "name": "Guwahati ICD Hub",
        "address_line": "Amingaon Industrial Corridor",
        "city": "Guwahati",
        "state": "Assam",
        "postal_code": "781031",
        "latitude": 26.1824,
        "longitude": 91.6881,
    }
    res = client.post("/api/v1/locations", json=loc_payload, headers=headers)
    assert res.status_code == 201
    loc_data = res.json()
    loc_id = loc_data["id"]
    assert loc_data["city"] == "Guwahati"

    # 2. Latitude out of bounds (-90 to +90) rejected
    bad_lat = {**loc_payload, "name": "Invalid Lat", "latitude": 95.5}
    lat_res = client.post("/api/v1/locations", json=bad_lat, headers=headers)
    assert lat_res.status_code == 422

    # 3. Longitude out of bounds (-180 to +180) rejected
    bad_lon = {**loc_payload, "name": "Invalid Lon", "longitude": -190.0}
    lon_res = client.post("/api/v1/locations", json=bad_lon, headers=headers)
    assert lon_res.status_code == 422

    # 4. List Locations
    list_res = client.get("/api/v1/locations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


# ------------------------------------------------------------------------------
# Delivery Tests & Time Window Validation
# ------------------------------------------------------------------------------
def test_delivery_crud_and_time_window_validation(client_and_auth):
    client, headers, _ = client_and_auth

    # Seed Pickup Location (Shillong)
    pickup_res = client.post(
        "/api/v1/locations",
        json={
            "name": "Shillong Mountain Depot",
            "address_line": "Police Bazar Commercial Route",
            "city": "Shillong",
            "state": "Meghalaya",
            "postal_code": "793001",
            "latitude": 25.5788,
            "longitude": 91.8933,
        },
        headers=headers,
    )
    pickup_id = pickup_res.json()["id"]

    # Seed Delivery Destination Location (Silchar)
    dest_res = client.post(
        "/api/v1/locations",
        json={
            "name": "Silchar Valley Warehouse",
            "address_line": "Rangirkhari Junction",
            "city": "Silchar",
            "state": "Assam",
            "postal_code": "788005",
            "latitude": 24.8333,
            "longitude": 92.7789,
        },
        headers=headers,
    )
    dest_id = dest_res.json()["id"]

    # 1. Create Delivery with valid chronological window
    delivery_payload = {
        "reference_number": "ORD-SHL-SIL-001",
        "pickup_location_id": pickup_id,
        "delivery_location_id": dest_id,
        "priority": "high",
        "status": "pending",
        "package_weight": 4250.0,
        "package_volume": 12.5,
        "requested_delivery_date": "2026-09-20",
        "time_window_start": "2026-09-20T08:00:00Z",
        "time_window_end": "2026-09-20T18:00:00Z",
        "notes": "Essential medical cargo; avoid flooded gorge bypass.",
    }
    create_res = client.post("/api/v1/deliveries", json=delivery_payload, headers=headers)
    assert create_res.status_code == 201
    del_data = create_res.json()
    del_id = del_data["id"]
    assert del_data["reference_number"] == "ORD-SHL-SIL-001"
    assert del_data["priority"] == "high"

    # 2. Inverted time window (start > end) must be rejected
    inverted_window = {
        **delivery_payload,
        "reference_number": "ORD-INVERTED-002",
        "time_window_start": "2026-09-20T20:00:00Z",
        "time_window_end": "2026-09-20T08:00:00Z",
    }
    inv_res = client.post("/api/v1/deliveries", json=inverted_window, headers=headers)
    assert inv_res.status_code == 422

    # 3. Read Delivery
    get_res = client.get(f"/api/v1/deliveries/{del_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["package_weight"] == 4250.0

    # 4. Update Delivery Status
    patch_res = client.patch(
        f"/api/v1/deliveries/{del_id}",
        json={"status": "in_transit"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "in_transit"
