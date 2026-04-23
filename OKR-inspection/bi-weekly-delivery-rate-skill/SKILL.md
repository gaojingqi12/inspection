---
name: bi-weekly-delivery-rate-inspection
description: 巡检 InsightEngine 双周交付率指标；页面自动化脚本在查询后直接从图表 DOM / ECharts 实例提取双周交付率并生成每日 JSON，JoyClaw 只负责读取历史 JSON 生成本周趋势。
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

查询完成后，脚本会保存截图，并直接从页面图表元素读取双周交付率，不使用视觉识别。脚本产出：

```text
out/history/YYYY-MM-DD.json
out/03_after_query.png
```

图表值来源于页面内的 `chart-render / chart-canvas / _echarts_instance_` 对应元素和 ECharts 实例，不依赖截图 OCR。

## 每日结果

每天巡检后，脚本写入：

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

如果页面图表结构有轻微变化，优先从目标图表元素的 tooltip DOM 或 ECharts `series.data` 中读取值；不要改字段名。不要再输出完成需求数、总需求数、双周内交付需求数等额外字段。

## 本周趋势

JoyClaw 只读取 `out/history/` 中本周已有 JSON，按日期升序输出本周截止当前日期的趋势 JSON。

如果 `out/history/` 不存在、为空，或缺少本周日期，不要停止；只汇总当前已经存在的日期，不要改用截图视觉识别去补历史值。

历史汇总规则：

- 只读取 `out/history/` 中已经存在的每日 JSON。
- 只保留本周周一到今天的日期。
- 不要从截图中估算、补写或回填历史值。
- 如果本周缺少某些日期，只输出已有日期，`summary` 或 `notes` 说明缺失情况即可。

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
- 历史趋势只使用每日 JSON。
- 不要编造缺失日期或不可见数值。
- 如需周五清理历史文件，必须在总报告生成并确认落盘后再清理。
