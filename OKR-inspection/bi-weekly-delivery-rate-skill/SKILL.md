---
name: bi-weekly-delivery-rate-inspection
description: 巡检 InsightEngine 双周交付率指标；页面自动化脚本只生成查询截图，JoyClaw 只从截图中的双周交付率目标区域拿数据，并生成每日 JSON 与本周趋势 JSON。
---

# bi-weekly-delivery-rate-inspection

## 目标

巡检目标指标：

**双周交付率**

固定部门：

**支付方案研发部**

## 自动化执行

从本 skill 根目录运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

脚本只负责打开固定页面，收起侧边栏，设置：

- 快照日期：保留页面默认最新日
- 卡片完成日期：上周五到今天
- 任务处理人部门C3：支付方案研发部

查询完成后，脚本只保存截图，不生成或读取任何指标 JSON。JoyClaw 只读取：

```text
out/03_after_query.png
```

只分析截图中与双周交付率有关的指标区域，不要读取其他无关图表。六类巡检中只有双周交付率允许从截图拿指标值。

## 每日结果

每天巡检后，JoyClaw 写入：

```text
out/history/YYYY-MM-DD.json
```

每日 JSON 只保留这 1 个指标：

- `biweekly_delivery_rate`：双周交付率，单位 `%`

格式：

```json
{
  "date": "2026-04-17",
  "indicator_type": "bi_weekly_delivery_rate",
  "indicator_name": "双周交付率",
  "department_c3": "支付方案研发部",
  "status": "success",
  "metrics": {
    "biweekly_delivery_rate": 80.0
  },
  "unit": {
    "biweekly_delivery_rate": "%"
  },
  "source": {
    "query_screenshot": "out/03_after_query.png"
  }
}
```

如果页面字段名与上面略有差异，按截图可见含义映射到上述固定 JSON 字段；不要改字段名。不要再输出完成需求数、总需求数、双周内交付需求数等额外字段。

## 本周趋势

JoyClaw 优先读取 `out/history/` 中本周已有 JSON，按日期升序输出本周截止当前日期的趋势 JSON。

如果 `out/history/` 不存在、为空，或缺少本周日期，不要停止。JoyClaw 需要从 `out/03_after_query.png` 的目标指标区域中读取历史结果、趋势图、明细表或可见日期列，直接抽取本周周一到今天的双周交付率序列。

截图兜底规则：

- 只读取截图中与“双周交付率”有关的指标区域。
- 只保留本周周一到今天的日期；如果截图只展示上周五到今天，则过滤掉不属于本周的日期。
- 只记录截图中可见或可通过页面交互明确读到的日期和值，不要估算曲线上的不可见点。
- JoyClaw 先输出 `out/weekly-trend-from-screenshot.json`；如果每个日期的双周交付率都能识别，再回填 `out/history/YYYY-MM-DD.json`。
- 如果只能读到部分日期，`status` 写 `partial`，并在 `notes` 中说明缺失日期。

```json
{
  "skill_name": "bi-weekly-delivery-rate-inspection",
  "indicator_type": "bi_weekly_delivery_rate",
  "indicator_name": "双周交付率",
  "department_c3": "支付方案研发部",
  "time_range": {
    "start_date": "2026-04-13",
    "end_date": "2026-04-17"
  },
  "status": "success",
  "history": {
    "biweekly_delivery_rate": [
      { "date": "2026-04-17", "value": 80.0, "unit": "%" }
    ]
  },
  "summary": "已汇总本周双周交付率核心指标历史数据。"
}
```

## 输出约束

- 只输出 JSON，不输出解释性文字。
- 数值用数字类型，不要带 `%`、`,` 或中文单位。
- 历史趋势优先使用每日 JSON；每日 JSON 缺失时从目标截图抽取本周序列。
- 不要编造缺失日期或不可见数值。
- 如需周五清理历史文件，必须在总报告生成并确认落盘后再清理。
