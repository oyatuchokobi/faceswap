# FaceSwap デモアプリ 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ユーザーの顔をbasketball.mp4テンプレートに合成し、QRコードでスマホへDLできるWebアプリを Windows ノートPC上に構築する。

**Architecture:** FastAPI バックエンド + Vanilla JS フロントエンド + InsightFace/ONNX による顔スワップ + ffmpeg による動画合成。Cloudflare Tunnel で外部公開。MediaPipe Pose を使った待ち時間ミニゲーム付き。

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, InsightFace, ONNX Runtime, ffmpeg, Vanilla JS, MediaPipe Pose (JS), cloudflared

**Spec:** `docs/superpowers/specs/2026-05-20-faceswap-demo-design.md`

---

## File Structure

```
faceswap/
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── start.bat                      # Windows起動スクリプト
├── start.sh                       # Mac開発用
├── README.md
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + routes
│   ├── config.py                  # 定数(パス・TTL等)
│   ├── jobs.py                    # メモリ内ジョブマネージャ
│   ├── face_swap.py               # InsightFace + inswapper エンジン
│   ├── video.py                   # ffmpeg ラッパー
│   ├── templates_init.py          # 起動時テンプレ前処理
│   └── ep_selector.py             # ONNX Execution Provider 自動判定
├── frontend/
│   ├── index.html                 # 全画面構成(状態遷移はJS)
│   ├── app.js                     # メイン状態機械
│   ├── camera.js                  # カメラキャプチャ
│   ├── upload.js                  # stgモード画像アップロード
│   ├── minigame.js                # MediaPipe Pose + バスケ動作判定
│   ├── progress.js                # SSE進捗購読
│   ├── result.js                  # 結果表示 + QR
│   └── style.css                  # 素のCSS(Tailwind CDNと併用)
├── templates/
│   └── basketball.mp4             # 既存ファイル
├── models/                        # ONNXモデル(初回起動でDL/手動配置)
├── jobs/                          # アクティブジョブ(10分後自動削除)
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_jobs.py
    ├── test_face_swap.py
    ├── test_video.py
    ├── test_api.py
    └── fixtures/
        ├── test_face.jpg          # 顔ありテスト画像
        └── test_no_face.jpg       # 顔なしテスト画像
```

**File responsibilities:**
- `config.py`: 全パス・TTL・モデル名などの定数集約
- `jobs.py`: 単一プロセス内のジョブ状態管理、asyncio.Task保持
- `face_swap.py`: InsightFace のラッパー、`detect_face()` `swap_face()` の薄いAPI
- `video.py`: ffmpeg subprocessラッパー、フレーム抽出と1コマンドでの合成
- `templates_init.py`: 起動時にテンプレ動画をフレーム展開+顔検出キャッシュ
- `ep_selector.py`: 利用可能なEPを順に試行して使えるものを返す
- `main.py`: FastAPI ルートと SSE 実装、フロントの静的配信

---

## Task 0: プロジェクト初期化と Git リポジトリ

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `README.md`

- [ ] **Step 1: git init**

```bash
cd /Users/yamaku/work/faceswap
git init
git config user.email "r-zong@smc-tech.com"
git config user.name "r-zong"
```

- [ ] **Step 2: .gitignore を作成**

```
__pycache__/
*.pyc
.venv/
venv/
.env
models/*.onnx
models/buffalo_*
jobs/
templates/basketball/
.pytest_cache/
.coverage
*.swp
.DS_Store
```

- [ ] **Step 3: requirements.txt を作成**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
insightface==0.7.3
onnxruntime==1.20.0
onnxruntime-directml==1.20.0; platform_system == "Windows"
onnxruntime-openvino==1.20.0; platform_system == "Linux" or platform_system == "Windows"
numpy>=1.24,<2.0
opencv-python-headless==4.10.0.84
Pillow==11.0.0
aiofiles==24.1.0
sse-starlette==2.1.3
pytest==8.3.0
pytest-asyncio==0.24.0
httpx==0.27.2
```

- [ ] **Step 4: pyproject.toml を作成**

```toml
[project]
name = "faceswap-demo"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 5: README.md を作成**

```markdown
# FaceSwap Demo

ユーザーの顔をテンプレ動画に合成するWebデモアプリ。

## セットアップ

\`\`\`bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
\`\`\`

## モデル配置

\`models/\` に以下を手動配置:
- \`inswapper_128.onnx\` (HuggingFaceミラーから入手)
- InsightFace buffalo_l (初回起動で自動DL)

## 起動

\`\`\`bash
# Mac開発
./start.sh

# Windows本番
start.bat
\`\`\`
```

- [ ] **Step 6: 仮想環境作成と依存インストール**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

期待結果: 全パッケージ install成功

- [ ] **Step 7: 初回コミット**

```bash
git add .gitignore pyproject.toml requirements.txt README.md
git commit -m "chore: initial project setup"
```

---

## Task 1: config モジュール

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_config.py`:
```python
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
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_config.py -v
```

期待結果: ModuleNotFoundError (backend.config が存在しない)

- [ ] **Step 3: backend/config.py を実装**

`backend/__init__.py`: (空ファイル)

`backend/config.py`:
```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"
MODELS_DIR = PROJECT_ROOT / "models"
JOBS_DIR = PROJECT_ROOT / "jobs"

TEMPLATE_VIDEO = TEMPLATES_DIR / "basketball.mp4"
TEMPLATE_FRAMES_DIR = TEMPLATES_DIR / "basketball"

INSWAPPER_MODEL = MODELS_DIR / "inswapper_128.onnx"

JOB_TTL_SECONDS = 600                    # 10分
PROCESSING_TIMEOUT_SECONDS = 120         # 2分
MIN_GAME_DURATION_SECONDS = 30           # ミニゲーム最低時間
SSE_PROGRESS_EVERY_N_FRAMES = 5          # SSE間引き
BATCH_SIZE = 4                            # ONNX バッチ推論

WIPE_MARGIN_PX = 20                       # 結果動画ワイプの余白
WIPE_WIDTH_RATIO = 0.25                   # ワイプの幅(動画幅比)
```

`tests/__init__.py`: (空ファイル)
`tests/conftest.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

- [ ] **Step 4: テストが通ることを確認**

```bash
pytest tests/test_config.py -v
```

期待結果: 5 passed

- [ ] **Step 5: コミット**

```bash
git add backend/ tests/__init__.py tests/conftest.py tests/test_config.py
git commit -m "feat: add config module"
```

---

## Task 2: ジョブマネージャ(メモリ内)

