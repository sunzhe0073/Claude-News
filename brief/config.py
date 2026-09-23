"""板块、信源、关键词配置。规则见 docs/SPEC.md。"""

from datetime import timedelta, timezone

# 页面日期、"今天/昨天"一律按北京时间（UTC+8）判断
LOCAL_TZ = timezone(timedelta(hours=8), "UTC+8")

# 时间窗口（按北京时间的日期差，0=今天，1=昨天）
STANDARD_MAX_AGE = 1   # 标准窗口：今天 + 昨天
RELAXED_MAX_AGE = 3    # 允许往前多找 1-2 天
EXTENDED_MAX_AGE = 6   # 仍不够时适度再往前（3-5 天），这部分会在页面上标注超窗天数

GROUPS = [
    ("geo", "地缘政治 / 冲突"),
    ("tech", "前沿科技"),
]

AI_RE = r"\bAI\b|\bA\.I\.|artificial intelligence|machine learning|\bLLMs?\b|chatbot|generative|\bgenAI\b|\bAGI\b|neural"

# key, 分组, 中文名, 条数, 标题/摘要关键词（正则，大小写不敏感）, 必须同时满足的正则
SECTIONS = [
    dict(key="ukraine", group="geo", name="俄乌战争", quota=5,
         keywords=r"ukrain|kyiv|kiev|russia|kremlin|putin|zelensky|donbas|donetsk|luhansk|crimea|kharkiv|zaporizh|kherson|odesa|moscow|sumy|pokrovsk|drone attack"),
    dict(key="israel", group="geo", name="哈以战争", quota=5,
         keywords=r"gaza|hamas|israel|\bidf\b|west bank|hezbollah|netanyahu|hostage|lebanon|houthi|palestin|rafah|jerusalem|tel aviv"),
    dict(key="iran", group="geo", name="美伊局势", quota=5,
         keywords=r"\biran|tehran|khamenei|\birgc\b|hormuz|pezeshkian|araghchi|uranium enrichment|snapback"),
    dict(key="immigration", group="geo", name="欧美移民新闻", quota=5,
         keywords=r"immigra|migrant|migration|asylum|deport|\bICE\b|border patrol|\bCBP\b|uscis|\bvisa|h-1b|refugee|green card|small boats|channel crossing|undocumented|citizenship"),
    dict(key="global", group="geo", name="全球格局观察", quota=10,
         keywords=r"china|chinese|beijing|\bxi\b|tariff|trade war|trade deal|export control|federal reserve|\bfed\b|inflation|interest rate|stocks?\b|markets?\b|treasur|bond yield|economy|\bgdp\b|recession|\bimf\b|\becb\b|oil price|yuan|dollar|wall street|central bank|spacex|nasa|satellite|rocket|\blaunch|orbit|starlink|lunar|\bmoon\b|\bmars\b|blue origin|\besa\b|space station|rare earth"),

    dict(key="ai_companies", group="tech", name="AI 代表性企业动态", quota=10,
         keywords=r"openai|anthropic|deepmind|gemini|\bmeta\b|\bxai\b|grok|nvidia|\bamd\b|microsoft|mistral|chatgpt|claude|llama|\bgpu|chips?\b|chipmaker|tsmc|intel\b|perplexity|hugging face|qualcomm|broadcom|deepseek|alibaba|sam altman|copilot|google",
         requires=AI_RE + r"|chips?\b|\bgpu|nvidia|openai|anthropic|deepmind|chatgpt"),
    dict(key="ai_general", group="tech", name="AI 综合", quota=10,
         keywords=r"regulat|\blaw\b|legislat|\bbill\b|policy|congress|senate|\beu\b|ai act|safety|ethic|lawsuit|sue[sd]?\b|copyright|court|\bjobs?\b|workers|layoff|employ|labor|research|study|paper|scientists|researchers|benchmark|governor|white house|ban\b|children|teen",
         requires=AI_RE),
    dict(key="ai_industry", group="tech", name="AI 与产业结合", quota=5,
         keywords=r"health|hospital|medical|patient|drug|pharma|bank|financ|insur|fintech|education|school|student|manufactur|factory|retail|legal|lawyer|agricult|farm|logistic|supply chain|customer service|enterprise|accounting|biotech",
         requires=AI_RE),
    dict(key="ai_infra", group="tech", name="AI 能源与基础设施", quota=5,
         keywords=r"data ?cent|power|electric|grid|energy|gigawatt|megawatt|\bgw\b|\bmw\b|nuclear|compute|cooling|hyperscal|cluster|supercomputer|utilit|turbine|gas plant",
         requires=AI_RE + r"|data ?cent|hyperscal|compute"),
    dict(key="frontier", group="tech", name="前沿科技综合", quota=10,
         keywords=r"fusion|nuclear|battery|batteries|solar|\bev\b|\bevs\b|electric vehicle|robotaxi|autonomous|self-driving|driverless|waymo|zoox|tesla|robot|humanoid|hydrogen|geothermal|reactor|lidar|drone|quantum|clean energy|wind"),
]
SECTION_BY_KEY = {s["key"]: s for s in SECTIONS}

