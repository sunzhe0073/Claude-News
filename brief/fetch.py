"""抓取：RSS/分类页、Times of Israel 当日 liveblog、AILA 每日移民新闻汇编。"""

from __future__ import annotations

import calendar
import html
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import HTTP_HEADERS, SOURCES, TRUSTED_DOMAINS

ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")
US_EASTERN = ZoneInfo("America/New_York")


@dataclass
class Article:
    title: str
    url: str
    source: str
    published: datetime | None          # 带时区
    summary: str = ""
    categories: list[str] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)   # 信源允许归入的板块
    dedicated: bool = False
    date_only: bool = False             # 只知道日期、不知道具体时刻
    # 以下由筛选阶段填写
    section: str | None = None
    score: float = 0.0
    cluster_size: int = 1
    age_days: int = 0
    headline: bool = False
    title_zh: str = ""


@dataclass
class FetchStatus:
    source: str
    url: str
    count: int
    error: str = ""


def _get(url: str, timeout: int = 15, tries: int = 2) -> requests.Response:
    last: Exception | None = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:  # noqa: BLE001 - 网络错误统一重试
            last = e
            if isinstance(e, requests.HTTPError) and e.response is not None and e.response.status_code == 404:
                break
            time.sleep(2 * (i + 1))
    raise last  # type: ignore[misc]