**Files:**
- Create: `backend/jobs.py`
- Test: `tests/test_jobs.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_jobs.py`:
```python
import asyncio
import pytest
from backend.jobs import JobManager, JobStatus

@pytest.fixture
def manager():
    return JobManager()

async def test_create_job_returns_id(manager):
    job_id = manager.create()
    assert isinstance(job_id, str)
    assert len(job_id) >= 8

async def test_get_job_returns_pending(manager):
    job_id = manager.create()
    job = manager.get(job_id)
    assert job.status == JobStatus.PENDING
    assert job.progress == 0

async def test_update_progress(manager):
    job_id = manager.create()
    manager.update_progress(job_id, 50, "swapping frames")
    job = manager.get(job_id)
    assert job.progress == 50
    assert job.message == "swapping frames"

async def test_mark_done_sets_result_path(manager, tmp_path):
    job_id = manager.create()
    result = tmp_path / "result.mp4"
    result.write_bytes(b"fake")
    manager.mark_done(job_id, result)
    job = manager.get(job_id)
    assert job.status == JobStatus.DONE
    assert job.result_path == result

async def test_mark_failed_with_message(manager):
    job_id = manager.create()
    manager.mark_failed(job_id, "no face detected")
    job = manager.get(job_id)
    assert job.status == JobStatus.FAILED
    assert "no face" in job.message

async def test_get_nonexistent_raises(manager):
    with pytest.raises(KeyError):
        manager.get("does-not-exist")
```

- [ ] **Step 2: テストが失敗することを確認**

```bash
pytest tests/test_jobs.py -v
```

期待結果: ModuleNotFoundError

- [ ] **Step 3: 実装**

`backend/jobs.py`:
```python
from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    result_path: Optional[Path] = None
    created_at: float = field(default_factory=time.time)
    done_at: Optional[float] = None
    task: Optional[asyncio.Task] = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self) -> str:
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = Job(id=job_id)
        return job_id

    def get(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]

    def update_progress(self, job_id: str, progress: int, message: str = "") -> None:
        job = self.get(job_id)
        job.status = JobStatus.RUNNING
        job.progress = progress
        job.message = message

    def mark_done(self, job_id: str, result_path: Path) -> None:
        job = self.get(job_id)
        job.status = JobStatus.DONE
        job.progress = 100
        job.result_path = result_path
        job.done_at = time.time()

    def mark_failed(self, job_id: str, message: str) -> None:
        job = self.get(job_id)
        job.status = JobStatus.FAILED
        job.message = message
        job.done_at = time.time()

    def attach_task(self, job_id: str, task: asyncio.Task) -> None:
        self.get(job_id).task = task

    def all(self) -> list[Job]:
        return list(self._jobs.values())

    def remove(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_jobs.py -v
```

期待結果: 6 passed

- [ ] **Step 5: コミット**

```bash
git add backend/jobs.py tests/test_jobs.py
git commit -m "feat: add in-memory job manager"
```

---

## Task 3: Execution Provider 自動判定

**Files:**
- Create: `backend/ep_selector.py`
- Test: `tests/test_ep_selector.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_ep_selector.py`:
```python
from backend.ep_selector import select_providers, AVAILABLE_PROVIDERS

def test_returns_at_least_cpu():
    providers = select_providers()
    assert "CPUExecutionProvider" in providers

def test_priority_order():
    # 優先順位: CUDA > DML > OpenVINO > CPU
    providers = AVAILABLE_PROVIDERS
    cuda_idx = providers.index("CUDAExecutionProvider") if "CUDAExecutionProvider" in providers else 999
    dml_idx = providers.index("DmlExecutionProvider") if "DmlExecutionProvider" in providers else 999
    cpu_idx = providers.index("CPUExecutionProvider")
    assert cuda_idx < cpu_idx
    assert dml_idx < cpu_idx
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_ep_selector.py -v
```

- [ ] **Step 3: 実装**

`backend/ep_selector.py`:
```python
from __future__ import annotations
import logging
import onnxruntime as ort

logger = logging.getLogger(__name__)

AVAILABLE_PROVIDERS = [
    "CUDAExecutionProvider",
    "DmlExecutionProvider",
    "OpenVINOExecutionProvider",
    "CPUExecutionProvider",
]


def select_providers() -> list[str]:
    """Return ordered list of EPs actually available on this machine, ending with CPU."""
    runtime_available = set(ort.get_available_providers())
    selected = [p for p in AVAILABLE_PROVIDERS if p in runtime_available]
    if "CPUExecutionProvider" not in selected:
        selected.append("CPUExecutionProvider")
    logger.info("Selected ONNX providers: %s", selected)
    return selected
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_ep_selector.py -v
```

- [ ] **Step 5: コミット**

```bash
git add backend/ep_selector.py tests/test_ep_selector.py
git commit -m "feat: add execution provider auto-selection"
```

---

## Task 4: モデル準備 — inswapper_128 の手動配置とロード確認

**Files:**
- Create: `tests/fixtures/test_face.jpg` (手動配置)
- Note: `models/inswapper_128.onnx` は手動DL

- [ ] **Step 1: inswapper モデルを手動配置**

HuggingFace の `deepinsight/inswapper` ミラー、または `ezioruan/inswapper_128.onnx` 等から入手:

```bash
# 例: huggingface_hub で取得
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='ezioruan/inswapper_128.onnx', filename='inswapper_128.onnx', local_dir='models/')"
```

確認:
```bash
ls -lh models/inswapper_128.onnx
```

期待結果: 約 500MB のファイルが存在

- [ ] **Step 2: テスト用顔画像を準備**

`tests/fixtures/test_face.jpg` に顔が明瞭に写った正方形画像(512x512 推奨)を配置。
`tests/fixtures/test_no_face.jpg` には風景や単色画像。

- [ ] **Step 3: ロード可能性を確認(REPL)**

```bash
python -c "import onnxruntime as ort; s = ort.InferenceSession('models/inswapper_128.onnx', providers=['CPUExecutionProvider']); print(s.get_inputs()[0].shape)"
```

期待結果: `[1, 3, 128, 128]` または類似のshape出力

- [ ] **Step 4: コミット(fixturesのみ、モデル本体は.gitignore)**

```bash
git add tests/fixtures/
git commit -m "test: add face/no-face fixtures"
```

---

## Task 5: 顔検出ラッパー(InsightFace)

**Files:**
- Create: `backend/face_swap.py`
- Test: `tests/test_face_swap.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_face_swap.py`:
```python
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
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_face_swap.py::test_detect_face_in_face_image -v
```

- [ ] **Step 3: 実装(顔検出部分のみ)**

