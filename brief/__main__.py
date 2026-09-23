"""入口：python -m brief [--out-dir DIR]。生成 index.html + archive/daily-brief-YYYY-MM-DD.html。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import LOCAL_TZ
from .fetch import fetch_all
from .render import render
from .select import select
from .translate import translate_titles


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=".", help="输出目录（仓库根目录）")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    articles, statuses = fetch_all(now)
    for s in statuses:
        print(f"[fetch] {'FAIL' if s.error and not s.count else 'ok  '} {s.count:3d}  {s.source}  {s.url}"
              + (f"  ({s.error})" if s.error else ""))

    results, stats = select(articles, now)
    chosen = [a for r in results for a in r.items]
    print(f"[select] {stats} -> 选中 {len(chosen)} 条")
    if not chosen:
        print("[error] 一条都没选出来，保留昨天的页面不覆盖", file=sys.stderr)
        return 1

    zh, failed = translate_titles([a.title for a in chosen])
    for a, t in zip(chosen, zh):
        a.title_zh = t or ""
    print(f"[translate] 失败 {failed} 条")

    html = render(results, statuses, stats, now, failed)
    out = Path(args.out_dir)
    (out / "archive").mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / "archive" / f"daily-brief-{now.astimezone(LOCAL_TZ):%Y-%m-%d}.html").write_text(html, encoding="utf-8")
    for r in results:
        print(f"[section] {r.name}: {len(r.items)}/{r.quota}  heat={r.heat:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
