from backend.config import (
    PROJECT_ROOT, TEMPLATES_DIR, MODELS_DIR, JOBS_DIR,
    JOB_TTL_SECONDS,
    TEMPLATE_VIDEO, TEMPLATE_FRAMES_DIR, GAME_VIDEO, INSWAPPER_MODEL,
)

def test_paths_are_project_relative():
    assert TEMPLATES_DIR == PROJECT_ROOT / "templates"
    assert MODELS_DIR == PROJECT_ROOT / "models"
    assert JOBS_DIR == PROJECT_ROOT / "jobs"

def test_template_video_is_target():
    assert TEMPLATE_VIDEO.name == "target.mp4"
    assert TEMPLATE_FRAMES_DIR == TEMPLATES_DIR / "target"

def test_game_video_is_shoot_3piece():
    assert GAME_VIDEO == TEMPLATES_DIR / "shoot_3piece.mp4"

def test_ttl_is_10_minutes():
    assert JOB_TTL_SECONDS == 600

def test_inswapper_model_filename():
    assert INSWAPPER_MODEL.name == "inswapper_128.onnx"