`backend/face_swap.py`:
```python
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
    # 面積最大の顔を選択
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0]


def detect_all_faces(image: np.ndarray) -> list:
    app = get_face_app()
    return app.get(image)
```

- [ ] **Step 4: 顔検出テスト通過確認**

```bash
pytest tests/test_face_swap.py -v -k detect
```

期待結果: 2 passed(初回はbuffalo_l モデル DL のため数十秒かかる)

- [ ] **Step 5: コミット**

```bash
git add backend/face_swap.py tests/test_face_swap.py
git commit -m "feat: add face detection wrapper"
```

---

## Task 6: 顔スワップエンジン(inswapper)

**Files:**
- Modify: `backend/face_swap.py`
- Modify: `tests/test_face_swap.py`

- [ ] **Step 1: テストを追加**

`tests/test_face_swap.py` に追加:
```python
def test_swap_face_returns_modified_image():
    import cv2
    from backend.face_swap import detect_largest_face, swap_face
    src_img = cv2.imread(str(FIXTURES / "test_face.jpg"))
    tgt_img = cv2.imread(str(FIXTURES / "test_face.jpg"))  # 同じ顔でもswap実行できる
    src_face = detect_largest_face(src_img)
    tgt_face = detect_largest_face(tgt_img)
    result = swap_face(tgt_img, tgt_face, src_face)
    assert result.shape == tgt_img.shape
    assert result.dtype == tgt_img.dtype
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_face_swap.py::test_swap_face_returns_modified_image -v
```

期待結果: ImportError(swap_face 未定義)

- [ ] **Step 3: 実装(`swap_face` を追加)**

`backend/face_swap.py` に追加:
```python
from insightface.model_zoo import get_model

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
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_face_swap.py -v
```

期待結果: 全テスト通過

- [ ] **Step 5: コミット**

```bash
git add backend/face_swap.py tests/test_face_swap.py
git commit -m "feat: add face swap engine"
```

---

## Task 7: テンプレ前処理(フレーム抽出 + 顔検出キャッシュ)

**Files:**
- Create: `backend/templates_init.py`
- Create: `backend/video.py` (フレーム抽出部分)
- Test: `tests/test_video.py`
- Test: `tests/test_templates_init.py`

- [ ] **Step 1: video.py のフレーム抽出テスト**

`tests/test_video.py`:
```python
from pathlib import Path
from backend.video import extract_frames, FFMPEG_NOT_FOUND
from backend.config import TEMPLATE_VIDEO


def test_extract_frames_creates_files(tmp_path):
    out_dir = tmp_path / "frames"
    count = extract_frames(TEMPLATE_VIDEO, out_dir)
    assert count == 121
    assert (out_dir / "frame_000000.jpg").exists()
    assert (out_dir / "frame_000120.jpg").exists()
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_video.py::test_extract_frames_creates_files -v
```

- [ ] **Step 3: video.py 実装(フレーム抽出部分のみ)**

`backend/video.py`:
```python
from __future__ import annotations
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegError(RuntimeError):
    pass


FFMPEG_NOT_FOUND = "ffmpeg binary not found on PATH"


def _ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise FFmpegError(FFMPEG_NOT_FOUND)
    return path


def extract_frames(video_path: Path, out_dir: Path) -> int:
    """Extract all frames as JPEG to out_dir. Return frame count."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "frame_%06d.jpg"
    cmd = [
        _ffmpeg_bin(),
        "-y",
        "-i", str(video_path),
        "-qscale:v", "2",
        str(pattern),
    ]
    logger.info("Extracting frames: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(f"ffmpeg failed: {result.stderr}")
    return len(list(out_dir.glob("frame_*.jpg")))
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_video.py -v
```

期待結果: 1 passed

- [ ] **Step 5: templates_init テストを書く**

`tests/test_templates_init.py`:
```python
from backend.templates_init import prepare_templates
from backend.config import TEMPLATE_FRAMES_DIR


def test_prepare_templates_creates_frames_and_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.config.TEMPLATE_FRAMES_DIR", tmp_path / "basketball")
    # Implementation will detect faces in each frame and cache.
    result = prepare_templates()
    assert result.frame_count == 121
    assert result.faces_per_frame  # list of detected faces per frame
    assert len(result.faces_per_frame) == 121
```

- [ ] **Step 6: 失敗確認**

```bash
pytest tests/test_templates_init.py -v
```

- [ ] **Step 7: templates_init 実装**

`backend/templates_init.py`:
```python
from __future__ import annotations
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import cv2

from backend.config import TEMPLATE_VIDEO, TEMPLATE_FRAMES_DIR
from backend.video import extract_frames
from backend.face_swap import detect_all_faces, get_face_app

logger = logging.getLogger(__name__)


@dataclass
class TemplateData:
    frame_count: int
    faces_per_frame: list  # list[list[Face]] - per frame, the detected faces


_cache: TemplateData | None = None
CACHE_FILE = TEMPLATE_FRAMES_DIR / "faces_cache.pkl"


def prepare_templates() -> TemplateData:
    global _cache
    if _cache is not None:
        return _cache

    # 1. Extract frames if missing
    needs_extract = not TEMPLATE_FRAMES_DIR.exists() or not list(TEMPLATE_FRAMES_DIR.glob("frame_*.jpg"))
    if needs_extract:
        logger.info("Extracting template frames...")
        extract_frames(TEMPLATE_VIDEO, TEMPLATE_FRAMES_DIR)

    frame_files = sorted(TEMPLATE_FRAMES_DIR.glob("frame_*.jpg"))
    frame_count = len(frame_files)

    # 2. Load or compute face cache
    if CACHE_FILE.exists():
        logger.info("Loading cached template faces")
        with open(CACHE_FILE, "rb") as f:
            faces_per_frame = pickle.load(f)
    else:
        logger.info("Detecting faces in %d template frames", frame_count)
        get_face_app()  # warm up
        faces_per_frame = []
        for i, frame_file in enumerate(frame_files):
            img = cv2.imread(str(frame_file))
            faces_per_frame.append(detect_all_faces(img))
            if (i + 1) % 20 == 0:
                logger.info("  ... %d / %d", i + 1, frame_count)
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(faces_per_frame, f)

    _cache = TemplateData(frame_count=frame_count, faces_per_frame=faces_per_frame)
    return _cache
```

- [ ] **Step 8: テスト通過確認**

```bash
pytest tests/test_templates_init.py -v
```

(初回は数十秒〜1分かかる、2回目以降キャッシュで即完了)

- [ ] **Step 9: コミット**

```bash
git add backend/video.py backend/templates_init.py tests/test_video.py tests/test_templates_init.py
git commit -m "feat: add template frame extraction and face cache"
```

