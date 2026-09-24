# 进度记录

## 2026-09-23（第一天）

### 已完成
- 从零搭好项目：`brief/`（抓取 → 筛选 → 翻译 → 生成页面）、`.github/workflows/daily-brief.yml`（每天 UTC 01:00 = 北京 09:00，另可手动 Run workflow）、`tests/test_brief.py`（8 个用例）。
- 仓库改为公开，GitHub Pages 已开启（main / root），网址：https://sunzhe0073.github.io/Claude-News/
- 实跑 3 次，第 3 次结果：60/70 条，翻译 0 失败，构建约 16 秒。
- 首次实跑后修正：软新闻漏网（门票广告、Guardian 署名评论、体育）、摘要误分类（关键词须命中标题）、AI 综合条数少（富余板块借调）、被 403 的信源用 Guardian/Jerusalem Post/Politico Europe 补位、翻译改用 Google 词典接口整批翻。

### 已知问题
- Times of Israel、SpaceNews 对 GitHub 服务器返回 403，无法绕过，靠其他信源补位。
- AILA 移民汇编页每天只解析出 0–1 条（本地网络被拦，看不到页面结构）；移民板块靠 Guardian/Politico 已能凑满。
- AI 与产业结合常只有 2/5；前沿科技、AI 综合会用到 3–5 天前的条目（已逐条标注超窗天数）。
- 免费翻译接口无保障：Google gtx 在 GitHub 服务器上 429，目前靠 `clients5.google.com` 词典接口；MyMemory 匿名额度约 5000 字符/天，仅兜底。

## 2026-09-24

- 修关键词误命中：`stock` 命中了 Birkenstock，Lidl 山寨凉鞋官司进了"全球格局观察"。给 stock/market/ban/sue/math/intel 加上单词开头边界，insur 改为 insuran（避免 insurgent），Taliban、issue、aftermath、supermarket 不再误命中。
- 时间窗口改为只要最近 24 小时，删掉往前 1-5 天补位的逻辑；条目不够的板块会显示"覆盖不足"。
- 今天的定时任务在北京时间 13:49 才提交（比 09:00 晚），线上网页是否跟着更新仍待确认。

## 下一步
1. **先确认 09-24 早上的定时任务**：Actions 里 Daily brief 是否在 09:00 左右自动跑、是否成功；网页顶部日期是否变成 09-24。若 Actions 成功但网页仍是 09-23，说明 bot 推送没有触发 Pages 部署，需要在工作流里加 `actions/deploy-pages` 部署步骤（并把 Pages Source 改成 GitHub Actions）。
2. 可选小修：标题数字高低不齐（Georgia 老式数字），在 `render.py` 的 CSS 里给 body 加 `font-variant-numeric: lining-nums;`。
3. 视需要：排查 AILA 页面结构（可在工作流里临时打印页面片段）、给"AI 与产业结合"补信源、规则书第十节的"今日最重要 3 条"摘要区。
