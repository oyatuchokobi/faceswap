from pathlib import Path
from backend.config import (
    PROJECT_ROOT, TEMPLATES_DIR, MODELS_DIR, JOBS_DIR,
    JOB_TTL_SECONDS, PROCESSING_TIMEOUT_SECONDS,
    TEMPLATE_VIDEO, INSWAPPER_MODEL,
)

def test_paths_are_project_relative():
    assert TEMPLATES_DIR == PROJECT_ROOT / "templates"
    assert MODELS_DIR == PROJECT_ROOT / "models"
    assert JOBS_DIR == PROJECT_ROOT / "jobs"

def test_template_video_exists():
    assert TEMPLATE_VIDEO.name == "basketball.mp4"

def test_ttl_is_10_minutes():
    assert JOB_TTL_SECONDS == 600

def test_processing_timeout_is_120():
    assert PROCESSING_TIMEOUT_SECONDS == 120

def test_inswapper_model_filename():
    assert INSWAPPER_MODEL.name == "inswapper_128.onnx"