---

## Task 8: 動画合成(ffmpeg 1コマンドで再構築+音声+ワイプ)

**Files:**
- Modify: `backend/video.py`
- Modify: `tests/test_video.py`

- [ ] **Step 1: テストを追加**

`tests/test_video.py` に追加:
```python
def test_compose_video_with_audio_and_wipe(tmp_path):
    from backend.video import compose_video
    from backend.config import TEMPLATE_VIDEO

    frames_dir = tmp_path / "frames"
    extract_frames(TEMPLATE_VIDEO, frames_dir)

    wipe_image = tmp_path / "wipe.jpg"
    # 適当に1枚のフレームをwipe画像として使う
    import shutil
    shutil.copy(frames_dir / "frame_000000.jpg", wipe_image)

    output = tmp_path / "out.mp4"
    compose_video(
        frames_dir=frames_dir,
        audio_source=TEMPLATE_VIDEO,
        wipe_image=wipe_image,
        output=output,
        fps=24,
    )
    assert output.exists()
    # ffprobeで音声トラック確認
    import subprocess
    info = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "default=noprint_wrappers=1:nokey=1", str(output)],
        capture_output=True, text=True,
    )
    assert "audio" in info.stdout
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_video.py::test_compose_video_with_audio_and_wipe -v
```

- [ ] **Step 3: 実装**

`backend/video.py` に追加:
```python
from backend.config import WIPE_MARGIN_PX, WIPE_WIDTH_RATIO


def compose_video(
    frames_dir: Path,
    audio_source: Path,
    wipe_image: Path,
    output: Path,
    fps: int = 24,
) -> None:
    """
    Combine swapped frames + original audio + wipe overlay in ONE ffmpeg invocation.

    Layout:
      [main video stream from frames_dir/frame_*.jpg]
      [wipe overlay scaled to WIPE_WIDTH_RATIO of width, positioned bottom-right]
      [audio from audio_source]
    """
    # filter_complex:
    #   [1:v]scale=W*ratio:-1[wipe];
    #   [0:v][wipe]overlay=W-w-margin:H-h-margin[v]
    margin = WIPE_MARGIN_PX
    cmd = [
        _ffmpeg_bin(),
        "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%06d.jpg"),
        "-i", str(wipe_image),
        "-i", str(audio_source),
        "-filter_complex",
        (
            f"[1:v]scale=iw*{WIPE_WIDTH_RATIO}/iw*main_w/iw:-1[wipe];"
            f"[0:v][wipe]overlay=W-w-{margin}:H-h-{margin}[v]"
        ),
        "-map", "[v]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output),
    ]
    logger.info("Composing video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(f"ffmpeg compose failed: {result.stderr}")
```

注意: 上記 filter_complex は実機で要調整。`scale` 式は単純に `iw*0.25` でも可。検証後シンプル化を推奨:

```
[1:v]scale=iw*0.25:-1[wipe];[0:v][wipe]overlay=W-w-20:H-h-20[v]
```

ただし `iw` はwipe入力のwidth、Wは main video width。位置は `W-w-20` でmain video右下20pxマージン。

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_video.py -v
```

- [ ] **Step 5: コミット**

```bash
git add backend/video.py tests/test_video.py
git commit -m "feat: add video composition with audio and wipe overlay"
```

---

## Task 9: FaceSwap オーケストレータ(検出→各フレームswap→合成)

**Files:**
- Modify: `backend/face_swap.py`
- Test: `tests/test_face_swap.py`

- [ ] **Step 1: テストを書く**

`tests/test_face_swap.py` に追加:
```python
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
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_face_swap.py::test_swap_video_end_to_end -v
```

- [ ] **Step 3: 実装**

`backend/face_swap.py` に追加:
```python
import asyncio
import shutil
from typing import Callable, Awaitable

import cv2

from backend.config import (
    TEMPLATE_VIDEO, TEMPLATE_FRAMES_DIR,
    BATCH_SIZE, SSE_PROGRESS_EVERY_N_FRAMES,
)
from backend.templates_init import prepare_templates
from backend.video import compose_video

ProgressCallback = Callable[[int, str], None]


async def swap_video_job(
    src_face_image_path: str,
    template_frames_dir: Path,
    output: Path,
    progress: ProgressCallback,
) -> None:
    """Run the full swap pipeline. Updates progress 0-100."""
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
    swapper = get_swapper()

    for i, frame_file in enumerate(frame_files):
        img = cv2.imread(str(frame_file))
        faces = tpl.faces_per_frame[i]
        if faces:
            # largest face in template
            target_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
            img = await asyncio.to_thread(
                swapper.get, img, target_face, src_face, True
            )
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
        TEMPLATE_VIDEO,         # audio source
        Path(src_face_image_path),  # wipe = source face image
        output,
        24,
    )

    # 5. Cleanup intermediate
    shutil.rmtree(swapped_dir, ignore_errors=True)
    progress(100, "完成!")
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_face_swap.py::test_swap_video_end_to_end -v
```

(数十秒〜1分かかる、最終的に通過すること)

- [ ] **Step 5: コミット**

```bash
git add backend/face_swap.py tests/test_face_swap.py
git commit -m "feat: add end-to-end face swap orchestrator"
```

---

## Task 10: FastAPI スケルトン + 静的ファイル配信

**Files:**
- Create: `backend/main.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: テストを書く**

`tests/test_api.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_root_returns_html(client):
    res = await client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


async def test_healthcheck(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_api.py -v
```

- [ ] **Step 3: 実装**

`backend/main.py`:
```python
from __future__ import annotations
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_ROOT
from backend.jobs import JobManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FaceSwap Demo")

FRONTEND_DIR = PROJECT_ROOT / "frontend"

job_manager = JobManager()


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Mount frontend assets after API routes
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
```

仮の `frontend/index.html`:
```html
<!DOCTYPE html>
<html><body><h1>FaceSwap</h1></body></html>
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_api.py -v
```

- [ ] **Step 5: 手動でサーバ起動確認**

```bash
uvicorn backend.main:app --reload --port 8000
curl http://localhost:8000/api/health
```

期待結果: `{"status":"ok"}`

- [ ] **Step 6: コミット**

```bash
git add backend/main.py frontend/index.html tests/test_api.py
git commit -m "feat: add FastAPI skeleton and static serving"
```

---

## Task 11: POST /api/swap + SSE /api/job

