import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Test GET /api/v1/health returns healthy and database connected."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test GET / returns basic metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Blood Connect API"
    assert data["health"] == "/api/v1/health"
    assert data["documentation"] == "/docs"
