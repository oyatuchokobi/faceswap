@echo off
cd /d %~dp0

echo [1/4] GitHubから最新コードを取得中...
git pull origin main
if errorlevel 1 (
    echo 警告: git pull に失敗しました。ローカルのコードで続行します。
)

if not exist ".venv\" (
    echo [2/4] 初回セットアップ中...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
    echo [2/4] 依存パッケージを確認中...
    pip install -r requirements.txt -q
)

if not exist "models\inswapper_128.onnx" (
    echo [3/4] モデルをダウンロード中（初回のみ、約554MB）...
    python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='ezioruan/inswapper_128.onnx', filename='inswapper_128.onnx', local_dir='models/')"
) else (
    echo [3/4] モデル確認済み
)

echo [4/4] サーバーを起動中...
start "uvicorn" /b python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

timeout /t 5 /nobreak

echo Cloudflare Tunnel を起動中...
.\cloudflared.exe tunnel --url http://localhost:8000

pause
