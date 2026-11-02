"""逐条核对缓存正文/附件中的明确控制价与 MySQL 数据。"""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path

from attachments import extract_pdf_text
from mysql_store import get_connection
from parser import extract_control_price, parse_detail_html


RAW_DIR = Path(__file__).resolve().parents[1] / "数据" / "raw" / "江苏"


def source_value(row):
    row_id = str(row["source_row_id"])
    html_path = RAW_DIR / f"{row_id}.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        project = parse_detail_html(html, row_id=row_id, detail_url=row.get("source_url"))
        if project.get("control_price") is not None:
            return row_id, project["control_price"], project.get("control_price_raw"), "正文", None

    attachment_dir = RAW_DIR / "attachments" / row_id
    for pdf in sorted(attachment_dir.glob("*.pdf")) if attachment_dir.exists() else []:
        try:
            found = extract_control_price(extract_pdf_text(pdf))
            if found["value"] is not None:
                return row_id, found["value"], found.get("raw"), f"附件:{pdf.name}", None
        except Exception as error:
            return row_id, None, None, None, f"{pdf.name}: {error}"
    return row_id, None, None, None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--report", default="数据/clean/control_price_audit.json")
    parser.add_argument("--apply-missing", action="store_true")
    parser.add_argument("--apply-report-only", action="store_true")
    args = parser.parse_args()

    report_path = Path(args.report)
    if args.apply_report_only:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        connection = get_connection()
        cursor = connection.cursor()
        updated = 0
        for item in report.get("missing", []):
            cursor.execute(
                "UPDATE projects SET control_price=%s, control_price_status=%s, "
                "control_price_raw=%s, updated_at=NOW() "
                "WHERE source_row_id=%s AND control_price IS NULL",
                (item["source_value"], "FOUND_FROM_AUDIT", f"[{item['source']}] {item['raw']}", item["row_id"]),
            )
            updated += cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        print(json.dumps({"report_missing": len(report.get("missing", [])), "updated": updated}, ensure_ascii=False))
        return

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT source_row_id, source_url, project_name, control_price, control_price_raw "
        "FROM projects WHERE source_platform='江苏建设工程招标网' AND source_row_id IS NOT NULL"
    )
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    by_id = {str(row["source_row_id"]): row for row in rows}

    explicit = []
    missing = []
    mismatched = []
    errors = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for index, result in enumerate(executor.map(source_value, rows), 1):
            row_id, value, raw, source, error = result
            if error:
                errors.append({"row_id": row_id, "error": error})
            if value is not None:
                row = by_id[row_id]
                item = {
                    "row_id": row_id,
                    "project_name": row["project_name"],
                    "source_value": float(value),
                    "database_value": float(row["control_price"]) if row["control_price"] is not None else None,
                    "source": source,
                    "raw": raw,
                }
                explicit.append(item)
                if row["control_price"] is None:
                    missing.append(item)
                elif abs(Decimal(str(row["control_price"])) - Decimal(str(value))) > Decimal("0.005"):
                    mismatched.append(item)
            if index % 250 == 0:
                print(f"[{index}/{len(rows)}] 明确值:{len(explicit)} 缺失:{len(missing)} 不一致:{len(mismatched)}", flush=True)

    report = {
        "scanned": len(rows),
        "explicit": len(explicit),
        "missing": missing,
        "mismatched": mismatched,
        "errors": errors,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.apply_missing and missing:
        connection = get_connection()
        cursor = connection.cursor()
        updated = 0
        for item in missing:
            cursor.execute(
                "UPDATE projects SET control_price=%s, control_price_status=%s, "
                "control_price_raw=%s, updated_at=NOW() "
                "WHERE source_row_id=%s AND control_price IS NULL",
                (
                    item["source_value"],
                    "FOUND_FROM_AUDIT",
                    f"[{item['source']}] {item['raw']}",
                    item["row_id"],
                ),
            )
            updated += cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        report["applied_missing"] = updated
    print(json.dumps({key: len(value) if isinstance(value, list) else value for key, value in report.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
