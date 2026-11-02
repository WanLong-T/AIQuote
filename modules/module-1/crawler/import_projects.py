import json
from pathlib import Path
from datetime import datetime

from db import get_connection


# =========================================================
# 路径配置
# =========================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

PROJECTS_JSON = (
    ROOT_DIR
    / "数据"
    / "clean"
    / "projects.json"
)


# =========================================================
# 日期处理
# =========================================================

def normalize_datetime(value):

    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt,
            )

        except ValueError:
            continue

    return None


# =========================================================
# JSON 字段
# =========================================================

def to_json_text(value):

    if value is None:
        return json.dumps(
            [],
            ensure_ascii=False,
        )

    if isinstance(
        value,
        (list, dict),
    ):

        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return json.dumps(
        [str(value)],
        ensure_ascii=False,
    )


# =========================================================
# 原始 HTML 路径
# =========================================================

def build_raw_file_path(
    project
):

    row_id = project.get(
        "source_row_id"
    )

    province = project.get(
        "province"
    )

    if not row_id:
        return None

    if province == "江苏省":

        relative_path = (
            Path("raw")
            / "江苏"
            / f"{row_id}.html"
        )

        return str(
            relative_path
        )

    return None


# =========================================================
# 单条项目写入数据库
# =========================================================

def upsert_project(
    cursor,
    project,
):

    sql = """
    INSERT INTO projects (
        project_id,
        project_name,
        parent_project_name,
        project_code,
        section_code,
        project_type,

        province,
        city,
        district,
        region_raw,

        owner_name,
        tenderer_name,
        main_entity_name,
        main_entity_type,

        publish_time,
        open_bid_time,
        bid_deadline,

        control_price,
        control_price_status,
        control_price_raw,

        estimated_contract_amount,
        estimated_contract_amount_source,
        estimated_contract_amount_confidence,
        estimated_contract_amount_raw,

        provisional_sum,
        provisional_sum_status,
        provisional_sum_raw,

        tracking_stage,
        rating,
        responsible_person,

        source_platform,
        source_row_id,
        source_url,

        list_project_name,
        raw_file_path,

        data_quality_status,
        quality_warnings,
        quality_errors,

        crawl_time
    )
    VALUES (
        %(project_id)s,
        %(project_name)s,
        %(parent_project_name)s,
        %(project_code)s,
        %(section_code)s,
        %(project_type)s,

        %(province)s,
        %(city)s,
        %(district)s,
        %(region_raw)s,

        %(owner_name)s,
        %(tenderer_name)s,
        %(main_entity_name)s,
        %(main_entity_type)s,

        %(publish_time)s,
        %(open_bid_time)s,
        %(bid_deadline)s,

        %(control_price)s,
        %(control_price_status)s,
        %(control_price_raw)s,

        %(estimated_contract_amount)s,
        %(estimated_contract_amount_source)s,
        %(estimated_contract_amount_confidence)s,
        %(estimated_contract_amount_raw)s,

        %(provisional_sum)s,
        %(provisional_sum_status)s,
        %(provisional_sum_raw)s,

        %(tracking_stage)s,
        %(rating)s,
        %(responsible_person)s,

        %(source_platform)s,
        %(source_row_id)s,
        %(source_url)s,

        %(list_project_name)s,
        %(raw_file_path)s,

        %(data_quality_status)s,
        %(quality_warnings)s,
        %(quality_errors)s,

        %(crawl_time)s
    )

    ON DUPLICATE KEY UPDATE

        project_id =
            VALUES(project_id),

        project_name =
            VALUES(project_name),

        parent_project_name =
            VALUES(parent_project_name),

        project_code =
            VALUES(project_code),

        section_code =
            VALUES(section_code),

        project_type =
            VALUES(project_type),

        province =
            VALUES(province),

        city =
            VALUES(city),

        district =
            VALUES(district),

        region_raw =
            VALUES(region_raw),

        owner_name =
            VALUES(owner_name),

        tenderer_name =
            VALUES(tenderer_name),

        main_entity_name =
            VALUES(main_entity_name),

        main_entity_type =
            VALUES(main_entity_type),

        publish_time =
            VALUES(publish_time),

        open_bid_time =
            VALUES(open_bid_time),

        bid_deadline =
            VALUES(bid_deadline),

        control_price =
            VALUES(control_price),

        control_price_status =
            VALUES(control_price_status),

        control_price_raw =
            VALUES(control_price_raw),

        estimated_contract_amount =
            VALUES(
                estimated_contract_amount
            ),

        estimated_contract_amount_source =
            VALUES(
                estimated_contract_amount_source
            ),

        estimated_contract_amount_confidence =
            VALUES(
                estimated_contract_amount_confidence
            ),

        estimated_contract_amount_raw =
            VALUES(
                estimated_contract_amount_raw
            ),

        provisional_sum =
            VALUES(provisional_sum),

        provisional_sum_status =
            VALUES(provisional_sum_status),

        provisional_sum_raw =
            VALUES(provisional_sum_raw),

        source_url =
            VALUES(source_url),

        list_project_name =
            VALUES(list_project_name),

        raw_file_path =
            VALUES(raw_file_path),

        data_quality_status =
            VALUES(data_quality_status),

        quality_warnings =
            VALUES(quality_warnings),

        quality_errors =
            VALUES(quality_errors),

        crawl_time =
            VALUES(crawl_time)
    """

    values = {

        "project_id":
            project.get(
                "project_id"
            ),

        "project_name":
            project.get(
                "project_name"
            ),

        "parent_project_name":
            project.get(
                "parent_project_name"
            ),

        "project_code":
            project.get(
                "project_code"
            ),

        "section_code":
            project.get(
                "section_code"
            ),

        "project_type":
            project.get(
                "project_type"
            ),

        "province":
            project.get(
                "province"
            ),

        "city":
            project.get(
                "city"
            ),

        "district":
            project.get(
                "district"
            ),

        "region_raw":
            project.get(
                "region_raw"
            ),

        "owner_name":
            project.get(
                "owner_name"
            ),

        "tenderer_name":
            project.get(
                "tenderer_name"
            ),

        "main_entity_name":
            project.get(
                "main_entity_name"
            )
            or project.get(
                "owner_name"
            )
            or project.get(
                "tenderer_name"
            ),

        "main_entity_type":
            project.get(
                "main_entity_type"
            ),

        "publish_time":
            normalize_datetime(
                project.get(
                    "publish_time"
                )
            ),

        "open_bid_time":
            normalize_datetime(
                project.get(
                    "open_bid_time"
                )
            ),

        "bid_deadline":
            normalize_datetime(
                project.get(
                    "bid_deadline"
                )
            ),

        "control_price":
            project.get(
                "control_price"
            ),

        "control_price_status":
            project.get(
                "control_price_status"
            ),

        "control_price_raw":
            project.get(
                "control_price_raw"
            ),

        "estimated_contract_amount":
            project.get(
                "estimated_contract_amount"
            ),

        "estimated_contract_amount_source":
            project.get(
                "estimated_contract_amount_source"
            ),

        "estimated_contract_amount_confidence":
            project.get(
                "estimated_contract_amount_confidence"
            ),

        "estimated_contract_amount_raw":
            project.get(
                "estimated_contract_amount_raw"
            ),

        "provisional_sum":
            project.get(
                "provisional_sum"
            ),

        "provisional_sum_status":
            project.get(
                "provisional_sum_status"
            ),

        "provisional_sum_raw":
            project.get(
                "provisional_sum_raw"
            ),

        "tracking_stage":
            project.get(
                "tracking_stage"
            )
            or "LEAD",

        "rating":
            project.get(
                "rating"
            )
            or "UNRATED",

        "responsible_person":
            project.get(
                "responsible_person"
            ),

        "source_platform":
            project.get(
                "source_platform"
            ),

        "source_row_id":
            project.get(
                "source_row_id"
            ),

        "source_url":
            project.get(
                "source_url"
            ),

        "list_project_name":
            project.get(
                "list_project_name"
            ),

        "raw_file_path":
            build_raw_file_path(
                project
            ),

        "data_quality_status":
            project.get(
                "data_quality_status"
            ),

        "quality_warnings":
            to_json_text(
                project.get(
                    "quality_warnings"
                )
            ),

        "quality_errors":
            to_json_text(
                project.get(
                    "quality_errors"
                )
            ),

        "crawl_time":
            (
                normalize_datetime(
                    project.get(
                        "crawl_time"
                    )
                )
                or datetime.now()
            ),
    }

    cursor.execute(
        sql,
        values,
    )


