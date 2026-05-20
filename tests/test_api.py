from pathlib import Path

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


async def test_swap_creates_job(client, tmp_path, monkeypatch):
    monkeypatch.setattr("backend.config.JOBS_DIR", tmp_path)
    monkeypatch.setattr("backend.main.JOBS_DIR", tmp_path)
    face_jpg = (Path(__file__).parent / "fixtures" / "test_face.jpg").read_bytes()
    res = await client.post(
        "/api/swap",
        files={"face": ("face.jpg", face_jpg, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    assert data["sse_url"].startswith("/api/job/")


async def test_job_not_found_returns_404(client):
    res = await client.get("/api/job/does-not-exist")
    assert res.status_code == 404
