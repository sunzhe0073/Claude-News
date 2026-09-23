"""筛选：剔除评论/软新闻 -> 跨媒体去重 -> 分板块 -> 按时间窗口和重要度挑条目 -> 标头条 -> 板块热度排序。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from .config import (AUTHORITY, EXTENDED_MAX_AGE, HARD_NEWS_RE, LOCAL_TZ, RELAXED_MAX_AGE, SECTIONS,
                     SOFT_CATEGORY_RE, SOFT_TITLE_RE, SOFT_URL_RE, STANDARD_MAX_AGE)
from .fetch import Article

_SOFT_TITLE = re.compile(SOFT_TITLE_RE, re.I)
_SOFT_URL = re.compile(SOFT_URL_RE, re.I)
_SOFT_CAT = re.compile(SOFT_CATEGORY_RE, re.I)
_HARD = re.compile(HARD_NEWS_RE, re.I)
_KW = {s["key"]: re.compile(s["keywords"], re.I) for s in SECTIONS}
_REQ = {s["key"]: re.compile(s["requires"], re.I) for s in SECTIONS if s.get("requires")}

_STOP = set("""a an the of to in on for and or but with from by at as is are was were be been has have had
its it this that these those after before over under into amid about new says said say will would could
may might than more most up out off not no his her their they he she we you i us""".split())


@dataclass
class SectionResult:
    key: str
    name: str
    group: str
    quota: int
    items: list[Article] = field(default_factory=list)
    heat: float = 0.0

    @property
    def insufficient(self) -> bool:
        return len(self.items) < self.quota / 2


def is_soft(a: Article) -> bool:
    title = a.title.strip()
    if a.source == "The Times of Israel" and "/liveblog" in a.url:
        return bool(_SOFT_TITLE.search(title)) and not title.lower().startswith("live")
    if _SOFT_TITLE.search(title) or _SOFT_URL.search(a.url):
        return True
    return any(_SOFT_CAT.search(c) for c in a.categories)


def _tokens(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", title.lower().replace("’", "'"))
    return {w.rstrip("s") if len(w) > 3 else w for w in words if w not in _STOP and len(w) > 1}


def similar(t1: set[str], t2: set[str]) -> bool:
    if len(t1) < 3 or len(t2) < 3:
        return False
    inter = len(t1 & t2)
    return inter / len(t1 | t2) >= 0.5 or inter / min(len(t1), len(t2)) >= 0.75


def dedupe(articles: list[Article]) -> list[Article]:
    """同一事件多家报道只留一条（权威度高、信息多的），cluster_size 记录报道家数。"""
    # 先按 URL 去重
    by_url: dict[str, Article] = {}
    for a in articles:
        by_url.setdefault(a.url.split("?")[0].rstrip("/"), a)
    arts = sorted(by_url.values(), key=lambda a: (-AUTHORITY.get(a.source, 2.0), -len(a.summary)))
    clusters: list[tuple[set[str], Article, set[str]]] = []
    for a in arts:
        tok = _tokens(a.title)
        for ctok, rep, srcs in clusters:
            if similar(tok, ctok):
                srcs.add(a.source)
                rep.cluster_size = len(srcs)
                # 代表条目不能归入的板块，从重复条目那里补上
                rep.sections = rep.sections + [s for s in a.sections if s not in rep.sections]
                break
        else:
            clusters.append((tok, a, {a.source}))
    return [rep for _, rep, _ in clusters]


def classify(a: Article) -> str | None:
    text_t, text_s = a.title, a.summary
    best, best_score = None, 0.0
    for key in a.sections:
        if key in _REQ and not (_REQ[key].search(text_t) or _REQ[key].search(text_s)):
            continue
        score = 2 * len(_KW[key].findall(text_t)) + 0.5 * min(len(_KW[key].findall(text_s)), 4)
        if score > best_score:
            best, best_score = key, score
    if best is None and a.dedicated and a.sections:
        key = a.sections[0]
        if key not in _REQ or _REQ[key].search(text_t + " " + text_s):
            return key
    # 至少标题命中一次，或摘要命中多次
    return best if best_score >= 1.0 else None


def age_days(a: Article, now: datetime) -> int | None:
    if a.published is None:
        return None
    return (now.astimezone(LOCAL_TZ).date() - a.published.astimezone(LOCAL_TZ).date()).days


def score(a: Article, now: datetime) -> float:
    hours = max((now - a.published).total_seconds() / 3600, 0) if a.published else 72
    s = AUTHORITY.get(a.source, 2.0)
    s += max(0.0, 2.0 - hours / 24)                  # 越新越高，48 小时后不再加分
    s += 1.5 * (a.cluster_size - 1)                  # 多家媒体都在报道
    s += 0.6 * min(len(_HARD.findall(a.title)), 3)   # 硬新闻信号词
    if a.section:
        s += 0.3 * min(len(_KW[a.section].findall(a.title)), 3)
    return s


def select(articles: list[Article], now: datetime) -> tuple[list[SectionResult], dict]:
    stats = {"fetched": len(articles), "soft": 0, "undated": 0, "too_old": 0, "future": 0}
    pool = []
    for a in articles:
        if is_soft(a):
            stats["soft"] += 1
            continue
        d = age_days(a, now)
        if d is None:
            stats["undated"] += 1
            continue
        if d < 0:  # 时区误差最多容忍 1 天
            if d < -1:
                stats["future"] += 1
                continue
            d = 0
        if d > EXTENDED_MAX_AGE:
            stats["too_old"] += 1
            continue
        a.age_days = d
        pool.append(a)

    pool = dedupe(pool)
    stats["after_dedupe"] = len(pool)

    buckets: dict[str, list[Article]] = {s["key"]: [] for s in SECTIONS}
    for a in pool:
        key = classify(a)
        if key:
            a.section = key
            a.score = score(a, now)
            buckets[key].append(a)

    results = []
    for s in SECTIONS:
        cands = sorted(buckets[s["key"]], key=lambda a: -a.score)
        chosen: list[Article] = []
        for limit in (STANDARD_MAX_AGE, RELAXED_MAX_AGE, EXTENDED_MAX_AGE):
            for a in cands:
                if len(chosen) >= s["quota"]:
                    break
                if a.age_days <= limit and a not in chosen:
                    chosen.append(a)
        chosen.sort(key=lambda a: -a.score)
        if chosen:
            chosen[0].headline = True
            if len(chosen) > 2 and (chosen[1].score >= 0.85 * chosen[0].score or chosen[1].cluster_size >= 2):
                chosen[1].headline = True
        fresh = [a for a in cands if a.age_days <= STANDARD_MAX_AGE]
        heat = sum(a.score for a in chosen[:5]) + 0.3 * len(fresh) + sum(a.cluster_size - 1 for a in fresh)
        results.append(SectionResult(s["key"], s["name"], s["group"], s["quota"], chosen, heat))

    results.sort(key=lambda r: -r.heat)
    return results, stats
