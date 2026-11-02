"""Read-only exporter for the legacy AIQuote project database.

The source folder is treated as evidence/data only.  This script never writes to
the legacy database and deliberately preserves source URLs and raw status fields.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"source database not found: {args.source}")
    args.output.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(f"file:{args.source.as_posix()}?mode=ro", uri=True)
    records: list[dict] = []
    for (payload,) in connection.execute("SELECT data FROM catalog_sections ORDER BY id"):
        row = json.loads(payload)
        records.append(
            {
                "province": row.get("province"),
                "city": row.get("city"),
                "district": row.get("district"),
                "project_name": row.get("project_name") or row.get("list_project_name"),
                "project_type": row.get("project_type"),
                "project_code": row.get("project_code"),
                "section_code": row.get("section_code"),
                "owner_name": row.get("owner_name"),
                "tenderer_name": row.get("tenderer_name"),
                "publish_time": row.get("publish_time"),
                "bid_deadline": row.get("bid_deadline"),
                "control_price": row.get("control_price"),
                "estimated_contract_amount": row.get("estimated_contract_amount"),
                "provisional_sum": row.get("provisional_sum"),
                "source_platform": row.get("source_platform"),
                "source_url": row.get("source_url"),
                "data_quality_status": row.get("data_quality_status"),
            }
        )

    fields = list(records[0]) if records else []
    with (args.output / "aiquote-projects.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (args.output / "aiquote-projects.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    by_province: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        by_province[row.get("province") or "未标注省份"].append(row)
    summary = []
    for province, rows in sorted(by_province.items(), key=lambda item: (-len(item[1]), item[0])):
        dates = [str(row["publish_time"]) for row in rows if row.get("publish_time")]
        summary.append(
            {
                "province": province,
                "project_count": len(rows),
                "earliest_publish_time": min(dates) if dates else None,
                "latest_publish_time": max(dates) if dates else None,
                "typed_project_count": sum(bool(row.get("project_type")) for row in rows),
                "source_platforms": dict(Counter(row.get("source_platform") or "未标注" for row in rows)),
            }
        )

    manifest = {
        "source_database": str(args.source),
        "source_mode": "read_only",
        "total_projects": len(records),
        "province_count": len(summary),
        "limitations": [
            "这是旧库快照，不代表当前全国完整项目库。",
            "仅导出 catalog_sections 中已标准化的项目；来源字段为空时保持为空。",
            "不得仅凭本导出覆盖当前生产库，导入前需按 source_url/section_code 去重并复核时效。",
        ],
        "province_summary": summary,
    }
    (args.output / "aiquote-province-summary.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"projects": len(records), "provinces": len(summary)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
