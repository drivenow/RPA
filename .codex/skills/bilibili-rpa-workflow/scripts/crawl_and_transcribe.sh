#!/usr/bin/env bash
# One-shot Bilibili flow: crawl UP spaces, then transcribe videos.
# Usage: bash crawl_and_transcribe.sh [--attach] [--keep-open] [--crawl-only] [--text-only] [--skip-sync] [--dry-run] [--include-done] [--mids 403375255 15741969]
# Note: --mids is supported only with --text-only; crawling by mid needs runner queue filtering.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

CRAWL_ARGS=()
TEXT_ARGS=()
MODE="both"
MIDS_MODE=0
HAS_MIDS=0

for arg in "$@"; do
    if [ $MIDS_MODE -eq 1 ]; then
        case "$arg" in
            --*) MIDS_MODE=0 ;;
            *) TEXT_ARGS+=("$arg"); continue ;;
        esac
    fi
    case "$arg" in
        --attach)       CRAWL_ARGS+=("--attach") ;;
        --keep-open)    CRAWL_ARGS+=("--keep-open") ;;
        --crawl-only)   MODE="crawl" ;;
        --text-only)    MODE="text" ;;
        --skip-sync)    TEXT_ARGS+=("--skip-sync") ;;
        --dry-run)      TEXT_ARGS+=("--dry-run") ;;
        --include-done) TEXT_ARGS+=("--include-done") ;;
        --mids)         TEXT_ARGS+=("--mids"); MIDS_MODE=1; HAS_MIDS=1 ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

if [ $HAS_MIDS -eq 1 ] && [ "$MODE" != "text" ]; then
    echo "[ERROR] --mids is currently supported only with --text-only. Use transcribe_ups.sh --mids ... or add crawl queue filtering first."
    exit 2
fi

if [ "$MODE" = "text" ]; then
    bash "$SCRIPT_DIR/transcribe_ups.sh" "${TEXT_ARGS[@]}"
    exit $?
fi

bash "$SCRIPT_DIR/crawl_ups.sh" "${CRAWL_ARGS[@]}"
if [ $? -ne 0 ]; then
    echo "[EXIT] crawl failed"
    exit 1
fi

if [ "$MODE" = "crawl" ]; then
    echo "[EXIT] crawl-only mode"
    exit 0
fi

bash "$SCRIPT_DIR/transcribe_ups.sh" "${TEXT_ARGS[@]}"
