from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from insightface.app import FaceAnalysis

from backend.config import INSWAPPER_MODEL
from backend.ep_selector import select_providers

logger = logging.getLogger(__name__)


class FaceNotFoundError(ValueError):
    pass


_face_app: Optional[FaceAnalysis] = None


def get_face_app() -> FaceAnalysis:
    global _face_app
    if _face_app is None:
        providers = select_providers()
        app = FaceAnalysis(name="buffalo_l", providers=providers)
        app.prepare(ctx_id=0, det_size=(640, 640))
        _face_app = app
    return _face_app


def detect_largest_face(image: np.ndarray):
    """Return the largest face in the image, or raise FaceNotFoundError."""
    app = get_face_app()
    faces = app.get(image)
    if not faces:
        raise FaceNotFoundError("No face detected")
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0]


def detect_all_faces(image: np.ndarray) -> list:
    app = get_face_app()
    return app.get(image)
