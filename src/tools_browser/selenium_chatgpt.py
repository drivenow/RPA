import os
import random
import subprocess
import time
import json
import socket
import urllib.request
from typing import Iterable, List, Optional, Sequence

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


def wait_for_devtools(host: str = "127.0.0.1", port: int = 9222, timeout: float = 8.0) -> bool:
    """Wait until Chrome's DevTools endpoint is reachable and returns /json/version."""
    deadline = time.time() + timeout
    url = f"http://{host}:{port}/json/version"
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.8):
                with urllib.request.urlopen(url, timeout=0.8) as r:
                    _ = json.load(r)  # ensure it's valid JSON
                return True
        except Exception:
            time.sleep(0.2)
    return False


def start_chrome(
    *,
    chrome_path: str = r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    user_data_dir: str = r"X:/RPA/selenium_tools/ChatGPTProfile",
    debug_port: int = 9222,
) -> Optional[subprocess.Popen]:
    """Launch Chrome with remote debugging enabled. Returns the Popen handle."""
    # Ensure dedicated, never-used-by-normal-Chrome profile
    profile_dir = os.path.abspath(f"{user_data_dir}")
    os.makedirs(profile_dir, exist_ok=True)

    # Build command; add stability flags
    cmd = [
        f'"{chrome_path}"',
        f"--remote-debugging-port={debug_port}",
        f'--user-data-dir="{profile_dir}"',
        # "--no-first-run",
        # "--no-default-browser-check",
        # 可选：无头
        # "--headless=new",
    ]
    command = " ".join(cmd)
    print(command)
    try:
        # Start detached; don't wait here
        proc = subprocess.Popen(command, shell=True)
        # 增加命令成功的判断
        if proc.poll() is not None:
            raise RuntimeError(f"Chrome 启动失败，退出码: {proc.returncode}")

        print(f"Chrome启动成功，调试端口: {debug_port}，Profile: {profile_dir}")
        return proc
    except Exception as exc:
        print(f"启动Chrome时出错: {exc}")
        return None


def connect_chrome(
    *,
    debug_port: int = 9222,
    driver_path: Optional[str] = None,
    devtools_timeout: float = 8.0,
) -> webdriver.Chrome:
    """Attach Selenium to an already-started Chrome with --remote-debugging-port."""
    if not wait_for_devtools("127.0.0.1", debug_port, devtools_timeout):
        raise RuntimeError(
            f"Chrome DevTools 未就绪：请确认已用 --remote-debugging-port={debug_port} 启动且端口可访问。"
        )

    chrome_options = webdriver.ChromeOptions()
    # Attach to the existing DevTools endpoint
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

    # Prefer Selenium Manager to resolve driver automatically.
    # If you must pin a driver, pass driver_path explicitly.
    service = Service(executable_path=driver_path) if driver_path else Service()

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def _find_chat_textarea(driver: webdriver.Chrome):
    # ChatGPT 的输入框使用 textarea 元素，等待其可用后返回
    # 定位 ChatGPT 输入框（contenteditable 的 div）
    input_box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][id='prompt-textarea']")

    # 点击聚焦
    input_box.click()    
    return input_box


def _wait_for_new_assistant_reply(
    driver: webdriver.Chrome,
    *,
    previous_count: int,
    timeout: int = 90,
) -> str:
    assistant_selector = (By.CSS_SELECTOR, '[data-message-author-role="assistant"]')

    def _has_new_answer(drv):
        elements = drv.find_elements(*assistant_selector)
        if len(elements) <= previous_count:
            return False
        text = elements[-1].text.strip()
        return text if text else False

    result = WebDriverWait(driver, timeout).until(_has_new_answer)
    return result.strip()


def _sanitize_label(value: str) -> str:
    label = value.strip().replace(" ", "_")
    for char in '\\/:*?"<>|':
        label = label.replace(char, "_")
    return label or "step"


def _log_page_html(
    driver: webdriver.Chrome,
    label: str,
    *,
    log_dir: Optional[str] = None,
) -> Optional[str]:
    log_dir = log_dir or os.path.join(os.getcwd(), "logs", "selenium_chatgpt")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{_sanitize_label(label)}.html"
    path = os.path.join(log_dir, filename)
    try:
        with open(path, "w", encoding="utf-8") as file_obj:
            file_obj.write(driver.page_source)
        print(f"页面快照已保存: {path}")
        return path
    except Exception as exc:  # pylint: disable=broad-except
        print(f"写入页面快照失败({label}): {exc}")
        return None


