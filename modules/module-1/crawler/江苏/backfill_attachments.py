"""用已缓存公告的 PDF 附件补全历史项目并同步 MySQL。"""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from attachments import enrich_from_attachments
from crawler import RAW_DIR, create_session, validate_project
from mysql_store import get_connection, sync_projects
from parser import parse_detail_html


CHECKPOINT = RAW_DIR.parents[1] / "clean" / "attachment_backfill_checkpoint.json"
WORKER_SESSION = None


def load_checkpoint():
    if not CHECKPOINT.exists():
        return {"completed": []}
    try:
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"completed": []}


def save_checkpoint(completed, totals):
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(
            {
                "completed": sorted(completed),
                "totals": totals,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def load_candidates():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        sql = """
            SELECT * FROM projects
            WHERE source_platform='江苏建设工程招标网'
              AND source_row_id IS NOT NULL
              AND (control_price IS NULL OR estimated_contract_amount IS NULL
                   OR provisional_sum IS NULL OR open_bid_time IS NULL)
            ORDER BY publish_time DESC, id DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def worker_session():
    global WORKER_SESSION
    if WORKER_SESSION is None:
        WORKER_SESSION = create_session()
    return WORKER_SESSION


def process_candidate(database_row):
    row_id = str(database_row["source_row_id"])
    raw_file = RAW_DIR / f"{row_id}.html"
    if not raw_file.exists():
        return row_id, None, [], "缺少原始HTML"

    html = raw_file.read_text(encoding="utf-8", errors="ignore")
    project = parse_detail_html(
        html,
        row_id=row_id,
        detail_url=database_row.get("source_url"),
        region_raw=database_row.get("region_raw"),
    )
    # 保留列表页/地区等数据库字段，避免回填附件时丢失现有信息。
    for key, value in database_row.items():
        if project.get(key) is None and value is not None:
            project[key] = value
    database_values = {key: database_row.get(key) for key in (
        "control_price", "estimated_contract_amount", "provisional_sum", "open_bid_time"
    )}
    enrich_from_attachments(
        project, html, database_row.get("source_url"), row_id, worker_session(), RAW_DIR,
        request_delay=0,
    )
    after = {key: project.get(key) for key in database_values}
    # 正文重解析得到的新金额与附件补出的金额都要入库；旧逻辑只比较附件
    # 处理前后，导致解析器升级后从正文识别出的金额被错误地忽略。
    changed = [
        key for key in database_values
        if database_values[key] != after[key] and after[key] is not None
    ]
    if not changed:
        return row_id, None, [], "附件无目标字段"

    quality = validate_project(project)
    project["data_quality_status"] = quality["quality_status"]
    project["quality_warnings"] = quality["warnings"]
    project["quality_errors"] = quality["errors"]
    project["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return row_id, project, changed, None


def main():
    parser = argparse.ArgumentParser(description="历史招标公告附件字段回填")
    parser.add_argument("--limit", type=int, help="本次最多处理多少条；不填则处理全部")
    parser.add_argument("--restart", action="store_true", help="忽略旧断点重新扫描")
    parser.add_argument("--workers", type=int, default=6, help="并发解析数，默认6")
    parser.add_argument("--batch-size", type=int, default=50, help="每批写入MySQL的项目数，默认50")
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers 必须在1到16之间")
    if args.batch_size < 1:
        parser.error("--batch-size 必须大于0")

    checkpoint = {"completed": []} if args.restart else load_checkpoint()
    completed = set(checkpoint.get("completed", []))
    totals = checkpoint.get("totals") or {"scanned": 0, "filled": 0, "failed": 0}

    candidates = [row for row in load_candidates() if str(row["source_row_id"]) not in completed]
    if args.limit:
        candidates = candidates[:args.limit]
    print(
        f"本次待扫描：{len(candidates)}，断点已完成：{len(completed)}，"
        f"并发数：{args.workers}，入库批次：{args.batch_size}",
        flush=True,
    )

    pending_projects = []
    pending_row_ids = []

    def flush_batch():
        if not pending_projects:
            return
        result = sync_projects(pending_projects)
        if result.get("failed"):
            raise RuntimeError(f"批量同步失败 {result['failed']} 条")
        totals["filled"] += len(pending_projects)
        completed.update(pending_row_ids)
        pending_projects.clear()
        pending_row_ids.clear()
        save_checkpoint(completed, totals)

    try:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            # map 的有序结果便于稳定保存断点；下载和PDF解析仍并发执行。
            for index, outcome in enumerate(executor.map(process_candidate, candidates), 1):
                row_id, project, changed, note = outcome
                totals["scanned"] += 1
                if project:
                    pending_projects.append(project)
                    pending_row_ids.append(row_id)
                    display = ",".join(changed)
                else:
                    completed.add(row_id)
                    display = note or "附件无目标字段"
                if len(pending_projects) >= args.batch_size:
                    flush_batch()
                elif index % args.batch_size == 0:
                    save_checkpoint(completed, totals)
                print(f"[{index}/{len(candidates)}] {row_id} {display}", flush=True)
        flush_batch()
    except KeyboardInterrupt:
        # 尚未提交数据库的项目不写入 completed，下次会安全重试。
        save_checkpoint(completed, totals)
        print("已停止，断点已保存。", flush=True)
        return
    except Exception as error:
        totals["failed"] += 1
        save_checkpoint(completed, totals)
        print(f"处理失败，断点已保存：{error}", flush=True)
        raise

    print(f"附件回填完成：{totals}", flush=True)


if __name__ == "__main__":
    main()
