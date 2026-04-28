"""Integration tests for the REST API."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.infrastructure.api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
class TestAPI:
    """Integration tests for all API endpoints."""

    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "alive"}

    async def test_step(self, client: AsyncClient) -> None:
        resp = await client.get("/step")
        assert resp.status_code == 200
        data = resp.json()
        assert "tick" in data
        assert "agents" in data
        assert "traffic_lights" in data

    async def test_state(self, client: AsyncClient) -> None:
        resp = await client.get("/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "tick" in data
        assert "grid_width" in data

    async def test_reset(self, client: AsyncClient) -> None:
        # Step a few times first
        await client.get("/step")
        await client.get("/step")

        resp = await client.post("/reset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tick"] == 0

    async def test_stats(self, client: AsyncClient) -> None:
        resp = await client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "tick" in data
        assert "active_cars" in data
        assert "active_pedestrians" in data
        assert "parked_cars" in data

    async def test_config(self, client: AsyncClient) -> None:
        resp = await client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["grid_width"] == 30
        assert data["grid_height"] == 30
        assert "max_cars" in data
        assert "building_count" in data

    async def test_step_increments_tick(self, client: AsyncClient) -> None:
        await client.post("/reset")
        r1 = await client.get("/step")
        r2 = await client.get("/step")
        assert r2.json()["tick"] > r1.json()["tick"]
