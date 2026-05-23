from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"
MODELS_DIR = PROJECT_ROOT / "models"
JOBS_DIR = PROJECT_ROOT / "jobs"

TEMPLATE_VIDEO = TEMPLATES_DIR / "basketball.mp4"
TEMPLATE_FRAMES_DIR = TEMPLATES_DIR / "basketball"

INSWAPPER_MODEL = MODELS_DIR / "inswapper_128.onnx"

JOB_TTL_SECONDS = 600                    # 10 min
PROCESSING_TIMEOUT_SECONDS = None        # no timeout
MIN_GAME_DURATION_SECONDS = 30           # mini-game minimum
SSE_PROGRESS_EVERY_N_FRAMES = 5
BATCH_SIZE = 4

WIPE_MARGIN_PX = 20
WIPE_WIDTH_RATIO = 0.25
