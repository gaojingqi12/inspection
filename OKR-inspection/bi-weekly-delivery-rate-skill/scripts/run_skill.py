import json
import re
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError, sync_playwright

URL = "https://ine.jd.com/portalDetail?location=%252Fdetail%253FportalUuid%253D20211122143031511247544858946828%252325738583d55e87d7698eb308460aff29"

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "out"
HISTORY_DIR = OUT_DIR / "history"

INDICATOR_NAME = "双周交付率"
CATEGORY_NAME = "支付方案"
DEPARTMENT_C3 = "支付方案研发部"
QUERY_SCREENSHOT_PATH = "out/03_after_query.png"


def log(msg: str):
    print(f"[DEBUG] {msg}")


def save_debug_screenshot(page, out_dir: Path, name: str):
    path = out_dir / name
    page.screenshot(path=str(path), full_page=True)
    log(f"已保存截图: {path}")


def dump_frames(page):
    try:
        log(f"当前标题: {page.title()}")
    except Exception:
        pass
    log(f"当前URL: {page.url}")
    log(f"frame 数量: {len(page.frames)}")
    for idx, frame in enumerate(page.frames):
        try:
            log(f"frame[{idx}] url = {frame.url}")
        except Exception as exc:
            log(f"读取 frame[{idx}] url 失败: {exc}")


def get_menu_frame(page, timeout_ms=15000):
    import time

    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        for idx, frame in enumerate(page.frames):
            try:
                if "bi.jd.com/detail" in (frame.url or ""):
                    log(f"命中菜单 frame[{idx}]")
                    return frame
            except Exception as exc:
                log(f"读取菜单 frame[{idx}] url 失败: {exc}")
        page.wait_for_timeout(500)

    raise Exception("没找到左侧菜单所在 frame")


def collapse_sidebar(page):
    menu_frame = get_menu_frame(page)
    btn = menu_frame.locator(".list-collapse").first
    btn.wait_for(state="visible", timeout=8000)
    btn.click()
    page.wait_for_timeout(1000)
    log("已点击收起侧边栏")


def get_dashboard_frame(page, timeout_ms=30000):
    import time

    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        for idx, frame in enumerate(page.frames):
            try:
                url = frame.url or ""
                log(f"轮询 frame[{idx}] url = {url}")
                if "jddbi.jd.com/export/dashboard" in url:
                    log(f"命中 dashboard frame[{idx}]")
                    return frame
            except Exception as exc:
                log(f"读取 frame[{idx}] url 失败: {exc}")
        page.wait_for_timeout(1000)

    raise Exception("等待超时：没找到目标 dashboard iframe")


def get_last_friday_and_today():
    today = date.today()
    days_since_friday = (today.weekday() - 4) % 7
    if days_since_friday == 0:
        days_since_friday = 7
    last_friday = today - timedelta(days=days_since_friday)
    return last_friday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def get_visible_filter_panel(frame):
    frame.page.wait_for_timeout(1000)

    panels = frame.locator(".filter-list")
    count = panels.count()
    log(f"匹配到 filter-list 数量: {count}")

    for i in range(count):
        panel = panels.nth(i)
        try:
            if panel.is_visible():
                log(f"命中可见筛选面板 panel[{i}]")
                return panel
        except Exception as exc:
            log(f"panel[{i}] 检查失败: {exc}")

    raise Exception(f"没找到可见的 filter-list，当前共匹配到 {count} 个")


def find_filter_item(panel, label_text: str):
    items = panel.locator(".filter-item")
    count = items.count()

    for i in range(count):
        item = items.nth(i)
        try:
            label = item.locator("span").first.inner_text().strip()
            label = label.replace("：", "").replace(":", "").strip()
            if label_text in label:
                return item
        except Exception:
            pass

    raise Exception(f"没找到筛选项: {label_text}")


def set_snapshot_latest_day(frame):
    panel = get_visible_filter_panel(frame)
    item = find_filter_item(panel, "快照日期")
    input_box = item.locator("input.el-input__inner").first
    input_box.wait_for(state="visible", timeout=5000)
    try:
        log(f"快照日期当前值: {input_box.input_value()}")
    except Exception:
        pass
    log("已保留：快照日期 = 最新日")


