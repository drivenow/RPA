---
name: wechat-rpa-workflow
description: Run and troubleshoot the X:\RPA WeChat public-account RPA workflow. Use when the user provides a WeChat article link and wants the full collection flow, asks to add a new official account, process WeChat article queues, scroll WeChatAppEx/WeChat built-in browser pages, verify WeChat collection results, or run the downstream URL processing step at X:\RPA\src\tools_data_process\engine_url_pg.py.
---

# WeChat RPA Workflow

## Core Facts

- Work from `X:\RPA`.
- WeChat background scrolling is not reliable. `WeChatAppEx.exe` usually scrolls only when the target page is foreground/active.
- Prefer the foreground scrolling queue script. Do not spend time trying `PostMessage`/`SendMessage` background scrolling unless the user explicitly asks to re-research it.
- Use PowerShell on Windows.
- If using Python dependencies from the project environment, prefer `E:\anaconda\envs\wechatapp\python.exe`.

## Full Workflow

For a single WeChat article link, use `--add-and-run`. The script extracts `__biz`, adds or updates the Excel queue, opens the official-account profile, scrolls in the WeChat built-in browser, then marks the row done after successful scrolling.

1. Confirm WeChat is open and the built-in browser can be brought to foreground.
2. Run `wechat_biz_browser_runner.py --add-and-run "<article_url>"` from `X:\RPA`.
3. Keep the WeChat built-in browser window foreground while scrolling.
4. Watch logs for selected window, extracted account name candidates, scroll progress, Excel row updates, and stop conditions.
5. Run the downstream URL processing script:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_data_process\engine_url_pg.py
```

## Useful Commands

Add a new official account from one article link, scroll it, and mark it done:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\wechat_biz_browser_runner.py --add-and-run "https://mp.weixin.qq.com/s?__biz=MzYzMTg1MzEwMg==&mid=..."
```

Add the account to Excel without scrolling:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\wechat_biz_browser_runner.py --add-and-run "https://mp.weixin.qq.com/s?__biz=MzYzMTg1MzEwMg==&mid=..." --no-scroll
```

Probe the WeChat browser window:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\wechat_biz_browser_runner.py --probe --dump tmp\wechat_probe.json
```

Run queue scrolling with foreground mode:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe src\tools_browser\wechat_biz_browser_runner.py --only-unfinished
```

If testing direct scroll helper:

```powershell
cd X:\RPA
E:\anaconda\envs\wechatapp\python.exe -c "from src.tools_browser.wechat_biz_browser_runner import find_wechat_browser_window, scroll_wechat_browser; w=find_wechat_browser_window(); scroll_wechat_browser(w.hwnd, max_scrolls=20, delay=(1,3), backend='foreground', check_bottom=True)"
```

## Validation

- Functional scroll means the visible WeChat page actually moves, not only that logs say `[SCROLL]`.
- For `--add-and-run`, success should include an `[EXCEL] 已添加` or `已存在` log, `[SCROLL]` progress, and `[EXCEL] 已标记完成`.
- Excel `是否已经爬取` treats blank/`0` as unfinished and `1`/`1.0`/done-like text as finished.
- The known failure mode is logs showing scroll attempts while the background window does not move.
- Avoid screenshot-only bottom detection when the window is covered; it can produce false positives.
- After collection, run `engine_url_pg.py` and check its logs/output for processed URL counts or errors.

## Troubleshooting

- If the page does not move, bring the WeChat page to foreground and rerun.
- If a one-line `python -c` command fails in PowerShell, keep it on one physical line and avoid full-width punctuation.
- If numpy/OpenBLAS warnings appear, treat them as non-fatal unless execution stops.
- If WeChat HTTPS/interface capture is requested, state the current known limitation: WeChat certificate validation blocks normal MITM capture, so the practical workflow is foreground UI automation plus downstream processing.
