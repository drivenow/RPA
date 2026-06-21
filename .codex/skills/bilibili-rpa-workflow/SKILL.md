---
name: bilibili-rpa-workflow
description: Run and troubleshoot the X:\RPA Bilibili browser RPA workflow. Use when the user asks to crawl Bilibili UP spaces, collections/seasons/lists/search pages, capture Bilibili JSON responses through Chrome, write mapped records using Guid2DB2Config, compare database increments, or run the downstream transcript/text process at X:\RPA\bili2text\main.py.
---

# Bilibili RPA Workflow

## Core Facts

- Work from `X:\RPA`.
- Use `E:\anaconda\envs\wechatapp\python.exe`; this environment has Selenium and PyMySQL.
- Main browser automation script: `src\tools_browser\bilibili_browser_roll_runner.py`.
- Field mappings live in `C:\ProgramData\CXT.RPA\CXT.RPA.db`, table `Guid2DB2Config`.
- Relevant mappings include:
  - `gk_id=124`: `seasons_archives_list` -> `b站搜索结果` and `b站合集meta`
  - `gk_id=127`: `acc/info` -> `b站个人主页`
  - `gk_id=141`: `arc/search` -> `b站搜索结果`
- MySQL defaults are already in the script: `192.168.1.2:3306`, user `admin`, database `mydatabase`.
- Chrome capture uses in-page `fetch/XMLHttpRequest` hooks, not HTTPS MITM.

## Full Workflow

1. Ask the user to close the external packet-capture program if the goal is to isolate script-written DB increments.
2. Record the before count for the target `mid`.
3. Run `bilibili_browser_roll_runner.py` with `--write-db --update-existing`.
4. Preserve `--mapped-dump` for audit/debugging.
5. Record the after count and report net added distinct `bvid`.
6. Run downstream processing (bili2text):
   - Sync MySQL → Excel: `mysql_engine.sql_to_excel("bili")`
   - Get sheet names for target UPs (may be mid, collection name, or author name)
   - For each sheet: `pipeline.build_jobs_from_excel("bili", sheet_name)` → `pipeline.process_job(job)`
   - See "Downstream: Video-to-Text" section below for details

## Standard Collection Command

Use this for UP-space collection/seasons crawling and DB writing:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\bilibili_browser_roll_runner.py "https://space.bilibili.com/403375255" --pages 50 --scrolls-per-page 1 --delay "0.3-0.8" --attach --keep-open --mapped-dump tmp\bili_403375255_all_collections.jsonl --write-db --update-existing
```

If Chrome is not already running with remote debugging, omit `--attach` and let the script launch Chrome.

For a fast smoke test, keep DB writes off and limit collection traversal:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\bilibili_browser_roll_runner.py "https://space.bilibili.com/403375255" --pages 1 --scrolls-per-page 1 --max-collections 1 --delay "0.3-0.5" --mapped-dump tmp\bili_smoke_403375255_mapped.jsonl
```

## Excel Queue (UP 主页管理)

Like the WeChat workflow, Bilibili now has an Excel queue at `X:\RAG_192.168.1.2\rpa_data\batch_urls\bili_up_queue.xlsx` with columns: `UP名称`, `mid`, `空间链接`, `是否已经爬取`.

Pre-populated from `bili_summary.xlsx` with 51 UPs.

### Add single UP and crawl immediately:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\bilibili_browser_roll_runner.py --add-and-run "https://space.bilibili.com/403375255" --attach --keep-open
```

### Batch crawl all unfinished UPs:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\bilibili_browser_roll_runner.py --only-unfinished --attach --keep-open
```

### Custom Excel path:

```powershell
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\bilibili_browser_roll_runner.py --only-unfinished --excel "path\to\custom.xlsx" --attach --keep-open
```

Queue mode defaults to `--write-db --update-existing`. Use `--no-write-db` to disable DB writing.

Each UP's mapped dump is saved to `tmp\bili_{mid}_mapped.jsonl`; the file is cleared at the start of that UP's run so it reflects the current run only. `--no-write-db` disables DB writes but still captures per-UP mapped dumps.

Do not pass positional URLs or `--mapped-dump` in queue mode; direct URL mode is the place to use a custom `--mapped-dump` file.

Running the script without `--add-and-run`, `--only-unfinished`, or direct URLs exits with a prompt instead of crawling hard-coded test UPs.

Default logs are concise. Use `--verbose` only when debugging page selectors, collection card detection, or "more" button candidates.

