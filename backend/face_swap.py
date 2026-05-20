from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

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


_swapper = None


def get_swapper():
    global _swapper
    if _swapper is None:
        providers = select_providers()
        _swapper = get_model(str(INSWAPPER_MODEL), providers=providers)
    return _swapper


def swap_face(target_image: np.ndarray, target_face, source_face) -> np.ndarray:
    """Swap target_face in target_image with source_face's identity."""
    swapper = get_swapper()
    result = swapper.get(target_image, target_face, source_face, paste_back=True)
    return result


def preload() -> None:
    """Pre-warm face detector and swapper at server startup."""
    get_face_app()
    get_swapper()
    logger.info("FaceSwap models preloaded")
