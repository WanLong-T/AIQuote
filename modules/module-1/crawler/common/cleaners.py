import re
from datetime import datetime


# =========================================================
# 基础文本清洗
# =========================================================

def clean_text(value):
    if value is None:
        return None

    value = str(value)

    value = value.replace("\xa0", " ")

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    if not value:
        return None

    return value


# =========================================================
# 业主单位清洗
# =========================================================

INVALID_OWNER_VALUES = {
    "名称",
    "单位名称",
    "建设单位",
    "建设单位名称",
    "招标人",
    "招标人名称",
    "业主单位",
    "业主名称",
    "无",
    "-",
    "/",
}


def clean_owner_name(value):
    value = clean_text(value)

    if value is None:
        return None

    if value in INVALID_OWNER_VALUES:
        return None

    # 太短通常不是有效单位名称
    if len(value) < 3:
        return None

    # 明显是标签而非值
    if value.endswith("："):
        return None

    return value


# =========================================================
# 时间标准化
# 统一转换成：
# YYYY-MM-DD HH:MM:SS
# =========================================================

def normalize_datetime(value):
    value = clean_text(value)

    if not value:
        return None

    # -----------------------------------------
    # 2026年10月30日09时30分
    # -----------------------------------------

    pattern1 = re.search(
        r"(20\d{2})年"
        r"(\d{1,2})月"
        r"(\d{1,2})日"
        r"(?:\s*)"
        r"(\d{1,2})时"
        r"(\d{1,2})分",
        value,
    )

    if pattern1:
        year, month, day, hour, minute = (
            pattern1.groups()
        )

        try:
            dt = datetime(
                int(year),
                int(month),
                int(day),
                int(hour),
                int(minute),
            )

            return dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:
            return None

    # -----------------------------------------
    # 2026-11-11 9:00:00
    # -----------------------------------------

    pattern2 = re.search(
        r"(20\d{2})[-/]"
        r"(\d{1,2})[-/]"
        r"(\d{1,2})"
        r"\s+"
        r"(\d{1,2}):"
        r"(\d{1,2})"
        r"(?::(\d{1,2}))?",
        value,
    )

    if pattern2:
        groups = pattern2.groups()

        year = int(groups[0])
        month = int(groups[1])
        day = int(groups[2])
        hour = int(groups[3])
        minute = int(groups[4])

        second = (
            int(groups[5])
            if groups[5]
            else 0
        )

        try:
            dt = datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
            )

            return dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:
            return None

    # -----------------------------------------
    # 只有日期
    # -----------------------------------------

    pattern3 = re.search(
        r"(20\d{2})[-年/]"
        r"(\d{1,2})[-月/]"
        r"(\d{1,2})日?",
        value,
    )

    if pattern3:
        year, month, day = pattern3.groups()

        try:
            dt = datetime(
                int(year),
                int(month),
                int(day),
            )

            return dt.strftime(
                "%Y-%m-%d 00:00:00"
            )

        except ValueError:
            return None

    # 注意：
    # "2026"
    # "详见招标文件"
    # "止，"
    # 都不能作为有效日期

    return None


# =========================================================
# 金额标准化
# 最终全部转换成“元”
# =========================================================

def normalize_money(value):
    value = clean_text(value)

    if not value:
        return None

    # 必须同时出现数字和金额单位
    match = re.search(
        r"([\d,]+(?:\.\d+)?)"
        r"\s*"
        r"(亿元|万元|万|元)",
        value,
    )

    if not match:
        return None

    number_text = (
        match.group(1)
        .replace(",", "")
    )

    unit = match.group(2)

    try:
        number = float(number_text)
    except ValueError:
        return None

    if unit == "亿元":
        number *= 100_000_000

    elif unit in {
        "万元",
        "万",
    }:
        number *= 10_000

    # 元无需转换

    # 防止异常值
    if number <= 0:
        return None

    return round(number, 2)


# =========================================================
# 工程类型标准化
# =========================================================

def normalize_project_type(value):
    value = clean_text(value)

    if not value:
        return None

    mapping = {
        "房屋建筑工程": "房屋建筑施工",
        "房屋建筑施工": "房屋建筑施工",

        "市政工程施工": "市政工程施工",

        "单独装饰装修施工": "装饰装修",

        "园林绿化": "园林绿化",

        "工程监理": "工程监理",

        "设计": "设计",

        "材料设备采购": "材料设备采购",

        "电力": "电力",

        "水利": "水利",

        "机电设备": "机电设备",

        "其它": "其它",
    }

    return mapping.get(
        value,
        value,
    )


# =========================================================
# 项目名称清洗
# =========================================================

def clean_project_name(value):
    value = clean_text(value)

    if not value:
        return None

    # 列表页被截断，不能作为正式项目名
    if value.endswith("..."):
        return None

    if value.endswith("…"):
        return None

    return value