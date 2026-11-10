from __future__ import annotations

import base64
import csv
import io
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path


def emit_progress(percent: int, stage: str, detail: str = "") -> None:
    """Write machine-readable progress without contaminating the final JSON stdout."""
    message = {"type": "progress", "percent": max(0, min(100, percent)), "stage": stage, "detail": detail}
    # Write UTF-8 bytes directly. Windows console code pages otherwise corrupt
    # Chinese progress text before Node can read the child-process stream.
    payload = ("COST_PROGRESS " + json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
    sys.stderr.buffer.write(payload)
    sys.stderr.buffer.flush()

from openpyxl import load_workbook


DATA_ROOT_CANDIDATES = [
    Path(os.getenv("COST_DATA_ROOT", "")) if os.getenv("COST_DATA_ROOT") else None,
    Path(r"D:\AI工程造价\AI工程造价系统"),
    Path(r"D:\AI工程造价系统"),
    Path(r"D:\AI+BIM"),
]
DATA_ROOT = next((path for path in DATA_ROOT_CANDIDATES if path and path.exists()), Path(r"D:\AI工程造价系统"))
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
JIANGSU_DATA_ROOT = REPOSITORY_ROOT / "modules" / "module-2" / "data" / "江苏省"
PROVINCE_PROFESSION_FILES = {
    "山东省": {
        "建筑工程": DATA_ROOT / "建筑工程清单库" / "山东2013清单规范-建筑工程.xlsx",
        "安装工程": DATA_ROOT / "安装工程清单库" / "山东2013清单规范-安装工程.xlsx",
        "市政工程": DATA_ROOT / "市政工程清单库" / "山东2013清单规范-市政工程.xlsx",
        "矿山工程": DATA_ROOT / "矿山工程清单库" / "山东2013清单规范-矿山工程.xlsx",
        "园林绿化工程": DATA_ROOT / "园林绿化工程清单库" / "山东2013清单规范-园林绿化工程.xlsx",
    },
    "江苏省": {
        "建筑工程": JIANGSU_DATA_ROOT / "清单" / "房屋建筑与装饰工程" / "江苏2024清单规范-房屋建筑与装饰工程.xlsx",
    },
}
QUOTA_FILE = DATA_ROOT / "建筑工程价目表.json"


def catalog_paths(province: str, profession: str) -> tuple[Path, Path | None]:
    province_files = PROVINCE_PROFESSION_FILES.get(province)
    if not province_files:
        raise ValueError(f"{province}清单库待补充")
    list_file = province_files.get(profession)
    if not list_file:
        raise ValueError(f"{province}暂未配置{profession}清单库")
    if not list_file.exists():
        raise ValueError(f"{province}{profession}清单文件不存在：{list_file}")
    quota_file = QUOTA_FILE if province == "山东省" and profession == "建筑工程" and QUOTA_FILE.exists() else None
    return list_file, quota_file

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class AIClient:
    """OpenAI-compatible client used for semantic parsing and quota selection.

    Secrets stay in server environment variables. Every call has a deterministic
    local fallback so a provider outage never makes the costing module unusable.
    """

    def __init__(self):
        self.api_key = os.getenv("COST_AI_API_KEY", "").strip()
        self.base_url = os.getenv("COST_AI_BASE_URL", "https://c4ai.ccccltd.cn/api/compatible/v1").strip().rstrip("/")
        self.model = os.getenv("COST_AI_MODEL", "jiaorong-kimi-k2.6").strip()
        self.local_provider = self.base_url.startswith(("http://127.0.0.1", "http://localhost"))
        self.configured = bool(self.api_key) or self.local_provider
        self.enabled = os.getenv("COST_AI_ENABLED", "true").lower() not in {"0", "false", "off"} and self.configured
        self.timeout = max(10, min(120, int(os.getenv("COST_AI_TIMEOUT", "45"))))
        self.calls = 0
        self.failures = 0
        self.errors = []

    @property
    def endpoint(self):
        return self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"

    def json_completion(self, system_prompt: str, data: dict) -> dict | None:
        if not self.enabled:
            return None
        request_body = json.dumps({
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ],
        }, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.endpoint, data=request_body, method="POST", headers=headers)
        self.calls += 1
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"].strip()
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I)
            return json.loads(content)
        except Exception as exc:
            self.failures += 1
            self.enabled = False
            message = f"{type(exc).__name__}: {exc}"
            if message not in self.errors:
                self.errors.append(message[:240])
            return None

    def field_mapping(self, headers: list[str], samples: list[list]) -> dict[str, dict]:
        response = self.json_completion(
            "你是工程造价清单解析专家。根据任意表头和样本内容，将列映射为标准字段。"
            "只允许使用code、name、features、unit、quantity五个标准字段，每个标准字段最多映射一次。"
            "无法确定的列不要映射，禁止编造原文件不存在的数据。返回JSON："
            '{"mappings":[{"sourceHeader":"原字段","standardField":"name","confidence":0到1,"reason":"简短理由"}]}。',
            {"headers": headers, "sampleRows": samples[:8]},
        )
        result = {}
        valid_fields = set(FIELD_DEFINITIONS)
        valid_headers = set(headers)
        for item in (response or {}).get("mappings", []):
            source = text(item.get("sourceHeader"))
            field = text(item.get("standardField"))
            if source in valid_headers and field in valid_fields and field not in result:
                result[field] = {
                    "column": headers.index(source),
                    "confidence": max(0.0, min(1.0, number(item.get("confidence")))),
                    "reason": text(item.get("reason")),
                }
        return result

    def choose_matches(self, entries: list[dict]) -> dict[str, dict]:
        if not entries:
            return {}
        response = self.json_completion(
            "你是工程造价清单与定额匹配专家。只能从每个项目提供的候选清单和候选定额中选择，"
            "禁止生成不存在的编码或价格。结合名称、项目特征、单位和施工工艺判断。"
            "一个清单项目通常需要多条定额共同覆盖，必须选择能够完整覆盖工作内容的最小、不重复组合，"
            "不要把互斥施工方案同时选入。每个项目最多选择8条定额；coefficient是将该定额单位价格换算到"
            "当前清单计量单位所需的正数系数，无法可靠换算时填1并在reason中明确要求复核。无可靠定额则返回空数组。返回JSON："
            '{"results":[{"id":"项目id","listCode":"候选编码或空","quotaSelections":'
            '[{"code":"候选定额编码","coefficient":1,"reason":"该定额覆盖的工序"}],'
            '"confidence":0到1,"reason":"组合选择依据或无法确定原因"}]}。',
            {"projects": entries},
        )
        return {text(item.get("id")): item for item in (response or {}).get("results", []) if text(item.get("id"))}

    def expand_match_queries(self, entries: list[dict]) -> dict[str, dict]:
        """Generate independent retrieval queries before the model sees candidates.

        This prevents the first local top-N ranking from permanently excluding a
        semantically correct catalog item. The generated terms are searched
        against the complete local list and quota libraries.
        """
        if not entries:
            return {}
        response = self.json_completion(
            "你是工程造价检索专家。不要选择答案，也不要编造价格。根据项目名称、项目特征和单位，"
            "独立生成用于检索完整清单库和完整定额库的规范化短语、同义词和施工工艺词。"
            "不要受任何候选列表影响。每类最多4个短语；可能的编码仅在十分确定时给出。返回JSON："
            '{"results":[{"id":"项目id","listSearchTerms":["短语"],'
            '"quotaSearchTerms":["短语"],"possibleCodes":["编码"]}]}。',
            {"projects": entries},
        )
        return {text(item.get("id")): item for item in (response or {}).get("results", []) if text(item.get("id"))}

    def summary(self):
        mode = "AI+定额双驱动" if self.enabled and self.calls > self.failures else "本地规则+定额降级"
        return {
            "configured": self.configured,
            "enabled": self.enabled,
            "mode": mode,
            "provider": self.base_url if self.enabled else "未配置",
            "model": self.model if self.enabled else "未配置",
            "calls": self.calls,
            "failures": self.failures,
            "errors": self.errors,
        }


