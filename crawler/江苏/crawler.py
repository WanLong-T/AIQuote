import re
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import (
    urljoin,
    urlparse,
    parse_qs,
)

import pandas as pd
import requests
import urllib3

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from parser import parse_detail_html
from attachments import enrich_from_attachments
from mysql_store import sync_projects


# =========================================================
# 基础配置
# =========================================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


BASE_URL = (
    "http://www.jszb.com.cn/jszb/YW_info/"
    "ZhaoBiaoGG/"
)


LIST_URL = urljoin(
    BASE_URL,
    "MoreInfo_ZBGG.aspx",
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/152.0.0.0 "
        "Safari/537.36"
    ),

    "Accept-Language":
        "zh-CN,zh;q=0.9",
}


# 每个详情页之间暂停
REQUEST_DELAY = 0.8


# =========================================================
# 项目目录
# =========================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


DATA_DIR = (
    ROOT_DIR
    / "数据"
)


RAW_DIR = (
    DATA_DIR
    / "raw"
    / "江苏"
)


CLEAN_DIR = (
    DATA_DIR
    / "clean"
)


REJECTED_DIR = (
    DATA_DIR
    / "rejected"
)


RAW_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


CLEAN_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


REJECTED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# requests Session
# =========================================================

def create_session():

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    retry = Retry(
        total=3,
        connect=3,
        read=3,

        backoff_factor=1,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],

        allowed_methods=[
            "GET",
        ],
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session.mount(
        "http://",
        adapter,
    )

    session.mount(
        "https://",
        adapter,
    )

    return session


SESSION = create_session()


# =========================================================
# 基础文本处理
# =========================================================

