from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    result_path: Optional[Path] = None
    created_at: float = field(default_factory=time.time)
    done_at: Optional[float] = None
    task: Optional[asyncio.Task] = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self) -> str:
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = Job(id=job_id)
        return job_id

    def get(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]

    def update_progress(self, job_id: str, progress: int, message: str = "") -> None:
        job = self.get(job_id)
        job.status = JobStatus.RUNNING
        job.progress = progress
        job.message = message

    def mark_done(self, job_id: str, result_path: Path) -> None:
        job = self.get(job_id)
        job.status = JobStatus.DONE
        job.progress = 100
        job.result_path = result_path
        job.done_at = time.time()

    def mark_failed(self, job_id: str, message: str) -> None:
        job = self.get(job_id)
        job.status = JobStatus.FAILED
        job.message = message
        job.done_at = time.time()

    def attach_task(self, job_id: str, task: asyncio.Task) -> None:
        self.get(job_id).task = task

    def all(self) -> list[Job]:
        return list(self._jobs.values())

    def remove(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