def text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def number(value) -> float:
    cleaned = re.sub(r"[^0-9.\-]", "", text(value).replace(",", ""))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def normalize_quota_selections(choice: dict | None) -> list[dict]:
    """Normalize the new multi-quota response and legacy single-code responses."""
    if not choice:
        return []
    raw = choice.get("quotaSelections")
    if not isinstance(raw, list):
        raw = [{"code": code} for code in choice.get("quotaCodes", [])] if isinstance(choice.get("quotaCodes"), list) else []
    legacy_code = text(choice.get("quotaCode"))
    if not raw and legacy_code:
        raw = [{"code": legacy_code}]
    result = []
    seen = set()
    for entry in raw:
        entry = entry if isinstance(entry, dict) else {"code": entry}
        code = text(entry.get("code"))
        if not code or code in seen:
            continue
        coefficient = number(entry.get("coefficient")) or 1.0
        if coefficient <= 0 or coefficient > 10000:
            coefficient = 1.0
        result.append({"code": code, "coefficient": coefficient, "reason": text(entry.get("reason"))})
        seen.add(code)
        if len(result) == 8:
            break
    return result


def quota_contribution(item: dict, tax_mode: str, coefficient=1.0, reason="") -> dict:
    prices = item["general" if tax_mode == "一般计税" else "simple"]
    coefficient = max(0.0, number(coefficient))
    return {
        "code": item.get("code", ""), "name": item.get("name", ""),
        "unit": item.get("unit", ""), "chapter": item.get("chapter", ""),
        "coefficient": coefficient, "reason": reason,
        "unitLabour": prices["labour"] * coefficient,
        "unitMaterial": prices["material"] * coefficient,
        "unitMachine": prices["machine"] * coefficient,
        "unitPrice": prices["unitPrice"] * coefficient,
    }


def sum_quota_contributions(selections: list[dict]) -> dict:
    return {
        "unitPrice": sum(item.get("unitPrice", 0.0) for item in selections),
        "labour": sum(item.get("unitLabour", 0.0) for item in selections),
        "material": sum(item.get("unitMaterial", 0.0) for item in selections),
        "machine": sum(item.get("unitMachine", 0.0) for item in selections),
    }


