"""标题英译中：免费接口，不需要 API key。Google 翻译网页接口为主，MyMemory 兜底，都失败则保留英文原标题。"""

from __future__ import annotations

import time

import requests

from .config import HTTP_HEADERS

GOOGLE = "https://translate.googleapis.com/translate_a/single"
MYMEMORY = "https://api.mymemory.translated.net/get"


def _google(text: str) -> str:
    r = requests.post(GOOGLE, params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t"},
                      data={"q": text}, headers=HTTP_HEADERS, timeout=20)
    r.raise_for_status()
    return "".join(seg[0] for seg in r.json()[0] if seg and seg[0])


def _mymemory(text: str) -> str:
    r = requests.get(MYMEMORY, params={"q": text, "langpair": "en|zh-CN"}, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = (data.get("responseData") or {}).get("translatedText") or ""
    if data.get("responseStatus") != 200 or not out or "MYMEMORY WARNING" in out.upper():
        raise ValueError(f"MyMemory: {data.get('responseDetails') or data.get('responseStatus')}")
    return out


def _one(text: str) -> str | None:
    for fn in (_google, _mymemory):
        for attempt in range(2):
            try:
                out = fn(text).strip()
                if out:
                    return out
            except Exception:  # noqa: BLE001
                time.sleep(1.5 * (attempt + 1))
    return None


def translate_titles(titles: list[str]) -> tuple[list[str | None], int]:
    """返回 (译文列表, 失败条数)。失败的位置是 None。先整批翻（换行分隔），条数对不上再逐条翻。"""
    result: list[str | None] = [None] * len(titles)
    chunks, cur, size = [], [], 0
    for i, t in enumerate(titles):
        if cur and size + len(t) > 2500:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += len(t) + 1
    if cur:
        chunks.append(cur)

    for idxs in chunks:
        batch = [titles[i].replace("\n", " ") for i in idxs]
        try:
            lines = [ln.strip() for ln in _google("\n".join(batch)).split("\n")]
            if len(lines) == len(batch) and all(lines):
                for i, ln in zip(idxs, lines):
                    result[i] = ln
                continue
        except Exception:  # noqa: BLE001
            pass
        for i in idxs:
            result[i] = _one(titles[i])
            time.sleep(0.3)
    return result, sum(r is None for r in result)