def fill_complete_date_range(frame):
    start_date, end_date = get_last_friday_and_today()
    log(f"卡片完成日期范围: {start_date} ~ {end_date}")

    panel = get_visible_filter_panel(frame)
    item = find_filter_item(panel, "卡片完成日期")

    inputs = item.locator("input.el-input__inner")
    count = inputs.count()
    log(f"卡片完成日期 input 数量: {count}")

    if count < 2:
        raise Exception(f"卡片完成日期 输入框数量异常: {count}")

    inputs.nth(0).scroll_into_view_if_needed()
    inputs.nth(0).click()
    inputs.nth(0).fill(start_date)
    frame.page.keyboard.press("Enter")
    frame.page.wait_for_timeout(500)

    inputs.nth(1).scroll_into_view_if_needed()
    inputs.nth(1).click()
    inputs.nth(1).fill(end_date)
    frame.page.keyboard.press("Enter")
    frame.page.wait_for_timeout(800)

    log("已填写：卡片完成日期")
    return start_date, end_date


def get_visible_popper(frame):
    poppers = frame.locator(".el-popper")
    count = poppers.count()
    for i in range(count):
        popper = poppers.nth(i)
        try:
            if popper.is_visible():
                log(f"命中可见弹层 index={i}")
                return popper
        except Exception:
            pass
    raise Exception("没找到可见的下拉弹层 el-popper")


def open_dropdown(item):
    select_box = item.locator(".el-select").first
    select_box.wait_for(state="visible", timeout=5000)
    select_box.click()
    item.page.wait_for_timeout(800)


def select_department_c3(frame, department_name=DEPARTMENT_C3):
    panel = get_visible_filter_panel(frame)
    item = find_filter_item(panel, "任务处理人部门C3")

    open_dropdown(item)
    log("已点开：任务处理人部门C3 下拉")

    popper = get_visible_popper(frame)
    search_box = None
    candidates = popper.locator('input[placeholder*="请输入"]')
    for i in range(candidates.count()):
        inp = candidates.nth(i)
        try:
            if inp.is_visible():
                search_box = inp
                break
        except Exception:
            pass

    if search_box:
        search_box.click()
        search_box.fill(department_name)
        frame.page.wait_for_timeout(800)
        log(f"已输入搜索词: {department_name}")

    option = popper.get_by_text(department_name, exact=True).first
    option.wait_for(state="visible", timeout=15000)
    option.click()
    frame.page.wait_for_timeout(2000)

    log(f"已选择：任务处理人部门C3 = {department_name}")
    frame.page.keyboard.press("Escape")
    frame.page.wait_for_timeout(500)


def click_query_button(frame):
    query_btn = frame.get_by_text("查询", exact=True).first
    query_btn.wait_for(state="visible", timeout=5000)
    query_btn.click()
    frame.page.wait_for_timeout(5000)
    log("已点击：查询")
    frame.page.wait_for_timeout(15000)


