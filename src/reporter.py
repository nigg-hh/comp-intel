"""分析結果から週次 Markdown レポートを生成する(GitHub Issue 本文にも使用)。"""
import json
import pathlib
from datetime import date

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
STARS = {5: "🔴", 4: "🟠", 3: "🟡", 2: "🟢", 1: "⚪"}


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text(encoding="utf-8"))
    analysis = json.loads(
        (ROOT / "reports" / "analysis_latest.json").read_text(encoding="utf-8")
    )
    today = date.today().isoformat()
    lines = [
        f"# 週次競合レポート [{cfg['niche']}] {today}",
        "",
        f"**総括**: {analysis.get('weekly_summary', '-')}",
        "",
    ]
    findings = sorted(
        analysis.get("findings", []), key=lambda f: -int(f.get("importance", 1))
    )
    if findings:
        lines += ["| 重要度 | 対象 | 変更内容 | 推奨アクション |", "|---|---|---|---|"]
        for f in findings:
            imp = int(f.get("importance", 1))
            lines.append(
                f"| {STARS.get(imp, '⚪')} {imp} | {f.get('target', '-')} "
                f"| {f.get('summary', '-')} | {f.get('action', '-')} |"
            )
    else:
        lines.append("変更は検出されませんでした。")
    lines += [
        "",
        "---",
        "## 判断してください(週1回の人間の作業)",
        "- [ ] アクションを実行する項目に✅、対応後このIssueをクローズ",
        "- [ ] 監視対象の追加/削除が必要なら `config/targets.yaml` を編集",
    ]
    out = ROOT / "reports" / f"report_{today}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    # Actions から参照する固定パスにもコピー
    (ROOT / "reports" / "report_latest.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] {out}")


if __name__ == "__main__":
    main()