# 信源权威度（用于去重时选代表条目、排序加分）
AUTHORITY = {
    "Reuters": 3.0, "AP": 3.0, "BBC": 3.0, "New York Times": 3.0, "Wall Street Journal": 3.0,
    "Bloomberg": 3.0, "Financial Times": 3.0, "Washington Post": 2.8, "The Guardian": 2.7,
    "CNN": 2.6, "Al Jazeera": 2.6, "The Times of Israel": 2.6, "Kyiv Independent": 2.6,
    "Kyiv Post": 2.3, "Politico": 2.6, "TechCrunch": 2.3, "MIT Technology Review": 2.5,
    "IEEE Spectrum": 2.3, "SpaceNews": 2.3, "DatacenterDynamics": 2.2, "AILA 汇编": 2.0,
}

TC = "https://techcrunch.com/category/{}/feed/"

# 信源：kind=rss / toi_liveblog / aila_clips
# sections=这个信源允许归入的板块；dedicated=True 表示不需要关键词命中也归入第一个板块
SOURCES = [
    # 俄乌
    dict(name="Kyiv Independent", kind="rss", url="https://kyivindependent.com/tag/war-update/rss/",
         html="https://kyivindependent.com/tag/war-update/", sections=["ukraine"], dedicated=True),
    dict(name="Kyiv Independent", kind="rss", url="https://kyivindependent.com/rss/", sections=["ukraine", "global"]),
    dict(name="Kyiv Post", kind="rss", url="https://www.kyivpost.com/feed", sections=["ukraine"]),
    # 哈以 / 美伊
    dict(name="The Times of Israel", kind="toi_liveblog", url="https://www.timesofisrael.com/liveblog-{date}/",
         sections=["iran", "israel"]),
    dict(name="The Times of Israel", kind="rss", url="https://www.timesofisrael.com/feed/", sections=["iran", "israel"]),
    dict(name="Al Jazeera", kind="rss", url="https://www.aljazeera.com/xml/rss/all.xml",
         sections=["iran", "israel", "ukraine", "immigration", "global"]),
    # 移民
    dict(name="AILA 汇编", kind="aila_clips",
         url="https://www.aila.org/immigration-news/daily-immigration-news-clips-{month}-{day}-{year}",
         sections=["immigration"], dedicated=True),
    dict(name="The Guardian", kind="rss", url="https://www.theguardian.com/us-news/usimmigration/rss",
         sections=["immigration"], dedicated=True),
    dict(name="The Guardian", kind="rss", url="https://www.theguardian.com/uk-news/immigration/rss",
         sections=["immigration"], dedicated=True),
    dict(name="The Guardian", kind="rss", url="https://www.theguardian.com/world/migration/rss",
         sections=["immigration"], dedicated=True),
    dict(name="Politico", kind="rss", url="https://rss.politico.com/politics-news.xml",
         sections=["immigration", "ai_general"]),
    # 综合大报（按关键词分流到各板块）
    dict(name="BBC", kind="rss", url="https://feeds.bbci.co.uk/news/world/rss.xml",
         sections=["iran", "israel", "ukraine", "immigration", "global"]),
    dict(name="BBC", kind="rss", url="https://feeds.bbci.co.uk/news/business/rss.xml", sections=["global"]),
    dict(name="New York Times", kind="rss", url="https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
         sections=["iran", "israel", "ukraine", "immigration", "global"]),
    dict(name="New York Times", kind="rss", url="https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
         sections=["global"]),
    dict(name="Wall Street Journal", kind="rss", url="https://feeds.a.dj.com/rss/RSSWorldNews.xml",
         sections=["iran", "israel", "ukraine", "global"]),
    dict(name="Wall Street Journal", kind="rss", url="https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
         sections=["global"]),
    dict(name="Bloomberg", kind="rss", url="https://feeds.bloomberg.com/markets/news.rss", sections=["global"]),
    dict(name="Bloomberg", kind="rss", url="https://feeds.bloomberg.com/politics/news.rss",
         sections=["iran", "global", "immigration"]),
    dict(name="Bloomberg", kind="rss", url="https://feeds.bloomberg.com/technology/news.rss",
         sections=["ai_companies", "ai_infra", "ai_industry", "global"]),
    dict(name="Financial Times", kind="rss", url="https://www.ft.com/world?format=rss",
         sections=["iran", "israel", "ukraine", "global"]),
    dict(name="The Guardian", kind="rss", url="https://www.theguardian.com/business/economics/rss", sections=["global"]),
    # 太空
    dict(name="TechCrunch", kind="rss", url=TC.format("space"), html="https://techcrunch.com/category/space/",
         sections=["global"], dedicated=True),
    dict(name="SpaceNews", kind="rss", url="https://spacenews.com/feed/", sections=["global"], dedicated=True),
    # AI / 科技
    dict(name="TechCrunch", kind="rss", url=TC.format("artificial-intelligence"),
         html="https://techcrunch.com/category/artificial-intelligence/",
         sections=["ai_companies", "ai_general", "ai_industry", "ai_infra", "frontier"]),
    dict(name="TechCrunch", kind="rss", url=TC.format("government-policy"),
         html="https://techcrunch.com/category/government-policy/", sections=["ai_general", "global", "immigration"]),
    dict(name="TechCrunch", kind="rss", url=TC.format("enterprise"),
         html="https://techcrunch.com/category/enterprise/", sections=["ai_industry", "ai_infra", "ai_companies"]),
    dict(name="TechCrunch", kind="rss", url=TC.format("climate"),
         html="https://techcrunch.com/category/climate/", sections=["ai_infra", "frontier"]),
    dict(name="TechCrunch", kind="rss", url=TC.format("robotics"),
         html="https://techcrunch.com/category/robotics/", sections=["frontier"], dedicated=True),
    dict(name="TechCrunch", kind="rss", url=TC.format("transportation"),
         html="https://techcrunch.com/category/transportation/", sections=["frontier"]),
    dict(name="MIT Technology Review", kind="rss",
         url="https://www.technologyreview.com/topic/artificial-intelligence/feed",
         sections=["ai_general", "ai_industry", "ai_infra", "ai_companies"]),
    dict(name="IEEE Spectrum", kind="rss", url="https://spectrum.ieee.org/feeds/feed.rss",
         sections=["frontier", "ai_infra", "ai_general"]),
    dict(name="DatacenterDynamics", kind="rss", url="https://www.datacenterdynamics.com/en/rss/",
         sections=["ai_infra"], dedicated=True),
]

