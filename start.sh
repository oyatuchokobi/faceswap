#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "[1/4] GitHubから最新コードを取得中..."
git pull origin main || echo "警告: git pull に失敗しました。ローカルのコードで続行します。"

if [ ! -d ".venv" ]; then
    echo "[2/4] 初回セットアップ中..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
    echo "[2/4] 依存パッケージを確認中..."
    pip install -r requirements.txt -q
fi

if [ ! -f "models/inswapper_128.onnx" ]; then
    echo "[3/4] モデルをダウンロード中（初回のみ、約554MB）..."
    python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='ezioruan/inswapper_128.onnx', filename='inswapper_128.onnx', local_dir='models/')"
else
    echo "[3/4] モデル確認済み"
fi

echo "[4/4] サーバーを起動中..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

echo "Cloudflare Tunnel を起動中..."
cloudflared tunnel --url http://localhost:8000

trap "kill $UVICORN_PID" EXIT
wait
