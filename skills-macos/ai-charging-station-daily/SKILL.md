---
name: ai-charging-station-daily
description: Inspect or maintain the local AI充电站 daily workflow at /Users/yuzhou4tc/Public/ai充电站, including latest-report.txt, latest-workflow.json, creator-first sources, RSSHub/ForgeRSS health, translation, history JSON, and the existing AI充电站日报 automation. Trigger only when the user explicitly mentions AI充电站, that project path, or one of its artifacts; generic current AI-news requests belong to aihot.
---

# AI Charging Station Daily

Work from `/Users/yuzhou4tc/Public/ai充电站`.

## Status First

For read-only status or daily-summary requests, inspect existing artifacts before running collection:

- `data/latest-report.txt`
- `data/latest-workflow.json`
- `data/latest.json`
- the matching `data/digests/YYYY-MM-DD.{json,md}`

Compare mtimes and embedded timestamps with the current Asia/Shanghai date. Treat `sourceHealth` as the operational truth. Do not rerun RSSHub, ForgeRSS, digest, or report unless the user explicitly asks for a run or repair.

## Explicit Run

When authorized to run or repair the pipeline:

```bash
npm run rsshub:doctor
npm run rsshub:start
npm run rsshub:doctor
npm run forgerss:xhs || true
npm run digest
npm run report
```

Start RSSHub only when the first doctor check shows it is not healthy. Keep ForgeRSS non-blocking because Xiaohongshu may require manual login or CAPTCHA verification.

## Output Contract

Keep creator and official-product sources ahead of AI HOT. AI HOT is supplementary discovery, not the primary source.

Use this reader-facing order:

1. 统计窗口
2. 总条目数
3. 今日必看
4. 创作者更新
5. 官方/行业补充
6. AI HOT 精选
7. 源状态提醒

Translate residual English titles and summaries before presenting them. If the 24-hour window is empty, say `过去 24 小时未发现新增内容`; do not pad with older items.

For repairs, report the exact command or file changed and verify against the resulting local artifact.

