from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from .config import settings
from .models import Article
from .storage import load_articles, merge_articles, save_articles
from .crawler import CrawlWindow, fetch_raw_items


def _today_range_utc(window_days: int) -> tuple[str, str]:
    now = datetime.now(timezone.utc).date()
    end_d = now
    start_d = end_d - timedelta(days=max(1, window_days) - 1)
    return start_d.strftime("%Y-%m-%d"), end_d.strftime("%Y-%m-%d")


def fetch_latest_articles() -> List[Article]:
    """
    使用解耦的 crawler 模块获取原始 JSON，再转为 Article。
    """
    start, end = _today_range_utc(settings.window_days)
    win = CrawlWindow(start=start, end=end)
    raw_items = fetch_raw_items(win)

    items: List[Article] = []
    for x in raw_items:
        if not isinstance(x, dict):
            continue
        try:
            if not x.get("canonical_url"):
                x["canonical_url"] = x.get("url", "")
            art = Article(**x)
        except Exception:
            continue
        items.append(art)

    return items[: settings.max_items]


def run_pipeline() -> List[Article]:
    """执行一次抓取 + 合并去重，并写入本地 JSON 和快照。"""
    incoming = fetch_latest_articles()

    # 保存本次抓取快照
    start, end = _today_range_utc(settings.window_days)
    snapshot_path = settings.snapshots_dir / f"snapshot_{start}_to_{end}.json"
    save_articles(snapshot_path, incoming)

    # 与历史数据合并去重
    existing = load_articles(settings.news_data_path)
    merged = merge_articles(existing, incoming)
    save_articles(settings.news_data_path, merged)
    return merged

