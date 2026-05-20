from __future__ import annotations
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import cv2

import backend.config as config
from backend.video import extract_frames
from backend.face_swap import detect_all_faces, get_face_app

logger = logging.getLogger(__name__)


@dataclass
class TemplateData:
    frame_count: int
    faces_per_frame: list


_cache: TemplateData | None = None


def prepare_templates() -> TemplateData:
    global _cache
    if _cache is not None:
        return _cache

    frames_dir: Path = config.TEMPLATE_FRAMES_DIR
    cache_file: Path = frames_dir / "faces_cache.pkl"

    needs_extract = not frames_dir.exists() or not list(frames_dir.glob("frame_*.jpg"))
    if needs_extract:
        logger.info("Extracting template frames...")
        extract_frames(config.TEMPLATE_VIDEO, frames_dir)

    frame_files = sorted(frames_dir.glob("frame_*.jpg"))
    frame_count = len(frame_files)

    if cache_file.exists():
        logger.info("Loading cached template faces")
        with open(cache_file, "rb") as f:
            faces_per_frame = pickle.load(f)
    else:
        logger.info("Detecting faces in %d template frames", frame_count)
        get_face_app()
        faces_per_frame = []
        for i, frame_file in enumerate(frame_files):
            img = cv2.imread(str(frame_file))
            faces_per_frame.append(detect_all_faces(img))
            if (i + 1) % 20 == 0:
                logger.info("  ... %d / %d", i + 1, frame_count)
        with open(cache_file, "wb") as f:
            pickle.dump(faces_per_frame, f)

    _cache = TemplateData(frame_count=frame_count, faces_per_frame=faces_per_frame)
    return _cache
