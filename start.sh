#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "初回セットアップを実行中..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    echo "セットアップ完了"
else
    source .venv/bin/activate
fi

if [ ! -f "models/inswapper_128.onnx" ]; then
    echo "モデルをダウンロード中（初回のみ、数分かかります）..."
    python3 -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='ezioruan/inswapper_128.onnx', filename='inswapper_128.onnx', local_dir='models/')"
fi

uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

echo "Cloudflare Tunnel を起動中..."
cloudflared tunnel --url http://localhost:8000

trap "kill $UVICORN_PID" EXIT
wait
