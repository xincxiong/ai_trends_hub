"""大模型 API 客户端封装：接入、管理、调度。支持 OpenAI 与国产大模型（智谱/通义/DeepSeek 等）。"""
from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import AuthenticationError, NotFoundError, RateLimitError

from ..config import (
    DOMESTIC_LLM_BASE_URLS,
    RESPONSES_API_SUPPORTED_PROVIDERS,
    settings,
)

# 国产大模型仅提供 Chat Completions，不提供 Responses API；此集合与 DOMESTIC_LLM_BASE_URLS 一致
DOMESTIC_PROVIDERS = frozenset(DOMESTIC_LLM_BASE_URLS.keys())


def _current_provider_kind() -> str:
    """
    识别当前接入方式类型，用于判断是否支持 Responses API。
    - 国产：返回 LLM_PROVIDER 值（如 zhipu, deepseek）
    - 仅设置 LLM_API_BASE：返回 "custom"
    - 否则（OpenAI 或未指定）：返回 "openai"
    """
    if settings.llm_provider and settings.llm_provider in DOMESTIC_PROVIDERS:
        return settings.llm_provider.strip().lower()
    if settings.llm_api_base:
        return "custom"
    return "openai"


def supports_responses_api() -> bool:
    """当前配置是否支持 OpenAI Responses API（含 web_search 等工具）。国产模型不支持。"""
    kind = _current_provider_kind()
    return kind in RESPONSES_API_SUPPORTED_PROVIDERS


def get_api_support_info() -> Dict[str, Any]:
    """
    返回当前 API 接入的支持情况，便于展示或日志。
    - provider_kind: 当前类型（openai / custom / zhipu / deepseek 等）
    - supports_responses_api: 是否支持 Responses API
    - description: 简短说明
    """
    kind = _current_provider_kind()
    supports = kind in RESPONSES_API_SUPPORTED_PROVIDERS
    if kind in DOMESTIC_PROVIDERS:
        desc = "仅支持 Chat Completions，无联网搜索，结果基于模型知识。"
    elif kind in RESPONSES_API_SUPPORTED_PROVIDERS:
        desc = (
            "支持 Responses API（含 web_search 联网搜索）。"
            if kind == "openai"
            else "自定义网关：会先尝试 Responses API，不支持则降级为 Chat Completions。"
        )
    else:
        desc = "未知接入类型，将使用 Chat Completions。"
    return {
        "provider_kind": kind,
        "supports_responses_api": supports,
        "description": desc,
    }


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
        raise ValueError(
            "LLM_API_KEY / OPENAI_API_KEY 未配置，无法调用大模型 API。\n"
            "请先配置：1) cp env.example.sh env.sh  2) 编辑 env.sh 填入 API Key  3) source env.sh  后再运行。"
        )

    client_kwargs: Dict[str, Any] = {"api_key": settings.llm_api_key}
    base_url = _resolve_base_url()
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def _call_chat_completions(client: OpenAI, prompt: str) -> SimpleNamespace:
    """使用 Chat Completions 接口调用（国产大模型或降级时使用，无联网搜索）。"""
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
    )
    content = (resp.choices[0].message.content or "").strip()
    return SimpleNamespace(output_text=content)


def call_responses(
    prompt: str,
    tools: Optional[List[Dict[str, Any]]] = None,
    **extra_kwargs: Any,
):
    """
    统一调用入口：返回带 output_text 的响应对象。
    - 国产大模型（LLM_PROVIDER 为 zhipu/moonshot/dashscope 等）：直接走 Chat Completions，无联网搜索。
    - 其他（如 OpenAI）：优先 Responses API（支持 web_search），若 404 则降级为 Chat Completions。
    """
    client = get_llm_client()

    # 国产大模型：不支持 Responses API，直接走 Chat Completions
    if not supports_responses_api():
        info = get_api_support_info()
        print(
            f"当前接入 [{info['provider_kind']}]：{info['description']}",
            file=sys.stderr,
        )
        return _call_chat_completions(client, prompt)

    # OpenAI 或自定义网关：优先 Responses API
    try:
        resp = client.responses.create(
            model=settings.llm_model,
            input=prompt,
            tools=tools,
            **extra_kwargs,
        )
        return resp
    except NotFoundError:
        print(
            "当前 API 不支持 Responses 接口，已降级为 Chat Completions（无联网搜索）。",
            file=sys.stderr,
        )
        return _call_chat_completions(client, prompt)
    except AuthenticationError as e:
        raise RuntimeError(
            "API Key 无效或已失效（401）。请检查 env.sh 中的 LLM_API_KEY / OPENAI_API_KEY 是否正确，"
            "或到对应平台（如 platform.openai.com、智谱/DeepSeek 等）重新获取 Key 后更新 env.sh 并 source 加载。"
        ) from e
    except RateLimitError as e:
        err_msg = str(e).lower()
        if "quota" in err_msg or "insufficient_quota" in err_msg:
            raise RuntimeError(
                "当前 API 配额已用尽（429 insufficient_quota）。请检查账户余额与计费设置，或更换 API Key / 改用国产模型（如 env.sh 中配置 LLM_PROVIDER=zhipu 等）。"
            ) from e
        raise RuntimeError(
            "请求频率超限（429）。可稍后重试，或更换 API / 使用国产模型。"
        ) from e
