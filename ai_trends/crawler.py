from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from .config import settings
from .llm import call_responses


@dataclass
class CrawlWindow:
    start: str  # YYYY-MM-DD
    end: str    # YYYY-MM-DD


def build_crawl_prompt(win: CrawlWindow) -> str:
    S = f"{win.start}..{win.end}"
    return f"""
你是一名 AI 行业情报编辑，负责从全球主流网站中【联网检索】过去几天 ({S}) 内的 AI 动态。

请通过搜索（工具会帮你）召回并阅读网页，输出一批结构化新闻条目，重点覆盖：
- AI 硬件：GPU/ASIC/TPU/NPU、AI 服务器、存储与网络、芯片制造与封装
- AI 软件：大模型/开源模型、框架与 SDK、Agent 平台、工具链与部署方案
- AI 行业应用：医疗/金融/制造/零售/教育/自动驾驶/广告等实际落地案例
- AI 融资并购：与 AI 相关的融资轮次、并购交易、投资与估值变动
- AI 科研：新算法/架构（如 Transformer 变体、MoE、Diffusion 等）、强化学习、决策优化、Agent 与多智能体系统、评测基准/论文/顶会进展

【重要要求】
- 必须基于真实网页内容或论文页面，不要编造
- 每条新闻至少来自一个可打开的新闻/博客/公告/论文页面
- 同一事件尽量只保留 1 条最权威或信息量最大的来源

【输出格式】
- 严格输出 JSON 数组，不要 markdown，不要额外说明
- 数组中每个对象字段：
  - url: 原文链接
  - canonical_url: 规范化后的链接（若不确定可与 url 相同）
  - date: YYYY-MM-DD（发布日期或事件确认日期）
  - title: 中文新闻标题（简洁、准确）
  - summary: 中文 2-3 句摘要，只写原文事实
  - source: 媒体/站点名（论文则填会议/期刊/平台，如 NeurIPS/ICLR/arXiv 等）
  - region: Global/China/US/EU/APAC（按主要关注地区粗分）
  - main_category: 五选一
    - ai_hardware（AI 硬件 / 芯片 / 服务器 / 存储 / 网络）
    - ai_software（模型 / 框架 / 工具链 / 平台 / SDK / Agent）
    - ai_application（各行业的实际应用）
    - ai_funding_ma（融资 / 投资 / 并购 / 上市 / 估值）
    - ai_research（科研进展 / 新算法 / 强化学习 / Agent / 多智能体 / 评测基准）
  - sub_categories: 2-5 个细分类标签（字符串数组），例如：
    - 对硬件：["GPU","AI server","HBM","inference accelerator"]
    - 对软件：["LLM","open-source model","MLOps","agent platform"]
    - 对应用：["医疗","自动驾驶","广告推荐","工业质检"]
    - 对融资并购：["Series A","acquisition","strategic investment"]
    - 对科研：["RL","offline RL","model-based RL","multi-agent","agent","benchmark","NeurIPS 2026"]
  - segment: 可选的简要业务/研究分段（如 "AI芯片","云计算","强化学习","Agent 系统"），可空字符串
  - tags: 2-5 个中文标签数组
  - event_type: fact/analysis/technical 三选一
  - metrics: 如无结构化数值信息则为 null；有的话为对象：
    - metric_type: spot_price/contract_price/cost_trend/lead_time/bom_cost/tco 等
    - item: 例如 H100/H200/GB200/HBM3e/DDR5/GDDR6/液冷 等
    - value: 数值或区间（字符串）
    - unit: 单位（USD/台/周/月/% 等）
    - context: 1 句上下文说明（必须来自原文）
    - channel_vendor: 若涉及渠道/厂商则填公司名，否则空字符串
    - geo: 报价/交期对应地区（US/China/...）
  - evidence: 用于真实性校验的证据对象：
    - title_on_page: 原文标题（原文语言）
    - published_date_text: 页面上显示的日期原文
    - key_fact_snippet: 关键事实的原文短句
    - pricing_or_leadtime_snippet: 若有价格/交期信息则给一段原文，否则空字符串

请输出不超过 100 条高质量新闻，严格 JSON 数组。
""".strip()


def _extract_json_array(text: str) -> str | None:
    text = (text or "").strip()
    if not text:
        return None
    if text.startswith("[") and text.endswith("]"):
        return text
    import re

    m = re.search(r"\[\s*\{.*\}\s*\]", text, flags=re.S)
    if m:
        return m.group(0)
    l, r = text.find("["), text.rfind("]")
    if l != -1 and r != -1 and r > l:
        return text[l : r + 1]
    return None


def fetch_raw_items(win: CrawlWindow) -> List[Dict[str, Any]]:
    """
    只负责“通过 OpenAI + web_search 抓取并返回原始 JSON 对象列表”，
    不做 Pydantic 校验与去重，便于与上层 pipeline 解耦。
    """
    prompt = build_crawl_prompt(win)
    tools = [{"type": "web_search"}]
    resp = call_responses(prompt=prompt, tools=tools)
    raw = resp.output_text or ""

    json_text = _extract_json_array(raw)
    if not json_text:
        raise ValueError("无法从模型输出中提取 JSON 数组。")

    data = json.loads(json_text)
    if not isinstance(data, list):
        raise ValueError("模型输出不是 JSON 数组。")

    items: List[Dict[str, Any]] = []
    for x in data:
        if isinstance(x, dict):
            items.append(x)
    return items

