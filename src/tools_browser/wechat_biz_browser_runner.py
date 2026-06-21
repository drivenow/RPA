# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from numbers import Number
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import psutil
import pyperclip
import win32con
import win32gui
import win32process
from filelock import FileLock
from pywinauto import Application
from pywinauto.keyboard import send_keys


WECHAT_BROWSER_PROCESS = "WeChatAppEx.exe"
WM_MOUSEWHEEL = 0x020A
WHEEL_DELTA = -120


@dataclass
class TopWindow:
    hwnd: int
    pid: int
    process_name: str
    title: str
    class_name: str
    rect: tuple[int, int, int, int]
    iconic: bool

    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]

    @property
    def area(self) -> int:
        return max(0, self.width) * max(0, self.height)


def build_profile_url(biz: str) -> str:
    biz = normalize_biz(biz)
    if not biz:
        raise ValueError("__biz is empty")
    return (
        "https://mp.weixin.qq.com/mp/profile_ext"
        f"?action=home&__biz={biz}&scene=124#wechat_redirect"
    )


def normalize_biz(value: str) -> str:
    biz = str(value or "").strip()
    if not biz:
        return ""
    return biz if biz.endswith("==") else f"{biz}=="


def extract_biz(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""

    if "__biz=" not in value and not value.startswith("http"):
        return normalize_biz(value)

    query = parse_qs(urlparse(value).query)
    biz = query.get("__biz", [""])[0]
    if biz:
        return normalize_biz(biz)

    match = re.search(r"[?&]__biz=([^&#]+)", value)
    return normalize_biz(match.group(1) if match else value)


def list_top_windows_by_process(process_name: str) -> list[TopWindow]:
    target = process_name.lower()
    rows: list[TopWindow] = []

    def callback(hwnd: int, _: Any) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            name = proc.name()
        except Exception:
            return

        if name.lower() != target:
            return

        rect = win32gui.GetWindowRect(hwnd)
        rows.append(
            TopWindow(
                hwnd=hwnd,
                pid=pid,
                process_name=name,
                title=win32gui.GetWindowText(hwnd).strip(),
                class_name=win32gui.GetClassName(hwnd),
                rect=rect,
                iconic=bool(win32gui.IsIconic(hwnd)),
            )
        )

    win32gui.EnumWindows(callback, None)
    return rows


def find_wechat_browser_window(hwnd: int | None = None) -> TopWindow:
    wins = list_top_windows_by_process(WECHAT_BROWSER_PROCESS)
    if hwnd is not None:
        for win in wins:
            if win.hwnd == hwnd:
                return win
        raise RuntimeError(f"没有找到指定 WeChatAppEx hwnd={hwnd}")

    wins = [win for win in wins if win.area > 100_000]
    if not wins:
        raise RuntimeError("没有找到 WeChatAppEx.exe 窗口。请先在微信里手动打开任意公众号文章。")

    return max(wins, key=lambda win: win.area)


def activate_hwnd(hwnd: int) -> None:
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)

    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    time.sleep(0.2)

    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_NOTOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception as exc:
            raise RuntimeError(
                f"无法将 hwnd={hwnd} 设为前台窗口，后续 send_keys 可能打到其他程序: {exc}"
            ) from exc

    time.sleep(0.3)


def get_uia_window(hwnd: int):
    app = Application(backend="uia").connect(handle=hwnd)
    return app.window(handle=hwnd)


def snapshot_uia(hwnd: int, limit: int | None = None) -> list[dict[str, Any]]:
    win = get_uia_window(hwnd)
    rows: list[dict[str, Any]] = []

    for elem in win.descendants():
        try:
            info = elem.element_info
            rect = elem.rectangle()
            row = {
                "text": elem.window_text() or "",
                "control_type": getattr(info, "control_type", ""),
                "class_name": getattr(info, "class_name", ""),
                "automation_id": getattr(info, "automation_id", ""),
                "rect": [rect.left, rect.top, rect.right, rect.bottom],
            }
            rows.append(row)
        except Exception:
            continue

        if limit is not None and len(rows) >= limit:
            break

    return rows


