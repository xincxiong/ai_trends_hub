from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# 国产模型 API 预设 Base URL（OpenAI 兼容端点）
# 使用方式：设置 LLM_PROVIDER=zhipu 等，无需再设 LLM_API_BASE
# 各厂商 API Base URL（OpenAI 兼容端点）；LLM_PROVIDER 对应时优先使用此处，否则用 LLM_API_BASE
DOMESTIC_LLM_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",                       # OpenAI 官方
    "zhipu": "https://open.bigmodel.cn/api/paas/v4/",            # 智谱 AI
    "moonshot": "https://api.moonshot.cn/v1",                     # 月之暗面 Kimi
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",  # 通义千问（兼容模式）
    "doubao": "https://ark.cn-beijing.volces.com/api/v3",         # 豆包（火山引擎，区域可调）
    "deepseek": "https://api.deepseek.com/v1",                    # DeepSeek
    "minimax": "https://api.minimax.chat/v1",                     # MiniMax
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1", # 通义（同 dashscope）
}

# 支持 OpenAI Responses API（含 web_search 联网搜索）的接入方式。
# - "openai"：未设置 LLM_PROVIDER 或使用 OpenAI 官方端点时，视为支持 Responses API。
# - "custom"：仅设置 LLM_API_BASE 时，会先尝试 Responses API，不支持则降级为 Chat Completions。
# 国产模型（DOMESTIC_LLM_BASE_URLS 中的 key）均不支持 Responses API，仅支持 Chat Completions。
RESPONSES_API_SUPPORTED_PROVIDERS = frozenset({"openai", "custom"})


@dataclass
class Settings:
    # 大模型配置（可自定义 API）
    # 优先使用 LLM_API_KEY，其次回退到 OPENAI_API_KEY
    llm_api_key: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    llm_api_base: str | None = os.getenv("LLM_API_BASE")  # 可选：自定义兼容 OpenAI 的 Base URL
    llm_model: str = os.getenv("AI_TRENDS_MODEL", "gpt-4.1-mini")
    # 国产模型接入：设为 zhipu / moonshot / dashscope / doubao / deepseek / minimax / qwen 等时，
    # 自动使用对应 Base URL（若未设置 LLM_API_BASE）
    llm_provider: str = (os.getenv("LLM_PROVIDER") or "").strip().lower()

    # 数据文件
    news_data_path: Path = DATA_DIR / "news.json"
    snapshots_dir: Path = DATA_DIR / "snapshots"

    # 抓取相关
    window_days: int = int(os.getenv("AI_TRENDS_WINDOW_DAYS", "2"))
    max_items: int = int(os.getenv("AI_TRENDS_MAX_ITEMS", "400"))
    report_tz: str = os.getenv("AI_TRENDS_REPORT_TZ", "Asia/Shanghai")

    # 两阶段抓取（URL 召回 + 联网核验）
    two_stage_fetch: bool = os.getenv("AI_TRENDS_TWO_STAGE", "true").lower() in ("1", "true", "yes")
    local_ref_path: str | None = os.getenv("AI_TRENDS_LOCAL_REF_PATH") or None  # 本地参考样本，用于去重与召回引导
    local_sample_size: int = int(os.getenv("AI_TRENDS_LOCAL_SAMPLE_SIZE", "120"))
    include_existing_in_output: bool = os.getenv("AI_TRENDS_INCLUDE_EXISTING", "true").lower() in ("1", "true", "yes")

    # Stage A 召回
    stage_a_passes: int = int(os.getenv("AI_TRENDS_STAGE_A_PASSES", "16"))
    stage_a_max_urls: int = int(os.getenv("AI_TRENDS_STAGE_A_MAX_URLS", "420"))
    stage_a_per_pass_limit: int = int(os.getenv("AI_TRENDS_STAGE_A_PER_PASS_LIMIT", "26"))
    relax_stage_a_filters: bool = True
    enable_channel_monitoring: bool = True

    # Stage B 核验
    verify_batch_size: int = int(os.getenv("AI_TRENDS_VERIFY_BATCH_SIZE", "10"))
    verify_min_confidence: float = float(os.getenv("AI_TRENDS_VERIFY_MIN_CONFIDENCE", "0.74"))
    verify_require_date: bool = True
    strict_domain_after_verify: bool = False

    # 存储与增量
    news_backup_before_merge: bool = True
    news_keep_days: int = int(os.getenv("AI_TRENDS_NEWS_KEEP_DAYS", "30"))

    # Chat Completions 适配层：外部联网检索（无 Responses API 时使用）
    # 可选：SERPER_API_KEY 使用 Serper 检索；不设则用 DuckDuckGo 免费检索
    serper_api_key: str = (os.getenv("SERPER_API_KEY") or "").strip()
    web_search_max_results: int = int(os.getenv("AI_TRENDS_WEB_SEARCH_MAX_RESULTS", "25"))

    # 基本类别
    main_categories: tuple[str, ...] = (
        "ai_hardware",
        "ai_software",
        "ai_application",
        "ai_funding_ma",
        "ai_research",
    )


settings = Settings()
settings.snapshots_dir.mkdir(parents=True, exist_ok=True)