Dynamic pages use adaptive scrolling: the script stops after two consecutive scrolls with no new visible links and no new mapped rows, instead of always scrolling the full `--pages` count.

## Downstream: Video-to-Text (bili2text)

After crawling UP spaces and writing to MySQL, use `bili2text\batch_process_ups.py` to batch-download videos and transcribe them to text.

### Quick Start (scripts)

Scripts live in `.codex\skills\bilibili-rpa-workflow\scripts\`. They are thin wrappers calling the actual Python scripts.

```powershell
cd X:\RPA\.codex\skills\bilibili-rpa-workflow\scripts

# 一键：爬取 + 转文字
.\crawl_and_transcribe.ps1 -Attach -KeepOpen

# 只爬取
.\crawl_ups.ps1 -Attach -KeepOpen

# 只转文字（跳过 MySQL 同步）
.\transcribe_ups.ps1 -SkipSync

# 只转指定 UP
.\transcribe_ups.ps1 -Mids "403375255","15741969"

# 预览匹配的 sheet
.\transcribe_ups.ps1 -DryRun
```

Underlying Python scripts (called by the wrappers above):
- `src\tools_browser\bilibili_browser_roll_runner.py` — crawl UP spaces
- `bili2text\batch_process_ups.py` — batch transcribe (reads queue Excel, syncs MySQL, calls `bili2text\main.py`)

### How it works

For more details on the underlying API:

### How sheet_name works

`build_jobs_from_excel(media_type, sheet_name)` reads video URLs from `bili_summary.xlsx`. The `sheet_name` is **not always the mid** — it depends on how the video was discovered. Priority:

1. **keyword** (搜索词) → sheet name is the keyword
2. **season_id** (合集) → sheet name is `"UP名 合集·合集名"` (e.g., `"渤海小吏 合集·安史之乱"`)
3. **作者** (author) → sheet name is the author name
4. **mid** → fallback, sheet name is the bare number (e.g., `"403375255"`)

So one UP's videos may span multiple sheets (one per collection + a mid sheet for uncategorized videos).

### Sync MySQL to Excel

```python
from src.tools_data_process.engine_mysql import MysqlEngine
mysql_engine = MysqlEngine()
mysql_engine.sql_to_excel(media_type="bili")
```

This writes/merges into `bili_summary.xlsx` (path from `get_media_url_excel_path("bili")`).

### List available sheets for a UP

```python
import pandas as pd
from src.tools_data_process.utils_path import get_media_url_excel_path
_, main_file = get_media_url_excel_path("bili")
all_sheets = pd.ExcelFile(main_file).sheet_names
# Filter by mid or UP name
up_sheets = [s for s in all_sheets if "403375255" in s or "扶光录" in s]
```

### Process one sheet

```python
from bili2text.main import BiliSpeechPipeline
pipeline = BiliSpeechPipeline()
jobs = pipeline.build_jobs_from_excel("bili", "403375255")
for job in jobs:
    result = pipeline.process_job(job, skip_existing=True)
    print(result.status, result.message)
```

### Process multiple UPs (batch)

```python
from bili2text.main import BiliSpeechPipeline
pipeline = BiliSpeechPipeline()
for sheet_name in ["403375255", "扶光录 合集·xxx", ...]:
    jobs = pipeline.build_jobs_from_excel("bili", sheet_name)
    for job in jobs:
        pipeline.process_job(job, skip_existing=True)
```

### Pipeline per video

1. Try subtitle download (fast path, no ASR needed)
2. Fallback: yt-dlp download → extract audio → split into 20-min slices → SiliconFlow ASR
3. Optional: punctuation restoration via FunASR ct-punc
4. Output: `.txt` file in the text directory

### Key paths

- Video save: `get_root_media_save_path("bili", sheet_name)` → `(audio_dir, text_dir, video_dir)`
- Transcript output: `text_dir / "{sanitized_title}.txt"`
- Skip existing: `_is_valid_transcript()` checks file exists and has >50 bytes of content beyond header

## Count Before And After

Replace `403375255` with the target mid:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe -c "import pymysql; q=chr(96); conn=pymysql.connect(host='192.168.1.2',port=3306,user='admin',password='ybsDW246401.',database='mydatabase',charset='utf8mb4',connect_timeout=5); cur=conn.cursor(); cur.execute('select count(distinct bvid), count(*), count(distinct season_id) from '+q+'b站搜索结果'+q+' where mid=%s and bvid is not null and bvid<>%s',('403375255','')); print(cur.fetchone()); cur.execute('select season_id,count(distinct bvid) from '+q+'b站搜索结果'+q+' where mid=%s and bvid is not null and bvid<>%s group by season_id order by season_id',('403375255','')); print(cur.fetchall()); conn.close()"
```

