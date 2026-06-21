# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime
from numbers import Number
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from filelock import FileLock
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = Path("selenium_tools") / "BiliProfile"
CHROMEDRIVER_DIR = Path("selenium_tools") / "chromedriver-win64"
CHROMEDRIVER_EXE = CHROMEDRIVER_DIR / "chromedriver.exe"
DEFAULT_CXT_RPA_DB = Path(r"C:\ProgramData\CXT.RPA\CXT.RPA.db")
DEFAULT_MYSQL_HOST = "192.168.1.2"
DEFAULT_MYSQL_PORT = 3306
DEFAULT_MYSQL_USER = "admin"
DEFAULT_MYSQL_PASSWORD = "ybsDW246401."
DEFAULT_MYSQL_DATABASE = "mydatabase"

K_TABLE_CONFIGS = "\u6570\u636e\u8868\u5bf9\u5e94\u914d\u7f6e"
K_TYPE = "\u7c7b\u578b"
K_PATH = "\u8def\u5f84"
K_TABLE = "\u6570\u636e\u5e93\u8868\u540d"
K_FIELDS = "\u8868\u5b57\u6bb5"
K_DEDUP = "\u6570\u636e\u662f\u5426\u53bb\u91cd"
K_DEDUP_FIELD = "\u6570\u636e\u53bb\u91cd\u5b57\u6bb5"

JSON_CAPTURE_HOOK = r"""
(() => {
  if (window.__rpaBiliHookInstalled) return;
  window.__rpaBiliHookInstalled = true;
  window.__rpaBiliJson = window.__rpaBiliJson || [];

  const keep = (url, text, status, source) => {
    try {
      url = String(url || '');
      text = String(text || '');
      if (!url.includes('bilibili.com')) return;
      if (!text || text.length < 2) return;
      const first = text.trim()[0];
      if (first !== '{' && first !== '[') return;
      JSON.parse(text);
      window.__rpaBiliJson.push({
        ts: Date.now(),
        source,
        url,
        status: status || 0,
        body: text
      });
    } catch (e) {}
  };

  const origFetch = window.fetch;
  if (origFetch && !origFetch.__rpaWrapped) {
    const wrappedFetch = async (...args) => {
      const resp = await origFetch(...args);
      try {
        const url = resp.url || (args[0] && args[0].url) || args[0];
        const ct = (resp.headers && resp.headers.get && resp.headers.get('content-type')) || '';
        if (String(url).includes('bilibili.com') && ct.includes('json')) {
          resp.clone().text().then(text => keep(url, text, resp.status, 'fetch'));
        }
      } catch (e) {}
      return resp;
    };
    wrappedFetch.__rpaWrapped = true;
    window.fetch = wrappedFetch;
  }

  if (!XMLHttpRequest.prototype.__rpaWrapped) {
    const origOpen = XMLHttpRequest.prototype.open;
    const origSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
      this.__rpaUrl = url;
      return origOpen.call(this, method, url, ...rest);
    };
    XMLHttpRequest.prototype.send = function(...args) {
      this.addEventListener('loadend', function() {
        try {
          const ct = (this.getResponseHeader && this.getResponseHeader('content-type')) || '';
          if (String(this.__rpaUrl).includes('bilibili.com') && ct.includes('json')) {
            keep(this.responseURL || this.__rpaUrl, this.responseText, this.status, 'xhr');
          }
        } catch (e) {}
      });
      return origSend.apply(this, args);
    };
    XMLHttpRequest.prototype.__rpaWrapped = true;
  }
})();
"""


@dataclass
class TableMapping:
    table: str
    path: str
    fields: list[str]
    dedup: bool
    dedup_field: str


@dataclass
class ResponseMapping:
    config_id: int
    name: str
    url: str
    tables: list[TableMapping]


class JsonCaptureRecorder:
    def __init__(
        self,
        json_dump: Path | None,
        mapped_dump: Path | None,
        mappings: list[ResponseMapping],
        db_writer: "MysqlMappedWriter | None" = None,
    ) -> None:
        self.json_dump = json_dump
        self.mapped_dump = mapped_dump
        self.mappings = mappings
        self.db_writer = db_writer
        self.seen_response_hashes: set[str] = set()
        self.seen_row_hashes: set[str] = set()
        self.first_flush = True
        self.last_response_count = 0
        self.last_mapped_count = 0
        for path in [json_dump, mapped_dump]:
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)

    def discard_browser_buffer(self, driver: webdriver.Chrome, label: str) -> bool:
        try:
            count = driver.execute_script(
                "const items = window.__rpaBiliJson || []; window.__rpaBiliJson = []; return items.length;"
            ) or 0
        except WebDriverException as exc:
            print(f"[JSON-CAPTURE-ERROR] {label} discard failed: {exc}")
            return False
        if count:
            print(f"[JSON-CAPTURE] discarded buffered responses={count} label={label}")
        return True

    def start_target(self, driver: webdriver.Chrome, mapped_dump: Path | None, label: str) -> bool:
        ok = self.discard_browser_buffer(driver, f"{label}:before-switch")
        if mapped_dump:
            mapped_dump.parent.mkdir(parents=True, exist_ok=True)
            self.mapped_dump = mapped_dump
        self.seen_response_hashes.clear()
        self.seen_row_hashes.clear()
        self.first_flush = False
        print(f"[JSON-CAPTURE] start target label={label} mapped_dump={self.mapped_dump}")
        return ok

    def flush(self, driver: webdriver.Chrome, label: str) -> bool:
        self.last_response_count = 0
        self.last_mapped_count = 0
        try:
            items = driver.execute_script(
                "const items = window.__rpaBiliJson || []; window.__rpaBiliJson = []; return items;"
            ) or []
        except WebDriverException as exc:
            print(f"[JSON-CAPTURE-ERROR] {label} flush failed: {exc}")
            return False

        if not items:
            self.first_flush = False
            return True

        if self.first_flush:
            self.first_flush = False
            print(f"[JSON-CAPTURE] discard initial buffered responses={len(items)} label={label}")
            return True

        new_items = []
        for item in items:
            body = item.get("body") or ""
            digest = hashlib.sha1(f"{item.get('url')}|{body}".encode("utf-8", errors="ignore")).hexdigest()
            if digest in self.seen_response_hashes:
                continue
            self.seen_response_hashes.add(digest)
            item = dict(item)
            item["label"] = label
            new_items.append(item)

        if not new_items:
            return True

        self.last_response_count = len(new_items)
        print(f"[JSON-CAPTURE] {label} responses={len(new_items)}")
        if self.json_dump:
            append_jsonl(self.json_dump, new_items)

        mapped_rows = []
        for item in new_items:
            mapped_rows.extend(map_response_item(item, self.mappings))

        unique_rows = []
        for row in mapped_rows:
            values = row.get("values") or {}
            dedup_fields = parse_dedup_fields(row.get("dedup_field"))
            if row.get("dedup") and dedup_fields and all(values.get(field) is not None for field in dedup_fields):
                dedup_values = "|".join(f"{field}={values.get(field)}" for field in dedup_fields)
                row_key = f"{row.get('table')}|{dedup_values}"
            else:
                row_key = json.dumps(row, ensure_ascii=False, sort_keys=True)
            digest = hashlib.sha1(row_key.encode("utf-8", errors="ignore")).hexdigest()
            if digest in self.seen_row_hashes:
                continue
            self.seen_row_hashes.add(digest)
            unique_rows.append(row)

        if unique_rows:
            table_counts: dict[str, int] = {}
            for row in unique_rows:
                table_counts[row["table"]] = table_counts.get(row["table"], 0) + 1
            self.last_mapped_count = len(unique_rows)
            print(f"[JSON-MAPPED] {label} rows={len(unique_rows)} tables={table_counts}")
            if self.mapped_dump:
                append_jsonl(self.mapped_dump, unique_rows)
            if self.db_writer:
                self.db_writer.write_rows(unique_rows, label)
        return True

    def close(self) -> None:
        if self.db_writer:
            self.db_writer.close()