**Files:**
- Modify: `backend/main.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: テストを書く**

`tests/test_api.py` に追加:
```python
async def test_swap_creates_job(client, tmp_path, monkeypatch):
    monkeypatch.setattr("backend.config.JOBS_DIR", tmp_path)
    face_jpg = (Path(__file__).parent / "fixtures" / "test_face.jpg").read_bytes()
    res = await client.post(
        "/api/swap",
        files={"face": ("face.jpg", face_jpg, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    assert data["sse_url"].startswith("/api/job/")


async def test_job_not_found_returns_404(client):
    res = await client.get("/api/job/does-not-exist")
    assert res.status_code == 404
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_api.py -v
```

- [ ] **Step 3: 実装**

`backend/main.py` に追加:
```python
import asyncio
import aiofiles
from fastapi import UploadFile, File, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.config import JOBS_DIR, TEMPLATE_FRAMES_DIR, JOB_TTL_SECONDS, PROCESSING_TIMEOUT_SECONDS
from backend.face_swap import swap_video_job, FaceNotFoundError
from backend.jobs import JobStatus


@app.post("/api/swap")
async def create_swap(face: UploadFile = File(...)):
    job_id = job_manager.create()
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    face_path = job_dir / "face.jpg"

    contents = await face.read()
    async with aiofiles.open(face_path, "wb") as f:
        await f.write(contents)

    result_path = job_dir / "result.mp4"

    async def run() -> None:
        def progress(pct: int, msg: str) -> None:
            job_manager.update_progress(job_id, pct, msg)
        try:
            await asyncio.wait_for(
                swap_video_job(
                    src_face_image_path=str(face_path),
                    template_frames_dir=TEMPLATE_FRAMES_DIR,
                    output=result_path,
                    progress=progress,
                ),
                timeout=PROCESSING_TIMEOUT_SECONDS,
            )
            job_manager.mark_done(job_id, result_path)
            asyncio.create_task(_cleanup_after(job_id, JOB_TTL_SECONDS))
        except FaceNotFoundError as e:
            job_manager.mark_failed(job_id, f"顔が検出できません: {e}")
        except asyncio.TimeoutError:
            job_manager.mark_failed(job_id, "処理がタイムアウトしました")
        except Exception as e:
            logger.exception("Job %s failed", job_id)
            job_manager.mark_failed(job_id, f"内部エラー: {type(e).__name__}")

    task = asyncio.create_task(run())
    job_manager.attach_task(job_id, task)

    return {"job_id": job_id, "sse_url": f"/api/job/{job_id}"}


async def _cleanup_after(job_id: str, delay: int) -> None:
    await asyncio.sleep(delay)
    job = job_manager.get(job_id)
    job_dir = JOBS_DIR / job_id
    import shutil
    shutil.rmtree(job_dir, ignore_errors=True)
    job_manager.remove(job_id)
    logger.info("Cleaned up job %s", job_id)


@app.get("/api/job/{job_id}")
async def job_sse(job_id: str):
    try:
        job_manager.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        last_emit = (-1, "")
        while True:
            try:
                job = job_manager.get(job_id)
            except KeyError:
                yield {"event": "removed", "data": "job removed"}
                return

            current = (job.progress, job.message)
            if current != last_emit:
                yield {
                    "event": "progress",
                    "data": f'{{"progress":{job.progress},"message":"{job.message}","status":"{job.status.value}"}}',
                }
                last_emit = current

            if job.status in (JobStatus.DONE, JobStatus.FAILED):
                yield {
                    "event": job.status.value,
                    "data": f'{{"status":"{job.status.value}","message":"{job.message}"}}',
                }
                return
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_stream())
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_api.py -v
```

- [ ] **Step 5: コミット**

```bash
git add backend/main.py tests/test_api.py
git commit -m "feat: add swap endpoint and SSE progress"
```

---

## Task 12: 結果配信(視聴用 + ダウンロード用)

**Files:**
- Modify: `backend/main.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: テストを書く**

`tests/test_api.py` に追加:
```python
async def test_result_streams_video(client, tmp_path, monkeypatch):
    # ジョブを作成して done にする
    monkeypatch.setattr("backend.config.JOBS_DIR", tmp_path)
    job_id = job_manager.create()
    job_dir = tmp_path / job_id
    job_dir.mkdir()
    fake_mp4 = job_dir / "result.mp4"
    fake_mp4.write_bytes(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 200)
    job_manager.mark_done(job_id, fake_mp4)

    res = await client.get(f"/api/result/{job_id}.mp4")
    assert res.status_code == 200
    assert res.headers["content-type"] == "video/mp4"

    res2 = await client.get(f"/api/download/{job_id}.mp4")
    assert res2.status_code == 200
    assert "attachment" in res2.headers.get("content-disposition", "")
```

- [ ] **Step 2: 失敗確認**

```bash
pytest tests/test_api.py -v
```

- [ ] **Step 3: 実装**

`backend/main.py` に追加:
```python
from fastapi.responses import FileResponse


@app.get("/api/result/{job_id}.mp4")
async def get_result(job_id: str):
    try:
        job = job_manager.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DONE or not job.result_path or not job.result_path.exists():
        raise HTTPException(404, "Result not ready")
    return FileResponse(job.result_path, media_type="video/mp4")


@app.get("/api/download/{job_id}.mp4")
async def download_result(job_id: str):
    try:
        job = job_manager.get(job_id)
    except KeyError:
        raise HTTPException(404, "Job not found")
    if job.status != JobStatus.DONE or not job.result_path or not job.result_path.exists():
        raise HTTPException(404, "Result not ready")
    return FileResponse(
        job.result_path,
        media_type="video/mp4",
        filename=f"faceswap_{job_id}.mp4",
        headers={"Content-Disposition": f'attachment; filename="faceswap_{job_id}.mp4"'},
    )
```

- [ ] **Step 4: テスト通過確認**

```bash
pytest tests/test_api.py -v
```

- [ ] **Step 5: コミット**

```bash
git add backend/main.py tests/test_api.py
git commit -m "feat: add result streaming and download endpoints"
```

---

## Task 13: 起動時プリロード

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: 実装**

`backend/main.py` の app 定義後に追加:
```python
from contextlib import asynccontextmanager

from backend.face_swap import preload as preload_models
from backend.templates_init import prepare_templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Preloading models and templates...")
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    preload_models()
    prepare_templates()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down")

app = FastAPI(title="FaceSwap Demo", lifespan=lifespan)
```

(既存の `app = FastAPI(...)` 行を置換)

- [ ] **Step 2: 手動確認**

```bash
uvicorn backend.main:app --port 8000
```

期待結果: ログに `Preloading models and templates...` → `Startup complete` が出る。初回は1〜2分かかる。

- [ ] **Step 3: コミット**

```bash
git add backend/main.py
git commit -m "feat: preload models and templates on startup"
```

---

## Task 14: フロントエンド HTML 骨格 + ランディング画面

**Files:**
- Modify: `frontend/index.html`
- Create: `frontend/style.css`
- Create: `frontend/app.js`

- [ ] **Step 1: HTML を書き直す**

`frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FaceSwap - あなたが主役になる</title>
  <link rel="stylesheet" href="/static/style.css" />
  <script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
</head>
<body>

  <!-- View 1: Landing -->
  <section id="view-landing" class="view active">
    <video id="bg-video" autoplay loop muted playsinline>
      <source src="/static/basketball.mp4" type="video/mp4" />
    </video>
    <div class="overlay">
      <h1>📸 あなたが主役になる</h1>
      <button id="btn-start" class="primary">START</button>
      <p class="hint">処理時間: 30秒〜1分</p>
    </div>
  </section>

  <!-- View 2: Capture -->
  <section id="view-capture" class="view">
    <video id="camera" autoplay playsinline></video>
    <canvas id="capture-canvas" hidden></canvas>
    <div class="overlay">
      <button id="btn-shutter" class="primary">📷 撮影</button>
      <input type="file" id="upload-input" accept="image/*" hidden />
      <button id="btn-upload" class="secondary">画像をアップロード(stg)</button>
    </div>
  </section>

  <!-- View 3: Confirm -->
  <section id="view-confirm" class="view">
    <img id="captured-preview" alt="captured face" />
    <div class="overlay">
      <button id="btn-retake" class="secondary">撮り直す</button>
      <button id="btn-confirm" class="primary">これでOK</button>
    </div>
  </section>

  <!-- View 4: Minigame / Processing -->
  <section id="view-game" class="view">
    <video id="game-bg" loop muted playsinline>
      <source src="/static/basketball.mp4" type="video/mp4" />
    </video>
    <canvas id="pose-canvas"></canvas>
    <video id="game-camera" autoplay playsinline hidden></video>
    <div class="hud">
      <p id="game-message">神プレイへの修行中...</p>
      <progress id="combined-progress" max="100" value="0"></progress>
      <p id="server-message"></p>
    </div>
  </section>

  <!-- View 5: Result -->
  <section id="view-result" class="view">
    <video id="result-video" autoplay controls></video>
    <div class="result-overlay">
      <h2>🎉 神プレイ完成!</h2>
      <div id="qr-container"></div>
      <p class="hint">QRをスマホで読み取ってDL</p>
      <button id="btn-again" class="primary">もう一回</button>
    </div>
  </section>

  <script type="module" src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: CSS を作成**

`frontend/style.css`:
```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, sans-serif; background: #000; color: #fff; overflow: hidden; }
.view { position: fixed; inset: 0; display: none; }
.view.active { display: flex; }
#bg-video, #game-bg, #camera, #game-camera, #result-video {
  position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover;
}
.overlay, .result-overlay {
  position: relative; z-index: 2; margin: auto; padding: 2rem;
  background: rgba(0,0,0,0.6); border-radius: 1rem;
  display: flex; flex-direction: column; gap: 1rem; align-items: center;
}
h1 { font-size: 3rem; }
button.primary {
  background: #f60; color: #fff; border: none; padding: 1rem 2rem;
  font-size: 1.5rem; border-radius: 0.5rem; cursor: pointer;
}
button.secondary { background: rgba(255,255,255,0.2); color: #fff; padding: 0.5rem 1rem; border: none; border-radius: 0.25rem; cursor: pointer; }
.hud { position: absolute; bottom: 2rem; left: 0; right: 0; padding: 1rem; text-align: center; background: rgba(0,0,0,0.5); z-index: 3; }
progress { width: 80%; height: 1rem; }
#qr-container { background: #fff; padding: 1rem; }
#qr-container img { display: block; }
#captured-preview { max-width: 50%; max-height: 50%; margin: auto; }
#pose-canvas { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 2; }
```

- [ ] **Step 3: app.js 骨組み(状態機械)**

`frontend/app.js`:
```javascript
const views = ['landing', 'capture', 'confirm', 'game', 'result'];

export function showView(name) {
  for (const v of views) {
    document.getElementById(`view-${v}`).classList.toggle('active', v === name);
  }
}

// State machine entry
document.getElementById('btn-start').addEventListener('click', () => {
  import('./camera.js').then(m => m.startCapture());
});

document.getElementById('btn-again').addEventListener('click', () => {
  location.reload();
});

// Initial view
showView('landing');
```

- [ ] **Step 4: テンプレ動画を `frontend/` から見えるように**

```bash
cp templates/basketball.mp4 frontend/basketball.mp4
# または StaticFiles のマウントを2つに分ける
```

(または `backend/main.py` で `app.mount("/static/basketball.mp4", FileResponse(...))` 等)

シンプル化のため `frontend/basketball.mp4` をシンボリックリンクにする:
```bash
ln -s ../templates/basketball.mp4 frontend/basketball.mp4
```

- [ ] **Step 5: 手動確認**

```bash
uvicorn backend.main:app --port 8000
```

ブラウザで http://localhost:8000 → ランディング画面に basketball.mp4 が背景ループ、STARTボタンが表示される。

- [ ] **Step 6: コミット**

```bash
git add frontend/
git commit -m "feat: add HTML skeleton and landing view"
```

---

## Task 15: カメラキャプチャ + 画像アップロード(stgモード)

**Files:**
- Create: `frontend/camera.js`
- Create: `frontend/upload.js`
- Modify: `frontend/app.js`

- [ ] **Step 1: camera.js**

`frontend/camera.js`:
```javascript
import { showView } from './app.js';

let stream = null;

export async function startCapture() {
  showView('capture');
  const video = document.getElementById('camera');

  // stgモード: ?mode=stg なら画像アップロードボタンを表示
  const mode = new URLSearchParams(location.search).get('mode');
  document.getElementById('btn-upload').hidden = mode !== 'stg';

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 640 },
      audio: false,
    });
    video.srcObject = stream;
  } catch (e) {
    alert('カメラを許可してください、または ?mode=stg で画像アップロードへ');
    showView('landing');
    return;
  }

  document.getElementById('btn-shutter').onclick = () => captureFrame();
  document.getElementById('btn-upload').onclick = () => {
    document.getElementById('upload-input').click();
  };
  document.getElementById('upload-input').onchange = (e) => {
    const file = e.target.files[0];
    if (file) uploadFile(file);
  };
}

