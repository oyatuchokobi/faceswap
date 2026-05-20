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
