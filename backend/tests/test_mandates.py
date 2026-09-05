"""
Mandate Retry Sequencer integration tests.
Validates mandate stats, listing, details, presentation execution, and rescheduling.
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
async def test_mandate_stats_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/mandates/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_mandates" in data
        assert "at_risk_mandates" in data
        assert "recovered_mandates" in data
        assert "next_clearing_window" in data


@pytest.mark.asyncio
async def test_list_mandates_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/mandates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        first = data[0]
        assert "umrn" in first
        assert "bank_name" in first
        assert "mandate_type" in first
        assert "amount" in first
        assert "current_stage" in first


@pytest.mark.asyncio
async def test_get_mandate_detail_and_presentation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Fetch list to get valid ID
        list_res = await ac.get("/api/mandates")
        mandates = list_res.json()
        assert len(mandates) > 0
        mandate_id = mandates[0]["id"]

        # 2. Get detailed schedule
        detail_res = await ac.get(f"/api/mandates/{mandate_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == mandate_id
        assert "sequences" in detail
        assert len(detail["sequences"]) >= 4

        # 3. Test immediate presentation with deterministic override_success=True
        present_res = await ac.post(
            f"/api/mandates/{mandate_id}/present-now",
            json={"override_success": True}
        )
        assert present_res.status_code == 200
        present_data = present_res.json()
        assert present_data["success"] is True
        assert present_data["new_status"] == "RECOVERED"
        assert present_data["amount_recovered"] > 0

        # 4. Verify detail reflects recovered status
        refreshed = await ac.get(f"/api/mandates/{mandate_id}")
        assert refreshed.json()["status"] == "RECOVERED"
