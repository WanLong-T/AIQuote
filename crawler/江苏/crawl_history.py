"""江苏建设工程招标公告历史采集器。

按公告日期向前回溯，逐页解析、逐页同步 MySQL，并保存断点。
任务中断后重新运行会从下一页继续，不重复下载已缓存的详情页。
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from crawler import CLEAN_DIR, RAW_DIR, REJECTED_DIR, REQUEST_DELAY, save_json
from crawl_remaining import (
    decode_response,
    fetch_or_parse,
    parse_list_html,
    request_first_page,
    request_page,
)
from mysql_store import sync_projects


HISTORY_LIST_DIR = RAW_DIR / "历史列表页"
HISTORY_DATA_DIR = CLEAN_DIR / "history_pages"
HISTORY_REJECTED_DIR = REJECTED_DIR / "history_pages"
HISTORY_CHECKPOINT = CLEAN_DIR / "history_checkpoint.json"

for directory in (HISTORY_LIST_DIR, HISTORY_DATA_DIR, HISTORY_REJECTED_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def default_since():
    today = datetime.now().date()
    try:
        return today.replace(year=today.year - 3)
    except ValueError:
        return today.replace(year=today.year - 3, day=28)


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def load_checkpoint():
    if not HISTORY_CHECKPOINT.exists():
        return {"next_page": 1, "completed": [], "finished": False}
    try:
        return json.loads(HISTORY_CHECKPOINT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"next_page": 1, "completed": [], "finished": False}


def save_checkpoint(page, completed, since, finished=False, totals=None):
    save_json(
        {
            "next_page": page,
            "completed": sorted(completed),
            "since": since.isoformat(),
            "finished": finished,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "totals": totals or {},
        },
        HISTORY_CHECKPOINT,
    )


def get_page(page_number, previous_html, refresh=False, retries=3):
    cache = HISTORY_LIST_DIR / f"page-{page_number:05d}.html"
    if cache.exists() and not refresh:
        return cache.read_text(encoding="utf-8", errors="ignore")

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            html = request_first_page() if page_number == 1 else request_page(previous_html, page_number)
            cache.write_text(html, encoding="utf-8")
            return html
        except Exception as error:
            last_error = error
            wait_seconds = attempt * 10
            print(f"列表第 {page_number} 页请求失败（{attempt}/{retries}）：{error}，{wait_seconds}秒后重试。", flush=True)
            time.sleep(wait_seconds)
    raise RuntimeError(f"列表第 {page_number} 页连续请求失败：{last_error}")


def main():
    parser = argparse.ArgumentParser(description="近三年招标公告无人值守采集")
    parser.add_argument("--since", default=default_since().isoformat(), help="最早公告日期，格式 YYYY-MM-DD")
    parser.add_argument("--max-pages", type=int, default=5000, help="安全页数上限")
    parser.add_argument("--refresh-list", action="store_true", help="重新下载历史列表页")
    parser.add_argument("--restart", action="store_true", help="从第一页重新扫描，详情缓存仍会复用")
    args = parser.parse_args()

    since = parse_date(args.since)
    if not since:
        parser.error("--since 必须是 YYYY-MM-DD")
    if args.max_pages < 1:
        parser.error("--max-pages 必须大于0")

    checkpoint = load_checkpoint()
    range_changed = checkpoint.get("since") != since.isoformat()
    reset_progress = args.restart or range_changed
    start_page = 1 if reset_progress else int(checkpoint.get("next_page", 1))
    completed = set() if reset_progress else set(checkpoint.get("completed", []))
    totals = (
        {"parsed": 0, "synced": 0, "rejected": 0, "failed": 0}
        if reset_progress
        else checkpoint.get("totals") or {"parsed": 0, "synced": 0, "rejected": 0, "failed": 0}
    )

    previous_html = None
    if start_page > 1:
        previous_cache = HISTORY_LIST_DIR / f"page-{start_page - 1:05d}.html"
        if previous_cache.exists():
            previous_html = previous_cache.read_text(encoding="utf-8", errors="ignore")
        else:
            # ASP.NET 翻页依赖上一页 VIEWSTATE；缓存不存在时安全地从第一页恢复。
            start_page = 1

    print(f"历史采集启动：公告日期 >= {since.isoformat()}，从第 {start_page} 页开始。", flush=True)

    for page in range(start_page, args.max_pages + 1):
        try:
            html = get_page(page, previous_html, refresh=args.refresh_list)
            previous_html = html
            items = parse_list_html(html)
            if not items:
                save_checkpoint(page, completed, since, finished=True, totals=totals)
                print(f"第 {page} 页无公告，历史采集结束。", flush=True)
                return

            dated_items = [(item, parse_date(item.get("list_publish_date"))) for item in items]
            relevant = [item for item, date_value in dated_items if date_value is None or date_value >= since]
            page_dates = [date_value for _, date_value in dated_items if date_value]
            reached_boundary = bool(page_dates) and max(page_dates) < since

            batch = []
            rejected = []
            batch_completed = set()
            for index, item in enumerate(relevant, 1):
                row_id = item["row_id"]
                if row_id in completed:
                    continue
                try:
                    result = None
                    last_error = None
                    for attempt in range(1, 4):
                        try:
                            result = fetch_or_parse(item)
                            break
                        except Exception as error:
                            last_error = error
                            if attempt < 3:
                                wait_seconds = attempt * 5
                                print(
                                    f"[页{page}] {row_id} 请求失败（{attempt}/3），{wait_seconds}秒后重试。",
                                    flush=True,
                                )
                                time.sleep(wait_seconds)
                    if result is None:
                        raise RuntimeError(f"连续3次处理失败：{last_error}")
                    if not result.get("publish_time") and item.get("list_publish_date"):
                        result["publish_time"] = f"{item['list_publish_date']} 00:00:00"
                    totals["parsed"] = int(totals.get("parsed", 0)) + 1
                    if result.get("data_quality_status") == "REJECTED":
                        rejected.append(result)
                        totals["rejected"] = int(totals.get("rejected", 0)) + 1
                    else:
                        batch.append(result)
                    batch_completed.add(row_id)
                    print(
                        f"[页{page} {index}/{len(relevant)}] {result.get('project_name') or item.get('list_project_name')}",
                        flush=True,
                    )
                except Exception as error:
                    totals["failed"] = int(totals.get("failed", 0)) + 1
                    print(f"[页{page}] {row_id} 解析失败：{error}", file=sys.stderr, flush=True)

            # 先落盘，再入库；数据库异常时不推进断点，下次可从缓存重试。
            save_json(batch, HISTORY_DATA_DIR / f"page-{page:05d}.json")
            save_json(rejected, HISTORY_REJECTED_DIR / f"page-{page:05d}.json")
            if batch:
                db_result = sync_projects(batch)
                if db_result.get("failed"):
                    raise RuntimeError(f"第 {page} 页有 {db_result['failed']} 条数据库同步失败")
                totals["synced"] = int(totals.get("synced", 0)) + len(batch)

            completed.update(batch_completed)
            next_page = page + 1
            save_checkpoint(next_page, completed, since, finished=reached_boundary, totals=totals)
            print(f"第 {page} 页完成：有效 {len(batch)}，无效 {len(rejected)}，下一页 {next_page}。", flush=True)

            if reached_boundary:
                print(f"公告日期已早于 {since.isoformat()}，近三年历史采集完成。", flush=True)
                return
            time.sleep(REQUEST_DELAY)
        except KeyboardInterrupt:
            print("任务已中断，断点已保留；下次启动将继续。", flush=True)
            return
        except Exception as error:
            save_checkpoint(page, completed, since, finished=False, totals=totals)
            print(f"第 {page} 页失败，断点已保存：{error}", file=sys.stderr, flush=True)
            raise


if __name__ == "__main__":
    main()
