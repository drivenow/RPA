# -*- coding: utf-8 -*-
"""
Playwright version of your Selenium uploader:
- Launches Chrome with a persistent user profile (so you stay logged-in).
- Opens ChatGPT, starts a fresh chat, uploads files via the real file chooser,
  waits for upload to finish, sends a summary prompt, and collects replies.
- Includes robust fallbacks for selectors and "always spinning" upload issues.

Usage:
  pip install playwright
  playwright install
  python playwright_chatgpt_upload.py --base_filelist_dir <path> --id A --prompt PROMPT_CODE 

Notes:
- Make sure the profile directory exists and is dedicated to automation (avoid your daily profile).
- The script assumes you are already logged in to chat.openai.com in that profile.
"""
import os, re, time, json, socket, random, subprocess
from datetime import datetime
from typing import Iterable, List, Optional, Tuple, Dict, Any
from bs4 import BeautifulSoup
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    expect,
)
import shutil
import argparse
from src.prompts.factor_prompts import PROMPT_CODE, PROMPT_LOGIC

# ------------------------------
# 多实例支持配置
# ------------------------------
CHATGPT_URL = "https://chat.openai.com"  # or your localized domain

HEADLESS = False  # only used if we fall back to persistent context launch
REPLY_TIMEOUT_SEC = 300
UPLOAD_TIMEOUT_SEC = 180
WAIT_BETWEEN_FILES = (30, 45)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def make_run_profile(run_id: str | None = None, profile_dir: str | None = None, PROFILE_TEMPLATE = r"X:/RPA/selenium_tools/ChatGPTProfile1") -> str:
    _ensure_dir(profile_dir)
    rid = run_id or f"{os.getpid()}-{int(time.time())}-{random.randint(1000,9999)}"
    dst = os.path.join(profile_dir, f"ChatGPTProfile_{rid}")
    if not os.path.exists(dst):
        # 可选：从模板复制（模板需在关闭 Chrome 后制作）
        if os.path.isdir(PROFILE_TEMPLATE):
            shutil.copytree(PROFILE_TEMPLATE, dst)
        else:
            os.makedirs(dst, exist_ok=True)
    return dst


def _sanitize_filename(name: str) -> str:
    bad = '<>:"/\\|?*'
    out = "".join("_" if c in bad else c for c in name)
    out = out.strip().strip(".")
    return out or "output"


def _write_text(path: str, text: str) -> None:
    _ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# 1) 清理零宽字符/行首 >、多余换行
_ZERO_WIDTH = dict.fromkeys(
    map(
        ord,
        [
            "\u200b",
            "\u200c",
            "\u200d",
            "\u200e",
            "\u200f",
            "\u202a",
            "\u202b",
            "\u202c",
            "\u202d",
            "\u202e",
            "\u2060",
            "\u2061",
            "\u2062",
            "\u2063",
            "\ufeff",
        ],
    ),
    None,
)


def _clean_text(s: str) -> str:
    s = s.translate(_ZERO_WIDTH)
    # 去掉被样式注入的行首 > / › / ❯ 等
    s = re.sub(r"^[>\u203a\u276f\u25b8]+\s*", "", s, flags=re.M)
    # 合并多余空行
    s = re.sub(r"\n[ \t]+\n", "\n\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _boot_playwright_persistent(user_data_dir: str, headless: bool = False):
    p = sync_playwright().start()
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        channel="chrome",
        headless=headless,
        args=["--no-first-run", "--no-default-browser-check"],
    )
    page = context.pages[0] if context.pages else context.new_page()
    return p, context.browser, context, page, None


# ------------------------------
# DOM helpers
# ------------------------------


def _goto(page, url: str):
    page.goto(url, wait_until="domcontentloaded")


def _start_new_chat(page) -> None:
    """
    Click "New chat" to ensure a clean composer. Try several selectors then fallback to reload.
    """
    candidates = [
        lambda: page.get_by_role("button", name=re.compile(r"New chat|新对话", re.I)),
        lambda: page.locator("button:has-text('New chat')"),
        lambda: page.locator("button:has-text('新对话')"),
    ]
    for fn in candidates:
        try:
            btn = fn()
            btn.first.wait_for(state="visible", timeout=3000)
            btn.first.click()
            page.wait_for_timeout(800)
            return
        except Exception:
            continue
    page.reload()
    page.wait_for_timeout(1500)


