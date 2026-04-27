---
name: joyclaw-daily-inspection-orchestrator
description: 编排 JoyClaw 每日巡检 OKR、AI、持续交付三类结果；先巡检 OKR，再巡检 AI，再巡检持续交付，最后把结果集成到根目录总 HTML 报告。
---

# joyclaw-daily-inspection-orchestrator

## 根入口说明

当前文件是整个项目的总入口 skill，也是后续接手时优先阅读的主说明。

- 根目录 `SKILL.md`：总编排主入口。
- `joyclaw-daily-inspection-orchestrator-skill/`：总编排实现目录，保存模板、聚合脚本、输出产物。
- 单项 skill 目录：分别负责 OKR、AI、持续交付的页面自动化或数据补齐。

看全局时，先读当前文件，再看单项 skill 和聚合脚本。

## 适用场景

当用户要求 JoyClaw 自动巡检、生成日报/周趋势、或统一编排以下 skill 时，使用本 skill：

- `delay-test-rate-inspection`
- `delay-online-rate-inspection`
- `technical-refactor-working-hours-inspection`
- `bi-weekly-delivery-rate-inspection`
- `ai-non-deep-user-inspection`
- `continuous-delivery-inspection`

固定部门：**支付方案研发部**

## 总巡检顺序

必须先巡检 OKR，再巡检 AI，再巡检持续交付，最后生成统一报告。

OKR 巡检顺序：

1. `OKR-inspection/delay-test-rate-skill`
2. `OKR-inspection/delay-online-rate-skill`
3. `OKR-inspection/technical-refactor-working-hours-skill`
4. `OKR-inspection/bi-weekly-delivery-rate-skill`

每个 OKR skill 目录下运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

AI 巡检在 OKR 完成后执行，从仓库根目录的 `AI-inspection` 目录运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

持续交付巡检在 AI 完成后执行，从仓库根目录的 `ContinuousDelivery-inspection` 目录运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

## 职责边界

- `scripts/run_skill.py` 默认负责页面自动化：打开页面、设置筛选条件、点击查询、保存截图。
- `OKR-inspection/delay-test-rate-skill`、`OKR-inspection/delay-online-rate-skill`、`OKR-inspection/technical-refactor-working-hours-skill` 这三个脚本会在查询后直接从目标卡片表格第一行提取当天值，并写入 `out/history/YYYY-MM-DD.json`。
- 双周交付率脚本只负责页面自动化和截图，不生成每日 JSON。
- OKR 部分：延期提测率、延期上线率、技术改造工时占比只读取脚本已生成的 `out/history/YYYY-MM-DD.json`，不从截图补数据；只有双周交付率从截图拿数据。
- AI 部分：JoyClaw 负责读取 `AI-inspection/out/non_deep_users_YYYY-MM-DD.json`，提取 `是否深度用户` 为 `否` 的人名，并生成 `AI-inspection/out/non_deep_user_names_YYYY-MM-DD.json`。
- 持续交付脚本会在查询后直接从三张卡片元素提取三个指标，并生成 `ContinuousDelivery-inspection/out/continuous_delivery_YYYY-MM-DD.json`。
- 总编排脚本 `aggregate_report.py` 只读取各模块已经生成的 JSON，产出总 JSON 和 HTML；它不负责从截图识别 OKR 指标，也不负责判断 AI 深度用户。

## 数据读取规则

JoyClaw 必须按下面的数据源读取，不要混用：

| 模块 | 数据源 | 规则 |
| --- | --- | --- |
| 延期提测率 | `OKR-inspection/delay-test-rate-skill/out/history/YYYY-MM-DD.json` | 直接读当天和本周每日 JSON |
| 延期上线率 | `OKR-inspection/delay-online-rate-skill/out/history/YYYY-MM-DD.json` | 直接读当天和本周每日 JSON |
| 技术改造工时占比 | `OKR-inspection/technical-refactor-working-hours-skill/out/history/YYYY-MM-DD.json` | 直接读当天和本周每日 JSON |
| AI 巡检 | `AI-inspection/out/non_deep_users_YYYY-MM-DD.json` | 直接读当天 JSON，再输出人名结果 JSON |
| 持续交付 | `ContinuousDelivery-inspection/out/continuous_delivery_YYYY-MM-DD.json` | 直接读当天 JSON |
| 双周交付率 | `OKR-inspection/bi-weekly-delivery-rate-skill/out/03_after_query.png` | 只有这一项从截图识别并生成每日 JSON |