def _click_attachment_button(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    selectors: Sequence[tuple] = (
        (By.CSS_SELECTOR, '[data-testid="attachment-button"]'),
        (By.CSS_SELECTOR, 'button[aria-label="Attach a file"]'),
        (By.CSS_SELECTOR, 'button[data-testid="plus-button"]'),
        (By.CSS_SELECTOR, 'button[aria-label*="上传"]'),
    ),
) -> bool:
    for by, value in selectors:
        try:
            button = wait.until(EC.element_to_be_clickable((by, value)))
            driver.execute_script("arguments[0].click();", button)
            return True
        except TimeoutException:
            continue
    return False


def _clear_uploaded_attachments(driver: webdriver.Chrome, *, max_rounds: int = 3) -> bool:
    """
    尝试点击附件 chip 上的“移除/删除”按钮；若失败，用 JS 直接移除节点兜底。
    """
    removed_any = False
    for _ in range(max_rounds):
        removed_this_round = False

        # 1) 先找可能的 chip 容器
        chips = driver.find_elements(
            By.CSS_SELECTOR,
            (
                "[data-testid*='uploaded'][data-testid*='file'], "
                "[data-testid*='attachment'], "
                "[class*='uploaded'][class*='file']"
            )
        )

        for chip in chips:
            try:
                # 2) 先尝试点“移除”类按钮
                btn = None
                for sel in [
                    "button[aria-label^='Remove']",
                    "button[aria-label*='移除']",
                    "button[aria-label*='删除']",
                    "[data-testid*='remove']",
                    "button"
                ]:
                    cand = chip.find_elements(By.CSS_SELECTOR, sel)
                    if cand:
                        btn = cand[-1]
                if btn:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    driver.execute_script("arguments[0].click();", btn)
                    removed_any = True
                    removed_this_round = True
                    time.sleep(0.2)
                    continue

                # 3) 点不到就直接移除节点（兜底）
                driver.execute_script("arguments[0].remove();", chip)
                removed_any = True
                removed_this_round = True
            except Exception:
                continue

        if not removed_this_round:
            break

    return removed_any


def _start_new_chat(driver: webdriver.Chrome, wait: WebDriverWait, timeout: int = 10) -> None:
    """
    点击 ChatGPT 左侧或顶部的“New chat”按钮。
    选择多个可能的 selector 以适配 UI 变更；找不到就刷新。
    """
    candidates = [
        (By.CSS_SELECTOR, "[data-testid='new-chat-button']"),
        (By.CSS_SELECTOR, "a[aria-label^='New chat']"),
        (By.XPATH, "//button[contains(., 'New chat') or contains(., '新对话')]"),
    ]
    for by, sel in candidates:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, sel)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8)
            return
        except Exception:
            continue
    # 兜底：刷新整页
    driver.refresh()
    time.sleep(1.5)


def _prepare_upload_composer(driver: webdriver.Chrome) -> None:
    """Clear residual upload state before starting a new attachment cycle."""
    _clear_uploaded_attachments(driver)



def chatgpt_ask_questions(
    driver: webdriver.Chrome,
    chatgpt_url: str,
    questions: Iterable[str],
    *,
    wait_between=(5, 10),
    log_html: bool = False,
    log_dir: Optional[str] = None,
) -> List[str]:
    """Visit ChatGPT and return assistant replies for each question."""
    driver.get(chatgpt_url)
    driver.implicitly_wait(10)
    if log_html:
        _log_page_html(driver, "page_loaded", log_dir=log_dir)

    answers: List[str] = []
    assistant_selector = (By.CSS_SELECTOR, '[data-message-author-role="assistant"]')

    for idx, question in enumerate(questions, start=1):
        if log_html:
            _log_page_html(driver, f"before_question_{idx}", log_dir=log_dir)
        textarea = _find_chat_textarea(driver)
        textarea.send_keys(Keys.CONTROL, "a")
        textarea.send_keys(Keys.BACKSPACE)
        textarea.send_keys(question)
        existing_answers = len(driver.find_elements(*assistant_selector))
        textarea.send_keys(Keys.ENTER)
        if log_html:
            _log_page_html(driver, f"question_submitted_{idx}", log_dir=log_dir)
        answer = _wait_for_new_assistant_reply(driver, previous_count=existing_answers)
        answers.append(answer)
        if log_html:
            _log_page_html(driver, f"answer_received_{idx}", log_dir=log_dir)
        time.sleep(random.randint(*wait_between))
    return answers