def normalized(value) -> str:
    return re.sub(r"[\s\-—_（）()、，,；;:/]+", "", text(value).lower())


def header_index(headers, aliases):
    for index, header in enumerate(headers):
        key = normalized(header)
        if any(normalized(alias) in key or key in normalized(alias) for alias in aliases):
            return index
    return None


FIELD_DEFINITIONS = {
    "code": {
        "label": "项目编码",
        "aliases": ["项目编码", "清单编码", "工程编码", "项目编号", "清单编号", "编码", "编号", "code"],
    },
    "name": {
        "label": "项目名称",
        "aliases": ["项目名称", "清单名称", "工程项目", "工程名称", "工作项目", "工作内容", "分部分项名称", "名称", "项目", "item", "description"],
    },
    "features": {
        "label": "项目特征",
        "aliases": ["项目特征", "特征描述", "项目描述", "工作特征", "技术要求", "技术说明", "规格型号", "规格描述", "特征", "说明", "specification"],
    },
    "unit": {
        "label": "计量单位",
        "aliases": ["计量单位", "计价单位", "工程单位", "单位", "unit"],
    },
    "quantity": {
        "label": "工程量",
        "aliases": ["工程数量", "清单工程量", "清单量", "暂定数量", "暂定量", "数量", "工程量", "qty", "quantity"],
    },
}
UNIT_VALUES = {
    "m", "m2", "m3", "㎡", "m²", "平方", "平方米", "立方", "立方米", "米", "km", "公里",
    "t", "吨", "kg", "千克", "个", "项", "套", "台", "樘", "块", "组", "座", "处", "根", "榀",
    "延米", "工日", "台班", "系统", "回路", "点", "只", "件", "幅", "间", "层",
}


def alias_score(header, aliases) -> float:
    key = normalized(header)
    if not key:
        return 0.0
    best = 0.0
    for alias in aliases:
        candidate = normalized(alias)
        if key == candidate:
            best = max(best, 1.0)
        elif candidate in key or key in candidate:
            best = max(best, 0.82)
        else:
            best = max(best, SequenceMatcher(None, key, candidate).ratio() * 0.55)
    return best


def is_number_like(value) -> bool:
    raw = text(value).replace(",", "")
    return bool(raw and re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:%|元)?", raw))


def is_code_like(value) -> bool:
    raw = re.sub(r"[.\-\s]", "", text(value))
    return bool(re.fullmatch(r"[A-Za-z0-9]{6,22}", raw) and any(char.isdigit() for char in raw))


def content_score(field: str, values: list) -> float:
    samples = [text(value) for value in values if text(value)][:30]
    if not samples:
        return 0.0
    numeric = sum(is_number_like(value) for value in samples) / len(samples)
    codes = sum(is_code_like(value) for value in samples) / len(samples)
    units = sum(normalized(value) in {normalized(unit) for unit in UNIT_VALUES} for value in samples) / len(samples)
    average_length = sum(len(value) for value in samples) / len(samples)
    chinese_text = sum(bool(re.search(r"[\u4e00-\u9fff]", value)) and not is_number_like(value) for value in samples) / len(samples)
    if field == "quantity":
        return numeric
    if field == "code":
        return codes
    if field == "unit":
        return units
    if field == "features":
        return min(1.0, chinese_text * 0.45 + max(0.0, average_length - 12) / 45)
    if field == "name":
        length_fit = 1.0 - min(1.0, abs(average_length - 12) / 30)
        return chinese_text * 0.7 + length_fit * 0.3
    return 0.0


def detect_header_row(matrix: list[list]) -> int:
    best = (-1.0, 0)
    for index, row in enumerate(matrix[:40]):
        values = [text(cell) for cell in row]
        nonempty = [value for value in values if value]
        if not nonempty:
            continue
        alias_hits = 0.0
        fields_hit = 0
        for definition in FIELD_DEFINITIONS.values():
            score = max((alias_score(value, definition["aliases"]) for value in nonempty), default=0.0)
            alias_hits += score
            fields_hit += score >= 0.72
        next_rows = matrix[index + 1 : index + 5]
        data_density = sum(any(text(cell) for cell in row) for row in next_rows) / max(1, len(next_rows))
        score = alias_hits * 3 + fields_hit * 2 + min(len(nonempty), 8) * 0.08 + data_density
        if score > best[0]:
            best = (score, index)
    return best[1]


def compose_headers(matrix: list[list], header_row: int) -> list[str]:
    width = max((len(row) for row in matrix), default=0)
    headers = []
    for column in range(width):
        parts = []
        for index in range(max(0, header_row - 1), header_row + 1):
            value = text(matrix[index][column]) if column < len(matrix[index]) else ""
            if value and value not in parts:
                parts.append(value)
        headers.append(" / ".join(parts) or f"第{column + 1}列")
    return headers


