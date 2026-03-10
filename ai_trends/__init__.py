"""
AI Trends Hub 核心包。

三层架构：
- 数据管理模块（data）：抓取、清洗、保存
- 模型调用中间层（model）：大模型 API 接入与管理调度
- 应用服务层（app）：前端内容展示、API 暴露
"""

from . import model, data, app
from .config import settings
from .models import Article, ArticleList

__all__ = ["data", "model", "app", "settings", "Article", "ArticleList"]
