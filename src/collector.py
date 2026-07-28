"""対象ページを取得しスナップショットとして保存する。週次cronで実行。

- 取得前に robots.txt を必ず確認し、拒否されている対象は自動でスキップする
- 連続アクセスの間隔を空け、対象サイトに負荷をかけない
"""
import hashlib
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from datetime import date

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "snapshots"
AGENT = "comp-intel-bot"
UA = {"User-Agent": f"{AGENT}/1.0 (weekly market monitoring)"}
DELAY_SEC = 5  # 対象サイトへの配慮

_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def robots_allows(url: str) -> bool:
    """robots.txt で許可されているか判定。取得失敗時は安全側に倒して True。"""
    parts = urllib.parse.urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{origin}/robots.txt")
        try:
            rp.read()
        except Exception:  # noqa: BLE001
            rp = None  # type: ignore[assignment]
        _robots_cache[origin] = rp
    rp = _robots_cache[origin]
    if rp is None:
        return True
    return rp.can_fetch(AGENT, url) and rp.can_fetch("*", url)


def clean_html(html: str) -> str:
    """タグ・スクリプトを除去して本文テキストに近づける(依存を増やさない簡易版)。"""
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=UA, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        return clean_html(r.text)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] fetch failed: {url}: {e}", file=sys.stderr)
        return None


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text(encoding="utf-8"))
    today = date.today().isoformat()
    for i, t in enumerate(cfg["targets"]):
        if not robots_allows(t["url"]):
            print(f"[skip] robots.txt により除外: {t['name']} ({t['url']})")
            continue
        if i:
            time.sleep(DELAY_SEC)
        text = fetch(t["url"])
        if text is None:
            continue
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", t["name"])
        d = SNAP / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{today}.txt").write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode()).hexdigest()[:12]
        print(f"[ok] {t['name']}: {len(text)} chars, sha={digest}")


if __name__ == "__main__":
    main()
