"""数据流水线：编排抓取 -> 清洗 -> 保存。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from ..config import settings
from ..models import Article
from .crawler import CrawlWindow, fetch_raw_items
from .cleaner import raw_items_to_articles
from .storage import load_articles, merge_articles, save_articles


def _today_range_utc(window_days: int) -> tuple[str, str]:
    now = datetime.now(timezone.utc).date()
    end_d = now
    start_d = end_d - timedelta(days=max(1, window_days) - 1)
    return start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")


def fetch_latest_articles() -> List[Article]:
    """抓取并清洗为 Article 列表（不写盘）。"""
    start, end = _today_range_utc(settings.window_days)
    win = CrawlWindow(start=start, end=end)
    raw_items = fetch_raw_items(win)
    return raw_items_to_articles(raw_items, max_items=settings.max_items)


def run_pipeline() -> List[Article]:
    """执行一次：抓取 -> 清洗 -> 保存快照 -> 与历史合并去重 -> 写入聚合文件。"""
    incoming = fetch_latest_articles()

    start, end = _today_range_utc(settings.window_days)
    snapshot_path = settings.snapshots_dir / f"snapshot_{start}_to_{end}.json"
    save_articles(snapshot_path, incoming)

    existing = load_articles(settings.news_data_path)
    merged = merge_articles(existing, incoming)
    save_articles(settings.news_data_path, merged)
    return merged
