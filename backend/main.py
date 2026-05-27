from __future__ import annotations
import asyncio
import json
import logging
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from backend.config import (
    GAME_VIDEO,
    JOB_TTL_SECONDS,
    JOBS_DIR,
    PROCESSING_TIMEOUT_SECONDS,
    PROJECT_ROOT,
    TEMPLATE_FRAMES_DIR,
    TEMPLATE_VIDEO,
)
from backend.face_swap import FaceNotFoundError, preload as preload_models, swap_video_job
from backend.jobs import JobManager, JobStatus
from backend.templates_init import prepare_templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Preloading models and templates...")
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    preload_models()
    prepare_templates()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down")


app = FastAPI(title="FaceSwap Demo", lifespan=lifespan)

FRONTEND_DIR = PROJECT_ROOT / "frontend"

job_manager = JobManager()


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


_VIDEO_ROUTES = {
    "template": TEMPLATE_VIDEO,
    "game": GAME_VIDEO,
}


@app.get("/api/videos/{name}")
async def serve_video(name: str):
    path = _VIDEO_ROUTES.get(name)
    if path is None:
        raise HTTPException(404, "Video not found")
    return FileResponse(path, media_type="video/mp4")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/swap")
async def create_swap(face: UploadFile = File(...)):
    job_id = job_manager.create()
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    face_path = job_dir / "face.jpg"

    contents = await face.read()
    async with aiofiles.open(face_path, "wb") as f:
        await f.write(contents)

    result_path = job_dir / "result.mp4"

    async def run() -> None:
        def progress(pct: int, msg: str) -> None:
            job_manager.update_progress(job_id, pct, msg)
        try:
            await asyncio.wait_for(
                swap_video_job(
                    src_face_image_path=str(face_path),
                    template_frames_dir=TEMPLATE_FRAMES_DIR,
                    output=result_path,
                    progress=progress,
                ),
                timeout=PROCESSING_TIMEOUT_SECONDS,
            )
            job_manager.mark_done(job_id, result_path)
            asyncio.create_task(_cleanup_after(job_id, JOB_TTL_SECONDS))
        except FaceNotFoundError as e:
            job_manager.mark_failed(job_id, f"顔が検出できません: {e}")
        except asyncio.TimeoutError:
            job_manager.mark_failed(job_id, "処理がタイムアウトしました")
        except Exception as e:
            logger.exception("Job %s failed", job_id)
            job_manager.mark_failed(job_id, f"内部エラー: {type(e).__name__}")

    task = asyncio.create_task(run())
    job_manager.attach_task(job_id, task)

    return {"job_id": job_id, "sse_url": f"/api/job/{job_id}"}


async def _cleanup_after(job_id: str, delay: int) -> None:
    await asyncio.sleep(delay)
    job_dir = JOBS_DIR / job_id
    shutil.rmtree(job_dir, ignore_errors=True)
    job_manager.remove(job_id)
    logger.info("Cleaned up job %s", job_id)


@app.get("/api/job/{job_id}")
async def job_sse(job_id: str):
    try:
        job_manager.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        last_emit = (-1, "")
        while True:
            try:
                job = job_manager.get(job_id)
            except KeyError:
                yield {"event": "removed", "data": "job removed"}
                return

            current = (job.progress, job.message)
            if current != last_emit:
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "progress": job.progress,
                        "message": job.message,
                        "status": job.status.value,
                    }),
                }
                last_emit = current

            if job.status in (JobStatus.DONE, JobStatus.FAILED):
                yield {
                    "event": job.status.value,
                    "data": json.dumps({
                        "status": job.status.value,
                        "message": job.message,
                    }),
                }
                return
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_stream())


@app.get("/api/result/{job_id}.mp4")
async def get_result(job_id: str):
    try:
        job = job_manager.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DONE or not job.result_path or not job.result_path.exists():
        raise HTTPException(404, "Result not ready")
    return FileResponse(job.result_path, media_type="video/mp4")


@app.get("/api/download/{job_id}.mp4")
async def download_result(job_id: str):
    try:
        job = job_manager.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DONE or not job.result_path or not job.result_path.exists():
        raise HTTPException(404, "Result not ready")
    return FileResponse(
        job.result_path,
        media_type="video/mp4",
        filename=f"faceswap_{job_id}.mp4",
        headers={"Content-Disposition": f'attachment; filename="faceswap_{job_id}.mp4"'},
    )


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
