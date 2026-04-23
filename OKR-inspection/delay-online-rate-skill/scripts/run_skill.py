from pathlib import Path
from datetime import date, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "https://ine.jd.com/portalDetail?location=%252Fdetail%253FportalUuid%253D20211122143031511247544858946828%2523bec0cff726e665ba2018519fef985cde"

# 如果页面里真实标题有差异，只改这一行
CARD_TITLE = "延期上线率-周（5->4）-汇总-C3维度"

# 保证输出目录固定落在 skill 根目录下的 out/
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
    for idx, f in enumerate(page.frames):
        log(f"frame[{idx}] url = {f.url}")


def get_menu_frame(page, timeout_ms=15000):
    import time
    start = time.time()

    while (time.time() - start) * 1000 < timeout_ms:
        for idx, f in enumerate(page.frames):
            try:
                url = f.url or ""
                log(f"轮询菜单 frame[{idx}] url = {url}")
                if "bi.jd.com/detail" in url:
                    log(f"命中菜单 frame[{idx}]")
                    return f
            except Exception as e:
                log(f"读取菜单 frame[{idx}] url 失败: {e}")

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
        for idx, f in enumerate(page.frames):
            try:
                url = f.url or ""
                log(f"轮询 frame[{idx}] url = {url}")
                if "jddbi.jd.com/export/dashboard" in url:
                    log(f"命中 dashboard frame[{idx}]")
                    return f
            except Exception as e:
                log(f"读取 frame[{idx}] url 失败: {e}")

        page.wait_for_timeout(1000)

    raise Exception("等待超时：没找到目标 dashboard iframe")


def locate_target_chart(frame):
    title = frame.locator(".chart-title", has_text=CARD_TITLE).first
    title.wait_for(state="visible", timeout=15000)
    title.scroll_into_view_if_needed()

    card = title.locator("xpath=ancestor::div[contains(@class,'vue-grid-item')]").first
    card.wait_for(state="visible", timeout=10000)
    return title, card


def hover_card(page, card):
    candidates = [
        card,
        card.locator(".element-contaienr").first,
        card.locator(".preview-set").first,
        card.locator(".chart-title").first,
        card.locator(".chart").first,
    ]

    for idx, loc in enumerate(candidates):
        try:
            if loc.count() > 0:
                loc.scroll_into_view_if_needed()
                loc.hover()
                page.wait_for_timeout(1200)
                log(f"hover 成功，第 {idx} 个候选")
                return
        except Exception as e:
            log(f"hover 失败，第 {idx} 个候选, error={e}")

    raise Exception("所有 hover 候选都失败")


def click_chart_filter_button(page, card):
    hover_card(page, card)

    btn = card.locator(
        ".preview-set > .preview-set-setting-button > .card-toolbar > div:nth-child(7) > .el-tooltip"
    ).first

    btn.wait_for(state="visible", timeout=8000)
    btn.click()
    log("已点击图表筛选按钮")


def get_last_friday_and_today():
    today = date.today()
    days_since_friday = (today.weekday() - 4) % 7
    if days_since_friday == 0:
        days_since_friday = 7
    last_friday = today - timedelta(days=days_since_friday)
    return last_friday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def get_visible_filter_panel(frame):
    frame.page.wait_for_timeout(1000)

    panels = frame.locator(".single-chart-filter")
    count = panels.count()
    log(f"匹配到 single-chart-filter 数量: {count}")

    for i in range(count):
        panel = panels.nth(i)
        try:
            visible = panel.is_visible()
            log(f"panel[{i}] visible = {visible}")
            if visible:
                return panel
        except Exception as e:
            log(f"panel[{i}] 检查失败: {e}")

    raise Exception(f"没找到可见的 single-chart-filter，当前共匹配到 {count} 个")


def find_filter_item(panel, label_text: str):
    items = panel.locator(".filter-item")
    count = items.count()

    for i in range(count):
        item = items.nth(i)
        try:
            label = item.locator(".filter-item-label").inner_text().strip()
            if label == label_text:
                return item
        except Exception:
            pass

    raise Exception(f"没找到筛选项: {label_text}")


