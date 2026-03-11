# -*- coding: utf-8 -*-
"""
Chat Completions 的 web_search 适配层：通过外部搜索 API 获取网页内容，注入到 prompt，
使仅支持 Chat Completions 的 API 也能获得“联网检索”能力，行为上接近 Responses API + web_search。
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from ..config import settings

# 从 prompt 中提取时间范围 (YYYY-MM-DD..YYYY-MM-DD)
_DATE_RANGE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\s*\.\.\s*(\d{4}-\d{2}-\d{2})")


def extract_date_range_from_prompt(prompt: str) -> Optional[Tuple[str, str]]:
    """从抓取类 prompt 中提取时间范围 (start, end)。"""
    m = _DATE_RANGE_RE.search(prompt)
    if m:
        return (m.group(1), m.group(2))
    return None


def _run_serper(query: str, num: int) -> List[dict]:
    """使用 Serper API 执行搜索，返回 [{"title","link","snippet"}, ...]。"""
    import httpx
    key = (getattr(settings, "serper_api_key", None) or "").strip()
    if not key:
        return []
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": min(num, 20)}
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                url,
                json=payload,
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []
    results = data.get("organic") or data.get("organicResults") or []
    out = []
    for item in results[:num]:
        if isinstance(item, dict):
            out.append({
                "title": item.get("title") or "",
                "link": item.get("link") or item.get("url") or "",
                "snippet": item.get("snippet") or "",
            })
    return out


def _run_duckduckgo(query: str, num: int) -> List[dict]:
    """使用 DuckDuckGo 执行搜索（无需 API Key），返回 [{"title","link","snippet"}, ...]。"""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []
    out = []
    try:
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=num)):
                if i >= num:
                    break
                out.append({
                    "title": (r.get("title") or "").strip(),
                    "link": (r.get("href") or r.get("link") or "").strip(),
                    "snippet": (r.get("body") or r.get("snippet") or "").strip(),
                })
    except Exception:
        pass
    return out


def run_web_search(query: str, num_results: Optional[int] = None) -> str:
    """
    执行一次联网检索，返回可注入到 prompt 的文本。
    优先使用 Serper（需配置 SERPER_API_KEY），否则使用 DuckDuckGo（无需 Key）。
    """
    num = num_results or getattr(settings, "web_search_max_results", 25) or 25
    num = min(max(1, num), 30)
    results = _run_serper(query, num)
    if not results:
        results = _run_duckduckgo(query, num)
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        title = (r.get("title") or "").strip()
        link = (r.get("link") or "").strip()
        snippet = (r.get("snippet") or "").strip()
        if not link and not snippet:
            continue
        lines.append(f"[{i}] 标题: {title}")
        if link:
            lines.append(f"    链接: {link}")
        if snippet:
            lines.append(f"    摘要: {snippet}")
        lines.append("")
    return "\n".join(lines).strip()


def build_queries_from_prompt(prompt: str) -> List[str]:
    """
    根据抓取类 prompt 生成多条搜索 query，用于多轮检索以覆盖不同维度。
    """
    date_range = extract_date_range_from_prompt(prompt)
    date_suffix = ""
    if date_range:
        start, end = date_range
        date_suffix = f" {start} {end}"
    queries = [
        f"AI 人工智能 新闻 动态 最新{date_suffix}",
        f"AI GPU 芯片 大模型 行业 新闻{date_suffix}",
        f"artificial intelligence news March 2025",
    ]
    return queries


def run_web_search_for_prompt(prompt: str) -> str:
    """
    根据 prompt 生成多条 query、执行联网检索并合并为一段参考文本，
    供后续 Chat Completions 使用（适配 Responses API 的 web_search 行为）。
    """
    queries = build_queries_from_prompt(prompt)
    num_per_query = max(8, (getattr(settings, "web_search_max_results", 25) or 25) // len(queries))
    parts = []
    seen_links = set()
    for q in queries:
        raw = run_web_search(q, num_results=num_per_query)
        if not raw:
            continue
        # 简单去重：同一链接只保留第一次出现
        block_lines = []
        for line in raw.split("\n"):
            if line.strip().startswith("链接:"):
                link = line.split(":", 1)[-1].strip()
                if link in seen_links:
                    continue
                seen_links.add(link)
            block_lines.append(line)
        if block_lines:
            parts.append("\n".join(block_lines))
    return "\n\n".join(parts).strip() if parts else ""
