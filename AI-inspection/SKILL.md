---
name: ai-non-deep-user-inspection
description: 巡检 AI 深度用户数据；页面脚本下载并生成当天 JSON，JoyClaw 读取当天 JSON，提取“是否深度用户”为“否”的用户姓名并输出人名结果 JSON。
---

# ai-non-deep-user-inspection

## 目标

从当天 AI 巡检 JSON 中找出：

```text
是否深度用户 = 否
```

并输出这些人的姓名列表。

## 执行顺序

从 `AI-inspection` 目录运行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

脚本职责：

- 打开 AI 深度用户占比页面。
- 切到日维度。
- 设置昨天到今天的日期范围。
- 下载 `AI深度用户占比-软开测试岗(%)` Excel。
- 生成当天源数据 JSON：

```text
out/non_deep_users_YYYY-MM-DD.json
```

JoyClaw 职责：

- 读取当天源数据 JSON。
- 筛选 `是否深度用户` 字段值为 `否` 的记录。
- 输出只用于汇总报告的人名结果 JSON。
- 不读取截图，也不从页面视觉结果推断人员名单。

## 输入

当天源数据文件：

```text
AI-inspection/out/non_deep_users_YYYY-MM-DD.json
```

源 JSON 是数组，每个元素可能包含：

```json
{
  "用户erp": "caiyongle",
  "用户姓名": "蔡永乐",
  "AI代码本地提交占比": 0.0,
  "是否深度用户": "否"
}
```

## 输出

JoyClaw 输出：

```text
AI-inspection/out/non_deep_user_names_YYYY-MM-DD.json
```

格式：

```json
{
  "date": "2026-04-18",
  "indicator_type": "ai_non_deep_users",
  "indicator_name": "AI深度用户占比-软开测试岗",
  "status": "success",
  "source_json": "out/non_deep_users_2026-04-18.json",
  "filter": {
    "field": "是否深度用户",
    "value": "否"
  },
  "count": 3,
  "names": ["蔡永乐", "常姜洲", "常彦升"],
  "users": [
    {
      "erp": "caiyongle",
      "name": "蔡永乐",
      "ai_code_local_submit_rate": 0.0,
      "is_deep_user": "否"
    }
  ]
}
```

## 规则

- 只处理当天 JSON，不读取昨天或更早的数据。
- 只以 `AI-inspection/out/non_deep_users_YYYY-MM-DD.json` 为数据源。
- 以 `用户姓名` 作为展示人名。
- 如果 `用户姓名` 为空，使用 `用户erp` 兜底。
- 只输出 `是否深度用户` 为 `否` 的人。
- 输出 `names` 时按源 JSON 顺序保留，不要排序。
- 如果当天源 JSON 不存在，输出 `status: "missing"`，`names: []`，并写明 `error`。
- 如果当天没有非深度用户，输出 `status: "success"`，`count: 0`，`names: []`。