def _find_prompt_input(page):
    """
    Return the prompt input (works for both <textarea id=prompt-textarea> and contenteditable div).
    """
    loc = page.locator("#prompt-textarea, div[contenteditable='true']#prompt-textarea")
    loc.first.wait_for(state="visible", timeout=10000)
    return loc.first


def _is_generating(page, last_selector: str | None = None) -> bool:
    try:
        # 全局 Stop 按钮（生成中）
        if page.locator('[data-testid="stop-button"]').count() > 0:
            return True
        # 最后一条 assistant 上的进度迹象
        if last_selector:
            last = page.locator(last_selector)
        else:
            last = page.locator("[data-message-author-role='assistant']").last
        if (
            last.count() > 0
            and last.locator(
                "[role='progressbar'], [aria-busy='true'], .animate-spin"
            ).count()
            > 0
        ):
            return True
    except Exception:
        pass
    return False


def _wait_until_idle(page, idle_timeout_sec: int = 15) -> bool:
    """等到页面不再处于生成中；返回是否成功空闲。"""
    t0 = time.time()
    while time.time() - t0 < idle_timeout_sec:
        if not _is_generating(page):
            return True
        time.sleep(0.25)
        # page.wait_for_timeout(250)
    return False


def _cancel_generation_if_any(page, max_wait_sec: int = 8) -> None:
    """如果在生成，就点 Stop；再等到空闲。"""
    try:
        btn = page.locator('[data-testid="stop-button"]')
        if btn.count() > 0:
            btn.first.click(timeout=2000)
    except Exception:
        pass
    _wait_until_idle(page, idle_timeout_sec=max_wait_sec)


def _clear_uploaded_attachments(page) -> bool:
    """
    Click 'Remove' buttons on attachment chips to clear composer.
    Returns True if any were removed.
    """
    removed_any = False
    try:
        remove_buttons = page.locator(
            "button[aria-label^='Remove'], button[aria-label*='移除'], button[aria-label*='删除']"
        )
        for _ in range(3):
            n = remove_buttons.count()
            if n == 0:
                break
            # click last ones first
            for i in reversed(range(n)):
                try:
                    remove_buttons.nth(i).click(timeout=1000)
                    removed_any = True
                    page.wait_for_timeout(200)
                except Exception:
                    pass
            # update reference
            remove_buttons = page.locator(
                "button[aria-label^='Remove'], button[aria-label*='移除'], button[aria-label*='删除']"
            )
    except Exception:
        pass

    # Fallback: brutal remove (JS) if buttons not found
    if not removed_any:
        try:
            page.evaluate(
                """() => {
                const chips = document.querySelectorAll('[data-testid*="attachment"], [class*="uploaded"][class*="file"]');
                chips.forEach(ch => ch.remove());
            }"""
            )
            removed_any = True
        except Exception:
            pass

    return removed_any


def _wait_for_upload_complete(
    page, *, filename: str | None = None, timeout_sec: int = 180
) -> None:
    """
    通用的“上传完成”判定：适配图片缩略图卡片和文件卡片（pdf、docx 等）。
    条件：
      1) 附件容器出现
      2) 至少一个附件卡片出现（缩略图或文件卡）
      3) 卡片上出现删除按钮（Remove/移除/删除）
      4) 卡片内无任何进度/旋转元素
    """

    # 1) 容器（水平滚动条/附件条）
    container_sels = [
        ".horizontal-scroll-fade-mask",  # 旧/常见
        "[data-testid*='attachment-strip']",
        "[data-testid*='attachmentBar']",
    ]
    container = page.locator(",".join(container_sels))
    container.first.wait_for(state="visible", timeout=timeout_sec * 1000)

    # 2) 附件卡片：图片缩略图 或 文件卡
    #   - 图片：通常是 <img> 或 [role="img"] 出现在容器里
    #   - 文件：常见有 .truncate.font-semibold（文件名），但不要强依赖
    chip_sels = [
        # 通用/内部测试 id
        "[data-testid*='attachment']",
        "[data-testid*='asset']",
        # 图片缩略图
        "img",
        "[role='img']",
        # 常见的文件卡根节点
        ".group.text-token-text-primary",
    ]
    chips = container.locator(",".join(chip_sels))
    chips.first.wait_for(state="visible", timeout=timeout_sec * 1000)

    # 3) 删除按钮（出现通常意味着上传已完成）
    remove_btn = container.locator(
        "button[aria-label^='Remove'],"
        "button[aria-label*='移除'],"
        "button[aria-label*='删除']"
    )
    remove_btn.first.wait_for(state="visible", timeout=timeout_sec * 1000)

    # （可选）如果传了文件名，尽量匹配一下但不强制
    if filename:
        base = os.path.basename(filename)
        stem = os.path.splitext(base)[0]
        key = stem[:12] if len(stem) > 12 else stem
        if key:
            try:
                container.locator(f":text('{key}')").first.wait_for(timeout=2000)
            except Exception:
                # 图片卡片可能没有文字文件名，忽略即可
                pass

    # 4) 轮询：容器里无“加载/进度”迹象
    def no_spinner() -> bool:
        return page.evaluate(
            """(containerSel) => {
                const root = document.querySelector(containerSel);
                if (!root) return false;
                const spinners = root.querySelectorAll([
                    '[role="progressbar"]',
                    '[aria-busy="true"]',
                    '.animate-spin',
                    'circle[stroke-dasharray]',
                    'circle[style*="stroke-dashoffset"]'
                ].join(','));
                return spinners.length === 0;
            }""",
            container_sels[0],  # 取第一个命中的容器选择器
        )

    t0 = time.time()
    while True:
        try:
            # 仍然可见的附件 + 删除按钮存在
            if chips.count() > 0 and remove_btn.count() > 0 and no_spinner():
                break
        except Exception:
            pass
        if time.time() - t0 > timeout_sec:
            raise TimeoutError("等待上传完成超时：仍检测到进度或未出现删除按钮")
        page.wait_for_timeout(300)

    # 5) （可选）发送按钮可用（有的版本一直可用，所以不强制）
    try:
        page.wait_for_selector(
            '#composer-submit-button:not([disabled]):not([aria-disabled="true"])',
            timeout=3000,
        )
    except Exception:
        pass


