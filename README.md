# FaceSwap Demo

ユーザーの顔をテンプレ動画に合成するWebデモアプリ。

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## モデル配置

`models/` に以下を手動配置:
- `inswapper_128.onnx` (HuggingFaceミラーから入手)
- InsightFace buffalo_l (初回起動で自動DL)

## デモ起動

1. `./start.sh` (Mac) または `start.bat` (Windows)
2. 出力に表示される `https://xxxxx.trycloudflare.com` を共有
3. ブラウザで開いて START
4. カメラ撮影 → ミニゲーム → 結果動画 → QRでスマホDL

`cloudflared` が PATH に必要(`brew install cloudflared` / Windows は GitHub releases)。
