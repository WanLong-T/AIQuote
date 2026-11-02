from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


# =========================================================
# 测试项目
# 分别选择：
# 897009 市政工程
# 897002 房屋建筑
# 897003 材料设备采购
# =========================================================

PROJECTS = [
    {
        "row_id": "897009",
        "name": "江都居民小区二次供水设施改造项目",
    },
    {
        "row_id": "897002",
        "name": "连云港第一人民医院应急救治中心项目",
    },
    {
        "row_id": "897003",
        "name": "文澜苑项目电梯采购及安装",
    },
]


BASE_URL = (
    "http://www.jszb.com.cn/jszb/YW_info/"
    "ZhaoBiaoGG/ViewReportDetail.aspx"
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}


# =========================================================
# 获取网页
# =========================================================

def get_html(row_id):

    url = (
        f"{BASE_URL}"
        f"?RowID={row_id}"
        f"&categoryNum=012"
        f"&siteid=1"
    )

    print("\n======================================")
    print(f"正在抓取 RowID：{row_id}")
    print(f"地址：{url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
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

    return response.text, url


# =========================================================
# 保存完整 HTML
# =========================================================

def save_html(
    soup,
    html,
    output_dir,
    row_id,
):

    file_path = (
        output_dir
        / f"{row_id}_page.html"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(html)

    print(
        f"HTML：{file_path}"
    )


# =========================================================
# 保存网页纯文本
# =========================================================

def save_text(
    soup,
    output_dir,
    row_id,
):

    file_path = (
        output_dir
        / f"{row_id}_text.txt"
    )

    text = soup.get_text(
        "\n",
        strip=True,
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(text)

    print(
        f"正文：{file_path}"
    )


# =========================================================
# 保存所有 table / tr / td
# =========================================================

def save_tables(
    soup,
    output_dir,
    row_id,
):

    file_path = (
        output_dir
        / f"{row_id}_tables.txt"
    )

    tables = soup.find_all(
        "table"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            f"TABLE总数量：{len(tables)}\n"
        )

        for table_index, table in enumerate(
            tables,
            start=1,
        ):

            f.write(
                "\n\n"
                f"========== TABLE {table_index} =========="
                "\n"
            )

            rows = table.find_all(
                "tr"
            )

            for row_index, row in enumerate(
                rows,
                start=1,
            ):

                cells = row.find_all(
                    ["td", "th"]
                )

                values = []

                for cell in cells:

                    value = cell.get_text(
                        " ",
                        strip=True,
                    )

                    if value:
                        values.append(
                            value
                        )

                if values:

                    f.write(
                        f"TR {row_index}: "
                    )

                    f.write(
                        " || ".join(
                            values
                        )
                    )

                    f.write("\n")

    print(
        f"表格：{file_path}"
    )


# =========================================================
# 专门搜索核心字段周围的内容
# =========================================================

def save_keywords(
    soup,
    output_dir,
    row_id,
):

    file_path = (
        output_dir
        / f"{row_id}_keywords.txt"
    )

    keywords = [
        "项目名称",
        "工程名称",
        "标段名称",

        "建设单位",
        "招标人",
        "业主",

        "公告发布时间",
        "发布时间",

        "开标时间",
        "开标日期",

        "投标截止时间",
        "投标文件递交截止时间",

        "招标控制价",
        "最高投标限价",
        "最高限价",

        "合同估算价",
        "合同估算金额",
        "估算价",

        "暂列金额",
        "暂列金",
    ]

    all_tags = soup.find_all(
        [
            "td",
            "th",
            "p",
            "div",
            "span",
            "li",
        ]
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as f:

        for index, tag in enumerate(
            all_tags
        ):

            text = tag.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            for keyword in keywords:

                if keyword in text:

                    f.write(
                        "\n\n"
                        "=================================\n"
                    )

                    f.write(
                        f"关键词：{keyword}\n"
                    )

                    f.write(
                        f"当前节点：{text}\n"
                    )

                    # 输出父节点
                    parent = tag.parent

                    if parent:

                        parent_text = (
                            parent.get_text(
                                " ",
                                strip=True,
                            )
                        )

                        f.write(
                            f"父节点：{parent_text}\n"
                        )

                    # 输出前一个节点
                    previous = (
                        tag.find_previous()
                    )

                    if previous:

                        previous_text = (
                            previous.get_text(
                                " ",
                                strip=True,
                            )
                        )

                        f.write(
                            f"前节点：{previous_text}\n"
                        )

                    # 输出后一个节点
                    next_tag = (
                        tag.find_next()
                    )

                    if next_tag:

                        next_text = (
                            next_tag.get_text(
                                " ",
                                strip=True,
                            )
                        )

                        f.write(
                            f"后节点：{next_text}\n"
                        )

                    break

    print(
        f"关键词：{file_path}"
    )


# =========================================================
# 主程序
# =========================================================

if __name__ == "__main__":

    # 项目数据爬虫目录
    root_dir = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    # 保存到 raw
    raw_dir = (
        root_dir
        / "数据"
        / "raw"
        / "江苏详情页测试"
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for project in PROJECTS:

        row_id = (
            project["row_id"]
        )

        try:

            html, url = get_html(
                row_id
            )

            soup = BeautifulSoup(
                html,
                "lxml",
            )

            output_dir = (
                raw_dir
                / row_id
            )

            output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            save_html(
                soup,
                html,
                output_dir,
                row_id,
            )

            save_text(
                soup,
                output_dir,
                row_id,
            )

            save_tables(
                soup,
                output_dir,
                row_id,
            )

            save_keywords(
                soup,
                output_dir,
                row_id,
            )

        except Exception as e:

            print(
                f"\n抓取失败：{row_id}"
            )

            print(
                "错误：",
                e,
            )

    print(
        "\n======================================"
    )

    print(
        "详情页诊断完成"
    )