def clean_text(value):

    if value is None:
        return None

    value = str(value)

    value = value.replace(
        "\xa0",
        " ",
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value or None


def compose_official_project_name(project):
    """生成与官网列表一致的完整公告名称。"""
    name = clean_text(project.get("project_name")) or ""
    parent = clean_text(project.get("parent_project_name")) or ""
    listed = clean_text(project.get("list_project_name")) or ""

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


# =========================================================
# 获取 HTML
# =========================================================

def get_html(url):

    print(
        f"访问：{url}"
    )

    response = SESSION.get(
        url,
        timeout=35,
        verify=False,
    )

    print(
        "状态码：",
        response.status_code,
    )

    response.raise_for_status()

    if (
        response.encoding is None
        or response.encoding.lower()
        == "iso-8859-1"
    ):
        response.encoding = (
            response.apparent_encoding
        )

    return response.text


# =========================================================
# 江苏行政区划
# =========================================================

REGION_MAP = {

    # 南京
    "南京": (
        "南京市",
        None,
    ),

    "南京市": (
        "南京市",
        None,
    ),

    # 无锡
    "无锡": (
        "无锡市",
        None,
    ),

    "宜兴": (
        "无锡市",
        "宜兴市",
    ),

    "江阴": (
        "无锡市",
        "江阴市",
    ),

    # 徐州
    "徐州": (
        "徐州市",
        None,
    ),

    "铜山": (
        "徐州市",
        "铜山区",
    ),

    "丰县": (
        "徐州市",
        "丰县",
    ),

    "沛县": (
        "徐州市",
        "沛县",
    ),

    "睢宁": (
        "徐州市",
        "睢宁县",
    ),

    "邳州": (
        "徐州市",
        "邳州市",
    ),

    "新沂": (
        "徐州市",
        "新沂市",
    ),

    # 常州
    "常州": (
        "常州市",
        None,
    ),

    # 苏州
    "苏州": (
        "苏州市",
        None,
    ),

    "吴江": (
        "苏州市",
        "吴江区",
    ),

    "苏州工业园区": (
        "苏州市",
        "苏州工业园区",
    ),

    "昆山": (
        "苏州市",
        "昆山市",
    ),

    "常熟": (
        "苏州市",
        "常熟市",
    ),

    "张家港": (
        "苏州市",
        "张家港市",
    ),

    "太仓": (
        "苏州市",
        "太仓市",
    ),

    # 南通
    "南通": (
        "南通市",
        None,
    ),

    # 连云港
    "连云港": (
        "连云港市",
        None,
    ),

    "连云港市": (
        "连云港市",
        None,
    ),

    "灌南": (
        "连云港市",
        "灌南县",
    ),

    "灌云": (
        "连云港市",
        "灌云县",
    ),

    "东海": (
        "连云港市",
        "东海县",
    ),

    # 淮安
    "淮安": (
        "淮安市",
        None,
    ),

    "淮安市": (
        "淮安市",
        None,
    ),

    # 盐城
    "盐城": (
        "盐城市",
        None,
    ),

    # 扬州
    "扬州": (
        "扬州市",
        None,
    ),

    "扬州市": (
        "扬州市",
        None,
    ),

    "江都": (
        "扬州市",
        "江都区",
    ),

    "高邮": (
        "扬州市",
        "高邮市",
    ),

    "仪征": (
        "扬州市",
        "仪征市",
    ),

    "宝应": (
        "扬州市",
        "宝应县",
    ),

    # 镇江
    "镇江": (
        "镇江市",
        None,
    ),

    "扬中": (
        "镇江市",
        "扬中市",
    ),

    "句容": (
        "镇江市",
        "句容市",
    ),

    "丹阳": (
        "镇江市",
        "丹阳市",
    ),

    # 泰州
    "泰州": (
        "泰州市",
        None,
    ),

    "泰兴": (
        "泰州市",
        "泰兴市",
    ),

    "靖江": (
        "泰州市",
        "靖江市",
    ),

    "兴化": (
        "泰州市",
        "兴化市",
    ),

    # 宿迁
    "宿迁": (
        "宿迁市",
        None,
    ),

    "宿迁市": (
        "宿迁市",
        None,
    ),

    # 省属
    "省属": (
        None,
        None,
    ),
}


def normalize_region(
    region_raw
):

    region_raw = clean_text(
        region_raw
    )

    if not region_raw:

        return {
            "city": None,
            "district": None,
        }

    result = REGION_MAP.get(
        region_raw
    )

    if result:

        return {
            "city": result[0],
            "district": result[1],
        }

    # 本身已经是某某市
    if region_raw.endswith(
        "市"
    ):

        return {
            "city": region_raw,
            "district": None,
        }

    return {
        "city": None,
        "district": None,
    }


# =========================================================
# 解析第一页列表
# =========================================================

def parse_list_page():

    html = get_html(
        LIST_URL
    )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    projects = []

    for a in soup.find_all(
        "a"
    ):

        onclick = a.get(
            "onclick",
            "",
        )

        if (
            "ViewReportDetail.aspx"
            not in onclick
        ):
            continue

        title_raw = clean_text(
            a.get_text(
                " ",
                strip=True,
            )
        )

        if not title_raw:
            continue

        # -------------------------------------
        # 提取 onclick 中详情页地址
        # -------------------------------------

        match = re.search(
            r'window\.open\('
            r'["\']'
            r'([^"\']*'
            r'ViewReportDetail\.aspx'
            r'[^"\']*)',
            onclick,
            re.I,
        )

        if not match:
            continue

        relative_url = (
            match.group(1)
        )

        detail_url = urljoin(
            LIST_URL,
            relative_url,
        )

        # -------------------------------------
        # RowID
        # -------------------------------------

        parsed = urlparse(
            detail_url
        )

        query = parse_qs(
            parsed.query
        )

        row_id = query.get(
            "RowID",
            [None],
        )[0]

        if not row_id:
            continue

        # -------------------------------------
        # 地区
        #
        # [江都]项目名称
        # -------------------------------------

        region_match = re.match(
            r"^\[([^\]]+)\]",
            title_raw,
        )

        region_raw = (
            region_match.group(1)
            if region_match
            else None
        )

        # -------------------------------------
        # 列表项目名称
        # -------------------------------------

        list_project_name = re.sub(
            r"^\[[^\]]+\]",
            "",
            title_raw,
        ).strip()

        projects.append(
            {
                "row_id":
                    row_id,

                "region_raw":
                    region_raw,

                "list_project_name":
                    list_project_name,

                "detail_url":
                    detail_url,
            }
        )

    # -----------------------------------------
    # 第一级去重：
    # 列表页按 RowID 去重
    # -----------------------------------------

    unique = []

    seen = set()

    for project in projects:

        row_id = project[
            "row_id"
        ]

        if row_id in seen:
            continue

        seen.add(
            row_id
        )

        unique.append(
            project
        )

    return unique


# =========================================================
# 保存原始 HTML
# =========================================================

def save_raw_html(
    row_id,
    html,
):

    file_path = (
        RAW_DIR
        / f"{row_id}.html"
    )

    file_path.write_text(
        html,
        encoding="utf-8",
    )

    return file_path


# =========================================================
# 数据质量检查
# =========================================================

def validate_project(
    project
):

    errors = []
    warnings = []

    # =========================================
    # 必须字段
    #
    # 缺失后数据无法识别，因此 REJECTED
    # =========================================

    if not project.get(
        "project_name"
    ):
        errors.append(
            "缺少项目名称"
        )

    # 不同地区、不同公告模板不一定披露项目编号。只要源站公告ID或
    # 标段/项目编号至少存在一个，就可以稳定去重，不应直接丢弃。
    if not any(project.get(field) for field in (
        "source_row_id", "section_code", "project_code"
    )):
        errors.append("缺少可用于识别项目的编号")
    elif not project.get("project_code"):
        warnings.append("缺少项目编号")

    if not project.get(
        "source_url"
    ):
        errors.append(
            "缺少来源URL"
        )

    # =========================================
    # 重要业务字段
    #
    # 缺失不删除项目，但标记 PARTIAL
    # =========================================

    if not project.get(
        "project_type"
    ):
        warnings.append(
            "缺少工程类型"
        )

    if not project.get(
        "publish_time"
    ):
        warnings.append(
            "缺少公告发布时间"
        )

    if (
     not project.get("owner_name")
     and not project.get("tenderer_name")
):
     warnings.append(
        "缺少项目业主及招标人"
    )

    if not project.get(
        "bid_deadline"
    ):
        warnings.append(
            "缺少投标截止时间"
        )

    if (
        not project.get(
            "city"
        )
        and project.get(
            "region_raw"
        )
        != "省属"
    ):
        warnings.append(
            "缺少标准城市"
        )

    # =========================================
    # 项目名称检查
    # =========================================

    project_name = (
        project.get(
            "project_name"
        )
        or ""
    )

    if (
        project_name.endswith(
            "..."
        )
        or project_name.endswith(
            "…"
        )
    ):
        errors.append(
            "项目名称被截断"
        )

    # =========================================
    # 日期格式检查
    # =========================================

    datetime_fields = [
        "publish_time",
        "open_bid_time",
        "bid_deadline",
    ]

    datetime_pattern = re.compile(
        r"^20\d{2}-"
        r"\d{2}-"
        r"\d{2}"
        r"(?: "
        r"\d{2}:"
        r"\d{2}:"
        r"\d{2})?$"
    )

    for field in datetime_fields:

        value = project.get(
            field
        )

        if value is None:
            continue

        if not datetime_pattern.match(
            str(value)
        ):
            errors.append(
                f"{field}格式错误"
            )

    # 截止/开标时间不可能早于公告发布时间。宁可留空等待复核，
    # 也不能把正文中的历史年份当成业务截止时间写入数据库。
    publish_value = project.get("publish_time")
    if publish_value:
        try:
            publish_dt = datetime.strptime(str(publish_value), "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            publish_dt = None
        if publish_dt:
            for field, label in (("bid_deadline", "投标截止时间"), ("open_bid_time", "开标时间")):
                value = project.get(field)
                if not value:
                    continue
                try:
                    value_dt = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
                except (TypeError, ValueError):
                    continue
                if value_dt <= publish_dt:
                    project[field] = None
                    warnings.append(f"{label}早于或等于公告发布时间，已清空待复核")

    # =========================================
    # 金额检查
    # =========================================

    money_fields = [
        "control_price",
        "estimated_contract_amount",
        "provisional_sum",
    ]

    for field in money_fields:

        value = project.get(
            field
        )

        if value is None:
            continue

        if not isinstance(
            value,
            (int, float),
        ):

            errors.append(
                f"{field}不是数字"
            )

            continue

        if value <= 0:

            errors.append(
                f"{field}金额异常"
            )

    # =========================================
    # 数据等级
    # =========================================

    if errors:

        quality_status = (
            "REJECTED"
        )

    elif warnings:

        quality_status = (
            "PARTIAL"
        )

    else:

        quality_status = (
            "VALID"
        )

    return {
        "errors":
            errors,

        "warnings":
            warnings,

        "quality_status":
            quality_status,
    }


# =========================================================
# 第二级去重
#
# 按标段编号去重
# =========================================================

def deduplicate_projects(
    projects
):
    """
    官网列表中的每一个 RowID 都是一条独立公告。

    项目编号、标段编号可以重复，不能用它们合并公告；这里只防止
    同一个 RowID 因重复翻页被加入两次。
    """

    result = {}

    for project in projects:

        key = project.get("source_row_id")

        if not key:
            continue

        result[str(key)] = project

    return list(
        result.values()
    )


# =========================================================
# 单个项目处理
# =========================================================

def process_project(
    project
):

    row_id = project[
        "row_id"
    ]

    detail_url = project[
        "detail_url"
    ]

    region_raw = project[
        "region_raw"
    ]

    print(
        "\n======================================"
    )

    print(
        f"处理项目：{row_id}"
    )

    print(
        "列表名称：",
        project[
            "list_project_name"
        ],
    )

    # -----------------------------------------
    # 获取详情页
    # -----------------------------------------

    html = get_html(
        detail_url
    )

    # -----------------------------------------
    # 保存原始 HTML
    # -----------------------------------------

    raw_path = save_raw_html(
        row_id,
        html,
    )

    print(
        "原始HTML：",
        raw_path,
    )

    # -----------------------------------------
    # 调用 parser.py
    # -----------------------------------------

    result = parse_detail_html(
        html,
        row_id=row_id,
        detail_url=detail_url,
        region_raw=region_raw,
    )

    result = enrich_from_attachments(
        result, html, detail_url, row_id, SESSION, RAW_DIR,
        request_delay=REQUEST_DELAY,
    )

    # -----------------------------------------
    # 行政区划
    # -----------------------------------------

    region = normalize_region(
        region_raw
    )

    result[
        "province"
    ] = "江苏省"

    result[
        "city"
    ] = region[
        "city"
    ]

    result[
        "district"
    ] = region[
        "district"
    ]

    result[
        "region_raw"
    ] = region_raw

    # -----------------------------------------
    # 保留列表页名称用于排错
    # -----------------------------------------

    result[
        "list_project_name"
    ] = project[
        "list_project_name"
    ]

    # -----------------------------------------
    # 数据质量检查
    # -----------------------------------------

    quality = validate_project(
        result
    )

    result[
        "data_quality_status"
    ] = quality[
        "quality_status"
    ]

    result[
        "quality_warnings"
    ] = quality[
        "warnings"
    ]

    result[
        "quality_errors"
    ] = quality[
        "errors"
    ]

    return result


# =========================================================
# 保存 JSON
# =========================================================

def save_json(
    data,
    file_path,
):

    file_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# =========================================================
# 主程序
# =========================================================

if __name__ == "__main__":

    print(
        "\n======================================"
    )

    print(
        "江苏最新招标项目采集开始"
    )

    print(
        "======================================\n"
    )

    # =========================================
    # 1. 抓第一页
    # =========================================

    projects = parse_list_page()

    print(
        f"\n第一页发现："
        f"{len(projects)} 个项目"
    )

    clean_projects = []

    rejected_projects = []

    # =========================================
    # 2. 逐个抓详情
    # =========================================

    for index, project in enumerate(
        projects,
        start=1,
    ):

        print(
            "\n--------------------------------------"
        )

        print(
            f"[{index}/{len(projects)}]"
        )

        try:

            result = process_project(
                project
            )

            quality_status = (
                result.get(
                    "data_quality_status"
                )
            )

            if (
                quality_status
                == "REJECTED"
            ):

                rejected_projects.append(
                    result
                )

                print(
                    "结果：REJECTED"
                )

                print(
                    "错误：",
                    result.get(
                        "quality_errors"
                    ),
                )

            else:

                clean_projects.append(
                    result
                )

                print(
                    "结果：",
                    quality_status,
                )

                if result.get(
                    "quality_warnings"
                ):

                    print(
                        "警告：",
                        result.get(
                            "quality_warnings"
                        ),
                    )

        except Exception as e:

            print(
                "抓取失败：",
                e,
            )

            rejected_projects.append(
                {
                    "row_id":
                        project.get(
                            "row_id"
                        ),

                    "project_name":
                        project.get(
                            "list_project_name"
                        ),

                    "region_raw":
                        project.get(
                            "region_raw"
                        ),

                    "source_url":
                        project.get(
                            "detail_url"
                        ),

                    "data_quality_status":
                        "REJECTED",

                    "quality_warnings":
                        [],

                    "quality_errors": [
                        str(e)
                    ],
                }
            )

        # -------------------------------------
        # 控制访问频率
        # -------------------------------------

        time.sleep(
            REQUEST_DELAY
        )

    # =========================================
    # 3. 按标段编号去重
    # =========================================

    before_dedup = len(
        clean_projects
    )

    clean_projects = (
        deduplicate_projects(
            clean_projects
        )
    )

    after_dedup = len(
        clean_projects
    )

    duplicate_count = (
        before_dedup
        - after_dedup
    )

    print(
        "\n======================================"
    )

    print(
        "项目去重结果"
    )

    print(
        "======================================"
    )

    print(
        f"去重前：{before_dedup} 条"
    )

    print(
        f"去重后：{after_dedup} 条"
    )

    print(
        f"重复删除：{duplicate_count} 条"
    )

    # =========================================
    # 4. 数据质量统计
    # =========================================

    valid_count = sum(
        1
        for project
        in clean_projects
        if project.get(
            "data_quality_status"
        )
        == "VALID"
    )

    partial_count = sum(
        1
        for project
        in clean_projects
        if project.get(
            "data_quality_status"
        )
        == "PARTIAL"
    )

    rejected_count = len(
        rejected_projects
    )

    print(
        "\n======================================"
    )

    print(
        "数据质量统计"
    )

    print(
        "======================================"
    )

    print(
        f"VALID：{valid_count} 条"
    )

    print(
        f"PARTIAL：{partial_count} 条"
    )

    print(
        f"REJECTED：{rejected_count} 条"
    )

    # =========================================
    # 5. 控制价统计
    # =========================================

    control_price_found = sum(
        1
        for project
        in clean_projects
        if project.get(
            "control_price"
        )
        is not None
    )

    need_limit_file = sum(
        1
        for project
        in clean_projects
        if project.get(
            "control_price_status"
        )
        == "NEEDS_LIMIT_PRICE_FILE"
    )

    print(
        "\n======================================"
    )

    print(
        "控制价统计"
    )

    print(
        "======================================"
    )

    print(
        f"已获得控制价："
        f"{control_price_found} 条"
    )

    print(
        f"需要限价文件补采："
        f"{need_limit_file} 条"
    )

    # =========================================
    # 6. 保存 clean JSON
    # =========================================

    clean_json = (
        CLEAN_DIR
        / "projects.json"
    )

    save_json(
        clean_projects,
        clean_json,
    )

    # =========================================
    # 7. 保存 clean CSV
    # =========================================

    clean_csv = (
        CLEAN_DIR
        / "projects.csv"
    )

    if clean_projects:

        df = pd.DataFrame(
            clean_projects
        )

        # list 类型写入 CSV 前
        # 转换成 JSON 字符串
        for column in [
            "quality_warnings",
            "quality_errors",
        ]:

            if column in df.columns:

                df[column] = (
                    df[column]
                    .apply(
                        lambda value:
                        json.dumps(
                            value,
                            ensure_ascii=False,
                        )
                    )
                )

        df.to_csv(
            clean_csv,
            index=False,
            encoding="utf-8-sig",
        )

    else:

        # 防止上一次旧 CSV 留在目录中
        if clean_csv.exists():
            clean_csv.unlink()

    # =========================================
    # 8. 保存 rejected
    # =========================================

    rejected_json = (
        REJECTED_DIR
        / "rejected_projects.json"
    )

    save_json(
        rejected_projects,
        rejected_json,
    )

    # =========================================
    # 9. 去重和质量检查完成后统一同步 MySQL
    # =========================================

    print("\n准备同步项目数据到 MySQL...")

    try:
        db_result = sync_projects(clean_projects)
        print(
            "数据库同步结果："
            f"新增 {db_result['inserted']}，"
            f"更新 {db_result['updated']}，"
            f"失败 {db_result['failed']}，"
            f"总数 {db_result['total']}"
        )
    except Exception as error:
        print("\n======================================")
        print("MySQL同步失败")
        print("======================================")
        print(error)
        print("本次 JSON/CSV 已正常保存，数据库同步失败不会导致爬虫数据丢失。")

    # =========================================
    # 完成
    # =========================================

    print(
        "\n======================================"
    )

    print(
        "采集完成"
    )

    print(
        "======================================"
    )

    print(
        f"列表原始项目："
        f"{len(projects)}"
    )

    print(
        f"去重后可用项目："
        f"{len(clean_projects)}"
    )

    print(
        f"VALID："
        f"{valid_count}"
    )

    print(
        f"PARTIAL："
        f"{partial_count}"
    )

    print(
        f"REJECTED："
        f"{rejected_count}"
    )

    print(
        "\nClean JSON："
    )

    print(
        clean_json
    )

    print(
        "\nClean CSV："
    )

    print(
        clean_csv
    )

    print(
        "\nRejected JSON："
    )

    print(
        rejected_json
    )
