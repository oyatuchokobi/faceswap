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

## 起動

```bash
# Mac開発
./start.sh

# Windows本番
start.bat
```
