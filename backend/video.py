from __future__ import annotations
import logging
import shutil
import subprocess
from pathlib import Path

from backend.config import WIPE_MARGIN_PX, WIPE_WIDTH_RATIO

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


def _get_video_width(video_path: Path) -> int:
    result = subprocess.run(
        [shutil.which("ffprobe") or "ffprobe",
         "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=width",
         "-of", "csv=p=0",
         str(video_path)],
        capture_output=True, text=True,
    )
    return int(result.stdout.strip())


def compose_video(
    frames_dir: Path,
    audio_source: Path,
    wipe_image: Path,
    output: Path,
    fps: int = 24,
) -> None:
    """
    Combine swapped frames + original audio + wipe overlay in ONE ffmpeg invocation.

    Layout:
      [main video stream from frames_dir/frame_*.jpg]
      [wipe overlay scaled to WIPE_WIDTH_RATIO of main video width, positioned bottom-right]
      [audio from audio_source]
    """
    margin = WIPE_MARGIN_PX

    # Compute wipe pixel width relative to the main video (not the wipe image itself)
    main_w = _get_video_width(audio_source)
    wipe_w = int(main_w * WIPE_WIDTH_RATIO)
    wipe_w = wipe_w - (wipe_w % 2)  # must be even for yuv420p

    # Check whether audio_source contains an audio stream
    probe = subprocess.run(
        [shutil.which("ffprobe") or "ffprobe",
         "-v", "error",
         "-select_streams", "a",
         "-show_entries", "stream=codec_type",
         "-of", "csv=p=0",
         str(audio_source)],
        capture_output=True, text=True,
    )
    has_audio = bool(probe.stdout.strip())

    if has_audio:
        filter_complex = (
            f"[1:v]scale={wipe_w}:-2[wipe];"
            f"[0:v][wipe]overlay=W-w-{margin}:H-h-{margin}[v]"
        )
        audio_map = ["2:a"]
    else:
        filter_complex = (
            f"[1:v]scale={wipe_w}:-2[wipe];"
            f"[0:v][wipe]overlay=W-w-{margin}:H-h-{margin}[v];"
            f"anullsrc=r=44100:cl=stereo[a]"
        )
        audio_map = ["[a]"]

    cmd = [
        _ffmpeg_bin(),
        "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%06d.jpg"),
        "-i", str(wipe_image),
        "-i", str(audio_source),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", *audio_map,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output),
    ]
    logger.info("Composing video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(f"ffmpeg compose failed: {result.stderr}")