class MysqlMappedWriter:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        update_existing: bool = False,
    ) -> None:
        import pymysql

        self.pymysql = pymysql
        self.database = database
        self.update_existing = update_existing
        self.conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
            autocommit=False,
            connect_timeout=10,
        )
        self.table_columns: dict[str, set[str]] = {}
        print(
            f"[DB] connected host={host} port={port} database={database} "
            f"user={user} update_existing={update_existing}"
        )

    def close(self) -> None:
        try:
            self.conn.close()
            print("[DB] closed")
        except Exception:
            pass

    def get_table_columns(self, table: str) -> set[str]:
        if table in self.table_columns:
            return self.table_columns[table]

        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                select COLUMN_NAME
                from information_schema.COLUMNS
                where TABLE_SCHEMA=%s and TABLE_NAME=%s
                """,
                (self.database, table),
            )
            columns = {row[0] for row in cursor.fetchall()}
        self.table_columns[table] = columns
        print(f"[DB-COLUMNS] table={table} columns={len(columns)}")
        return columns

    @staticmethod
    def quote_identifier(identifier: str) -> str:
        return "`" + identifier.replace("`", "``") + "`"

    def write_rows(self, rows: list[dict], label: str) -> None:
        table_rows: dict[str, list[dict]] = {}
        for row in rows:
            table_rows.setdefault(row["table"], []).append(row)

        total_affected = 0
        total_ignored = 0
        try:
            with self.conn.cursor() as cursor:
                for table, group in table_rows.items():
                    columns = self.get_table_columns(table)
                    affected, ignored = self.write_table_rows(cursor, table, columns, group)
                    total_affected += affected
                    total_ignored += ignored
            self.conn.commit()
            print(
                f"[DB-WRITE] {label} rows={len(rows)} affected={total_affected} "
                f"ignored={total_ignored} tables={list(table_rows.keys())}"
            )
        except Exception as exc:
            self.conn.rollback()
            print(f"[DB-ERROR] {label} rollback rows={len(rows)} error={exc}")

    def write_table_rows(self, cursor, table: str, columns: set[str], rows: list[dict]) -> tuple[int, int]:
        affected = 0
        ignored = 0
        for row in rows:
            values = {
                key: value
                for key, value in (row.get("values") or {}).items()
                if key in columns
            }
            if not values:
                print(f"[DB-SKIP] table={table} no matching columns source={row.get('source_url')}")
                continue

            dedup_fields = parse_dedup_fields(row.get("dedup_field"))
            if (
                row.get("dedup")
                and dedup_fields
                and all(field in values and values[field] is not None for field in dedup_fields)
            ):
                where_clause = " AND ".join(
                    f"{self.quote_identifier(field)}=%s" for field in dedup_fields
                )
                where_values = [values[field] for field in dedup_fields]
                check_sql = (
                    f"SELECT 1 FROM {self.quote_identifier(table)} "
                    f"WHERE {where_clause} LIMIT 1"
                )
                cursor.execute(check_sql, where_values)
                if cursor.fetchone():
                    if self.update_existing:
                        update_values = {
                            key: value
                            for key, value in values.items()
                            if key not in dedup_fields and value is not None
                        }
                        if update_values:
                            set_clause = ", ".join(
                                f"{self.quote_identifier(key)}=%s" for key in update_values
                            )
                            update_sql = (
                                f"UPDATE {self.quote_identifier(table)} SET {set_clause} "
                                f"WHERE {where_clause}"
                            )
                            cursor.execute(update_sql, list(update_values.values()) + where_values)
                            affected += cursor.rowcount
                        else:
                            ignored += 1
                    else:
                        ignored += 1
                    continue

            sql_columns = ", ".join(self.quote_identifier(key) for key in values)
            placeholders = ", ".join(["%s"] * len(values))
            verb = "INSERT IGNORE" if row.get("dedup") else "INSERT"
            sql = f"{verb} INTO {self.quote_identifier(table)} ({sql_columns}) VALUES ({placeholders})"
            cursor.execute(sql, list(values.values()))
            if cursor.rowcount:
                affected += 1
            else:
                ignored += 1

        return affected, ignored


JSON_RECORDER: JsonCaptureRecorder | None = None


def append_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_dedup_fields(dedup_field: str | None) -> list[str]:
    if not dedup_field:
        return []
    return [field.strip() for field in dedup_field.split(",") if field.strip()]


def install_json_capture(driver: webdriver.Chrome) -> None:
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": JSON_CAPTURE_HOOK})
    try:
        driver.execute_script(JSON_CAPTURE_HOOK)
        driver.execute_script("window.__rpaBiliJson = [];")
    except WebDriverException:
        pass
    print("[JSON-CAPTURE] installed fetch/xhr hook")


def flush_json_capture(driver: webdriver.Chrome, label: str) -> bool:
    if JSON_RECORDER:
        return JSON_RECORDER.flush(driver, label)
    return True


def last_json_capture_counts() -> tuple[int, int]:
    if not JSON_RECORDER:
        return 0, 0
    return JSON_RECORDER.last_response_count, JSON_RECORDER.last_mapped_count


def load_guid_mappings(db_path: Path) -> list[ResponseMapping]:
    import sqlite3

    if not db_path.exists():
        print(f"[GUID-CONFIG] not found: {db_path}")
        return []

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            "select gk_id,name,url,configStr,status from Guid2DB2Config where configStr is not null"
        ).fetchall()
    finally:
        con.close()

    mappings: list[ResponseMapping] = []
    for row in rows:
        url = row["url"] or ""
        if "bilibili.com" not in url:
            continue
        try:
            config = json.loads(row["configStr"])
        except Exception as exc:
            print(f"[GUID-CONFIG-ERROR] gk_id={row['gk_id']} parse failed: {exc}")
            continue

        table_configs = config.get(K_TABLE_CONFIGS) or []
        tables = []
        for table_config in table_configs:
            fields = [
                field.strip()
                for field in (table_config.get(K_FIELDS) or "").split(",")
                if field.strip()
            ]
            table = table_config.get(K_TABLE) or ""
            path = table_config.get(K_PATH) or ""
            if not table or not path or not fields:
                continue
            tables.append(
                TableMapping(
                    table=table,
                    path=path,
                    fields=fields,
                    dedup=bool(table_config.get(K_DEDUP)),
                    dedup_field=table_config.get(K_DEDUP_FIELD) or "",
                )
            )

        if tables:
            mappings.append(
                ResponseMapping(
                    config_id=int(row["gk_id"]),
                    name=row["name"] or "",
                    url=url,
                    tables=tables,
                )
            )

    print(f"[GUID-CONFIG] loaded bilibili mappings={len(mappings)} from {db_path}")
    for mapping in mappings:
        table_desc = ", ".join(f"{table.table}:{table.path}" for table in mapping.tables)
        print(f"[GUID-CONFIG] gk_id={mapping.config_id} name={mapping.name} url={mapping.url} tables={table_desc}")
    return mappings


def get_path_value(data, path: str):
    current = data
    if not path:
        return current
    for part in path.split("."):
        tokens = re.findall(r"([^\[\]]+)|\[(\d+)\]", part)
        for name_token, index_token in tokens:
            if name_token:
                if not isinstance(current, dict):
                    return None
                current = current.get(name_token)
            elif index_token:
                if not isinstance(current, list):
                    return None
                try:
                    current = current[int(index_token)]
                except IndexError:
                    return None
    return current


def flatten_json(value, prefix: str = "") -> dict:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_json(child, child_key))
        return result
    if isinstance(value, list):
        return {prefix: json.dumps(value, ensure_ascii=False)}
    return {prefix: value}


def map_response_item(item: dict, mappings: list[ResponseMapping]) -> list[dict]:
    url = item.get("url") or ""
    matched = [mapping for mapping in mappings if mapping.url and mapping.url in url]
    if not matched:
        return []

    try:
        body = json.loads(item.get("body") or "")
    except Exception as exc:
        print(f"[JSON-MAP-ERROR] parse body failed url={url}: {exc}")
        return []

    query_values = {
        key: values[-1] if values else ""
        for key, values in parse_qs(urlparse(url).query, keep_blank_values=True).items()
    }
    rows = []
    for mapping in matched:
        for table in mapping.tables:
            records = get_path_value(body, table.path)
            if records is None:
                print(f"[JSON-MAP-SKIP] gk_id={mapping.config_id} path not found: {table.path}")
                continue
            if isinstance(records, dict):
                records = [records]
            if not isinstance(records, list):
                print(f"[JSON-MAP-SKIP] gk_id={mapping.config_id} path is not list/dict: {table.path}")
                continue

            for index, record in enumerate(records):
                flat = flatten_json(record)
                values = {}
                for field in table.fields:
                    if field in flat:
                        values[field] = flat[field]
                    elif field in query_values:
                        values[field] = query_values[field]
                    else:
                        values[field] = None
                rows.append(
                    {
                        "config_id": mapping.config_id,
                        "config_name": mapping.name,
                        "source_url": url,
                        "table": table.table,
                        "path": table.path,
                        "index": index,
                        "dedup": table.dedup,
                        "dedup_field": table.dedup_field,
                        "values": values,
                    }
                )

    return rows


def sleep_random(delay_min: float, delay_max: float) -> None:
    delay = random.uniform(delay_min, delay_max)
    print(f"[WAIT] {delay:.1f}s")
    time.sleep(delay)


def extract_mid(url: str) -> str | None:
    match = re.search(r"space\.bilibili\.com/(\d+)", url)
    return match.group(1) if match else None


def fetch_up_name(mid: str) -> str:
    """通过 Bilibili 空间页面 title 获取 UP 名称，失败时返回空字符串。"""
    try:
        url = f"https://space.bilibili.com/{mid}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        m = re.search(r"<title[^>]*>([^<]+)</title>", html)
        if m:
            # Pattern: "UP名称 的个人空间 - 哔哩哔哩" or "UP名称的个人空间-..."
            m2 = re.match(r"(.+?)\s*的个人空间", m.group(1))
            if m2:
                return m2.group(1).strip()
    except Exception as e:
        print(f"[PAGE] 获取 UP 名称失败 mid={mid}: {e}")
    return ""


# ---------------------------------------------------------------------------
# Excel 队列管理（对标微信 wechat_biz_browser_runner.py）
# ---------------------------------------------------------------------------

BILI_EXCEL_COLUMNS = ["UP名称", "mid", "空间链接", "是否已经爬取"]


def default_bili_excel_path() -> Path:
    from src.tools_data_process.utils_path import get_root_media_save_path

    base_dir = get_root_media_save_path("homepage_url", None)[1]
    return Path(base_dir) / "bili_up_queue.xlsx"


def _ensure_bili_excel_columns(df, columns: list[str]):
    import pandas as pd

    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df


def is_bili_done_status(value: Any) -> bool:
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
    if not text:
        return False
    # 时间戳格式也算完成（如 "2026-06-19 18:08:34"）
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            pass
    return text in {"1", "1.0", "true", "yes", "y", "done", "完成", "已完成", "已爬取"}


def add_mid_to_excel(excel_path: Path, mid: str, name: str, url: str) -> tuple[bool, int]:
    """添加 UP 到 Excel 队列，返回 (是否新增, DataFrame 行索引)。"""
    import pandas as pd

    lock = FileLock(str(excel_path) + ".lock")
    with lock:
        if excel_path.exists():
            df = pd.read_excel(excel_path, dtype={"mid": str})
        else:
            df = pd.DataFrame(columns=BILI_EXCEL_COLUMNS)

        df = _ensure_bili_excel_columns(df, BILI_EXCEL_COLUMNS)

        matched = df.index[df["mid"].astype(str) == str(mid)].tolist()
        if matched:
            row_index = matched[0]
            print(f"[EXCEL] mid={mid} 已存在，跳过新增 row={row_index + 2}")
            updated = False
            existing_name = str(df.at[row_index, "UP名称"] or "").strip()
            if existing_name in ("nan", "None"):
                existing_name = ""
            # 名称为空或就是 mid 本身时，用新名称覆盖
            if name and (not existing_name or existing_name == str(mid)):
                df.at[row_index, "UP名称"] = name
                updated = True
            if not str(df.at[row_index, "空间链接"] or "").strip():
                df.at[row_index, "空间链接"] = url
                updated = True
            if updated:
                excel_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_excel(excel_path, index=False)
                print(f"[EXCEL] 已补齐已有行 row={row_index + 2}")
            return False, row_index

        new_row = {
            "UP名称": name,
            "mid": str(mid),
            "空间链接": url,
            "是否已经爬取": "",
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(excel_path, index=False)
        row_index = len(df) - 1

    print(f"[EXCEL] 已添加:")
    print(f"  UP名称: {name}")
    print(f"  mid: {mid}")
    print(f"  空间链接: {url}")
    print(f"  Excel行号: {row_index + 2}")
    print(f"  现有数据: {len(df)} 行")
    return True, row_index


def mark_mid_done_in_excel(excel_path: Path, mid: str, row_index: int | None = None) -> None:
    """按行索引或 mid 标记已爬取（写入时间戳）。"""
    import pandas as pd
    from datetime import datetime

    if not excel_path.exists():
        print(f"[EXCEL-WARN] 文件不存在，无法标记完成: {excel_path}")
        return

    lock = FileLock(str(excel_path) + ".lock")
    with lock:
        df = pd.read_excel(excel_path, dtype={"mid": str})
        df = _ensure_bili_excel_columns(df, BILI_EXCEL_COLUMNS)
        target_index = row_index
        if target_index is None or target_index not in df.index:
            matched = df.index[df["mid"].astype(str) == str(mid)].tolist()
            target_index = matched[0] if matched else None

        if target_index is None:
            print(f"[EXCEL-WARN] 没找到 mid={mid}，无法标记完成")
            return

        df.at[target_index, "是否已经爬取"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(excel_path, index=False)
    print(f"[EXCEL] 已标记完成 row={target_index + 2} mid={mid}")


def load_bili_targets(args: argparse.Namespace) -> list[dict[str, Any]]:
    """从 Excel 加载未完成的 UP 列表。"""
    import pandas as pd

    excel = Path(args.excel) if args.excel else default_bili_excel_path()
    if not excel.exists():
        print(f"[EXCEL-WARN] 文件不存在: {excel}")
        return []

    df = pd.read_excel(excel, dtype={"mid": str})
    df = _ensure_bili_excel_columns(df, BILI_EXCEL_COLUMNS)

    if args.only_unfinished and "是否已经爬取" in df.columns:
        df = df[~df["是否已经爬取"].map(is_bili_done_status)]

    targets: list[dict[str, Any]] = []
    for row_index, row in df.iterrows():
        mid = str(row.get("mid", "") or "").strip()
        if not mid:
            # 尝试从空间链接提取
            link = str(row.get("空间链接", "") or "")
            mid = extract_mid(link) or ""
        if not mid:
            continue
        name = str(row.get("UP名称", "") or "").strip() or mid
        raw_url = str(row.get("空间链接", "") or "").strip()
        link_mid = extract_mid(raw_url) if raw_url else None
        if raw_url and not link_mid:
            print(f"[EXCEL-WARN] row={row_index + 2} 空间链接无效，改用 mid 生成链接: {raw_url}")
        elif link_mid and link_mid != mid:
            print(
                f"[EXCEL-WARN] row={row_index + 2} mid={mid} 与空间链接 mid={link_mid} 不一致，"
                "改用 mid 生成链接"
            )
        url = normalize_space_home_url(raw_url if link_mid == mid else f"https://space.bilibili.com/{mid}")
        targets.append({"mid": mid, "name": name, "url": url, "row_index": row_index})

    print(f"[EXCEL] 加载 {len(targets)} 个 UP 目标")
    return targets


# ---------------------------------------------------------------------------


def normalize_space_home_url(url: str) -> str:
    mid = extract_mid(url)
    if not mid:
        raise ValueError(f"不是 Bilibili UP 空间地址: {url}")
    return f"https://space.bilibili.com/{mid}"


def normalize_space_video_url(url: str, page_no: int) -> str:
    mid = extract_mid(url)
    if not mid:
        raise ValueError(f"不是 Bilibili UP 空间地址: {url}")
    return (
        f"https://space.bilibili.com/{mid}/upload/video"
        f"?tid=0&pn={page_no}&keyword=&order=pubdate"
    )


def normalize_space_opus_url(url: str, page_no: int) -> str:
    mid = extract_mid(url)
    if not mid:
        raise ValueError(f"不是 Bilibili UP 空间地址: {url}")
    return f"https://space.bilibili.com/{mid}/upload/opus?pn={page_no}"


def normalize_space_dynamic_url(url: str) -> str:
    mid = extract_mid(url)
    if not mid:
        raise ValueError(f"不是 Bilibili UP 空间地址: {url}")
    return f"https://space.bilibili.com/{mid}/dynamic"


def normalize_space_lists_url(url: str) -> str:
    mid = extract_mid(url)
    if not mid:
        raise ValueError(f"不是 Bilibili UP 空间地址: {url}")
    return f"https://space.bilibili.com/{mid}/lists"


def start_chrome(port: int, user_data_dir: Path) -> None:
    user_data_dir.mkdir(parents=True, exist_ok=True)
    command = [
        CHROME_PATH,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir.resolve()}",
        "--start-maximized",
    ]
    print("[CHROME] " + " ".join(f'"{part}"' if " " in part else part for part in command))
    subprocess.Popen(command)
    time.sleep(2)


def get_installed_chrome_version() -> str:
    chrome_dir = Path(CHROME_PATH).parent
    versions = []
    for child in chrome_dir.iterdir():
        if child.is_dir() and re.fullmatch(r"\d+\.\d+\.\d+\.\d+", child.name):
            versions.append(child.name)

    if versions:
        return sorted(versions, key=lambda v: tuple(map(int, v.split("."))), reverse=True)[0]

    raise RuntimeError(f"没有找到 Chrome 版本目录: {chrome_dir}")


def _download_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def find_chromedriver_download_url(chrome_version: str) -> str:
    build = ".".join(chrome_version.split(".")[:3])
    patch_url = "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build-with-downloads.json"
    data = _download_json(patch_url)
    entry = data.get("builds", {}).get(build)

    if not entry:
        milestone = chrome_version.split(".")[0]
        milestone_url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
        data = _download_json(milestone_url)
        entry = data.get("milestones", {}).get(milestone)

    if not entry:
        raise RuntimeError(f"Chrome for Testing 清单里找不到 Chrome {chrome_version} 的 chromedriver")

    for item in entry.get("downloads", {}).get("chromedriver", []):
        if item.get("platform") == "win64":
            return item["url"]

    raise RuntimeError(f"Chrome for Testing 清单里没有 win64 chromedriver: {chrome_version}")


def ensure_chromedriver() -> Path:
    if CHROMEDRIVER_EXE.exists():
        return CHROMEDRIVER_EXE

    chrome_version = get_installed_chrome_version()
    url = find_chromedriver_download_url(chrome_version)
    zip_path = Path("tmp") / "chromedriver-win64.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[DRIVER] Chrome {chrome_version}")
    print(f"[DRIVER] downloading {url}")
    urllib.request.urlretrieve(url, zip_path)

    CHROMEDRIVER_DIR.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(CHROMEDRIVER_DIR.parent)

    if not CHROMEDRIVER_EXE.exists():
        raise RuntimeError(f"chromedriver 下载后仍不存在: {CHROMEDRIVER_EXE}")

    return CHROMEDRIVER_EXE


def make_driver(port: int | None, launch: bool) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    if port is not None:
        if launch:
            start_chrome(port, PROFILE_DIR)
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    else:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={PROFILE_DIR.resolve()}")

    driver_path = ensure_chromedriver()
    service = Service(str(driver_path))
    return webdriver.Chrome(service=service, options=options)


def collect_media_links(driver: webdriver.Chrome) -> list[str]:
    script = """
    return Array.from(document.querySelectorAll('a[href*="/video/BV"],a[href*="/opus/"],a[href*="/read/"]'))
      .map(a => a.href.split('?')[0])
      .filter(Boolean);
    """
    links = driver.execute_script(script)
    return sorted(set(links or []))


def log_media_links(label: str, links: list[str], seen_links: set[str] | None = None) -> set[str]:
    unique_links = set(links)
    if seen_links is None:
        seen_links = set()

    new_links = unique_links - seen_links
    repeat_links = unique_links & seen_links
    print(
        f"[LINK-STATS] {label} visible={len(links)} unique={len(unique_links)} "
        f"new={len(new_links)} repeat={len(repeat_links)}"
    )
    if new_links:
        print("[LINK-NEW] sample=" + " | ".join(sorted(new_links)[:3]))
    elif unique_links:
        print("[LINK-REPEAT] sample=" + " | ".join(sorted(unique_links)[:3]))

    seen_links.update(unique_links)
    return seen_links


def scroll_page(driver: webdriver.Chrome, count: int, delay_min: float, delay_max: float) -> None:
    for index in range(1, count + 1):
        driver.execute_script("window.scrollBy(0, Math.max(window.innerHeight * 0.85, 700));")
        print(f"[SCROLL] {index}/{count}")
        sleep_random(delay_min, delay_max)


def scroll_until_stable(
    driver: webdriver.Chrome,
    label: str,
    max_scrolls: int,
    delay_min: float,
    delay_max: float,
    stable_limit: int = 2,
) -> int:
    seen_links = set(collect_media_links(driver))
    stable_count = 0

    for index in range(1, max_scrolls + 1):
        driver.execute_script("window.scrollBy(0, Math.max(window.innerHeight * 0.85, 700));")
        print(f"[SCROLL] {label} {index}/{max_scrolls}")
        sleep_random(delay_min, delay_max)
        flush_ok = flush_json_capture(driver, f"{label}:scroll={index}")
        response_count, mapped_count = last_json_capture_counts()

        links = collect_media_links(driver)
        unique_links = set(links)
        new_links = unique_links - seen_links
        seen_links.update(unique_links)

        if not flush_ok:
            stable_count = 0
            print(f"[SCROLL-STATS] {label} flush_failed=True visible={len(links)}")
            continue

        has_new_data = bool(new_links or mapped_count)
        stable_count = 0 if has_new_data else stable_count + 1
        print(
            f"[SCROLL-STATS] {label} visible={len(links)} new_links={len(new_links)} "
            f"json={response_count} mapped={mapped_count} stable={stable_count}/{stable_limit}"
        )
        if stable_count >= stable_limit:
            print(f"[STOP] {label} 连续 {stable_limit} 次没有新增链接或映射行，停止滚动")
            break

    return len(seen_links)


def log_debug(verbose: bool, message: str) -> None:
    if verbose:
        print(message)


def click_more_buttons(
    driver: webdriver.Chrome,
    scope=None,
    label: str = "",
    max_clicks: int = 5,
    verbose: bool = False,
) -> int:
    target = scope if scope is not None else None
    script = """
    const root = arguments[0] || document;
    const maxClicks = Math.max(0, Number(arguments[1] || 0));
    const nodes = Array.from(root.querySelectorAll('button,a'));
    const candidates = nodes.map((el, index) => {
      const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim();
      const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true' ||
        (el.className || '').toString().includes('disabled');
      return {el, index, text, disabled};
    }).filter(item => !item.disabled && /查看更多|展开更多|更多/.test(item.text));
    const targets = candidates.slice(0, maxClicks).map(item => item.el);
    for (const el of targets) {
      el.scrollIntoView({block: 'center'});
      el.click();
    }
    return {
      clicked: targets.length,
      candidates: candidates.map(item => item.text).slice(0, 10)
    };
    """
    try:
        result = driver.execute_script(script, target, max_clicks) or {}
        clicked = int(result.get("clicked") or 0)
        candidates = result.get("candidates") or []
        log_debug(
            verbose,
            f"[MORE-CANDIDATES] {label or 'global'} clicked={clicked} "
            f"max_clicks={max_clicks} candidates={candidates}",
        )
        return clicked
    except WebDriverException as exc:
        print(f"[MORE-ERROR] {label or 'global'} failed: {exc}")
        return 0


def click_next_if_available(driver: webdriver.Chrome) -> bool:
    script = """
    const findNext = (root) => {
      const nodes = Array.from(root.querySelectorAll('button,a,li'));
      return nodes.find(el => {
        const text = (el.innerText || el.getAttribute('aria-label') || el.title || '').trim();
        const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true' ||
          (el.className || '').toString().includes('disabled');
        return !disabled && /下一页|下页|Next|›|>/.test(text);
      });
    };

    const pagers = Array.from(document.querySelectorAll(
      '[class*="page"],[class*="pagination"],[class*="pager"],.vui_pagenation,.be-pager'
    ));
    let source = 'pagination';
    let next = null;
    for (const pager of pagers) {
      next = findNext(pager);
      if (next) break;
    }
    if (!next) {
      source = 'global';
      next = findNext(document);
    }
    if (!next) {
      return {clicked: false, source, text: '', candidates: pagers.length};
    }

    const text = (next.innerText || next.getAttribute('aria-label') || next.title || '').trim();
    next.scrollIntoView({block: 'center'});
    next.click();
    return {clicked: true, source, text, candidates: pagers.length};
    """
    try:
        result = driver.execute_script(script) or {}
        clicked = bool(result.get("clicked"))
        print(
            f"[NEXT] clicked={clicked} source={result.get('source')} "
            f"text={result.get('text')!r} pager_candidates={result.get('candidates')}"
        )
        return clicked
    except WebDriverException as exc:
        print(f"[NEXT-ERROR] {exc}")
        return False


def get_main_content_scope(driver: webdriver.Chrome):
    script = """
    return document.querySelector('[class*="content"],[class*="list"],main') || document.body;
    """
    try:
        return driver.execute_script(script)
    except WebDriverException:
        return None


def get_collection_cards(driver: webdriver.Chrome, verbose: bool = False) -> list[dict[str, str]]:
    """获取当前页面的合集卡片（B站 lists 页面结构）"""
    from selenium.webdriver.common.by import By

    collections = []
    headers = driver.find_elements(By.CSS_SELECTOR, ".video-list__header")
    log_debug(verbose, f"[DEBUG] 找到 {len(headers)} 个 .video-list__header")

    for idx, header in enumerate(headers):
        try:
            # 获取标题
            title_el = header.find_elements(By.CSS_SELECTOR, ".video-list__title")
            title = title_el[0].text.strip() if title_el else "未知合集"
            log_debug(verbose, f"[DEBUG] 合集 {idx+1} 标题: {title}")

            # 获取视频数量
            desc_el = header.find_elements(By.CSS_SELECTOR, ".video-list__desc")
            desc = desc_el[0].text.strip() if desc_el else ""

            # 获取"查看全部"按钮。不要依赖按钮顺序，B站页面会调整 DOM。
            buttons = header.find_elements(By.CSS_SELECTOR, "button")
            view_all = None
            button_texts = [button.text.strip() for button in buttons]
            for button in buttons:
                btn_text = button.text.strip()
                if button.is_displayed() and (
                    "查看全部" in btn_text
                    or "查看更多" in btn_text
                    or ("查看" in btn_text and "全部" in btn_text)
                ):
                    view_all = button
                    break

            if view_all:
                log_debug(
                    verbose,
                    f"[DEBUG] 合集 {idx+1} 找到查看全部按钮: {view_all.text.strip()} buttons={button_texts}",
                )

            if not view_all:
                log_debug(verbose, f"[DEBUG] 合集 {idx+1} 没找到查看全部按钮，buttons={button_texts}")

            collections.append({
                "title": title,
                "desc": desc,
                "buttons": button_texts,
                "button": view_all,
            })
        except Exception as e:
            log_debug(verbose, f"[DEBUG] 合集 {idx+1} 异常: {e}")
            continue

    return collections


def wait_for_collection_card(
    driver: webdriver.Chrome,
    title: str,
    attempts: int,
    scrolls_per_page: int,
    delay_min: float,
    delay_max: float,
    verbose: bool = False,
) -> dict[str, str] | None:
    for attempt in range(1, attempts + 1):
        cards = get_collection_cards(driver, verbose=verbose)
        titles = [card.get("title", "") for card in cards]
        log_debug(verbose, f"[COLLECTION-SEARCH] attempt={attempt}/{attempts} target={title!r} visible={titles}")

        for card in cards:
            if card.get("title") == title:
                return card

        scroll_page(driver, max(1, scrolls_per_page), delay_min, delay_max)

    return None


def visit_all_collections(
    driver: webdriver.Chrome,
    mid: str,
    max_pages: int,
    scrolls_per_page: int,
    delay_min: float,
    delay_max: float,
    max_collections: int | None = None,
    verbose: bool = False,
) -> None:
    """访问UP主的所有合集/系列，逐个翻页"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # 访问合集列表页面
    lists_url = f"https://space.bilibili.com/{mid}/lists"
    print(f"[COLLECTIONS] 访问合集列表 {lists_url}")
    flush_json_capture(driver, "collections:before-open")
    driver.get(lists_url)
    sleep_random(delay_min, delay_max)
    flush_json_capture(driver, "collections:after-open")

    # 等待合集卡片加载
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".video-list__header"))
        )
        print("[COLLECTIONS] 合集卡片已加载")
    except Exception:
        print("[COLLECTIONS] 等待合集卡片超时")

    # 滚动加载更多合集（但不点击"查看更多"按钮，避免页面跳转）
    scroll_page(driver, scrolls_per_page * 2, delay_min, delay_max)

    # 获取合集卡片（在点击任何按钮之前）
    collection_cards = get_collection_cards(driver, verbose=verbose)
    total_collections = len(collection_cards)
    if max_collections is not None:
        collection_cards = collection_cards[:max_collections]
        print(f"[COLLECTIONS] 找到 {total_collections} 个合集，本次限制处理 {len(collection_cards)} 个")
    else:
        print(f"[COLLECTIONS] 找到 {total_collections} 个合集")

    if not collection_cards:
        print("[COLLECTIONS] 未找到合集")
        return

    for i, card in enumerate(collection_cards, 1):
        title = card.get("title", f"合集{i}")

        print(f"\n[COLLECTION-PROGRESS] {i}/{len(collection_cards)} {title}")

        # 每次循环重新获取按钮（避免stale element）
        fresh_card = wait_for_collection_card(
            driver,
            title=title,
            attempts=4,
            scrolls_per_page=scrolls_per_page,
            delay_min=delay_min,
            delay_max=delay_max,
            verbose=verbose,
        )
        fresh_button = fresh_card.get("button") if fresh_card else None

        if not fresh_button:
            print(f"[COLLECTION-SKIP] {title} 没有查看全部按钮")
            continue

        try:
            # 记录当前窗口
            original_window = driver.current_window_handle
            original_windows = driver.window_handles

            # 滚动到按钮位置并用JS点击
            print(f"[COLLECTION-CLICK] 点击查看全部: {title}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fresh_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", fresh_button)
            sleep_random(delay_min, delay_max)

            # 检查是否打开了新窗口
            new_windows = driver.window_handles
            if len(new_windows) > len(original_windows):
                # 切换到新窗口
                new_window = [w for w in new_windows if w not in original_windows][0]
                driver.switch_to.window(new_window)
                print(f"[COLLECTION-NEW-WINDOW] 切换到新窗口")

            current_url = driver.current_url
            print(f"[COLLECTION-PAGE] {title} {current_url}")
            flush_json_capture(driver, f"collection:{title}:after-open")

            # 翻页
            empty_pages = 0
            no_new_pages = 0
            seen_links: set[str] = set()
            for page_no in range(1, max_pages + 1):
                print(f"[COLLECTION-PAGE] {title} page={page_no}/{max_pages}")
                scroll_page(driver, scrolls_per_page, delay_min, delay_max)

                # 点击"查看更多"
                scope = get_main_content_scope(driver)
                clicked = click_more_buttons(
                    driver,
                    scope=scope,
                    label=f"collection:{title}:page={page_no}",
                    verbose=verbose,
                )
                if clicked:
                    sleep_random(delay_min, delay_max)
                    scroll_page(driver, max(1, scrolls_per_page // 2), delay_min, delay_max)

                flush_json_capture(driver, f"collection:{title}:page={page_no}")
                links = collect_media_links(driver)
                page_links = len(links)
                print(f"[COLLECTION-LINKS] {title} page={page_no} visible={page_links}")
                if links[:3]:
                    print("[COLLECTION-LINKS] sample=" + " | ".join(links[:3]))
                prev_count = len(seen_links)
                log_media_links(f"{title} page={page_no}", links, seen_links)
                new_count = len(seen_links) - prev_count

                if page_links == 0:
                    empty_pages += 1
                    if empty_pages >= 2:
                        print(f"[COLLECTION-STOP] {title} 连续 {empty_pages} 页无链接")
                        break
                else:
                    empty_pages = 0

                # 连续 2 页没有新链接，说明已到最后
                no_new_pages = no_new_pages + 1 if new_count == 0 else 0
                if no_new_pages >= 2:
                    print(f"[COLLECTION-STOP] {title} 连续 2 页没有新链接，停止翻页")
                    break

                if page_no >= max_pages:
                    break

                if not click_next_if_available(driver):
                    print(f"[COLLECTION-STOP] {title} 没有下一页了")
                    break

                sleep_random(delay_min, delay_max)
                flush_json_capture(driver, f"collection:{title}:after-next")

            # 返回合集列表
            if len(new_windows) > len(original_windows):
                # 关闭新窗口，切回原窗口
                flush_json_capture(driver, f"collection:{title}:before-close")
                driver.close()
                driver.switch_to.window(original_window)
                print(f"[COLLECTION-CLOSE] 关闭新窗口，切回原窗口")
            else:
                # 同窗口导航，返回列表
                flush_json_capture(driver, f"collection:{title}:before-return")
                driver.get(lists_url)
                print(f"[COLLECTION-RETURN] 返回合集列表")

            sleep_random(delay_min, delay_max)
            flush_json_capture(driver, f"collection:{title}:after-return")

            # 重新滚动加载合集（因为页面重新加载了）
            if i < len(collection_cards):
                next_title = collection_cards[i].get("title", f"合集{i + 1}")
                print(f"[COLLECTION-RELOAD] 准备定位下一个合集: {next_title}")
                next_card = wait_for_collection_card(
                    driver,
                    title=next_title,
                    attempts=6,
                    scrolls_per_page=scrolls_per_page,
                    delay_min=delay_min,
                    delay_max=delay_max,
                    verbose=verbose,
                )
                if next_card:
                    print(f"[COLLECTION-RELOAD] 已定位下一个合集: {next_title}")
                else:
                    print(f"[COLLECTION-RELOAD-WARN] 没能定位下一个合集: {next_title}")

        except Exception as e:
            print(f"[COLLECTION-ERROR] {title}: {e}")
            # 尝试返回
            try:
                if len(driver.window_handles) > 1:
                    flush_json_capture(driver, f"collection:{title}:error-before-close")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                else:
                    flush_json_capture(driver, f"collection:{title}:error-before-return")
                    driver.get(lists_url)
                    sleep_random(delay_min, delay_max)
                    flush_json_capture(driver, f"collection:{title}:error-after-return")
            except Exception:
                pass


def visit_and_scroll(
    driver: webdriver.Chrome,
    label: str,
    target: str,
    scrolls_per_page: int,
    delay_min: float,
    delay_max: float,
    click_more: bool = False,
    verbose: bool = False,
    adaptive_stop: bool = False,
) -> int:
    print(f"[OPEN] {label} {target}")
    flush_json_capture(driver, f"{label}:before-open")
    driver.get(target)
    sleep_random(delay_min, delay_max)
    flush_json_capture(driver, f"{label}:after-open")
    if click_more:
        clicked = click_more_buttons(driver, label=f"{label}:before-scroll", verbose=verbose)
        if clicked:
            print(f"[MORE] clicked={clicked}")
            sleep_random(delay_min, delay_max)
            flush_json_capture(driver, f"{label}:after-more-before-scroll")
    if adaptive_stop:
        scroll_until_stable(driver, label, scrolls_per_page, delay_min, delay_max)
    else:
        scroll_page(driver, scrolls_per_page, delay_min, delay_max)
        flush_json_capture(driver, f"{label}:after-scroll")
    if click_more:
        clicked = click_more_buttons(driver, label=f"{label}:after-scroll", verbose=verbose)
        if clicked:
            print(f"[MORE] clicked={clicked}")
            sleep_random(delay_min, delay_max)
            scroll_page(driver, max(1, scrolls_per_page // 2), delay_min, delay_max)
            flush_json_capture(driver, f"{label}:after-more-after-scroll")

    links = collect_media_links(driver)
    print(f"[LINKS] {label} visible_media_links={len(links)}")
    if links[:3]:
        print("[LINKS] sample=" + " | ".join(links[:3]))
    flush_json_capture(driver, f"{label}:done")
    return len(links)


def run_paginated_route(
    driver: webdriver.Chrome,
    label: str,
    first_url: str,
    pages: int,
    scrolls_per_page: int,
    delay_min: float,
    delay_max: float,
) -> None:
    print(f"[OPEN] {label} {first_url}")
    flush_json_capture(driver, f"{label}:before-open")
    driver.get(first_url)
    sleep_random(delay_min, delay_max)
    flush_json_capture(driver, f"{label}:after-open")

    empty_pages = 0
    no_new_pages = 0
    seen_links: set[str] = set()
    for page_no in range(1, pages + 1):
        print(f"[PAGE] {label} {page_no}/{pages} current={driver.current_url}")
        scroll_page(driver, scrolls_per_page, delay_min, delay_max)
        flush_json_capture(driver, f"{label}:page={page_no}")
        links = collect_media_links(driver)
        print(f"[LINKS] {label} page={page_no} visible_media_links={len(links)}")
        if links[:3]:
            print("[LINKS] sample=" + " | ".join(links[:3]))
        prev_count = len(seen_links)
        log_media_links(f"{label} page={page_no}", links, seen_links)
        new_count = len(seen_links) - prev_count

        empty_pages = empty_pages + 1 if not links else 0
        if empty_pages >= 2:
            print(f"[STOP] {label} 连续 2 页没有媒体链接")
            break

        # 连续 2 页没有新链接，说明已到最后
        no_new_pages = no_new_pages + 1 if new_count == 0 else 0
        if no_new_pages >= 2:
            print(f"[STOP] {label} 连续 2 页没有新链接，停止翻页")
            break

        if page_no >= pages:
            break

        if not click_next_if_available(driver):
            print(f"[STOP] {label} 没找到可点击的下一页")
            break
        sleep_random(delay_min, delay_max)
        flush_json_capture(driver, f"{label}:after-next")


def run_space_pages(
    driver: webdriver.Chrome,
    urls: list[str],
    pages: int,
    scrolls_per_page: int,
    delay_min: float,
    delay_max: float,
    max_collections: int | None = None,
    verbose: bool = False,
) -> None:
    for url in urls:
        mid = extract_mid(url)
        if not mid:
            print(f"[SKIP] 不是 UP 空间地址: {url}")
            continue

        print(f"\n[SPACE] mid={mid} source={url}")
        visit_and_scroll(
            driver,
            label="home",
            target=normalize_space_home_url(url),
            scrolls_per_page=scrolls_per_page,
            delay_min=delay_min,
            delay_max=delay_max,
            # UP 首页的“查看更多”入口可能同时命中多个合集/模块，容易改变页面状态；
            # 首页只滚动触发请求，合集详情交给 visit_all_collections。
            click_more=False,
            verbose=verbose,
        )

        # 访问所有合集，逐个翻页
        visit_all_collections(
            driver,
            mid=mid,
            max_pages=pages,
            scrolls_per_page=scrolls_per_page,
            delay_min=delay_min,
            delay_max=delay_max,
            max_collections=max_collections,
            verbose=verbose,
        )

        visit_and_scroll(
            driver,
            label="lists",
            target=normalize_space_lists_url(url),
            scrolls_per_page=scrolls_per_page * 2,
            delay_min=delay_min,
            delay_max=delay_max,
            # 合集详情由 visit_all_collections 逐个进入；列表页只滚动触发接口，
            # 避免批量点击多个“查看更多”导致页面状态不可预测。
            click_more=False,
            verbose=verbose,
        )
        visit_and_scroll(
            driver,
            label="dynamic",
            target=normalize_space_dynamic_url(url),
            scrolls_per_page=max(scrolls_per_page * pages, scrolls_per_page),
            delay_min=delay_min,
            delay_max=delay_max,
            click_more=False,
            verbose=verbose,
            adaptive_stop=True,
        )

        run_paginated_route(
            driver,
            label="video",
            first_url=normalize_space_video_url(url, 1),
            pages=pages,
            scrolls_per_page=scrolls_per_page,
            delay_min=delay_min,
            delay_max=delay_max,
        )
        # opus（图文）页面不爬取，只抓视频


def run_generic_pages(
    driver: webdriver.Chrome,
    pages: int,
    scrolls_per_page: int,
    delay_min: float,
    delay_max: float,
) -> None:
    print(f"[GENERIC] current={driver.current_url}")
    for page_no in range(1, pages + 1):
        print(f"[PAGE] generic {page_no}/{pages}")
        scroll_page(driver, scrolls_per_page, delay_min, delay_max)
        flush_json_capture(driver, f"generic:page={page_no}")
        links = collect_media_links(driver)
        print(f"[LINKS] visible_media_links={len(links)}")
        if not click_next_if_available(driver):
            print("[STOP] 没找到可点击的下一页")
            break
        sleep_random(delay_min, delay_max)
        flush_json_capture(driver, f"generic:after-next")


def _parse_delay(value: str) -> tuple[float, float]:
    """解析 --delay 参数。支持 '0.5' 或 '0.3-0.8' 两种格式。"""
    text = str(value or "").strip()
    if not text:
        raise ValueError("delay cannot be empty")
    if "-" in text:
        lo, hi = [part.strip() for part in text.split("-", 1)]
        delay_min, delay_max = float(lo), float(hi)
    else:
        delay_min = delay_max = float(text)
    if delay_min < 0 or delay_max < 0 or delay_min > delay_max:
        raise ValueError("delay must be a non-negative number or min-max range")
    return delay_min, delay_max


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bilibili UP 空间自动抓取入库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
常用示例:
  添加 UP 并抓取:
    %(prog)s --add-and-run "https://space.bilibili.com/403375255" --attach --keep-open
  批量抓取未完成:
    %(prog)s --only-unfinished --attach --keep-open
""",
    )

    # --- 核心参数 ---
    parser.add_argument("urls", nargs="*", help="Bilibili UP 空间地址（直接模式）")
    queue_group = parser.add_mutually_exclusive_group()
    queue_group.add_argument("--add-and-run", metavar="URL", help="添加 UP 到 Excel 队列并立即抓取")
    queue_group.add_argument("--only-unfinished", action="store_true", help="批量处理 Excel 中未完成的 UP")
    browser_group = parser.add_mutually_exclusive_group()
    browser_group.add_argument("--attach", action="store_true", help="连接已打开的 Chrome（需 --remote-debugging-port）")
    parser.add_argument("--keep-open", action="store_true", help="完成后不关闭浏览器")

    # --- 可选调整 ---
    parser.add_argument("--pages", type=int, default=50, help="每个 UP 最多处理页数（默认 50）")
    parser.add_argument("--delay", default="1.0-3.0", metavar="SEC", help="随机等待秒数，单值或范围如 0.3-0.8（默认 1.0-3.0）")
    parser.add_argument("--write-db", action="store_true", help="队列模式下也写数据库（默认不写）")
    parser.add_argument("--excel", metavar="PATH", help="队列 Excel 路径（默认 bili_up_queue.xlsx）")

    # --- 高级选项（一般不需要改） ---
    adv = parser.add_argument_group("高级选项")
    adv.add_argument("--mode", choices=["space", "generic"], default="space", help="space=UP空间页 generic=通用翻页（默认 space）")
    adv.add_argument("--scrolls-per-page", type=int, default=4, help="每页滚动次数（默认 4）")
    adv.add_argument("--max-collections", type=int, help="每个 UP 最多处理多少个合集（默认全部，smoke test 可设 1）")
    adv.add_argument("--debug-port", type=int, default=9222, help="Chrome 调试端口（默认 9222）")
    browser_group.add_argument("--new-browser", action="store_true", help="Selenium 直接新开浏览器（不用 remote debugging）")
    adv.add_argument("--verbose", action="store_true", help="输出详细调试日志")
    # --write-db 已在主参数组定义
    adv.add_argument("--update-existing", action="store_true", help="去重命中时更新非空字段")
    adv.add_argument("--json-dump", type=Path, metavar="PATH", help="保存原始 B 站 JSON 响应（JSONL）")
    adv.add_argument("--mapped-dump", type=Path, metavar="PATH", help="保存映射后入库行（JSONL）")
    adv.add_argument("--guid-config-db", type=Path, default=DEFAULT_CXT_RPA_DB, metavar="PATH", help="CXT.RPA.db 路径")
    adv.add_argument("--mysql-host", default=DEFAULT_MYSQL_HOST, help="MySQL 地址（默认 192.168.1.2）")
    adv.add_argument("--mysql-port", type=int, default=DEFAULT_MYSQL_PORT, help="MySQL 端口（默认 3306）")
    adv.add_argument("--mysql-user", default=DEFAULT_MYSQL_USER, help="MySQL 用户")
    adv.add_argument("--mysql-password", default=DEFAULT_MYSQL_PASSWORD, help="MySQL 密码")
    adv.add_argument("--mysql-database", default=DEFAULT_MYSQL_DATABASE, help="MySQL 数据库名")

    args = parser.parse_args()

    # 解析 --delay 为 (min, max) 元组
    try:
        args.delay_min, args.delay_max = _parse_delay(args.delay)
    except ValueError as exc:
        parser.error(f"--delay 格式错误: {exc}; 示例: 1.0 或 0.3-0.8")

    queue_mode = bool(args.add_and_run or args.only_unfinished)
    if queue_mode and args.urls:
        parser.error("队列模式不能同时传 positional urls；请只使用 --add-and-run 或 --only-unfinished")
    # --write-db 统一控制是否写数据库
    if queue_mode and args.mapped_dump:
        parser.error("队列模式会自动写 tmp\\bili_{mid}_mapped.jsonl，不支持 --mapped-dump；直接模式才使用 --mapped-dump")
    if args.max_collections is not None and args.max_collections < 1:
        parser.error("--max-collections 必须是正整数")

    return args


def _setup_recorder(args, driver, force_capture: bool = False):
    """初始化 JSON 捕获 hook 和数据库写入器。"""
    global JSON_RECORDER

    if not (force_capture or args.json_dump or args.mapped_dump or args.write_db):
        print(f"[MODE] run_mode={getattr(args, 'run_mode', 'direct')} json_capture=False write_db=False mapped_dump=None")
        return

    mappings = load_guid_mappings(args.guid_config_db)
    db_writer = None
    if args.write_db:
        db_writer = MysqlMappedWriter(
            host=args.mysql_host,
            port=args.mysql_port,
            user=args.mysql_user,
            password=args.mysql_password,
            database=args.mysql_database,
            update_existing=args.update_existing,
        )
    JSON_RECORDER = JsonCaptureRecorder(
        json_dump=args.json_dump,
        mapped_dump=args.mapped_dump,
        mappings=mappings,
        db_writer=db_writer,
    )
    install_json_capture(driver)
    print(
        f"[MODE] run_mode={getattr(args, 'run_mode', 'direct')} "
        f"json_capture=True write_db={bool(args.write_db)} "
        f"update_existing={bool(args.update_existing)} raw_json_dump={args.json_dump} "
        f"mapped_dump={args.mapped_dump or 'per-up'}"
    )


def per_up_mapped_dump(mid: str, clear: bool = True) -> Path:
    path = Path("tmp") / f"bili_{mid}_mapped.jsonl"
    if clear and path.exists():
        path.unlink()
        print(f"[JSON-MAPPED] cleared previous dump path={path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _crawl_single_up(driver, args, url: str, mapped_dump: Path | None = None) -> bool:
    """对单个 UP 空间执行完整抓取流程。"""
    global JSON_RECORDER

    mid = extract_mid(url)
    if not mid:
        raise ValueError(f"不是 UP 空间地址: {url}")

    # 队列模式下按 UP 切换 mapped-dump，并重置内存去重，避免跨 UP 串文件或漏数据。
    if mapped_dump:
        if not JSON_RECORDER:
            print(f"[JSON-CAPTURE-WARN] 未初始化 recorder，无法写入 mapped_dump={mapped_dump}")
        elif not JSON_RECORDER.start_target(driver, mapped_dump, f"mid={mid}"):
            raise RuntimeError(f"无法清空 JSON 捕获缓冲，停止处理 mid={mid}")

    if args.mode == "space":
        run_space_pages(
            driver,
            urls=[url],
            pages=args.pages,
            scrolls_per_page=args.scrolls_per_page,
            delay_min=args.delay_min,
            delay_max=args.delay_max,
            max_collections=args.max_collections,
            verbose=args.verbose,
        )
    else:
        flush_json_capture(driver, "generic:before-open")
        driver.get(url)
        sleep_random(args.delay_min, args.delay_max)
        flush_json_capture(driver, "generic:after-open")
        run_generic_pages(
            driver,
            pages=args.pages,
            scrolls_per_page=args.scrolls_per_page,
            delay_min=args.delay_min,
            delay_max=args.delay_max,
        )
    if not flush_json_capture(driver, f"final:mid={mid}"):
        raise RuntimeError(f"final flush failed mid={mid}")
    return True


def main() -> None:
    global JSON_RECORDER

    args = parse_args()

    # --- 队列模式：--add-and-run ---
    if args.add_and_run:
        args.run_mode = "queue-add"
        url = args.add_and_run
        mid = extract_mid(url)
        if not mid:
            raise ValueError(f"无法从 URL 提取 mid: {url}")

        excel_path = Path(args.excel) if args.excel else default_bili_excel_path()
        space_url = normalize_space_home_url(url)

        # 获取 UP 名称
        name = fetch_up_name(mid)
        if name:
            print(f"[API] UP名称: {name}")
        else:
            name = mid
            print(f"[API] 未获取到名称，使用 mid={mid}")

        _, row_index = add_mid_to_excel(excel_path, mid, name, space_url)

        # 队列模式默认不写数据库，需显式传 --write-db
        if args.write_db:
            args.update_existing = True

        port = None if args.new_browser else args.debug_port
        driver = make_driver(port=port, launch=not args.attach and not args.new_browser)
        driver.implicitly_wait(5)
        _setup_recorder(args, driver, force_capture=True)

        try:
            mapped = per_up_mapped_dump(mid)
            _crawl_single_up(driver, args, space_url, mapped_dump=mapped)
            mark_mid_done_in_excel(excel_path, mid, row_index=row_index)
            print(f"[DONE] mid={mid} 抓取完成")
        finally:
            if JSON_RECORDER:
                JSON_RECORDER.close()
            if args.keep_open:
                print("[DONE] keep browser open")
            else:
                driver.quit()
        return

    # --- 队列模式：--only-unfinished ---
    if args.only_unfinished:
        args.run_mode = "queue-batch"
        targets = load_bili_targets(args)
        if not targets:
            print("[EXIT] 没有可处理的目标")
            return

        # 队列模式默认不写数据库，需显式传 --write-db
        if args.write_db:
            args.update_existing = True

        port = None if args.new_browser else args.debug_port
        driver = make_driver(port=port, launch=not args.attach and not args.new_browser)
        driver.implicitly_wait(5)
        _setup_recorder(args, driver, force_capture=True)

        excel_path = Path(args.excel) if args.excel else default_bili_excel_path()
        failed: list[str] = []

        try:
            for i, target in enumerate(targets):
                mid = target["mid"]
                url = target["url"]
                row_index = target["row_index"]
                print(f"\n[QUEUE] {i+1}/{len(targets)} mid={mid} name={target['name']}")

                try:
                    mapped = per_up_mapped_dump(mid)
                    _crawl_single_up(driver, args, url, mapped_dump=mapped)
                    mark_mid_done_in_excel(excel_path, mid, row_index=row_index)
                    print(f"[DONE] mid={mid} 抓取完成")
                except Exception as exc:
                    failed.append(mid)
                    print(
                        f"[FAIL] row={row_index + 2} mid={mid} name={target['name']!r} "
                        f"url={url} error_type={type(exc).__name__} error={exc}"
                    )
                    # 刷新捕获缓冲区，避免残留数据污染下一个 UP
                    try:
                        if not flush_json_capture(driver, f"fail:mid={mid}"):
                            print(f"[JSON-CAPTURE-WARN] mid={mid} 失败后 flush 未成功，下一轮会在 start_target 再次清空缓冲")
                    except Exception:
                        pass

            if failed:
                print(f"\n[SUMMARY] {len(targets) - len(failed)}/{len(targets)} 成功，失败: {failed}")
            else:
                print(f"\n[SUMMARY] {len(targets)}/{len(targets)} 全部成功")
        finally:
            if JSON_RECORDER:
                JSON_RECORDER.close()
            if args.keep_open:
                print("[DONE] keep browser open")
            else:
                driver.quit()
        return

    # --- 原有模式：直接传 URL ---
    if not args.urls:
        raise SystemExit(
            "没有传入 Bilibili URL。请使用 --add-and-run、--only-unfinished，"
            "或直接传入 https://space.bilibili.com/<mid>。"
        )
    args.run_mode = "direct"
    urls = args.urls
    if args.mapped_dump and args.mapped_dump.exists():
        args.mapped_dump.unlink()
        print(f"[JSON-MAPPED] cleared previous dump path={args.mapped_dump}")

    port = None if args.new_browser else args.debug_port
    driver = make_driver(port=port, launch=not args.attach and not args.new_browser)
    driver.implicitly_wait(5)
    _setup_recorder(args, driver)

    try:
        if args.mode == "space":
            run_space_pages(
                driver,
                urls=urls,
                pages=args.pages,
                scrolls_per_page=args.scrolls_per_page,
                delay_min=args.delay_min,
                delay_max=args.delay_max,
                max_collections=args.max_collections,
                verbose=args.verbose,
            )
        else:
            if urls:
                flush_json_capture(driver, "generic:before-open")
                driver.get(urls[0])
                sleep_random(args.delay_min, args.delay_max)
                flush_json_capture(driver, "generic:after-open")
            run_generic_pages(
                driver,
                pages=args.pages,
                scrolls_per_page=args.scrolls_per_page,
                delay_min=args.delay_min,
                delay_max=args.delay_max,
            )
        flush_json_capture(driver, "final")
    finally:
        if JSON_RECORDER:
            JSON_RECORDER.close()
        if args.keep_open:
            print("[DONE] keep browser open")
        else:
            driver.quit()


if __name__ == "__main__":
    main()
