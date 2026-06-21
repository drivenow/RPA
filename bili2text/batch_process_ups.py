# -*- coding: utf-8 -*-
"""
批量处理 bili_up_queue.xlsx 中的 UP 视频转文字。

功能:
  - 去重: 同一个 bvid 跨 sheet 不重复处理
  - 断点续跑: 通过 state 文件记录已处理 bvid，中断后重跑自动跳过
  - 跳过付费视频: 通过 Bilibili API 检测 is_upower_exclusive

用法:
  python batch_process_ups.py                        # 默认: 处理所有未转文字 UP
  python batch_process_ups.py --include-done         # 包含已转文字的 UP
  python batch_process_ups.py --skip-sync            # 跳过 MySQL 同步
  python batch_process_ups.py --mids 403375255       # 只处理指定 mid
  python batch_process_ups.py --dry-run              # 只打印不执行
  python batch_process_ups.py --reset-state          # 清除断点状态，重新开始
  python batch_process_ups.py --no-skip-paid         # 不跳过付费视频
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools_data_process.engine_mysql import MysqlEngine
from src.tools_data_process.engine_excel import ExcelEngine
from src.tools_data_process.utils_path import get_media_url_excel_path, get_root_media_save_path
from main import BiliSpeechPipeline, VideoJob, sanitize_title

# ---------------------------------------------------------------------------
# State file for checkpoint/resume
# ---------------------------------------------------------------------------

DEFAULT_STATE_FILE = Path(__file__).resolve().parent / "batch_state.json"
CRAWL_DONE_COL = "是否已经爬取"
TRANSCRIBE_DONE_COL = "是否已经转文字"
MEMBER_COL = "是否订阅会员"
QUEUE_COLUMNS = ["UP名称", "mid", "空间链接", CRAWL_DONE_COL, TRANSCRIBE_DONE_COL, MEMBER_COL]
CHECKPOINT_SKIP_STATUSES = {"success", "skipped", "paid"}


def load_state(state_file: Path) -> dict:
    """加载断点状态。格式: {"processed_bvids": {...}, "paid_bvids": {...}}"""
    state = {"processed_bvids": {}, "paid_bvids": {}}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                state.update(loaded)
        except Exception as exc:
            print(f"[STATE-WARN] 读取状态文件失败，将使用空状态: {state_file} error={exc}")
    if not isinstance(state.get("processed_bvids"), dict):
        print(f"[STATE-WARN] processed_bvids 格式异常，已重置: {state_file}")
        state["processed_bvids"] = {}
    if not isinstance(state.get("paid_bvids"), dict):
        print(f"[STATE-WARN] paid_bvids 格式异常，已重置: {state_file}")
        state["paid_bvids"] = {}
    return state


def save_state(state_file: Path, state: dict) -> None:
    """保存断点状态。"""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def mark_processed(state_file: Path, state: dict, bvid: str, status: str, sheet: str) -> None:
    """标记一个 bvid 已处理。"""
    if not bvid:
        return
    state["processed_bvids"][bvid] = {
        "status": status,
        "sheet": sheet,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_state(state_file, state)


def should_skip_checkpoint(entry) -> tuple[bool, str]:
    """Only completed checkpoint statuses should suppress future retries."""
    if isinstance(entry, dict):
        status = str(entry.get("status") or "").strip().lower()
    else:
        status = str(entry or "").strip().lower()
    return status in CHECKPOINT_SKIP_STATUSES, status or "unknown"


# ---------------------------------------------------------------------------
# Bvid extraction & paid video check
# ---------------------------------------------------------------------------

_BVID_RE = re.compile(r"BV[\w]+")


def extract_bvid(url: str) -> str | None:
    """从 URL 提取 bvid。"""
    m = _BVID_RE.search(str(url))
    return m.group(0) if m else None


def _load_bili_cookies() -> str:
    """从 bili_cookies.txt 加载 Bilibili cookies，返回 Cookie header 值。"""
    cookie_file = PROJECT_ROOT / "bili_cookies.txt"
    if not cookie_file.exists():
        return ""
    cookies = {}
    try:
        with open(cookie_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
    except Exception as exc:
        print(f"[COOKIE-WARN] 读取 {cookie_file} 失败: {exc}")
    return "; ".join(f"{k}={v}" for k, v in cookies.items()) if cookies else ""


_BILI_COOKIES: str | None = None


def _get_bili_cookies() -> str:
    global _BILI_COOKIES
    if _BILI_COOKIES is None:
        _BILI_COOKIES = _load_bili_cookies()
    return _BILI_COOKIES


def check_paid_video(bvid: str) -> bool:
    """检查视频是否为付费/充电视频。返回 True 表示是付费视频。"""
    try:
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        headers = {"User-Agent": "Mozilla/5.0"}
        cookie = _get_bili_cookies()
        if cookie:
            headers["Cookie"] = cookie
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("code") == 0:
            info = data["data"]
            return bool(info.get("is_upower_exclusive") or info.get("is_chargeable_season"))
    except Exception as exc:
        print(f"[PAID-CHECK-WARN] bvid={bvid} error={type(exc).__name__}: {exc}")
    return False


# ---------------------------------------------------------------------------
# Sheet matching & job building
# ---------------------------------------------------------------------------

def build_jobs_from_sheet(main_file: str, sheet_name: str) -> list[VideoJob]:
    """从 bili_summary.xlsx 读取 sheet，创建 VideoJob 列表。"""
    try:
        df = pd.read_excel(main_file, sheet_name=sheet_name)
    except Exception as exc:
        print(f"[ERROR] 读取 sheet={sheet_name} 失败: {exc}")
        return []

    jobs: list[VideoJob] = []
    for _, row in df.iterrows():
        raw_title = row.get("标题")
        title_value = "" if pd.isna(raw_title) else str(raw_title)
        url = row.get("url")
        if not url or pd.isna(url):
            continue
        url_str = str(url).strip()
        if not url_str:
            continue
        video_type = "bili" if url_str.startswith("https://www.bilibili.com/video/") else "youtube"
        title = sanitize_title(title_value or "", fallback=url_str)
        jobs.append(VideoJob(
            media_type="bili",
            url=url_str,
            title=title,
            sheet_name=sheet_name,
            video_type=video_type,
        ))
    return jobs


def find_sheets_for_ups(all_sheets: list[str], up_mids: set[str], up_names: set[str]) -> list[str]:
    """从 sheet 列表中筛选属于目标 UP 的 sheet。"""
    matched = []
    for sheet in all_sheets:
        s = str(sheet).strip()
        if s.isdigit():
            if s in up_mids:
                matched.append(s)
            continue
        for name in up_names:
            if name and s.startswith(name):
                matched.append(s)
                break
    return matched


def load_up_queue(excel_path: Path) -> pd.DataFrame:
    df = pd.read_excel(excel_path, dtype={"mid": str})
    for col in QUEUE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def is_done(value) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text or text in ("nan", "none"):
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            from datetime import datetime
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            pass
    return text in {"1", "1.0", "true", "yes", "y", "done", "完成", "已完成", "已爬取"}


def is_member(value) -> bool:
    """判断 UP 是否为订阅会员（允许爬取付费视频）。"""
    if value is None:
        return False
    text = str(value).strip().lower()
    if not text or text in ("nan", "none", "0", "false", "no", ""):
        return False
    return True


def sync_mysql_to_excel():
    print("[SYNC] 开始同步 MySQL → Excel ...")
    mysql_engine = MysqlEngine()
    mysql_engine.sql_to_excel(media_type="bili")
    print("[SYNC] 同步完成")


def mark_transcribed_in_queue(excel_path: Path, mids: set[str]) -> None:
    """转文字批次无失败时，回写 UP 队列的转文字完成时间。"""
    target_mids = {str(mid).strip() for mid in mids if str(mid).strip()}
    if not target_mids:
        return

    try:
        df = load_up_queue(excel_path)
    except Exception as exc:
        print(f"[QUEUE-WARN] 无法读取队列，跳过转文字完成标记: {excel_path} error={exc}")
        return

    matched = df.index[df["mid"].astype(str).str.strip().isin(target_mids)].tolist()
    if not matched:
        print(f"[QUEUE-WARN] 无法标记转文字完成，队列中没有匹配 mid={sorted(target_mids)}")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for index in matched:
        df.at[index, TRANSCRIBE_DONE_COL] = timestamp

    excel_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(excel_path, index=False)
    print(f"[QUEUE] 已标记转文字完成 rows={len(matched)} mids={sorted(target_mids)} at={timestamp}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="批量处理 B站 UP 视频转文字")
    parser.add_argument("--queue-excel", type=Path,
                        default=Path(r"X:\RAG_192.168.1.2\rpa_data\batch_urls\bili_up_queue.xlsx"))
    parser.add_argument("--mids", nargs="*", help="只处理指定 mid")
    parser.add_argument("--sync-only", action="store_true")
    parser.add_argument("--include-done", action="store_true", help="包含已转文字完成的 UP")
    parser.add_argument("--skip-sync", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset-state", action="store_true", help="清除断点状态")
    parser.add_argument("--no-skip-paid", action="store_true", help="不跳过付费视频")
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    args = parser.parse_args()

    # 1. 加载/重置断点状态
    if args.reset_state and args.state_file.exists():
        args.state_file.unlink()
        print(f"[STATE] 已清除断点状态: {args.state_file}")

    state = load_state(args.state_file)
    processed = state.get("processed_bvids", {})
    paid_cache = state.get("paid_bvids", {})
    print(f"[STATE] 已处理: {len(processed)} 个 bvid, 已知付费: {len(paid_cache)} 个")

    # 2. 加载 UP 队列
    queue_df = load_up_queue(args.queue_excel)
    print(f"[QUEUE] 共 {len(queue_df)} 个 UP")

    if args.mids:
        queue_df = queue_df[queue_df["mid"].astype(str).isin(set(args.mids))]
        print(f"[QUEUE] 按 --mids 过滤后 {len(queue_df)} 个")
    elif not args.include_done:
        queue_df = queue_df[~queue_df[TRANSCRIBE_DONE_COL].map(is_done)]
        print(f"[QUEUE] 过滤已转文字完成，剩余 {len(queue_df)} 个")

    if queue_df.empty:
        print("[EXIT] 没有需要处理的 UP")
        return

    up_mids = set(queue_df["mid"].astype(str).str.strip())
    up_names = set(queue_df["UP名称"].astype(str).str.strip())
    up_names.discard("")
    up_names.discard("nan")

    # 订阅会员的 UP mid 集合（允许爬取付费视频）
    member_mids: set[str] = set()
    for _, row in queue_df.iterrows():
        if is_member(row.get(MEMBER_COL)):
            mid = str(row.get("mid", "") or "").strip()
            if mid:
                member_mids.add(mid)
    if member_mids:
        print(f"[MEMBER] 订阅会员 UP: {sorted(member_mids)}")

    # 3. 同步 MySQL → Excel
    if not args.skip_sync:
        sync_mysql_to_excel()
    if args.sync_only:
        print("[EXIT] --sync-only 模式")
        return

    # 4. 获取 sheet 列表
    _, main_file = get_media_url_excel_path(media_type="bili")
    main_file = Path(main_file)
    if not main_file.exists():
        print(f"[ERROR] bili_summary.xlsx 不存在: {main_file}")
        return

    excel_engine = ExcelEngine()
    all_sheets = excel_engine.get_excel_sheet_names(str(main_file))
    matched_sheets = find_sheets_for_ups(all_sheets, up_mids, up_names)
    print(f"[MATCH] {len(matched_sheets)} 个 sheet")

    if not matched_sheets:
        print("[EXIT] 没有匹配到任何 sheet")
        return

    if args.dry_run:
        print("[DRY-RUN] 将处理以下 sheet:")
        for s in matched_sheets:
            print(f"  - {s}")
        return

    # 5. 逐 sheet 处理
    pipeline = BiliSpeechPipeline()
    global_seen_bvids: set[str] = set()  # 跨 sheet 去重
    stats = {"success": 0, "skipped_dup": 0, "skipped_state": 0, "skipped_paid": 0,
             "skipped_existing": 0, "failed": 0, "total": 0}
    failed_details: list[tuple[str, str, str]] = []

    for i, sheet_name in enumerate(matched_sheets, 1):
        print(f"\n{'='*60}")
        print(f"[SHEET] {i}/{len(matched_sheets)} {sheet_name}")
        print(f"{'='*60}")

        try:
            jobs = build_jobs_from_sheet(str(main_file), sheet_name)
        except Exception as exc:
            print(f"[ERROR] 读取 sheet 失败: {exc}")
            failed_details.append((sheet_name, "-", f"读取失败: {exc}"))
            continue

        if not jobs:
            print(f"[SKIP] sheet={sheet_name} 无视频")
            continue

        print(f"[JOBS] sheet={sheet_name} 共 {len(jobs)} 个视频")
        sheet_dup = 0
        sheet_state = 0
        sheet_paid = 0

        # 判断当前 sheet 对应的 UP 是否为订阅会员
        sheet_mid = sheet_name.strip() if sheet_name.strip().isdigit() else ""
        sheet_is_member = sheet_mid in member_mids
        if sheet_is_member:
            print(f"  [MEMBER] mid={sheet_mid} 订阅会员，不跳过付费视频")

        for j, job in enumerate(jobs, 1):
            bvid = extract_bvid(job.url)
            stats["total"] += 1

            # 5a. 跨 sheet 去重
            if bvid and bvid in global_seen_bvids:
                sheet_dup += 1
                stats["skipped_dup"] += 1
                continue
            if bvid:
                global_seen_bvids.add(bvid)

            # 5b. 断点续跳: 只跳过真正完成的 bvid，失败/异常状态允许重试。
            if bvid and bvid in processed:
                skip_checkpoint, checkpoint_status = should_skip_checkpoint(processed[bvid])
                if skip_checkpoint:
                    sheet_state += 1
                    stats["skipped_state"] += 1
                    continue
                print(f"  [RETRY] bvid={bvid} previous_status={checkpoint_status}")

            # 5c. 跳过付费视频（订阅会员的 UP 不跳过）
            if bvid and not args.no_skip_paid and not sheet_is_member:
                if bvid in paid_cache:
                    is_paid = paid_cache[bvid]
                else:
                    is_paid = check_paid_video(bvid)
                    paid_cache[bvid] = is_paid
                    state["paid_bvids"] = paid_cache
                    save_state(args.state_file, state)

                if is_paid:
                    sheet_paid += 1
                    stats["skipped_paid"] += 1
                    mark_processed(args.state_file, state, bvid, "paid", sheet_name)
                    continue

            # 5d. 处理视频
            print(f"\n  [{j}/{len(jobs)}] {job.title}")
            print(f"  URL: {job.url}")
            try:
                result = pipeline.process_job(job, skip_existing=True)
                if result.succeeded:
                    stats["success"] += 1
                    mark_processed(args.state_file, state, bvid, "success", sheet_name)
                    print(f"  [OK] ({result.elapsed:.1f}s) {result.message or ''}")
                elif result.skipped:
                    stats["skipped_existing"] += 1
                    mark_processed(args.state_file, state, bvid, "skipped", sheet_name)
                    print(f"  [SKIP] 已存在")
                else:
                    stats["failed"] += 1
                    mark_processed(args.state_file, state, bvid, "failed", sheet_name)
                    failed_details.append((sheet_name, job.title, result.message or "unknown"))
                    print(f"  [FAIL] {result.message}")
            except Exception as exc:
                stats["failed"] += 1
                mark_processed(args.state_file, state, bvid, "error", sheet_name)
                failed_details.append((sheet_name, job.title, str(exc)))
                print(f"  [EXCEPTION] {exc}")
                traceback.print_exc()

        if sheet_dup or sheet_state or sheet_paid:
            print(f"  [FILTER] dup={sheet_dup} checkpoint={sheet_state} paid={sheet_paid}")

    # 6. 汇总
    print(f"\n{'='*60}")
    print(f"[SUMMARY]")
    print(f"  sheets: {len(matched_sheets)}")
    print(f"  total videos: {stats['total']}")
    print(f"  success: {stats['success']}")
    print(f"  skipped (already in transcript): {stats['skipped_existing']}")
    print(f"  skipped (duplicate bvid): {stats['skipped_dup']}")
    print(f"  skipped (checkpoint/resume): {stats['skipped_state']}")
    print(f"  skipped (paid video): {stats['skipped_paid']}")
    print(f"  failed: {stats['failed']}")
    print(f"  state file: {args.state_file}")

    if failed_details:
        print(f"\n[FAILED] ({len(failed_details)} 个)")
        for sheet, title, err in failed_details[:20]:
            print(f"  sheet={sheet} title={title[:40]} error={err[:60]}")
        if len(failed_details) > 20:
            print(f"  ... 还有 {len(failed_details) - 20} 个")
        print("[QUEUE] 存在失败任务，不标记转文字完成，便于下次重跑")
    elif stats["total"] > 0:
        mark_transcribed_in_queue(args.queue_excel, up_mids)


if __name__ == "__main__":
    main()
