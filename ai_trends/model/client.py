"""大模型 API 客户端封装：接入、管理、调度。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import OpenAI

from ..config import settings


def get_llm_client() -> OpenAI:
    """
    返回已根据配置初始化的大模型客户端。
    支持 LLM_API_KEY / LLM_API_BASE / AI_TRENDS_MODEL 自定义，
    兼容 OpenAI 官方或第三方兼容网关。
    """
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY / OPENAI_API_KEY 未配置，无法调用大模型 API。")

    client_kwargs: Dict[str, Any] = {"api_key": settings.llm_api_key}
    if settings.llm_api_base:
        client_kwargs["base_url"] = settings.llm_api_base
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
