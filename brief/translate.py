"""标题英译中：免费接口，不需要 API key。
顺序：Google gtx 整批 -> Google 词典扩展接口整批 -> 逐条（gtx、词典接口、MyMemory），都失败则保留英文原标题。
MyMemory 匿名每天约 5000 字符额度，只作最后兜底。"""

from __future__ import annotations

import time

import requests

from .config import HTTP_HEADERS

GOOGLE = "https://translate.googleapis.com/translate_a/single"
GOOGLE_DICT = "https://clients5.google.com/translate_a/t"
MYMEMORY = "https://api.mymemory.translated.net/get"


def _google(text: str) -> str:
    r = requests.post(GOOGLE, params={"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t"},
                      data={"q": text}, headers=HTTP_HEADERS, timeout=20)
    r.raise_for_status()
    return "".join(seg[0] for seg in r.json()[0] if seg and seg[0])


def _google_dict_batch(texts: list[str]) -> list[str]:
    """Chrome 词典扩展用的接口，一次请求可带多个 q，返回同样顺序的译文列表。"""
    r = requests.get(GOOGLE_DICT, params=[("client", "dict-chrome-ex"), ("sl", "en"), ("tl", "zh-CN")]
                     + [("q", t) for t in texts], headers=HTTP_HEADERS, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = [(d[0] if isinstance(d, list) else d) for d in data]
    if len(out) != len(texts) or not all(isinstance(x, str) and x.strip() for x in out):
        raise ValueError(f"词典接口返回条数不符：{len(out)}/{len(texts)}")
    return [x.strip() for x in out]


def _google_dict(text: str) -> str:
    return _google_dict_batch([text])[0]


def _mymemory(text: str) -> str:
    r = requests.get(MYMEMORY, params={"q": text, "langpair": "en|zh-CN"}, timeout=20)
    r.raise_for_status()
    data = r.json()
    out = (data.get("responseData") or {}).get("translatedText") or ""
    if data.get("responseStatus") != 200 or not out or "MYMEMORY WARNING" in out.upper():
        raise ValueError(f"MyMemory: {data.get('responseDetails') or data.get('responseStatus')}")
    return out


TIME_BUDGET = 180          # 翻译总共最多花 3 分钟，超时的保留英文
MAX_CONSECUTIVE_FAILS = 3  # 某个接口连续失败这么多次就不再用它（被限流时别一直等）

_fails = {"_google": 0, "_google_dict": 0, "_mymemory": 0}


def _one(text: str, deadline: float) -> str | None:
    for fn in (_google, _google_dict, _mymemory):
        if _fails[fn.__name__] >= MAX_CONSECUTIVE_FAILS or time.monotonic() > deadline:
            continue
        try:
            out = fn(text).strip()
            if out:
                _fails[fn.__name__] = 0
                return out
        except Exception as e:  # noqa: BLE001
            _fails[fn.__name__] += 1
            print(f"[translate] {fn.__name__} 失败：{type(e).__name__}: {str(e)[:100]}", flush=True)
            time.sleep(1)
    return None


def translate_titles(titles: list[str]) -> tuple[list[str | None], int]:
    """返回 (译文列表, 失败条数)。失败的位置是 None。先整批翻（换行分隔），条数对不上再逐条翻。"""
    result: list[str | None] = [None] * len(titles)
    deadline = time.monotonic() + TIME_BUDGET
    chunks, cur, size = [], [], 0
    for i, t in enumerate(titles):
        if cur and size + len(t) > 2500:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += len(t) + 1
    if cur:
        chunks.append(cur)

    gtx_ok = True
    for idxs in chunks:
        batch = [titles[i].replace("\n", " ") for i in idxs]
        if gtx_ok:
            try:
                lines = [ln.strip() for ln in _google("\n".join(batch)).split("\n")]
                if len(lines) == len(batch) and all(lines):
                    for i, ln in zip(idxs, lines):
                        result[i] = ln
                    continue
                print(f"[translate] gtx 整批行数不符（{len(lines)}/{len(batch)}）", flush=True)
            except Exception as e:  # noqa: BLE001
                gtx_ok = False
                _fails["_google"] = MAX_CONSECUTIVE_FAILS  # 整批都被限流，逐条也不用再试
                print(f"[translate] gtx 整批失败：{type(e).__name__}: {str(e)[:100]}", flush=True)
        try:
            for j in range(0, len(idxs), 20):
                sub = idxs[j:j + 20]
                for i, t in zip(sub, _google_dict_batch([titles[i] for i in sub])):
                    result[i] = t
            continue
        except Exception as e:  # noqa: BLE001
            print(f"[translate] 词典接口整批失败：{type(e).__name__}: {str(e)[:100]}", flush=True)
        for i in idxs:
            if result[i]:
                continue
            result[i] = _one(titles[i], deadline)
            time.sleep(0.3)
    return result, sum(r is None for r in result)
