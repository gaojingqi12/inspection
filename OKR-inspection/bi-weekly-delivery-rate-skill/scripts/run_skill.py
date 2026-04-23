from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

URL = "https://ine.jd.com/portalDetail?location=%252Fdetail%253FportalUuid%253D20211122143031511247544858946828%252325738583d55e87d7698eb308460aff29"

BASE_DIR = Path(__file__).resolve().parents[1]
OUT_DIR = BASE_DIR / "out"


def log(msg: str):
    print(f"[DEBUG] {msg}")


def save_debug_screenshot(page, out_dir: Path, name: str):
    path = out_dir / name
    page.screenshot(path=str(path), full_page=True)
    log(f"已保存截图: {path}")


def dump_frames(page):
    log(f"当前标题: {page.title()}")
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
                url = frame.url or ""
                if "bi.jd.com/detail" in url:
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
    log(f"快照日期当前值: {input_box.input_value()}")
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


def select_department_c3(frame, department_name="支付方案研发部"):
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
    frame.page.wait_for_timeout(20000)


def main():
    out_dir = OUT_DIR
    out_dir.mkdir(exist_ok=True)

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

            select_department_c3(dashboard_frame, "支付方案研发部")
            save_debug_screenshot(page, out_dir, "02_after_select_c3.png")

            click_query_button(dashboard_frame)
            save_debug_screenshot(page, out_dir, "03_after_query.png")

            log(f"巡检完成，卡片完成日期范围：{start_date} ~ {end_date}")

        except PlaywrightTimeoutError as exc:
            log(f"Playwright 超时: {exc}")
            save_debug_screenshot(page, out_dir, "timeout_error.png")
            raise
        except Exception as exc:
            log(f"执行失败: {exc}")
            save_debug_screenshot(page, out_dir, "general_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
