import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_root_returns_html(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


async def test_healthcheck(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
