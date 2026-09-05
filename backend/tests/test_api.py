"""
FastAPI Endpoints integration tests.
Verifies health, dashboard, revenue risk, policies, and agent permissions.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database.database import async_session, init_db
from app.simulation.data_generator import seed_initial_data
from main import app


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_test_db():
    await init_db()
    async with async_session() as db:
        await seed_initial_data(db)


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_dashboard_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "revenue_at_risk" in data
        assert "revenue_recovered" in data
        assert "recovery_rate" in data
        assert "active_cases" in data


@pytest.mark.asyncio
async def test_revenue_risk_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/revenue-risk?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "amount" in data[0]
            assert "recovery_type" in data[0]


@pytest.mark.asyncio
async def test_policies_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/policies")
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert len(data["policies"]) > 0


@pytest.mark.asyncio
async def test_agent_permissions_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/policies/permissions")
        assert response.status_code == 200
        data = response.json()
        assert "autonomous" in data
        assert "requires_approval" in data
        assert "never_allowed" in data
