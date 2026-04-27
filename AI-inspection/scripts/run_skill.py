from pathlib import Path
from datetime import date, timedelta
import json
import time

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "http://xingyun.jd.com/jStatisticsRoot/saleDashbord/customization?dashboardId=6098"

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "out"

TARGET_NAMES = [
    "蔡永乐", "常姜洲", "常彦升", "桂斌", "兰春秋", "李进锋", "李景伦",
    "刘竟博(Seven)", "刘卫强", "刘学", "陆鑫(Max)", "秦赞", "邱登辉",
    "邰广有", "覃杨阳", "王佳斌(Bin)", "王诗赋", "王朝华", "温丽星",
    "谢传威", "徐涛", "杨飞宇", "张鑫", "张欣强", "赵波", "赵梓博",
    "郑双龙", "朱涛"
]


def log(msg: str):
    print(f"[DEBUG] {msg}")


def save_debug_screenshot(page, out_dir: Path, name: str):
    path = out_dir / name
    page.screenshot(path=str(path), full_page=True)
    log(f"已保存截图: {path}")


def get_yesterday_and_today():
    today = date.today()
    yesterday = today - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def click_day_tab(page):
    day_btn = page.get_by_text("日", exact=True).first
    day_btn.wait_for(state="visible", timeout=15000)
    day_btn.click()
    page.wait_for_timeout(2200)
    log("已点击：日")


def find_visible_date_inputs(page):
    visible_inputs = page.locator("input.el-range-input:visible")
    count = visible_inputs.count()
    log(f"可见日期输入框数量: {count}")

    if count < 2:
        raise Exception(f"没找到可见的开始/结束日期输入框，当前数量: {count}")

    return visible_inputs.nth(0), visible_inputs.nth(1)


def fill_input_and_tab(page, input_locator, value: str):
    input_locator.click(timeout=15000)
    page.wait_for_timeout(500)

    page.keyboard.press("Meta+A")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(300)

    input_locator.fill(value)
    page.wait_for_timeout(500)

    page.keyboard.press("Tab")
    page.wait_for_timeout(800)


def fill_input_and_enter(page, input_locator, value: str):
    input_locator.click(timeout=15000)
    page.wait_for_timeout(500)

    page.keyboard.press("Meta+A")
    page.keyboard.press("Backspace")
    page.wait_for_timeout(300)

    input_locator.fill(value)
    page.wait_for_timeout(500)

    page.keyboard.press("Enter")
    log("已敲回车，等待页面刷新...")
    page.wait_for_timeout(30000)


def fill_date_range(page):
    start_date, end_date = get_yesterday_and_today()
    log(f"开始日期: {start_date}, 结束日期: {end_date}")

    wrappers = page.locator(".el-date-editor.el-range-editor:visible")
    wrapper_count = wrappers.count()
    log(f"可见日期范围组件数量: {wrapper_count}")

    if wrapper_count > 0:
        wrappers.first.click(timeout=15000)
        page.wait_for_timeout(1200)
        log("已点击日期范围组件")

    start_input, end_input = find_visible_date_inputs(page)

    start_readonly = start_input.get_attribute("readonly")
    end_readonly = end_input.get_attribute("readonly")
    log(f"开始输入框 readonly: {start_readonly}")
    log(f"结束输入框 readonly: {end_readonly}")

    if start_readonly is not None or end_readonly is not None:
        raise Exception("日期输入框是 readonly，当前页面不能直接 fill，需要改为点日历面板")

    fill_input_and_tab(page, start_input, start_date)
    fill_input_and_enter(page, end_input, end_date)

    log("已填写日期范围，并模拟回车")
    return start_date, end_date


def wait_for_file_stable(file_path: Path, timeout_seconds: int = 45):
    """
    等待文件大小稳定，避免刚下载完还没写完
    """
    start_time = time.time()
    last_size = -1
    stable_count = 0

    while time.time() - start_time < timeout_seconds:
        if file_path.exists():
            current_size = file_path.stat().st_size
            if current_size == last_size and current_size > 0:
                stable_count += 1
                if stable_count >= 2:
                    return
            else:
                stable_count = 0
                last_size = current_size
        time.sleep(1)

    raise Exception(f"文件长时间未稳定: {file_path}")


def download_indicator_file(page, out_dir: Path):
    log("开始下载指标文件")

    card = page.locator(".el-card__body").filter(
        has=page.locator("label.indicator-card__label", has_text="AI深度用户占比-软开测试岗(%)")
    ).first

    card.wait_for(state="visible", timeout=45000)
    log("已定位到目标指标卡片")

    download_btn = card.locator(".indicator-card__download").first
    download_btn.wait_for(state="visible", timeout=15000)
    download_btn.hover()
    page.wait_for_timeout(800)

    with page.expect_download(timeout=45000) as download_info:
        download_btn.click()

    download = download_info.value
    save_path = out_dir / download.suggested_filename
    download.save_as(str(save_path))

    wait_for_file_stable(save_path)

    log(f"下载完成: {save_path}")
    return save_path


def export_non_deep_users_to_json(excel_path: Path, target_names: list[str], out_dir: Path):
    log(f"开始读取Excel: {excel_path}")

    df = pd.read_excel(excel_path)
    df.columns = [str(col).strip() for col in df.columns]

    required_cols = ["用户erp", "用户姓名", "AI代码本地提交占比", "是否深度用户"]
    for col in required_cols:
        if col not in df.columns:
            raise Exception(f"Excel中缺少必要字段: {col}，当前表头: {list(df.columns)}")

    df["用户姓名"] = df["用户姓名"].astype(str).str.strip()
    df["是否深度用户"] = df["是否深度用户"].astype(str).str.strip()

    target_name_set = set(target_names)

    result_df = df[
        df["用户姓名"].isin(target_name_set) &
        (df["是否深度用户"] == "否")
    ][["用户erp", "用户姓名", "AI代码本地提交占比", "是否深度用户"]]

    result = result_df.to_dict(orient="records")

    today_str = date.today().strftime("%Y-%m-%d")
    json_path = out_dir / f"non_deep_users_{today_str}.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    log(f"筛选完成，共 {len(result)} 人")
    log(f"JSON已输出: {json_path}")

    return json_path, result


def main():
    out_dir = OUT_DIR
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            accept_downloads=True
        )
        page = context.new_page()

        try:
            log("开始打开页面")
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(7500)

            save_debug_screenshot(page, out_dir, "00_home.png")

            click_day_tab(page)
            save_debug_screenshot(page, out_dir, "01_after_click_day.png")

            start_date, end_date = fill_date_range(page)
            save_debug_screenshot(page, out_dir, "02_after_fill_date.png")

            download_path = download_indicator_file(page, out_dir)
            save_debug_screenshot(page, out_dir, "03_after_download.png")

            json_path, result = export_non_deep_users_to_json(
                download_path,
                TARGET_NAMES,
                out_dir
            )

            log(f"完成：日维度，日期范围 {start_date} ~ {end_date}")
            log(f"Excel已下载到: {download_path}")
            log(f"JSON已输出到: {json_path}")
            log(f"结果内容: {result}")

        except PlaywrightTimeoutError as e:
            log(f"Playwright 超时: {e}")
            save_debug_screenshot(page, out_dir, "timeout_error.png")
            raise
        except Exception as e:
            log(f"执行失败: {e}")
            save_debug_screenshot(page, out_dir, "general_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()