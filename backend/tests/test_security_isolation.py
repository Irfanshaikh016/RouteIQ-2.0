"""
RouteIQ 2.0 - Phase 2 Cross-Organization Tenant Isolation Security Tests
CRITICAL SECURITY VERIFICATION:
Guarantees that a user from Organization A CANNOT inspect, modify, delete,
or reference assets belonging to Organization B.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.store import get_store


@pytest.fixture
def two_tenants_client():
    store = get_store()
    store.clear()
    c = TestClient(app)

    # 1. Register User in Organization A (Assam Transport Corp)
    reg_a = c.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@assam-transport.in",
            "password": "AssamPassword#2026",
            "full_name": "Dipankar Barman",
            "organization_name": "Assam Transport Corporation",
            "role": "admin",
        },
    )
    data_a = reg_a.json()
    token_a = data_a["access_token"]
    org_a_id = data_a["organization_id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User in Organization B (Meghalaya Hill Logistics)
    reg_b = c.post(
        "/api/v1/auth/register",
        json={
            "email": "manager@meghalaya-logistics.in",
            "password": "MeghalayaPass#2026",
            "full_name": "Wanshan Marbaniang",
            "organization_name": "Meghalaya Hill Logistics",
            "role": "manager",
        },
    )
    data_b = reg_b.json()
    token_b = data_b["access_token"]
    org_b_id = data_b["organization_id"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    return c, headers_a, org_a_id, headers_b, org_b_id


def test_cross_organization_vehicle_isolation(two_tenants_client):
    client, headers_a, _, headers_b, _ = two_tenants_client

    # User A creates Vehicle in Org A
    v_a = client.post(
        "/api/v1/vehicles",
        json={
            "vehicle_name": "Org A Fleet Truck",
            "vehicle_type": "Truck",
            "registration_number": "AS-01-ORG-A",
            "capacity": 15000.0,
        },
        headers=headers_a,
    ).json()
    vehicle_a_id = v_a["id"]

    # User B creates Vehicle in Org B
    v_b = client.post(
        "/api/v1/vehicles",
        json={
            "vehicle_name": "Org B Fleet Van",
            "vehicle_type": "Van",
            "registration_number": "ML-01-ORG-B",
            "capacity": 3500.0,
        },
        headers=headers_b,
    ).json()
    vehicle_b_id = v_b["id"]

    # 1. User B cannot GET Vehicle A
    get_res = client.get(f"/api/v1/vehicles/{vehicle_a_id}", headers=headers_b)
    assert get_res.status_code == 404

    # 2. User B cannot PATCH Vehicle A
    patch_res = client.patch(
        f"/api/v1/vehicles/{vehicle_a_id}",
        json={"vehicle_name": "Hacked Vehicle Name"},
        headers=headers_b,
    )
    assert patch_res.status_code == 404

    # 3. User B cannot DELETE Vehicle A
    del_res = client.delete(f"/api/v1/vehicles/{vehicle_a_id}", headers=headers_b)
    assert del_res.status_code == 404

    # 4. User A listing vehicles sees only Vehicle A
    list_a = client.get("/api/v1/vehicles", headers=headers_a).json()
    assert len(list_a) == 1
    assert list_a[0]["id"] == vehicle_a_id

    # 5. User B listing vehicles sees only Vehicle B
    list_b = client.get("/api/v1/vehicles", headers=headers_b).json()
    assert len(list_b) == 1
    assert list_b[0]["id"] == vehicle_b_id


def test_cross_organization_location_and_delivery_isolation(two_tenants_client):
    client, headers_a, _, headers_b, _ = two_tenants_client

    # User A creates locations in Org A
    loc_a1 = client.post(
        "/api/v1/locations",
        json={
            "name": "Org A Depot 1",
            "city": "Guwahati",
            "state": "Assam",
            "latitude": 26.1445,
            "longitude": 91.7362,
        },
        headers=headers_a,
    ).json()

    loc_a2 = client.post(
        "/api/v1/locations",
        json={
            "name": "Org A Depot 2",
            "city": "Jorhat",
            "state": "Assam",
            "latitude": 26.7509,
            "longitude": 94.2037,
        },
        headers=headers_a,
    ).json()

    # User A creates delivery in Org A
    del_a = client.post(
        "/api/v1/deliveries",
        json={
            "reference_number": "DEL-ORG-A-001",
            "pickup_location_id": loc_a1["id"],
            "delivery_location_id": loc_a2["id"],
            "priority": "normal",
        },
        headers=headers_a,
    ).json()
    delivery_a_id = del_a["id"]

    # 1. User B cannot GET Location A1
    assert client.get(f"/api/v1/locations/{loc_a1['id']}", headers=headers_b).status_code == 404

    # 2. User B cannot PATCH Location A1
    assert client.patch(
        f"/api/v1/locations/{loc_a1['id']}",
        json={"name": "Hacked Location"},
        headers=headers_b,
    ).status_code == 404

    # 3. User B cannot DELETE Location A1
    assert client.delete(f"/api/v1/locations/{loc_a1['id']}", headers=headers_b).status_code == 404

    # 4. User B cannot GET Delivery A
    assert client.get(f"/api/v1/deliveries/{delivery_a_id}", headers=headers_b).status_code == 404

    # 5. User B cannot PATCH Delivery A
    assert client.patch(
        f"/api/v1/deliveries/{delivery_a_id}",
        json={"priority": "urgent"},
        headers=headers_b,
    ).status_code == 404

    # 6. User B cannot DELETE Delivery A
    assert client.delete(f"/api/v1/deliveries/{delivery_a_id}", headers=headers_b).status_code == 404

    # 7. User B CANNOT create a delivery using User A's locations!
    b_cross_delivery = client.post(
        "/api/v1/deliveries",
        json={
            "reference_number": "DEL-ILLEGAL-REF",
            "pickup_location_id": loc_a1["id"],  # Belongs to Org A!
            "delivery_location_id": loc_a2["id"],  # Belongs to Org A!
            "priority": "high",
        },
        headers=headers_b,
    )
    assert b_cross_delivery.status_code == 400
    assert "not found in your organization" in b_cross_delivery.json()["detail"].lower()
