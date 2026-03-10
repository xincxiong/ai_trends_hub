"""数据存储：读写、去重、快照、备份、按日期过滤。"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from ..models import Article


def _norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[""\"'’`]", "", t)
    t = re.sub(r"[^a-z0-9\u4e00-\u9fa5 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _canonicalize_url(u: str) -> str:
    u = (u or "").strip()
    if u.endswith("/"):
        u = u[:-1]
    return u


def load_articles(path: Path) -> List[Article]:
    if not path.exists():
        return []
    try:
        raw = path.read_text("utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return [Article(**item) for item in data if isinstance(item, dict)]
    except Exception:
        return []


def load_local_news(path: Optional[Path] = None) -> List[dict]:
    """读取本地 JSON 列表（参考样本/去重用），空或损坏时返回 []。"""
    if not path or not path.exists():
        return []
    try:
        raw = path.read_text("utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        return [x for x in data if isinstance(x, dict)]
    except Exception:
        return []


def save_articles(path: Path, articles: Iterable[Article]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [a.model_dump(mode="json") for a in articles]
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def build_dedup_keys(existing: Iterable[Article]) -> Tuple[set, set]:
    url_keys, title_keys = set(), set()
    for a in existing:
        cu = _canonicalize_url(a.canonical_url or str(a.url))
        if cu:
            url_keys.add(cu)
        if a.title:
            title_keys.add(_norm_title(a.title))
    return url_keys, title_keys


def merge_articles(existing: List[Article], incoming: List[Article]) -> List[Article]:
    ex_url, ex_title = build_dedup_keys(existing)
    seen_pair = set()
    merged: List[Article] = list(existing)

    for art in incoming:
        cu = _canonicalize_url(art.canonical_url or str(art.url))
        nt = _norm_title(art.title)
        if cu in ex_url or nt in ex_title:
            continue
        key = f"{cu}::{nt}"
        if key in seen_pair:
            continue
        seen_pair.add(key)
        ex_url.add(cu)
        ex_title.add(nt)
        merged.append(art)

    merged.sort(key=lambda a: (a.date, a.source or ""), reverse=True)
    return merged


def backup_file(path: Path) -> Optional[Path]:
    """备份文件到 path.bak_YYYYMMDD_HHMMSS，返回备份路径；不存在则返回 None。"""
    if not path.exists():
        return None
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = path.parent / f"{path.name}.bak_{ts}"
    bak.write_bytes(path.read_bytes())
    return bak


def _is_valid_yyyy_mm_dd(s: str) -> bool:
    return bool(s) and isinstance(s, str) and bool(re.fullmatch(r"20\d{2}-\d{2}-\d{2}", (s or "").strip()))


def filter_articles_by_date_range(articles: List[Article], start: str, end: str) -> List[Article]:
    """保留 date 在 [start, end] 内的文章（start/end 为 YYYY-MM-DD）。"""
    out: List[Article] = []
    for a in articles:
        d = (a.date or "").strip()
        if not _is_valid_yyyy_mm_dd(d):
            continue
        if start <= d <= end:
            out.append(a)
    return out
