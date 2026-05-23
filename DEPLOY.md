# デプロイガイド

このアプリを外部公開するための手順書です。

---

## 環境の選択

| 環境 | GPU | セットアップ | 安定性 | 推奨用途 |
|------|-----|------------|--------|---------|
| **Google Colab** | T4 GPU（無料） | 簡単 | セッション最大12h | デモ・テスト |
| **Windows PC** | CPU / DirectML | 中程度 | 常時稼働可 | 本番運用 |

---

## A. Google Colab でデプロイ

### 必要なもの

- Google アカウント
- GitHub アカウント（リポジトリへのアクセス）
- ngrok アカウント（無料）→ [ngrok.com](https://ngrok.com)

### A-1. 初回セットアップ

**1. Google Drive に保存フォルダを作成**

Drive 上に `faceswap-data/` フォルダを作成します（自動で作られるので手動操作不要）。

**2. ngrok トークンを取得**

[dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) からトークンをコピーしてメモしておく。

**3. ノートブックを開く**

GitHub から `colab_faceswap.ipynb` を開く:

```
https://github.com/oyatuchokobi/faceswap
```

`colab_faceswap.ipynb` → `Open in Colab` ボタン、またはColabで `ファイル > GitHubからノートブックを開く`。

**4. GPU ランタイムを設定**

`Runtime` → `Change runtime type` → `T4 GPU` → 保存

**5. NGROK_TOKEN を設定**

Cell 3 を編集:
```python
NGROK_TOKEN = 'ngrok_xxxxxxxxxxxxxxxxxx'  # ← 取得したトークンに書き換え
```

**6. 全セル実行**

`Runtime` → `Run all`

初回は以下の処理が走ります（合計 5〜10 分）:
- GitHubからコードをクローン
- Drive に `faceswap-data/` フォルダを作成してシンボリックリンクを設定
- pip install
- `inswapper_128.onnx`（554MB）を Drive にダウンロード
- InsightFace `buffalo_l`（275MB）を自動ダウンロード
- テンプレート動画のフレーム抽出と顔検出キャッシュを生成

**7. URL を確認**

Cell 6 の出力に表示された URL がアプリのエンドポイントです:

```
🎉 アプリURL: https://xxxx-xx-xx.ngrok-free.app
```

### A-2. 2回目以降の起動

Drive にモデルとキャッシュが残っているため、初回より大幅に速くなります。

1. `colab_faceswap.ipynb` を Colab で開く
2. GPU ランタイムを確認（T4 GPU になっているか）
3. `Runtime` → `Run all`（3〜5分で起動完了）

> NGROK_TOKEN は Colab のシークレットに保存しておくと毎回入力不要になります:
> `🔑` アイコン → `NGROK_TOKEN` として追加 → Cell 3 を以下に変更:
> ```python
> from google.colab import userdata
> NGROK_TOKEN = userdata.get('NGROK_TOKEN')
> ```

### A-3. セッション切断からの復旧

Colab は一定時間アイドルでセッションが切断されます。

復旧手順:
1. Colab を開き直す（ランタイムは自動リセット）
2. `Runtime` → `Run all`（モデルは Drive にあるので再DL不要）

---

## B. Windows PC でデプロイ

### 必要なもの

- Windows 10/11（64bit）
- Python 3.11 以上
- ffmpeg（PATH に通っておくこと）
- cloudflared（同梱の `cloudflared.exe` を使用）

### B-1. 初回セットアップ

**1. リポジトリをクローン**

```bat
git clone https://github.com/oyatuchokobi/faceswap.git
cd faceswap
```

**2. ffmpeg のインストール（未インストールの場合）**

```bat
winget install ffmpeg
```

またはこちらから手動DL: https://ffmpeg.org/download.html

**3. start.bat を実行**

```bat
start.bat
```

初回は自動で以下を実行します:
- `.venv` 仮想環境を作成
- `pip install -r requirements.txt`
- `inswapper_128.onnx`（554MB）を `models/` にダウンロード
- uvicorn でサーバー起動
- cloudflared でトンネルを開く

> 初回のみ合計 5〜10 分かかります。

**4. URL を確認**

コンソールに以下のような行が表示されれば完了:

```
2024-XX-XX INFO  |  https://xxxx.trycloudflare.com
```

この URL をブラウザで開いて動作確認してください。

### B-2. 2回目以降の起動

`start.bat` をダブルクリックするだけです。

起動時間の目安:
- モデルロード（buffalo_l + inswapper）: 20〜40 秒
- テンプレートキャッシュ（既存）: 数秒

### B-3. 推論速度について

Windows での EP（実行プロバイダー）の優先順位:

| EP | 条件 | 推論速度 |
|----|------|---------|
| CUDA | NVIDIA GPU あり | 速い |
| DirectML | GPU あり（Intel/AMD/NVIDIA） | 中程度 |
| CPU | 上記なし | 遅い（1フレーム数秒） |

現在のマシンで使われている EP は起動ログで確認できます:
```
INFO: Selected ONNX providers: ['DmlExecutionProvider', 'CPUExecutionProvider']
```

---

## 動作確認

デプロイ後、以下の URL にアクセスして確認してください。

| エンドポイント | 期待するレスポンス |
|--------------|-----------------|
| `/api/health` | `{"status": "ok"}` |
| `/` | HTML ページが表示される |
| `/?mode=stg` | カメラなしで画像アップロードできるテストモード |

`/api/health` の確認:
```bash
curl https://your-url.ngrok-free.app/api/health
# → {"status":"ok"}
```

---

## ファイル構成（デプロイ時の役割）

```
faceswap/
├── backend/          # FastAPI サーバー（GitHub から取得）
├── frontend/         # Web UI（GitHub から取得）
├── templates/
│   ├── basketball.mp4          # テンプレ動画（GitHub から取得）
│   └── basketball/             # フレームキャッシュ（Drive/ローカルに保持）
├── models/
│   └── inswapper_128.onnx      # 推論モデル（Drive/ローカルに保持・gitignore済み）
├── jobs/                       # 処理中ジョブ（一時ファイル・gitignore済み）
├── start.bat                   # Windows 起動スクリプト
├── start.sh                    # Mac 起動スクリプト
└── colab_faceswap.ipynb        # Colab ノートブック
```

---

## トラブルシューティング

### `inswapper_128.onnx` のダウンロードが失敗する

HuggingFace のレート制限に引っかかることがあります。

対処:
```bash
huggingface-cli login  # アカウントでログインするとレート上限が上がる
huggingface-cli download ezioruan/inswapper_128.onnx inswapper_128.onnx --local-dir models/
```

### テンプレートのフレームキャッシュ生成でエラー

古い形式のキャッシュが残っている場合:

```bash
# Colab
rm /content/drive/MyDrive/faceswap-data/templates/basketball/faces_cache.pkl

# Windows
del templates\basketball\faces_cache.pkl
```

削除後、サーバーを再起動すると自動で再生成されます（約1分）。

### ngrok の URL が機能しない

- ngrok の無料プランは同時接続1セッションのみ。別のセッションで起動していないか確認
- Colab を再起動した場合は Cell 6 を再実行して新しい URL を取得

### cloudflared のトンネルが開かない（Windows）

```bat
# cloudflared.exe が同じフォルダにあるか確認
dir cloudflared.exe

# 手動でトンネルを開く
.\cloudflared.exe tunnel --url http://localhost:8000
```
