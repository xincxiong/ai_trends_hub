# -*- coding: utf-8 -*-
"""Stage A：多轮检索召回候选 URL（URL-first recall）。"""
from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List

from ..config import settings
from ..model.web_search_adapter import run_web_search
from .domains import CHANNEL_VENDOR_KEYWORDS
from .url_utils import canonicalize_url
from .fetch_status import set_current_content, set_current_site, set_current_url, set_phase
from .llm_helpers import call_model_json_array


# URL 有效性正则：基础验证
_URL_RE = re.compile(r"^https?://[^\s<>\"]+$", re.IGNORECASE)


def _is_valid_url(url: str) -> bool:
    """严格校验 URL：必须是有效的 http/https 链接。"""
    if not url:
        return False
    url = url.strip()
    if _URL_RE.match(url):
        return True
    return False


def _filter_valid_urls(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """过滤出有有效 URL 的条目，丢弃无 URL 或 URL 无效的项。"""
    valid = []
    for x in items:
        url = (x.get("url") or "").strip()
        if _is_valid_url(url):
            valid.append(x)
    return valid


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
        {"name": "industry-application", "queries": [
            f"AI healthcare medical diagnosis drug discovery {S}",
            f"AI finance fintech trading risk automation {S}",
            f"AI manufacturing smart factory industrial {S}",
            f"AI retail ecommerce recommendation personalization {S}",
            f"AI education edtech learning {S}",
            f"autonomous driving self-driving AI vehicle {S}",
            f"AI advertising marketing campaign {S}",
            f"enterprise AI deployment use case {S}",
            f"vertical AI application industry {S}",
            f"AI 医疗 金融 制造 教育 落地 应用 {S}",
        ]},
        {"name": "research-algorithms", "queries": [
            f"arXiv AI ML paper 2024 2025 {S}",
            f"NeurIPS ICLR ICML 2024 2025 AI {S}",
            f"Transformer MoE diffusion new architecture {S}",
            f"reinforcement learning LLM agent {S}",
            f"AI benchmark evaluation LLM {S}",
            f"new AI model release paper preprint {S}",
            f"large language model research paper {S}",
            f"multimodal agent reasoning paper {S}",
            f"AI 论文 顶会 开源 模型 评测 {S}",
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
    focus_extra = ""
    if "industry" in pass_name or "application" in pass_name:
        focus_extra = """
【本轮回召重点：行业应用与落地产品】
- 医疗/健康、金融/风控、制造/工厂、零售/电商、教育、自动驾驶、广告/营销等垂直行业
- 企业部署案例、实际落地产品与解决方案、行业报告与动态
"""
    elif "research" in pass_name or "algorithm" in pass_name:
        focus_extra = """
【本轮回召重点：科研与算法】
- 论文与预印本（arXiv、OpenReview、顶会）、新模型/新架构发布
- 强化学习、Agent、多模态、推理与评测基准
"""
    else:
        focus_extra = """
【特别关注：你必须尽量覆盖】
- GPU 渠道链条信号：AIB/系统商/分销商（GIGABYTE/技嘉、Supermicro、ASUS、MSI 等）
- 渠道报价/现货/交期/配额/库存
- 供应链与采购成本：HBM3e/DRAM/DDR5/GDDR、CoWoS/封装/ABF基板、交付周期变化
"""
    prompt = f"""
你是一名 AI/GPU 行业情报召回助手。请基于联网搜索，在时间窗口 {start}~{end} 召回候选【原文 URL】。
你只需要输出候选 URL 列表（URL + 少量线索），不要写完整新闻摘要，不要编造。

【本地已收录样本（用于避免重复方向）】
{json.dumps(local_refs, ensure_ascii=False, indent=2)}
{focus_extra}

【输出要求】⚠️ 关键：每条新闻/信息必须附带真实可访问的 URL，无 URL 的条目将全部被丢弃！
- 只输出严格 JSON 数组，不要 markdown，不要解释
- 每条对象字段：
  - url: 原文链接（必须可打开的完整 URL，以 http:// 或 https:// 开头，禁止编造）
  - source_hint: 站点名/媒体名（可空）
  - title_hint: 页面标题（可空）
  - date_hint: YYYY-MM-DD（不确定可空）
  - reason: 1句话说明强相关点（可空）
- 每轮最多 {per_pass} 条（pass={pass_name}）
- 不要输出 docs/help/wiki/manual/faq 页面
- 禁止输出无 URL 的条目，禁止使用占位符 URL（如 https://example.com）
""".strip() + "\n\n【本轮检索关键词】\n" + "\n".join("- " + q for q in queries)

    set_phase("recall")
    set_current_site(f"召回: {pass_name}")
    first_q = (queries[0] or "").strip() if queries else ""
    set_current_url(first_q[:500] if first_q else pass_name)
    set_current_content("检索关键词: " + ", ".join((q or "").strip()[:60] for q in (queries or [])[:5]))
    try:
        data = call_model_json_array(prompt, pass_name=f"recall-url-{pass_name}", use_web_search=True)
    except ValueError as e:
        print(f"[recall] 本轮回召解析失败 (pass={pass_name})，跳过本轮: {e}", file=sys.stderr)
        return []

    # 严格过滤：仅保留有有效 URL 的条目
    data = _filter_valid_urls(data)
    if not data:
        print(f"[recall] 本轮回召无有效 URL (pass={pass_name})，跳过", file=sys.stderr)
        return []

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


def recall_research_papers(start: str, end: str, local_refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    科研论文专项检索：在 arXiv/顶会/预印本平台搜索近期最新论文，返回带摘要的真实链接。
    与普通召回不同，这里直接调用外部搜索获取真实论文 URL + 摘要，不依赖大模型编造。
    """
    S = f"{start} to {end}"
    # 构造多维度论文检索 query
    paper_queries = [
        f"site:arxiv.org AI machine learning {S}",
        f"site:arxiv.org LLM large language model {S}",
        f"site:arxiv.org transformer MoE diffusion {S}",
        f"NeurIPS ICLR ICML 2025 paper",
        f"arXiv new papers AI 2025",
    ]

    # 使用外部搜索获取真实论文链接（不经过大模型，避免编造）
    paper_results: List[Dict[str, Any]] = []
    seen_urls = set()

    for q in paper_queries:
        set_phase("recall")
        set_current_site("科研论文检索")
        set_current_url(q[:200])
        set_current_content(f"论文检索: {q}")

        raw = run_web_search(q, num_results=10)
        if not raw:
            continue

        # 解析搜索结果：提取标题、链接、摘要
        current_item = {}
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("标题:"):
                current_item = {"title": line.split(":", 1)[-1].strip(), "url": "", "snippet": ""}
            elif line.startswith("链接:") and current_item:
                url = line.split(":", 1)[-1].strip()
                if url and url not in seen_urls and _is_valid_url(url):
                    current_item["url"] = url
                    seen_urls.add(url)
            elif line.startswith("摘要:") and current_item:
                current_item["snippet"] = line.split(":", 1)[-1].strip()
                # 完成一条，保存
                if current_item.get("url"):
                    paper_results.append(current_item)
                    current_item = {}

        # 防止最后一条没有摘要的情况
        if current_item.get("url") and "snippet" not in current_item:
            paper_results.append(current_item)

    if not paper_results:
        print("[recall] 科研论文检索未返回结果", file=sys.stderr)
        return []

    # 只保留前 10 篇最新最相关的
    paper_results = paper_results[:10]

    # 转换为标准召回格式
    out = []
    for i, p in enumerate(paper_results):
        url = p.get("url", "").strip()
        if not url or not _is_valid_url(url):
            continue
        out.append({
            "url": url,
            "canonical_url": canonicalize_url(url),
            "source_hint": p.get("source_hint", "").strip() or "arXiv/论文",
            "title_hint": p.get("title", "").strip(),
            "date_hint": "",
            "reason": (p.get("snippet") or "").strip()[:100],
            "pass": "research-papers",
        })

    print(f"[recall] 科研论文检索完成，获取 {len(out)} 篇论文", file=sys.stderr)
    return out
