from __future__ import annotations
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegError(RuntimeError):
    pass


FFMPEG_NOT_FOUND = "ffmpeg binary not found on PATH"


def _ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise FFmpegError(FFMPEG_NOT_FOUND)
    return path


def extract_frames(video_path: Path, out_dir: Path) -> int:
    """Extract all frames as JPEG to out_dir. Return frame count."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "frame_%06d.jpg"
    cmd = [
        _ffmpeg_bin(),
        "-y",
        "-i", str(video_path),
        "-start_number", "0",
        "-qscale:v", "2",
        str(pattern),
    ]
    logger.info("Extracting frames: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(f"ffmpeg failed: {result.stderr}")
    return len(list(out_dir.glob("frame_*.jpg")))
