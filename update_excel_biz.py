# -*- coding: utf-8 -*-
"""
往微信公众号 Excel 队列中添加一条 biz 记录。

用法:
  python update_excel_biz.py --biz MzYzMTg1MzEwMg== --name "老张的AI研究院"
  python update_excel_biz.py --url "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=xxx==#wechat_redirect"
  python update_excel_biz.py --biz MzYzMTg1MzEwMg== --excel "X:/path/to/home_page_url.xlsx"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.tools_browser.wechat_biz_browser_runner import (
    add_biz_to_excel,
    build_profile_url,
    default_excel_path,
    extract_biz,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="添加微信公众号到 Excel 队列")
    parser.add_argument("--biz", help="__biz 值（可带或不带 == 后缀）")
    parser.add_argument("--url", help="包含 __biz 的完整 URL")
    parser.add_argument("--name", default="", help="公众号名称")
    parser.add_argument("--excel", type=Path, help="Excel 文件路径（默认使用 default_excel_path）")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.biz and not args.url:
        parser.error("必须指定 --biz 或 --url")

    biz = extract_biz(args.biz or args.url)
    if not biz:
        raise ValueError(f"无法提取 __biz: {args.biz or args.url}")

    profile_url = build_profile_url(biz)
    excel_path = args.excel or default_excel_path()

    is_new, row_index = add_biz_to_excel(excel_path, biz, args.name, profile_url)
    if is_new:
        print(f"已添加: __biz={biz} name={args.name!r} row={row_index + 2}")
    else:
        print(f"已存在: __biz={biz} row={row_index + 2}")


if __name__ == "__main__":
    main()
