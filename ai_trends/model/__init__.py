# 模型调用处理中间层：负责大模型 API 接入、管理、调度
from .client import get_llm_client, call_responses

# 国产模型预设列表（与 config.DOMESTIC_LLM_BASE_URLS 一致，便于文档与 API 展示）
SUPPORTED_DOMESTIC_PROVIDERS = (
    "zhipu",      # 智谱 AI
    "moonshot",   # 月之暗面 Kimi
    "dashscope",  # 通义千问
    "qwen",       # 通义（同 dashscope）
    "doubao",     # 豆包
    "deepseek",   # DeepSeek
    "minimax",    # MiniMax
)

__all__ = ["get_llm_client", "call_responses", "SUPPORTED_DOMESTIC_PROVIDERS"]
