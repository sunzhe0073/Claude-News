# 每日新闻简报

每天北京时间 09:00 由 GitHub Actions 自动运行：抓取国际权威媒体的分类页/RSS/liveblog → 按规则筛选（只要最近 24 小时、剔除评论与软新闻、跨媒体去重、分板块、挑头条、按热度排序）→ 标题免费翻译为中文 → 生成 `index.html` 并 commit，由 GitHub Pages 发布到固定网址。每天另存一份到 `archive/daily-brief-YYYY-MM-DD.html`。

规则见 [`docs/SPEC.md`](docs/SPEC.md)。

## 首次设置（只需一次）

1. **Settings → Pages**：Source 选 *Deploy from a branch*，Branch 选 `main`、目录 `/ (root)`，保存。网址为 `https://<用户名>.github.io/<仓库名>/`。
2. **Settings → Actions → General → Workflow permissions**：选 *Read and write permissions*（工作流要 push 生成的页面）。
3. **Actions → Daily brief → Run workflow** 手动跑第一次，确认成功。
4. 可选：**Settings → General** 勾选 *Automatically delete head branches*，PR 合并后自动删分支。

之后每天自动运行，无需任何人工确认。运行失败时 GitHub 会给仓库所有者发邮件。

## 本地运行

```bash
pip install -r requirements.txt
python -m brief --out-dir /tmp/out
python -m pytest tests -q
```

## 说明

- 不使用付费 API：筛选/去重/排序为规则实现，翻译依次用 Google 翻译网页接口、Google 词典扩展接口，MyMemory 最后兜底，仍失败则保留英文标题并标"未翻译"。
- 信源、关键词、软新闻判定规则集中在 `brief/config.py`，可直接改。
- 只收最近 24 小时的新闻，不够宁可板块不满；抓取失败的信源、数量不足的板块都会在页面上标出（页脚"抓取明细"可展开）。
