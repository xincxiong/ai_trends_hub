# -*- coding: utf-8 -*-
"""Stage B：对候选 URL 联网核验并抽取结构化字段（真实性证据）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from ..config import settings
from .url_utils import canonicalize_url, force_source_normalization
from .llm_helpers import call_model_json_array


def _chunk_list(lst: List[Any], n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def verify_urls(url_items: List[Dict[str, Any]], start: str, end: str) -> List[Dict[str, Any]]:
    batch_size = getattr(settings, "verify_batch_size", 10)
    verified_all: List[Dict[str, Any]] = []

    for batch in _chunk_list(url_items, batch_size):
        prompt = f"""
你是一名【事实核验编辑】。请对下面候选 URL 逐条联网打开核验，并从原文抽取结构化字段。
时间窗口：{start}~{end}（以发布时间或事件确认日期为准）。

【真实性硬规则（很重要）】
- 你必须能在页面上明确看到：标题 + 来源/站点 + 发布时间/日期（或可推断为同日且页面明确标注）
- 如果无法确认日期/标题/关键事实一致：verified=false
- 如果内容明显是“论坛瞎聊/无来源传闻/二手拼接且无法对应原文证据”：verified=false
- summary 只写原文事实（中文 2-3 句），不要推测
- 渠道/报价/成本类：尽量抽取“报价区间/交期/供需/成本驱动因素”，但必须来自原文

【输出要求】
- 只输出严格 JSON 数组，不要 markdown，不要解释
- Reuters 转载源（Yahoo/MSN/Investing/MarketScreener/Nasdaq等），source 统一写 Reuters

每条输出字段：
- url
- canonical_url
- verified: true/false
- confidence: 0~1
- date: YYYY-MM-DD（核验后的发布日期或事件确认日期；无法确认则空字符串）
- title: 核验后的中文标题（新闻标题风格）
- source: 核验后的媒体/站点名
- summary: 中文 2-3 句（事实，不推测）
- region: Global/China/US/EU/APAC
- main_category: 五选一（必填）ai_hardware / ai_software / ai_application / ai_funding_ma / ai_research
  - 行业落地、垂直应用、企业案例、医疗/金融/制造/教育等 → ai_application
  - 论文、顶会、新算法、评测、开源模型研究 → ai_research
- segment: 例如
  AI芯片/云计算/数据中心/投融资/并购/出口管制/软件生态/供应链
  大模型发布/大模型开源/推理与部署/Agent工具链/国产GPU/智算中心
  渠道与现货/内存与成本/采购与TCO
  行业应用与落地/医疗金融制造教育自动驾驶
  科研与算法/论文/顶会/评测基准
- tags: 2-5 个中文标签
- event_type: fact/analysis/technical（三选一）
- metrics: 仅渠道/成本/采购类填写，否则为 null
  - metric_type: spot_price/quote/contract_price/cost_trend/lead_time/supply_tightness/bom_cost/tco
  - item: H100/H200/B200/GB200/HBM3e/DDR5/GDDR7/CoWoS/ABF substrate/液冷 等
  - value: 数值或区间（可空）
  - unit: USD/台/周/月/% 等（可空）
  - context: 1句上下文（必须来自原文）
  - channel_vendor: 技嘉/GIGABYTE/Supermicro/ASUS/MSI/分销商名（可空）
  - geo: 报价/交期对应地区（US/China/Singapore/... 可空）
- evidence: 【真实性证据】对象（必须有；否则 verified=false）
  - title_on_page: 原文页标题（原文语言）
  - published_date_text: 页面显示的日期原文（例如 “Jan 21, 2026” 或 “2026年1月21日”）
  - key_fact_snippet: 关键事实的原文短句（<=25词/<=40字）
  - pricing_or_leadtime_snippet: 如果是渠道/成本类，给出原文短句（否则空字符串）

候选 URL items：
{json.dumps(batch, ensure_ascii=False, indent=2)}
""".strip()

        data = call_model_json_array(prompt, pass_name="verify-url", use_web_search=True)

        for x in data:
            if not isinstance(x, dict):
                continue
            url = (x.get("url") or "").strip()
            if not url:
                continue

            cu = (x.get("canonical_url") or "").strip() or canonicalize_url(url)
            x["canonical_url"] = cu
            x["source"] = force_source_normalization(url, x.get("source", ""))

            et = (x.get("event_type") or "fact").strip().lower()
            if et not in {"fact", "analysis", "technical"}:
                et = "fact"
            x["event_type"] = et

            m = x.get("metrics")
            if not isinstance(m, dict):
                x["metrics"] = None
            else:
                for k in ["metric_type", "item", "value", "unit", "context", "channel_vendor", "geo"]:
                    if k not in m:
                        m[k] = ""
                x["metrics"] = m

            ev = x.get("evidence")
            if not isinstance(ev, dict):
                x["evidence"] = None
            else:
                for k in ["title_on_page", "published_date_text", "key_fact_snippet", "pricing_or_leadtime_snippet"]:
                    if k not in ev:
                        ev[k] = ""
                x["evidence"] = ev

            verified_all.append(x)

    return verified_all