def fill_test_stage_date_range(frame):
    start_date, end_date = get_last_friday_and_today()
    log(f"开始时间: {start_date}, 结束时间: {end_date}")

    panel = get_visible_filter_panel(frame)
    target_item = find_filter_item(panel, "卡片完成日期")

    inputs = target_item.locator("input.el-input__inner")
    input_count = inputs.count()
    log(f"卡片完成日期 input 数量: {input_count}")

    if input_count < 2:
        raise Exception(f"卡片完成日期 输入框数量异常: {input_count}") 

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


def select_department_c3(frame, department_name="支付方案研发部"):
    panel = get_visible_filter_panel(frame)
    target_item = find_filter_item(panel, "任务处理人部门C3")

    dropdown_btn = target_item.locator("button.qd-button").first
    dropdown_btn.wait_for(state="visible", timeout=5000)
    dropdown_btn.click()
    frame.page.wait_for_timeout(1000)
    log("已点开：任务处理人部门C3 下拉")

    poppers = frame.locator(".el-popper")
    visible_popper = None
    for i in range(poppers.count()):
        p = poppers.nth(i)
        try:
            if p.is_visible():
                visible_popper = p
                log(f"命中可见弹层 index={i}")
                break
        except Exception:
            pass

    if visible_popper is None:
        raise Exception("没找到可见的下拉弹层 el-popper")

    search_box = None
    search_candidates = [
        'input.el-input__inner[placeholder="请输入..."]',
        'input.el-input__inner[placeholder*="请输入"]',
        'input[placeholder="请输入..."]',
        'input[placeholder*="请输入"]',
    ]

    for sel in search_candidates:
        try:
            locs = visible_popper.locator(sel)
            for i in range(locs.count()):
                inp = locs.nth(i)
                if inp.is_visible():
                    search_box = inp
                    log(f"命中搜索框 selector={sel}, index={i}")
                    break
            if search_box is not None:
                break
        except Exception as e:
            log(f"搜索框候选失败: {sel}, error={e}")

    if search_box is None:
        raise Exception("没找到任务处理人部门C3 下拉弹层里的搜索框")

    search_box.click()
    search_box.fill(department_name)
    frame.page.wait_for_timeout(1000)
    log(f"已输入搜索词: {department_name}")

    option = None
    option_candidates = [
        visible_popper.get_by_text(department_name, exact=True),
        frame.get_by_text(department_name, exact=True),
    ]

    for cand in option_candidates:
        try:
            for i in range(cand.count()):
                opt = cand.nth(i)
                if opt.is_visible():
                    option = opt
                    break
            if option is not None:
                break
        except Exception as e:
            log(f"选项候选失败: {e}")

    if option is None:
        raise Exception(f"没找到可见选项: {department_name}")

    option.click()
    frame.page.wait_for_timeout(800)
    log(f"已选择：任务处理人部门C3 = {department_name}")


def click_query_button(frame):
    panel = get_visible_filter_panel(frame)
    query_btn = panel.locator(".serach-btn button").first
    query_btn.wait_for(state="visible", timeout=5000)
    query_btn.click()
    frame.page.wait_for_timeout(5000)
    log("已点击：查询")


def main():
    out_dir = OUT_DIR
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        try:
            log("开始打开页面")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(3000)

            collapse_sidebar(page)

            save_debug_screenshot(page, out_dir, "00_home.png")
            dump_frames(page)

            dashboard_frame = get_dashboard_frame(page)
            log(f"dashboard frame: {dashboard_frame.url}")

            title, card = locate_target_chart(dashboard_frame)
            log(f"已定位到目标标题: {title.inner_text().strip()}")

            card.screenshot(path=str(out_dir / "01_target_card.png"))
            log("已保存目标卡片截图")

            click_chart_filter_button(page, card)
            save_debug_screenshot(page, out_dir, "02_after_click_filter.png")

            start_date, end_date = fill_test_stage_date_range(dashboard_frame)
            save_debug_screenshot(page, out_dir, "03_after_fill_date_range.png")

            select_department_c3(dashboard_frame, "支付方案研发部")
            save_debug_screenshot(page, out_dir, "04_after_select_c3.png")

            click_query_button(dashboard_frame)
            save_debug_screenshot(page, out_dir, "05_after_query.png")

            log(f"延期上线率巡检完成，时间范围：{start_date} ~ {end_date}")


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