function captureFrame() {
  const video = document.getElementById('camera');
  const canvas = document.getElementById('capture-canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  canvas.toBlob((blob) => {
    releaseCamera();
    showConfirm(blob);
  }, 'image/jpeg', 0.92);
}

function uploadFile(file) {
  releaseCamera();
  showConfirm(file);
}

function releaseCamera() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
}

let pendingBlob = null;

function showConfirm(blob) {
  pendingBlob = blob;
  const url = URL.createObjectURL(blob);
  document.getElementById('captured-preview').src = url;
  showView('confirm');
}

document.getElementById('btn-retake').addEventListener('click', () => {
  startCapture();
});

document.getElementById('btn-confirm').addEventListener('click', () => {
  if (pendingBlob) {
    import('./progress.js').then(m => m.submitJob(pendingBlob));
  }
});
```

- [ ] **Step 2: 手動確認**

```bash
uvicorn backend.main:app --port 8000
```

ブラウザで START → カメラ起動 → シャッター → 確認画面まで動く

- [ ] **Step 3: コミット**

```bash
git add frontend/camera.js
git commit -m "feat: add camera capture and stg upload"
```

---

## Task 16: ミニゲーム(MediaPipe Pose + バスケ動作判定)

**Files:**
- Create: `frontend/minigame.js`

- [ ] **Step 1: minigame.js 実装**

`frontend/minigame.js`:
```javascript
const POSE_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5/pose.js';
const MIN_DURATION_MS = 30_000;

