from pathlib import Path
from backend.video import extract_frames, FFMPEG_NOT_FOUND
from backend.config import TEMPLATE_VIDEO


def test_extract_frames_creates_files(tmp_path):
    out_dir = tmp_path / "frames"
    count = extract_frames(TEMPLATE_VIDEO, out_dir)
    assert count == 121
    assert (out_dir / "frame_000000.jpg").exists()
    assert (out_dir / "frame_000120.jpg").exists()
