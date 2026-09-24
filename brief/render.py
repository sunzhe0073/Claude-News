"""生成 Techmeme 风格的单页 HTML。"""

from __future__ import annotations

from datetime import datetime
from html import escape

from .config import GROUPS, LOCAL_TZ, MAX_AGE_HOURS
from .fetch import Article, FetchStatus
from .select import SectionResult

WEEKDAYS = "一二三四五六日"

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6f6c66;--rule:#e2dfd8;--accent:#a4161a;--accent-bg:#fbeeee;
--warn:#8a5a00;--warn-bg:#fff4dc;--link:#1d1d1b;--visited:#5b4f8a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#e9e6df;--muted:#9a968d;
--rule:#2e2d2a;--accent:#ff6b6b;--accent-bg:#2a1a1a;--warn:#f0b64a;--warn-bg:#2b2413;--link:#e9e6df;--visited:#b3a6e6}}
:root[data-theme="dark"]{--bg:#161615;--fg:#e9e6df;--muted:#9a968d;--rule:#2e2d2a;--accent:#ff6b6b;
--accent-bg:#2a1a1a;--warn:#f0b64a;--warn-bg:#2b2413;--link:#e9e6df;--visited:#b3a6e6}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:Georgia,"Noto Serif SC","Source Han Serif SC","Songti SC","STSong",serif;line-height:1.5}
.wrap{max-width:860px;margin:0 auto;padding:28px 16px 60px}
.mono,.meta,header .sub,nav,footer{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
header{border-bottom:2px solid var(--fg);padding-bottom:10px;margin-bottom:6px}
header h1{font-size:28px;margin:0;letter-spacing:.02em}
header .sub{color:var(--muted);font-size:12px;margin-top:4px}
nav{font-size:12px;color:var(--muted);padding:8px 0 4px;border-bottom:1px solid var(--rule);line-height:1.9}
nav a{color:var(--muted);text-decoration:none;margin-right:12px;white-space:nowrap}
nav a:hover{color:var(--accent)}
nav b{color:var(--fg);margin-right:8px;font-weight:600}
h2.group{font-size:13px;letter-spacing:.2em;margin:34px 0 0;padding:6px 0;border-bottom:2px solid var(--fg);
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;text-transform:uppercase}
section{padding-top:14px}
h3{font-size:18px;margin:6px 0 6px;display:flex;align-items:baseline;gap:10px}
h3 .count{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11px;color:var(--muted);font-weight:normal}
.warn{background:var(--warn-bg);color:var(--warn);font-size:12px;padding:6px 10px;margin:4px 0 8px;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;border-left:3px solid var(--warn)}
ul{list-style:none;margin:0;padding:0}
li{padding:7px 0 7px 12px;border-bottom:1px solid var(--rule);border-left:3px solid transparent}
li a.t{color:var(--link);text-decoration:none;font-size:15.5px}
li a.t:visited{color:var(--visited)}
li a.t:hover{text-decoration:underline}
li.lead{border-left-color:var(--accent);background:var(--accent-bg)}
li.lead a.t{font-size:18px;font-weight:700}
li.lead a.t::before{content:"★ ";color:var(--accent)}
.meta{display:block;font-size:11.5px;color:var(--muted);margin-top:2px}
.tag{font-size:10.5px;padding:0 4px;border:1px solid currentColor;border-radius:2px;margin-left:6px;color:var(--warn)}
.empty{color:var(--muted);font-size:14px;padding:8px 0 8px 12px}
footer{margin-top:40px;border-top:2px solid var(--fg);padding-top:10px;font-size:11.5px;color:var(--muted)}
footer h4{font-size:12px;color:var(--fg);margin:14px 0 4px}
footer ul li{border:0;padding:1px 0}
footer a{color:var(--muted)}
footer details{margin-top:10px}
@media (max-width:560px){header h1{font-size:23px}li a.t{font-size:15px}li.lead a.t{font-size:16.5px}}
"""


def _fmt_time(a: Article) -> str:
    if a.published is None:
        return ""
    t = a.published.astimezone(LOCAL_TZ)
    return t.strftime("%m-%d") if a.date_only else t.strftime("%m-%d %H:%M")


def _item(a: Article) -> str:
    cls = ' class="lead"' if a.headline else ""
    title = a.title_zh or a.title
    tags = ""
    if not a.title_zh:
        tags += '<span class="tag">未翻译</span>'
    meta = " · ".join(x for x in (escape(a.source), _fmt_time(a)) if x)
    return (f'<li{cls}><a class="t" href="{escape(a.url, quote=True)}" title="{escape(a.title, quote=True)}" '
            f'target="_blank" rel="noopener">{escape(title)}</a>'
            f'<span class="meta">{meta}{tags}</span></li>')


def _section(r: SectionResult) -> str:
    out = [f'<section id="{r.key}"><h3>{escape(r.name)}<span class="count">{len(r.items)}/{r.quota}</span></h3>']
    if r.insufficient:
        out.append(f'<div class="warn">⚠ 本板块本次覆盖不足（{len(r.items)}/{r.quota}）：'
                   f'时间窗口内符合条件的硬新闻不够，宁缺毋滥</div>')
    if r.items:
        out.append("<ul>" + "".join(_item(a) for a in r.items) + "</ul>")
    else:
        out.append('<div class="empty">本次未抓到符合条件的硬新闻。</div>')
    out.append("</section>")
    return "".join(out)


def render(results: list[SectionResult], statuses: list[FetchStatus], stats: dict, now: datetime,
           untranslated: int) -> str:
    local = now.astimezone(LOCAL_TZ)
    total = sum(len(r.items) for r in results)
    quota = sum(r.quota for r in results)
    date_str = f"{local:%Y-%m-%d} 星期{WEEKDAYS[local.weekday()]}"

    nav, body = [], []
    for gkey, gname in GROUPS:
        rs = [r for r in results if r.group == gkey]
        nav.append(f"<div><b>{escape(gname)}</b>" + "".join(
            f'<a href="#{r.key}">{escape(r.name)} {len(r.items)}</a>' for r in rs) + "</div>")
        body.append(f'<h2 class="group">{escape(gname)}</h2>' + "".join(_section(r) for r in rs))

    foot = [f"<div>生成于 {local:%Y-%m-%d %H:%M}（北京时间）· 共 {total}/{quota} 条 · "
            f"时间窗口：最近 {MAX_AGE_HOURS} 小时· 板块按当日热度排序 · ★ 为板块头条</div>"]
    short = [r for r in results if len(r.items) < r.quota]
    if short:
        foot.append("<h4>数量不足的板块</h4><div>" + "；".join(
            f"{escape(r.name)} {len(r.items)}/{r.quota}" for r in short) + "</div>")
    if untranslated:
        foot.append(f"<h4>翻译</h4><div>{untranslated} 条标题免费翻译接口失败，保留英文原标题。</div>")
    failed = [s for s in statuses if s.error]
    foot.append(
        "<details><summary>抓取明细</summary>"
        f"<div>抓到 {stats['fetched']} 条 · 剔除评论/软新闻 {stats['soft']} 条 · 无日期 {stats['undated']} 条 · "
        f"过旧 {stats['too_old']} 条 · 去重后 {stats.get('after_dedupe', 0)} 条</div><ul>" + "".join(
            f'<li>{"✗" if s.error and not s.count else "✓"} {escape(s.source)} · {s.count} 条 · '
            f'<a href="{escape(s.url, quote=True)}">{escape(s.url)}</a>'
            f'{" · " + escape(s.error) if s.error else ""}</li>' for s in statuses) + "</ul></details>")
    if failed:
        foot.insert(1, f"<div>⚠ {len([s for s in failed if not s.count])} 个信源本次抓取失败，见下方抓取明细。</div>")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>每日新闻简报 {local:%Y-%m-%d}</title>
<meta name="description" content="每日国际要闻与前沿科技简报（中文标题，原文链接）">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header><h1>每日新闻简报</h1>
<div class="sub">{date_str} · 更新于 {local:%H:%M}（北京时间）· 共 {total}/{quota} 条 · 点击标题阅读原文</div></header>
<nav>{"".join(nav)}</nav>
{"".join(body)}
<footer>{"".join(foot)}</footer>
</div>
</body>
</html>
"""
