from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
SKILL_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = SKILL_DIR / "out"
HTML_OUTPUT_PATH = ROOT_DIR / "index.html"
REPORT_SCREENSHOT_DIR = ROOT_DIR / "assets" / "screenshots"
TEMPLATE_PATH = SKILL_DIR / "assets" / "weekly-line-report-template.html"
AI_DIR = ROOT_DIR / "AI-inspection"
CONTINUOUS_DELIVERY_DIR = ROOT_DIR / "ContinuousDelivery-inspection"


@dataclass(frozen=True)
class MetricConfig:
    key: str
    label: str
    unit: str


@dataclass(frozen=True)
class SkillConfig:
    directory: str
    skill_name: str
    indicator_type: str
    indicator_name: str
    department_c3: str
    screenshot: str
    focus_metric_key: str
    metrics: tuple[MetricConfig, ...]


SKILLS: tuple[SkillConfig, ...] = (
    SkillConfig(
        directory="OKR-inspection/delay-test-rate-skill",
        skill_name="delay-test-rate-inspection",
        indicator_type="delay_test_rate",
        indicator_name="延期提测率 - 周（5->4）-汇总-C3 维度",
        department_c3="支付方案研发部",
        screenshot="out/05_after_query.png",
        focus_metric_key="delay_test_rate_okr",
        metrics=(
            MetricConfig("planned_test_requirements", "计划提测需求数", "count"),
            MetricConfig("delayed_test_requirements", "延期提测需求数", "count"),
            MetricConfig("delay_test_rate_okr", "延期提测率（OKR 考核指标）", "%"),
        ),
    ),
    SkillConfig(
        directory="OKR-inspection/delay-online-rate-skill",
        skill_name="delay-online-rate-inspection",
        indicator_type="delay_online_rate",
        indicator_name="延期上线率 - 周（5->4）-汇总-C3 维度",
        department_c3="支付方案研发部",
        screenshot="out/05_after_query.png",
        focus_metric_key="delay_online_rate",
        metrics=(
            MetricConfig("planned_online_requirements", "计划上线需求数", "count"),
            MetricConfig("delayed_online_requirements", "延期上线需求数", "count"),
            MetricConfig("delay_online_rate", "延期上线率", "%"),
        ),
    ),
    SkillConfig(
        directory="OKR-inspection/technical-refactor-working-hours-skill",
        skill_name="technical-refactor-working-hours-inspection",
        indicator_type="technical_refactor_working_hours",
        indicator_name="技术改造工时占比 - 周（5->4）-汇总-C3 维度",
        department_c3="支付方案研发部",
        screenshot="out/05_after_query.png",
        focus_metric_key="technical_refactor_working_hours_rate",
        metrics=(
            MetricConfig("total_working_hours", "总工时/填报工时", "hour"),
            MetricConfig("technical_refactor_working_hours", "技术改造工时", "hour"),
            MetricConfig("technical_refactor_working_hours_rate", "技术改造工时占比", "%"),
        ),
    ),
    SkillConfig(
        directory="OKR-inspection/bi-weekly-delivery-rate-skill",
        skill_name="bi-weekly-delivery-rate-inspection",
        indicator_type="bi_weekly_delivery_rate",
        indicator_name="双周交付率",
        department_c3="支付方案研发部",
        screenshot="out/03_after_query.png",
        focus_metric_key="biweekly_delivery_rate",
        metrics=(
            MetricConfig("biweekly_delivery_rate", "双周交付率", "%"),
        ),
    ),
)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def current_week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_numberish(value: Any) -> Any:
    if isinstance(value, (int, float)) or value is None:
        return value
    if not isinstance(value, str):
        return value

    raw = value.strip().replace(",", "")
    if not raw:
        return None
    if raw.endswith("%"):
        raw = raw[:-1].strip()
    if raw.lstrip("-").isdigit():
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return value


