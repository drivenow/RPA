#!/usr/bin/env bash
# Batch transcribe Bilibili videos from the queue/MySQL export.
# Usage: bash transcribe_ups.sh [--skip-sync] [--dry-run] [--include-done] [--mids 403375255 15741969]
set -euo pipefail

ROOT="X:/RPA"
PY="E:/anaconda/envs/wechatapp/python.exe"
SCRIPT="$ROOT/bili2text/batch_process_ups.py"

ARGS=("$SCRIPT")
MIDS_MODE=0
for arg in "$@"; do
    if [ $MIDS_MODE -eq 1 ]; then
        ARGS+=("$arg")
        continue
    fi
    case "$arg" in
        --skip-sync)    ARGS+=("--skip-sync") ;;
        --dry-run)      ARGS+=("--dry-run") ;;
        --include-done) ARGS+=("--include-done") ;;
        --mids)         ARGS+=("--mids"); MIDS_MODE=1 ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

echo "[TRANSCRIBE] $PY ${ARGS[*]}"
"$PY" "${ARGS[@]}"