def infer_fields(headers: list[str], data_rows: list[list], ai: AIClient | None = None) -> tuple[dict, list[dict]]:
    scores = []
    for field, definition in FIELD_DEFINITIONS.items():
        for column, header in enumerate(headers):
            values = [row[column] if column < len(row) else "" for row in data_rows[:40]]
            header_value = alias_score(header, definition["aliases"])
            sample_value = content_score(field, values)
            combined = header_value * 0.68 + sample_value * 0.32
            scores.append((combined, header_value, sample_value, field, column))
    fields, used = {}, set()
    mappings = []
    # Exact standard headers are authoritative. In particular, when a source has
    # both "工程名称" (group/project heading) and "项目名称" (bill item), AI must
    # not replace the exact 项目名称 column with the broader alias 工程名称.
    for field, definition in FIELD_DEFINITIONS.items():
        expected = normalized(definition["label"])
        column = next((index for index, header in enumerate(headers) if normalized(header) == expected), None)
        if column is None or column in used:
            continue
        fields[field] = column
        used.add(column)
        mappings.append({
            "standardField": field,
            "standardLabel": definition["label"],
            "sourceHeader": headers[column],
            "column": column + 1,
            "confidence": 100.0,
            "method": "标准表头精确匹配",
            "reason": "原始表头与标准字段完全一致，优先级高于AI和别名推断",
        })
    ai_mappings = ai.field_mapping(headers, [[text(cell) for cell in row] for row in data_rows[:8]]) if ai else {}
    for field, decision in ai_mappings.items():
        column = decision["column"]
        if field in fields or column in used:
            continue
        fields[field] = column
        used.add(column)
        mappings.append({
            "standardField": field,
            "standardLabel": FIELD_DEFINITIONS[field]["label"],
            "sourceHeader": headers[column],
            "column": column + 1,
            "confidence": round(decision["confidence"] * 100, 1),
            "method": "AI大模型语义识别",
            "reason": decision["reason"],
        })
    for combined, header_value, sample_value, field, column in sorted(scores, reverse=True):
        threshold = 0.34 if field in {"name", "quantity"} else 0.42
        if field in fields or column in used or combined < threshold:
            continue
        fields[field] = column
        used.add(column)
    # A document with unfamiliar headings must still be ingestible: use the strongest
    # textual column as the item name and keep uncertain mappings visible for review.
    if "name" not in fields:
        candidates = []
        for column in range(len(headers)):
            values = [row[column] if column < len(row) else "" for row in data_rows[:40]]
            candidates.append((content_score("name", values), column))
        if candidates:
            _, fields["name"] = max(candidates)
            used.add(fields["name"])
    for field, column in fields.items():
        if any(item["standardField"] == field for item in mappings):
            continue
        match = max((item for item in scores if item[3] == field and item[4] == column), default=(0, 0, 0, field, column))
        combined, header_value, sample_value, _, _ = match
        confidence = round(min(99.0, max(35.0, combined * 100)), 1)
        mappings.append({
            "standardField": field,
            "standardLabel": FIELD_DEFINITIONS[field]["label"],
            "sourceHeader": headers[column],
            "column": column + 1,
            "confidence": confidence,
            "method": "表头+内容推断" if header_value >= 0.45 and sample_value >= 0.25 else ("表头语义" if header_value >= sample_value else "样本内容推断"),
            "reason": "AI不可用或未给出确定映射，使用本地规则兜底",
        })
    return fields, sorted(mappings, key=lambda item: item["column"])


def parse_matrix(matrix: list[list], source_name: str, ai: AIClient | None = None) -> tuple[list[dict], dict]:
    matrix = [list(row) for row in matrix if any(text(cell) for cell in row)]
    if not matrix:
        return [], {"sourceName": source_name, "headerRow": 0, "mappings": [], "unmappedHeaders": []}
    header_row = detect_header_row(matrix)
    headers = compose_headers(matrix, header_row)
    data_rows = matrix[header_row + 1 :]
    fields, mappings = infer_fields(headers, data_rows, ai)
    rows = []
    for source_row, row in enumerate(data_rows, header_row + 2):
        raw_fields = {headers[index]: text(value) for index, value in enumerate(row) if text(value)}
        if not raw_fields:
            continue
        def cell(field):
            index = fields.get(field)
            return row[index] if index is not None and index < len(row) else ""
        name = text(cell("name"))
        # Skip obvious repeated headings and totals, but never reject a row only because
        # an expected source heading was not present.
        if name in {"项目名称", "清单名称", "名称"} or normalized(name) in {"合计", "总计", "小计"}:
            continue
        nonempty_values = [value for value in raw_fields.values() if value]
        if not name:
            name = max((value for value in nonempty_values if not is_number_like(value)), key=len, default=f"未命名清单项（第{source_row}行）")
        quantity_raw = cell("quantity")
        rows.append({
            "sourceRow": source_row,
            "sourceSheet": source_name,
            "originalCode": text(cell("code")),
            "name": name,
            "features": text(cell("features")),
            "unit": text(cell("unit")),
            "quantity": number(quantity_raw),
            "quantityRecognized": bool(text(quantity_raw) and is_number_like(quantity_raw)),
            "rawFields": raw_fields,
        })
    mapped_columns = {item["column"] - 1 for item in mappings}
    parsing = {
        "sourceName": source_name,
        "headerRow": header_row + 1,
        "mappings": mappings,
        "unmappedHeaders": [header for index, header in enumerate(headers) if index not in mapped_columns and header],
    }
    return rows, parsing


