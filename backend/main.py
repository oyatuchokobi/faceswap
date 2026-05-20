from __future__ import annotations
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_ROOT
from backend.jobs import JobManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FaceSwap Demo")

FRONTEND_DIR = PROJECT_ROOT / "frontend"

job_manager = JobManager()


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