def _wait_for_new_assistant_reply(
    page,
    previous_count: int,  # 参数保留但不强依赖
    timeout_sec: int = REPLY_TIMEOUT_SEC,
    stability_window_sec: float = 3,  # 文本在此时间内不再变化 => 完成
) -> str:
    sel = "[data-message-author-role='assistant']"
    msgs = page.locator(sel)

    start_time = time.time()
    deadline = start_time + timeout_sec

    # 记录“开始前”的状态
    try:
        initial_count = msgs.count()
    except Exception:
        initial_count = 0
    try:
        initial_last_html = msgs.last.inner_html() if initial_count > 0 else ""
    except Exception:
        initial_last_html = ""

    # -------- 1) 等“生成开始”：新增一条 或 最后一条变化 或 出现 Stop/进度 --------
    def _started() -> bool:
        try:
            cur_count = msgs.count()
            if cur_count > initial_count:
                return True
            if cur_count > 0 and cur_count == initial_count:
                try:
                    cur_last_html = msgs.last.inner_html()
                except Exception:
                    cur_last_html = ""
                if cur_last_html != initial_last_html:
                    return True
            if _is_generating(page):  # Stop 按钮/进度元素
                return True
        except Exception:
            pass
        return False

    while time.time() < deadline and not _started():
        page.wait_for_timeout(150)

    if time.time() >= deadline:
        raise TimeoutError("等待助手开始生成超时")

    # -------- 2) 文本稳定窗口 --------
    last = msgs.last
    try:
        last.wait_for(state="visible", timeout=10_000)
    except Exception:
        pass

    prev_text = ""
    stable_since = time.time()

    while True:
        try:
            cur_text = last.inner_text(timeout=1000).strip()
        except Exception:
            cur_text = ""

        # 仍在生成，或文本变化 => 重置稳定计时
        if cur_text != prev_text or _is_generating(
            page, last_selector=sel + ":last-of-type"
        ):
            prev_text = cur_text
            stable_since = time.time()
        else:
            if time.time() - stable_since >= stability_window_sec:
                break

        if time.time() >= deadline:
            break
        time.sleep(0.2)
        # page.wait_for_timeout(200)

    return (prev_text or "").strip()


