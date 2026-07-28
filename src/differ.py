"""前回スナップショットとの差分を抽出し JSON で出力する。"""
import difflib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / "snapshots"


def latest_two(d: pathlib.Path) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    files = sorted(d.glob("*.txt"))
    if len(files) >= 2:
        return files[-2], files[-1]
    if len(files) == 1:
        return None, files[-1]
    return None, None


def diff_text(old: str, new: str, context: int = 40) -> list[str]:
    """単語レベルの差分から追加/削除ブロックを抽出。"""
    sm = difflib.SequenceMatcher(a=old.split(), b=new.split())
    changes: list[str] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        removed = " ".join(old.split()[i1:i2])[: context * 4]
        added = " ".join(new.split()[j1:j2])[: context * 4]
        if added:
            changes.append(f"+ {added}")
        if removed:
            changes.append(f"- {removed}")
    return changes[:50]  # レポート肥大化防止


def main() -> None:
    result = {}
    for d in sorted(SNAP.iterdir()):
        if not d.is_dir():
            continue
        prev, cur = latest_two(d)
        if cur is None:
            continue
        if prev is None:
            result[d.name] = {"status": "first_snapshot", "changes": []}
            continue
        changes = diff_text(
            prev.read_text(encoding="utf-8"), cur.read_text(encoding="utf-8")
        )
        result[d.name] = {
            "status": "changed" if changes else "no_change",
            "changes": changes,
        }
    out = ROOT / "reports" / "diff_latest.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v["status"] for k, v in result.items()}, ensure_ascii=False))
    if not result:
        print("[warn] no snapshots found", file=sys.stderr)


if __name__ == "__main__":
    main()
