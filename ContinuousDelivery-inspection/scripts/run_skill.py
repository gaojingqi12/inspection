import json
import os
import re
from datetime import date

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

URL = "https://easybi.jd.com/bi/#/insight?code=361A3E1072028B83D4BF84086F5E30DFE3DE53F9F1A81091693866D563AA89BA"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUT_DIR = os.path.join(PROJECT_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)


TARGET_METRICS = [
    "团队空间开发测试上线需求数",
    "团队空间_持需交付_开发测试上线需求数",
    "持续交付_团队空间上线需求占比",
]


def log(msg: str):
    print(f"[DEBUG] {msg}")


def clear_out_dir():
    for filename in os.listdir(OUT_DIR):
        file_path = os.path.join(OUT_DIR, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                log(f"删除旧文件失败: {file_path}, error={e}")


def save_final_locator_shot(locator, name="final_three_cards"):
    clear_out_dir()
    path = os.path.join(OUT_DIR, f"{name}.png")
    locator.screenshot(path=path)
    log(f"最终截图已保存: {path}")
    return path


def wait_page_stable(page):
    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass

    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    page.wait_for_timeout(2500)


def handle_guide_popup(page):
    try:
        log("检查是否存在引导弹窗")
        page.wait_for_timeout(1500)

        skip_btn = page.get_by_text("跳过", exact=True)
        if skip_btn.count() > 0 and skip_btn.first.is_visible():
            skip_btn.first.click(timeout=3000)
            log("已点击：跳过")
            page.wait_for_timeout(1000)
            return

        finish_btn = page.get_by_text("完成", exact=True)
        if finish_btn.count() > 0 and finish_btn.first.is_visible():
            finish_btn.first.click(timeout=3000)
            log("已点击：完成")
            page.wait_for_timeout(1000)
            return

        log("未发现引导弹窗")

    except Exception as e:
        log(f"处理引导弹窗异常（忽略）: {e}")


def click_delivery_detail_menu(page):
    log("开始点击左侧菜单：持续交付交付明细")
    page.wait_for_timeout(2000)

    candidates = [
        page.get_by_text("持续交付交付明细", exact=True),
        page.locator("text=持续交付交付明细"),
        page.locator("span:has-text('持续交付交付明细')"),
        page.locator("div:has-text('持续交付交付明细')"),
        page.locator("li:has-text('持续交付交付明细')"),
        page.locator("a:has-text('持续交付交付明细')"),
    ]

    for i, locator in enumerate(candidates, start=1):
        try:
            if locator.count() == 0:
                continue

            target = locator.first
            try:
                target.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass

            page.wait_for_timeout(500)

            if target.is_visible():
                target.click(timeout=5000)
                log(f"已点击：持续交付交付明细（方案{i}）")
                page.wait_for_timeout(2500)
                return

        except Exception as e:
            log(f"菜单定位方案{i}失败: {e}")

    raise Exception("未找到或无法点击左侧菜单：持续交付交付明细")


def get_department_cascade(page):
    li = page.locator("li").filter(
        has=page.locator("span.name:has-text('交付负责人部门')")
    ).first

    if li.count() == 0:
        raise Exception("未找到“交付负责人部门”区域")

    cascade = li.locator("div.query-cascade").first
    if cascade.count() == 0:
        raise Exception("未找到“交付负责人部门”的级联控件")

    return cascade


def page_wait(page, ms=500):
    page.wait_for_timeout(ms)


def clear_select_value(page, select_box):
    try:
        close_icons = select_box.locator("i.el-tag__close")
        while close_icons.count() > 0:
            try:
                close_icons.nth(0).click(timeout=1000)
                page_wait(page, 300)
            except Exception:
                break
    except Exception:
        pass


def get_select_input(select_box):
    candidates = [
        select_box.locator("input.el-select__input"),
        select_box.locator("input.el-input__inner"),
    ]

    for locator in candidates:
        try:
            if locator.count() > 0:
                return locator.first
        except Exception:
            pass

    raise Exception("未找到选择框输入元素")


def open_and_type_select(page, select_box, value, level_idx):
    try:
        select_box.scroll_into_view_if_needed(timeout=3000)
    except Exception:
        pass

    input_box = get_select_input(select_box)
    input_box.click(timeout=5000)
    page_wait(page, 300)

    try:
        select_box.click(timeout=2000)
        page_wait(page, 300)
    except Exception:
        pass

    input_box = get_select_input(select_box)

    try:
        input_box.fill("")
    except Exception:
        input_box.click()
        try:
            page.keyboard.press("Meta+A")
        except Exception:
            page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")

    page_wait(page, 200)

    try:
        input_box.fill(value)
    except Exception:
        input_box.click()
        page.keyboard.type(value, delay=80)

    log(f"第{level_idx}级已输入：{value}")
    page_wait(page, 1000)


def click_dropdown_option(page, text, level_idx):
    candidates = [
        page.locator(".el-select-dropdown:visible .el-select-dropdown__item span").filter(has_text=text),
        page.locator(".el-select-dropdown:visible .el-select-dropdown__item").filter(has_text=text),
        page.locator(".el-select-dropdown__item span").filter(has_text=text),
        page.locator(".el-select-dropdown__item").filter(has_text=text),
    ]

    for i, locator in enumerate(candidates, start=1):
        try:
            if locator.count() == 0:
                continue

            option = locator.first
            try:
                option.scroll_into_view_if_needed(timeout=2000)
            except Exception:
                pass

            option.click(timeout=5000)
            log(f"已点击第{level_idx}级下拉项：{text}（方案{i}）")
            page_wait(page, 1200)
            return
        except Exception as e:
            log(f"第{level_idx}级点击下拉项失败（方案{i}）: {e}")

    raise Exception(f"未找到第{level_idx}级下拉选项：{text}")


def input_and_select_level(page, select_box, value, level_idx):
    log(f"开始处理第{level_idx}级，目标值：{value}")
    clear_select_value(page, select_box)
    page_wait(page, 300)
    open_and_type_select(page, select_box, value, level_idx)
    click_dropdown_option(page, value, level_idx)


def select_department_levels(page):
    log("开始重新输入交付负责人部门 1~4 级")

    cascade = get_department_cascade(page)
    selects = cascade.locator("div.el-select")
    select_count = selects.count()
    log(f"级联下拉框数量: {select_count}")

    if select_count < 5:
        raise Exception(f"级联下拉框数量不足，实际数量: {select_count}")

    values = [
        "京东科技",
        "金融科技事业群",
        "金融科技研发部",
        "支付方案研发部",
    ]

    for idx, value in enumerate(values, start=1):
        input_and_select_level(page, selects.nth(idx - 1), value, idx)

    log("第5级保持不动")


def click_query_button(page):
    log("开始点击查询按钮")

    query_group = page.locator("div.queryGroup.control").first
    candidates = [
        query_group.get_by_role("button", name="查询"),
        query_group.locator("button:has-text('查询')"),
        page.get_by_role("button", name="查询"),
        page.locator("button:has-text('查询')"),
    ]

    for i, locator in enumerate(candidates, start=1):
        try:
            if locator.count() == 0:
                continue

            btn = locator.first
            try:
                btn.scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass

            page.wait_for_timeout(300)
            btn.click(timeout=5000)
            log(f"已点击查询按钮（方案{i}）")
            page.wait_for_timeout(4000)
            return

        except Exception as e:
            log(f"查询按钮方案{i}失败: {e}")

    raise Exception("未找到或无法点击查询按钮")


def locate_three_cards_row(page):
    log("开始定位三个指标卡片")

    keywords = TARGET_METRICS

    first_card_title = page.get_by_text(keywords[0], exact=False).first
    first_card_title.scroll_into_view_if_needed(timeout=5000)
    page.wait_for_timeout(1500)

    candidates = [
        page.locator("div").filter(has=page.get_by_text(keywords[0], exact=False))
                           .filter(has=page.get_by_text(keywords[1], exact=False))
                           .filter(has=page.get_by_text(keywords[2], exact=False)),
        page.locator("section").filter(has=page.get_by_text(keywords[0], exact=False))
                               .filter(has=page.get_by_text(keywords[1], exact=False))
                               .filter(has=page.get_by_text(keywords[2], exact=False)),
    ]

    for i, locator in enumerate(candidates, start=1):
        try:
            count = locator.count()
            log(f"三卡片公共容器方案{i}，匹配数量: {count}")
            if count == 0:
                continue

            target = locator.first
            target.scroll_into_view_if_needed(timeout=3000)
            page.wait_for_timeout(1000)
            return target
        except Exception as e:
            log(f"三卡片公共容器方案{i}失败: {e}")

    fallback = page.locator("body")
    return fallback


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_metric_value(raw: str):
    raw = normalize_text(raw).replace(",", "")
    if raw.endswith("%"):
        percent = raw[:-1].strip()
        if re.fullmatch(r"-?\d+", percent):
            return int(percent)
        if re.fullmatch(r"-?\d+\.\d+", percent):
            return float(percent)
        return percent
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def extract_three_metrics(page) -> dict:
    log("开始提取三个指标卡片的数据")

    cards = page.locator(".item-card__content")
    count = cards.count()
    log(f"匹配到 item-card__content 数量: {count}")

    result_map = {}

    for i in range(count):
        card = cards.nth(i)
        try:
            if not card.is_visible():
                continue

            title_el = card.locator(".item-card__title").first
            value_el = card.locator(".item-card__display span").first

            if title_el.count() == 0 or value_el.count() == 0:
                continue

            title = normalize_text(title_el.inner_text())
            value = normalize_text(value_el.inner_text())

            if not title:
                continue

            log(f"card[{i}] title={title}, value={value}")
            result_map[title] = value
        except Exception as e:
            log(f"提取 card[{i}] 失败: {e}")

    missing = [name for name in TARGET_METRICS if name not in result_map]
    if missing:
        raise Exception(f"未提取到以下指标卡片: {missing}")

    return {
        "team_space_dev_test_online_requirements": parse_metric_value(
            result_map["团队空间开发测试上线需求数"]
        ),
        "team_space_continuous_delivery_dev_test_online_requirements": parse_metric_value(
            result_map["团队空间_持需交付_开发测试上线需求数"]
        ),
        "continuous_delivery_team_space_online_requirement_rate": parse_metric_value(
            result_map["持续交付_团队空间上线需求占比"]
        ),
    }


def build_daily_payload(metrics: dict, final_screenshot_path: str) -> dict:
    return {
        "date": date.today().strftime("%Y-%m-%d"),
        "indicator_type": "continuous_delivery",
        "indicator_name": "持续交付",
        "department_c3": "支付方案研发部",
        "status": "success",
        "filters": {
            "department_level_1": "京东科技",
            "department_level_2": "金融科技事业群",
            "department_level_3": "金融科技研发部",
            "department_level_4": "支付方案研发部",
        },
        "metrics": metrics,
        "unit": {
            "team_space_dev_test_online_requirements": "count",
            "team_space_continuous_delivery_dev_test_online_requirements": "count",
            "continuous_delivery_team_space_online_requirement_rate": "%",
        },
        "source": {
            "query_screenshot": os.path.relpath(final_screenshot_path, PROJECT_DIR).replace("\\", "/"),
            "metric_titles": TARGET_METRICS,
        },
        "source_mode": "metric_cards_dom",
        "notes": "查询后直接从三个指标卡片元素提取标题和值，并按统一 HTML 字段落盘。",
    }


def write_daily_json(payload: dict) -> str:
    path = os.path.join(OUT_DIR, f"continuous_delivery_{payload['date']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log(f"已写入当日巡检 JSON: {path}")
    return path


def write_failed_daily_json(error_message: str) -> str:
    payload = {
        "date": date.today().strftime("%Y-%m-%d"),
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
        "error": error_message,
        "source": {
            "query_screenshot": "out/three_cards.png",
            "metric_titles": TARGET_METRICS,
        },
        "source_mode": "metric_cards_dom",
    }
    return write_daily_json(payload)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )

        context = browser.new_context(
            viewport={"width": 1600, "height": 900}
        )
        page = context.new_page()

        try:
            log("开始打开页面")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            wait_page_stable(page)
            handle_guide_popup(page)
            click_delivery_detail_menu(page)
            select_department_levels(page)
            click_query_button(page)

            cards_row = locate_three_cards_row(page)
            final_path = save_final_locator_shot(cards_row, "three_cards")

            metrics = extract_three_metrics(page)
            payload = build_daily_payload(metrics, final_path)
            json_path = write_daily_json(payload)

            log("流程完成")
            log(f"提取结果: {json.dumps(metrics, ensure_ascii=False)}")
            log(f"最终输出文件: {final_path}")
            log(f"JSON 输出文件: {json_path}")

            page.wait_for_timeout(3000)

        except PlaywrightTimeout as e:
            log(f"Playwright 超时: {e}")
            try:
                write_failed_daily_json(f"Playwright 超时: {e}")
            except Exception as json_exc:
                log(f"写入失败 JSON 失败: {json_exc}")
        except Exception as e:
            log(f"执行异常: {e}")
            try:
                write_failed_daily_json(str(e))
            except Exception as json_exc:
                log(f"写入失败 JSON 失败: {json_exc}")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
