from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class Evidence(BaseModel):
    title_on_page: str = ""
    published_date_text: str = ""
    key_fact_snippet: str = ""
    pricing_or_leadtime_snippet: str = ""


class Metrics(BaseModel):
    metric_type: str = ""
    item: str = ""
    value: str = ""
    unit: str = ""
    context: str = ""
    channel_vendor: str = ""
    geo: str = ""


class Article(BaseModel):
    date: str = Field(..., description="发布日期 YYYY-MM-DD")
    title: str
    summary: str
    source: str
    url: str = Field(..., description="原文链接")
    canonical_url: str = ""

    region: str = "Global"
    segment: str = ""
    tags: List[str] = Field(default_factory=list)
    event_type: str = "fact"

    metrics: Optional[Metrics] = None
    evidence: Optional[Evidence] = None

    main_category: str = Field(
        "",
        description="ai_hardware / ai_software / ai_application / ai_funding_ma / ai_research",
    )
    sub_categories: List[str] = Field(default_factory=list)

    already_in_local: Optional[bool] = None

    @validator("date")
    def _validate_date(cls, v: str) -> str:
        # 容错：只要能 parse 成日期就接受
        try:
            datetime.strptime(v.strip(), "%Y-%m-%d")
        except Exception:
            raise ValueError("date must be YYYY-MM-DD")
        return v.strip()

    @validator("url", pre=True)
    def _coerce_url(cls, v: object) -> str:
        if v is None or v == "":
            raise ValueError("url is required")
        return str(v).strip()


class ArticleList(BaseModel):
    total: int
    items: List[Article]

