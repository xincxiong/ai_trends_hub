# -*- coding: utf-8 -*-
"""数据流水线：编排抓取 -> 清洗 -> 保存。支持单阶段与两阶段（URL 召回 + 核验）模式。"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

from ..config import settings
from ..models import Article
from ..model import supports_responses_api
from .crawler import CrawlWindow, fetch_raw_items
from .cleaner import (
    raw_items_to_articles,
    filter_verified_to_final,
    verified_items_to_articles,
    translate_titles_to_zh,
)
from .recall import build_pass_queries, recall_urls_for_pass, is_channel_or_cost_signal
from .verify import verify_urls
from .storage import (
    load_articles,
    load_local_news,
    merge_articles,
    save_articles,
    backup_file,
    filter_articles_by_date_range,
)
from .url_utils import (
    canonicalize_url,
    china_official_url_allowed,
    domain_allowed,
    iso_date,
    norm_title,
)


def _today_range_utc(window_days: int) -> Tuple[str, str]:
    from datetime import timezone
    now = datetime.now(timezone.utc).date()
    end_d = now
    start_d = end_d - timedelta(days=max(1, window_days) - 1)
    return start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")


def _today_range_tz(tz_name: str, window_days: int) -> Tuple[str, str]:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz=tz)
    end_d = now.date()
    start_d = end_d - timedelta(days=max(1, window_days) - 1)
    return iso_date(start_d), iso_date(end_d)


def _build_local_refs(local_news: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
    if not local_news:
        return []
    tail = local_news[-k:] if len(local_news) > k else local_news
    return [
        {
            "date": n.get("date"),
            "title": n.get("title"),
            "source": n.get("source"),
            "url": n.get("url"),
            "region": n.get("region"),
            "segment": n.get("segment"),
            "tags": n.get("tags", []),
        }
        for n in tail
    ]


def _build_local_dedup_keys(local_news: List[Dict[str, Any]]) -> Tuple[set, set]:
    title_keys: set = set()
    url_keys: set = set()
    for n in local_news:
        t = (n.get("title") or "").strip()
        u = (n.get("url") or "").strip()
        cu = canonicalize_url(n.get("canonical_url") or u)
        if t:
            title_keys.add(norm_title(t))
        if cu:
            url_keys.add(cu)
    return title_keys, url_keys


def fetch_latest_articles() -> List[Article]:
    """单阶段：抓取并清洗为 Article 列表（不写盘）。"""
    start, end = _today_range_utc(settings.window_days)
    win = CrawlWindow(start=start, end=end)
    raw_items = fetch_raw_items(win)
    return raw_items_to_articles(raw_items, max_items=settings.max_items)


def _run_two_stage_fetch() -> List[Article]:
    """两阶段：召回 URL -> 核验 -> 清洗 -> 返回 Article 列表（不写盘）。"""
    report_tz = getattr(settings, "report_tz", "Asia/Shanghai")
    start, end = _today_range_tz(report_tz, settings.window_days)

    local_path = getattr(settings, "local_ref_path", None)
    local_path = Path(local_path) if local_path else None
    local_news = load_local_news(local_path)
    local_refs = _build_local_refs(local_news, getattr(settings, "local_sample_size", 120))
    local_title_keys, local_url_keys = _build_local_dedup_keys(local_news)

    # Stage A: 多轮召回
    pass_specs = build_pass_queries(start=start, end=end)
    all_url_items: List[Dict[str, Any]] = []
    for spec in pass_specs:
        all_url_items.extend(
            recall_urls_for_pass(spec["name"], spec["queries"], start, end, local_refs)
        )

    # Stage A 过滤与去重
    stage_a_max = getattr(settings, "stage_a_max_urls", 420)
    relax = getattr(settings, "relax_stage_a_filters", True)
    seen_cu: set = set()
    candidates: List[Dict[str, Any]] = []
    drop_a = {"missing_url": 0, "china_official_docs": 0, "domain": 0, "dedup": 0}

    for it in all_url_items:
        url = (it.get("url") or "").strip()
        if not url:
            drop_a["missing_url"] += 1
            continue
        if not china_official_url_allowed(url):
            drop_a["china_official_docs"] += 1
            continue

        cu = canonicalize_url(url)
        it["canonical_url"] = cu
        title_hint = (it.get("title_hint") or "") + " " + (it.get("reason") or "")
        protected = is_channel_or_cost_signal(title_hint)

        if relax:
            if (not domain_allowed(url)) and (not protected):
                drop_a["domain"] += 1
                continue
        else:
            if not domain_allowed(url):
                drop_a["domain"] += 1
                continue
        if cu in seen_cu:
            drop_a["dedup"] += 1
            continue
        seen_cu.add(cu)
        candidates.append(it)
        if len(candidates) >= stage_a_max:
            break

    # Stage B: 核验
    verified = verify_urls(candidates, start=start, end=end)
    min_conf = getattr(settings, "verify_min_confidence", 0.74)
    require_date = getattr(settings, "verify_require_date", True)
    strict_domain = getattr(settings, "strict_domain_after_verify", False)
    final_dicts = filter_verified_to_final(verified, min_conf, require_date, strict_domain)

    include_existing = getattr(settings, "include_existing_in_output", True)
    articles = verified_items_to_articles(
        final_dicts,
        local_title_keys=local_title_keys,
        local_url_keys=local_url_keys,
        include_existing=include_existing,
        max_items=settings.max_items,
    )
    articles = translate_titles_to_zh(articles, batch_size=30)
    return articles


def fetch_latest_articles_two_stage() -> List[Article]:
    """两阶段抓取并返回 Article 列表（不写盘）。"""
    return _run_two_stage_fetch()


def run_pipeline() -> List[Article]:
    """执行一次：抓取 -> 清洗 -> 保存快照 -> 与历史合并去重 -> 写入聚合文件。
    支持 Responses API 时可用两阶段（URL 召回+核验）；仅 Chat Completions 时自动走单阶段（基于知识生成）。
    """
    two_stage = getattr(settings, "two_stage_fetch", True)
    report_tz = getattr(settings, "report_tz", "Asia/Shanghai")
    start, end = _today_range_tz(report_tz, settings.window_days)

    # 仅当支持 Responses API（含 web_search）时才走两阶段；否则用单阶段 + 知识生成
    if two_stage and supports_responses_api():
        incoming = _run_two_stage_fetch()
    else:
        incoming = fetch_latest_articles()

    snapshot_path = settings.snapshots_dir / f"snapshot_{start}_to_{end}.json"
    save_articles(snapshot_path, incoming)

    existing = load_articles(settings.news_data_path)
    merged = merge_articles(existing, incoming)

    if getattr(settings, "news_backup_before_merge", True) and settings.news_data_path.exists():
        bak = backup_file(settings.news_data_path)
        if bak:
            print(f"[newsdata] backup created: {bak}")

    keep_days = getattr(settings, "news_keep_days", 30)
    if keep_days > 0:
        tz = ZoneInfo(report_tz)
        now_d = datetime.now(tz=tz).date()
        keep_start = iso_date(now_d - timedelta(days=max(1, keep_days) - 1))
        merged = filter_articles_by_date_range(merged, keep_start, end)
        merged.sort(key=lambda a: (a.date or "", a.source or ""), reverse=True)

    save_articles(settings.news_data_path, merged)
    return merged
