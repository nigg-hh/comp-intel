# comp-intel — 週次競合インテリジェンス自動レポート

初期費用ゼロ(GitHub無料枠のみ)で稼働する、週1回人が判断するだけの市場監視システム。
初期対象ニッチ: **建設業向けバーティカルSaaS**

## 仕組み
```
毎週月曜 08:00 JST (GitHub Actions cron)
  ↓ collector.py   robots.txt を確認 → 許可された対象のみ取得しスナップショット保存
  ↓ differ.py      先週分との差分を抽出
  ↓ analyzer.py    GitHub Models API(無料枠)で重要度スコアリング
  ↓ reporter.py    Markdownレポート生成
  ↓ gh issue create → 人間はIssueを見て週1回判断するだけ
```

## セットアップ(初回のみ・約5分)
1. GitHubに新規リポジトリを作成し、このフォルダ一式をpush
2. Settings → Actions → General → Workflow permissions を
   「Read and write permissions」に設定
3. Actions タブから `weekly-comp-intel` を手動実行(workflow_dispatch)
   → 初回スナップショットを取得(この回は差分なし)
4. 翌週の自動実行から差分レポートのIssueが立ちます

## 運用(週1回・5分)
- 立ったIssueを開き、重要度🔴🟠の項目だけ確認して判断
- 監視対象の増減は `config/targets.yaml` を編集してcommitするだけ
- 別業種に切り替えたい場合も `targets.yaml` の差し替えのみ

## robots.txt の扱い
`collector.py` は取得前に必ず robots.txt を確認し、拒否されている対象は自動でスキップします
(ログに `[skip] robots.txt により除外` と出力)。
2026-07 時点の確認結果:

| ドメイン | 取得可否 |
|---|---|
| andpad.jp | 可 |
| aldagram.com | 可 |
| spiderplus.co.jp | **不可**(Disallow) — 対象に追加しないこと |

比較サイト・レビューサイト(ITreview、BOXIL 等)は利用規約でスクレイピングを
禁じている場合が多いため、対象に含めていません。

## 収益化への発展パス
1. 建設SaaS市場で1〜2ヶ月運用し、レポート品質を安定させる
2. 匿名化した「建設DX週次ウォッチ」をnote/Substackで無料公開 → 認知獲得
3. 建設SaaSベンダーや建設会社のDX担当者向けにカスタム版を月額提供(請求は当初手動)
4. 需要が確認できたらセルフサービスSaaS化(対象URL登録→自動レポート配信)

## 注意
- GitHub Models 無料枠にはレート制限あり。超過時は差分一覧のみのフォールバック動作
- 週1回・数ページの取得のため対象サイトへの負荷は軽微(5秒間隔でアクセス)