def html_to_markdown(html_content, save_file=None):
    from markdownify import markdownify as md
    from markdownify import MarkdownConverter
    from bs4 import BeautifulSoup

    class MathFriendlyConverter(MarkdownConverter):
        def convert_sup(self, el, text, convert_as_inline):
            return f"<sup>{text}</sup>"  # 保留原始 HTML，不丢信息

        def convert_sub(self, el, text, convert_as_inline):
            return f"<sub>{text}</sub>"

        # MathML → LaTeX 片段
        def convert_msup(self, el, text, inline):
            base = self.convert(el.contents[0])
            sup = self.convert(el.contents[1])
            return f"${base}^{{{sup}}}$"

        def convert_msub(self, el, text, inline):
            base = self.convert(el.contents[0])
            sub = self.convert(el.contents[1])
            return f"${base}_{{{sub}}}$"

        def convert_msubsup(self, el, text, inline):
            base = self.convert(el.contents[0])
            sub = self.convert(el.contents[1])
            sup = self.convert(el.contents[2])
            return f"${base}_{{{sub}}}^{{{sup}}}$"

    def html_to_md_keep_math(html):
        soup = BeautifulSoup(html, "lxml")

        # KaTeX：优先换回原始 TeX（最佳做法）
        for katex in soup.select("span.katex"):
            ann = katex.select_one('annotation[encoding="application/x-tex"]')
            if ann and ann.string:
                katex.replace_with(f"${ann.string.strip()}$")

        # 运行自定义转换器；wrap=None 关闭自动换行，避免把 \sigma 之类切断
        return MathFriendlyConverter(wrap=None).convert_soup(soup)

    html_content = html_to_md_keep_math(html_content)
    markdown_content = md(html_content, heading_style="ATX")  # 自定义标题风格为ATX
    # print(markdown_content)
    if save_file:
        with open(save_file, "w", encoding="utf-8") as f:
            f.writelines(markdown_content)
    return markdown_content


def _get_last_assistant_markdown(page) -> str:
    last = page.locator("[data-message-author-role='assistant']").last
    html = last.inner_html()  # 不触发 CSP 的 unsafe-eval
    return html_to_markdown(html)


def _send_prompt_and_wait(
    page, prompt: str, reply_timeout_sec: int = REPLY_TIMEOUT_SEC
) -> str:
    # 先把上一次的生成停掉/等到空闲
    _cancel_generation_if_any(page, max_wait_sec=10)

    input_box = _find_prompt_input(page)
    try:
        input_box.fill("")
    except Exception:
        input_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")

    try:
        input_box.fill(prompt)
    except Exception:
        input_box.click()
        page.keyboard.type(prompt)

    # 点击发送按钮更稳（避免 Enter 被当作换行）
    send_btn = page.locator("#composer-submit-button, [data-testid='send-button']")
    if send_btn.count() > 0:
        try:
            send_btn.first.click(timeout=2000)
        except Exception:
            input_box.press("Enter")
    else:
        input_box.press("Enter")

    # 不再依赖 “+1”，直接进入新版等待
    reply = _wait_for_new_assistant_reply(
        page, previous_count=0, timeout_sec=reply_timeout_sec
    )
    # 用 HTML → Markdown 的方式再取一次“最后一条”，得到干净的文本/TeX
    try:
        reply_md = _get_last_assistant_markdown(page)
        return reply_md if reply_md else _clean_text(reply)
    except Exception:
        return _clean_text(reply)


def _export_summary_and_transcript(
    page, out_dir: str, summary_path: str, answer: str, prompt: str = None, 
):
    _ensure_dir(out_dir)
    meta = f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nURL: {page.url}\n\n"
    if prompt:
        _write_text(
            summary_path,
            meta + "### Prompt\n" + prompt + "\n\n### Assistant Reply\n" + answer,
        )
    else:
        _write_text(summary_path, answer)

    return summary_path


# ------------------------------
# High-level flows
# ------------------------------


def chatgpt_ask_questions(
    page, chatgpt_url: str, questions: Iterable[str], wait_between=(5, 10)
) -> List[str]:
    _goto(page, chatgpt_url)
    answers: List[str] = []
    for q in questions:
        _start_new_chat(page)
        ans = _send_prompt_and_wait(page, q, reply_timeout_sec=REPLY_TIMEOUT_SEC)
        answers.append(ans)
        page.wait_for_timeout(random.randint(*wait_between) * 1000)
    return answers