def chatgpt_file_summary(
    driver: webdriver.Chrome,
    chatgpt_url: str,
    file_list: Iterable[str],
    *,
    summary_prompt: str = "请忘记历史对话，阅读刚刚上传的文件内容，并用中文概括其核心观点和关键结论。",
    wait_between: tuple[int, int] = (60, 90),
    upload_wait: float = 10.0,
    reply_timeout: int = 180,
    log_html: bool = False,
    log_dir: Optional[str] = None,
) -> List[tuple[str, str]]:
    """Upload documents to ChatGPT and request summaries for each file."""
    driver.get(chatgpt_url)
    driver.implicitly_wait(15)
    if log_html:
        _log_page_html(driver, "file_flow_page_loaded", log_dir=log_dir)

    wait = WebDriverWait(driver, 15)
    answers: List[tuple[str, str]] = []
    assistant_selector = (By.CSS_SELECTOR, '[data-message-author-role="assistant"]')

    for file_path in file_list:
        file_name = os.path.basename(file_path)
        if not os.path.exists(file_path):
            print(f"文件不存在，跳过: {file_path}")
            continue

         # 0) 先开新对话，确保干净
        _start_new_chat(driver, wait)

        # 1) 清理 composer（理论上新对话已干净，这步是兜底）
        _prepare_upload_composer(driver)

        if log_html:
            _log_page_html(driver, f"before_upload_{_sanitize_label(file_name)}", log_dir=log_dir)
        
        _click_attachment_button(driver, wait)
        # 3) 取“最后一个” file input 来 send_keys（避免误用旧的隐藏 input）
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if not file_inputs:
            raise RuntimeError("未找到文件选择框")
        file_inputs[-1].send_keys(file_path)
        time.sleep(upload_wait)

        # 4) 发送提示词并等待回复
        textarea = _find_chat_textarea(driver)
        textarea.send_keys(Keys.CONTROL, "a")
        textarea.send_keys(Keys.BACKSPACE)
        prompt = f"{summary_prompt}\n文件名：{file_name}"
        textarea.send_keys(prompt)
        previous_count = len(driver.find_elements(*assistant_selector))
        textarea.send_keys(Keys.ENTER)
        if log_html:
            _log_page_html(driver, f"after_submit_{_sanitize_label(file_name)}", log_dir=log_dir)
        try:
            answer = _wait_for_new_assistant_reply(
                driver,
                previous_count=previous_count,
                timeout=reply_timeout,
            )
            answers.append((file_name, answer))
            if log_html:
                _log_page_html(driver, f"answer_{_sanitize_label(file_name)}", log_dir=log_dir)
        except TimeoutException:
            print(f"等待回复超时: {file_name}")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"处理文件 {file_name} 时发生错误: {exc}")
            
         # 5) 本轮结束后再清一次附件（保险）
        _prepare_upload_composer(driver)
        # 6) 随机间隔
        time.sleep(random.randint(*wait_between))

    return answers


if __name__ == "__main__":
    PORT = 9222
    CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    PROFILE = r"X:/RPA/selenium_tools/ChatGPTProfile1"

    # 1) 启动带调试端口的 Chrome
    proc = start_chrome(chrome_path=CHROME, user_data_dir=PROFILE, debug_port=PORT)

    # 2) 连接已启动的实例
    #    建议先不传 driver_path，让 Selenium Manager 自动匹配驱动版本
    driver = connect_chrome(debug_port=PORT, driver_path="X:/RPA/selenium_tools/chromedriver-win64/chromedriver.exe")
    url = "https://chat.openai.com"
    try:
        # 示例1：直接询问chatgpt问题
        # prompts = [
        #     "请用100字总结一下人工智能的核心挑战。",
        #     "列出3个常用的Python数据分析库，并说明各自的典型用途。",
        # ]
        # results = chatgpt_ask_questions(
        #     driver,
        #     chatgpt_url=url,
        #     questions=prompts,
        #     log_html=True,
        #     log_dir=os.path.join(os.getcwd(), "logs", "selenium_chatgpt"),
        # )
        # for idx, response in enumerate(results, start=1):
        #     print(f"第{idx}个问题的回答:\n{response}\n{'-' * 40}")

        # 示例：批量上传文件并请求 ChatGPT 输出总结
        base_dir = r"X:\RAG_192.168.1.2\rag_data\量化拯救散户"
        if os.path.isdir(base_dir):
            files_to_upload = [
                os.path.join(base_dir, name)
                for name in os.listdir(base_dir)
                if os.path.isfile(os.path.join(base_dir, name))
            ]
            summaries = chatgpt_file_summary(
                driver,
                chatgpt_url=url,
                file_list=files_to_upload,
                summary_prompt="请直接总结我刚上传的文件，关注主要观点和数据结果。",
                wait_between=(70, 100),
                upload_wait=12.0,
                reply_timeout=240,
                log_html=True,
                log_dir=os.path.join(os.getcwd(), "logs", "selenium_chatgpt"),
            )
            for fname, summary in summaries:
                print(f"文件: {fname}\n回复:\n{summary}\n{'=' * 40}")
    finally:
        try:
            driver.quit()
        finally:
            # 尝试关闭我们自己启动的 Chrome 进程（如果需要）
            if proc and proc.poll() is None:
                proc.terminate()
