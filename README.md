# FaceSwap Demo

ユーザーの顔を `templates/target.mp4` テンプレ動画に合成して、QRコードでスマホDLできる Web デモアプリ。

## ステータス

**実装は完了**(2026-05-20)。Plan Task 0-19 全コミット済み、`pytest` 25/25 passed。
残るは別マシンでの**手動 E2E 動作確認のみ**。

最新コミット: `637b224 docs: add TODOS for deferred items`

## 別マシンで再開するには(これだけ読めばOK)

### 1. リポジトリ取得

```bash
git clone https://github.com/oyatuchokobi/faceswap.git
cd faceswap
```

### 2. Python 環境

**Mac (M3 / Apple Silicon)**:
```bash
# Homebrew の python3.11/3.12 は libexpat エラーで壊れがち。uv 製 Python を推奨:
uv venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows ノート(本番)**:
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` には platform 別分岐があるので `onnxruntime-directml` (Windows) / `onnxruntime-openvino` (Linux/Windows) が自動で入る。Mac は CPU EP のみ。

### 3. モデル配置

`models/inswapper_128.onnx`(554MB)が必要。配布停止モデルなので HuggingFace ミラーから:

```bash
# 例(変更されている可能性あり):
huggingface-cli download ezioruan/inswapper_128.onnx inswapper_128.onnx --local-dir models
```

または手動で `models/inswapper_128.onnx` に置く。

InsightFace `buffalo_l`(検出+認識モデル)は初回起動で `~/.insightface/models/` に自動DL(~275MB、数十秒)。

### 4. cloudflared

URL 公開用:
- Mac: `brew install cloudflared`
- Windows: https://github.com/cloudflare/cloudflared/releases から `.exe` を DL、PATH に配置

### 5. テンプレ前処理キャッシュ(任意、初回起動で自動生成)

`templates/target/` にフレーム展開 + `faces_cache.pkl` が無い場合、初回起動時に自動生成(~1分)。

### 6. デモ起動

```bash
./start.sh        # Mac
start.bat         # Windows
```

出力に `https://xxxxx.trycloudflare.com` が表示される → 別端末/スマホから開いて:

1. START
2. カメラ撮影(またはアップロード `?mode=stg` クエリ)
3. ミニゲーム + バックエンド処理(30秒〜1分)
4. 結果動画再生 + QRコード表示
5. スマホでQR読み込み → MP4 ダウンロード

### 7. テスト走らせる

```bash
source .venv/bin/activate
pytest -v
```

期待: 25 passed(初回 E2E テストは cache 生成のため 3-5 分かかる)

## デモ当日の流れ

1. `start.bat`（Windows）または Colab で起動
2. コンソール/Cell 6 に表示された URL を参加者に共有（QR化 or LINE等）
3. 参加者: URL開く → START → カメラ撮影 → ミニゲーム待機 → 結果動画 → QRでスマホDL
4. 終了: コンソールを閉じる（または Colab: `Runtime` → `Disconnect and delete runtime`）

> `/?mode=stg` を URL 末尾に付けるとカメラなし・画像アップロードのテストモードになる。

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| 顔が検出されない | 明るい場所で正面から大きく撮り直し |
| 処理が5分以上進まない | サーバーを再起動 |
| カメラが起動しない | ブラウザのカメラ許可を確認 / `?mode=stg` で画像ファイル代用 |
| cloudflared が開かない | `cloudflared.exe` が同フォルダにあるか確認 |
| Colab URL が変わった | 毎回変わる仕様。Cell 6 の最新 URL を共有し直す |
| キャッシュが壊れた | `del templates\target\faces_cache.pkl` 後に再起動 |

## 既知のハマりどころ

1. **`insightface.app.common.Face` は pickle round-trip 不可** —
   `Face(dict)` の `__getattr__` が常に None を返す設計で、pickle protocol の `__setstate__` チェックが None.__call__ になり `TypeError: 'NoneType' object is not callable` を出す。
   対処: `backend/templates_init.py` で `bbox`/`kps`/`embedding` を dict として保存、ロード時に `Face(d)` で再構築している。**既存の faces_cache.pkl が古いフォーマットで壊れていたら削除して再生成**:
   ```bash
   rm templates/target/faces_cache.pkl
   ```

2. **`templates/target.mp4` は音声トラック無し** —
   `compose_video` は ffprobe で検出して `-an` で無音出力にフォールバックする。音声付きにしたければ target.mp4 を音声付き素材に差し替えれば自動で音声が乗る(コード変更不要)。

3. **Homebrew Python は壊れがち**(Mac) —
   `libexpat` 関連エラーで起動不能になる。`uv venv .venv` で uv 製 Python を使うのが安全。Windows の `python -m venv` は問題なし。

4. **初回 E2E は遅い** —
   `templates/target/faces_cache.pkl` が無いと フレーム × 顔検出で 30秒〜1分。テストの `test_swap_video_end_to_end` は 3-5分かかる(顔検出 + フレーム swap + ffmpeg compose)。

## プロジェクト構成

