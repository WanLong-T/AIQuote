import re
import json
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup


# =========================================================
# 基础清洗
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

    return value or None


# =========================================================
# HTML 表格字段读取
# =========================================================

FIELD_ALIASES = {
    "项目编号": ("项目编号", "项目代码", "项目编码", "工程编号"),
    "项目名称": ("项目名称", "工程名称", "招标项目名称", "建设项目名称"),
    "标段编号": ("标段编号", "标段代码", "标段编码"),
    "标段名称": ("标段名称", "招标标段名称", "工程标段名称"),
    "公告开始时间": ("公告开始时间", "公告发布时间", "公告发布日期", "发布时间", "发布日期", "招标公告发布时间"),
    "公告结束时间": ("公告结束时间", "公告截止时间"),
    "工程类型": ("工程类型", "项目类型", "工程类别", "项目类别", "招标类型"),
    "项目所在地": ("项目所在地", "项目地点", "建设地点", "工程地点", "所属地区"),
    "项目业主": ("项目业主", "业主单位", "建设单位", "建设单位名称", "项目法人"),
    "招标人": ("招标人", "招标单位", "招标人名称", "发包人", "招标主体"),
    "投标截止时间": (
        "投标截止时间", "投标文件递交截止时间", "递交投标文件截止时间",
        "递交截止时间", "申请截止时间", "投标截止日期",
        "资格审查截止时间", "资格审查登记截止时间", "资格审查截至时间",
        "资格预审申请文件递交截止时间",
    ),
    "开标时间": ("开标时间", "开标日期", "开标时间和地点"),
    "招标控制价": ("招标控制价", "最高投标限价", "最高限价", "投标最高限价"),
    "预估合同额": ("预估合同额", "预计合同额", "合同估算价", "工程合同估算价", "标段估算价", "项目总投资", "总投资", "投资额"),
    "暂列金额": ("暂列金额", "暂列金", "暂列款"),
}


def normalize_label(value):
    value = clean_text(value) or ""
    value = re.sub(r"[\s:：()（）【】\[\]_-]+", "", value)
    return value.rstrip("为")


NORMALIZED_FIELD_ALIASES = {
    canonical: tuple(normalize_label(alias) for alias in aliases)
    for canonical, aliases in FIELD_ALIASES.items()
}


def match_field_label(label):
    """把近义或存在轻微错字的表格标签映射为统一字段名。"""
    normalized = normalize_label(label)
    if not normalized or len(normalized) > 24:
        return None

    best_match = None
    best_score = 0.0
    for canonical, aliases in NORMALIZED_FIELD_ALIASES.items():
        for alias in aliases:
            if normalized == alias:
                return canonical
            if len(alias) >= 4 and (alias in normalized or normalized in alias):
                score = min(len(alias), len(normalized)) / max(len(alias), len(normalized))
                if score > best_score:
                    best_match, best_score = canonical, score
            if min(len(alias), len(normalized)) >= 4:
                score = SequenceMatcher(None, normalized, alias).ratio()
                if score > best_score:
                    best_match, best_score = canonical, score

    return best_match if best_score >= 0.78 else None

def extract_table_fields(soup):
    """
    从详情页顶部结构化表格中读取：
    项目编号
    项目名称
    标段编号
    标段名称
    公告开始时间
    公告结束时间
    工程类型
    """

    result = {}

    for row in soup.find_all("tr"):

        cells = [
            clean_text(cell.get_text(" ", strip=True))
            for cell in row.find_all(
                ["td", "th"],
                recursive=False,
            )
        ]

        cells = [
            value
            for value in cells
            if value
        ]

        if len(cells) < 2:
            continue

        # 一行可能是：
        # 项目编号 | xxx | 项目名称 | xxx
        # 或：
        # 公告开始时间 | xxx | 公告结束时间 | xxx

        for index in range(
            0,
            len(cells) - 1,
        ):
            canonical = match_field_label(cells[index])
            if not canonical:
                continue

            value = cells[index + 1]

            # 防止下一格还是另一个标签
            if match_field_label(value):
                continue

            if canonical not in result:
                result[canonical] = value
                # 金额表头经常把单位写在标签中（例如“招标控制价（万元）”），
                # 只保存数值格会丢掉单位，进而导致金额无法解析或数量级错误。
                result[f"{canonical}__label"] = cells[index]

    return result


# =========================================================
# 日期处理
# =========================================================

