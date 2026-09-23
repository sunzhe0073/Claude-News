# 每日新闻简报 · 项目规则书（GitHub Actions 迁移版）

> 用户与 Claude 逐步确认，2026-09-23 补充"GitHub Actions 迁移"背景后更新。实现时的取舍见文末"实现约定"。

## 〇、背景

原方案在 Claude Cowork 里定时运行、发布到固定 Artifact 网址，但"覆盖已有 Artifact"需要人工点 Replace 确认，且该确认未被持久化，导致页面停更 12 天。现改为 GitHub 仓库 + GitHub Actions：代码实现抓取、翻译、生成 HTML，cron 定时触发，生成的 HTML commit 到仓库并由 GitHub Pages 发布，全程无需人工确认。

## 一、任务目标

每天定时搜集国际权威英文媒体最新新闻，按指定话题和数量筛选，标题译成中文，生成 HTML 网页。执行时间：每天北京时间上午 9 点（cron 用 UTC，即 `0 1 * * *`），并保留 `workflow_dispatch` 手动入口。

## 二、搜索方法

不用泛用关键词搜索。对每个板块确定 1-3 个专业媒体，直接抓取其**分类页/专题页**（按时间倒序、带日期和作者的真实头条列表），再按本规则挑选。地缘政治类用媒体自己的 liveblog / war-tracker 页面。搜索引擎只作为分类页抓取失败时的兜底。

## 三、信源要求

只用国际公认权威媒体：Reuters、AP、BBC、NYT、WSJ、Washington Post、Bloomberg、The Guardian、CNN、FT、Al Jazeera（中东）、Kyiv Independent / Kyiv Post（俄乌）、The Times of Israel（哈以，liveblog 质量高）。排除个人博客、论坛、未经证实的社交媒体、小道消息、自媒体聚合站。

| 板块 | 专业信源 |
|---|---|
| 俄乌战争 | Kyiv Independent（`/tag/war-update/`）、Kyiv Post、ISW |
| 哈以战争 | Times of Israel 当天 `liveblog-YYYY-MM-DD`、Al Jazeera |
| 美伊局势 | Times of Israel liveblog、Al Jazeera、Bloomberg |
| 欧美移民新闻 | Politico、AP、Bloomberg Law、AILA `daily-immigration-news-clips-*` 汇编页 |
| 全球格局：中美/经济 | Bloomberg、Reuters、FT、WSJ |
| 全球格局：太空 | TechCrunch Space、SpaceNews |
| AI 代表性企业动态 | TechCrunch AI、The Information |
| AI 综合 | TechCrunch AI / Government & Policy、MIT Technology Review |
| AI 与产业结合 | TechCrunch Enterprise、Bloomberg Technology |
| AI 能源与基础设施 | TechCrunch Climate / Cloud Computing、DataCenter Dynamics |
| 前沿科技 | TechCrunch Robotics / Transportation、IEEE Spectrum |

## 四、时间范围与凑数规则

- 优先"今天 + 昨天"。
- 硬新闻不足时允许往前多找 1-2 天。
- 不允许用软性分析、观点评论凑数。
- 仍不够可适度再往前（3-5 天），但须在页面或日志中注明哪些条目超出标准窗口、超出多少天。**真实硬新闻 > 凑够数量**。

## 五、去重规则

同一事件多家媒体报道，只选 1 条信息最全面、来源最权威的。

## 六、板块与数量（共 70 条/天）

地缘政治 / 冲突：俄乌战争 5、哈以战争 5、美伊局势 5、欧美移民新闻 5、全球格局观察 10（中美关系/科技竞争、全球宏观经济与金融市场、太空/卫星，不设固定比例）。

前沿科技：AI 代表性企业动态 10（大模型公司 + 芯片公司，不偏重某家）、AI 综合 10（政策监管/安全伦理/就业社会影响/学术研究）、AI 与产业结合 5、AI 能源与基础设施 5、前沿科技综合 10（新能源、核聚变、自动驾驶、机器人）。