## Interpret Results

Report at least two separate counts:

- Database net increment: after `count(distinct bvid)` minus before `count(distinct bvid)`.
- Current run captured count: unique `values.bvid` in the mapped dump.

For mapped-dump analysis, filter collection videos with:

- `config_id == 124`
- `table == "b站搜索结果"`
- `values.bvid` non-empty
- `values.season_id` non-empty

Use this quick mapped-dump summary:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe -c "import json,collections; p='tmp/bili_403375255_all_collections.jsonl'; rows=[json.loads(x) for x in open(p,encoding='utf-8')]; vids=[r for r in rows if r.get('config_id')==124 and r.get('table')=='b站搜索结果' and r.get('values',{}).get('bvid') and r.get('values',{}).get('season_id')]; bvids={r['values']['bvid'] for r in vids}; by=collections.defaultdict(set); [by[str(r['values'].get('season_id'))].add(r['values']['bvid']) for r in vids]; print('collection_rows',len(vids),'unique_bvid',len(bvids)); print(sorted((k,len(v)) for k,v in by.items()))"
```

## Validation Signals

- Logs should show `[GUID-CONFIG] loaded bilibili mappings=...`.
- Logs should show `[JSON-CAPTURE] installed fetch/xhr hook`.
- For each collection, logs should show `[COLLECTION-PROGRESS]`, `[COLLECTION-PAGE]`, and `[NEXT]` where pagination exists.
- Successful DB writing logs look like `[DB-WRITE] ... affected=... ignored=...`.
- `affected` includes both inserted and updated rows when `--update-existing` is used.

## Troubleshooting

- If Chinese log text is garbled in PowerShell, rely on IDs, URLs, counts, and JSONL files; the files are UTF-8.
- If `conda activate wechatapp` is slow or unreliable, invoke `E:\anaconda\envs\wechatapp\python.exe` directly.
- If the database count does not change, inspect `--mapped-dump`; existing `bvid` rows may have been updated instead of inserted.
- If an external packet-capture program is running, do not attribute DB increments solely to this script.
- If page navigation works but JSON rows are missing, ensure the script was run with `--mapped-dump`, `--write-db`, or `--json-dump`; otherwise the capture hook is not installed.

## Long-Running Tasks (Critical)

**Claude 会话启动的子进程会被会话清理机制终止**（无论用 `run_in_background`、bash `&`、还是 `Start-Process`）。进程会在 1-2 分钟内被杀，无 traceback、无 exit code。

对于需要长时间运行的任务（批量转文字、大批量爬取等），**必须使用 Windows 计划任务**：

```powershell
# 1. 创建包装脚本（带日志重定向）
# 参考 X:\RPA\bili2text\run_with_diag.bat

# 2. 注册计划任务
$action = New-ScheduledTaskAction -Execute "X:\path\to\wrapper.bat" -WorkingDirectory "X:\RPA"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(3)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "TaskName" -Action $action -Trigger $trigger -Settings $settings -Force

# 3. 启动
Start-ScheduledTask -TaskName "TaskName"

# 4. 查看状态
Get-ScheduledTask -TaskName "TaskName"
Get-Process -Name python*

# 5. 停止
Stop-ScheduledTask -TaskName "TaskName"
Unregister-ScheduledTask -TaskName "TaskName" -Confirm:$false
```

计划任务由 Windows 任务计划程序服务管理，完全独立于 Claude 会话。即使关掉终端、注销登录，任务都会继续跑。

**注意：** 短时间任务（几分钟内完成的）仍可用 `run_in_background`。

## Current Implementation Notes

- `bili2text\batch_process_ups.py` uses `是否已经转文字` for transcription completion. Do not filter transcription jobs by `是否已经爬取`; crawled rows are exactly the rows that should be transcribed.
- `--include-done` means include already-transcribed UPs.
- The transcription checkpoint skips only `success`, `skipped`, and `paid`; `failed` and `error` are retried on the next run.
- In `crawl_and_transcribe` wrappers, `-Mids` / `--mids` is currently supported only with text-only mode. The crawler does not yet filter queue rows by mid.
- The PowerShell wrappers intentionally use ASCII comments/log messages so Windows PowerShell 5.1 does not garble diagnostic output.
