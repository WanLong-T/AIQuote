"""江苏省建设工程招标网未截止项目分页采集器。

特点：
1. 使用 ASP.NET __VIEWSTATE 顺序翻页；
2. 原始详情页落盘，重复运行时默认使用缓存；
3. 每处理一条即写入断点，程序中断后可继续；
4. 默认只输出投标截止时间尚未到达的项目；
5. 公告未披露字段保持 None，不编造数据。

示例：
    python crawl_remaining.py --pages 5
    python crawl_remaining.py --pages 20 --refresh-list
    python crawl_remaining.py --pages 20 --refresh-details
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
from bs4 import BeautifulSoup

from crawler import (
    CLEAN_DIR,
    LIST_URL,
    RAW_DIR,
    REJECTED_DIR,
    REQUEST_DELAY,
    SESSION,
    clean_text,
    compose_official_project_name,
    deduplicate_projects,
    normalize_region,
    save_json,
    validate_project,
)
from parser import parse_detail_html
from attachments import enrich_from_attachments
from mysql_store import sync_projects


CHECKPOINT_FILE = CLEAN_DIR / "crawl_checkpoint.json"
LIST_CACHE_DIR = RAW_DIR / "列表页"
LIST_CACHE_DIR.mkdir(parents=True, exist_ok=True)

DISTRICT_TO_CITY = {
    "玄武": "南京市", "秦淮": "南京市", "建邺": "南京市", "鼓楼": "南京市",
    "栖霞": "南京市", "雨花台": "南京市", "江宁": "南京市", "浦口": "南京市",
    "六合": "南京市", "溧水": "南京市", "高淳": "南京市",
    "梁溪": "无锡市", "锡山": "无锡市", "惠山": "无锡市", "滨湖": "无锡市",
    "新吴": "无锡市", "江阴": "无锡市", "宜兴": "无锡市",
    "云龙": "徐州市", "鼓楼区": "徐州市", "贾汪": "徐州市", "泉山": "徐州市",
    "铜山": "徐州市", "丰县": "徐州市", "沛县": "徐州市", "睢宁": "徐州市",
    "新沂": "徐州市", "邳州": "徐州市",
    "天宁": "常州市", "钟楼": "常州市", "新北": "常州市", "武进": "常州市",
    "金坛": "常州市", "溧阳": "常州市",
    "姑苏": "苏州市", "虎丘": "苏州市", "吴中": "苏州市", "相城": "苏州市",
    "吴江": "苏州市", "常熟": "苏州市", "张家港": "苏州市", "昆山": "苏州市",
    "太仓": "苏州市", "工业园区": "苏州市",
    "崇川": "南通市", "通州": "南通市", "海门": "南通市", "启东": "南通市",
    "如皋": "南通市", "海安": "南通市", "如东": "南通市",
    "连云": "连云港市", "海州": "连云港市", "赣榆": "连云港市",
    "东海": "连云港市", "灌云": "连云港市", "灌南": "连云港市",
    "淮安区": "淮安市", "淮阴": "淮安市", "清江浦": "淮安市", "洪泽": "淮安市",
    "涟水": "淮安市", "盱眙": "淮安市", "金湖": "淮安市",
    "亭湖": "盐城市", "盐都": "盐城市", "大丰": "盐城市", "响水": "盐城市",
    "滨海": "盐城市", "阜宁": "盐城市", "射阳": "盐城市", "建湖": "盐城市",
    "东台": "盐城市",
    "广陵": "扬州市", "邗江": "扬州市", "江都": "扬州市", "宝应": "扬州市",
    "仪征": "扬州市", "高邮": "扬州市",
    "京口": "镇江市", "润州": "镇江市", "丹徒": "镇江市", "丹阳": "镇江市",
    "扬中": "镇江市", "句容": "镇江市",
    "海陵": "泰州市", "高港": "泰州市", "姜堰": "泰州市", "兴化": "泰州市",
    "靖江": "泰州市", "泰兴": "泰州市",
    "宿城": "宿迁市", "宿豫": "宿迁市", "沭阳": "宿迁市", "泗阳": "宿迁市",
    "泗洪": "宿迁市",
}


def decode_response(response):
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "gb18030"
    return response.text


def request_first_page():
    return decode_response(SESSION.get(LIST_URL, timeout=35, verify=False))


def hidden_fields(html):
    soup = BeautifulSoup(html, "lxml")
    return {
        node.get("name"): node.get("value", "")
        for node in soup.select('input[type="hidden"][name]')
    }


def request_page(previous_html, page_number):
    form = hidden_fields(previous_html)
    form["__EVENTTARGET"] = "MoreInfoList1$Pager"
    form["__EVENTARGUMENT"] = str(page_number)
    form.pop("__LASTFOCUS", None)
    response = SESSION.post(LIST_URL, data=form, timeout=35, verify=False)
    return decode_response(response)


def parse_list_html(html):
    soup = BeautifulSoup(html, "lxml")
    rows = []
    seen = set()
    for anchor in soup.find_all("a"):
        onclick = anchor.get("onclick", "")
        if "ViewReportDetail.aspx" not in onclick:
            continue
        match = re.search(
            r"window\.open\([\"']([^\"']*ViewReportDetail\.aspx[^\"']*)", onclick, re.I
        )
        if not match:
            continue
        detail_url = urljoin(LIST_URL, match.group(1))
        row_id = parse_qs(urlparse(detail_url).query).get("RowID", [None])[0]
        if not row_id or row_id in seen:
            continue
        seen.add(row_id)
        title = clean_text(anchor.get("title") or anchor.get_text(" ", strip=True)) or ""
        region_match = re.match(r"^\[([^\]]+)]", title)
        row = anchor.find_parent("tr")
        row_text = " ".join(row.stripped_strings) if row else ""
        publish_match = re.search(r"20\d{2}-\d{1,2}-\d{1,2}", row_text)
        rows.append({
            "row_id": row_id,
            "region_raw": region_match.group(1) if region_match else None,
            "list_project_name": re.sub(r"^\[[^\]]+]", "", title).strip(),
            "list_publish_date": publish_match.group(0) if publish_match else None,
            "detail_url": detail_url,
        })
    return rows


def collect_list_items(page_count, refresh=False):
    all_items = []
    seen = set()
    previous_html = None
    for page in range(1, page_count + 1):
        cache = LIST_CACHE_DIR / f"page-{page:04d}.html"
        if cache.exists() and not refresh:
            html = cache.read_text(encoding="utf-8", errors="ignore")
        elif page == 1:
            html = request_first_page()
            cache.write_text(html, encoding="utf-8")
        else:
            if previous_html is None:
                previous_html = request_first_page()
            html = request_page(previous_html, page)
            cache.write_text(html, encoding="utf-8")
            time.sleep(REQUEST_DELAY)
        previous_html = html
        page_items = parse_list_html(html)
        if not page_items:
            print(f"第 {page} 页没有识别到公告，停止翻页。")
            break
        new_count = 0
        for item in page_items:
            if item["row_id"] not in seen:
                seen.add(item["row_id"])
                all_items.append(item)
                new_count += 1
        print(f"列表第 {page} 页：识别 {len(page_items)} 条，新增 {new_count} 条")
        if page > 1 and new_count == 0:
            raise RuntimeError("翻页结果与上一页重复，ASP.NET 分页请求未生效")
    return all_items


def infer_region(project):
    region = normalize_region(project.get("region_raw"))
    if region.get("city"):
        return region
    haystack = " ".join(str(project.get(k) or "") for k in (
        "region_raw", "project_name", "parent_project_name", "owner_name", "tenderer_name"
    ))
    for district, city in DISTRICT_TO_CITY.items():
        if district in haystack:
            district_name = project.get("region_raw") or district
            if district_name and not district_name.endswith(("区", "县", "市")):
                district_name += "区"
            return {"city": city, "district": district_name}
    for city in ("南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"):
        if city in haystack:
            return {"city": city + "市", "district": None}
    return region


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def parse_deadline(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def fetch_or_parse(item, refresh_details=False):
    raw_file = RAW_DIR / f"{item['row_id']}.html"
    if raw_file.exists() and not refresh_details:
        html = raw_file.read_text(encoding="utf-8", errors="ignore")
    else:
        response = SESSION.get(item["detail_url"], timeout=35, verify=False)
        html = decode_response(response)
        raw_file.write_text(html, encoding="utf-8")
        time.sleep(REQUEST_DELAY)
    result = parse_detail_html(
        html, row_id=item["row_id"], detail_url=item["detail_url"], region_raw=item["region_raw"]
    )
    result = enrich_from_attachments(
        result, html, item["detail_url"], item["row_id"], SESSION, RAW_DIR,
        request_delay=REQUEST_DELAY,
    )
    # 列表页地区优先；列表未给出时使用详情表中的“建设地点/项目所在地”。
    effective_region_raw = item.get("region_raw") or result.get("region_raw")
    region = infer_region({**result, **item, "region_raw": effective_region_raw})
    result.update({
        "province": "江苏省",
        "city": region.get("city"),
        "district": region.get("district"),
        "region_raw": effective_region_raw,
        "list_project_name": item["list_project_name"],
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    result["project_name"] = compose_official_project_name(result)
    quality = validate_project(result)
    result["data_quality_status"] = quality["quality_status"]
    result["quality_warnings"] = quality["warnings"]
    result["quality_errors"] = quality["errors"]
    return result


def save_outputs(projects, rejected):
    projects = deduplicate_projects(projects)
    projects.sort(key=lambda row: (row.get("bid_deadline") or "9999", row.get("source_row_id") or ""))
    save_json(projects, CLEAN_DIR / "projects.json")
    save_json(rejected, REJECTED_DIR / "rejected_projects.json")
    if projects:
        frame = pd.DataFrame(projects)
        for column in ("quality_warnings", "quality_errors"):
            if column in frame.columns:
                frame[column] = frame[column].apply(lambda value: json.dumps(value, ensure_ascii=False))
        frame.to_csv(CLEAN_DIR / "projects.csv", index=False, encoding="utf-8-sig")
    return projects


def main():
    parser = argparse.ArgumentParser(description="分页采集江苏未截止招标项目")
    parser.add_argument("--pages", type=int, default=5, help="从最新公告开始采集的页数，默认5页")
    parser.add_argument("--refresh-list", action="store_true", help="忽略列表页缓存，重新请求")
    parser.add_argument("--refresh-details", action="store_true", help="忽略详情页缓存，重新请求")
    parser.add_argument("--reparse-cached", action="store_true", help="重新解析已缓存详情页，不重新下载")
    parser.add_argument("--include-unknown-deadline", action="store_true", help="保留无法解析截止时间的公告")
    args = parser.parse_args()
    if args.pages < 1:
        parser.error("--pages 必须大于0")

    items = collect_list_items(args.pages, refresh=args.refresh_list)
    existing = load_json(CLEAN_DIR / "projects.json", [])
    rejected = load_json(REJECTED_DIR / "rejected_projects.json", [])
    by_id = {str(row.get("source_row_id")): row for row in existing if row.get("source_row_id")}
    checkpoint = load_json(CHECKPOINT_FILE, {"completed": []})
    completed = set(checkpoint.get("completed", []))
    now = datetime.now()

    for index, item in enumerate(items, 1):
        row_id = item["row_id"]
        if (
            row_id in completed
            and row_id in by_id
            and not args.refresh_details
            and not args.reparse_cached
        ):
            print(f"[{index}/{len(items)}] {row_id} 已完成，跳过")
            continue
        try:
            result = fetch_or_parse(item, refresh_details=args.refresh_details)
            deadline = parse_deadline(result.get("bid_deadline"))
            is_open = deadline is not None and deadline >= now
            # 官网最新列表中的公告必须逐条保留。部分站点只在招标文件中给出
            # 截止时间，解析不到日期不等于项目无效，不能因此漏掉整条公告。
            keep = is_open or deadline is None
            if result["data_quality_status"] == "REJECTED":
                rejected.append(result)
            elif keep:
                by_id[row_id] = result
                print(f"[{index}/{len(items)}] 保留：{result.get('project_name')} / {result.get('bid_deadline') or '截止时间未知'}")
            else:
                by_id.pop(row_id, None)
                print(f"[{index}/{len(items)}] 排除已截止或截止时间未知：{result.get('project_name')}")
            completed.add(row_id)
            save_json({"completed": sorted(completed), "updated_at": datetime.now().isoformat()}, CHECKPOINT_FILE)
            save_outputs(list(by_id.values()), rejected)
        except KeyboardInterrupt:
            print("\n用户中断，断点已保留。")
            break
        except Exception as exc:
            print(f"[{index}/{len(items)}] 失败 {row_id}: {exc}", file=sys.stderr)
            rejected.append({**item, "data_quality_status": "REJECTED", "quality_errors": [str(exc)]})
            save_outputs(list(by_id.values()), rejected)

    final = save_outputs(list(by_id.values()), rejected)
    print("准备同步项目数据到 MySQL...")
    try:
        db_result = sync_projects(final)
        print(
            f"MySQL同步完成：新增 {db_result['inserted']}，更新 {db_result['updated']}，"
            f"失败 {db_result['failed']}，数据库总数 {db_result['total']}。"
        )
    except Exception as error:
        print(f"MySQL同步失败：{error}")
        print("JSON/CSV 已保存，本次数据库异常不会导致爬取数据丢失。")
    print(f"采集完成：未截止有效项目 {len(final)} 条；失败/无效记录 {len(rejected)} 条。")
    print(f"JSON：{CLEAN_DIR / 'projects.json'}")
    print(f"CSV：{CLEAN_DIR / 'projects.csv'}")


if __name__ == "__main__":
    main()
