# Google Colab 対応設計

**日付:** 2026-05-20  
**目的:** 開発・テスト用途で Windows ノートを使わずに FaceSwap デモを Colab 上で動かす

---

## 概要

既存プロジェクトを Google Drive に配置し、Colab ノートブック (`colab_faceswap.ipynb`) から Drive をマウントして起動する。モデルファイルも Drive に保存することでセッション再起動後も即起動できる。

---

## ファイル配置

```
Google Drive/MyDrive/faceswap/     ← 既存プロジェクトをそのまま配置
├── backend/
├── frontend/
├── templates/
│   └── basketball.mp4
├── models/
│   └── inswapper_128.onnx         ← 初回のみ HuggingFace からDL、以降 Drive から読む
├── colab_faceswap.ipynb           ← 今回作成
└── requirements.txt
```

---

## ノートブック構成（5セル）

### Cell 1: Google Drive マウント
```python
from google.colab import drive
drive.mount('/content/drive')
```

### Cell 2: 依存パッケージインストール
Windows 専用パッケージを除外し、GPU 推論用に `onnxruntime-gpu` を使用。
```bash
pip install fastapi==0.115.0 "uvicorn[standard]==0.32.0" python-multipart==0.0.12 \
    insightface==0.7.3 onnxruntime-gpu opencv-python-headless==4.10.0.84 \
    Pillow==11.0.0 aiofiles==24.1.0 sse-starlette==2.1.3 pyngrok
```

### Cell 3: プロジェクトパス設定 & モデル確認
ユーザーが `PROJECT_PATH` を1か所だけ編集すれば動く設計。
```python
import sys
from pathlib import Path

PROJECT_PATH = "/content/drive/MyDrive/faceswap"  # ← ここだけ変更
sys.path.insert(0, PROJECT_PATH)

model = Path(PROJECT_PATH) / "models" / "inswapper_128.onnx"
if not model.exists():
    print("モデルをダウンロード中... (約 554MB)")
    !huggingface-cli download ezioruan/inswapper_128.onnx inswapper_128.onnx \
        --local-dir {PROJECT_PATH}/models
    print("完了・Drive に保存しました")
else:
    print(f"モデル確認済み: {model}")
```

### Cell 4: uvicorn バックグラウンド起動
```python
import os, subprocess, time

os.chdir(PROJECT_PATH)
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "backend.main:app",
     "--host", "0.0.0.0", "--port", "8000"],
    env={**os.environ, "PYTHONPATH": PROJECT_PATH}
)
print("サーバー起動中... (モデルロードに15〜20秒)")
time.sleep(20)

import urllib.request
try:
    urllib.request.urlopen("http://localhost:8000/api/health", timeout=5)
    print("✅ サーバー起動完了")
except Exception as e:
    print(f"⚠️  起動確認失敗: {e}")
```

### Cell 5: ngrok トンネル → URL 表示
```python
from pyngrok import ngrok, conf

NGROK_TOKEN = "YOUR_NGROK_TOKEN"  # ← ngrok アカウントの authtoken を入力
conf.get_default().auth_token = NGROK_TOKEN

tunnel = ngrok.connect(8000)
print(f"\n🎉 アプリURL: {tunnel.public_url}\n")
print("このURLをブラウザで開いてください（スマホも可）")
```

---

## Windows 版との差分

| 項目 | Windows 版 | Colab 版 |
|------|-----------|---------|
| ONNX EP | CPU / DML / OpenVINO | **CUDA**（GPU高速） |
| パッケージ | onnxruntime + directml + openvino | **onnxruntime-gpu** のみ |
| トンネル | cloudflared | **pyngrok** |
| 起動スクリプト | start.bat | colab_faceswap.ipynb |

---

## 前提条件

- Google アカウント（Drive 利用）
- ngrok アカウント（無料、authtoken 取得が必要）
- Drive に `MyDrive/faceswap/` としてプロジェクトをアップロード済み

---

## 非対応項目（スコープ外）

- Colab Pro / Pro+ の自動判定
- セッション切断時の自動再接続
- 複数ユーザーの同時利用