## 七、重要程度标记

每个板块挑 1-2 条头条，用醒目样式（加大加粗 + ★ + 左侧强调色条），其余正常列出。

## 八、页面展示格式

- 每条：中文标题（点击跳原文）+ 来源媒体 + 发布时间。
- 分「地缘政治/冲突」「前沿科技」两大组，组内板块按当天热度自动排序。
- Techmeme 风格：极简文字列表，标题衬线字体，来源/时间等宽字体弱化，头条强调色，无大图。

## 九、输出与发布（GitHub Pages）

1. 固定地址：`https://<用户名>.github.io/<仓库名>/`。
2. 每天覆盖写入仓库根目录 `index.html`，自动 commit + push 到默认分支，Pages 从该分支部署，无需人工确认。
3. 每天另存 `archive/daily-brief-YYYY-MM-DD.html` 作为历史归档。
4. 推送通知非必须，可后续再加。

## 十、后续可迭代项（暂不启用）

- 板块内部权重精细调整
- 页面顶部"今日最重要 3 条"全局摘要区
- 更多话题方向

## 附录一：已验证网址

| 板块 | 网址 |
|---|---|
| AI 代表性企业动态 | `https://techcrunch.com/category/artificial-intelligence/` |
| 机器人/自动驾驶 | `https://techcrunch.com/category/robotics/` |
| AI 能源 / 新能源核聚变 | `https://techcrunch.com/category/climate/` |
| 太空 | `https://techcrunch.com/category/space/` |
| AI 政策监管 | `https://techcrunch.com/category/government-policy/` |
| AI 与产业结合 | `https://techcrunch.com/category/enterprise/`（更新频率较低） |
| 俄乌战争 | `https://kyivindependent.com/tag/war-update/` |
| 哈以 / 美伊 | `https://www.timesofisrael.com/liveblog-YYYY-MM-DD/`（按当天日期拼） |
| 欧美移民 | `https://www.aila.org/immigration-news/daily-immigration-news-clips-<月份英文全称>-<日>-<年>`（如 `-september-22-2026`） |

注意：网址可能随改版失效，需要重试/告警；按日期拼的 URL 要注意时区（ToI 用以色列当地日期，AILA 用美东日期）。

## 附录二：内容质量注意事项

- 筛选逻辑要能主动排除评论/深度解读/软新闻，宁可某板块 4/5 条。
- 某板块数量低于应有条数一半时，页面上醒目标注"本板块本次覆盖不足"。

## 实现约定（2026-09-23）

- **不用付费 API**（用户要求）：筛选、去重、分板块、挑头条、热度排序都用规则实现（`brief/config.py` 的关键词和软新闻正则）；标题翻译用 Google 翻译网页接口，MyMemory 兜底，都失败则保留英文并标"未翻译"。
- 分类页优先抓对应 RSS（与分类页同一批文章、结构更稳），RSS 失败再解析分类页 HTML。
- 除专业信源外，另接了 BBC、NYT、WSJ、Bloomberg、FT、Guardian 的 RSS，按关键词分流到各板块，补足条数。
- "今天/昨天"按北京时间日期判断；超出"今天+昨天"的条目在页面上逐条标注"超出标准窗口 N 天"，并在页脚汇总。
- 一条都选不出来时工作流失败退出、不覆盖昨天的页面（GitHub 会发失败邮件）。
- 2026-09-23 首次实跑后调整：板块关键词必须在**标题**里命中（摘要只加分）；条数不够的板块可从富余板块借"同时符合本板块"的条目；软新闻规则补上活动门票/促销、Guardian 署名评论（标题末尾 `| 作者名`、`/commentisfree/`）、体育；Times of Israel 与 SpaceNews 会 403 拦 GitHub 服务器，补了 Jerusalem Post、Guardian 以色列/加沙/伊朗/乌克兰/太空标签页和 Politico Europe；翻译加了 Google 词典扩展接口整批翻译，MyMemory（匿名约 5000 字符/天）只做最后兜底。
