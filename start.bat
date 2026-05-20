@echo off
cd /d %~dp0

call .venv\Scripts\activate

start "uvicorn" /b python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

timeout /t 5 /nobreak

echo Starting Cloudflare Tunnel...
cloudflared tunnel --url http://localhost:8000

pause
