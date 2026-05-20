import cv2
import pytest
from pathlib import Path
from backend.face_swap import detect_largest_face, FaceNotFoundError

FIXTURES = Path(__file__).parent / "fixtures"


def test_detect_face_in_face_image():
    img = cv2.imread(str(FIXTURES / "test_face.jpg"))
    face = detect_largest_face(img)
    assert face is not None
    assert face.normed_embedding.shape == (512,)

def test_detect_returns_none_for_no_face():
    img = cv2.imread(str(FIXTURES / "test_no_face.jpg"))
    with pytest.raises(FaceNotFoundError):
        detect_largest_face(img)


def test_swap_face_returns_modified_image():
    from backend.face_swap import detect_largest_face, swap_face
    src_img = cv2.imread(str(FIXTURES / "test_face.jpg"))
    tgt_img = cv2.imread(str(FIXTURES / "test_face.jpg"))
    src_face = detect_largest_face(src_img)
    tgt_face = detect_largest_face(tgt_img)
    result = swap_face(tgt_img, tgt_face, src_face)
    assert result.shape == tgt_img.shape
    assert result.dtype == tgt_img.dtype


async def test_swap_video_end_to_end(tmp_path):
    from backend.face_swap import swap_video_job
    from backend.templates_init import prepare_templates
    from backend.config import TEMPLATE_FRAMES_DIR

    prepare_templates()
    src_face_img = str(FIXTURES / "test_face.jpg")
    output = tmp_path / "result.mp4"

    progress_log = []
    def cb(pct, msg):
        progress_log.append((pct, msg))

    await swap_video_job(
        src_face_image_path=src_face_img,
        template_frames_dir=TEMPLATE_FRAMES_DIR,
        output=output,
        progress=cb,
    )
    assert output.exists()
    assert progress_log[-1][0] == 100
