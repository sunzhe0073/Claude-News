# 项目须知

每日新闻简报：GitHub Actions 每天北京时间 09:00 抓取权威媒体新闻 → 规则筛选 → 免费接口翻译标题 → 生成 `index.html`（GitHub Pages 发布）+ `archive/daily-brief-YYYY-MM-DD.html` 归档。

- 需求规则书：`docs/SPEC.md`（改筛选/信源/格式前先看）
- 进度记录：`docs/PROGRESS.md`，开始工作前先看"下一步"
- 代码：`brief/config.py`（板块、信源、关键词、软新闻规则）、`fetch.py`（抓取）、`select.py`（筛选去重排序）、`translate.py`（免费翻译，不用 API key）、`render.py`（页面）
- 本地跑：`pip install -r requirements.txt && python -m brief --out-dir /tmp/out`
- 测试：`python -m pytest tests -q`
- 不使用任何付费 API（用户明确要求免费方案）
