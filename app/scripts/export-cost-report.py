import base64
import io
import json
import sys
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


def number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def normalize_unit(value):
    return str(value or "").replace("m3", "m³").replace("m2", "m²")


def quota_rows(item):
    selections = item.get("quotaSelections") or []
    if selections:
        return selections
    codes = [part.strip() for part in str(item.get("quotaCode") or "").split("；") if part.strip()]
    names = [part.strip() for part in str(item.get("quotaName") or "").split("；")]
    if len(codes) > 1:
        share = len(codes)
        return [{
            "code": code,
            "name": names[index] if index < len(names) else "",
            "unit": item.get("unit"),
            "unitLabour": number(item.get("unitLabour")) / share,
            "unitMaterial": number(item.get("unitMaterial")) / share,
            "unitMachine": number(item.get("unitMachine")) / share,
        } for index, code in enumerate(codes)]
    if codes:
        return [{
            "code": codes[0], "name": names[0] if names else "", "unit": item.get("unit"),
            "unitLabour": item.get("unitLabour"), "unitMaterial": item.get("unitMaterial"),
            "unitMachine": item.get("unitMachine"),
        }]
    return []


def build_report(payload):
    result = payload.get("result") or {}
    items = result.get("items") or []
    manage_rate = number(payload.get("manageRate")) / 100
    profit_rate = number(payload.get("profitRate")) / 100
    code_counts = defaultdict(int)
    rows = []
    total_cost = 0.0

    for serial, item in enumerate(items, 1):
        code = str(item.get("listCode") or "-")
        display_code = code
        if code != "-":
            code_counts[code] += 1
            display_code = f"{code}{code_counts[code]:03d}"
        description = str(item.get("listName") or item.get("name") or "")
        features = str(item.get("features") or "").strip()
        if features and features not in description:
            description = f"{description}\n项目特征：{features}"
        confidence = number(item.get("confidence"))
        rows.append({
            "values": [serial, display_code, description, normalize_unit(item.get("unit")), number(item.get("quantity")), "", "", "", "", "", "", ""],
            "kind": "list", "unmatched": code == "-", "confidence": confidence,
        })

        quotas = quota_rows(item)
        if not quotas:
            rows.append({
                "values": ["", "-", "未匹配定额", normalize_unit(item.get("unit")), number(item.get("quantity")), "", "", "", "", "", "", ""],
                "kind": "quota", "unmatched": True, "confidence": confidence,
            })
            continue
        for quota in quotas:
            quantity = number(item.get("quantity"))
            labour_unit = number(quota.get("unitLabour"))
            material_unit = number(quota.get("unitMaterial"))
            machine_unit = number(quota.get("unitMachine"))
            direct_unit = labour_unit + material_unit + machine_unit
            management_unit = direct_unit * manage_rate
            profit_unit = (direct_unit + management_unit) * profit_rate
            unit_price = direct_unit + management_unit + profit_unit
            total_price = unit_price * quantity
            total_cost += total_price
            rows.append({
                "values": ["", str(quota.get("code") or "-"), str(quota.get("name") or ""), normalize_unit(quota.get("unit") or item.get("unit")), quantity,
                           unit_price, total_price, labour_unit * quantity, material_unit * quantity,
                           machine_unit * quantity, management_unit * quantity, profit_unit * quantity],
                "kind": "quota", "unmatched": not quota.get("code"), "confidence": confidence,
            })

    wb = Workbook()
    ws = wb.active
    ws.title = "工程量清单与计价表"
    ws.sheet_view.showGridLines = False
    base_widths = [8, 20, 50, 10, 14, 16, 18, 16, 16, 16, 16, 16]
    for index, width in enumerate(base_widths, 1):
        ws.column_dimensions[chr(64 + index)].width = width

    ws.merge_cells("A1:L1")
    title = ws["A1"]
    title.value = "工程量清单与计价表"
    title.font = Font(name="宋体", size=18, bold=True, color="1F4E79")
    title.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    for cell_range, value in [("A2:A3", "序号"), ("B2:B3", "项目编码"), ("C2:C3", "项目名称及特征描述"),
                              ("D2:D3", "计量单位"), ("E2:E3", "工程量"), ("F2:G2", "金额(元)"), ("H2:L2", "其中(元)")]:
        ws.merge_cells(cell_range)
        ws[cell_range.split(":")[0]] = value
    for column, value in enumerate(["综合单价", "合价", "人工费", "材料费", "机械费", "管理费", "利润"], 6):
        ws.cell(3, column, value)

    thin = Side(style="thin", color="496B85")
    medium = Side(style="medium", color="1F4E79")
    header_fill = PatternFill("solid", fgColor="1F4E79")
    for row in ws.iter_rows(min_row=2, max_row=3, min_col=1, max_col=12):
        for cell in row:
            cell.fill = header_fill
            cell.font = Font(name="宋体", size=10, color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for column in range(1, 13):
        ws.cell(3, column).border = Border(left=thin, right=thin, top=thin, bottom=medium)
    ws.row_dimensions[2].height = 24
    ws.row_dimensions[3].height = 24

    fills = {
        "list": PatternFill("solid", fgColor="E7F0FF"),
        "quota": PatternFill("solid", fgColor="F2F2F2"),
        "unmatched": PatternFill("solid", fgColor="FFE6E6"),
        "low": PatternFill("solid", fgColor="FFD966"),
    }
    for row_index, row_data in enumerate(rows, 4):
        for column, value in enumerate(row_data["values"], 1):
            cell = ws.cell(row_index, column, value)
            cell.font = Font(name="宋体", size=10)
            cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
            fill_key = "unmatched" if row_data["unmatched"] else ("low" if row_data["confidence"] < 65 else row_data["kind"])
            cell.fill = fills[fill_key]
            cell.alignment = Alignment(horizontal="right" if column >= 5 else ("left" if column == 3 else "center"),
                                       vertical="center", wrap_text=column == 3,
                                       indent=1 if column == 3 and row_data["kind"] == "quota" else 0)
            if column in range(5, 13) and isinstance(value, (int, float)):
                cell.number_format = "#,##0.00"
        ws.row_dimensions[row_index].height = 34 if "\n" in str(row_data["values"][2]) else 24

    # Excel displays #### when a numeric value is wider than its column.  Size
    # every numeric column from the longest formatted value in this export so
    # large quantities and amounts remain readable without manual adjustment.
    for column in range(5, 13):
        formatted_lengths = []
        for row_data in rows:
            value = row_data["values"][column - 1]
            if isinstance(value, (int, float)):
                formatted_lengths.append(len(f"{value:,.2f}"))
        required_width = (max(formatted_lengths) + 2) if formatted_lengths else base_widths[column - 1]
        ws.column_dimensions[chr(64 + column)].width = max(base_widths[column - 1], min(28, required_width))

    total_row = 4 + len(rows)
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=5)
    ws.merge_cells(start_row=total_row, start_column=6, end_row=total_row, end_column=12)
    ws.cell(total_row, 1, "工程总造价汇总")
    ws.cell(total_row, 6, total_cost)
    ws.cell(total_row, 6).number_format = "#,##0.00"
    ws.column_dimensions["F"].width = max(ws.column_dimensions["F"].width, min(28, len(f"{total_cost:,.2f}") + 2))
    total_fill = PatternFill("solid", fgColor="FFF2CC")
    for column in range(1, 13):
        cell = ws.cell(total_row, column)
        cell.fill = total_fill
        cell.font = Font(name="宋体", size=10, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(left=thin, right=thin, top=thin, bottom=medium)

    remark_row = total_row + 1
    ws.merge_cells(start_row=remark_row, start_column=1, end_row=remark_row, end_column=12)
    ws.cell(remark_row, 1, f"备注：按项目特征拆解必需工序，并以定额名称/工作内容进行最小集合覆盖；未覆盖、换算或缺少工作内容的结果必须复核。管理费率{manage_rate:.2%}，利润率{profit_rate:.2%}。红色=未匹配，橙色=低相似度。")
    ws.cell(remark_row, 1).font = Font(name="宋体", size=10, color="FF0000", italic=True)
    ws.cell(remark_row, 1).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[remark_row].height = 32
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:L{max(3, total_row - 1)}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = "1:3"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:L{remark_row}"

    output = io.BytesIO()
    wb.save(output)
    return base64.b64encode(output.getvalue()).decode("ascii")


def main():
    try:
        request = json.load(sys.stdin)
        print(json.dumps({"success": True, "fileBase64": build_report(request)}, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"success": False, "message": str(error)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