def _clean(text: str) -> str:
    text = BeautifulSoup(text or "", "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _struct_to_dt(st) -> datetime | None:
    if not st:
        return None
    return datetime.fromtimestamp(calendar.timegm(st), tz=timezone.utc)


def parse_rss(content: bytes, src: dict) -> list[Article]:
    feed = feedparser.parse(content)
    out = []
    for e in feed.entries:
        title = _clean(e.get("title", ""))
        link = e.get("link", "")
        if not title or not link:
            continue
        out.append(Article(
            title=title, url=link, source=src["name"],
            published=_struct_to_dt(e.get("published_parsed") or e.get("updated_parsed")),
            summary=_clean(e.get("summary", ""))[:600],
            categories=[t.get("term", "") for t in e.get("tags", []) if t.get("term")],
            sections=src["sections"], dedicated=src.get("dedicated", False),
        ))
    return out


def parse_category_html(content: bytes, base_url: str, src: dict) -> list[Article]:
    """RSS 失败时的兜底：从分类页 HTML 里找"标题链接 + <time datetime>"。没有日期的条目不要。"""
    soup = BeautifulSoup(content, "html.parser")
    host = urlparse(base_url).netloc
    out, seen = [], set()
    for a in soup.select("h2 a[href], h3 a[href]"):
        href = urljoin(base_url, a["href"])
        title = _clean(a.get_text())
        if len(title) < 15 or urlparse(href).netloc != host or href in seen:
            continue
        box = a
        t = None
        for _ in range(6):
            box = box.parent
            if box is None:
                break
            t = box.find("time", attrs={"datetime": True})
            if t:
                break
        if not t:
            continue
        try:
            dt = datetime.fromisoformat(t["datetime"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        seen.add(href)
        out.append(Article(title=title, url=href, source=src["name"], published=dt,
                           sections=src["sections"], dedicated=src.get("dedicated", False)))
    return out


_TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\s*([ap])\.?m\.?", re.I)


def parse_toi_liveblog(content: bytes, day, src: dict) -> list[Article]:
    """Times of Israel 当日 liveblog：每条快讯链接形如 /liveblog_entry/xxx/。"""
    soup = BeautifulSoup(content, "html.parser")
    out, seen = [], set()
    for a in soup.select('a[href*="/liveblog_entry/"]'):
        href = a["href"].split("#")[0]
        title = _clean(a.get_text())
        if len(title) < 15 or href in seen:
            continue
        seen.add(href)
        published, date_only = None, True
        box = a
        for _ in range(5):
            box = box.parent
            if box is None:
                break
            ts = box.find(attrs={"data-timestamp": True})
            if ts and ts["data-timestamp"].isdigit():
                published = datetime.fromtimestamp(int(ts["data-timestamp"]), tz=timezone.utc)
                date_only = False
                break
            m = _TIME_RE.search(box.get_text(" "))
            if m:
                h, mi, ap = int(m.group(1)) % 12, int(m.group(2)), m.group(3).lower()
                h += 12 if ap == "p" else 0
                published = datetime(day.year, day.month, day.day, h, mi, tzinfo=ISRAEL_TZ)
                date_only = False
                break
        if published is None:
            published = datetime(day.year, day.month, day.day, 12, 0, tzinfo=ISRAEL_TZ)
        out.append(Article(title=title, url=href, source=src["name"], published=published,
                           sections=src["sections"], dedicated=src.get("dedicated", False),
                           date_only=date_only))
    return out


def parse_aila_clips(content: bytes, day, src: dict) -> list[Article]:
    """AILA 每日移民新闻汇编：只收权威媒体域名的外链，来源显示为原媒体。"""
    soup = BeautifulSoup(content, "html.parser")
    out, seen = [], set()
    for a in soup.select("a[href]"):
        href = a["href"]
        host = urlparse(href).netloc.lower().removeprefix("www.")
        media = TRUSTED_DOMAINS.get(host) or next(
            (v for k, v in TRUSTED_DOMAINS.items() if host.endswith("." + k)), None)
        title = _clean(a.get_text())
        if not media or len(title) < 20 or href in seen:
            continue
        seen.add(href)
        out.append(Article(title=title, url=href, source=media,
                           published=datetime(day.year, day.month, day.day, 12, 0, tzinfo=US_EASTERN),
                           sections=src["sections"], dedicated=True, date_only=True))
    return out


def _fetch_one(src: dict, now: datetime) -> tuple[list[Article], list[FetchStatus]]:
    kind = src["kind"]
    results: list[Article] = []
    statuses: list[FetchStatus] = []

    if kind == "rss":
        try:
            arts = parse_rss(_get(src["url"]).content, src)
            if not arts:
                raise ValueError("RSS 为空")
            statuses.append(FetchStatus(src["name"], src["url"], len(arts)))
            results += arts
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"[:160]
            if src.get("html"):
                try:
                    arts = parse_category_html(_get(src["html"]).content, src["html"], src)
                    statuses.append(FetchStatus(src["name"], src["html"], len(arts), f"RSS 失败，改抓分类页（{err}）"))
                    results += arts
                except Exception as e2:  # noqa: BLE001
                    statuses.append(FetchStatus(src["name"], src["url"], 0, f"{err}；分类页也失败：{e2}"[:240]))
            else:
                statuses.append(FetchStatus(src["name"], src["url"], 0, err))
        return results, statuses

    # 按日期拼 URL 的页面：抓"当地今天 + 昨天"两页
    tz = ISRAEL_TZ if kind == "toi_liveblog" else US_EASTERN
    today = now.astimezone(tz).date()
    for day in (today, today - timedelta(days=1)):
        if kind == "toi_liveblog":
            url = src["url"].format(date=day.isoformat())
            parser = parse_toi_liveblog
        else:
            url = src["url"].format(month=day.strftime("%B").lower(), day=day.day, year=day.year)
            parser = parse_aila_clips
        try:
            arts = parser(_get(url).content, day, src)
            statuses.append(FetchStatus(src["name"], url, len(arts)))
            results += arts
        except Exception as e:  # noqa: BLE001
            statuses.append(FetchStatus(src["name"], url, 0, f"{type(e).__name__}: {e}"[:160]))
    return results, statuses


def fetch_all(now: datetime) -> tuple[list[Article], list[FetchStatus]]:
    articles: list[Article] = []
    statuses: list[FetchStatus] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for arts, sts in pool.map(lambda s: _fetch_one(s, now), SOURCES):
            articles += arts
            statuses += sts
    return articles, statuses