约束：

- 延期提测率、延期上线率、技术改造工时占比、AI 巡检、持续交付都不允许从截图补指标值。
- 双周交付率只读取截图中与“双周交付率”有关的目标区域，不分析其他卡片、无关表格或页面装饰。
- 巡检目标是“本周变化趋势”，但数据点只来自本周每日 JSON；双周交付率可由截图识别后回填每日 JSON。
- 数值必须是数字类型，百分比不带 `%`。
- 无法识别的指标写 `null`，对应文件 `status` 写 `failed` 或 `partial` 并记录 `error`。

## 没有每日 JSON 时

如果延期提测率、延期上线率、技术改造工时占比、AI 巡检或持续交付缺少当天 JSON，不要从截图补数据。该模块在总报告中标为 `missing` 或 `partial`，并在 `notes` 或 `error` 中说明缺失文件。

只有双周交付率缺少当天 JSON 时，JoyClaw 才能改用截图作为数据源：

1. 读取 `OKR-inspection/bi-weekly-delivery-rate-skill/out/03_after_query.png`。
2. 只分析与“双周交付率”有关的指标区域。
3. 只抽取本周周一到今天的日期；如果截图只展示上周五到今天，则只保留其中属于本周的日期。
4. 对每个可见日期读取页面展示值；不要根据曲线形状估算不可见数值。
5. JoyClaw 先写入 `OKR-inspection/bi-weekly-delivery-rate-skill/out/weekly-trend-from-screenshot.json`。
6. JoyClaw 如果能识别每个日期的双周交付率，再按日期回填 `out/history/YYYY-MM-DD.json`。

双周交付率的 `out/weekly-trend-from-screenshot.json` 额外增加：

```json
{
  "source_mode": "screenshot_weekly_trend",
  "confidence": "high",
  "notes": "缺少每日历史 JSON，已从查询截图中的本周趋势区域抽取。"
}
```

如果截图里没有可读的一周序列，只写当前可读日期和数值，`status` 写 `partial`，`notes` 说明缺少哪些日期；不要编造缺失日期。

## 四个每日 JSON 字段

延期提测率：

- `planned_test_requirements`
- `delayed_test_requirements`
- `delay_test_rate_okr`

延期上线率：

- `planned_online_requirements`
- `delayed_online_requirements`
- `delay_online_rate`

技术改造工时占比：

- `total_working_hours`
- `technical_refactor_working_hours`
- `technical_refactor_working_hours_rate`

双周交付率：

- `biweekly_delivery_rate`

## HTML 模板填充

HTML 模板固定使用：

```text
joyclaw-daily-inspection-orchestrator-skill/assets/weekly-line-report-template.html
```

聚合脚本负责读取 OKR 每日巡检 JSON、AI 当天人名结果 JSON、持续交付当天 JSON，并把模板中的：

```text
__JOYCLAW_WEEKLY_REPORT_JSON__
```

替换为本周报告 JSON。最终 HTML 会内置报告数据，但截图仍通过 `assets/screenshots/...` 相对路径引用，不内嵌 base64 图片。

只取当前自然周的数据：

- 本周起点：本周一。
- 本周终点：今天。
- 巡检最新日期：今天，写入报告 JSON 根字段 `inspection_date`。
- 忽略本周一之前的所有每日巡检 JSON，即使文件存在也不要放进 HTML。
- 不要补齐没有巡检 JSON 的日期；缺失日期不画点。

折线图规则：

- 延期提测率卡片必须在同一张折线图里画 3 条线：
  - `planned_test_requirements`：计划提测需求数
  - `delayed_test_requirements`：延期提测需求数
  - `delay_test_rate_okr`：延期提测率