```
backend/
  config.py             # パスと定数(TTL=600s, timeout=120s 等)
  ep_selector.py        # onnxruntime EP 自動判定(CUDA/DML/OpenVINO/CPU)
  jobs.py               # JobManager(in-memory dict、SQLite 化は YAGNI)
  face_swap.py          # 顔検出/スワップ + E2E オーケストレータ swap_video_job
  templates_init.py     # フレーム抽出 + 顔検出キャッシュ
  video.py              # ffmpeg ラッパ(extract_frames + compose_video)
  main.py               # FastAPI アプリ(/, /api/health, /api/swap, /api/job, /api/result, /api/download)
frontend/
  index.html            # 5 view(landing/capture/confirm/game/result)
  style.css
  app.js                # state machine(view 切替)
  camera.js             # カメラ取得 + stg アップロード
  minigame.js           # MediaPipe Pose + ドリブル/シュート判定
  progress.js           # SSE 購読 + ジョブ提出
  result.js             # 結果動画再生 + QR 生成
templates/
  target.mp4            # テンプレ動画(顔合成先、音声無し)
  shoot_3piece.mp4      # ミニゲーム参考動画(ループ再生)
  target/               # 抽出フレーム + faces_cache.pkl(初回自動生成)
models/
  inswapper_128.onnx    # 顔スワップモデル(手動配置)
tests/                  # pytest 25 件
docs/superpowers/
  specs/2026-05-20-faceswap-demo-design.md     # 設計仕様
  plans/2026-05-20-faceswap-demo.md            # 19 タスクの実装計画(参考、全完了済)
TODOS.md                # 後回し項目(SimSwap移行、Named Tunnel化 等)
start.sh / start.bat    # 起動スクリプト(uvicorn + cloudflared)
```

## 設計の根拠

「無料 + 1分以内 + 神プレイ感」を全部満たすため、ローカル Python 推論 + ブラウザ MediaPipe Pose で構成。

- ホスト: Windows ノート単体運用想定
- 公開: cloudflared quick tunnel(無料、URL揮発許容)
- ジョブ TTL: 10分自動削除(`backend/main.py` の `_cleanup_after`)
- ミニゲーム解禁: 30秒経過 AND バックエンド完了の両方
- ワイプ: 顔キャプチャ画像を結果動画右下に overlay(`WIPE_WIDTH_RATIO=0.25`, `WIPE_MARGIN_PX=20`)

詳細は `docs/superpowers/specs/2026-05-20-faceswap-demo-design.md` 参照。

## Google Colab で動かす

`colab_faceswap.ipynb` を使うと T4 GPU で高速推論できる（Windows CPU より数倍速い）。

### ファイルの置き場所

| ファイル種別 | 置き場所 | 理由 |
|-------------|---------|------|
| ソースコード（backend/ frontend/ 等） | **GitHub** | 毎回 git pull で自動取得 |
| `inswapper_128.onnx`（554MB） | **Google Drive** | 初回だけDL、以降使いまわし |
| テンプレートフレームキャッシュ | **Google Drive** | 生成に数分かかるため使いまわし |
| `colab_faceswap.ipynb` | **GitHub** | Colab から直接開ける |

手元でファイルを用意したり Drive にアップロードする必要はない。ノートブックが全部自動でやる。

### 必要なもの

- **Google アカウント**（Drive マウント用）のみ。トークン登録不要。

### 初回セットアップ

1. [colab_faceswap.ipynb を Colab で開く](https://colab.research.google.com/github/oyatuchokobi/faceswap/blob/main/colab_faceswap.ipynb)
2. `Runtime` → `Change runtime type` → **T4 GPU** を選択して保存（**必ず保存ボタンを押す**）
3. `Runtime` → `Run all`

初回は以下が自動で走る（合計 5〜10 分）:
- GitHub からコードをクローン
- Drive に `faceswap-data/` フォルダを作成してシンボリックリンクを設定
- pip install
- `inswapper_128.onnx`（554MB）を Drive にダウンロード
- uvicorn 起動 → cloudflared でトンネル開通

4. Cell 6 に表示された URL をブラウザ/スマホで開けば使える

### 2回目以降

Drive にモデルとキャッシュが残っているので手順 1〜3 の後 `Run all` するだけ（3〜5分で起動）。

> 無料 Colab はアイドル 90 分でセッションが切れる。切れたら `Run all` で再起動（モデル再DL不要）。

### Windows 版との違い

| 項目 | Windows | Colab |
|------|---------|-------|
| 推論EP | CPU / DirectML | **CUDA GPU** |
| トンネル | cloudflared | **cloudflared** |
| モデル保存 | ローカル | **Google Drive** |
| コード取得 | git pull（自動） | git pull（自動） |

> **注意:** 無料 Colab はアイドル 90 分でセッションが切れる。
> 切れた場合は `Runtime` → `Run all` で再実行（モデル再DL不要）。

## 後回し項目

`TODOS.md` 参照(inswapper ライセンス問題対応、Named Tunnel化、複数テンプレ UI 等)。
