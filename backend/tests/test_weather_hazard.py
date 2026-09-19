"""
RouteIQ 2.0 - Weather, Hazard & Road Restriction Tests (Phase 6)
Tests dynamic weather observation tracking, hazard event lifecycle with TTL/expiry,
and road restriction status (OPEN, SLOW, RESTRICTED, CLOSED).
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, hash_password
from app.repositories.store import get_store
from app.weather.schemas import RoadRestrictionStatus


@pytest.fixture
def weather_setup():
    store = get_store()
    store.clear()

    org = store.create_organization(name="Brahmaputra Logistics")
    user = store.create_user(
        organization_id=org["id"],
        email="manager@brahmaputra.in",
        password_hash=hash_password("SecurePass#2026"),
        full_name="Operations Manager",
        role="manager",
    )
    token = create_access_token(subject=user["id"], org_id=org["id"], role="manager")

    return {
        "client": TestClient(app),
        "headers": {"Authorization": f"Bearer {token}"},
        "org": org,
        "user": user,
    }


def test_weather_health_endpoint(weather_setup):
    c = weather_setup["client"]
    res = c.get("/api/v1/weather/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert data["provider"] == "StaticWeatherProvider"
    assert "active_hazards_count" in data
    assert "active_restrictions_count" in data


def test_weather_current_observation(weather_setup):
    c = weather_setup["client"]
    headers = weather_setup["headers"]

    # Query current weather at Guwahati coordinates
    res = c.get("/api/v1/weather/current?latitude=26.1445&longitude=91.7362", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["latitude"] == 26.1445
    assert data["longitude"] == 91.7362
    assert "rainfall_mm" in data
    assert "temperature_c" in data
    assert data["source"] in ("STATIC_PROVIDER", "STATIC_FIXTURE", "SIMULATED_TEST")


def test_hazard_event_lifecycle_and_ttl_expiry(weather_setup):
    c = weather_setup["client"]
    headers = weather_setup["headers"]

    now = datetime.now(timezone.utc)
    # 1. Active hazard (expires in 2 hours)
    active_payload = {
        "hazard_type": "landslide",
        "severity": 0.85,
        "latitude": 25.5788,
        "longitude": 91.8933,
        "radius_meters": 5000.0,
        "description": "Active rockfall on NH-6 bypass",
        "starts_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=2)).isoformat(),
        "source": "MODELED_HEURISTIC",
    }
    res_active = c.post("/api/v1/weather/hazards", json=active_payload, headers=headers)
    assert res_active.status_code == 201
    active_hazard = res_active.json()
    assert active_hazard["hazard_type"] == "landslide"
    assert active_hazard["severity"] == 0.85
    assert active_hazard["is_active"] is True

    # 2. Expired hazard (expired 30 minutes ago)
    expired_payload = {
        "hazard_type": "flood",
        "severity": 0.6,
        "latitude": 26.1445,
        "longitude": 91.7362,
        "radius_meters": 3000.0,
        "description": "Cleared waterlogging",
        "starts_at": (now - timedelta(hours=2)).isoformat(),
        "expires_at": (now - timedelta(minutes=30)).isoformat(),
        "source": "MODELED_HEURISTIC",
    }
    res_expired = c.post("/api/v1/weather/hazards", json=expired_payload, headers=headers)
    assert res_expired.status_code == 201

    # Query active hazards - should only return the unexpired landslide
    res_query = c.get("/api/v1/weather/hazards", headers=headers)
    assert res_query.status_code == 200
    hazards = res_query.json()
    assert len(hazards) == 1
    assert hazards[0]["hazard_type"] == "landslide"
    assert hazards[0]["description"] == "Active rockfall on NH-6 bypass"


def test_road_restrictions_lifecycle(weather_setup):
    c = weather_setup["client"]
    headers = weather_setup["headers"]

    now = datetime.now(timezone.utc)
    restriction_payload = {
        "road_edge_id": "NH-6-SHILLONG-01",
        "road_name": "NH-6 Shillong Bypass",
        "status": "CLOSED",
        "speed_multiplier": 0.0,
        "reason": "Massive landslide blocking both lanes",
        "starts_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=6)).isoformat(),
    }
    res = c.post("/api/v1/weather/restrictions", json=restriction_payload, headers=headers)
    assert res.status_code == 201
    created = res.json()
    assert created["road_edge_id"] == "NH-6-SHILLONG-01"
    assert created["status"] == "CLOSED"
    assert created["speed_multiplier"] == 0.0

    # List active restrictions
    res_list = c.get("/api/v1/weather/restrictions", headers=headers)
    assert res_list.status_code == 200
    restr_list = res_list.json()
    assert len(restr_list) == 1
    assert restr_list[0]["road_edge_id"] == "NH-6-SHILLONG-01"
    assert restr_list[0]["status"] == "CLOSED"

    # Impose a SLOW restriction on another edge
    slow_payload = {
        "road_edge_id": "GS-ROAD-02",
        "road_name": "GS Road Khanapara",
        "status": "SLOW",
        "speed_multiplier": 0.4,
        "reason": "Single lane traffic due to water accumulation",
        "starts_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=3)).isoformat(),
    }
    res_slow = c.post("/api/v1/weather/restrictions", json=slow_payload, headers=headers)
    assert res_slow.status_code == 201
    assert res_slow.json()["status"] == "SLOW"
    assert res_slow.json()["speed_multiplier"] == 0.4
