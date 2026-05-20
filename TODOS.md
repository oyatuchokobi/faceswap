# TODOS — 後回し項目

## モデル関連
- [ ] **inswapper代替モデル検証** — 商用利用・外部公開する場合 SimSwap or GhostFaceShifter への移行を検討。`face_swap.py` の `swap_face()` 関数のみ差し替え

## インフラ関連
- [ ] **Named Tunnel化** — quick tunnel のURL揮発が運用上問題になった時点で対応。Cloudflareアカウント登録 → `cloudflared tunnel create` → DNS設定

## 機能拡張(必要に応じて)
- [ ] **複数テンプレート対応UI** — basketball以外のテンプレを追加する時のUI設計
- [ ] **ジョブ永続化** — 本番運用が見えてきたらSQLiteへ
- [ ] **観衆の歓声SE** — 処理中の没入感向上
- [ ] **シェアボタン**(SNS連携)
- [ ] **ウォーターマーク**(悪用抑止)
- [ ] **多言語対応**(EN/JP切替)
