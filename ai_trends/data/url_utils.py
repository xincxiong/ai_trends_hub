# -*- coding: utf-8 -*-
"""URL 与标题规范化、域名校验等工具。"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from .domains import CHINA_OFFICIAL_DOMAINS, CORE_DOMAINS, REUTERS_SYNDICATION, SECONDARY_DOMAINS


def iso_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def get_domain(u: str) -> str:
    try:
        d = urlparse(u).netloc.lower()
        if d.startswith("www."):
            d = d[4:]
        return 
    except Exception:
        return ""


def canonicalize_url(u: str) -> str:
    """稳定去重：去掉 tracking query、统一 host、去尾斜杠。"""
    try:
        p = urlparse(u)
        host = p.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        keep_q = []
        for k, v in parse_qsl(p.query, keep_blank_values=True):
            lk = k.lower()
            if lk.startswith("utm_") or lk in {"spm", "fbclid", "gclid", "mc_cid", "mc_eid"}:
                continue
            keep_q.append((k, v))
        query = urlencode(keep_q, doseq=True)
        path = p.path.rstrip("/") or p.path
        p2 = p._replace(netloc=host, query=query, path=path)
        return urlunparse(p2)
    except Exception:
        return (u or "").strip()


def domain_allowed(u: str) -> bool:
    d = get_domain(u)
    if not d:
        return False
    ok_core = any(d == ad or d.endswith("." + ad) for ad in CORE_DOMAINS)
    ok_sec = any(d == ad or d.endswith("." + ad) for ad in SECONDARY_DOMAINS)
    return ok_core or ok_sec


def norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[""'’`]", "", t)
    t = re.sub(r"[^a-z0-9\u4e00-\u9fa5 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def looks_like_docs_url(url: str) -> bool:
    path = (urlparse(url).path or "").lower()
    bad = ["/docs", "/documentation", "/help", "/support", "/wiki", "/manual", "/guide", "/faq"]
    return any(bt in path for bt in bad)


def china_official_url_allowed(url: str, china_official_domains: Optional[set] = None) -> bool:
    domains = china_official_domains or CHINA_OFFICIAL_DOMAINS
    d = get_domain(url)
    if d not in domains and not any(d.endswith("." + x) for x in domains):
        return True
    return not looks_like_docs_url(url)


def force_source_normalization(url: str, source: str) -> str:
    d = get_domain(url)
    if d in REUTERS_SYNDICATION:
        return "Reuters"
    return (source or "").strip()


def parse_date_from_url(url: str) -> Optional[str]:
    m = re.search(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})", url)
    if not m:
        return None
    y, mo, da = m.group(1), int(m.group(2)), int(m.group(3))
    return f"{y}-{mo:02d}-{da:02d}"


def has_cjk(text: str) -> bool:
    return bool(text) and re.search(r"[\u4e00-\u9fff]", text) is not None


def is_valid_yyyy_mm_dd(s: str) -> bool:
    return bool(s) and isinstance(s, str) and re.fullmatch(r"20\d{2}-\d{2}-\d{2}", (s or "").strip()) is not None
