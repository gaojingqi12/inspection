import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

URL = "https://easybi.jd.com/bi/#/insight?code=361A3E1072028B83D4BF84086F5E30DFE3DE53F9F1A81091693866D563AA89BA"

# scripts 目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# scripts 的上一级目录，也就是 ContinuousDelivery-inspection
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# 输出到和 scripts 同级的 out
OUT_DIR = os.path.join(PROJECT_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)


def clear_out_dir():
    """
    清空 out 目录中的旧截图，只保留最终截图
    """
    for filename in os.listdir(OUT_DIR):
        file_path = os.path.join(OUT_DIR, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"[DEBUG] 删除旧文件失败: {file_path}, error={e}")


def save_final_locator_shot(locator, name="final_three_cards"):
    """
    对指定 locator 截图，只保存最终一张
    """
    clear_out_dir()
    path = os.path.join(OUT_DIR, f"{name}.png")
    locator.screenshot(path=path)
    print(f"[DEBUG] 最终截图已保存: {path}")
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
        print("[DEBUG] 检查是否存在引导弹窗")
        page.wait_for_timeout(1500)

        skip_btn = page.get_by_text("跳过", exact=True)
        if skip_btn.count() > 0 and skip_btn.first.is_visible():
            skip_btn.first.click(timeout=3000)
            print("[DEBUG] 已点击：跳过")
            page.wait_for_timeout(1000)
            return

        finish_btn = page.get_by_text("完成", exact=True)
        if finish_btn.count() > 0 and finish_btn.first.is_visible():
            finish_btn.first.click(timeout=3000)
            print("[DEBUG] 已点击：完成")
            page.wait_for_timeout(1000)
            return

        print("[DEBUG] 未发现引导弹窗")

    except Exception as e:
        print(f"[DEBUG] 处理引导弹窗异常（忽略）: {e}")


def click_delivery_detail_menu(page):
    print("[DEBUG] 开始点击左侧菜单：持续交付交付明细")
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
                print(f"[DEBUG] 已点击：持续交付交付明细（方案{i}）")
                page.wait_for_timeout(2500)
                return

        except Exception as e:
            print(f"[DEBUG] 菜单定位方案{i} 失败: {e}")

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
    """
    清空单个下拉框已选标签
    """
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
    """
    优先使用可输入搜索框
    """
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

    print(f"[DEBUG] 第{level_idx}级已输入：{value}")
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
            print(f"[DEBUG] 已点击第{level_idx}级下拉项：{text}（方案{i}）")
            page_wait(page, 1200)
            return
        except Exception as e:
            print(f"[DEBUG] 第{level_idx}级点击下拉项失败（方案{i}）: {e}")

    raise Exception(f"未找到第{level_idx}级下拉选项：{text}")


def input_and_select_level(page, select_box, value, level_idx):
    print(f"[DEBUG] 开始处理第{level_idx}级，目标值：{value}")
    clear_select_value(page, select_box)
    page_wait(page, 300)
    open_and_type_select(page, select_box, value, level_idx)
    click_dropdown_option(page, value, level_idx)


def select_department_levels(page):
    """
    前4个框重新输入，第5个框不动
    """
    print("[DEBUG] 开始重新输入交付负责人部门 1~4 级")

    cascade = get_department_cascade(page)
    selects = cascade.locator("div.el-select")
    select_count = selects.count()
    print(f"[DEBUG] 级联下拉框数量: {select_count}")

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

    print("[DEBUG] 第5级保持不动")


def click_query_button(page):
    print("[DEBUG] 开始点击查询按钮")

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
            print(f"[DEBUG] 已点击查询按钮（方案{i}）")
            page.wait_for_timeout(4000)
            return
        except Exception as e:
            print(f"[DEBUG] 查询按钮方案{i}失败: {e}")

    raise Exception("未找到或无法点击查询按钮")


def locate_three_cards_row(page):
    """
    定位这3个指标卡片所在的整行区域，然后截图
    """
    print("[DEBUG] 开始定位三个指标卡片")

    keywords = [
        "团队空间开发测试上线需求数",
        "团队空间_持需交付_开发测试上线需求数",
        "持续交付_团队空间上线需求占比",
    ]

    # 先滚动到第一个卡片附近
    first_card_title = page.get_by_text(keywords[0], exact=False).first
    first_card_title.scroll_into_view_if_needed(timeout=5000)
    page.wait_for_timeout(1500)

    # 找同时包含这三个标题的最小公共容器
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
            print(f"[DEBUG] 三卡片公共容器方案{i}，匹配数量: {count}")
            if count == 0:
                continue

            # 取面积较小、靠前的一个，一般就是这一行容器
            target = locator.first
            target.scroll_into_view_if_needed(timeout=3000)
            page.wait_for_timeout(1000)
            return target
        except Exception as e:
            print(f"[DEBUG] 三卡片公共容器方案{i}失败: {e}")

    # 兜底：如果找不到公共容器，就取从第一个卡片到第三个卡片的外层祖先
    fallback = page.locator("body")
    return fallback


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
            print("[DEBUG] 开始打开页面")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            wait_page_stable(page)
            handle_guide_popup(page)
            click_delivery_detail_menu(page)
            select_department_levels(page)
            click_query_button(page)

            # 定位三张卡片整行
            cards_row = locate_three_cards_row(page)

            # 只保存这一张最终截图
            final_path = save_final_locator_shot(cards_row, "three_cards")

            print("[DEBUG] 流程完成")
            print(f"[DEBUG] 最终输出文件: {final_path}")

            page.wait_for_timeout(3000)

        except PlaywrightTimeout as e:
            print(f"[DEBUG] Playwright 超时: {e}")
        except Exception as e:
            print(f"[DEBUG] 执行异常: {e}")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()