# JoyClaw 每日巡检项目帮助文档

## 1. 项目简介

这是一个给 JoyClaw 使用的每日巡检项目，目标是把 **OKR 巡检、AI 巡检、持续交付巡检** 三类结果统一收集起来，最终生成一份可查看的周报 HTML。

当前固定巡检部门：

- `支付方案研发部`

当前项目包含 3 类巡检内容：

1. **OKR 巡检**
   - 延期提测率
   - 延期上线率
   - 技术改造工时占比
   - 双周交付率
2. **AI 巡检**
   - 从当天 AI 巡检结果里找出“是否深度用户 = 否”的人员名单
3. **持续交付巡检**
   - 团队空间开发测试上线需求数
   - 团队空间_持需交付_开发测试上线需求数
   - 持续交付_团队空间上线需求占比


## 2. 根目录结构

项目根目录主要结构如下：

```text
daily-inspection-skill/
├── OKR-inspection/
│   ├── delay-test-rate-skill/
│   ├── delay-online-rate-skill/
│   ├── technical-refactor-working-hours-skill/
│   └── bi-weekly-delivery-rate-skill/
├── AI-inspection/
├── ContinuousDelivery-inspection/
└── joyclaw-daily-inspection-orchestrator-skill/
```

各目录职责：

- `OKR-inspection/`
  - 4 个 OKR 巡检 skill
- `AI-inspection/`
  - AI 深度用户占比巡检
- `ContinuousDelivery-inspection/`
  - 持续交付三卡片巡检
- `joyclaw-daily-inspection-orchestrator-skill/`
  - 总编排
  - 汇总 JSON
  - HTML 模板
  - 最终周报 HTML


## 3. 当前巡检职责划分

### 3.1 页面自动化脚本做什么

大多数 `scripts/run_skill.py` 负责：

- 打开页面
- 设置筛选项
- 点击查询
- 保存截图或下载源文件

其中：

- 延期提测率、延期上线率、技术改造工时占比
  - 会在查询后直接从目标卡片表格第一行提取当天值，并写入每日 JSON
- 双周交付率
  - 仍然只截图，由 JoyClaw 做视觉识别
- AI 巡检
  - 下载 Excel 后直接生成当天源 JSON
- 持续交付
  - 仍然只截图，由 JoyClaw 生成当天 JSON


### 3.2 JoyClaw 做什么

JoyClaw 主要负责：

- 读取截图或源数据
- 在脚本未直接生成当天 JSON 时，按固定字段补齐当天 JSON
- 读取历史 JSON
- 生成本周趋势
- 把结果汇总进统一 HTML


### 3.3 双周交付率当前口径

双周交付率当前和前面三个 OKR skill 不同：

- 脚本只负责查询和截图
- JoyClaw 负责从截图中读取指标
- JoyClaw 负责生成当天 JSON 和本周趋势 JSON


## 4. 巡检顺序

统一执行顺序必须是：

1. 先巡检 **OKR**
2. 再巡检 **AI**
3. 再巡检 **持续交付**
4. 最后跑 **总编排**

OKR 内部顺序：

1. `delay-test-rate-skill`
2. `delay-online-rate-skill`
3. `technical-refactor-working-hours-skill`
4. `bi-weekly-delivery-rate-skill`


## 5. 快速开始

### 5.1 运行环境

当前项目默认使用这个 Python 环境：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python
```

执行前建议确认：

- 本机能正常打开相关 JD 内网页面
- Playwright 浏览器环境可用
- 当前账号已登录需要的系统


### 5.2 单项执行命令

#### OKR 四项

分别进入各自目录执行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

适用目录：

- `OKR-inspection/delay-test-rate-skill`
- `OKR-inspection/delay-online-rate-skill`
- `OKR-inspection/technical-refactor-working-hours-skill`
- `OKR-inspection/bi-weekly-delivery-rate-skill`

#### AI 巡检

在 `AI-inspection` 目录执行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

#### 持续交付巡检

在 `ContinuousDelivery-inspection` 目录执行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python scripts/run_skill.py
```

#### 总编排

在项目根目录执行：

```bash
/Users/gaojingqi.5/miniconda3/envs/xunjian/bin/python joyclaw-daily-inspection-orchestrator-skill/scripts/aggregate_report.py
```


## 6. 标准执行链路

### 第一步：跑 OKR 四项

#### 延期提测率

脚本会从目标卡片表格第一行直接提取当天数据，并生成：

```text
OKR-inspection/delay-test-rate-skill/out/history/YYYY-MM-DD.json
```

如缺少本周历史日期，再由 JoyClaw 补充：

