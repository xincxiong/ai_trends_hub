# -*- coding: utf-8 -*-
"""数据层调用 LLM 的通用封装：解析 JSON 数组。支持 Responses API（联网）与 Chat Completions。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from ..model import call_responses


def extract_json_array(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        return text
    m = re.search(r"\[\s*\{.*?\}\s*\]", text, flags=re.S)
    if m:
        return m.group(0)
    l, r = text.find("["), text.rfind("]")
    if l != -1 and r != -1 and r > l:
        return text[l : r + 1]
    return None


def safe_json_loads(raw: Optional[str]) -> Optional[Any]:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def call_model_json_array(
    prompt: str,
    pass_name: str = "",
    use_web_search: bool = True,
) -> List[Dict[str, Any]]:
    """调用模型并解析输出为 JSON 数组；失败时尝试一次修复解析。需要联网时传 web_search，由 API 能力决定是否生效。"""
    use_web = use_web_search  # 始终按调用方意图传 web_search，不支持时 call_responses 会降级
    tools = [{"type": "web_search"}] if use_web else None
    resp = call_responses(prompt=prompt, tools=tools)
    raw = getattr(resp, "output_text", None) or ""

    json_text = extract_json_array(raw)
    data = safe_json_loads(json_text)

    if data is None:
        repair_prompt = f"""
把下面输出转换成【严格 JSON 数组】。只输出 JSON，不要解释。

原始输出：
{raw}
""".strip()
        resp2 = call_responses(prompt=repair_prompt, tools=None)
        raw2 = getattr(resp2, "output_text", None) or ""
        json_text2 = extract_json_array(raw2)
        data = safe_json_loads(json_text2)

    if data is None or not isinstance(data, list):
        raise ValueError("无法解析模型输出为 JSON 数组。请查看上方 RAW 输出。")

    return [x for x in data if isinstance(x, dict)]