def build_datetime(groups):
    year = int(groups[0])
    month = int(groups[1])
    day = int(groups[2])

    hour = (
        int(groups[3])
        if len(groups) > 3 and groups[3]
        else 0
    )

    minute = (
        int(groups[4])
        if len(groups) > 4 and groups[4]
        else 0
    )

    second = (
        int(groups[5])
        if len(groups) > 5 and groups[5]
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

    except ValueError:
        return None

    return dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def parse_datetime_text(text):
    if not text:
        return None

    text = clean_text(text)

    # 公告正文经常把日期的每个数字拆到不同的 span 中，例如：
    # “2026 年 1 1 月 16 日”。BeautifulSoup 提取文本后会在两个
    # 数字之间留下空格，需要先还原成“2026 年 11 月 16 日”。
    # 只处理紧邻年月日时分秒单位的数字，避免误合并正文中的普通数字。
    previous = None
    while text != previous:
        previous = text
        text = re.sub(
            r"(?<=\d)\s+(?=\d\s*[年月日时分秒])",
            "",
            text,
        )

    patterns = [
        # 2026年10月30日09时30分
        (
            r"(20\d{2})\s*年\s*"
            r"(\d{1,2})\s*月\s*"
            r"(\d{1,2})\s*日\s*"
            r"(\d{1,2})\s*时\s*"
            r"(\d{1,2})\s*分"
            r"(?:\s*(\d{1,2})\s*秒)?"
        ),

        # 2026年11月 11 日 09:30
        (
            r"(20\d{2})\s*年\s*"
            r"(\d{1,2})\s*月\s*"
            r"(\d{1,2})\s*日\s*"
            r"(\d{1,2})\s*:\s*"
            r"(\d{1,2})"
            r"(?:\s*:\s*(\d{1,2}))?"
        ),

        # 2026-11-11 9:00:00
        (
            r"(20\d{2})\s*-\s*"
            r"(\d{1,2})\s*-\s*"
            r"(\d{1,2})\s+"
            r"(\d{1,2})\s*:\s*"
            r"(\d{1,2})"
            r"(?:\s*:\s*(\d{1,2}))?"
        ),

        # 2026/11/11 9:00、2026.11.11 9:00
        (
            r"(20\d{2})\s*[/．.]\s*"
            r"(\d{1,2})\s*[/．.]\s*"
            r"(\d{1,2})\s+"
            r"(\d{1,2})\s*:\s*"
            r"(\d{1,2})"
            r"(?:\s*:\s*(\d{1,2}))?"
        ),

        # 只有日期
        (
            r"(20\d{2})\s*年\s*"
            r"(\d{1,2})\s*月\s*"
            r"(\d{1,2})\s*日"
        ),

        (
            r"(20\d{2})\s*-\s*"
            r"(\d{1,2})\s*-\s*"
            r"(\d{1,2})"
        ),
        (
            r"(20\d{2})\s*[/．.]\s*"
            r"(\d{1,2})\s*[/．.]\s*"
            r"(\d{1,2})"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:
            return build_datetime(
                match.groups()
            )

    return None


def extract_datetime_after_anchor(
    text,
    anchors,
    window=150,
):

    for anchor in anchors:

        match = re.search(
            anchor,
            text,
            re.I,
        )

        if not match:
            continue

        snippet = text[
            match.end():
            match.end() + window
        ]

        value = parse_datetime_text(
            snippet
        )

        if value:
            return value

    return None


# =========================================================
# 金额处理
# =========================================================

def money_to_yuan(
    number_text,
    unit,
):

    try:
        number = float(
            number_text.replace(",", "")
        )
    except Exception:
        return None

    if unit == "亿元":
        number *= 100_000_000

    elif unit in {
        "万元",
        "万",
    }:
        number *= 10_000

    return round(
        number,
        2,
    )


MONEY_TERMS = (
    "工程合同估算价", "标段合同估算价", "合同估算金额", "合同估算价",
    "标段估算价", "招标控制价", "最高投标限价", "投标最高限价",
    "最高限价", "暂列金额", "暂列金", "项目总投资", "总投资",
    "建安工程费", "工程费用", "人民币", "亿元", "万元",
)


def normalize_money_text(text):
    """统一全角字符，并修复PDF抽取后金额标签被空格拆开的情况。"""
    value = unicodedata.normalize("NFKC", str(text or ""))
    value = re.sub(r"(?<=\d)[，,](?=\d{3}(?:\D|$))", ",", value)
    for term in MONEY_TERMS:
        spaced = r"\s*".join(map(re.escape, term))
        value = re.sub(spaced, term, value, flags=re.I)
    value = re.sub(r"亿\s*元", "亿元", value)
    value = re.sub(r"万\s*元", "万元", value)
    return value


# =========================================================
# 合同估算金额
# =========================================================

def extract_estimated_amount(text):

    text = normalize_money_text(text)

    # -----------------------------------------
    # 第一优先：
    # 工程合同估算价（万元）：233.54
    # -----------------------------------------

    match = re.search(
        r"(?:本标段|本项目)?(?:工程)?(?:合同|标段)(?:估算价|估算金额)"
        r"(?:\s*[（(]\s*(万元|亿元|元)\s*[）)])?"
        r"\s*(?:为|约|[:：])?\s*"
        r"([\d,]+(?:\.\d+)?)"
        r"\s*(亿元|万元|万|元)?",
        text,
    )

    if match:

        raw = match.group(0)

        return {
            "value": money_to_yuan(
                match.group(2),
                match.group(3) or match.group(1) or "万元",
            ),
            "raw": raw,
            "source": "工程合同估算价",
            "confidence": "HIGH",
        }

    match = re.search(
        r"(?:发包估价|招标金额|建安工程费|工程费用)"
        r"(?:\s*[（(]\s*(万元|亿元|元)\s*[）)])?"
        r"\s*(?:为|约|[:：=])?\s*(?:人民币\s*)?[¥￥]?\s*"
        r"([\d,]+(?:\.\d+)?)\s*(亿元|万元|万|元)?",
        text,
    )
    if match:
        return {
            "value": money_to_yuan(match.group(2), match.group(3) or match.group(1) or "万元"),
            "raw": match.group(0),
            "source": "工程投资金额",
            "confidence": "MEDIUM",
        }

    # -----------------------------------------
    # 第二优先：
    # 投资约306.56万元
    #
    # 这个不是严格意义上的合同估算价，
    # 所以标记 MEDIUM
    # -----------------------------------------

    match = re.search(
        r"(?:项目总投资|总投资|投资)\s*(?:约|为|[:：])?\s*"
        r"([\d,]+(?:\.\d+)?)"
        r"\s*(亿元|万元|万|元)",
        text,
    )

    if match:

        return {
            "value": money_to_yuan(
                match.group(1),
                match.group(2),
            ),
            "raw": match.group(0),
            "source": "投资约",
            "confidence": "MEDIUM",
        }

    return {
        "value": None,
        "raw": None,
        "source": None,
        "confidence": None,
    }


# =========================================================
# 控制价
# =========================================================

def extract_control_price(text):

    text = normalize_money_text(text)

    """
    只有存在明确数字时才认为抓到控制价。

    以下内容不会被认为是控制价：
    最高投标限价为B
    最高投标限价×30%
    最高投标限价文件下载
    """

    patterns = [
        (
            r"(最高投标限价|招标控制价|最高限价)"
            r"\s*金额\s*(?:为|约|[:：=])\s*(?:人民币\s*)?[¥￥]?\s*"
            r"([\d,]+(?:\.\d+)?)"
            r"\s*(亿元|万元|万|元)?"
        ),
        (
            r"(最高投标限价|招标控制价|最高限价)"
            r"\s*(?:金额)?\s*(?:为|约|[:：=])\s*(?:人民币\s*)?[¥￥]?\s*"
            r"([\d,]+(?:\.\d+)?)"
            r"\s*(亿元|万元|万|元)"
        ),

        (
            r"(最高投标限价|招标控制价|最高限价)"
            r"\s*[（(]\s*万元\s*[）)]"
            r"\s*(?:为|[:：=])?\s*(?:人民币\s*)?[¥￥]?\s*"
            r"([\d,]+(?:\.\d+)?)"
        ),
        (
            r"(最高投标限价|招标控制价|最高限价)"
            r"\s*[:：]?\s*人民币?\s*"
            r"([\d,]+(?:\.\d+)?)"
            r"\s*(亿元|万元|万|元)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if not match:
            continue

        if len(match.groups()) == 3:

            value = money_to_yuan(
                match.group(2),
                match.group(3) or "元",
            )

        else:

            value = money_to_yuan(
                match.group(2),
                "万元",
            )

        return {
            "value": value,
            "raw": match.group(0),
            "status": "FOUND",
        }

    # -----------------------------------------
    # 页面提到了最高投标限价，
    # 但没有披露明确金额
    # -----------------------------------------

    if "最高投标限价" in text:

        if (
            "最高投标限价文件下载"
            in text
        ):
            status = "NEEDS_LIMIT_PRICE_FILE"

        else:
            status = "MENTIONED_BUT_NO_VALUE"

        return {
            "value": None,
            "raw": None,
            "status": status,
        }

    return {
        "value": None,
        "raw": None,
        "status": "NOT_FOUND",
    }


# =========================================================
# 暂列金额
# =========================================================

def extract_provisional_sum(text):

    text = normalize_money_text(text)

    pattern = re.compile(
        r"(?:暂列金额|暂列金)"
        r"(?:\s*[（(][^）)]{0,24}[）)])?"
        r"\s*(?:金额)?\s*(?:为|约|[:：=])?\s*(?:人民币\s*)?[¥￥]?\s*"
        r"([\d,]+(?:\.\d+)?)"
        r"\s*(亿元|万元|万|元)?"
    )

    for match in pattern.finditer(text):

        numeric_value = float(match.group(1).replace(",", ""))
        explicit_unit = match.group(2)

        # PDF表格转文本后，下一行的序号可能紧跟在“暂列金额”后面，
        # 例如“暂列金额 3.2 其中：专业工程暂估价 218000.00”。
        # 没有金额单位的小数且数值小于100，通常是3.1/3.2一类行号，
        # 不能作为暂列金额；继续寻找同页后续的真实金额。
        if explicit_unit is None and numeric_value < 100:
            continue

        before = text[
            max(
                0,
                match.start() - 120,
            ):
            match.start()
        ]

        # -------------------------------------
        # 如果是：
        #
        # 专业工程暂估价、暂列金额合计...
        #
        # 这个数字不能当成单独暂列金额
        # -------------------------------------

        if (
            "专业工程暂估价"
            in before
        ):
            continue

        return {
            "value": money_to_yuan(
                match.group(1),
                explicit_unit or "元",
            ),
            "raw": match.group(0),
            "status": "FOUND",
        }

    # -----------------------------------------
    # 检查是否只公布了合计金额
    # -----------------------------------------

    combined = re.search(
        r"专业工程暂估价"
        r".{0,150}?"
        r"暂列金额"
        r".{0,80}?"
        r"(?:为|[:：])\s*"
        r"([\d,]+(?:\.\d+)?)"
        r"\s*(亿元|万元|万|元)",
        text,
    )

    if combined:

        return {
            "value": None,
            "raw": combined.group(0),
            "status": "COMBINED_AMOUNT_ONLY",
        }

    return {
        "value": None,
        "raw": None,
        "status": "NOT_FOUND",
    }


# =========================================================
# 单位名称
# =========================================================

KNOWN_OWNER_CORRECTIONS = {
    "江苏川?实业集团有限公司": "江苏川昇实业集团有限公司",
    "南通海?开发建设有限公司": "南通海璟开发建设有限公司",
}


def normalize_owner_name(value):
    value = clean_text(value)
    if not value:
        return None

    # 部分源站公告把 Word 特殊字体字符转换成问号。只对经过其他公开
    # 招标来源核实的单位名称做定向修正，避免猜测未知字符。
    value = KNOWN_OWNER_CORRECTIONS.get(value, value)

    # 防止“项目建设采用：自建/代建”被错误并入项目业主名称。
    value = re.split(r"\s*项目建设采用\s*[:：]", value, maxsplit=1)[0].strip(" 、,，")
    return value or None

def extract_owner(text):

    patterns = [
        # 项目业主为 XXX，
        r"项目业主(?:为)?\s*[:：]?\s*"
        r"([^，。；]{2,100}?)"
        r"(?=\s*[，。；])",
        r"(?:业主单位|建设单位(?:名称)?|项目法人)\s*[:：]\s*"
        r"([^，。；\n]{2,100}?)"
        r"(?=\s*(?:招标人|联系人|地址|，|。|；|$))",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            value = normalize_owner_name(
                match.group(1)
            )

            if value:
                return value

    return None


def extract_tenderer(text):

    patterns = [
        r"招标人为\s*[:：]?\s*"
        r"([^，。；]{2,100}?)"
        r"(?=\s*[，。；])",

        r"招标人\s*[:：]\s*"
        r"([^，。；]{2,100}?)"
        r"(?=\s+招标代理机构|[，。；])",

        r"(?:招标单位|发包人|招标主体)\s*[:：]\s*"
        r"([^，。；\n]{2,100}?)"
        r"(?=\s*(?:招标代理机构|联系人|地址|，|。|；|$))",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:

            value = normalize_owner_name(
                match.group(1)
            )

            if value:
                return value

    return None


def datetime_is_after(candidate, reference):
    """业务日期校验：截止时间必须严格晚于公告发布时间。"""
    if not candidate:
        return False
    if not reference:
        return True
    try:
        return datetime.strptime(candidate, "%Y-%m-%d %H:%M:%S") > datetime.strptime(
            reference, "%Y-%m-%d %H:%M:%S"
        )
    except (TypeError, ValueError):
        return False


def extract_valid_datetime_after_anchor(text, anchors, reference=None, window=180):
    """逐个检查同一锚点的所有命中，跳过正文中的历史日期和无效日期。"""
    for anchor in anchors:
        for match in re.finditer(anchor, text, re.I):
            snippet = text[match.end():match.end() + window]
            value = parse_datetime_text(snippet)
            if datetime_is_after(value, reference):
                return value
    return None


def infer_project_type(project_name, text):
    """结构化字段缺失时，根据项目名称及正文关键词做保守分类。"""
    haystack = f"{project_name or ''} {text or ''}"[:5000]
    rules = (
        ("工程监理", ("监理",)),
        ("设计", ("勘察设计", "方案设计", "施工图设计", "工程设计")),
        ("材料设备采购", ("设备采购", "材料采购", "货物采购")),
        ("装饰装修", ("装饰装修", "装修工程", "修缮改造")),
        ("园林绿化", ("园林绿化", "景观绿化", "绿化工程")),
        ("水利", ("水利工程", "河道整治", "泵站工程", "灌区")),
        ("电力", ("电力工程", "变电站", "输电线路", "光伏")),
        ("市政工程施工", ("市政工程", "道路工程", "污水管网", "供水管网", "排水工程")),
        ("房屋建筑施工", ("房屋建筑", "施工总承包", "厂房", "住宅", "办公楼", "教学楼")),
    )
    for project_type, keywords in rules:
        if any(keyword in haystack for keyword in keywords):
            return project_type
    return None


# =========================================================
# 主解析函数
# =========================================================

def parse_detail_html(
    html,
    row_id=None,
    detail_url=None,
    region_raw=None,
):

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    table = extract_table_fields(
        soup
    )

    project_code = table.get(
        "项目编号"
    )

    parent_project_name = table.get(
        "项目名称"
    )

    section_code = table.get(
        "标段编号"
    )

    section_name = table.get(
        "标段名称"
    )

    # -----------------------------------------
    # 系统里的“项目名称”
    # 使用标段名称更合理
    # -----------------------------------------

    project_name = (
        section_name
        or parent_project_name
    )

    project_type = table.get(
        "工程类型"
    )
    if not project_type:
        project_type = infer_project_type(project_name, page_text)

    publish_time = parse_datetime_text(
        table.get(
            "公告开始时间"
        )
    )

    if not publish_time:
        publish_time = extract_datetime_after_anchor(
            page_text,
            [
                r"公告(?:发布|开始)?时间\s*(?:为|[:：])?",
                r"公告发布日期\s*(?:为|[:：])?",
                r"发布时间\s*(?:为|[:：])?",
                r"发布日期\s*(?:为|[:：])?",
            ],
        )

    # -----------------------------------------
    # 投标截止时间
    # -----------------------------------------

    bid_deadline = parse_datetime_text(table.get("投标截止时间"))
    if not datetime_is_after(bid_deadline, publish_time):
        bid_deadline = None
    if not bid_deadline:
        bid_deadline = (
            extract_valid_datetime_after_anchor(
            page_text,
            [
                r"资格审查登记截止时间\s*(?:为|[:：])?",
                r"资格审查(?:申请文件)?(?:递交)?截[至止]时间\s*(?:为|[:：])?",
                r"资格预审申请文件递交截止时间\s*(?:为|[:：])?",
                (
                    r"投标文件递交的截止时间"
                    r"(?:\s*[（(].{0,50}?"
                    r"投标截止时间.{0,50}?[）)])?"
                    r"\s*为"
                ),

                (
                    r"投标截止时间\s*"
                    r"[（(][^）)]{0,50}[）)]\s*"
                    r"(?:为|[:：])?"
                ),
                r"投标截止时间\s*为\s*[:：]?",
                r"投标文件递交截止时间\s*(?:为|[:：])?",
                r"递交投标文件截止时间\s*(?:为|[:：])?",
                r"递交截止时间\s*(?:为|[:：])?",
                r"申请截止时间\s*(?:为|[:：])?",
            ],
            reference=publish_time,
            )
        )

    # -----------------------------------------
    # 开标时间
    #
    # 没写就 null，
    # 不自动等同于投标截止时间
    # -----------------------------------------

    open_bid_time = parse_datetime_text(table.get("开标时间"))
    if open_bid_time and publish_time and not datetime_is_after(open_bid_time, publish_time):
        open_bid_time = None
    if not open_bid_time:
        open_bid_time = (
            extract_valid_datetime_after_anchor(
            page_text,
            [
                r"开标时间\s*[:：为]?",
                r"开标日期\s*[:：为]?",
            ],
            reference=publish_time,
            )
        )

    owner_name = extract_owner(
        page_text
    ) or normalize_owner_name(table.get("项目业主"))

    tenderer_name = extract_tenderer(
        page_text
    ) or normalize_owner_name(table.get("招标人"))

    estimated = extract_estimated_amount(
        page_text
    )

    control = extract_control_price(
        page_text
    )

    provisional = extract_provisional_sum(
        page_text
    )

    # 部分公告仅在顶部表格中展示金额，仍复用带金额单位校验的规则。
    if estimated["value"] is None and table.get("预估合同额"):
        estimated = extract_estimated_amount(
            f"{table.get('预估合同额__label') or '合同估算价'}：{table['预估合同额']}"
        )
    if control["value"] is None and table.get("招标控制价"):
        control = extract_control_price(
            f"{table.get('招标控制价__label') or '招标控制价'}：{table['招标控制价']}"
        )
    if provisional["value"] is None and table.get("暂列金额"):
        provisional = extract_provisional_sum(
            f"{table.get('暂列金额__label') or '暂列金额'}：{table['暂列金额']}"
        )

    result = {
        # ==============================
        # 系统标识
        # ==============================

        "project_id": (
            f"JS-{row_id}"
            if row_id
            else None
        ),

        # ==============================
        # 基础信息
        # ==============================

        "project_name": project_name,

        "parent_project_name":
            parent_project_name,

        "project_code":
            project_code,

        "section_code":
            section_code,

        "project_type":
            project_type,

        "province":
            "江苏省",

        "city":
            None,

        "district":
            None,

        "region_raw":
            region_raw or table.get("项目所在地"),

        # 注意：
        # 业主和招标人分开
        "owner_name":
            owner_name,

        "tenderer_name":
            tenderer_name,

        # ==============================
        # 时间
        # ==============================

        "publish_time":
            publish_time,

        "open_bid_time":
            open_bid_time,

        "bid_deadline":
            bid_deadline,

        # ==============================
        # 造价
        # ==============================

        "control_price":
            control["value"],

        "control_price_status":
            control["status"],

        "control_price_raw":
            control["raw"],

        "estimated_contract_amount":
            estimated["value"],

        "estimated_contract_amount_source":
            estimated["source"],

        "estimated_contract_amount_confidence":
            estimated["confidence"],

        "estimated_contract_amount_raw":
            estimated["raw"],

        "provisional_sum":
            provisional["value"],

        "provisional_sum_status":
            provisional["status"],

        "provisional_sum_raw":
            provisional["raw"],

        # ==============================
        # 企业内部字段
        # ==============================

        "tracking_stage":
            "LEAD",

        "rating":
            "UNRATED",

        "responsible_person":
            None,

        # ==============================
        # 来源
        # ==============================

        "source_platform":
            "江苏建设工程招标网",

        "source_row_id":
            row_id,

        "source_url":
            detail_url,
    }

    return result


# =========================================================
# 本地三项目测试
# =========================================================

if __name__ == "__main__":

    root_dir = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    test_root = (
        root_dir
        / "数据"
        / "raw"
        / "江苏详情页测试"
    )

    row_ids = [
        "897009",
        "897003",
        "897002",
    ]

    results = []

    for row_id in row_ids:

        html_file = (
            test_root
            / row_id
            / f"{row_id}_page.html"
        )

        print(
            "\n=================================="
        )

        print(
            f"测试项目：{row_id}"
        )

        if not html_file.exists():

            print(
                f"找不到文件：{html_file}"
            )

            continue

        html = html_file.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        result = parse_detail_html(
            html,
            row_id=row_id,
        )

        results.append(
            result
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

    output_file = (
        root_dir
        / "数据"
        / "clean"
        / "parser_test.json"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\n测试结果已保存：{output_file}"
    )
