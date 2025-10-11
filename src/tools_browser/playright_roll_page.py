from playwright.sync_api import sync_playwright
from tools_data_process.utils_path import get_project_root
import time


def visible_operation(url):
    with sync_playwright() as p:
        # 启动自定义路径的Chrome（带可视化界面）
        browser = p.chromium.launch_persistent_context(
            user_data_dir=os.path.join(get_project_root(), "playwright_tools/chromedriver-win64/"),  # 用户数据目录[1](@ref)
            headless=False,  # 显示浏览器界面[7](@ref)
            slow_mo=500,  # 操作延迟500ms便于观察[3](@ref)
            # proxy={"server": config["proxy_server"]},  # 代理配置[3](@ref)
            args=[
                '--disable-blink-features=AutomationControlled',  # 绕过自动化检测[1](@ref)
                '--remote-debugging-port=9222'  # 开启调试端口[1](@ref)
            ],
        )

        page = browser.new_page()
        print("► 浏览器启动完成，开始访问页面...")

        # 分步可视化操作
        page.goto(url, timeout=60000)
        print("✓ 页面加载完成:", page.title())

        # 滚动页面（分步可视化）
        for i in range(3):
            page.mouse.wheel(0, 2000)  # 每次滚动2000像素
            print(f"⇅ 第{i + 1}次滚动页面")
            time.sleep(1)

        # 保存过程记录
        page.screenshot(path="search_result.png")
        print("📸 已截图保存搜索结果")

        browser.close()


if __name__ == "__main__":
    visible_operation(
        "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzIxNzMxMTA0OA==&scene=124#wechat_redirect")