def chatgpt_file_summary(
    page,
    chatgpt_url: str,
    file_list: Iterable[str],
    export_dir: str,
    *,
    summary_prompt: str = "请忘记历史对话，阅读刚刚上传的文件内容，并用中文概括其核心观点和关键结论。",
    wait_between: Tuple[int, int] = (60, 90),
    reply_timeout_sec: int = REPLY_TIMEOUT_SEC,
) -> List[Tuple[str, str]]:
    _goto(page, chatgpt_url)
    results: List[Tuple[str, str]] = []

    for file_path in file_list:
        if True:
            fname = os.path.basename(file_path)
            safe_base = _sanitize_filename(os.path.splitext(fname)[0])
            summary_path = os.path.join(export_dir, f"{safe_base}.summary.txt")
            if os.path.exists(summary_path):
                continue
            if not os.path.exists(file_path):
                print(f"[Skip] 文件不存在: {file_path}")
                continue

            print(f"[Info] 处理文件: {fname}")
            _start_new_chat(page)
            _clear_uploaded_attachments(page)

            # 1) open the plus/menu -> click "Add photos & files" (or zh)
            # Use role=button then role=menuitem with regex names
            plus_candidates = [
                page.locator("#composer-plus-btn"),
                page.locator("[data-testid='composer-plus-btn']"),
                page.get_by_role("button", name=re.compile(r"Add|添加|\+", re.I)),
            ]
            clicked_plus = False
            for loc in plus_candidates:
                try:
                    loc.wait_for(state="visible", timeout=3000)
                    loc.click()
                    clicked_plus = True
                    break
                except Exception:
                    continue
            if not clicked_plus:
                # try a generic popup menu button
                try:
                    page.locator("button[aria-haspopup='menu']").first.click(
                        timeout=3000
                    )
                    clicked_plus = True
                except Exception:
                    pass

            if not clicked_plus:
                raise RuntimeError("找不到“+”动作菜单按钮")

            # 2) Expect a file chooser from the menu item click
            menuitem = None
            for loc in [
                page.get_by_role(
                    "menuitem",
                    name=re.compile(
                        r"(?:Add photos.*files|Add files|添加照片和文件|添加文件)", re.I
                    ),
                ),
                page.locator("div[role='menuitem']:has-text('Add files')"),
                page.locator("div[role='menuitem']:has-text('添加照片和文件')"),
            ]:
                try:
                    loc.first.wait_for(state="visible", timeout=5000)
                    menuitem = loc.first
                    break
                except Exception:
                    continue
            if menuitem is None:
                raise RuntimeError("找不到“添加照片和文件 / Add files”菜单项")

            with page.expect_file_chooser() as fc_info:
                menuitem.click()
            file_chooser = fc_info.value
            file_chooser.set_files(file_path)  # <-- reliably triggers change event

            # 3) wait for upload to complete
            _wait_for_upload_complete(page, timeout_sec=UPLOAD_TIMEOUT_SEC)

            # 4) send the summary prompt and wait
            prompt = f"{summary_prompt}\n文件名：{fname}"
            try:
                answer = _send_prompt_and_wait(
                    page, prompt, reply_timeout_sec=reply_timeout_sec
                )
            except TimeoutError:
                # 一次兜底：停掉生成 -> 再点发送
                _cancel_generation_if_any(page, max_wait_sec=10)
                if (
                    page.locator(
                        "#composer-submit-button, [data-testid='send-button']"
                    ).count()
                    > 0
                ):
                    page.locator(
                        "#composer-submit-button, [data-testid='send-button']"
                    ).first.click()
                else:
                    _find_prompt_input(page).press("Enter")
                answer = _wait_for_new_assistant_reply(
                    page, previous_count=0, timeout_sec=reply_timeout_sec
                )

            results.append((fname, answer))

            print(f"[Export] 写入输出到目录：{export_dir}")
            _export_summary_and_transcript(
                page,
                out_dir=export_dir,
                summary_path=summary_path,
                prompt="",
                answer=answer,
            )

            _clear_uploaded_attachments(page)
            page.wait_for_timeout(random.randint(*wait_between) * 1000)

    return results


# ------------------------------
# Main
# ------------------------------


def chat_example(
    run_id: str | None = None, profile_dir: str | None = None, headless: bool = False
):
    profile_dir = make_run_profile(run_id, profile_dir=profile_dir)
    print(f"[Instance] run_id={run_id or 'auto'}  profile={profile_dir}")
    p, browser, context, page, proc = _boot_playwright_persistent(
        profile_dir, headless=headless
    )
    answers = chatgpt_ask_questions(
        page,
        CHATGPT_URL,
        [
            "请用100字总结一下人工智能的核心挑战。",
            "列出3个常用的Python数据分析库，并说明各自的典型用途。",
        ],
        wait_between=REPLY_TIMEOUT_SEC,
    )
    for i, a in enumerate(answers, 1):
        print(f"Q{i} 答复：\n{a}\n{'-'*40}")


