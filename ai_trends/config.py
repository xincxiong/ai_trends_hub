from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    # 大模型配置（可自定义 API）
    # 优先使用 LLM_API_KEY，其次回退到 OPENAI_API_KEY
    llm_api_key: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    llm_api_base: str | None = os.getenv("LLM_API_BASE")  # 可选：自定义兼容 OpenAI 的 Base URL
    llm_model: str = os.getenv("AI_TRENDS_MODEL", "gpt-4.1-mini")

    # 数据文件
    news_data_path: Path = DATA_DIR / "news.json"
    snapshots_dir: Path = DATA_DIR / "snapshots"

    # 抓取相关
    window_days: int = int(os.getenv("AI_TRENDS_WINDOW_DAYS", "2"))
    max_items: int = int(os.getenv("AI_TRENDS_MAX_ITEMS", "400"))

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

