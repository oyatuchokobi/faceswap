@echo off
cd /d %~dp0

if not exist ".venv\" (
    echo 初回セットアップを実行中...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
    echo セットアップ完了
) else (
    call .venv\Scripts\activate
)

if not exist "models\inswapper_128.onnx" (
    echo モデルをダウンロード中 ^(初回のみ、数分かかります^)...
    python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='ezioruan/inswapper_128.onnx', filename='inswapper_128.onnx', local_dir='models/')"
)

start "uvicorn" /b python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

timeout /t 5 /nobreak

echo Cloudflare Tunnel を起動中...
.\cloudflared.exe tunnel --url http://localhost:8000

pause