def main(
    base_filelist_dir,
    export_dir,
    prompt,
    run_id: str | None = None,
    profile_dir: str | None = None,
    headless: bool = False,
    debug = False,
):
    """
    功能描述：基于 ChatGPT 聊天机器人，对指定目录下的文件进行自动摘要。
    base_filelist_dir: 待上传文件目录
    export_dir: 导出目录
    prompt: 摘要提问
    run_id: 实例标识(用于用户目录后缀)
    profile_dir: 用户目录；不传则自动创建并可从模板复制
    debug: 调试模式，手动操作浏览器保存cookies
    """

    # 1) 为本实例准备端口与用户目录
    profile_dir = make_run_profile(run_id, profile_dir=profile_dir)
    print(f"[Instance] run_id={run_id or 'auto'}  profile={profile_dir} base_filelist_dir={base_filelist_dir} export_dir={export_dir} prompt={prompt[:50]}")
    p, browser, context, page, proc = _boot_playwright_persistent(
        profile_dir, headless=headless
    )
    if debug:
        time.sleep(100000)  # 等待 attach 调试器
    try:
        # Example: summarize a directory of files
        if os.path.isdir(base_filelist_dir):
            files_to_upload = []
            for name in os.listdir(base_filelist_dir):
                if os.path.isfile(os.path.join(base_filelist_dir, name)) and \
                     os.path.getsize(os.path.join(base_filelist_dir, name)) \
                    <= 50 * 1024 * 1024 and \
                     not name.lower().endswith((".zip", ".rar")):
                    files_to_upload.append(os.path.join(base_filelist_dir, name))
        else:
            files_to_upload = []

        if not files_to_upload:
            print("[Warn] 未找到待上传文件；请修改 base_filelist_dir 或传入自定义列表。")
        else:
            summaries = chatgpt_file_summary(
                page,
                chatgpt_url=CHATGPT_URL,
                file_list=files_to_upload,
                summary_prompt=prompt,
                wait_between=WAIT_BETWEEN_FILES,
                reply_timeout_sec=REPLY_TIMEOUT_SEC,
                export_dir=export_dir,
            )
            for fname, summary in summaries:
                print(f"文件: {fname}\n回复:\n{summary}\n{'=' * 40}")
            print(f"[Done] 导出目录：{export_dir}")
    finally:
        # Otherwise, close as usual
        try:
            context.close()
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            p.stop()
        except Exception:
            pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input_dir", dest="base_filelist_dir", default=None, help="待上传文件目录"
    )
    ap.add_argument("--prompt", dest="prompt", default="PROMPT_LOGIC", choices=["PROMPT_CODE", "PROMPT_LOGIC"], help="摘要提问")
    ap.add_argument("--id", dest="run_id", help="实例标识(用于用户目录后缀)")
    ap.add_argument(
        "--profile",
        dest="profile_dir",
        default=None,
        help="用户目录；不传则自动创建并可从模板复制",
    )
    ap.add_argument("--debug", dest="debug", action="store_true", help="调试模式，手动操作浏览器保存cookies")
    args = ap.parse_args()

    PROMPT = args.prompt
    PROFILE_DIR = (
        r"X:/RPA/selenium_tools/ChatGPTProfiles"
        if args.profile_dir is None
        else args.profile_dir
    )  # 运行时实例的根目录, 用于存放用户浏览器数据
    # BASE_DIR = r"X:/RAG_192.168.1.2/rag_data/yinzirili_pdf_images/" if args.base_filelist_dir is None else args.base_filelist_dir
    BASE_FILELIST_DIR = (
        r"X:/RAG_192.168.1.2/rag_data/量化拯救散户/"
        if args.base_filelist_dir is None
        else args.base_filelist_dir
    )
    BASE_NAME = os.path.basename(BASE_FILELIST_DIR.strip("/\\"))
    EXPORT_DIR = os.path.join(
        r"X:/RAG_192.168.1.2/rag_data/{}".format(PROMPT), BASE_NAME
    )
    PROMPT = eval(PROMPT)

    retry = 0
    while retry < 10:
        try:
            main(
                run_id=args.run_id,
                profile_dir=PROFILE_DIR,
                base_filelist_dir=BASE_FILELIST_DIR,
                export_dir=EXPORT_DIR,
                prompt=PROMPT,
                headless=False,
                debug=args.debug,
            )
            break
        except Exception as e:
            import traceback

            traceback.print_exc()
            print("main Error:", e)
            retry += 1

    print("浏览器会随着本进程一起关；主动按 Ctrl+C 结束。")
    time.sleep(100000)


