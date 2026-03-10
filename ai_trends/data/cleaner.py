"""数据清洗：原始条目规范化、校验、转为 Article。"""
from __future__ import annotations

from typing import Any, Dict, List

from ..models import Article


def raw_items_to_articles(raw_items: List[Dict[str, Any]], max_items: int = 0) -> List[Article]:
    """将抓取得到的原始 dict 列表清洗为 Article 列表。"""
    items: List[Article] = []
    for x in raw_items:
        if not isinstance(x, dict):
            continue
        try:
            if not x.get("canonical_url"):
                x["canonical_url"] = x.get("url", "")
            art = Article(**x)
            items.append(art)
        except Exception:
            continue
    if max_items > 0:
        items = items[:max_items]
    return items
