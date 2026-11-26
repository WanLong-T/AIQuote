import base64
import csv
import io
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook


ALIASES = {
    "resourceCode": ["资源编码", "材料编码", "编码", "code"],
    "resourceName": ["资源名称", "材料名称", "名称", "name"],
    "resourceType": ["资源类型", "类别", "类型", "type"],
    "specification": ["规格型号", "规格", "型号", "specification"],
    "unit": ["计量单位", "单位", "unit"],
    "unitPrice": ["含税单价", "除税单价", "单价", "价格", "unitprice"],
    "taxIncluded": ["是否含税", "含税", "taxincluded"],
    "taxRate": ["税率", "税率%", "taxrate"],
    "evidenceReference": ["证据来源", "来源", "备注", "evidence"],
}


def normalized(value):
    return re.sub(r"[\s_（）()\-—%]+", "", str(value or "").strip().lower())


def as_number(value):
    text = re.sub(r"[^0-9.\-]", "", str(value or "").replace(",", ""))
    try:
        return float(text) if text else None
    except ValueError:
        return None


def resource_type(value):
    value = normalized(value)
    if any(key in value for key in ["人工", "劳务", "labour", "labor"]):
        return "labour"
    if any(key in value for key in ["机械", "设备", "machine", "equipment"]):
        return "machine"
    return "material"


def tax_included(value, header):
    text = normalized(value)
    if "除税" in normalized(header) or text in {"否", "不含税", "false", "0"}:
        return False
    return True


def map_headers(headers):
    result = {}
    for field, aliases in ALIASES.items():
        choices = {normalized(alias) for alias in aliases}
        for index, header in enumerate(headers):
            if normalized(header) in choices:
                result[field] = index
                break
    return result


def parse_rows(rows, sheet_name):
    warnings = []
    header_index = 0
    mappings = {}
    for index, row in enumerate(rows[:20]):
        candidate = map_headers(row)
        if "resourceName" in candidate and "unitPrice" in candidate:
            header_index = index
            mappings = candidate
            break
    if not mappings:
        return [], [f"{sheet_name}：未找到包含资源名称和单价的表头"]
    headers = [str(value or "").strip() for value in rows[header_index]]
    resources = []
    for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
        def value(field):
            index = mappings.get(field)
            return row[index] if index is not None and index < len(row) else ""

        name = str(value("resourceName") or "").strip()
        price = as_number(value("unitPrice"))
        if not name and price is None:
            continue
        if not name or price is None or price < 0:
            warnings.append(f"{sheet_name}第{row_number}行：名称或单价无效，已跳过")
            continue
        code = str(value("resourceCode") or "").strip() or f"AUTO-{sheet_name}-{row_number}"
        tax_rate = as_number(value("taxRate")) or 0
        resources.append(
            {
                "resourceCode": code,
                "resourceName": name,
                "resourceType": resource_type(value("resourceType")),
                "specification": str(value("specification") or "").strip(),
                "unit": str(value("unit") or "").strip() or "项",
                "unitPrice": price,
                "taxIncluded": tax_included(value("taxIncluded"), headers[mappings["unitPrice"]]),
                "taxRate": tax_rate,
                "evidenceReference": str(value("evidenceReference") or "").strip(),
                "sourceSheet": sheet_name,
                "sourceRow": row_number,
            }
        )
    return resources, warnings


def main():
    payload = json.load(sys.stdin)
    file_name = str(payload.get("fileName") or "")
    raw = base64.b64decode(payload.get("fileBase64") or "")
    suffix = Path(file_name).suffix.lower()
    sheets = []
    if suffix == ".csv":
        text = raw.decode("utf-8-sig", errors="replace")
        sheets.append(("CSV", list(csv.reader(io.StringIO(text)))))
    elif suffix in {".xlsx", ".xlsm"}:
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        for worksheet in workbook.worksheets:
            sheets.append((worksheet.title, [list(row) for row in worksheet.iter_rows(values_only=True)]))
    else:
        raise ValueError("仅支持xlsx、xlsm和csv价格文件")
    resources = []
    warnings = []
    for sheet_name, rows in sheets:
        parsed, sheet_warnings = parse_rows(rows, sheet_name)
        resources.extend(parsed)
        warnings.extend(sheet_warnings)
    seen = set()
    unique = []
    for item in resources:
        if item["resourceCode"] in seen:
            warnings.append(f"资源编码重复：{item['resourceCode']}，仅保留首次出现记录")
            continue
        seen.add(item["resourceCode"])
        unique.append(item)
    print(json.dumps({"success": True, "data": {"resources": unique, "warnings": warnings}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"success": False, "message": str(error)}, ensure_ascii=False))
        sys.exit(1)
