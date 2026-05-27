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


async def test_result_streams_video(client, tmp_path, monkeypatch):
    from backend.main import job_manager
    monkeypatch.setattr("backend.config.JOBS_DIR", tmp_path)
    job_id = job_manager.create()
    job_dir = tmp_path / job_id
    job_dir.mkdir()
    fake_mp4 = job_dir / "result.mp4"
    fake_mp4.write_bytes(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 200)
    job_manager.mark_done(job_id, fake_mp4)

    res = await client.get(f"/api/result/{job_id}.mp4")
    assert res.status_code == 200
    assert res.headers["content-type"] == "video/mp4"

    res2 = await client.get(f"/api/download/{job_id}.mp4")
    assert res2.status_code == 200
    assert "attachment" in res2.headers.get("content-disposition", "")


async def test_template_video_endpoint(client):
    res = await client.get("/api/videos/template")
    assert res.status_code == 200
    assert res.headers["content-type"] == "video/mp4"


async def test_game_video_endpoint(client):
    res = await client.get("/api/videos/game")
    assert res.status_code == 200
    assert res.headers["content-type"] == "video/mp4"


async def test_basketball_endpoint_removed(client):
    res = await client.get("/static/basketball.mp4")
    assert res.status_code == 404
