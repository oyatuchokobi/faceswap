#!/bin/bash
set -e
cd "$(dirname "$0")"

source .venv/bin/activate

uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

echo "Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:8000

trap "kill $UVICORN_PID" EXIT
wait