def copy_screenshot_asset(source_path: Path, asset_name: str) -> str:
    if not source_path.exists():
        return ""

    REPORT_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    target_path = REPORT_SCREENSHOT_DIR / asset_name
    shutil.copy2(source_path, target_path)
    return f"assets/screenshots/{asset_name}"


def skill_screenshot_path(config: SkillConfig) -> Path:
    return ROOT_DIR / config.directory / config.screenshot


def skill_screenshot_asset(config: SkillConfig) -> str:
    return copy_screenshot_asset(skill_screenshot_path(config), f"{config.indicator_type}.png")


def continuous_delivery_screenshot_asset() -> str:
    return copy_screenshot_asset(CONTINUOUS_DELIVERY_DIR / "out" / "three_cards.png", "continuous_delivery.png")


def remove_html_file_addresses(payload: Any) -> None:
    """最终 HTML 不暴露本地源文件地址；报告内部截图相对路径保留给 img 使用。"""
    hidden_keys = {"history_dir", "source_json", "output_json", "json"}
    if isinstance(payload, dict):
        for key in list(payload.keys()):
            if key in hidden_keys:
                payload.pop(key, None)
            else:
                remove_html_file_addresses(payload[key])
    elif isinstance(payload, list):
        for item in payload:
            remove_html_file_addresses(item)