def configure_tesseract():
    try:
        import pytesseract
        candidates = [
            shutil.which("tesseract"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        executable = next((path for path in candidates if path and Path(path).exists()), None)
        if executable:
            pytesseract.pytesseract.tesseract_cmd = executable
        return pytesseract if executable else None
    except ImportError:
        return None


def read_pdf(raw: bytes, ai: AIClient | None = None) -> tuple[list[dict], list[dict], list[str]]:
    import pdfplumber
    rows, parsing, warnings = [], [], []
    with pdfplumber.open(io.BytesIO(raw)) as document:
        for page_index, page in enumerate(document.pages, 1):
            tables = page.extract_tables() or []
            for table_index, table in enumerate(tables, 1):
                parsed, meta = parse_matrix(table, f"第{page_index}页·表{table_index}", ai)
                rows.extend(parsed)
                parsing.append(meta)
            if not tables:
                page_text = page.extract_text() or ""
                lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                if lines:
                    # Loose PDF text remains processable and reviewable instead of failing.
                    for line_index, line in enumerate(lines, 1):
                        rows.append({
                            "sourceRow": line_index,
                            "sourceSheet": f"第{page_index}页",
                            "originalCode": "", "name": line, "features": "", "unit": "", "quantity": 0.0,
                            "quantityRecognized": False, "rawFields": {"PDF文本": line},
                        })
                    parsing.append({"sourceName": f"第{page_index}页", "headerRow": 0, "mappings": [{
                        "standardField": "name", "standardLabel": "项目名称", "sourceHeader": "PDF文本",
                        "column": 1, "confidence": 45.0, "method": "PDF文本行推断",
                    }], "unmappedHeaders": []})
        if not rows:
            ocr = configure_tesseract()
            if ocr:
                for page_index, page in enumerate(document.pages, 1):
                    image = page.to_image(resolution=200).original
                    content = ocr.image_to_string(image, lang="chi_sim+eng")
                    for line_index, line in enumerate((item.strip() for item in content.splitlines()), 1):
                        if line:
                            rows.append({"sourceRow": line_index, "sourceSheet": f"第{page_index}页OCR", "originalCode": "", "name": line,
                                         "features": "", "unit": "", "quantity": 0.0, "quantityRecognized": False, "rawFields": {"OCR文本": line}})
                warnings.append("扫描版PDF已通过OCR提取；请重点复核数量、单位和小数点。")
            else:
                raise ValueError("该PDF没有可提取文字或表格，且本机未安装Tesseract OCR；请安装OCR组件后重试")
    return rows, parsing, warnings


def read_rows(file_name: str, encoded: str, ai: AIClient | None = None) -> tuple[list[dict], dict]:
    raw = base64.b64decode(encoded)
    suffix = Path(file_name).suffix.lower()
    parsing, warnings = [], []
    if suffix == ".csv":
        decoded = None
        for encoding in ("utf-8-sig", "gb18030"):
            try:
                decoded = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                pass
        if decoded is None:
            raise ValueError("CSV编码无法识别，请另存为UTF-8格式")
        rows, meta = parse_matrix(list(csv.reader(io.StringIO(decoded))), Path(file_name).name, ai)
        parsing.append(meta)
    elif suffix in {".xlsx", ".xlsm"}:
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        rows = []
        for sheet in workbook.worksheets:
            parsed, meta = parse_matrix([list(row) for row in sheet.iter_rows(values_only=True)], sheet.title, ai)
            rows.extend(parsed)
            parsing.append(meta)
    elif suffix == ".pdf":
        rows, parsing, warnings = read_pdf(raw, ai)
    else:
        raise ValueError("支持xlsx、xlsm、csv和pdf工程量清单")
    if not rows:
        raise ValueError("没有识别到有效清单项目")
    low_confidence = sum(item["confidence"] < 65 for block in parsing for item in block["mappings"])
    missing_quantity = sum(not row["quantityRecognized"] for row in rows)
    if missing_quantity:
        warnings.append(f"{missing_quantity}行未识别到明确工程量，已保留原始数据并标记待复核。")
    return rows, {
        "sheets": parsing,
        "mappedFields": sum(len(block["mappings"]) for block in parsing),
        "lowConfidenceFields": low_confidence,
        "warnings": warnings,
    }


def load_lists(path: Path) -> list[dict]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    matrix = [list(row) for row in sheet.iter_rows(values_only=True)]
    headers = [text(cell) for cell in matrix[0]]
    code_idx = header_index(headers, ["编码"])
    name_idx = header_index(headers, ["名称"])
    unit_idx = header_index(headers, ["单位"])
    result = []
    for row in matrix[1:]:
        name = text(row[name_idx]) if name_idx is not None and name_idx < len(row) else ""
        if not name:
            continue
        result.append({
            "code": text(row[code_idx]).split(".", 1)[0].zfill(9) if code_idx is not None else "",
            "name": name,
            "unit": text(row[unit_idx]) if unit_idx is not None and unit_idx < len(row) else "",
        })
    return result


def price_block(value, general=False):
    value = value or {}
    return {
        "unitPrice": number(value.get("单价（除税）" if general else "单价（含税）")),
        "labour": number(value.get("人工费")),
        "material": number(value.get("材料费（除税）" if general else "材料费（含税）")),
        "machine": number(value.get("机械费（除税）" if general else "机械费（含税）")),
    }


def load_quotas(path: Path) -> list[dict]:
    source = json.loads(path.read_text(encoding="utf-8"))
    result = []
    def walk(node, parents=()):
        if isinstance(node, dict):
            if "定额编号" in node:
                result.append({
                    "code": text(node.get("定额编号")),
                    "name": text(node.get("名称")),
                    "unit": text(node.get("计量单位")),
                    "chapter": " > ".join(parents[-5:]),
                    "simple": price_block(node.get("简易计税")),
                    "general": price_block(node.get("一般计税"), True),
                })
            else:
                for key, value in node.items():
                    walk(value, parents + (text(key),))
        elif isinstance(node, list):
            for value in node:
                walk(value, parents)
    walk(source)
    return result


def catalog_for_ui(payload: dict) -> dict:
    province = payload.get("province", "山东省")
    profession = payload.get("profession", "建筑工程")
    list_file, quota_file = catalog_paths(province, profession)
    tax_key = "general" if payload.get("taxMode", "一般计税") == "一般计税" else "simple"
    lists = load_lists(list_file)
    quotas = load_quotas(quota_file) if quota_file else []
    return {
        "lists": lists,
        "quotas": [{
            "code": item["code"], "name": item["name"], "unit": item["unit"],
            "chapter": item.get("chapter", ""),
            "unitLabour": item[tax_key]["labour"],
            "unitMaterial": item[tax_key]["material"],
            "unitMachine": item[tax_key]["machine"],
        } for item in quotas],
    }


def similarity(query: str, candidate: str, source_unit="", candidate_unit="") -> float:
    left, right = normalized(query), normalized(candidate)
    if not left or not right:
        return 0.0
    ratio = SequenceMatcher(None, left, right).ratio()
    contains = 1.0 if left in right or right in left else 0.0
    common = len(set(left) & set(right)) / max(1, len(set(left)))
    left_bigrams = {left[index:index + 2] for index in range(max(1, len(left) - 1))}
    right_bigrams = {right[index:index + 2] for index in range(max(1, len(right) - 1))}
    bigram = len(left_bigrams & right_bigrams) / max(1, len(left_bigrams | right_bigrams))
    unit_bonus = 0.08 if source_unit and candidate_unit and normalized(source_unit) == normalized(candidate_unit) else 0.0
    return min(1.0, ratio * 0.42 + bigram * 0.25 + common * 0.18 + contains * 0.15 + unit_bonus)


def best_match(query: str, unit: str, candidates: list[dict]):
    ranked = top_matches(query, unit, candidates, 1)
    return ranked[0] if ranked else (0.0, None)


def top_matches(query: str, unit: str, candidates: list[dict], limit=5):
    return sorted(
        ((similarity(query, item["name"] + item.get("chapter", ""), unit, item.get("unit", "")), item) for item in candidates),
        key=lambda value: value[0], reverse=True,
    )[:limit]


def expanded_matches(queries: list[str], unit: str, candidates: list[dict], existing: list, possible_codes: list[str], limit=30):
    """Search the complete library with multiple independent queries and merge results."""
    by_code = {item["code"]: item for item in candidates}
    merged = {item["code"]: (score, item) for score, item in existing}
    for code in possible_codes:
        if code in by_code:
            merged[code] = (1.0, by_code[code])
    for query in queries[:8]:
        for score, item in top_matches(query, unit, candidates, 12):
            previous = merged.get(item["code"])
            if previous is None or score > previous[0]:
                merged[item["code"]] = (score, item)
    return sorted(merged.values(), key=lambda value: value[0], reverse=True)[:limit]


def calculate(payload: dict) -> dict:
    province = payload.get("province", "山东省")
    profession = payload.get("profession", "建筑工程")
    list_file, quota_file = catalog_paths(province, profession)
    emit_progress(8, "读取清单文件", "正在校验文件并识别工作表")
    ai = AIClient()
    rows, parsing = read_rows(payload.get("fileName", ""), payload.get("fileBase64", ""), ai)
    emit_progress(24, "字段智能识别", f"已识别 {len(rows)} 条清单记录")
    lists = load_lists(list_file)
    quotas = load_quotas(quota_file) if quota_file else []
    emit_progress(32, "加载定额数据库", f"清单库 {len(lists)} 条，定额库 {len(quotas)} 条")
    list_by_code = {item["code"]: item for item in lists}
    quota_by_code = {item["code"]: item for item in quotas}
    tax_mode = payload.get("taxMode", "一般计税")
    manage_rate = max(0.0, min(1.0, number(payload.get("manageRate", 15)) / 100))
    profit_rate = max(0.0, min(1.0, number(payload.get("profitRate", 10)) / 100))
    tax_rate = max(0.0, min(1.0, number(payload.get("taxRate", 9)) / 100))
    prepared = []
    ai_requests = []
    ai_match_limit = max(0, min(500, int(os.getenv("COST_AI_MATCH_LIMIT", "150"))))
    for index, row in enumerate(rows[:2000]):
        query = f'{row["name"]} {row["features"]}'.strip()
        source_code = row["originalCode"]
        list_item = list_by_code.get(source_code)
        list_score = 1.0 if list_item else 0.0
        list_candidates = top_matches(query, row["unit"], lists, 20)
        if not list_item:
            list_score, list_item = list_candidates[0] if list_candidates else (0.0, None)
        quota_item = quota_by_code.get(source_code)
        quota_score = 1.0 if quota_item else 0.0
        quota_candidates = top_matches(query + " " + (list_item or {}).get("name", ""), row["unit"], quotas, 20)
        if not quota_item:
            quota_score, quota_item = quota_candidates[0] if quota_candidates else (0.0, None)
        prepared.append({
            "row": row, "listItem": list_item, "quotaItem": quota_item,
            "listScore": list_score, "quotaScore": quota_score,
            "listCandidates": list_candidates, "quotaCandidates": quota_candidates,
        })
        exact = source_code in list_by_code and (not quotas or source_code in quota_by_code)
        if ai.enabled and not exact and len(ai_requests) < ai_match_limit:
            ai_requests.append({
                "id": str(index), "name": row["name"], "features": row["features"], "unit": row["unit"],
            })
        if index == 0 or (index + 1) % 50 == 0 or index + 1 == min(len(rows), 2000):
            ratio = (index + 1) / max(1, min(len(rows), 2000))
            emit_progress(32 + round(ratio * 28), "本地清单与定额初筛", f"已处理 {index + 1}/{min(len(rows), 2000)} 条")
    ai_choices = {}
    request_batches = max(1, (len(ai_requests) + 11) // 12)
    query_expansions = {}
    for batch_index, start in enumerate(range(0, len(ai_requests), 12)):
        query_expansions.update(ai.expand_match_queries(ai_requests[start : start + 12]))
        emit_progress(60 + round((batch_index + 1) / request_batches * 8), "AI全库检索扩展", f"已扩展 {min(start + 12, len(ai_requests))}/{len(ai_requests)} 条检索词")
    enriched_requests = []
    for request in ai_requests:
        index = int(request["id"])
        item = prepared[index]
        expansion = query_expansions.get(request["id"], {})
        possible_codes = [text(code) for code in expansion.get("possibleCodes", []) if text(code)]
        list_queries = [f'{item["row"]["name"]} {item["row"]["features"]}'.strip()]
        list_queries.extend(text(value) for value in expansion.get("listSearchTerms", []) if text(value))
        quota_queries = list(list_queries)
        quota_queries.extend(text(value) for value in expansion.get("quotaSearchTerms", []) if text(value))
        item["listCandidates"] = expanded_matches(list_queries, item["row"]["unit"], lists, item["listCandidates"], possible_codes)
        item["quotaCandidates"] = expanded_matches(quota_queries, item["row"]["unit"], quotas, item["quotaCandidates"], possible_codes)
        enriched_requests.append({
            **request,
            "listCandidates": [{"code": candidate["code"], "name": candidate["name"], "unit": candidate["unit"], "retrievalScore": round(score, 3)} for score, candidate in item["listCandidates"]],
            "quotaCandidates": [{"code": candidate["code"], "name": candidate["name"], "unit": candidate["unit"], "chapter": candidate.get("chapter", ""), "retrievalScore": round(score, 3)} for score, candidate in item["quotaCandidates"]],
        })
    for batch_index, start in enumerate(range(0, len(enriched_requests), 12)):
        ai_choices.update(ai.choose_matches(enriched_requests[start : start + 12]))
        emit_progress(68 + round((batch_index + 1) / request_batches * 14), "AI语义复核", f"已复核 {min(start + 12, len(enriched_requests))}/{len(enriched_requests)} 条疑难项")
    if not ai_requests:
        emit_progress(82, "匹配结果复核", "编码与本地语义匹配已完成")

    results = []
    totals = {"labour": 0.0, "material": 0.0, "machine": 0.0}
    for index, item in enumerate(prepared):
        row = item["row"]
        source_code = row["originalCode"]
        list_item, quota_item = item["listItem"], item["quotaItem"]
        list_score, quota_score = item["listScore"], item["quotaScore"]
        selected_quotas = []
        quota_scores = []
        ai_choice = ai_choices.get(str(index))
        ai_reason = ""
        if ai_choice:
            selected_list = text(ai_choice.get("listCode"))
            ai_confidence = max(0.0, min(1.0, number(ai_choice.get("confidence"))))
            allowed_lists = {candidate[1]["code"]: candidate for candidate in item["listCandidates"]}
            allowed_quotas = {candidate[1]["code"]: candidate for candidate in item["quotaCandidates"]}
            if selected_list in allowed_lists:
                retrieval_score, list_item = allowed_lists[selected_list]
                list_score = max(retrieval_score, ai_confidence)
            for selection in normalize_quota_selections(ai_choice):
                if selection["code"] not in allowed_quotas:
                    continue
                retrieval_score, selected_item = allowed_quotas[selection["code"]]
                selected_quotas.append(quota_contribution(
                    selected_item, tax_mode, selection["coefficient"], selection["reason"]
                ))
                quota_scores.append(max(retrieval_score, ai_confidence))
            ai_reason = text(ai_choice.get("reason"))
        if not selected_quotas and quota_item and not ai_choice:
            selected_quotas = [quota_contribution(quota_item, tax_mode)]
            quota_scores = [quota_score]
        prices = sum_quota_contributions(selected_quotas)
        quantity = row["quantity"]
        for field in totals:
            totals[field] += prices[field] * quantity
        # The final confidence must reflect the complete list + quota chain.
        # Using max() made a strong list match hide a weak quota match (for
        # example showing 95% while still requiring review).
        quota_confidence = min(quota_scores) if quota_scores else 0.0
        confidence = round((min(list_score, quota_confidence) if quotas else list_score) * 100, 1)
        review_reasons = []
        matched = list_score >= 0.72 and (not quotas or (selected_quotas and quota_confidence >= 0.62))
        if not matched:
            review_reasons.append("清单/定额匹配置信度不足")
        if quotas and not selected_quotas:
            review_reasons.append("未形成可靠的定额组合")
        if not row["quantityRecognized"]:
            review_reasons.append("未识别到明确工程量")
        if not row["unit"]:
            review_reasons.append("未识别到计量单位")
        status = "已匹配" if not review_reasons else "待复核"
        results.append({
            **row,
            "listCode": (list_item or {}).get("code", ""),
            "listName": (list_item or {}).get("name", ""),
            "quotaCode": "；".join(entry["code"] for entry in selected_quotas),
            "quotaName": "；".join(entry["name"] for entry in selected_quotas),
            "quotaSelections": selected_quotas,
            "confidence": confidence,
            "status": status,
            "reviewReasons": review_reasons,
            "matchMethod": "AI多定额组合匹配" if ai_choice else ("编码精确匹配" if source_code in list_by_code or source_code in quota_by_code else "本地相似度匹配"),
            "aiReason": ai_reason,
            "unitLabour": prices["labour"],
            "unitMaterial": prices["material"],
            "unitMachine": prices["machine"],
            "subtotal": prices["unitPrice"] * quantity,
        })
        if index == 0 or (index + 1) % 100 == 0 or index + 1 == len(prepared):
            ratio = (index + 1) / max(1, len(prepared))
            emit_progress(82 + round(ratio * 13), "汇总人材机成本", f"已计算 {index + 1}/{len(prepared)} 条")
    direct = totals["labour"] + totals["material"] + totals["machine"]
    management = direct * manage_rate
    profit = (direct + management) * profit_rate
    before_tax = direct + management + profit
    tax = before_tax * tax_rate
    total = before_tax + tax
    sensitivity = []
    for change in (-10, -5, 0, 5, 10):
        changed_direct = totals["labour"] + totals["machine"] + totals["material"] * (1 + change / 100)
        changed_management = changed_direct * manage_rate
        changed_profit = (changed_direct + changed_management) * profit_rate
        changed_before_tax = changed_direct + changed_management + changed_profit
        sensitivity.append({"change": change, "total": round(changed_before_tax * (1 + tax_rate), 2)})
    emit_progress(98, "生成测算结果", "正在汇总报价方案与风险分析")
    return {
        "source": f"{province}{profession}清单库" + ("/定额库" if quotas else "（定额待补充）"),
        "province": province,
        "profession": profession,
        "taxMode": tax_mode,
        "catalog": {"lists": len(lists), "quotas": len(quotas)},
        "parsing": parsing,
        "ai": ai.summary(),
        "items": results,
        "summary": {
            **{key: round(value, 2) for key, value in totals.items()},
            "management": round(management, 2), "profit": round(profit, 2),
            "tax": round(tax, 2), "total": round(total, 2),
            "matched": sum(item["status"] == "已匹配" for item in results),
            "review": sum(item["status"] != "已匹配" for item in results),
        },
        "quotes": {
            "breakEven": round(total, 2),
            "regular": round(total * 1.05, 2),
            "competitive": round(total * 1.02, 2),
        },
        "sensitivity": sensitivity,
        "limitations": (
            "江苏省建筑工程清单库已接入；江苏省定额价格库尚未导入，当前仅提供清单识别与匹配，价格结果为零且不可用于报价。"
            if province == "江苏省" else
            "当前价格库仅覆盖山东建筑工程；其他专业先完成清单匹配，价格结果需补充对应地区定额库。"
        ) + "AI不可用时系统会自动切换到本地规则，不会中断测算。",
    }


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        data = catalog_for_ui(payload) if payload.get("action") == "catalog" else calculate(payload)
        print(json.dumps({"success": True, "data": data}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"success": False, "message": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
