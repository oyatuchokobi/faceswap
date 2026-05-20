import asyncio
import pytest
from backend.jobs import JobManager, JobStatus

@pytest.fixture
def manager():
    return JobManager()

async def test_create_job_returns_id(manager):
    job_id = manager.create()
    assert isinstance(job_id, str)
    assert len(job_id) >= 8

async def test_get_job_returns_pending(manager):
    job_id = manager.create()
    job = manager.get(job_id)
    assert job.status == JobStatus.PENDING
    assert job.progress == 0

async def test_update_progress(manager):
    job_id = manager.create()
    manager.update_progress(job_id, 50, "swapping frames")
    job = manager.get(job_id)
    assert job.progress == 50
    assert job.message == "swapping frames"

async def test_mark_done_sets_result_path(manager, tmp_path):
    job_id = manager.create()
    result = tmp_path / "result.mp4"
    result.write_bytes(b"fake")
    manager.mark_done(job_id, result)
    job = manager.get(job_id)
    assert job.status == JobStatus.DONE
    assert job.result_path == result

async def test_mark_failed_with_message(manager):
    job_id = manager.create()
    manager.mark_failed(job_id, "no face detected")
    job = manager.get(job_id)
    assert job.status == JobStatus.FAILED
    assert "no face" in job.message

async def test_get_nonexistent_raises(manager):
    with pytest.raises(KeyError):
        manager.get("does-not-exist")
