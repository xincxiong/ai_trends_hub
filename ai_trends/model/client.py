"""大模型 API 客户端封装：接入、管理、调度。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..config import DOMESTIC_LLM_BASE_URLS, settings


def _resolve_base_url() -> Optional[str]:
    """解析 Base URL：优先 LLM_API_BASE，否则按 LLM_PROVIDER 使用国产模型预设。"""
    if settings.llm_api_base:
        return settings.llm_api_base.strip().rstrip("/")
    if settings.llm_provider and settings.llm_provider in DOMESTIC_LLM_BASE_URLS:
        return DOMESTIC_LLM_BASE_URLS[settings.llm_provider].rstrip("/")
    return None


def get_llm_client() -> OpenAI:
    """
    返回已根据配置初始化的大模型客户端。
    - 支持 LLM_API_KEY / LLM_API_BASE / AI_TRENDS_MODEL 自定义。
    - 国产模型：设置 LLM_PROVIDER=zhipu|moonshot|dashscope|doubao|deepseek|minimax|qwen
      即可使用对应厂商的 OpenAI 兼容端点，无需再配 LLM_API_BASE。
    """
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY / OPENAI_API_KEY 未配置，无法调用大模型 API。")

    client_kwargs: Dict[str, Any] = {"api_key": settings.llm_api_key}
    base_url = _resolve_base_url()
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def call_responses(
    prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
    **extra_kwargs: Any,
):
    """统一封装 Responses API 调用，供数据层抓取等场景使用。"""
    client = get_llm_client()
    resp = client.responses.create(
        model=settings.llm_model,
        input=prompt,
        tools=tools,
        **extra_kwargs,
    )
    return resp
