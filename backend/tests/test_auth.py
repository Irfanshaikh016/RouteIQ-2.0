"""
RouteIQ 2.0 - Phase 2 Authentication & User Security Tests
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.main import app
from app.repositories.store import get_store


@pytest.fixture
def client():
    # Fresh store state for clean isolation
    store = get_store()
    store.clear()
    return TestClient(app)


def test_password_hashing_and_verification():
    raw_password = "SecurePassword2026!"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_jwt_token_generation_and_decoding():
    token = create_access_token("user-uuid-1", "org-uuid-1", "admin")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-uuid-1"
    assert payload["org_id"] == "org-uuid-1"
    assert payload["role"] == "admin"


def test_user_registration_success(client):
    payload = {
        "email": "dispatcher@logistics-ner.in",
        "password": "DispatchPass2026!",
        "full_name": "Tenzing Norbu",
        "organization_name": "Himalayan Express Logistics",
        "role": "admin",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "dispatcher@logistics-ner.in"
    assert data["role"] == "admin"
    assert data["full_name"] == "Tenzing Norbu"
    assert "organization_id" in data


def test_registration_duplicate_email_rejected(client):
    payload = {
        "email": "duplicate@logistics-ner.in",
        "password": "DispatchPass2026!",
        "full_name": "Rahul Sharma",
        "organization_name": "Assam Cargo Lines",
    }
    first_res = client.post("/api/v1/auth/register", json=payload)
    assert first_res.status_code == 201

    second_res = client.post("/api/v1/auth/register", json=payload)
    assert second_res.status_code == 400
    assert "already exists" in second_res.json()["detail"].lower()


def test_login_success_and_failure(client):
    reg_payload = {
        "email": "driver@guwahatifleet.in",
        "password": "GuwahatiPass#123",
        "full_name": "Biren Das",
        "organization_name": "Brahmaputra Freight Lines",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Valid login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "driver@guwahatifleet.in", "password": "GuwahatiPass#123"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data

    # Invalid password (must not leak user existence)
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "driver@guwahatifleet.in", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401
    assert "invalid" in bad_login.json()["detail"].lower()


def test_authenticated_me_endpoint(client):
    reg_payload = {
        "email": "me_test@ner.in",
        "password": "TestPassword#2026",
        "full_name": "Ananya Barua",
        "organization_name": "Shillong Transit Hub",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "me_test@ner.in"
    assert me_data["full_name"] == "Ananya Barua"
    assert "password_hash" not in me_data  # Strict check: never leak password_hash


def test_unauthenticated_access_rejected(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
