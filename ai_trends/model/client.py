"""大模型 API 客户端封装：接入、管理、调度。支持 OpenAI 与国产大模型（智谱/通义/DeepSeek 等）。"""
from __future__ import annotations

import sys
import locale
import httpx
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import AuthenticationError, NotFoundError, RateLimitError

from ..config import (
    DOMESTIC_LLM_BASE_URLS,
    RESPONSES_API_SUPPORTED_PROVIDERS,
    settings,
)

# 强制使用 UTF-8 编码，解决 httpx 的 UnicodeEncodeError
if sys.version_info >= (3, 7):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

locale.setlocale(locale.LC_ALL, 'C.UTF-8') if 'C.UTF-8' in locale.locale_alias else locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

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
    """解析 Base URL：已设 LLM_PROVIDER 时用该厂商预设，保证与 Key 一致；否则用 LLM_API_BASE。"""
    if settings.llm_provider and settings.llm_provider in DOMESTIC_LLM_BASE_URLS:
        return DOMESTIC_LLM_BASE_URLS[settings.llm_provider].rstrip("/")
    if settings.llm_api_base:
        return settings.llm_api_base.strip().rstrip("/")
    return None


def get_llm_client() -> OpenAI:
    """
    返回已根据配置初始化的大模型客户端。
    - 支持 LLM_API_KEY / LLM_API_BASE / AI_TRENDS_MODEL 自定义。
    - 国产模型：设置 LLM_PROVIDER=zhipu|moonshot|dashscope|doubao|deepseek|minimax|qwen
      即可使用对应厂商的 OpenAI 兼容端点，无需再配 LLM_API_BASE。
    - 使用 httpx 客户端，强制 UTF-8 编码以避免 UnicodeEncodeError。
    """
    if not settings.llm_api_key:
        raise ValueError(
            "LLM_API_KEY / OPENAI_API_KEY 未配置，无法调用大模型 API。\n"
            "请先配置：1) cp env.example.sh env.sh  2) 编辑 env.sh 填入 API Key  3) source env.sh  后再运行。"
        )

    http_client = httpx.Client(
        timeout=120.0,
        headers={"Accept-Charset": "utf-8"},
    )

    client_kwargs: Dict[str, Any] = {"api_key": settings.llm_api_key, "http_client": http_client}
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
    - 优先尝试 Responses API（含 web_search 联网搜索），若 404 则自动降级为 Chat Completions。
    - 国产模型也先尝试 Responses API，一般会 404 降级；若明确不支持可节省一次调用。
    - 返回结果附带 actual_mode 属性，标记实际使用的模式（responses / chat）。
    """
    client = get_llm_client()
    info = get_api_support_info()
    provider = info['provider_kind']

    # 如果参数明确不传 tools（如重试/修复场景），直接走 Chat 避免无意义调用
    if tools is None:
        print(
            f"当前接入 [{provider}]：不使用联网搜索，直接使用 Chat Completions（基于模型知识）。",
            file=sys.stderr,
        )
        try:
            result = _call_chat_completions(client, prompt)
            result.actual_mode = "chat"
            return result
        except AuthenticationError as e:
            base = _resolve_base_url() or "(OpenAI 默认)"
            raise RuntimeError(
                f"API Key 认证失败（401）。当前使用：provider={provider}, base={base}。"
                "请确认：1) env.sh 里的 LLM_API_KEY 是否来自该厂商；2) 该 Key 在对应控制台是否有效、未过期；"
                "3) 若用代理或自定义 Base，LLM_API_BASE 是否与 Key 所属服务一致。修改后请重新 source env.sh 再运行。"
            ) from e

    # 尝试 Responses API
    try:
        resp = client.responses.create(
            model=settings.llm_model,
            input=prompt,
            tools=tools,
            **extra_kwargs,
        )
        resp.actual_mode = "responses"
        print(
            f"当前接入 [{provider}]：使用 Responses API（联网检索）。",
            file=sys.stderr,
        )
        return resp
    except NotFoundError:
        print(
            f"当前接入 [{provider}]：Responses API 不支持，已降级为 Chat Completions（基于模型知识，无联网检索）。",
            file=sys.stderr,
        )
        result = _call_chat_completions(client, prompt)
        result.actual_mode = "chat"
        return result
    except AuthenticationError as e:
        base = _resolve_base_url() or "(OpenAI 默认)"
        raise RuntimeError(
            f"API Key 认证失败（401）。当前使用：provider={provider}, base={base}。"
            "请确认：1) env.sh 里的 LLM_API_KEY 是否来自该厂商；2) 该 Key 在对应控制台是否有效、未过期；"
            "3) 若用代理或自定义 Base，LLM_API_BASE 是否与 Key 所属服务一致。修改后请重新 source env.sh 再运行。"
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
