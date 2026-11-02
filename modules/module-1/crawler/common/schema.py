from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class ProjectRecord:
    # =========================
    # 系统标识
    # =========================
    project_id: str

    # =========================
    # 1. 基础信息
    # =========================
    project_name: str
    project_type: Optional[str]

    province: str
    city: Optional[str]
    district: Optional[str]

    owner_name: Optional[str]

    # =========================
    # 2. 时间维度
    # =========================
    publish_time: Optional[str]
    open_bid_time: Optional[str]
    bid_deadline: Optional[str]

    # =========================
    # 3. 造价数据
    # 统一单位：元
    # =========================
    control_price: Optional[float]
    estimated_contract_amount: Optional[float]
    provisional_sum: Optional[float]

    # =========================
    # 招投标辅助信息
    # =========================
    project_code: Optional[str]

    # =========================
    # 4. 企业跟踪管理
    # =========================
    tracking_stage: str = "LEAD"
    rating: str = "UNRATED"
    responsible_person: Optional[str] = None

    # =========================
    # 数据来源
    # =========================
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    source_row_id: Optional[str] = None
    crawl_time: Optional[str] = None

    def to_dict(self):
        return asdict(self)


def current_time():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )