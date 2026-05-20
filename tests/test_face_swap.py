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