def first_present(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value is not None and value != "":
            return value
    return None


def normalize_ai_user(item: dict[str, Any]) -> dict[str, Any]:
    erp = first_present(item, "erp", "用户erp", "用户 erp", "用户ERP")
    name = first_present(item, "name", "用户姓名", "姓名", "用户erp", "用户 erp", "erp")
    submit_rate = first_present(
        item,
        "ai_code_local_submit_rate",
        "AI代码本地提交占比",
        "AI 代码本地提交占比",
        "AI代码本地提交占比(%)",
        "AI 代码本地提交占比(%)",
    )
    return {
        "erp": erp or "",
        "name": name or "",
        "ai_code_local_submit_rate": parse_numberish(submit_rate),
        "is_deep_user": first_present(item, "is_deep_user", "是否深度用户") or "",
    }


def normalize_continuous_delivery(data: dict[str, Any], today: date) -> dict[str, Any]:
    day = today.isoformat()
    metrics = data.get("metrics") or {}
    units = data.get("unit") or {}
    return {
        "date": data.get("date", day),
        "indicator_type": "continuous_delivery",
        "indicator_name": data.get("indicator_name", "持续交付"),
        "department_c3": data.get("department_c3", "支付方案研发部"),
        "status": data.get("status", "success"),
        "metrics": {
            "team_space_dev_test_online_requirements": parse_numberish(
                metrics.get("team_space_dev_test_online_requirements", metrics.get("team_space_dev_test_online_requirement_count"))
            ),
            "team_space_continuous_delivery_dev_test_online_requirements": parse_numberish(
                metrics.get(
                    "team_space_continuous_delivery_dev_test_online_requirements",
                    metrics.get("team_space_continuous_delivery_dev_test_online_requirement_count"),
                )
            ),
            "continuous_delivery_team_space_online_requirement_rate": parse_numberish(
                metrics.get(
                    "continuous_delivery_team_space_online_requirement_rate",
                    metrics.get("continuous_delivery_team_space_online_requirement_ratio"),
                )
            ),
        },
        "unit": {
            "team_space_dev_test_online_requirements": units.get("team_space_dev_test_online_requirements", units.get("team_space_dev_test_online_requirement_count", "count")),
            "team_space_continuous_delivery_dev_test_online_requirements": units.get(
                "team_space_continuous_delivery_dev_test_online_requirements",
                units.get("team_space_continuous_delivery_dev_test_online_requirement_count", "count"),
            ),
            "continuous_delivery_team_space_online_requirement_rate": units.get(
                "continuous_delivery_team_space_online_requirement_rate",
                units.get("continuous_delivery_team_space_online_requirement_ratio", "%"),
            ),
        },
        "source": {
            "query_screenshot": continuous_delivery_screenshot_asset(),
            "json": f"../../ContinuousDelivery-inspection/out/continuous_delivery_{day}.json",
        },
        "error": data.get("error", ""),
    }


def load_continuous_delivery(today: date) -> dict[str, Any]:
    day = today.isoformat()
    json_path = CONTINUOUS_DELIVERY_DIR / "out" / f"continuous_delivery_{day}.json"
    legacy_json_path = CONTINUOUS_DELIVERY_DIR / "out" / "history" / f"{day}.json"
    screenshot_path = CONTINUOUS_DELIVERY_DIR / "out" / "three_cards.png"

    if json_path.exists():
        try:
            return normalize_continuous_delivery(read_json(json_path), today)
        except Exception as exc:
            return {
                "date": day,
                "indicator_type": "continuous_delivery",
                "indicator_name": "持续交付",
                "department_c3": "支付方案研发部",
                "status": "failed",
                "metrics": {
                    "team_space_dev_test_online_requirements": None,
                    "team_space_continuous_delivery_dev_test_online_requirements": None,
                    "continuous_delivery_team_space_online_requirement_rate": None,
                },
                "unit": {
                    "team_space_dev_test_online_requirements": "count",
                    "team_space_continuous_delivery_dev_test_online_requirements": "count",
                    "continuous_delivery_team_space_online_requirement_rate": "%",
                },
                "source": {
                    "query_screenshot": continuous_delivery_screenshot_asset(),
                    "json": f"../../ContinuousDelivery-inspection/out/continuous_delivery_{day}.json",
                },
                "error": str(exc),
            }

    if legacy_json_path.exists():
        try:
            return normalize_continuous_delivery(read_json(legacy_json_path), today)
        except Exception as exc:
            return {
                "date": day,
                "indicator_type": "continuous_delivery",
                "indicator_name": "持续交付",
                "department_c3": "支付方案研发部",
                "status": "failed",
                "metrics": {
                    "team_space_dev_test_online_requirements": None,
                    "team_space_continuous_delivery_dev_test_online_requirements": None,
                    "continuous_delivery_team_space_online_requirement_rate": None,
                },
                "unit": {
                    "team_space_dev_test_online_requirements": "count",
                    "team_space_continuous_delivery_dev_test_online_requirements": "count",
                    "continuous_delivery_team_space_online_requirement_rate": "%",
                },
                "source": {
                    "query_screenshot": continuous_delivery_screenshot_asset(),
                    "json": f"../../ContinuousDelivery-inspection/out/history/{day}.json",
                },
                "error": str(exc),
            }

    return {
        "date": day,
        "indicator_type": "continuous_delivery",
        "indicator_name": "持续交付",
        "department_c3": "支付方案研发部",
        "status": "missing",
        "metrics": {
            "team_space_dev_test_online_requirements": None,
            "team_space_continuous_delivery_dev_test_online_requirements": None,
            "continuous_delivery_team_space_online_requirement_rate": None,
        },
        "unit": {
            "team_space_dev_test_online_requirements": "count",
            "team_space_continuous_delivery_dev_test_online_requirements": "count",
            "continuous_delivery_team_space_online_requirement_rate": "%",
        },
        "source": {
            "query_screenshot": continuous_delivery_screenshot_asset() if screenshot_path.exists() else "",
            "json": f"../../ContinuousDelivery-inspection/out/continuous_delivery_{day}.json",
        },
        "error": "当天持续交付 JSON 不存在",
    }


def load_ai_inspection(today: date) -> dict[str, Any]:
    day = today.isoformat()
    output_json = AI_DIR / "out" / f"non_deep_user_names_{day}.json"
    source_json = AI_DIR / "out" / f"non_deep_users_{day}.json"

    if source_json.exists():
        try:
            raw_data = read_json(source_json)
            raw_users = raw_data if isinstance(raw_data, list) else raw_data.get("users", [])
            users = [
                normalize_ai_user(item)
                for item in raw_users
                if str(first_present(item, "是否深度用户", "is_deep_user") or "").strip() == "否"
            ]
            names = [user["name"] for user in users if user["name"]]
            return {
                "date": day,
                "indicator_type": "ai_non_deep_users",
                "indicator_name": "AI 深度用户占比 - 软开测试岗",
                "status": "success",
                "source_json": f"../../AI-inspection/out/{source_json.name}",
                "output_json": f"../../AI-inspection/out/{output_json.name}" if output_json.exists() else "",
                "count": len(names),
                "names": names,
                "users": users,
            }
        except Exception as exc:
            return {
                "date": day,
                "indicator_type": "ai_non_deep_users",
                "indicator_name": "AI 深度用户占比 - 软开测试岗",
                "status": "failed",
                "source_json": f"../../AI-inspection/out/{source_json.name}",
                "output_json": f"../../AI-inspection/out/{output_json.name}" if output_json.exists() else "",
                "count": 0,
                "names": [],
                "users": [],
                "error": str(exc),
            }

    if output_json.exists():
        try:
            data = read_json(output_json)
            
            # 支持两种格式：对象格式 (有 users/names 字段) 或 数组格式 (直接是用户列表)
            if isinstance(data, dict):
                users = [normalize_ai_user(item) for item in data.get("users", [])]
                names = data.get("names") or [user["name"] for user in users if user["name"]]
                count = data.get("count", len(names))
                status = data.get("status", "success")
            elif isinstance(data, list):
                # 数组格式：直接是用户列表
                users = [normalize_ai_user(item) for item in data]
                names = [user["name"] for user in users if user["name"]]
                count = len(names)
                status = "success"
            else:
                raise ValueError(f"Unexpected data type: {type(data)}")
            
            return {
                "date": day,
                "indicator_type": "ai_non_deep_users",
                "indicator_name": "AI 深度用户占比 - 软开测试岗",
                "status": status,
                "source_json": f"../../AI-inspection/out/{source_json.name}",
                "output_json": f"../../AI-inspection/out/{output_json.name}",
                "count": count,
                "names": names,
                "users": users,
            }
        except Exception as exc:
            return {
                "date": day,
                "indicator_type": "ai_non_deep_users",
                "indicator_name": "AI 深度用户占比 - 软开测试岗",
                "status": "failed",
                "source_json": f"../../AI-inspection/out/{source_json.name}",
                "output_json": f"../../AI-inspection/out/{output_json.name}",
                "count": 0,
                "names": [],
                "users": [],
                "error": str(exc),
            }

    return {
        "date": day,
        "indicator_type": "ai_non_deep_users",
        "indicator_name": "AI 深度用户占比 - 软开测试岗",
        "status": "missing",
        "source_json": f"../../AI-inspection/out/{source_json.name}",
        "output_json": f"../../AI-inspection/out/{output_json.name}",
        "count": 0,
        "names": [],
        "users": [],
        "error": "当天 AI 巡检 JSON 不存在",
    }


def load_history(config: SkillConfig, start_date: date, end_date: date) -> list[dict[str, Any]]:
    history_dir = ROOT_DIR / config.directory / "out" / "history"
    if not history_dir.exists():
        return []

    rows: list[dict[str, Any]] = []
    for path in sorted(history_dir.glob("*.json")):
        try:
            item = read_json(path)
            item_date = parse_date(str(item.get("date", path.stem)))
        except Exception:
            continue

        if start_date <= item_date <= end_date:
            rows.append(item)

    # 如果今天的数据全为 0，使用最近的有效数据替换
    if rows:
        sorted_rows = sorted(rows, key=lambda r: r.get("date", ""))
        today_row = next((r for r in sorted_rows if r.get("date") == end_date.isoformat()), None)
        
        if today_row:
            metrics = today_row.get("metrics", {})
            # 检查是否所有指标都是 0
            all_zero = all(
                (metrics.get(metric.key, 0) or 0) == 0 
                for metric in config.metrics
            )
            
            if all_zero:
                # 查找最近的有效行（从所有历史数据中找，不限于本周）
                all_history = list(history_dir.glob("*.json"))
                valid_row = None
                
                # 按日期排序，从新到旧找
                for json_path in sorted(all_history, key=lambda p: p.stem, reverse=True):
                    try:
                        candidate = read_json(json_path)
                        candidate_date = parse_date(str(candidate.get("date", json_path.stem)))
                        
                        # 跳过今天
                        if candidate_date == end_date:
                            continue
                        
                        # 检查是否有有效数据
                        cand_metrics = candidate.get("metrics", {})
                        if any((cand_metrics.get(m.key, 0) or 0) != 0 for m in config.metrics):
                            valid_row = candidate
                            break
                    except Exception:
                        continue
                
                if valid_row:
                    # 用有效数据替换今天的数据
                    today_row["metrics"] = valid_row["metrics"].copy()
                    # 保留今天的日期，只借用最近一次有效指标值
                    today_row["date"] = end_date.isoformat()

    return sorted(rows, key=lambda row: str(row.get("date", "")))


def load_weekly_trend_from_screenshot(config: SkillConfig, start_date: date, end_date: date) -> list[dict[str, Any]]:
    path = ROOT_DIR / config.directory / "out" / "weekly-trend-from-screenshot.json"
    if not path.exists():
        return []

    try:
        data = read_json(path)
    except Exception:
        return []

    history = data.get("history")
    if not isinstance(history, dict):
        return []

    rows_by_date: dict[str, dict[str, Any]] = {}
    units = {metric.key: metric.unit for metric in config.metrics}

    for metric in config.metrics:
        points = history.get(metric.key) or []
        if not isinstance(points, list):
            continue

        for point in points:
            if not isinstance(point, dict):
                continue

            raw_date = point.get("date")
            if not raw_date:
                continue

            try:
                point_date = parse_date(str(raw_date))
            except Exception:
                continue

            if not start_date <= point_date <= end_date:
                continue

            row = rows_by_date.setdefault(
                point_date.isoformat(),
                {
                    "date": point_date.isoformat(),
                    "indicator_type": config.indicator_type,
                    "indicator_name": config.indicator_name,
                    "department_c3": config.department_c3,
                    "status": data.get("status", "partial"),
                    "metrics": {},
                    "unit": units,
                    "source": {
                        "weekly_trend": f"{config.directory}/out/weekly-trend-from-screenshot.json",
                        "query_screenshot": f"{config.directory}/{config.screenshot}",
                    },
                },
            )
            row["metrics"][metric.key] = point.get("value")

    return [rows_by_date[key] for key in sorted(rows_by_date)]


def build_skill_summary(config: SkillConfig, rows: list[dict[str, Any]], start_date: date, end_date: date) -> dict[str, Any]:
    history: dict[str, list[dict[str, Any]]] = {metric.key: [] for metric in config.metrics}
    metric_units = {metric.key: metric.unit for metric in config.metrics}
    all_dates = set()

    for row in rows:
        metrics = row.get("metrics") or {}
        row_date = row.get("date")
        if row_date:
            all_dates.add(row_date)
        for metric in config.metrics:
            history[metric.key].append(
                {
                    "date": row.get("date"),
                    "value": metrics.get(metric.key),
                    "unit": metric.unit,
                }
            )

    # 如果今天的数据全是 0，使用最近的有效日期范围
    if rows:
        if not all_dates:
            # 从 rows 中提取实际日期
            for row in rows:
                if row.get("date"):
                    all_dates.add(row["date"])
    
    # 确定显示的时间范围：使用有数据的日期范围，最多扩展到本周
    effective_start = start_date
    effective_end = end_date
    
    if all_dates:
        valid_dates = [parse_date(d) for d in all_dates if d]
        if valid_dates:
            min_date = min(valid_dates)
            max_date = max(valid_dates)
            # 确保范围在本周内，但可以包含历史有效数据
            effective_start = min(min_date, start_date)
            effective_end = max(max_date, end_date)
            # 但上限不超过今天
            if effective_end > end_date:
                effective_end = end_date

    statuses = {str(row.get("status", "success")) for row in rows}
    status = "success" if rows and statuses == {"success"} else "partial" if rows else "missing"

    return {
        "skill_name": config.skill_name,
        "indicator_type": config.indicator_type,
        "indicator_name": config.indicator_name,
        "department_c3": config.department_c3,
        "time_range": {
            "start_date": effective_start.isoformat(),
            "end_date": effective_end.isoformat(),
        },
        "status": status,
        "focus_metric_key": config.focus_metric_key,
        "history": history,
        "unit": metric_units,
        "source": {
            "history_dir": f"{config.directory}/out/history",
            "query_screenshot": skill_screenshot_asset(config),
        },
    }


def render_html(summary: dict[str, Any], output_path: Path) -> None:
    payload = json.loads(json.dumps({
        **summary,
        "generated_at": summary.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "focus_series": summary.get("focus_series") or build_focus_series(summary),
    }, ensure_ascii=False))
    remove_html_file_addresses(payload)
    content = TEMPLATE_PATH.read_text(encoding="utf-8").replace(
        "__JOYCLAW_WEEKLY_REPORT_JSON__",
        json.dumps(payload, ensure_ascii=False, indent=2),
    )
    output_path.write_text(content, encoding="utf-8")


def build_focus_series(summary: dict[str, Any]) -> list[dict[str, Any]]:
    configs = {config.indicator_type: config for config in SKILLS}
    multi_metric_indicators = {"delay_test_rate", "delay_online_rate"}
    series = []
    for indicator in summary.get("indicators", []):
        config = configs.get(indicator.get("indicator_type"))
        if not config:
            continue

        if config.indicator_type in multi_metric_indicators:
            metrics = config.metrics
        else:
            metrics = tuple(metric for metric in config.metrics if metric.key == config.focus_metric_key)

        series.append(
            {
                "indicator_type": config.indicator_type,
                "name": {
                    "delay_test_rate": "延期提测率",
                    "delay_online_rate": "延期上线率",
                }.get(config.indicator_type, next(metric.label for metric in metrics)),
                "indicator_name": config.indicator_name,
                "default_metric_key": config.focus_metric_key,
                "screenshot": indicator.get("source", {}).get("query_screenshot") or skill_screenshot_asset(config),
                "screenshot_label": "当天巡检截图",
                "metrics": [
                    {
                        "key": metric.key,
                        "label": metric.label,
                        "unit": metric.unit,
                        "points": indicator.get("history", {}).get(metric.key, []),
                    }
                    for metric in metrics
                ],
            }
        )
    return series


def build_summary(start_date: date, end_date: date) -> dict[str, Any]:
    indicators = []
    for config in SKILLS:
        rows = load_history(config, start_date, end_date)
        screenshot_rows = load_weekly_trend_from_screenshot(config, start_date, end_date)
        if screenshot_rows and len(screenshot_rows) > len(rows):
            rows = screenshot_rows
        indicators.append(build_skill_summary(config, rows, start_date, end_date))

    statuses = {item["status"] for item in indicators}
    status = "success" if statuses == {"success"} else "partial" if "success" in statuses or "partial" in statuses else "missing"

    return {
        "skill_name": "joyclaw-daily-inspection-orchestrator",
        "department_c3": "支付方案研发部",
        "time_range": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "status": status,
        "indicators": indicators,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate current-week JoyClaw inspection history into JSON and HTML reports.")
    parser.parse_args()

    today = date.today()
    start_date = current_week_start(today)
    end_date = today

    OUT_DIR.mkdir(exist_ok=True)
    summary = build_summary(start_date, end_date)
    summary["inspection_date"] = today.isoformat()
    summary["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary["focus_series"] = build_focus_series(summary)
    summary["ai_inspection"] = load_ai_inspection(today)
    summary["continuous_delivery"] = load_continuous_delivery(today)

    json_path = OUT_DIR / "weekly-inspection-summary.json"
    html_path = HTML_OUTPUT_PATH

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    render_html(summary, html_path)

    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
