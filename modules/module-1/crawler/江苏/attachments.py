"""招标公告附件下载与结构化字段补全。"""

import re
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup
from pypdf import PdfReader

from parser import (
    clean_text,
    extract_control_price,
    extract_estimated_amount,
    extract_provisional_sum,
    extract_valid_datetime_after_anchor,
)


MAX_ATTACHMENT_BYTES = 30 * 1024 * 1024


def extract_attachment_links(html, detail_url):
    """返回公告中的可下载 PDF 附件；兼容源站 ReadAttachFile.aspx 接口。"""
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        label = clean_text(anchor.get_text(" ", strip=True)) or "附件"
        haystack = f"{label} {href}".lower()
        if not (
            "readattachfile.aspx" in haystack
            or ".pdf" in haystack
            or ("附件" in label and "download" in haystack)
        ):
            continue
        url = urljoin(detail_url, href)
        if url in seen:
            continue
        seen.add(url)
        links.append({"label": label, "url": url})
    return links


def _safe_filename(response, link, index):
    final_name = unquote(Path(urlparse(response.url).path).name)
    if not final_name.lower().endswith(".pdf"):
        label = re.sub(r'[<>:"/\\|?*]+', "_", link["label"]).strip(" ._")
        final_name = f"{label or f'attachment-{index}'}.pdf"
    return final_name


def download_pdf(session, link, target_dir, index, referer=None):
    target_dir.mkdir(parents=True, exist_ok=True)
    response = session.get(
        link["url"], timeout=60, verify=False, stream=True,
        headers={"Referer": referer} if referer else None,
    )
    response.raise_for_status()
    content_length = int(response.headers.get("content-length") or 0)
    if content_length > MAX_ATTACHMENT_BYTES:
        raise ValueError(f"附件超过30MB：{content_length} bytes")
    filename = _safe_filename(response, link, index)
    path = target_dir / filename
    if path.exists() and path.stat().st_size > 4:
        with path.open("rb") as handle:
            if handle.read(4) == b"%PDF":
                return path
    content = response.content
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise ValueError(f"附件超过30MB：{len(content)} bytes")
    if not content.startswith(b"%PDF"):
        raise ValueError("附件响应不是PDF文件")
    path.write_bytes(content)
    return path


def extract_pdf_text(path):
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return clean_text(" ".join(chunks)) or ""


def _prefixed_raw(filename, value):
    return f"[附件:{filename}] {value}" if value else f"[附件:{filename}]"


def merge_attachment_fields(project, text, filename):
    """仅补空字段，正文中已有的明确值优先。"""
    changed = []
    if not project.get("control_price"):
        value = extract_control_price(text)
        if value["value"] is not None:
            project["control_price"] = value["value"]
            project["control_price_status"] = "FOUND_FROM_ATTACHMENT"
            project["control_price_raw"] = _prefixed_raw(filename, value["raw"])
            changed.append("control_price")

    if not project.get("estimated_contract_amount"):
        value = extract_estimated_amount(text)
        if value["value"] is not None:
            project["estimated_contract_amount"] = value["value"]
            project["estimated_contract_amount_source"] = f"附件-{value['source']}"
            project["estimated_contract_amount_confidence"] = value["confidence"]
            project["estimated_contract_amount_raw"] = _prefixed_raw(filename, value["raw"])
            changed.append("estimated_contract_amount")

    if not project.get("provisional_sum"):
        value = extract_provisional_sum(text)
        if value["value"] is not None:
            project["provisional_sum"] = value["value"]
            project["provisional_sum_status"] = "FOUND_FROM_ATTACHMENT"
            project["provisional_sum_raw"] = _prefixed_raw(filename, value["raw"])
            changed.append("provisional_sum")

    publish_time = project.get("publish_time")
    if not project.get("bid_deadline"):
        value = extract_valid_datetime_after_anchor(
            text,
            [
                r"资格审查登记截止时间\s*(?:为|[:：])?",
                r"资格审查(?:申请文件)?(?:递交)?截[至止]时间\s*(?:为|[:：])?",
                r"资格预审申请文件递交截止时间\s*(?:为|[:：])?",
                r"投标文件递交(?:的)?截止时间\s*(?:为|[:：])?",
                r"投标截止时间\s*(?:为|[:：])?",
            ],
            reference=publish_time,
            window=220,
        )
        if value:
            project["bid_deadline"] = value
            changed.append("bid_deadline")

    if not project.get("open_bid_time"):
        value = extract_valid_datetime_after_anchor(
            text, [r"开标时间\s*(?:为|[:：])?", r"开标日期\s*(?:为|[:：])?"],
            reference=publish_time, window=220,
        )
        if not value and project.get("bid_deadline") and re.search(
            r"开标时间.{0,30}(?:同|与).{0,20}投标截止时间|"
            r"开标时间.{0,30}即.{0,20}投标截止时间|"
            r"投标截止时间.{0,30}(?:同|与).{0,20}开标时间",
            text,
        ):
            value = project["bid_deadline"]
        if value:
            project["open_bid_time"] = value
            changed.append("open_bid_time")
    return changed


def enrich_from_attachments(project, html, detail_url, row_id, session, root_dir, request_delay=0):
    """下载并解析附件，返回原项目字典（原地补全）。"""
    wanted = ("control_price", "estimated_contract_amount", "provisional_sum", "open_bid_time")
    if all(project.get(field) is not None for field in wanted):
        return project
    links = extract_attachment_links(html, detail_url)
    if not links:
        project["attachment_parse_status"] = "NO_ATTACHMENT"
        return project

    target_dir = Path(root_dir) / "attachments" / str(row_id)
    parsed = 0
    changes = []
    errors = []
    for index, link in enumerate(links, 1):
        try:
            path = download_pdf(session, link, target_dir, index, referer=detail_url)
            text = extract_pdf_text(path)
            if len(text) < 80:
                errors.append(f"{path.name}:扫描件或无可提取文本")
                continue
            parsed += 1
            changes.extend(merge_attachment_fields(project, text, path.name))
            if request_delay:
                time.sleep(request_delay)
        except Exception as error:
            errors.append(f"{link['label']}:{error}")

    project["attachment_parse_status"] = (
        "PARSED_AND_FILLED" if changes else "PARSED_NO_TARGET_VALUE" if parsed else "UNREADABLE"
    )
    project["attachment_filled_fields"] = sorted(set(changes))
    project["attachment_parse_errors"] = errors
    return project
