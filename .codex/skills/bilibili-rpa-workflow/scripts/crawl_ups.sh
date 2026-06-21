#!/usr/bin/env bash
# 爬取 bili_up_queue.xlsx 中所有未完成 UP 的空间数据
# 用法: bash crawl_ups.sh [--attach] [--keep-open] [--no-write-db]
set -euo pipefail

ROOT="X:/RPA"
PY="E:/anaconda/envs/wechatapp/python.exe"
SCRIPT="$ROOT/src/tools_browser/bilibili_browser_roll_runner.py"

ARGS=("$SCRIPT" "--only-unfinished")
for arg in "$@"; do
    case "$arg" in
        --attach)     ARGS+=("--attach") ;;
        --keep-open)  ARGS+=("--keep-open") ;;
        --no-write-db) ARGS+=("--no-write-db") ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

echo "[CRAWL] $PY ${ARGS[*]}"
"$PY" "${ARGS[@]}"