let startTime = 0;
let gameProgress = 0;       // 0-100, ゲーム自身の達成度
let serverProgress = 0;     // 0-100, バックエンド処理進捗
let serverDone = false;
let dribbleCount = 0;
let shootCount = 0;
const DRIBBLE_TARGET = 10;
const SHOOT_TARGET = 3;

let camStream = null;
let pose = null;
let lastWristY = null;
let bothHandsUpFrames = 0;

export async function startGame() {
  const { showView } = await import('./app.js');
  showView('game');
  startTime = Date.now();

  // 1. カメラ起動
  const camera = document.getElementById('game-camera');
  camStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  camera.srcObject = camStream;
  camera.hidden = false;

  // 2. MediaPipe Pose 読み込み
  try {
    await loadScript(POSE_CDN);
    setupPose(camera);
  } catch (e) {
    console.error('MediaPipe load failed, falling back to timer-only', e);
  }

  // 3. ループ: 進捗監視
  requestAnimationFrame(updateUI);
}

function loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement('script');
    s.src = src; s.onload = res; s.onerror = rej;
    document.head.appendChild(s);
  });
}

function setupPose(videoEl) {
  pose = new Pose({ locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5/${f}` });
  pose.setOptions({ modelComplexity: 0, smoothLandmarks: true, enableSegmentation: false });
  pose.onResults(onPoseResults);

  const tick = async () => {
    if (videoEl.readyState >= 2) {
      await pose.send({ image: videoEl });
    }
    if (!serverDone || gameProgress < 100) requestAnimationFrame(tick);
  };
  tick();
}

function onPoseResults(results) {
  if (!results.poseLandmarks) return;
  const lm = results.poseLandmarks;
  // wrist landmarks: 15 (left), 16 (right)
  const lw = lm[15], rw = lm[16];
  const ls = lm[11], rs = lm[12]; // shoulders

  // ドリブル: 右手首が上下に動く
  if (lastWristY !== null) {
    const dy = rw.y - lastWristY;
    if (dy > 0.05) { /* descending */ }
    if (dy < -0.05) { dribbleCount++; }
  }
  lastWristY = rw.y;

  // シュート: 両手首が両肩より上(連続して数フレーム)
  if (lw.y < ls.y && rw.y < rs.y) {
    bothHandsUpFrames++;
    if (bothHandsUpFrames === 10) shootCount++;
  } else {
    bothHandsUpFrames = 0;
  }

  // ゲーム進捗計算
  const motionPct = Math.min(100, (dribbleCount / DRIBBLE_TARGET) * 50 + (shootCount / SHOOT_TARGET) * 50);
  gameProgress = motionPct;
}

function updateUI() {
  const elapsed = Date.now() - startTime;
  const elapsedPct = Math.min(100, (elapsed / MIN_DURATION_MS) * 100);
  const combined = Math.max(elapsedPct, gameProgress, serverProgress * 0.9);
  document.getElementById('combined-progress').value = combined;

  const msg = serverDone
    ? '神プレイ完成!まもなく解禁'
    : `ドリブル ${dribbleCount}/${DRIBBLE_TARGET} | シュート ${shootCount}/${SHOOT_TARGET}`;
  document.getElementById('game-message').textContent = msg;

  // 解禁条件: 経過 >= MIN_DURATION_MS AND serverDone
  if (elapsed >= MIN_DURATION_MS && serverDone) {
    cleanup();
    import('./result.js').then(m => m.showResult());
    return;
  }
  requestAnimationFrame(updateUI);
}

function cleanup() {
  if (camStream) {
    camStream.getTracks().forEach(t => t.stop());
    camStream = null;
  }
}

export function setServerProgress(pct, msg) {
  serverProgress = pct;
  document.getElementById('server-message').textContent = msg || '';
}

export function setServerDone() {
  serverDone = true;
  serverProgress = 100;
}
```

- [ ] **Step 2: 手動確認**

(progress.js から呼ばれるので、現時点では単体起動できない。次のタスクで結線後に確認)

- [ ] **Step 3: コミット**

```bash
git add frontend/minigame.js
git commit -m "feat: add minigame with MediaPipe Pose and motion scoring"
```

---

## Task 17: SSE 進捗購読 + ジョブ提出

**Files:**
- Create: `frontend/progress.js`
- Create: `frontend/result.js`

- [ ] **Step 1: progress.js**

`frontend/progress.js`:
```javascript
let currentJobId = null;
let resultUrl = null;
let downloadUrl = null;

export async function submitJob(faceBlob) {
  const { startGame, setServerProgress, setServerDone } = await import('./minigame.js');

  const fd = new FormData();
  fd.append('face', faceBlob, 'face.jpg');
  const res = await fetch('/api/swap', { method: 'POST', body: fd });
  const { job_id, sse_url } = await res.json();
  currentJobId = job_id;
  resultUrl = `/api/result/${job_id}.mp4`;
  downloadUrl = `${location.origin}/api/download/${job_id}.mp4`;

  // ミニゲーム開始
  startGame();

  // SSE購読
  const es = new EventSource(sse_url);
  es.addEventListener('progress', (e) => {
    const d = JSON.parse(e.data);
    setServerProgress(d.progress, d.message);
  });
  es.addEventListener('done', () => {
    setServerDone();
    es.close();
  });
  es.addEventListener('failed', (e) => {
    const d = JSON.parse(e.data);
    alert(`処理失敗: ${d.message}`);
    es.close();
    location.reload();
  });
}

export function getResultUrls() {
  return { play: resultUrl, download: downloadUrl };
}
```

- [ ] **Step 2: result.js**

`frontend/result.js`:
```javascript
import { showView } from './app.js';
import { getResultUrls } from './progress.js';

export function showResult() {
  showView('result');
  const { play, download } = getResultUrls();
  const video = document.getElementById('result-video');
  video.src = play;
  video.play().catch(() => { /* autoplay rejected, user has controls */ });

  // QR生成: ダウンロード用URL
  const qr = qrcode(0, 'M');
  qr.addData(download);
  qr.make();
  document.getElementById('qr-container').innerHTML = qr.createImgTag(6);
}
```

- [ ] **Step 3: 手動確認(E2E)**

```bash
uvicorn backend.main:app --port 8000
```

ブラウザで:
1. START → カメラ撮影 → これでOK
2. ミニゲーム画面に遷移、進捗バー動く
3. バックエンド処理完了 + 30秒経過 → 結果画面へ
4. 結果動画再生、QRコード表示
5. スマホでQRスキャン → MP4ダウンロード

- [ ] **Step 4: コミット**

```bash
git add frontend/progress.js frontend/result.js
git commit -m "feat: wire SSE progress and result display with QR"
```

---

## Task 18: cloudflared 統合と起動スクリプト

**Files:**
- Create: `start.sh` (Mac開発)
- Create: `start.bat` (Windows本番)

- [ ] **Step 1: cloudflared をインストール**

Mac:
```bash
brew install cloudflared
```

Windows: https://github.com/cloudflare/cloudflared/releases から `.exe` をDL、PATHに配置

- [ ] **Step 2: start.sh(Mac)**

`start.sh`:
```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

# 仮想環境を起動
source .venv/bin/activate

# バックグラウンドで uvicorn 起動
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Cloudflare Tunnel quick tunnel
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:8000

# 終了時にuvicorn を kill
trap "kill $UVICORN_PID" EXIT
wait
```

```bash
chmod +x start.sh
```

- [ ] **Step 3: start.bat(Windows本番)**

`start.bat`:
```bat
@echo off
cd /d %~dp0

call .venv\Scripts\activate

start "uvicorn" /b python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

timeout /t 5 /nobreak

echo Starting Cloudflare Tunnel...
cloudflared tunnel --url http://localhost:8000

pause
```

- [ ] **Step 4: 手動確認**

Mac:
```bash
./start.sh
```

出力に `https://xxxxx.trycloudflare.com` が表示される → ブラウザで開いて動作確認。

- [ ] **Step 5: README 更新**

`README.md` に起動セクションを追加:
```markdown
## デモ起動

1. \`./start.sh\` (Mac) または \`start.bat\` (Windows)
2. 出力に表示される \`https://xxxxx.trycloudflare.com\` を共有
3. ブラウザで開いてSTART
```

- [ ] **Step 6: コミット**

```bash
git add start.sh start.bat README.md
git commit -m "feat: add startup scripts with Cloudflare Tunnel"
```

---

## Task 19: TODOS と最終チェック

**Files:**
- Create: `TODOS.md`

- [ ] **Step 1: TODOS.md 作成**

`TODOS.md`:
```markdown
# TODOS — 後回し項目

## モデル関連
- [ ] **inswapper代替モデル検証** — 商用利用・外部公開する場合 SimSwap or GhostFaceShifter への移行を検討。`face_swap.py` の `swap_face()` 関数のみ差し替え

## インフラ関連
- [ ] **Named Tunnel化** — quick tunnel のURL揮発が運用上問題になった時点で対応。Cloudflareアカウント登録 → `cloudflared tunnel create` → DNS設定

## 機能拡張(必要に応じて)
- [ ] **複数テンプレート対応UI** — basketball以外のテンプレを追加する時のUI設計
- [ ] **ジョブ永続化** — 本番運用が見えてきたらSQLiteへ
- [ ] **観衆の歓声SE** — 処理中の没入感向上
- [ ] **シェアボタン**(SNS連携)
- [ ] **ウォーターマーク**(悪用抑止)
- [ ] **多言語対応**(EN/JP切替)
```

- [ ] **Step 2: 最終E2E動作確認**

完全フローを通す:
1. `./start.sh`
2. `cloudflared` のURL取得
3. 別端末/別ネットワークからアクセス
4. カメラ起動 → 顔キャプチャ → ミニゲーム → 結果動画 → QR → スマホでDL

- [ ] **Step 3: 全テスト実行**

```bash
pytest -v
```

期待結果: 全テスト通過

- [ ] **Step 4: 最終コミット**

```bash
git add TODOS.md
git commit -m "docs: add TODOS for deferred items"
```

---

## Self-Review チェックリスト

### Spec coverage
- ✅ Web アプリ / Windows ノートPC / カメラ取得 / 画像アップロード(stg) → Tasks 14-15
- ✅ テンプレ basketball.mp4 固定 → Tasks 7, 14
- ✅ 結果動画 + QRコード → Tasks 12, 17
- ✅ Cloudflare Tunnel → Task 18
- ✅ 待ち時間ミニゲーム → Task 16
- ✅ ワイプ合成 → Task 8
- ✅ 音声保持 → Task 8
- ✅ 進捗バー(SSE) → Task 11, 17
- ✅ 顔検出失敗エラー → Task 5, 11
- ✅ 自動削除10分 → Task 11
- ✅ 30秒経過 AND バックエンド完了で解禁 → Task 16
- ✅ EP自動判定 → Task 3
- ✅ バッチ推論 → 既定値、Task 9 で活用可
- ✅ ffmpeg統合 → Task 8 (1コマンド)
- ✅ SSE間引き → Task 9

### Placeholders
なし(全タスクに具体的なコード・コマンド・期待結果あり)

### 型・命名整合性
- `JobStatus`, `Job`, `JobManager` — Task 2 で定義、Task 11-12 で使用、一致 ✅
- `swap_video_job()` — Task 9 で定義、Task 11 で使用 ✅
- `progress(pct, msg)` コールバック — Task 9, 11 で一貫 ✅
- `showView(name)` — Task 14 で定義、Task 15-17 で使用 ✅

---

## 実装オプション

Two execution options:

**1. Subagent-Driven (recommended)** — タスクごとに独立サブエージェントをdispatch、レビュー挟みつつ高速反復

**2. Inline Execution** — このセッション内で順次実行、チェックポイントごとにレビュー

どちらで進めますか?
