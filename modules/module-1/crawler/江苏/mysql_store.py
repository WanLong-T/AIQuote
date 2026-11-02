import json
import os
from datetime import datetime
from pathlib import Path

import mysql.connector


DB_HOST = os.getenv("BIDDING_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("BIDDING_DB_PORT", "3306"))
DB_USER = os.getenv("BIDDING_DB_USER", "root")
DB_NAME = os.getenv("BIDDING_DB_NAME", "bidding_system")


def get_connection():
    password = os.getenv("BIDDING_DB_PASSWORD")
    if not password:
        raise RuntimeError("没有找到环境变量 BIDDING_DB_PASSWORD")
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=password,
        database=DB_NAME,
        charset="utf8mb4",
        use_unicode=True,
    )


def normalize_datetime(value):
    if not value or isinstance(value, datetime):
        return value or None
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def to_json_text(value):
    if value is None:
        value = []
    if not isinstance(value, (list, dict)):
        value = [str(value)]
    return json.dumps(value, ensure_ascii=False)


def normalize_project_name(project):
    def clean(value):
        return " ".join(str(value or "").split()).strip()

    name = clean(project.get("project_name"))
    parent = clean(project.get("parent_project_name"))
    listed = clean(project.get("list_project_name"))
    if listed and "..." not in listed and "…" not in listed:
        return listed
    if not parent:
        return name or listed
    if not name:
        return parent or listed
    if parent in name:
        return name
    if name in parent:
        return parent
    for size in range(min(len(parent), len(name)), 2, -1):
        if parent[-size:] == name[:size]:
            return parent + name[size:]
    return parent + name


def find_existing_project_id(cursor, project):
    platform = project.get("source_platform")
    row_id = project.get("source_row_id")
    if not platform or not row_id:
        return None
    # 官网一行对应数据库一行。项目编号和标段编号均可能在多条公告中重复，
    # 只有官网 RowID 能标识本次公告，不能用父项目编号覆盖其他标段。
    cursor.execute(
        "SELECT id FROM projects WHERE source_platform=%s AND source_row_id=%s ORDER BY id DESC LIMIT 1",
        (platform, row_id),
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    return None


def build_values(project):
    main_entity_name = (
        project.get("main_entity_name")
        or project.get("owner_name")
        or project.get("tenderer_name")
    )
    main_entity_type = project.get("main_entity_type")
    if not main_entity_type and main_entity_name:
        main_entity_type = "OWNER" if project.get("owner_name") else "TENDERER"
    row_id = project.get("source_row_id")
    raw_file_path = str(Path("raw") / "江苏" / f"{row_id}.html") if row_id else None
    values = dict(project)
    values.update(
        project_name=normalize_project_name(project),
        main_entity_name=main_entity_name,
        main_entity_type=main_entity_type,
        publish_time=normalize_datetime(project.get("publish_time")),
        open_bid_time=normalize_datetime(project.get("open_bid_time")),
        bid_deadline=normalize_datetime(project.get("bid_deadline")),
        tracking_stage=project.get("tracking_stage") or "LEAD",
        rating=project.get("rating") or "UNRATED",
        raw_file_path=raw_file_path,
        quality_warnings=to_json_text(project.get("quality_warnings")),
        quality_errors=to_json_text(project.get("quality_errors")),
        crawl_time=normalize_datetime(project.get("crawl_time")) or datetime.now(),
    )
    for field in (
        "project_id", "project_name", "parent_project_name", "project_code", "section_code",
        "project_type", "province", "city", "district", "region_raw", "owner_name",
        "tenderer_name", "control_price", "control_price_status", "control_price_raw",
        "estimated_contract_amount", "estimated_contract_amount_source",
        "estimated_contract_amount_confidence", "estimated_contract_amount_raw",
        "provisional_sum", "provisional_sum_status", "provisional_sum_raw",
        "responsible_person", "source_platform", "source_row_id", "source_url",
        "list_project_name", "data_quality_status",
    ):
        values.setdefault(field, None)
    # mysql-connector 会尝试转换参数字典中的所有值，即使 SQL 未引用该键。
    # 附件解析会携带 filled_fields/errors 等列表型审计信息，因此这里只把
    # projects 表实际使用的列交给驱动，避免“Python type list cannot be converted”。
    return {name: values.get(name) for name in COLUMNS}


COLUMNS = (
    "project_id", "project_name", "parent_project_name", "project_code", "section_code",
    "project_type", "province", "city", "district", "region_raw", "owner_name",
    "tenderer_name", "main_entity_name", "main_entity_type", "publish_time", "open_bid_time",
    "bid_deadline", "control_price", "control_price_status", "control_price_raw",
    "estimated_contract_amount", "estimated_contract_amount_source",
    "estimated_contract_amount_confidence", "estimated_contract_amount_raw", "provisional_sum",
    "provisional_sum_status", "provisional_sum_raw", "tracking_stage", "rating",
    "responsible_person", "source_platform", "source_row_id", "source_url", "list_project_name",
    "raw_file_path", "data_quality_status", "quality_warnings", "quality_errors", "crawl_time",
)


def insert_project(cursor, project):
    values = build_values(project)
    columns = ", ".join(COLUMNS)
    placeholders = ", ".join(f"%({name})s" for name in COLUMNS)
    cursor.execute(f"INSERT INTO projects ({columns}) VALUES ({placeholders})", values)


def update_project(cursor, database_id, project):
    values = build_values(project)
    values["database_id"] = database_id
    # 人工业务字段 tracking_stage/rating/responsible_person 不允许被爬虫覆盖。
    protected = {"tracking_stage", "rating", "responsible_person"}
    # 官网字段可能分散在正文、附件或后续发布的控制价文件中。一次刷新没有
    # 解析到值时，不能用 NULL 覆盖历史上已经抓到的金额及其来源审计信息。
    preserve_when_empty = {
        "control_price", "control_price_status", "control_price_raw",
        "estimated_contract_amount", "estimated_contract_amount_source",
        "estimated_contract_amount_confidence", "estimated_contract_amount_raw",
        "provisional_sum", "provisional_sum_status", "provisional_sum_raw",
    }
    assignments = ", ".join(
        f"{name}=COALESCE(%({name})s, {name})" if name in preserve_when_empty
        else f"{name}=%({name})s"
        for name in COLUMNS if name not in protected
    )
    cursor.execute(f"UPDATE projects SET {assignments} WHERE id=%(database_id)s", values)


def sync_projects(projects):
    connection = get_connection()
    cursor = connection.cursor()
    inserted = updated = skipped = failed = 0
    print("\n======================================\n开始同步 MySQL\n======================================")
    try:
        for index, project in enumerate(projects, start=1):
            name = project.get("project_name") or "未命名项目"
            if project.get("data_quality_status") == "REJECTED":
                skipped += 1
                continue
            try:
                existing_id = find_existing_project_id(cursor, project)
                if existing_id:
                    update_project(cursor, existing_id, project)
                    updated += 1
                    action = "更新"
                else:
                    insert_project(cursor, project)
                    inserted += 1
                    action = "新增"
                print(f"[{index}/{len(projects)}] {action}：{name}")
            except Exception as error:
                failed += 1
                print(f"[{index}/{len(projects)}] MySQL同步失败：{name} / {error}")
        connection.commit()
        cursor.execute("SELECT COUNT(*) FROM projects")
        total = cursor.fetchone()[0]
        result = {"inserted": inserted, "updated": updated, "skipped": skipped, "failed": failed, "total": total}
        print(f"MySQL同步完成：{result}")
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