# =========================================================
# 主导入程序
# =========================================================

def main():

    print(
        "\n======================================"
    )

    print(
        "项目数据导入 MySQL"
    )

    print(
        "======================================\n"
    )

    # -----------------------------------------
    # 检查文件
    # -----------------------------------------

    if not PROJECTS_JSON.exists():

        print(
            "找不到 projects.json："
        )

        print(
            PROJECTS_JSON
        )

        return

    # -----------------------------------------
    # 读取 JSON
    # -----------------------------------------

    with PROJECTS_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:

        projects = json.load(
            f
        )

    if not isinstance(
        projects,
        list,
    ):

        print(
            "projects.json 格式错误："
            "最外层必须是数组。"
        )

        return

    print(
        f"读取项目：{len(projects)} 条"
    )

    connection = None
    cursor = None

    success_count = 0
    fail_count = 0

    try:

        connection = (
            get_connection()
        )

        cursor = (
            connection.cursor()
        )

        for index, project in enumerate(
            projects,
            start=1,
        ):

            project_name = (
                project.get(
                    "project_name"
                )
                or "未命名项目"
            )

            try:

                upsert_project(
                    cursor,
                    project,
                )

                success_count += 1

                print(
                    f"[{index}/{len(projects)}] "
                    f"成功：{project_name}"
                )

            except Exception as e:

                fail_count += 1

                print(
                    f"[{index}/{len(projects)}] "
                    f"失败：{project_name}"
                )

                print(
                    f"    原因：{e}"
                )

        # -------------------------------------
        # 全部成功/失败处理完以后统一提交
        # -------------------------------------

        connection.commit()

        # -------------------------------------
        # 查询数据库当前总数
        # -------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM projects
            """
        )

        database_count = (
            cursor.fetchone()[0]
        )

        print(
            "\n======================================"
        )

        print(
            "导入完成"
        )

        print(
            "======================================"
        )

        print(
            f"JSON项目数：{len(projects)}"
        )

        print(
            f"成功处理：{success_count}"
        )

        print(
            f"失败：{fail_count}"
        )

        print(
            f"MySQL当前项目总数：{database_count}"
        )

    except Exception as e:

        if connection:

            connection.rollback()

        print(
            "\n数据库导入发生错误："
        )

        print(
            e
        )

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# 程序入口
# =========================================================

if __name__ == "__main__":

    main()