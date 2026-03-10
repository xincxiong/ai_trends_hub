# -*- coding: utf-8 -*-
"""Stage A：多轮检索召回候选 URL（URL-first recall）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from ..config import settings
from .domains import CHANNEL_VENDOR_KEYWORDS
from .url_utils import canonicalize_url
from .llm_helpers import call_model_json_array


def is_channel_or_cost_signal(title_or_reason: str) -> bool:
    text = (title_or_reason or "").lower()
    kws = [
        "channel", "distributor", "reseller", "broker", "spot price", "street price",
        "quotation", "quote", "lead time", "allocation", "inventory",
        "hbm", "hbm3e", "dram", "ddr5", "gddr6", "gddr7",
        "contract price", "cost", "bom", "bill of materials", "tco",
        "cowos", "soic", "packaging", "substrate", "abf",
        "现货", "渠道", "分销", "代理", "报价", "交期", "配额", "库存",
        "内存", "存储", "封装", "基板", "采购", "成本",
    ]
    if any(k in text for k in kws):
        return True
    if any(v.lower() in text for v in CHANNEL_VENDOR_KEYWORDS):
        return True
    return False


def build_pass_queries(start: str, end: str) -> List[Dict[str, Any]]:
    S = f"{start}..{end}"
    passes: List[Dict[str, Any]] = [
        {"name": "reuters-core", "queries": [
            f"site:reuters.com AI chip {S}",
            f"site:reuters.com Nvidia GPU H200 B200 {S}",
            f"site:reuters.com HBM3e SK Hynix Micron Samsung {S}",
            f"site:reuters.com CoWoS packaging substrate {S}",
            f"site:reuters.com cloud GPU capacity {S}",
        ]},
        {"name": "cloud-dc", "queries": [
            f"AWS GPU instance launch H200 B200 {S}",
            f"Azure ND H100 H200 Blackwell VM {S}",
            f"Google Cloud A3 A4 GPU {S}",
            f"Oracle Cloud GPU instance {S}",
            f"AI data center buildout power cooling {S}",
        ]},
        {"name": "chips-supply", "queries": [
            f"HBM3e supply price trend {S}",
            f"DRAM DDR5 contract price server {S}",
            f"GDDR7 supply price {S}",
            f"CoWoS SoIC advanced packaging capacity cost {S}",
            f"ABF substrate shortage price {S}",
        ]},
        {"name": "policy-geo", "queries": [
            f"US BIS AI chip export controls H200 {S}",
            f"Nvidia AI chip China license {S}",
        ]},
        {"name": "china-llm", "queries": [
            f"DeepSeek 模型 发布 开源 {S}",
            f"通义千问 Qwen 发布 开源 {S}",
            f"MiniMax 发布 智能体 模型 {S}",
            f"Kimi Moonshot 模型 发布 {S}",
        ]},
        {"name": "funding-ma", "queries": [
            f"AI data center funding investment {S}",
            f"semiconductor HBM packaging funding {S}",
            f"AI startup funding model release {S}",
        ]},
    ]

    if getattr(settings, "enable_channel_monitoring", True):
        passes.extend([
            {"name": "channel-aib-system", "queries": [
                f"H200 HGX channel quote lead time allocation {S}",
                f"B200 GB200 channel allocation lead time {S}",
                f"GPU server street price quote H100 H200 {S}",
                f"AI server reseller quotation HGX H100 H200 {S}",
                f"GPU distributor inventory allocation {S}",
                f"GIGABYTE AI server quote H100 H200 {S}",
                f"Gigabyte NVIDIA HGX H100 H200 availability lead time {S}",
                f"技嘉 AI 服务器 报价 H100 H200 交期 配额 {S}",
                f"Supermicro GPU server price H200 lead time {S}",
                f"ASUS server GPU quote H100 H200 lead time {S}",
                f"MSI server GPU quote {S}",
                f"TD SYNNEX Nvidia H200 allocation {S}",
                f"Ingram Micro Nvidia H200 quote {S}",
                f"Arrow Avnet GPU server quote lead time {S}",
            ]},
            {"name": "procurement-cost", "queries": [
                f"HGX H200 system cost breakdown BOM HBM3e {S}",
                f"GB200 NVL72 cost power cooling rack {S}",
                f"AI server BOM cost HBM3e CoWoS ABF substrate {S}",
                f"lead time HBM3e CoWoS substrate cost impact {S}",
                f"AI GPU supply allocation cost increase {S}",
                f"datacenter TCO GPU power cooling liquid cooling cost {S}",
            ]},
            {"name": "memory-cost", "queries": [
                f"TrendForce HBM3e price contract {S}",
                f"DRAMeXchange DDR5 contract price server {S}",
                f"HBM3e supply tightness price SK hynix Samsung Micron {S}",
                f"GDDR6 GDDR7 price trend {S}",
            ]},
        ])

    n = max(1, getattr(settings, "stage_a_passes", 16))
    return passes[:n]


def recall_urls_for_pass(
    pass_name: str,
    queries: List[str],
    start: str,
    end: str,
    local_refs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    per_pass = getattr(settings, "stage_a_per_pass_limit", 26)
    prompt = f"""
你是一名 AI/GPU 行业情报召回助手。请基于联网搜索，在时间窗口 {start}~{end} 召回候选【原文 URL】。
你只需要输出候选 URL 列表（URL + 少量线索），不要写完整新闻摘要，不要编造。

【本地已收录样本（用于避免重复方向）】
{json.dumps(local_refs, ensure_ascii=False, indent=2)}

【特别关注：你必须尽量覆盖】
- GPU 渠道链条信号：AIB/系统商/分销商（GIGABYTE/技嘉、Supermicro、ASUS、MSI 等）
- 渠道报价/现货/交期/配额/库存
- 供应链与采购成本：HBM3e/DRAM/DDR5/GDDR、CoWoS/封装/ABF基板、交付周期变化

【输出要求】
- 只输出严格 JSON 数组，不要 markdown，不要解释
- 每条对象字段：
  - url: 原文链接（必须可打开的具体页面）
  - source_hint: 站点名/媒体名（可空）
  - title_hint: 页面标题（可空）
  - date_hint: YYYY-MM-DD（不确定可空）
  - reason: 1句话说明强相关点（可空）
- 每轮最多 {per_pass} 条（pass={pass_name}）
- 不要输出 docs/help/wiki/manual/faq 页面
""".strip() + "\n\n【本轮检索关键词】\n" + "\n".join("- " + q for q in queries)

    data = call_model_json_array(prompt, pass_name=f"recall-url-{pass_name}", use_web_search=True)

    out: List[Dict[str, Any]] = []
    for x in data:
        url = (x.get("url") or "").strip()
        if not url:
            continue
        out.append({
            "url": url,
            "canonical_url": canonicalize_url(url),
            "source_hint": (x.get("source_hint") or "").strip(),
            "title_hint": (x.get("title_hint") or "").strip(),
            "date_hint": (x.get("date_hint") or "").strip(),
            "reason": (x.get("reason") or "").strip(),
            "pass": pass_name,
        })
    return out