- 延期上线率卡片必须在同一张折线图里画 3 条线：
  - `planned_online_requirements`：计划上线需求数
  - `delayed_online_requirements`：延期上线需求数
  - `delay_online_rate`：延期上线率
- 技术改造工时占比卡片画 1 条线：`technical_refactor_working_hours_rate`。
- 双周交付率卡片画 1 条线：`biweekly_delivery_rate`。
- HTML 模板支持点击折线或图例。点击后高亮该折线，并切换卡片顶部的最新值、较周初、最新日期。
- 卡片顶部“最新日期”必须展示 `inspection_date`，也就是当天巡检日期；不要用折线里最后一个数据点的日期替代。
- 不同单位的线条在同一图中按各自数值区间归一化绘制，展示值仍使用每日 JSON 中的原始值。

每个指标还要贴当天巡检截图。HTML 报告输出在：

```text
index.html
```

聚合脚本会把当天截图复制到报告输出目录下：

```text
assets/screenshots/
```

统一报告 JSON 中的截图路径必须使用报告内部相对路径，禁止写本机绝对路径、`file://` 路径或指向仓库外层目录的 `../../...` 路径。最终 HTML 直接通过 `assets/screenshots/...` 相对路径渲染图片，不要写入 `screenshot_base64url` / `query_screenshot_base64url`，也不要生成 `data:image/png;base64,...`。最终 HTML 页面不要展示原始文件地址。

| 指标 | HTML 中使用的截图路径 |
| --- | --- |
| 延期提测率 | `assets/screenshots/delay_test_rate.png` |
| 延期上线率 | `assets/screenshots/delay_online_rate.png` |
| 技术改造工时占比 | `assets/screenshots/technical_refactor_working_hours.png` |
| 双周交付率 | `assets/screenshots/bi_weekly_delivery_rate.png` |
| 持续交付 | `assets/screenshots/continuous_delivery.png` |

HTML 内置的报告 JSON 使用这个结构：

```json
{
  "generated_at": "2026-04-19 10:30:00",
  "inspection_date": "2026-04-19",
  "department_c3": "支付方案研发部",
  "time_range": {
    "start_date": "2026-04-13",
    "end_date": "2026-04-19"
  },
  "focus_series": [
    {
      "indicator_type": "delay_test_rate",
      "name": "延期提测率",
      "default_metric_key": "delay_test_rate_okr",
      "screenshot": "assets/screenshots/delay_test_rate.png",
      "screenshot_label": "当天巡检截图",
      "metrics": [
        {
          "key": "planned_test_requirements",
          "label": "计划提测需求数",
          "unit": "count",
          "points": [
            { "date": "2026-04-13", "value": 18, "unit": "count" }
          ]
        },
        {
          "key": "delayed_test_requirements",
          "label": "延期提测需求数",
          "unit": "count",
          "points": [
            { "date": "2026-04-13", "value": 2, "unit": "count" }
          ]
        },
        {
          "key": "delay_test_rate_okr",
          "label": "延期提测率",
          "unit": "%",
          "points": [
            { "date": "2026-04-13", "value": 11.1, "unit": "%" }
          ]
        }
      ]
    }
  ]
}
```

输出文件：

```text
joyclaw-daily-inspection-orchestrator-skill/out/weekly-inspection-summary.json
index.html
```

模板已经内置折线图渲染逻辑，不需要外部图表库。JoyClaw 不要改模板结构，只替换 JSON 数据。

## 总汇总

