"""数据抓取：通过模型中间层获取原始内容。支持 Responses API（联网检索）与 Chat Completions（基于知识）。"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from ..model import call_responses
from .domains import get_preferred_domains_hint


@dataclass
class CrawlWindow:
    start: str  # YYYY-MM-DD
    end: str    # YYYY-MM-DD


def build_crawl_prompt(win: CrawlWindow, use_web_search: bool = True) -> str:
    S = f"{win.start}..{win.end}"
    if use_web_search:
        return f"""
你是一名 AI 行业情报编辑，负责从全球主流网站中【联网检索】过去几天 ({S}) 内的 AI 动态。

请优先从以下项目配置的权威信源检索并采集（可配合站点内搜索）：{get_preferred_domains_hint()}
在以上站点及同类媒体、厂商官网、学术与开源站点中召回并阅读网页，输出一批结构化新闻条目，重点覆盖：
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
  - sub_categories: 2-5 个细分类标签（字符串数组）
  - segment: 可选的简要业务/研究分段，可空字符串
  - tags: 2-5 个中文标签数组
  - event_type: fact/analysis/technical 三选一
  - metrics: 如无则为 null；有则为对象（metric_type, item, value, unit, context, channel_vendor, geo）
  - evidence: 对象（title_on_page, published_date_text, key_fact_snippet, pricing_or_leadtime_snippet）

请输出不超过 100 条高质量新闻，严格 JSON 数组。
""".strip()

    # 仅 Chat Completions 时：基于模型知识生成，无联网
    return f"""
你是一名 AI 行业情报编辑。当前无法联网检索，请基于你的知识库，列出近期（约 {S} 时间段）可能出现的或已知的 AI/GPU 相关新闻、动态、产品发布与行业事件。

重点覆盖：
- AI 硬件：GPU/ASIC/TPU、AI 服务器、芯片与封装（如 NVIDIA/AMD/Intel、HBM、CoWoS）
- AI 软件：大模型、开源模型、框架与 Agent 平台
- AI 行业应用与融资并购、科研进展（新模型、顶会、论文）

【要求】
- 每条尽量给出真实存在过的来源域名或媒体名（如 reuters.com、techcrunch.com、arxiv.org），url 可填该站点根域名或合理路径
- 若无法确定具体链接，url 可填 https://example.com/placeholder，不要编造不存在的 URL 路径
- 日期填你已知或合理推断的 YYYY-MM-DD

【输出格式】
- 严格输出 JSON 数组，不要 markdown，不要额外说明
- 数组中每个对象字段：
  - url: 原文链接（可合理推断）
  - canonical_url: 与 url 相同即可
  - date: YYYY-MM-DD
  - title: 中文新闻标题
  - summary: 中文 2-3 句摘要
  - source: 媒体/站点名
  - region: Global/China/US/EU/APAC
  - main_category: 五选一 ai_hardware / ai_software / ai_application / ai_funding_ma / ai_research
  - sub_categories: 2-5 个细分类标签（字符串数组）
  - segment: 可空字符串
  - tags: 2-5 个中文标签数组
  - event_type: fact/analysis/technical 三选一
  - metrics: 如无则为 null
  - evidence: 对象（title_on_page, published_date_text, key_fact_snippet, pricing_or_leadtime_snippet），可填空字符串

请输出不超过 80 条，严格 JSON 数组。
""".strip()


def _extract_json_array(text: str) -> str | None:
    text = (text or "").strip()
    if not text:
        return None
    if text.startswith("[") and text.endswith("]"):
        return text
    m = re.search(r"\[\s*\{.*\}\s*\]", text, flags=re.S)
    if m:
        return m.group(0)
    l, r = text.find("["), text.rfind("]")
    if l != -1 and r != -1 and r > l:
        return text[l : r + 1]
    return None


def fetch_raw_items(win: CrawlWindow) -> List[Dict[str, Any]]:
    """通过模型中间层抓取并返回原始 JSON 对象列表。始终请求联网检索；若 API 不支持则自动降级为基于模型知识。"""
    use_web = True  # 始终请求 web_search，由 call_responses 根据 API 能力尝试或降级
    prompt = build_crawl_prompt(win, use_web_search=use_web)
    tools = [{"type": "web_search"}]
    resp = call_responses(prompt=prompt, tools=tools)
    raw = getattr(resp, "output_text", None) or ""

    json_text = _extract_json_array(raw)
    if not json_text:
        raise ValueError("无法从模型输出中提取 JSON 数组。")

    data = json.loads(json_text)
    if not isinstance(data, list):
        raise ValueError("模型输出不是 JSON 数组。")

    return [x for x in data if isinstance(x, dict)]
