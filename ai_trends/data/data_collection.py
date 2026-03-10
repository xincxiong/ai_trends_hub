# -*- coding: utf-8 -*-
"""
数据收集入口：对接项目架构，支持两阶段抓取（URL 召回 + 联网核验）与增量写入。

- Stage A：多轮检索召回候选 URL（降低“编新闻”风险）
- Stage B：逐条联网核验并从原文抽取字段（真实/一致才入库）
- 配置来自 ai_trends.config.settings 与环境变量（见 env.example.sh）
- 通过 ai_trends.data.pipeline.run_pipeline() 执行完整流水线
"""
from __future__ import annotations

from .pipeline import run_pipeline, fetch_latest_articles, fetch_latest_articles_two_stage


def fetch_daily_news() -> list:
    """
    执行一次完整数据收集并写入聚合文件。

    - 若配置 two_stage_fetch=True（默认），使用两阶段抓取（召回 + 核验）
    - 否则使用单阶段抓取（单次大 prompt）
    - 路径与条数等由 ai_trends.config.settings 及环境变量控制
    """
    return run_pipeline()


__all__ = [
    "fetch_daily_news",
    "fetch_latest_articles",
    "fetch_latest_articles_two_stage",
    "run_pipeline",
]
