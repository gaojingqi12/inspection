---
name: technical-refactor-working-hours-inspection
description: 巡检 InsightEngine 技术改造工时占比指标；页面自动化脚本只生成查询截图，JoyClaw 负责读取目标卡片数据、生成每日 JSON、读取历史 JSON 与生成本周趋势 JSON。
---

# technical-refactor-working-hours-inspection

## 目标

巡检目标卡片：

**技术改造工时占比-周（5->4）-汇总-C3维度**

固定部门：

**支付方案研发部**

## 自动化执行

从本 skill 根目录运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

脚本只负责打开固定页面，收起侧边栏，定位目标卡片，打开图表筛选，设置：

- 填报日期：上周五到今天
- 填报人部门C3：支付方案研发部

查询完成后，脚本只保存截图，不生成或读取任何指标 JSON。JoyClaw 只读取：

```text
out/05_after_query.png
```

不要分析其他卡片或页面其他区域。

## 每日结果

每天巡检后，JoyClaw 写入：

```text
out/history/YYYY-MM-DD.json
```

每日 JSON 只保留这 3 个指标：

- `total_working_hours`：总工时或填报工时，单位 `hour`
- `technical_refactor_working_hours`：技术改造工时，单位 `hour`
- `technical_refactor_working_hours_rate`：技术改造工时占比，单位 `%`

格式：

```json
{
  "date": "2026-04-17",
  "indicator_type": "technical_refactor_working_hours",
  "indicator_name": "技术改造工时占比-周（5->4）-汇总-C3维度",
  "department_c3": "支付方案研发部",
  "status": "success",
  "metrics": {
    "total_working_hours": 120.5,
    "technical_refactor_working_hours": 18.0,
    "technical_refactor_working_hours_rate": 14.9
  },
  "unit": {
    "total_working_hours": "hour",
    "technical_refactor_working_hours": "hour",
    "technical_refactor_working_hours_rate": "%"
  },
  "source": {
    "query_screenshot": "out/05_after_query.png"
  }
}
```

如果截图中的文案是“技术改造”“技术重构”或类似表达，以页面可见口径为准，但 JSON 字段名保持不变。

## 本周趋势

JoyClaw 优先读取 `out/history/` 中本周已有 JSON，按日期升序输出本周截止当前日期的趋势 JSON。

如果 `out/history/` 不存在、为空，或缺少本周日期，不要停止。JoyClaw 需要从 `out/05_after_query.png` 的目标卡片中读取历史结果、趋势图、明细表或可见日期列，直接抽取本周周一到今天的三项指标序列。

截图兜底规则：

- 只读取目标卡片“技术改造工时占比-周（5->4）-汇总-C3维度”内部的数据。
- 只保留本周周一到今天的日期；如果截图只展示上周五到今天，则过滤掉不属于本周的日期。
- 只记录截图中可见或可通过卡片交互明确读到的日期和值，不要估算曲线上的不可见点。
- JoyClaw 先输出 `out/weekly-trend-from-screenshot.json`；如果每个日期的三项指标都能识别，再回填 `out/history/YYYY-MM-DD.json`。
- 如果只能读到部分日期，`status` 写 `partial`，并在 `notes` 中说明缺失日期。

```json
{
  "skill_name": "technical-refactor-working-hours-inspection",
  "indicator_type": "technical_refactor_working_hours",
  "indicator_name": "技术改造工时占比-周（5->4）-汇总-C3维度",
  "department_c3": "支付方案研发部",
  "time_range": {
    "start_date": "2026-04-13",
    "end_date": "2026-04-17"
  },
  "status": "success",
  "history": {
    "total_working_hours": [
      { "date": "2026-04-17", "value": 120.5, "unit": "hour" }
    ],
    "technical_refactor_working_hours": [
      { "date": "2026-04-17", "value": 18.0, "unit": "hour" }
    ],
    "technical_refactor_working_hours_rate": [
      { "date": "2026-04-17", "value": 14.9, "unit": "%" }
    ]
  },
  "summary": "已汇总本周技术改造工时占比核心指标历史数据。"
}
```

## 输出约束

- 只输出 JSON，不输出解释性文字。
- 数值用数字类型，不要带 `%`、`,` 或中文单位。
- 历史趋势优先使用每日 JSON；每日 JSON 缺失时从目标截图抽取本周序列。
- 不要编造缺失日期或不可见数值。
- 如需周五清理历史文件，必须在总报告生成并确认落盘后再清理。
