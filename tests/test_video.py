from pathlib import Path
from backend.video import extract_frames, FFMPEG_NOT_FOUND
from backend.config import TEMPLATE_VIDEO


def test_extract_frames_creates_files(tmp_path):
    out_dir = tmp_path / "frames"
    count = extract_frames(TEMPLATE_VIDEO, out_dir)
    assert count == 121
    assert (out_dir / "frame_000000.jpg").exists()
    assert (out_dir / "frame_000120.jpg").exists()


def test_compose_video_with_audio_and_wipe(tmp_path):
    from backend.video import compose_video
    from backend.config import TEMPLATE_VIDEO

    frames_dir = tmp_path / "frames"
    extract_frames(TEMPLATE_VIDEO, frames_dir)

    wipe_image = tmp_path / "wipe.jpg"
    import shutil
    shutil.copy(frames_dir / "frame_000000.jpg", wipe_image)

    output = tmp_path / "out.mp4"
    compose_video(
        frames_dir=frames_dir,
        audio_source=TEMPLATE_VIDEO,
        wipe_image=wipe_image,
        output=output,
        fps=24,
    )
    assert output.exists()
    import subprocess
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
        capture_output=True, text=True,
    )
    assert "audio" in info.stdout
