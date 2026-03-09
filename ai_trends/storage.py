from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from .models import Article


def _norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[“”\"'’`]", "", t)
    t = re.sub(r"[^a-z0-9\u4e00-\u9fa5 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _canonicalize_url(u: str) -> str:
    # 简化版 canonical URL，只做首尾空格与末尾斜杠处理
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

    # 按日期倒序
    merged.sort(key=lambda a: (a.date, a.source or ""), reverse=True)
    return merged

