"""差分を GitHub Models API(無料枠)で分析し、重要度スコア付きの所見を生成する。

GITHUB_TOKEN 環境変数を使用(Actions 上では自動付与される)。
API が使えない場合は差分をそのまま所見として出力するフォールバック付き。
"""
import json
import os
import pathlib
import sys

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://models.github.ai/inference/chat/completions"
MODEL = os.environ.get("CI_MODEL", "openai/gpt-4o-mini")


def build_prompt(cfg: dict, diffs: dict) -> str:
    focus = "\n".join(f"- {f}" for f in cfg.get("analysis_focus", []))
    body = json.dumps(diffs, ensure_ascii=False, indent=2)
    return f"""あなたは競合分析アナリストです。以下は監視対象サイトの1週間の変更差分です。

分析の観点:
{focus}

差分データ:
{body}

以下のJSONのみを出力してください(前置き・コードブロック不要):
{{"findings": [{{"target": "対象名", "importance": 1-5の整数, "summary": "変更内容の要約",
"action": "推奨アクション(なければ'様子見')"}}], "weekly_summary": "全体総括を3文以内"}}"""


def call_api(prompt: str) -> dict | None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[warn] GITHUB_TOKEN 未設定。フォールバックします", file=sys.stderr)
        return None
    try:
        r = requests.post(
            API,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=60,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(text)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] AI分析失敗: {e}", file=sys.stderr)
        return None


def fallback(diffs: dict) -> dict:
    findings = [
        {
            "target": name,
            "importance": 3 if d["status"] == "changed" else 1,
            "summary": " / ".join(d["changes"][:3]) or d["status"],
            "action": "差分を目視確認" if d["status"] == "changed" else "様子見",
        }
        for name, d in diffs.items()
    ]
    return {"findings": findings, "weekly_summary": "AI分析が利用できなかったため機械的な差分一覧のみ。"}


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text(encoding="utf-8"))
    diffs = json.loads((ROOT / "reports" / "diff_latest.json").read_text(encoding="utf-8"))
    changed = {k: v for k, v in diffs.items() if v["status"] == "changed"}
    if changed:
        analysis = call_api(build_prompt(cfg, changed)) or fallback(changed)
    else:
        analysis = {"findings": [], "weekly_summary": "今週は監視対象に有意な変更なし。"}
    out = ROOT / "reports" / "analysis_latest.json"
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] findings={len(analysis.get('findings', []))}")


if __name__ == "__main__":
    main()