def page_signature(hwnd: int) -> str:
    title = win32gui.GetWindowText(hwnd).strip()
    rows = snapshot_uia(hwnd, limit=120)
    pieces = [title]

    for row in rows:
        if row["control_type"] in {"Document", "TabItem"} and row["text"]:
            pieces.append(row["text"][:500])

    if len(pieces) == 1:
        for row in rows:
            if row["text"]:
                pieces.append(row["text"][:200])
                if len(pieces) >= 4:
                    break

    return "\n".join(pieces)


def visible_page_signature(hwnd: int) -> str:
    rows = snapshot_uia(hwnd, limit=240)
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    pieces: list[str] = []
    document_pieces: list[str] = []

    for row in rows:
        text = " ".join((row["text"] or "").split())
        if not text:
            continue

        rect = row["rect"]
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        if width <= 0 or height <= 0:
            continue

        if rect[2] < left or rect[0] > right or rect[3] < top + 60 or rect[1] > bottom:
            continue

        if row["control_type"] == "Document":
            document_pieces.append(f"{row['control_type']}:{rect}:{text[:200]}")
        elif row["control_type"] in {"Text", "Hyperlink", "ListItem"}:
            pieces.append(f"{row['control_type']}:{rect}:{text[:160]}")

    if not pieces:
        return "\n".join(document_pieces[:10])

    return "\n".join(pieces[:80])


