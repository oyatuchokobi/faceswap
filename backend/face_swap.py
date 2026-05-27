from __future__ import annotations
import asyncio
import logging
import shutil
import threading
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

from backend.config import (
    INSWAPPER_MODEL,
    TEMPLATE_VIDEO,
    SSE_PROGRESS_EVERY_N_FRAMES,
)
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


def _face_area(face) -> float:
    return (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1])


def detect_largest_face(image: np.ndarray):
    """Return the largest face in the image, or raise FaceNotFoundError."""
    app = get_face_app()
    faces = app.get(image)
    if not faces:
        raise FaceNotFoundError("No face detected")
    return max(faces, key=_face_area)


def detect_all_faces(image: np.ndarray) -> list:
    app = get_face_app()
    return app.get(image)


_swapper = None
_swapper_lock = threading.Lock()


def get_swapper():
    global _swapper
    if _swapper is None:
        with _swapper_lock:
            if _swapper is None:
                providers = select_providers()
                _swapper = get_model(str(INSWAPPER_MODEL), providers=providers)
    return _swapper


def swap_face(target_image: np.ndarray, target_face, source_face) -> np.ndarray:
    """Swap target_face in target_image with source_face's identity."""
    swapper = get_swapper()
    return swapper.get(target_image, target_face, source_face, paste_back=True)


def preload() -> None:
    """Pre-warm face detector and swapper at server startup."""
    get_face_app()
    get_swapper()
    logger.info("FaceSwap models preloaded")


ProgressCallback = Callable[[int, str], None]


async def swap_video_job(
    src_face_image_path: str,
    template_frames_dir: Path,
    output: Path,
    progress: ProgressCallback,
) -> None:
    """Run the full swap pipeline. Updates progress 0-100."""
    from backend.templates_init import prepare_templates
    from backend.video import compose_video

    progress(0, "顔を解析中...")

    # 1. Source face embedding
    src_img = cv2.imread(src_face_image_path)
    if src_img is None:
        raise FaceNotFoundError("Source image could not be loaded")
    src_face = await asyncio.to_thread(detect_largest_face, src_img)
    progress(5, "顔の特徴を抽出しました")

    # 2. Template data (cached)
    tpl = await asyncio.to_thread(prepare_templates)
    frame_files = sorted(template_frames_dir.glob("frame_*.jpg"))
    n_frames = len(frame_files)

    # 3. Per-frame swap
    swapped_dir = output.parent / "swapped_frames"
    swapped_dir.mkdir(parents=True, exist_ok=True)

    for i, frame_file in enumerate(frame_files):
        img = cv2.imread(str(frame_file))
        faces = tpl.faces_per_frame[i]
        if faces:
            target_face = max(faces, key=_face_area)
            img = await asyncio.to_thread(swap_face, img, target_face, src_face)
        out_path = swapped_dir / frame_file.name
        cv2.imwrite(str(out_path), img)
        if (i + 1) % SSE_PROGRESS_EVERY_N_FRAMES == 0:
            pct = 5 + int(85 * (i + 1) / n_frames)
            progress(pct, f"神プレイに変身中... {i+1}/{n_frames}")

    progress(90, "動画を仕上げ中...")

    # 4. Compose final video with audio + wipe
    await asyncio.to_thread(
        compose_video,
        swapped_dir,
        TEMPLATE_VIDEO,
        Path(src_face_image_path),
        output,
        24,
    )

    # 5. Cleanup intermediate
    shutil.rmtree(swapped_dir, ignore_errors=True)
    progress(100, "完成!")