```text
OKR-inspection/delay-test-rate-skill/out/weekly-trend-from-screenshot.json
```

#### 延期上线率

脚本会从目标卡片表格第一行直接提取当天数据，并生成：

```text
OKR-inspection/delay-online-rate-skill/out/history/YYYY-MM-DD.json
```

如缺少本周历史日期，再由 JoyClaw 补充：

```text
OKR-inspection/delay-online-rate-skill/out/weekly-trend-from-screenshot.json
```

#### 技术改造工时占比

脚本会从目标卡片表格第一行直接提取当天数据，并生成：

```text
OKR-inspection/technical-refactor-working-hours-skill/out/history/YYYY-MM-DD.json
```

如缺少本周历史日期，再由 JoyClaw 补充：

```text
OKR-inspection/technical-refactor-working-hours-skill/out/weekly-trend-from-screenshot.json
```

#### 双周交付率

脚本产出截图，JoyClaw 负责识别并生成：

```text
OKR-inspection/bi-weekly-delivery-rate-skill/out/history/YYYY-MM-DD.json
OKR-inspection/bi-weekly-delivery-rate-skill/out/weekly-trend-from-screenshot.json
```

说明：

- 当前只关注一个指标：`biweekly_delivery_rate`
- 不再输出完成需求数、总需求数、双周内交付需求数


### 第二步：跑 AI 巡检

AI 脚本会下载 Excel，并生成当天源 JSON：

```text
AI-inspection/out/non_deep_users_YYYY-MM-DD.json
```

然后 JoyClaw 再从里面筛选 `是否深度用户 = 否`，输出：

```text
AI-inspection/out/non_deep_user_names_YYYY-MM-DD.json
```


### 第三步：跑持续交付巡检

持续交付脚本会生成：

```text
ContinuousDelivery-inspection/out/three_cards.png
```

然后 JoyClaw 需要从这张图里提取 3 个指标，并写入：

```text
ContinuousDelivery-inspection/out/continuous_delivery_YYYY-MM-DD.json
```


### 第四步：跑总编排

总编排会读取前面产出的 JSON，并生成：

```text
joyclaw-daily-inspection-orchestrator-skill/out/weekly-inspection-summary.json
joyclaw-daily-inspection-orchestrator-skill/out/weekly-inspection-report.html
```


## 7. 各模块输入输出一览

| 模块 | 输入 | 输出 |
| --- | --- | --- |
| 延期提测率 | 查询截图 | `out/history/YYYY-MM-DD.json`、`out/weekly-trend-from-screenshot.json` |
| 延期上线率 | 查询截图 | `out/history/YYYY-MM-DD.json`、`out/weekly-trend-from-screenshot.json` |
| 技术改造工时占比 | 查询截图 | `out/history/YYYY-MM-DD.json`、`out/weekly-trend-from-screenshot.json` |
| 双周交付率 | 查询截图 | `out/history/YYYY-MM-DD.json`、`out/weekly-trend-from-screenshot.json` |
| AI 巡检 | 下载 Excel | `out/non_deep_users_YYYY-MM-DD.json`、`out/non_deep_user_names_YYYY-MM-DD.json` |
| 持续交付 | 三卡片截图 | `out/continuous_delivery_YYYY-MM-DD.json` |
| 总编排 | 各模块 JSON | `weekly-inspection-summary.json`、`weekly-inspection-report.html` |


## 8. 当前报表规则

### 8.1 时间范围

最终 HTML 只展示：

- **本周周一到今天**

不会展示前一周或更早的自然周数据。

规则：

- 本周起点：本周一
- 本周终点：今天
- 不补不存在的日期
- 缺失日期不画点


### 8.2 HTML 模板位置

模板文件：

[weekly-line-report-template.html](/Users/gaojingqi.5/Desktop/daily-inspection-skill/joyclaw-daily-inspection-orchestrator-skill/assets/weekly-line-report-template.html)

最终产物：

[weekly-inspection-report.html](/Users/gaojingqi.5/Desktop/daily-inspection-skill/joyclaw-daily-inspection-orchestrator-skill/out/weekly-inspection-report.html)


### 8.3 折线图规则

- 延期提测率：1 张图 3 条线
  - `planned_test_requirements`
  - `delayed_test_requirements`
  - `delay_test_rate_okr`
- 延期上线率：1 张图 3 条线
  - `planned_online_requirements`
  - `delayed_online_requirements`
  - `delay_online_rate`
- 技术改造工时占比：1 条线
  - `technical_refactor_working_hours_rate`