# AILA 汇编页里外链域名 -> 媒体名（只收权威媒体）
TRUSTED_DOMAINS = {
    "apnews.com": "AP", "reuters.com": "Reuters", "nytimes.com": "New York Times",
    "washingtonpost.com": "Washington Post", "wsj.com": "Wall Street Journal", "bloomberg.com": "Bloomberg",
    "bloomberglaw.com": "Bloomberg Law", "news.bloomberglaw.com": "Bloomberg Law",
    "theguardian.com": "The Guardian", "cnn.com": "CNN", "bbc.com": "BBC", "bbc.co.uk": "BBC",
    "ft.com": "Financial Times", "politico.com": "Politico", "politico.eu": "Politico",
    "npr.org": "NPR", "axios.com": "Axios", "cbsnews.com": "CBS News", "nbcnews.com": "NBC News",
    "abcnews.go.com": "ABC News", "latimes.com": "Los Angeles Times", "aljazeera.com": "Al Jazeera",
}

# 评论/解读/软新闻：标题模式
SOFT_TITLE_RE = (
    r"^(opinion|analysis|explainer|explained|review|podcast|watch|video|listen|interview|quiz|photos?|"
    r"in pictures|the week|week in review|newsletter|letters?|editorial|comment|live|live updates|"
    r"first look|hands-on|deals?)\b"
    r"|\?$|^(how|why|what|who|when|where|is|are|can|should|will|does|do)\b"
    r"|here'?s|everything you need|things to know|what we know|what to know|how to\b|we tried|i tried|"
    r"\bbest\b.*\bof 20\d\d|\bbuying guide|save up to|tickets?\b.*\b(disrupt|event)|techcrunch disrupt|"
    r"strictlyvc|sponsored|\bpartner content|last chance|register now|\bdeal of the day|"
    r"\bthis week in\b|\bweek ahead\b|\bmorning brief|\bevening brief|\bwhat'?s next\b"
)
SOFT_URL_RE = (
    r"/(opinion|opinions|commentary|comment|analysis|podcasts?|video|videos|live|features?|long-read|"
    r"newsletters?|sponsored|events?|gallery|interactive|reviews?|deals|podcast|explainers?)/"
)
SOFT_CATEGORY_RE = r"opinion|analysis|podcast|commentary|feature|review|sponsored|video|newsletter|explainer|events"

# 标题里出现这些词，重要度加分（硬新闻信号）
HARD_NEWS_RE = (
    r"kill|dead|strike|attack|missile|ceasefire|truce|sanction|agree|deal\b|treaty|talks|summit|"
    r"announce|launch|unveil|release|raise[sd]?|funding|billion|acquire|acquisition|merger|ban\b|"
    r"approve|pass(es|ed)?\b|sign(s|ed)?\b|order|rule[sd]?\b|court|sue[sd]?\b|fine[sd]?\b|record|"
    r"surge|plunge|tumble|soar|cut|hike|resign|fire[sd]?\b|elect|vote|invade|seize|capture|explosion|"
    r"arrest|deport|tariff"
)

HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