JoyClaw 确认延期提测率、延期上线率、技术改造工时占比、AI 巡检、持续交付的当天 JSON 已生成，并完成双周交付率截图识别或历史 JSON 回填后，从项目根目录运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python joyclaw-daily-inspection-orchestrator-skill/scripts/aggregate_report.py
```

默认输出：

```text
joyclaw-daily-inspection-orchestrator-skill/out/weekly-inspection-summary.json
index.html
```

脚本不接受自定义日期范围；本报告只展示当前自然周，也就是本周一到今天。

即使 `out/history/` 里存在上周、前周或更早的每日 JSON，JoyClaw 和聚合脚本都必须过滤掉，不得放入 HTML 折线图。

## AI 结果集成

AI 巡检只展示当天结果，不画本周趋势。

JoyClaw 读取：

```text
AI-inspection/out/non_deep_user_names_YYYY-MM-DD.json
```

如果该文件不存在，可以兜底读取：

```text
AI-inspection/out/non_deep_users_YYYY-MM-DD.json
```

并筛选：

```text
是否深度用户 = 否
```

统一报告 JSON 中增加：

```json
{
  "ai_inspection": {
    "date": "2026-04-18",
    "indicator_type": "ai_non_deep_users",
    "indicator_name": "AI深度用户占比-软开测试岗",
    "status": "success",
    "source_json": "../../AI-inspection/out/non_deep_users_2026-04-18.json",
    "output_json": "../../AI-inspection/out/non_deep_user_names_2026-04-18.json",
    "count": 2,
    "names": ["蔡永乐", "常姜洲"],
    "users": [
      {
        "erp": "caiyongle",
        "name": "蔡永乐",
        "ai_code_local_submit_rate": 0.0,
        "is_deep_user": "否"
      }
    ]
  }
}
```

HTML 模板会把 `ai_inspection.users` 渲染为简约名单卡片，并展示人数。

## 持续交付结果集成

持续交付只展示当天结果，不画趋势。

持续交付脚本会先生成当天 JSON，JoyClaw 只需要校验字段并运行总编排。不要让总报告直接读截图，也不要只在对话中给出数值。

JoyClaw 读取：

```text
ContinuousDelivery-inspection/out/continuous_delivery_YYYY-MM-DD.json
```

统一报告 JSON 中增加：

```json
{
  "continuous_delivery": {
    "date": "2026-04-18",
    "indicator_type": "continuous_delivery",
    "indicator_name": "持续交付",
    "department_c3": "支付方案研发部",
    "status": "success",
    "metrics": {
      "team_space_dev_test_online_requirements": 62,
      "team_space_continuous_delivery_dev_test_online_requirements": 51,
      "continuous_delivery_team_space_online_requirement_rate": 82.26
    },
    "unit": {
      "team_space_dev_test_online_requirements": "count",
      "team_space_continuous_delivery_dev_test_online_requirements": "count",
      "continuous_delivery_team_space_online_requirement_rate": "%"
    },
    "source": {
      "query_screenshot": "assets/screenshots/continuous_delivery.png",
      "json": "../../ContinuousDelivery-inspection/out/continuous_delivery_2026-04-18.json"
    }
  }
}
```

HTML 模板会展示三项指标值，并贴当天三卡片截图。

如果当天持续交付 JSON 缺失，JoyClaw 必须回到 `ContinuousDelivery-inspection/SKILL.md` 的规则，先重新执行持续交付脚本生成当天 JSON，再重新生成总 HTML。

## 成功标准

- OKR 4 个单项 skill 均已执行，或失败项有明确错误截图与错误信息。
- AI 巡检已执行，并且 JoyClaw 已生成或兜底读取当天非深度用户名单。
- 持续交付巡检已执行，并且当天三指标 JSON 已生成。
- 延期提测率、延期上线率、技术改造工时占比都存在本周 `out/history/*.json`；双周交付率至少存在 `out/history/*.json` 或 `out/weekly-trend-from-screenshot.json`。
- 总 JSON 包含 4 个指标的本周历史序列。
- 总 JSON 包含 `ai_inspection`。
- 总 JSON 包含 `continuous_delivery`。
- HTML 报告可以直接打开查看；最终 HTML 通过报告内部相对路径展示截图，上传 Web 时需要同时上传 `assets/screenshots/` 目录，且 HTML 中不得出现 base64 截图载荷、本机绝对截图路径或 `data:image/png;base64,...`。

## 清理规则

不要在生成总报告前删除历史 JSON。

如果用户要求周五清理本周巡检 JSON，只能在确认以下文件已生成后清理：

```text
joyclaw-daily-inspection-orchestrator-skill/out/weekly-inspection-summary.json
index.html
```
