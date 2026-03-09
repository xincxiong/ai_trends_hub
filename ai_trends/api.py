from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse

from .config import settings
from .models import Article, ArticleList
from .storage import load_articles

app = FastAPI(
    title="AI Trends Hub API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
)


def get_articles() -> list[Article]:
    return load_articles(settings.news_data_path)


@app.get("/health", summary="健康检查")
def health() -> dict:
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.get(
    "/articles",
    response_model=ArticleList,
    summary="按模块分页获取文章列表",
)
def list_articles(
    main_category: Optional[str] = Query(
        None,
        description="主类别：ai_hardware / ai_software / ai_application / ai_funding_ma / ai_research",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="按标题/摘要/来源模糊搜索关键字（简单包含匹配）"),
    articles: list[Article] = Depends(get_articles),
) -> ArticleList:
    data = articles

    if main_category:
        mc = main_category.strip().lower()
        if mc not in settings.main_categories:
            raise HTTPException(status_code=400, detail="无效的 main_category")
        data = [a for a in data if (a.main_category or "").lower() == mc]

    if q:
        q_lower = q.strip().lower()
        data = [
            a
            for a in data
            if q_lower in a.title.lower()
            or q_lower in a.summary.lower()
            or q_lower in (a.source or "").lower()
        ]

    total = len(data)
    page = data[offset : offset + limit]
    return ArticleList(total=total, items=page)

