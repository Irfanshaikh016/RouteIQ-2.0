"""
RouteIQ 2.0 - Backend Health & Foundation Tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import check_database_health


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    """Verifies root endpoint returns 200 and platform metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "RouteIQ 2.0" in data["service"]
    assert data["status"] == "operational"
    assert "health" in data


def test_direct_health_endpoint(client):
    """Verifies GET /health returns HTTP 200 with required structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "RouteIQ 2.0" in data["service"]
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "database" in data
    assert isinstance(data["database"], dict)


def test_versioned_health_endpoint(client):
    """Verifies GET /api/v1/health returns HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


@pytest.mark.asyncio
async def test_database_health_check_resilience():
    """Verifies that database health check function returns clean diagnostic dict without crashing."""
    health = await check_database_health()
    assert isinstance(health, dict)
    assert "configured" in health
    assert "primary" in health


def test_cors_headers_present(client):
    """Verifies CORS headers are returned properly for allowed origin."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_openapi_docs_endpoint(client):
    """Verifies OpenAPI schema is served with Phase 1 endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "/health" in schema["paths"]
    assert "/api/v1/health" in schema["paths"]
    assert schema["info"]["title"] == "RouteIQ 2.0 API"

