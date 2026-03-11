"""数据清洗：原始条目规范化、校验、转为 Article；核验结果过滤与标题翻译。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from ..models import Article, Evidence, Metrics
from ..model import call_responses
from .url_utils import (
    canonicalize_url,
    domain_allowed,
    force_source_normalization,
    get_domain,
    has_cjk,
    norm_title,
)
from .domains import CHANNEL_VENDOR_DOMAINS, CHINA_OFFICIAL_DOMAINS, LLM_PRIMARY_SOURCES
from .llm_helpers import extract_json_array, safe_json_loads


# segment 关键词 -> main_category 映射
SEGMENT_TO_MAIN_CATEGORY = {
    "ai_hardware": ("AI芯片", "云计算", "数据中心", "国产GPU", "智算中心", "GPU", "HBM", "CoWoS", "渠道与现货", "内存与成本", "采购与TCO"),
    "ai_software": ("大模型发布", "大模型开源", "推理与部署", "Agent工具链", "软件生态"),
    "ai_application": ("行业应用", "落地"),
    "ai_funding_ma": ("投融资", "并购"),
    "ai_research": ("科研", "算法", "论文"),
}


def _segment_to_main_category(segment: str) -> str:
    seg = (segment or "").strip()
    if not seg:
        return ""
    for cat, keywords in SEGMENT_TO_MAIN_CATEGORY.items():
        if any(kw in seg for kw in keywords):
            return cat
    return "ai_hardware"  # 默认


def raw_items_to_articles(raw_items: List[Dict[str, Any]], max_items: int = 0) -> List[Article]:
    """将抓取得到的原始 dict 列表清洗为 Article 列表（单阶段抓取用）。"""
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


def filter_verified_to_final(
    verified: List[Dict[str, Any]],
    min_confidence: float,
    require_date: bool,
    strict_domain: bool,
) -> List[Dict[str, Any]]:
    """从核验结果中筛出符合置信度、日期、证据、域名的条目。"""
    final: List[Dict[str, Any]] = []
    for x in verified:
        try:
            conf = float(x.get("confidence") or 0)
        except Exception:
            conf = 0.0
        if not x.get("verified") or conf < min_confidence:
            continue

        url = (x.get("url") or "").strip()
        title = (x.get("title") or "").strip()
        summary = (x.get("summary") or "").strip()
        date_s = (x.get("date") or "").strip()
        ev = x.get("evidence") or {}

        if not isinstance(ev, dict):
            continue
        if not (ev.get("title_on_page") and ev.get("published_date_text") and ev.get("key_fact_snippet")):
            continue
        if not url or not title or not summary:
            continue
        if require_date and not date_s:
            continue

        if strict_domain:
            if not domain_allowed(url):
                d = get_domain(url)
                one_hand = any(
                    d == ad or d.endswith("." + ad)
                    for ad in (LLM_PRIMARY_SOURCES | CHINA_OFFICIAL_DOMAINS | CHANNEL_VENDOR_DOMAINS)
                )
                if not one_hand:
                    continue

        x["source"] = force_source_normalization(url, x.get("source", ""))
        final.append(x)
    return final


def verified_items_to_articles(
    items: List[Dict[str, Any]],
    local_title_keys: set,
    local_url_keys: set,
    include_existing: bool,
    max_items: int,
) -> List[Article]:
    """将核验后的 dict 转为 Article 列表，做去重、标签规范化、main_category 映射。"""
    seen = set()
    out: List[Article] = []
    for item in items:
        url = (item.get("url") or "").strip()
        cu = canonicalize_url(item.get("canonical_url") or url)
        title = (item.get("title") or "").strip()
        summary = (item.get("summary") or "").strip()
        date_s = (item.get("date") or "").strip()
        source = force_source_normalization(url, item.get("source", ""))

        if not url or not title or not summary:
            continue

        already = (cu in local_url_keys) or (norm_title(title) in local_title_keys)
        if already and not include_existing:
            continue

        k = f"{cu}::{norm_title(title)}"
        if k in seen:
            continue
        seen.add(k)

        region = (item.get("region") or "Global").strip()
        if region not in {"Global", "China", "US", "EU", "APAC"}:
            region = "Global"

        tags = item.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r"[，,;/|]+", tags) if t.strip()]
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip() for t in tags if str(t).strip()][:5]

        et = (item.get("event_type") or "fact").strip().lower()
        if et not in {"fact", "analysis", "technical"}:
            et = "fact"

        segment = (item.get("segment") or "").strip()
        main_cat = (item.get("main_category") or "").strip().lower()
        if main_cat not in ("ai_hardware", "ai_software", "ai_application", "ai_funding_ma", "ai_research"):
            main_cat = _segment_to_main_category(segment)
        if not main_cat:
            main_cat = "ai_hardware"

        metrics = item.get("metrics")
        evidence = item.get("evidence")
        if isinstance(metrics, dict):
            metrics = Metrics(**{k: metrics.get(k, "") for k in ["metric_type", "item", "value", "unit", "context", "channel_vendor", "geo"]})
        else:
            metrics = None
        if isinstance(evidence, dict):
            evidence = Evidence(**{k: evidence.get(k, "") for k in ["title_on_page", "published_date_text", "key_fact_snippet", "pricing_or_leadtime_snippet"]})
        else:
            evidence = None

        art = Article(
            date=date_s,
            title=title,
            summary=summary,
            source=source,
            url=url,
            canonical_url=cu,
            region=region,
            segment=segment,
            tags=tags,
            event_type=et,
            main_category=main_cat,
            sub_categories=[],
            metrics=metrics,
            evidence=evidence,
            already_in_local=already if include_existing else None,
        )
        out.append(art)
        if max_items > 0 and len(out) >= max_items:
            break
    return out


def translate_titles_to_zh(articles: List[Article], batch_size: int = 30) -> List[Article]:
    """将英文标题翻译为中文（仅处理无 CJK 的标题）。"""
    idx_map: List[int] = []
    src_titles: List[str] = []
    for i, a in enumerate(articles):
        t = (a.title or "").strip()
        if not t or has_cjk(t):
            continue
        idx_map.append(i)
        src_titles.append(t)

    if not src_titles:
        return articles

    for start_i in range(0, len(src_titles), batch_size):
        chunk = src_titles[start_i : start_i + batch_size]
        prompt = f"""
把下面英文标题逐条翻译为【简洁、准确、新闻标题风格】中文。
要求：保留公司/产品/型号/数字，不添加原文没有的信息。
输出：严格 JSON 数组，长度与输入一致。

输入：
{json.dumps(chunk, ensure_ascii=False, indent=2)}
""".strip()
        try:
            resp = call_responses(prompt=prompt, tools=None)
            raw = getattr(resp, "output_text", None) or ""
            j = extract_json_array(raw)
            data = safe_json_loads(j)
            if not isinstance(data, list) or len(data) != len(chunk):
                continue
            for k, zh_title in enumerate(data):
                if isinstance(zh_title, str):
                    articles[idx_map[start_i + k]].title = zh_title.strip()
        except Exception:
            continue
    return articles
