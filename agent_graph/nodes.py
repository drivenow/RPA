from __future__ import annotations

import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
try:
    from markdownify import markdownify as md
except ImportError:  # pragma: no cover - optional dependency
    def md(html: str) -> str:
        return html

from src.tools_data_process.utils_html_lazy_picture import (
    normalize_lazy_images,
    fix_strikethrough_html,
)

from .state import GraphState


class NodeError(RuntimeError):
    """统一的节点异常，便于写入 GraphState。"""

    def __init__(self, node: str, message: str):
        self.node = node
        self.message = message
        super().__init__(f"{node}: {message}")


def fetch_html_node(state: GraphState, timeout: int = 20) -> GraphState:
    """根据 URL 读取 HTML，可处理 http(s) 与 file:///本地路径。"""

    start = time.time()
    source = state.url

    try:
        if source.startswith("file://"):
            file_path = Path(urlparse(source).path)
            html = file_path.read_text(encoding="utf-8")
            origin = "file"
        else:
            file_candidate = Path(source)
            if file_candidate.exists():
                html = file_candidate.read_text(encoding="utf-8")
                origin = "file"
            else:
                headers = {"User-Agent": "LangGraphDemo/0.1"}
                resp = requests.get(source, timeout=timeout, headers=headers)
                resp.raise_for_status()
                html = resp.text
                origin = "http"
    except Exception as exc:
        raise NodeError("FetchHtmlNode", str(exc)) from exc

    state.raw_html = html
    duration_ms = int((time.time() - start) * 1000)
    state.context["fetch"] = {"origin": origin, "cost_ms": duration_ms}
    return state


def lazy_image_node(state: GraphState) -> GraphState:
    """调用现有工具，修复懒加载图片并去除删除线样式。"""

    if not state.raw_html:
        raise NodeError("LazyImageFixNode", "raw_html is empty")

    try:
        normalized = normalize_lazy_images(state.raw_html)
        fixed = fix_strikethrough_html(normalized)
    except Exception as exc:
        raise NodeError("LazyImageFixNode", str(exc)) from exc

    state.clean_html = fixed
    state.context["lazy_image"] = {"updated": True}
    return state


def html_to_text_node(state: GraphState) -> GraphState:
    """将 HTML 转为纯文本，方便下游摘要。"""

    html = state.clean_html or state.raw_html
    if not html:
        raise NodeError("Html2TextNode", "no html content to parse")

    try:
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text("\n")
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)
    except Exception as exc:
        raise NodeError("Html2TextNode", str(exc)) from exc

    state.plain_text = text
    state.context["text"] = {"word_count": len(text)}
    state.context["markdown_preview"] = md(html)[:1000]
    return state


def summary_node(state: GraphState, max_sentences: int = 3) -> GraphState:
    """简单规则总结，后续可以换为真正的 LLM 调用。"""

    if not state.plain_text:
        raise NodeError("SummaryNode", "plain_text is empty")

    sentences = [
        s for s in state.plain_text.replace("！", "。").split("。") if s.strip()
    ]
    summary = "。".join(sentences[:max_sentences])
    if summary:
        summary += "。"

    state.summary = summary or state.plain_text[:200]
    state.context["summary"] = {"sentences_used": min(max_sentences, len(sentences))}
    return state


NodeFunc = Callable[[GraphState], GraphState]

PIPELINE: tuple[NodeFunc, ...] = (
    fetch_html_node,
    lazy_image_node,
    html_to_text_node,
    summary_node,
)
