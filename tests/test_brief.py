from datetime import date, datetime, timedelta, timezone

from brief.fetch import Article, parse_aila_clips, parse_rss, parse_toi_liveblog
from brief.render import render
from brief.select import classify, dedupe, is_soft, select

NOW = datetime(2026, 9, 23, 1, 0, tzinfo=timezone.utc)  # 北京时间 09:00


def art(title, source="Reuters", hours=5, sections=("ukraine", "global"), url=None, **kw):
    return Article(title=title, url=url or f"https://example.com/{abs(hash(title))}", source=source,
                   published=NOW - timedelta(hours=hours), sections=list(sections), **kw)


def test_soft_news_filtered():
    assert is_soft(art("Opinion: Why the West is losing Ukraine"))
    assert is_soft(art("What we know about the drone strike on Kyiv"))
    assert is_soft(art("Will the Fed cut rates again?"))
    assert is_soft(art("Russia strikes Kyiv overnight", url="https://x.com/analysis/2026/abc"))
    assert is_soft(art("Russia strikes Kyiv overnight", categories=["Opinion"]))
    assert not is_soft(art("Russian missile strike kills 12 in Kyiv"))


def test_dedupe_keeps_most_authoritative():
    a = art("Russian missile strike kills 12 in Kyiv, officials say", source="Kyiv Post")
    b = art("Russian missile strike on Kyiv kills 12, officials say", source="Reuters")
    c = art("Nvidia unveils new AI chip for data centers", sections=("ai_companies",))
    out = dedupe([a, b, c])
    assert len(out) == 2
    rep = next(x for x in out if "Kyiv" in x.title)
    assert rep.source == "Reuters" and rep.cluster_size == 2


def test_classify_requires_ai():
    ai = art("OpenAI signs data center power deal", sections=("ai_companies", "ai_infra", "frontier"))
    assert classify(ai) in {"ai_companies", "ai_infra"}
    not_ai = art("Hospital chain reports record profit", sections=("ai_industry",))
    assert classify(not_ai) is None
    iran = art("Iran rejects US demand on uranium enrichment", sections=("iran", "israel"))
    assert classify(iran) == "iran"


def test_select_windows_and_headlines():
    arts = [art("Russian drone attack hits Kharkiv power station", hours=3),
            art("EU agrees new sanctions package on Russian oil exports", hours=4),
            art("Ukraine retakes village near Pokrovsk, army says", hours=5)]
    old = art("Ukraine and Russia hold prisoner exchange talks in Istanbul", hours=24 * 4 + 2)
    too_old = art("Zelensky meets European leaders in Brussels summit", hours=24 * 10)
    results, stats = select(arts + [old, too_old], NOW)
    ua = next(r for r in results if r.key == "ukraine")
    assert len(ua.items) == 4 and ua.items[0].headline
    assert any(a.age_days == 4 for a in ua.items)
    assert stats["too_old"] == 1
    israel = next(r for r in results if r.key == "israel")
    assert israel.insufficient and not israel.items

    html = render(results, [], stats, NOW, 0)
    assert "超出标准窗口 3 天" in html and "本板块本次覆盖不足" in html and '<li class="lead">' in html


RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Nvidia &amp; AMD unveil chips</title><link>https://techcrunch.com/2026/09/22/a/</link>
<pubDate>Tue, 22 Sep 2026 14:00:00 +0000</pubDate><category>AI</category><description>&lt;p&gt;Body&lt;/p&gt;</description></item>
</channel></rss>"""


def test_parse_rss():
    src = dict(name="TechCrunch", sections=["ai_companies"])
    (a,) = parse_rss(RSS, src)
    assert a.title == "Nvidia & AMD unveil chips" and a.summary == "Body" and a.categories == ["AI"]
    assert a.published == datetime(2026, 9, 22, 14, tzinfo=timezone.utc)


def test_parse_toi_and_aila():
    toi = b"""<div class="liveblog-entry"><span class="date">9:15 pm</span>
      <h4><a href="https://www.timesofisrael.com/liveblog_entry/iran-says-talks-over/">Iran says nuclear talks with US are over</a></h4></div>"""
    (a,) = parse_toi_liveblog(toi, date(2026, 9, 22), dict(name="The Times of Israel", sections=["iran"]))
    assert a.published.hour == 21 and not a.date_only

    aila = b"""<a href="https://apnews.com/article/xyz">Judge blocks deportation flights to third countries</a>
      <a href="https://someblog.com/p">Random blog post about immigration policy here</a>"""
    (b,) = parse_aila_clips(aila, date(2026, 9, 22), dict(name="AILA", sections=["immigration"]))
    assert b.source == "AP" and b.date_only


def test_real_misses_from_first_run():
    # 2026-09-23 首次实跑漏网的条目
    assert is_soft(art("Prices go up in 7 days — get your Disrupt tickets now", source="TechCrunch"))
    assert is_soft(art("Before blaming [INSERT ISSUE HERE] on immigrants, remember what migrants did for "
                       "Australia | Jess Harwood", source="The Guardian"))
    assert is_soft(art("Neutral venue and no away fans - how Israel v Republic of Ireland became so contentious",
                       source="BBC"))
    pk = art("Pakistan's latest Trump bet is a drone firm that already sold to India", source="Al Jazeera",
             sections=("iran", "israel", "ukraine", "immigration", "global"),
             summary="The company previously supplied drones used by Israel.")
    assert classify(pk) is None


def test_rebalance_fills_ai_general():
    ai_sections = ("ai_companies", "ai_general", "ai_industry", "ai_infra", "frontier")
    company_titles = [
        "Nvidia unveils Blackwell successor GPU", "OpenAI launches cheaper GPT model", "Anthropic releases new Claude",
        "Meta opens Llama weights to developers", "AMD ships MI500 accelerator", "Qualcomm debuts AI phone chips",
        "Mistral raises funding from Nvidia", "xAI rolls out Grok update", "Perplexity adds shopping assistant",
        "Broadcom wins custom chip order from Google", "Alibaba expands DeepSeek rival Qwen"]
    arts = [art(t + " AI", source="TechCrunch", sections=ai_sections, hours=2 + i)
            for i, t in enumerate(company_titles)]
    # 企业词更多、先归 AI 企业动态，但同时符合 AI 综合（政策/安全）
    dual = [art("OpenAI, Google and Microsoft back AI safety law", source="TechCrunch", sections=ai_sections),
            art("Nvidia and Meta lobby Congress on AI regulation", source="TechCrunch", sections=ai_sections)]
    results, _ = select(arts + dual, NOW)
    by = {r.key: r for r in results}
    assert len(by["ai_companies"].items) == 10
    assert {a.title for a in by["ai_general"].items} == {a.title for a in dual}