def dump_uia(hwnd: int, output: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows = snapshot_uia(hwnd, limit=limit)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    for row in rows:
        if row["text"]:
            print(
                f"[UIA] {row['control_type']} class={row['class_name']} "
                f"rect={tuple(row['rect'])} text={row['text']!r}"
            )
    print(f"[UIA] dumped {len(rows)} elements -> {output}")
    return rows


def find_address_edit_by_uia(hwnd: int):
    win = get_uia_window(hwnd)
    win_rect = win.rectangle()
    candidates: list[tuple[float, Any]] = []

    for elem in win.descendants():
        try:
            info = elem.element_info
            control_type = getattr(info, "control_type", "")
            if control_type != "Edit":
                continue

            text = elem.window_text() or ""
            rect = elem.rectangle()
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width < 200 or height < 18:
                continue

            score = width / 1000
            if rect.top < win_rect.top + 180:
                score += 3
            if any(token in text for token in ("地址", "网址", "URL", "http", "mp.weixin")):
                score += 10

            candidates.append((score, elem))
        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def navigate_by_address_edit(hwnd: int, url: str) -> bool:
    activate_hwnd(hwnd)
    edit = find_address_edit_by_uia(hwnd)
    if edit is None:
        print("[NAV] UIA 没找到可用 Edit 地址栏")
        return False

    try:
        print("[NAV] 尝试 UIA Edit 地址栏导航")
        edit.click_input()
        time.sleep(0.2)
        pyperclip.copy(url)
        send_keys("^a")
        time.sleep(0.1)
        send_keys("^v")
        time.sleep(0.1)
        send_keys("{ENTER}")
        return True
    except Exception as exc:
        print(f"[WARN] UIA Edit 导航失败: {exc}")
        return False


def navigate_by_ctrl_l(hwnd: int, url: str) -> bool:
    activate_hwnd(hwnd)
    try:
        print("[NAV] 尝试 Ctrl+L 导航")
        pyperclip.copy(url)
        send_keys("^l")
        time.sleep(0.2)
        send_keys("^a")
        time.sleep(0.1)
        send_keys("^v")
        time.sleep(0.1)
        send_keys("{ENTER}")
        return True
    except Exception as exc:
        print(f"[WARN] Ctrl+L 导航失败: {exc}")
        return False


def navigate_wechat_browser(hwnd: int, url: str, wait_seconds: float) -> str:
    print(f"[NAV] target={url}")
    before = page_signature(hwnd)

    method = ""
    if navigate_by_address_edit(hwnd, url):
        method = "uia-edit"
    elif navigate_by_ctrl_l(hwnd, url):
        method = "ctrl-l"
    else:
        raise RuntimeError("WeChatAppEx 没有可用导航入口，需要退回微信内点击链接方案。")

    time.sleep(wait_seconds)
    after = page_signature(hwnd)
    if after == before:
        raise RuntimeError(
            f"WeChatAppEx 已执行 {method}，但页面签名没有变化。"
            "该窗口大概率不支持外部导航，需要退回微信内点击链接方案。"
        )

    return method


def _pack_lparam(x: int, y: int) -> int:
    return (x & 0xFFFF) | ((y & 0xFFFF) << 16)


def _pack_wparam(high_word: int, low_word: int = 0) -> int:
    return (low_word & 0xFFFF) | ((high_word & 0xFFFF) << 16)


def _window_area(rect: tuple[int, int, int, int]) -> int:
    return max(0, rect[2] - rect[0]) * max(0, rect[3] - rect[1])


def list_child_windows(hwnd: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def callback(child_hwnd: int, _: Any) -> None:
        try:
            rect = win32gui.GetWindowRect(child_hwnd)
            rows.append(
                {
                    "hwnd": child_hwnd,
                    "class_name": win32gui.GetClassName(child_hwnd),
                    "title": win32gui.GetWindowText(child_hwnd),
                    "rect": rect,
                    "visible": bool(win32gui.IsWindowVisible(child_hwnd)),
                    "area": _window_area(rect),
                }
            )
        except Exception:
            return

    win32gui.EnumChildWindows(hwnd, callback, None)
    return rows


def find_render_targets(hwnd: int) -> list[int]:
    targets: list[tuple[int, int]] = []
    for row in list_child_windows(hwnd):
        if not row["visible"] or row["area"] <= 10_000:
            continue
        class_name = row["class_name"]
        if class_name in {"Chrome_RenderWidgetHostHWND", "Intermediate D3D Window"}:
            targets.append((row["area"], row["hwnd"]))

    targets.append((_window_area(win32gui.GetWindowRect(hwnd)), hwnd))
    targets.sort(reverse=True)
    return [target_hwnd for _, target_hwnd in targets]


def scroll_by_uia(hwnd: int, count: int = 1) -> bool:
    win = get_uia_window(hwnd)
    candidates: list[tuple[int, Any]] = []

    for elem in win.descendants():
        try:
            info = elem.element_info
            control_type = getattr(info, "control_type", "")
            if control_type not in {"Document", "Pane", "List"}:
                continue

            rect = elem.rectangle()
            area = max(0, rect.right - rect.left) * max(0, rect.bottom - rect.top)
            if area <= 10_000:
                continue

            score = area
            if control_type == "Document":
                score += 10_000_000
            candidates.append((score, elem))
        except Exception:
            continue

    candidates.sort(key=lambda item: item[0], reverse=True)

    for _, elem in candidates:
        try:
            elem.scroll("down", "page", count=count)
            return True
        except Exception:
            continue

    return False


def scroll_by_mousewheel_message(hwnd: int, clicks: int = 5) -> bool:
    sent = False

    for target_hwnd in find_render_targets(hwnd):
        try:
            left, top, right, bottom = win32gui.GetWindowRect(target_hwnd)
            x = left + (right - left) // 2
            y = top + (bottom - top) // 2
            lparam = _pack_lparam(x, y)
            wparam = _pack_wparam(WHEEL_DELTA)

            for _ in range(clicks):
                win32gui.PostMessage(target_hwnd, WM_MOUSEWHEEL, wparam, lparam)
                time.sleep(0.03)
            sent = True
            break
        except Exception:
            continue

    return sent


def scroll_by_foreground_key(hwnd: int) -> bool:
    activate_hwnd(hwnd)

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    x = left + (right - left) // 2
    y = top + (bottom - top) // 2
    win32gui.SetCursorPos((x, y))
    time.sleep(0.2)
    send_keys("{PGDN}")
    return True


def scroll_once(hwnd: int, backend: str = "auto") -> str:
    backends = ["uia", "wheel", "foreground"] if backend == "auto" else [backend]

    for current in backends:
        if current == "uia" and scroll_by_uia(hwnd):
            return "uia"
        if current == "wheel" and scroll_by_mousewheel_message(hwnd):
            return "wheel"
        if current == "foreground" and scroll_by_foreground_key(hwnd):
            return "foreground"

    raise RuntimeError(f"所有滚动后端都失败: {backend}")


def scroll_wechat_browser(
    hwnd: int,
    max_scrolls: int,
    delay: float,
    backend: str = "auto",
    check_bottom: bool = True,
    stable_limit: int = 3,
    delay_range: tuple[float, float] | None = None,
) -> int:
    no_change_count = 0
    prev_signature = visible_page_signature(hwnd) if check_bottom else ""
    backend_hits: dict[str, int] = {}
    backend_order = ["uia", "wheel", "foreground"] if backend == "auto" else [backend]

    for i in range(1, max_scrolls + 1):
        attempted: list[str] = []
        changed = False
        current_signature = ""

        for candidate in backend_order:
            try:
                used_backend = scroll_once(hwnd, backend=candidate)
            except RuntimeError:
                continue

            attempted.append(used_backend)
            backend_hits[used_backend] = backend_hits.get(used_backend, 0) + 1
            current_delay = random.uniform(*delay_range) if delay_range else delay
            print(
                f"[SCROLL] {i}/{max_scrolls} backend={'+'.join(attempted)} "
                f"delay={current_delay:.1f}s",
                end="\r",
            )
            time.sleep(current_delay)

            if not check_bottom:
                changed = True
                break

            current_signature = visible_page_signature(hwnd)
            if not prev_signature or not current_signature:
                changed = True
                break

            if current_signature == prev_signature:
                continue

            no_change_count = 0
            changed = True
            break

        if not attempted:
            raise RuntimeError(f"所有滚动后端都失败: {backend}")

        if check_bottom:
            if changed:
                if current_signature:
                    prev_signature = current_signature
            else:
                no_change_count += 1
                if current_signature:
                    prev_signature = current_signature

            if no_change_count >= stable_limit:
                print(
                    f"\n[SCROLL] detected bottom after {i} scrolls "
                    f"(stable={stable_limit}, backends={backend_hits})"
                )
                return i

    print(f"\n[SCROLL] done {max_scrolls}, backends={backend_hits}")
    return max_scrolls


def default_excel_path() -> Path:
    from src.tools_data_process.utils_path import get_root_media_save_path

    base_dir = get_root_media_save_path("homepage_url", None)[1]
    return Path(base_dir) / "home_page_url.xlsx"


def is_done_status(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, Number):
        try:
            if math.isnan(value):
                return False
        except TypeError:
            pass
        return value != 0

    text = str(value).strip().lower()
    if not text or text in ("nan", "none"):
        return False
    # 时间戳格式也算完成（如 "2026-06-19 18:08:34"）
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            pass
    return text in {"1", "1.0", "true", "yes", "y", "done", "完成", "已完成", "已爬取"}


def load_targets(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.biz:
        return [{"name": args.name or args.biz, "biz": extract_biz(args.biz)}]
    if args.url:
        return [{"name": args.name or args.url, "biz": extract_biz(args.url)}]

    import pandas as pd

    excel = Path(args.excel) if args.excel else default_excel_path()
    df = pd.read_excel(excel)
    if args.only_unfinished and "是否已经爬取" in df.columns:
        df = df[~df["是否已经爬取"].map(is_done_status)]

    targets: list[dict[str, Any]] = []
    for row_index, row in df.iterrows():
        name = str(row.get("主页名称", "") or "").strip()
        if "__biz" in df.columns:
            biz = extract_biz(str(row.get("__biz", "") or ""))
        else:
            biz = extract_biz(str(row.get("主页链接", "") or ""))
        if biz:
            targets.append({"name": name or biz, "biz": biz, "row_index": row_index})

    return targets[: args.limit] if args.limit else targets


def run_one(target: dict[str, Any], hwnd: int | None, args: argparse.Namespace) -> None:
    browser = find_wechat_browser_window(hwnd=hwnd)
    print(
        f"[BROWSER] hwnd={browser.hwnd} pid={browser.pid} title={browser.title!r} "
        f"class={browser.class_name!r} rect={browser.rect}"
    )

    url = build_profile_url(target["biz"])
    method = navigate_wechat_browser(browser.hwnd, url, wait_seconds=args.wait)
    print(f"[NAV] method={method} name={target['name']!r}")

    if args.dump_after:
        dump_uia(browser.hwnd, Path(args.dump_after), limit=args.dump_limit)

    if not args.no_scroll:
        scroll_count = scroll_wechat_browser(
            browser.hwnd,
            max_scrolls=args.max_scrolls,
            delay=args.delay,
            backend=args.scroll_backend,
            check_bottom=not args.no_check_bottom,
            stable_limit=args.bottom_stable_count,
        )
        if not (args.biz or args.url):
            excel_path = Path(args.excel) if args.excel else default_excel_path()
            row_index = target.get("row_index")
            mark_biz_done_in_excel(
                excel_path,
                target["biz"],
                row_index=int(row_index) if row_index is not None else None,
            )
        print(f"[DONE] {target['name']} 滚动完成 scrolls={scroll_count}")


def run_probe(args: argparse.Namespace) -> None:
    wins = list_top_windows_by_process(WECHAT_BROWSER_PROCESS)
    if not wins:
        raise RuntimeError("没有找到 WeChatAppEx.exe 窗口")

    print("[PROBE] WeChatAppEx windows:")
    for win in sorted(wins, key=lambda item: item.area, reverse=True):
        print(json.dumps(asdict(win), ensure_ascii=False))

    browser = find_wechat_browser_window(hwnd=args.hwnd)
    print(f"[PROBE] selected hwnd={browser.hwnd}")
    dump_uia(browser.hwnd, Path(args.dump), limit=args.dump_limit)

    if args.biz or args.url:
        target = load_targets(args)[0]
        url = build_profile_url(target["biz"])
        method = navigate_wechat_browser(browser.hwnd, url, wait_seconds=args.wait)
        print(f"[PROBE] navigation method={method}")


def _ensure_excel_columns(df, columns: list[str]):
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    return df


def _excel_biz_series(df):
    import pandas as pd

    if "__biz" in df.columns:
        return df["__biz"].fillna("").astype(str).map(extract_biz)
    if "主页链接" in df.columns:
        return df["主页链接"].fillna("").astype(str).map(extract_biz)
    return pd.Series([""] * len(df), index=df.index)


def add_biz_to_excel(excel_path: Path, biz: str, name: str, url: str) -> tuple[bool, int]:
    """添加公众号到 Excel，返回 (是否新增, DataFrame 行索引)。"""
    import pandas as pd

    biz = normalize_biz(biz)

    lock = FileLock(str(excel_path) + ".lock")
    with lock:
        if excel_path.exists():
            df = pd.read_excel(excel_path)
        else:
            df = pd.DataFrame(columns=["主页名称", "__biz", "主页链接", "是否已经爬取"])

        df = _ensure_excel_columns(df, ["主页名称", "__biz", "主页链接", "是否已经爬取"])
        existing_biz = _excel_biz_series(df)
        matched = df.index[existing_biz == biz].tolist()
        if matched:
            row_index = matched[0]
            print(f"[EXCEL] __biz {biz} 已存在，跳过新增 row={row_index + 2}")
            updated = False
            if name and not str(df.at[row_index, "主页名称"] or "").strip():
                df.at[row_index, "主页名称"] = name
                updated = True
            if not str(df.at[row_index, "__biz"] or "").strip():
                df.at[row_index, "__biz"] = biz
                updated = True
            if not str(df.at[row_index, "主页链接"] or "").strip():
                df.at[row_index, "主页链接"] = url
                updated = True
            if updated:
                excel_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_excel(excel_path, index=False)
                print(f"[EXCEL] 已补齐已有行 row={row_index + 2}")
            return False, row_index

        new_row = {
            "主页名称": name,
            "__biz": biz,
            "主页链接": url,
            "是否已经爬取": "",
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(excel_path, index=False)
        row_index = len(df) - 1

    print(f"[EXCEL] 已添加:")
    print(f"  主页名称: {name}")
    print(f"  __biz: {biz}")
    print(f"  主页链接: {url}")
    print(f"  Excel行号: {row_index + 2}")
    print(f"  现有数据: {len(df)} 行")
    return True, row_index


def mark_biz_done_in_excel(excel_path: Path, biz: str, row_index: int | None = None) -> None:
    """按 DataFrame 行索引或 __biz 标记已爬取。"""
    import pandas as pd

    if not excel_path.exists():
        print(f"[EXCEL-WARN] 文件不存在，无法标记完成: {excel_path}")
        return

    lock = FileLock(str(excel_path) + ".lock")
    with lock:
        df = pd.read_excel(excel_path)
        df = _ensure_excel_columns(df, ["主页名称", "__biz", "主页链接", "是否已经爬取"])
        target_index = row_index
        if target_index is None or target_index not in df.index:
            existing_biz = _excel_biz_series(df)
            matched = df.index[existing_biz == normalize_biz(biz)].tolist()
            target_index = matched[0] if matched else None

        if target_index is None:
            print(f"[EXCEL-WARN] 没找到 __biz={biz}，无法标记完成")
            return

        df.at[target_index, "是否已经爬取"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(excel_path, index=False)
    print(f"[EXCEL] 已标记完成 row={target_index + 2} __biz={normalize_biz(biz)}")


def extract_name_from_page(hwnd: int) -> str:
    """从页面 UIA 提取公众号名称（过滤 + 打分）。"""
    rows = snapshot_uia(hwnd, limit=50)
    win_rect = win32gui.GetWindowRect(hwnd)
    win_top = win_rect[1]
    win_height = max(1, win_rect[3] - win_rect[1])

    ignored = {
        "微信", "更多", "关闭", "最大化", "最小化", "恢复",
        "返回", "前进", "刷新",
        "首页", "发现", "视频号", "通讯录", "消息", "搜一搜", "看一看",
        "公众号", "服务", "菜单", "关注", "已关注", "发消息",
    }

    _URL_RE = re.compile(r"https?://|\.com|\.cn|\.net", re.IGNORECASE)
    _NUM_RE = re.compile(r"^\d+$")
    _BUTTON_HINTS = {"下载", "安装", "打开", "查看", "阅读原文", "置顶", "投诉", "复制链接"}

    scored: list[tuple[float, str, str]] = []  # (score, text, control_type)
    for row in rows:
        text = " ".join(str(row.get("text", "") or "").split())
        if not text or len(text) < 2 or len(text) >= 30:
            continue
        if text in ignored:
            continue

        control_type = row.get("control_type", "")

        # ---- 过滤 ----
        if _NUM_RE.match(text):
            continue
        if _URL_RE.search(text):
            continue
        if text in _BUTTON_HINTS or text.startswith("点按"):
            continue

        # ---- 打分 ----
        score = 0.0

        # 控制类型: Text 优于 Document
        if control_type == "Text":
            score += 5
        elif control_type == "Document":
            score += 2
        else:
            score += 1

        # 靠近窗口上方 = 更像标题区域
        rect = row.get("rect") or [0, 0, 0, 0]
        elem_top = rect[1]
        relative_y = (elem_top - win_top) / win_height  # 0=顶部, 1=底部
        score += max(0, 10 - relative_y * 10)  # 顶部 10 分, 底部 0 分

        # 长度偏好: 4-15 字的名称最常见
        if 4 <= len(text) <= 15:
            score += 3
        elif 2 <= len(text) <= 3:
            score += 1

        scored.append((score, text, control_type))

    if not scored:
        return ""

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_text, best_type = scored[0]
    top_n = [(f"{s:.1f}", t, c) for s, t, c in scored[:8]]
    print(f"[NAME-SCORED] best={best_text!r} score={best_score:.1f} type={best_type} top={top_n}")

    return best_text


def run_add_and_run(args: argparse.Namespace) -> None:
    """添加新公众号到 Excel 并执行滚动"""
    url = args.add_and_run

    # 提取 __biz
    biz = extract_biz(url)
    if not biz:
        raise ValueError(f"无法从 URL 提取 __biz: {url}")

    print(f"[ADD] URL: {url}")
    print(f"[ADD] __biz: {biz}")

    # 构建主页链接
    profile_url = build_profile_url(biz)

    # 找到微信窗口
    browser = find_wechat_browser_window(hwnd=args.hwnd)
    print(f"[BROWSER] hwnd={browser.hwnd}")

    # 导航到主页
    method = navigate_wechat_browser(browser.hwnd, profile_url, wait_seconds=args.wait)
    print(f"[NAV] method={method}")

    # 提取公众号名称
    name = args.name
    if not name:
        name = extract_name_from_page(browser.hwnd)
        if not name:
            name = biz
    print(f"[NAME] {name}")

    # 添加到 Excel
    excel_path = Path(args.excel) if args.excel else default_excel_path()
    _, row_index = add_biz_to_excel(excel_path, biz, name, profile_url)

    # 滚动
    if not args.no_scroll:
        print(f"[SCROLL] 开始滚动...")
        scroll_count = scroll_wechat_browser(
            browser.hwnd,
            max_scrolls=args.max_scrolls,
            delay=args.delay,
            backend=args.scroll_backend,
            check_bottom=not args.no_check_bottom,
            stable_limit=args.bottom_stable_count,
        )
        mark_biz_done_in_excel(excel_path, biz, row_index=row_index)
        print(f"[DONE] {name} 滚动完成 scrolls={scroll_count}")
    else:
        print("[EXCEL] --no-scroll 已跳过滚动，不标记完成")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control an already opened WeChat built-in browser window."
    )
    parser.add_argument("--probe", action="store_true", help="list WeChatAppEx windows and dump UIA")
    parser.add_argument("--biz", help="target __biz value")
    parser.add_argument("--url", help="target article/profile URL containing __biz")
    parser.add_argument("--name", help="display name for logs")
    parser.add_argument("--excel", help="home_page_url.xlsx path")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only-unfinished", action="store_true")
    parser.add_argument("--hwnd", type=lambda value: int(value, 0), help="specific WeChatAppEx hwnd")
    parser.add_argument("--wait", type=float, default=5.0, help="seconds to wait after navigation")
    parser.add_argument("--max-scrolls", type=int, default=120)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument(
        "--scroll-backend",
        choices=["auto", "uia", "wheel", "foreground"],
        default="foreground",
        help="scroll backend. Default foreground is required for reliable WeChat scrolling.",
    )
    parser.add_argument("--no-check-bottom", action="store_true", help="disable UIA visible-text bottom detection")
    parser.add_argument("--bottom-stable-count", type=int, default=3, help="unchanged signatures before stopping")
    parser.add_argument("--no-scroll", action="store_true")
    parser.add_argument("--dump", default=str(Path("tmp") / "wechat_appex_uia.json"))
    parser.add_argument("--dump-after", default="")
    parser.add_argument("--dump-limit", type=int, default=300)
    parser.add_argument("--add-and-run", help="add new公众号 URL to Excel and run滚动")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.probe:
        run_probe(args)
        return

    if args.add_and_run:
        run_add_and_run(args)
        return

    targets = load_targets(args)
    if not targets:
        raise RuntimeError("没有可处理的目标。请传 --biz/--url，或确认 Excel 里有 __biz/主页链接。")

    hwnd = args.hwnd
    for index, target in enumerate(targets, start=1):
        print(f"[TARGET] {index}/{len(targets)} name={target['name']!r} biz={target['biz']!r}")
        run_one(target, hwnd=hwnd, args=args)


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parents[2])
    main()
