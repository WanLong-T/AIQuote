import base64
import csv
import io
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook


ALIASES = {
    "quotaCode": ["定额编码", "定额编号", "quota code", "quotacode"],
    "resourceCode": ["资源编码", "人材机编码", "材料编码", "resource code", "resourcecode"],
    "resourceName": ["资源名称", "人材机名称", "材料名称", "resource name", "resourcename"],
    "resourceType": ["资源类型", "人材机类型", "类别", "resource type", "resourcetype"],
    "unit": ["单位", "计量单位", "unit"],
    "consumption": ["消耗量", "定额含量", "含量", "consumption"],
    "sourceReference": ["来源依据", "来源", "证据", "source", "evidence"],
}


def normalized(value):
    return re.sub(r"[\s_\-—（）()、，,；;:/]+", "", str(value or "").strip().lower())


def column_map(headers):
    result = {}
    for index, header in enumerate(headers):
        key = normalized(header)
        for field, aliases in ALIASES.items():
            if field not in result and any(normalized(alias) == key for alias in aliases):
                result[field] = index
    return result


def number(value):
    cleaned = re.sub(r"[^0-9.\-]", "", str(value or "").replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def resource_type(value):
    key = normalized(value)
    if key in {"人工", "人工费", "工日", "labour", "labor"}:
        return "labour"
    if key in {"材料", "材料费", "主材", "辅材", "material"}:
        return "material"
    if key in {"机械", "机械费", "机械台班", "machine"}:
        return "machine"
    return ""


def parse_rows(rows, source_name):
    warnings = []
    if not rows:
        return [], [f"{source_name}没有可读取的数据"]
    header_index = next((i for i, row in enumerate(rows[:30]) if len(column_map(row)) >= 4), -1)
    if header_index < 0:
        return [], [f"{source_name}未识别到定额编码、资源编码、名称、类型、单位、消耗量等必要表头"]
    headers = rows[header_index]
    mapping = column_map(headers)
    required = {"quotaCode", "resourceCode", "resourceName", "resourceType", "unit", "consumption"}
    missing = required - set(mapping)
    if missing:
        return [], [f"{source_name}缺少字段：{'、'.join(sorted(missing))}"]
    result = []
    for row_no, row in enumerate(rows[header_index + 1 :], header_index + 2):
        get = lambda field: row[mapping[field]] if mapping[field] < len(row) else ""
        quota_code = str(get("quotaCode") or "").strip()
        code = str(get("resourceCode") or "").strip()
        name = str(get("resourceName") or "").strip()
        kind = resource_type(get("resourceType"))
        unit = str(get("unit") or "").strip()
        consumption = number(get("consumption"))
        if not any([quota_code, code, name]):
            continue
        if not quota_code or not code or not name or not kind or not unit or consumption <= 0:
            warnings.append(f"{source_name}第{row_no}行数据不完整或消耗量不大于0，已跳过")
            continue
        result.append({
            "quotaCode": quota_code,
            "resourceCode": code,
            "resourceName": name,
            "resourceType": kind,
            "unit": unit,
            "consumption": consumption,
            "sourceReference": str(get("sourceReference") or "").strip() if "sourceReference" in mapping else "",
            "sourceSheet": source_name,
            "sourceRow": row_no,
        })
    return result, warnings


def main(payload):
    file_name = str(payload.get("fileName") or "")
    raw = base64.b64decode(payload.get("fileBase64") or "")
    suffix = Path(file_name).suffix.lower()
    all_rows, warnings = [], []
    if suffix == ".csv":
        text = raw.decode("utf-8-sig", errors="replace")
        rows, row_warnings = parse_rows(list(csv.reader(io.StringIO(text))), Path(file_name).name)
        all_rows.extend(rows)
        warnings.extend(row_warnings)
    elif suffix in {".xlsx", ".xlsm"}:
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        for sheet in workbook.worksheets:
            matrix = [[cell if cell is not None else "" for cell in row] for row in sheet.iter_rows(values_only=True)]
            rows, row_warnings = parse_rows(matrix, sheet.title)
            all_rows.extend(rows)
            warnings.extend(row_warnings)
    else:
        raise ValueError("定额消耗量仅支持xlsx、xlsm和csv文件")
    if not all_rows:
        raise ValueError("文件中没有识别到有效的定额人材机消耗量")
    return {"success": True, "data": {"consumptions": all_rows, "warnings": warnings}}


if __name__ == "__main__":
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        print(json.dumps(main(payload), ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False))