def parse_percentage(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            return round(float(match.group(0)), 2)
    return None


def normalize_percent_value(val: float | None) -> float | None:
    if val is None:
        return None
    if 0 <= val <= 1:
        return round(val * 100, 2)
    return round(val, 2)


def collect_chart_candidates(frame) -> list[dict]:
    charts = frame.locator(".chart-canvas[_echarts_instance_]")
    count = charts.count()
    log(f"页面可见 ECharts 图表数量: {count}")

    if count == 0:
        return []

    summaries = charts.evaluate_all(
        """
        (elements, params) => {
          const indicatorName = params.indicatorName;
          const categoryName = params.categoryName;

          const safeStringify = (obj) => {
            try {
              return JSON.stringify(obj);
            } catch (e) {
              return String(obj);
            }
          };

          const textAround = (el) => {
            const parts = [];
            let cur = el;
            let depth = 0;
            while (cur && depth < 4) {
              const txt = (cur.innerText || cur.textContent || "").trim();
              if (txt) parts.push(txt);
              cur = cur.parentElement;
              depth += 1;
            }
            return parts.join("\\n");
          };

          return elements.map((el, index) => {
            const visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            let option = null;
            let optionText = "";
            let score = 0;

            try {
              const inst = window.echarts && window.echarts.getInstanceByDom
                ? window.echarts.getInstanceByDom(el)
                : null;
              if (inst && inst.getOption) {
                option = inst.getOption() || {};
                optionText = safeStringify(option);
              }
            } catch (e) {
              optionText = String(e);
            }

            const context = textAround(el);
            const joined = `${context}\\n${optionText}`;

            if (joined.includes(indicatorName)) score += 10;
            if (joined.includes(categoryName)) score += 8;
            if (joined.includes("JC3")) score += 2;
            if (joined.includes("支付方案研发部")) score += 2;

            return {
              index,
              visible,
              score,
              context,
              option_preview: optionText.slice(0, 3000)
            };
          });
        }
        """,
        {"indicatorName": INDICATOR_NAME, "categoryName": CATEGORY_NAME},
    )

    candidates = [item for item in summaries if item.get("visible")]
    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

    for item in candidates[:10]:
        log(f"候选图表 chart[{item['index']}], score={item['score']}")
    return candidates


def recursive_find_numeric(value):
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            return float(match.group(0))
        return None

    if isinstance(value, list):
        for item in reversed(value):
            found = recursive_find_numeric(item)
            if found is not None:
                return found
        return None

    if isinstance(value, dict):
        priority_keys = [
            "value", "percent", "rate", "y", "data", "metricValue",
            "displayValue", "rawValue", "val"
        ]
        for key in priority_keys:
            if key in value:
                found = recursive_find_numeric(value.get(key))
                if found is not None:
                    return found

        for _, item in value.items():
            found = recursive_find_numeric(item)
            if found is not None:
                return found

    return None


def extract_value_from_option(chart: Locator) -> dict | None:
    data = chart.evaluate(
        """
        (el) => {
          const inst = window.echarts && window.echarts.getInstanceByDom
            ? window.echarts.getInstanceByDom(el)
            : null;

          if (!inst || !inst.getOption) {
            return { ok: false, reason: "no_echarts_instance" };
          }

          const option = inst.getOption() || {};
          const seriesList = Array.isArray(option.series) ? option.series : [];

          return {
            ok: true,
            option: {
              title: option.title || null,
              legend: option.legend || null,
              xAxis: option.xAxis || null,
              yAxis: option.yAxis || null,
              series: seriesList
            }
          };
        }
        """
    )

    if not data or not data.get("ok"):
        return None

    option = data.get("option") or {}
    series_list = option.get("series") or []

    for idx, series_item in enumerate(series_list):
        series_name = ""
        if isinstance(series_item, dict):
            series_name = str(series_item.get("name") or "")

            if "data" in series_item:
                raw = recursive_find_numeric(series_item.get("data"))
                if raw is not None:
                    value = normalize_percent_value(raw)
                    return {
                        "source_mode": "echarts_option",
                        "value": value,
                        "series_name": series_name,
                        "tooltip_text": "",
                        "debug_from": f"series[{idx}].data"
                    }

            raw = recursive_find_numeric(series_item)
            if raw is not None:
                value = normalize_percent_value(raw)
                return {
                    "source_mode": "echarts_option",
                    "value": value,
                    "series_name": series_name,
                    "tooltip_text": "",
                    "debug_from": f"series[{idx}]"
                }

    return None


def read_global_tooltip_text(frame) -> str:
    js = """
    () => {
      const nodes = Array.from(document.querySelectorAll("body *"));
      const texts = [];

      for (const node of nodes) {
        const style = window.getComputedStyle(node);
        if (!style) continue;
        if (style.visibility === "hidden") continue;
        if (style.display === "none") continue;

        const text = (node.innerText || node.textContent || "").trim();
        if (!text) continue;

        if (
          text.includes("双周交付率") ||
          text.includes("支付方案") ||
          /\\d+(?:\\.\\d+)?%/.test(text)
        ) {
          texts.push(text);
        }
      }

      texts.sort((a, b) => b.length - a.length);
      return texts.slice(0, 20);
    }
    """
    texts = frame.page.evaluate(js)
    if not texts:
        return ""
    return "\n---\n".join(texts)


def extract_value_from_tooltip_by_hover(frame, chart: Locator) -> dict | None:
    box = chart.bounding_box()
    if not box:
        return None

    points = [
        (0.50, 0.45),
        (0.50, 0.55),
        (0.52, 0.40),
        (0.48, 0.40),
        (0.50, 0.30),
        (0.50, 0.65),
    ]

    best_text = ""

    for ratio_x, ratio_y in points:
        x = box["x"] + box["width"] * ratio_x
        y = box["y"] + box["height"] * ratio_y
        frame.page.mouse.move(x, y)
        frame.page.wait_for_timeout(800)

        tooltip_text = read_global_tooltip_text(frame)
        if tooltip_text:
            best_text = tooltip_text
            log(f"hover 命中文本: {tooltip_text[:300]}")

            pattern = re.compile(
                r"(?:双周交付率[：:\\s]*)(-?\\d+(?:\\.\\d+)?)%?"
            )
            match = pattern.search(tooltip_text)
            if match:
                value = normalize_percent_value(float(match.group(1)))
                return {
                    "source_mode": "global_tooltip_hover",
                    "value": value,
                    "series_name": INDICATOR_NAME,
                    "tooltip_text": tooltip_text,
                    "debug_from": f"hover({ratio_x},{ratio_y})"
                }

            matches = re.findall(r"(-?\\d+(?:\\.\\d+)?)%", tooltip_text)
            if matches:
                value = normalize_percent_value(float(matches[-1]))
                return {
                    "source_mode": "global_tooltip_hover",
                    "value": value,
                    "series_name": INDICATOR_NAME,
                    "tooltip_text": tooltip_text,
                    "debug_from": f"hover({ratio_x},{ratio_y})"
                }

    if best_text:
        log(f"虽然 hover 到文本，但未解析出数值: {best_text[:500]}")
    return None


def extract_metric_from_chart(frame, chart: Locator) -> dict:
    result = extract_value_from_option(chart)
    if result and result.get("value") is not None:
        log(f"已通过 option 解析到数值: {result}")
        return result

    log("option 未解析到数值，开始尝试 hover tooltip")
    result = extract_value_from_tooltip_by_hover(frame, chart)
    if result and result.get("value") is not None:
        log(f"已通过 tooltip 解析到数值: {result}")
        return result

    debug_info = chart.evaluate(
        """
        (el) => {
          const inst = window.echarts && window.echarts.getInstanceByDom
            ? window.echarts.getInstanceByDom(el)
            : null;
          if (!inst || !inst.getOption) {
            return { has_instance: false };
          }
          const option = inst.getOption() || {};
          return {
            has_instance: true,
            option_preview: JSON.stringify({
              title: option.title || null,
              legend: option.legend || null,
              xAxis: option.xAxis || null,
              yAxis: option.yAxis || null,
              series: option.series || null
            }).slice(0, 5000)
          };
        }
        """
    )
    raise Exception(f"已定位到目标图表，但未解析出数值，调试信息: {json.dumps(debug_info, ensure_ascii=False)}")


def extract_biweekly_delivery_rate(frame) -> dict:
    frame.locator(".chart-canvas[_echarts_instance_]").first.wait_for(state="visible", timeout=30000)
    frame.page.wait_for_timeout(3000)

    candidates = collect_chart_candidates(frame)
    if not candidates:
        raise Exception("页面中未找到可见的 ECharts 图表")

    charts = frame.locator(".chart-canvas[_echarts_instance_]")

    last_error = None
    for candidate in candidates[:8]:
        index = int(candidate["index"])
        score = candidate.get("score", 0)
        log(f"开始尝试候选图表 chart[{index}], score={score}")

        chart = charts.nth(index)
        try:
            result = extract_metric_from_chart(frame, chart)
            if result and result.get("value") is not None:
                log(f"候选图表 chart[{index}] 提取成功: {result}")
                return result
        except Exception as exc:
            last_error = str(exc)
            log(f"候选图表 chart[{index}] 提取失败: {exc}")

    raise Exception(f"所有候选图表均提取失败，最后一次错误: {last_error}")


def build_daily_payload(status: str, start_date: str | None, end_date: str | None, metric_value, *, source_mode: str, notes: str = "", error: str = "") -> dict:
    payload = {
        "date": date.today().strftime("%Y-%m-%d"),
        "indicator_type": "bi_weekly_delivery_rate",
        "indicator_name": INDICATOR_NAME,
        "department_c3": DEPARTMENT_C3,
        "status": status,
        "metrics": {
            "biweekly_delivery_rate": metric_value,
        },
        "unit": {
            "biweekly_delivery_rate": "%",
        },
        "source": {
            "query_screenshot": QUERY_SCREENSHOT_PATH,
        },
        "source_mode": source_mode,
    }

    if start_date and end_date:
        payload["filters"] = {
            "date_range": f"{start_date} ~ {end_date}",
            "department_c3": DEPARTMENT_C3,
        }
    if notes:
        payload["notes"] = notes
    if error:
        payload["error"] = error

    return payload


def write_daily_history_json(payload: dict) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    path = HISTORY_DIR / f"{payload['date']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"已写入当日巡检 JSON: {path}")
    return path


def write_failed_history_json(start_date: str | None, end_date: str | None, error_message: str) -> Path:
    payload = build_daily_payload(
        "failed",
        start_date,
        end_date,
        None,
        source_mode="unknown",
        error=error_message,
    )
    return write_daily_history_json(payload)


def main():
    out_dir = OUT_DIR
    out_dir.mkdir(exist_ok=True)

    start_date = None
    end_date = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        try:
            log("开始打开页面")
            page.goto(URL, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(5000)
            page.wait_for_load_state("domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            collapse_sidebar(page)
            save_debug_screenshot(page, out_dir, "00_home.png")
            dump_frames(page)

            dashboard_frame = get_dashboard_frame(page)
            log(f"dashboard frame: {dashboard_frame.url}")

            set_snapshot_latest_day(dashboard_frame)
            start_date, end_date = fill_complete_date_range(dashboard_frame)
            save_debug_screenshot(page, out_dir, "01_after_fill_date.png")

            select_department_c3(dashboard_frame, DEPARTMENT_C3)
            save_debug_screenshot(page, out_dir, "02_after_select_c3.png")

            click_query_button(dashboard_frame)
            save_debug_screenshot(page, out_dir, "03_after_query.png")

            extracted = extract_biweekly_delivery_rate(dashboard_frame)
            daily_payload = build_daily_payload(
                "success",
                start_date,
                end_date,
                extracted["value"],
                source_mode=extracted.get("source_mode", "unknown"),
                notes=f"从页面图表直接提取 {INDICATOR_NAME} = {extracted['value']}%，优先读取 ECharts option，失败后回退到 hover tooltip。",
            )
            json_path = write_daily_history_json(daily_payload)

            log(f"巡检完成，卡片完成日期范围：{start_date} ~ {end_date}")
            log(f"{INDICATOR_NAME} = {extracted['value']}%")
            log(f"source_mode = {extracted.get('source_mode')}")
            log(f"JSON 已输出到: {json_path}")

        except PlaywrightTimeoutError as exc:
            log(f"Playwright 超时: {exc}")
            save_debug_screenshot(page, out_dir, "timeout_error.png")
            try:
                write_failed_history_json(start_date, end_date, f"Playwright 超时: {exc}")
            except Exception as json_exc:
                log(f"写入失败 JSON 失败: {json_exc}")
            raise
        except Exception as exc:
            log(f"执行失败: {exc}")
            save_debug_screenshot(page, out_dir, "general_error.png")
            try:
                write_failed_history_json(start_date, end_date, str(exc))
            except Exception as json_exc:
                log(f"写入失败 JSON 失败: {json_exc}")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()