- 双周交付率：1 条线
  - `biweekly_delivery_rate`

支持点击图例或折线高亮查看。


### 8.4 截图处理规则

最终 HTML 中的截图已经做过处理：

- 不暴露本机绝对路径
- 不保留原始文件地址
- 不使用 `data:image`
- 通过 `base64url + Blob URL` 方式在页面内显示

所以最终上传展示时，优先使用最终 HTML 文件，不要依赖本地路径。


## 9. 最新日期规则

最终 HTML 卡片顶部的“最新日期”使用：

- 报告 JSON 根字段 `inspection_date`

也就是：

- **当天巡检日期**

不是折线图最后一个数据点的日期。


## 10. 关键文件位置

### 根编排

- [joyclaw-daily-inspection-orchestrator-skill/SKILL.md](/Users/gaojingqi.5/Desktop/daily-inspection-skill/joyclaw-daily-inspection-orchestrator-skill/SKILL.md)
- [aggregate_report.py](/Users/gaojingqi.5/Desktop/daily-inspection-skill/joyclaw-daily-inspection-orchestrator-skill/scripts/aggregate_report.py)

### OKR

- [delay-test-rate-skill](/Users/gaojingqi.5/Desktop/daily-inspection-skill/OKR-inspection/delay-test-rate-skill)
- [delay-online-rate-skill](/Users/gaojingqi.5/Desktop/daily-inspection-skill/OKR-inspection/delay-online-rate-skill)
- [technical-refactor-working-hours-skill](/Users/gaojingqi.5/Desktop/daily-inspection-skill/OKR-inspection/technical-refactor-working-hours-skill)
- [bi-weekly-delivery-rate-skill](/Users/gaojingqi.5/Desktop/daily-inspection-skill/OKR-inspection/bi-weekly-delivery-rate-skill)

### AI

- [AI-inspection/SKILL.md](/Users/gaojingqi.5/Desktop/daily-inspection-skill/AI-inspection/SKILL.md)

### 持续交付

- [ContinuousDelivery-inspection/SKILL.md](/Users/gaojingqi.5/Desktop/daily-inspection-skill/ContinuousDelivery-inspection/SKILL.md)


## 11. 常见问题

### 11.1 为什么有截图但没有当天 JSON

先看是哪类模块：

- 延期提测率 / 延期上线率 / 技术改造工时占比
  - 这三项默认还是 JoyClaw 读截图生成 JSON
- 双周交付率
  - 这项现在也由 JoyClaw 读截图生成 JSON
- 持续交付
  - 需要 JoyClaw 从 `three_cards.png` 生成 JSON
- AI
  - 先有源 JSON，再有人名 JSON


### 11.2 双周交付率提取失败怎么办

优先检查：

- 页面是否成功查询
- `out/03_after_query.png` 是否生成
- JoyClaw 是否已经根据截图生成 `out/history/YYYY-MM-DD.json`
- 截图里是否能清晰看到双周交付率目标区域

双周交付率已经改回视觉识别路线，所以重点看截图质量、目标卡片是否完整可见，以及 JoyClaw 是否按截图成功回填了每日 JSON。


### 11.3 为什么 HTML 上传后变成下载

这通常不是 HTML 内容问题，而是文件托管平台把它当附件下载了。

要想在线看，需要托管平台返回类似：

- `Content-Type: text/html`
- `Content-Disposition: inline`

如果平台给的是 `/download/...` 这种接口，浏览器大概率会直接下载。


### 11.4 为什么线上看不到图片

当前 HTML 已经避免使用本机绝对路径，但如果目标平台限制：

- `blob:` 图片
- 内联脚本

那页面里的截图仍可能加载失败。这时需要换支持静态 HTML 预览的平台。


## 12. 推荐交接阅读顺序

如果是第一次接手这个项目，建议按这个顺序看：

1. 本文档
2. [joyclaw-daily-inspection-orchestrator-skill/SKILL.md](/Users/gaojingqi.5/Desktop/daily-inspection-skill/joyclaw-daily-inspection-orchestrator-skill/SKILL.md)
3. 各模块自己的 `SKILL.md`
4. `joyclaw-daily-inspection-orchestrator-skill/scripts/aggregate_report.py`
5. 最终 HTML 模板


## 13. 当前项目默认事实

- 最终总输出和总编排 skill 都在根目录的 `joyclaw-daily-inspection-orchestrator-skill/`
- HTML 只展示本周数据
- HTML 会集成 OKR、AI、持续交付三部分内容
- 双周交付率只关注 `biweekly_delivery_rate`
- HTML 截图不允许暴露原始本地路径
