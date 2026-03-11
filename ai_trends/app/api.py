"""应用服务层：FastAPI 路由，为前端提供内容展示接口。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse, HTMLResponse

from ..config import settings
from ..models import Article, ArticleList
from ..data import load_articles

# 分类展示名称（与 main_category 对应）
CATEGORY_LABELS: dict[str, str] = {
    "ai_hardware": "AI 硬件",
    "ai_software": "AI 软件",
    "ai_application": "行业应用与落地产品",
    "ai_funding_ma": "融资并购",
    "ai_research": "科研与算法",
}

app = FastAPI(
    title="AI Trends Hub API",
    version="0.2.0",
    default_response_class=ORJSONResponse,
)


def get_articles() -> list[Article]:
    """从数据层读取聚合后的文章列表。"""
    return load_articles(settings.news_data_path)


@app.get("/", response_class=HTMLResponse, summary="前端展示页面")
def index_page() -> str:
    """前端页面：数据来源说明 + 按主类别分块展示，每类 5～10 条最新抓取的网页数据。"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>AI 趋势周报 · AI 市场前沿</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg: #0c0f14;
      --bg-elevated: #12161d;
      --card: #161b24;
      --card-hover: #1a202c;
      --border: #252d3a;
      --border-subtle: #1e2530;
      --text: #e6edf5;
      --text-secondary: #8b9cb3;
      --text-muted: #6b7c99;
      --accent: #4f7cff;
      --accent-soft: rgba(79, 124, 255, 0.15);
      --link: #6b9fff;
      --link-hover: #8bb3ff;
      --radius: 10px;
      --radius-sm: 6px;
      --shadow: 0 4px 24px rgba(0,0,0,0.35);
      --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
    }
    * { box-sizing: border-box; }
    body {
      font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
      margin: 0; padding: 0;
      background: var(--bg);
      background-image: radial-gradient(ellipse 120% 80% at 50% -20%, rgba(79, 124, 255, 0.08), transparent), radial-gradient(ellipse 60% 40% at 100% 0%, rgba(79, 124, 255, 0.04), transparent);
      color: var(--text);
      font-size: 15px;
      line-height: 1.65;
      -webkit-font-smoothing: antialiased;
    }
    .page-wrap { display: flex; min-height: 100vh; }
    .sidebar {
      width: 220px; flex-shrink: 0;
      padding: 28px 20px;
      background: var(--bg-elevated);
      border-right: 1px solid var(--border-subtle);
      position: sticky; top: 0; height: 100vh; overflow-y: auto;
    }
    .sidebar h3 {
      font-size: 11px; font-weight: 600;
      color: var(--text-muted);
      margin: 0 0 20px 0;
      letter-spacing: 0.12em; text-transform: uppercase;
    }
    .sidebar nav { display: flex; flex-direction: column; gap: 4px; }
    .sidebar nav a {
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 14px; font-weight: 500;
      padding: 10px 14px;
      border-radius: var(--radius-sm);
      transition: color 0.2s, background 0.2s;
    }
    .sidebar nav a:hover { background: var(--accent-soft); color: var(--link); }
    .main { flex: 1; padding: 0 40px 56px; max-width: 780px; }
    .site-header {
      padding: 32px 0 28px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 16px;
    }
    .site-title {
      font-size: 26px; font-weight: 700;
      margin: 0;
      color: #f0f4f9;
      letter-spacing: -0.03em;
    }
    .site-subtitle { font-size: 14px; color: var(--text-muted); margin: 6px 0 0 0; font-weight: 500; }
    .site-date {
      font-size: 13px; font-weight: 500;
      color: var(--text-muted);
      padding: 6px 12px;
      background: var(--card);
      border: 1px solid var(--border-subtle);
      border-radius: 20px;
    }
    .toolbar { display: flex; align-items: center; gap: 14px; margin: 20px 0 28px 0; }
    .toolbar button {
      padding: 10px 20px;
      border-radius: var(--radius-sm);
      border: none;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font-size: 14px; font-weight: 600;
      font-family: inherit;
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .toolbar button:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(79, 124, 255, 0.4); }
    .toolbar button:active { transform: translateY(0); }
    #status { font-size: 13px; color: var(--text-muted); }
    .key-conclusions {
      margin-bottom: 36px;
      scroll-margin-top: 28px;
      padding: 24px 26px;
      background: var(--card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
    }
    .key-conclusions h2 {
      font-size: 16px; font-weight: 600;
      margin: 0 0 18px 0;
      color: var(--text);
      letter-spacing: -0.01em;
    }
    .conclusion-list { list-style: none; padding: 0; margin: 0; }
    .conclusion-list li {
      padding: 12px 0;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 14px; line-height: 1.55;
      transition: background 0.15s;
    }
    .conclusion-list li:last-child { border-bottom: none; }
    .conclusion-list li:hover { background: rgba(255,255,255,0.02); margin: 0 -12px; padding-left: 12px; padding-right: 12px; border-radius: var(--radius-sm); }
    .conclusion-list .item-date { color: var(--text-muted); font-size: 12px; margin-right: 12px; font-variant-numeric: tabular-nums; }
    .conclusion-list a { color: var(--link); text-decoration: none; font-weight: 500; transition: color 0.15s; }
    .conclusion-list a:hover { color: var(--link-hover); }
    .conclusion-list .item-source { color: var(--text-muted); font-size: 12px; margin-left: 10px; }
    .section-brief {
      margin-bottom: 44px;
      scroll-margin-top: 28px;
      padding: 26px 28px;
      background: var(--card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius);
      box-shadow: var(--shadow-sm);
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .section-brief:hover { border-color: var(--border); box-shadow: var(--shadow); }
    .section-brief h2 {
      font-size: 17px; font-weight: 600;
      margin: 0 0 6px 0;
      color: var(--text);
      letter-spacing: -0.02em;
    }
    .brief-meta { font-size: 12px; color: var(--text-muted); margin-bottom: 18px; }
    .category-summary {
      margin-bottom: 18px;
      padding: 16px 18px;
      background: var(--bg-elevated);
      border-radius: var(--radius-sm);
      border-left: 3px solid var(--accent);
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.6;
    }
    .category-summary.loading { font-style: italic; opacity: 0.85; }
    .category-summary.empty { display: none; }
    .brief-list { list-style: none; padding: 0; margin: 0; }
    .brief-list li {
      padding: 14px 0;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 14px;
      transition: background 0.15s;
    }
    .brief-list li:last-child { border-bottom: none; }
    .brief-list li:hover { background: rgba(255,255,255,0.02); margin: 0 -10px; padding: 14px 10px; border-radius: var(--radius-sm); }
    .brief-list .item-head { margin-bottom: 6px; }
    .brief-list .item-date { color: var(--text-muted); font-size: 12px; margin-right: 10px; font-variant-numeric: tabular-nums; }
    .brief-list a { color: var(--link); text-decoration: none; font-weight: 500; transition: color 0.15s; }
    .brief-list a:hover { color: var(--link-hover); }
    .brief-list .item-desc { color: var(--text-secondary); font-size: 13px; line-height: 1.55; margin-top: 8px; }
    .site-footer {
      margin-top: 52px;
      padding-top: 24px;
      border-top: 1px solid var(--border-subtle);
      font-size: 13px;
      color: var(--text-muted);
    }
  </style>
</head>
<body>
  <div class="page-wrap">
    <aside class="sidebar" aria-label="目录">
      <h3>目录</h3>
      <nav>
        <a href="#block-overview">重点关注结论</a>
        <a href="#block-ai_hardware">AI 硬件</a>
        <a href="#block-ai_software">AI 软件</a>
        <a href="#block-ai_application">行业应用与落地产品</a>
        <a href="#block-ai_funding_ma">融资并购</a>
        <a href="#block-ai_research">科研与算法</a>
      </nav>
    </aside>
    <main class="main">
      <header class="site-header">
        <div>
          <h1 class="site-title">AI 趋势周报</h1>
          <p class="site-subtitle">AI 市场前沿</p>
        </div>
        <span class="site-date" id="siteDate">—</span>
      </header>
      <div class="toolbar">
        <button id="reloadBtn">刷新</button>
        <span id="status"></span>
      </div>
      <section class="key-conclusions" id="block-overview" aria-label="重点关注结论">
        <h2>重点关注结论</h2>
        <ul class="conclusion-list" id="overviewList"></ul>
      </section>
      <div id="byCategory"></div>
      <footer class="site-footer">© AI Trends Hub · 数据来自全球主流媒体与学术站点聚合</footer>
    </main>
  </div>

  <script>
    const CATEGORIES = [
      { id: "ai_hardware", label: "AI 硬件" },
      { id: "ai_software", label: "AI 软件" },
      { id: "ai_application", label: "行业应用与落地产品" },
      { id: "ai_funding_ma", label: "融资并购" },
      { id: "ai_research", label: "科研与算法" },
    ];
    const PER_CATEGORY = 10;
    const FETCH_LIMIT = 2000;
    const OVERVIEW_MAX = 8;
    const WEEK_DAYS = 7;

    function getWeekRangeFromEnd(endDateStr) {
      if (!endDateStr || !/^\\d{4}-\\d{2}-\\d{2}$/.test(endDateStr)) return null;
      var end = new Date(endDateStr + "T12:00:00Z");
      var start = new Date(end);
      start.setUTCDate(start.getUTCDate() - (WEEK_DAYS - 1));
      function toYMD(d) { return d.toISOString().slice(0, 10); }
      return { start: toYMD(start), end: toYMD(end) };
    }

    function filterItemsInWeek(items, weekRange) {
      if (!weekRange) return items;
      return items.filter(function(a) {
        var d = (a.date || "").trim();
        return d >= weekRange.start && d <= weekRange.end;
      });
    }

    function escapeHtml(s) {
      return (s || "").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function renderDailyOverview(items) {
      const listEl = document.getElementById("overviewList");
      if (!listEl) return;
      if (!items.length) { listEl.innerHTML = ""; return; }
      let html = "";
      for (const a of items) {
        const date = escapeHtml(a.date || "");
        const title = escapeHtml(a.title || "");
        const url = (typeof a.url === "string" ? a.url : (a.url && a.url.url) || "#");
        const source = escapeHtml(a.source || "");
        html += '<li><span class="item-date">' + date + '</span><a href="' + url + '" target="_blank" rel="noopener noreferrer">' + title + '</a><span class="item-source">' + source + '</span></li>';
      }
      listEl.innerHTML = html;
    }

    function renderCategory(categoryId, label, items, dateRange) {
      if (!items.length) return "";
      var startEnd = dateRange && dateRange.start && dateRange.end ? (dateRange.start + " 至 " + dateRange.end) : "";
      var meta = startEnd ? "时间：" + startEnd + "｜来源：聚合数据" : "来源：聚合数据";
      var html = '<section class="section-brief" id="block-' + categoryId + '"><h2>' + escapeHtml(label) + '</h2>';
      html += '<p class="brief-meta">' + meta + '</p>';
      html += '<div class="category-summary loading" id="summary-' + categoryId + '" data-category="' + categoryId + '">概要生成中…</div>';
      html += '<ul class="brief-list">';
      for (const a of items) {
        const date = escapeHtml(a.date || "");
        const title = escapeHtml(a.title || "");
        const summary = escapeHtml(a.summary || "");
        const url = (typeof a.url === "string" ? a.url : (a.url && a.url.url) || "#");
        html += '<li><div class="item-head"><span class="item-date">' + date + '：</span><a href="' + url + '" target="_blank" rel="noopener noreferrer">' + title + '</a></div>';
        if (summary) html += '<div class="item-desc">' + summary + '</div>';
        html += '</li>';
      }
      html += '</ul></section>';
      return html;
    }

    async function loadArticles() {
      const container = document.getElementById("byCategory");
      const statusEl = document.getElementById("status");
      statusEl.textContent = "加载中…";
      container.innerHTML = "";
      try {
        const resp = await fetch("/articles?limit=" + FETCH_LIMIT + "&offset=0");
        if (!resp.ok) throw new Error("HTTP " + resp.status + " " + (await resp.text()));
        const data = await resp.json();
        const items = Array.isArray(data.items) ? data.items : [];
        var sortedByDate = items.slice().sort((x, y) => (y.date || "").localeCompare(x.date || ""));
        var latestDate = sortedByDate.length ? (sortedByDate[0].date || "").trim() : "";
        var weekRange = getWeekRangeFromEnd(latestDate);
        var weekItems = weekRange ? filterItemsInWeek(items, weekRange) : items;
        var dateRange = weekRange || { start: "", end: "" };
        var dailyItems = latestDate ? weekItems.filter(function(a) { return (a.date || "").trim() === latestDate; }) : [];
        dailyItems = dailyItems.slice(0, OVERVIEW_MAX);
        renderDailyOverview(dailyItems);
        var dateEl = document.getElementById("siteDate");
        if (dateEl) dateEl.textContent = latestDate || new Date().toISOString().slice(0, 10);
        const byCat = {};
        for (const c of CATEGORIES) byCat[c.id] = [];
        for (const a of weekItems) {
          const mc = (a.main_category || "").toLowerCase().trim();
          if (byCat[mc]) byCat[mc].push(a);
        }
        for (const c of CATEGORIES) {
          const list = (byCat[c.id] || []).sort((x, y) => (y.date || "").localeCompare(x.date || "")).slice(0, PER_CATEGORY);
          container.insertAdjacentHTML("beforeend", renderCategory(c.id, c.label, list, dateRange));
        }
        statusEl.textContent = "共 " + weekItems.length + " 条（近" + WEEK_DAYS + "日），每类最多 " + PER_CATEGORY + " 条";
        fillCategorySummaries(dateRange.end, WEEK_DAYS);
      } catch (e) {
        console.error(e);
        statusEl.textContent = "加载失败：" + (e.message || "请检查后端服务。");
      }
    }
    async function fillCategorySummaries(weekEnd, days) {
      for (const c of CATEGORIES) {
        const el = document.getElementById("summary-" + c.id);
        if (!el) continue;
        try {
          var query = "main_category=" + encodeURIComponent(c.id);
          if (weekEnd && days) query += "&end_date=" + encodeURIComponent(weekEnd) + "&days=" + days;
          const resp = await fetch("/category-summary?" + query);
          if (!resp.ok) { el.textContent = ""; el.classList.add("empty"); continue; }
          const data = await resp.json();
          const text = data.summary && data.summary.trim();
          if (text) {
            el.textContent = text;
            el.classList.remove("loading", "empty");
          } else {
            el.textContent = "";
            el.classList.add("empty");
          }
        } catch (e) {
          el.textContent = "";
          el.classList.add("empty");
        }
      }
    }

    document.getElementById("reloadBtn").addEventListener("click", loadArticles);
    loadArticles();
  </script>
</body>
</html>
    """.strip()


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
    limit: int = Query(20, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="按标题/摘要/来源模糊搜索"),
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


def _summarize_category_with_llm(main_category: str, articles: list[Article]) -> Optional[str]:
    """用大模型对指定分类下的新闻生成 2～3 句话概要。无 Key 或调用失败时返回 None。"""
    if not articles:
        return None
    label = CATEGORY_LABELS.get(main_category, main_category)
    # 最多取 12 条，避免 prompt 过长
    subset = articles[:12]
    lines = []
    for a in subset:
        title = (a.title or "").strip()
        summary = (a.summary or "").strip()
        if len(summary) > 200:
            summary = summary[:200] + "…"
        if title or summary:
            lines.append(f"· {title}\n  {summary}")
    if not lines:
        return None
    prompt = (
        "你是一名 AI 行业编辑。以下是一组【" + label + "】类别的新闻标题与摘要。"
        "请用 2～3 句话概括这些新闻的要点与趋势，不要列举具体标题，只输出概括性中文概要。\n\n"
        + "\n\n".join(lines)
    )
    try:
        from ..model import get_llm_client
        client = get_llm_client()
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
        )
        content = (resp.choices[0].message.content or "").strip()
        return content if content else None
    except Exception:
        return None


def _filter_articles_by_week(articles: list[Article], end_date: str, days: int) -> list[Article]:
    """保留 date 在 [end_date - (days-1), end_date] 内的文章。end_date 为 YYYY-MM-DD。"""
    if not end_date or days <= 0:
        return articles
    from datetime import datetime, timedelta
    try:
        end_d = datetime.strptime(end_date.strip()[:10], "%Y-%m-%d").date()
        start_d = end_d - timedelta(days=days - 1)
        start_s, end_s = start_d.isoformat(), end_d.isoformat()
        return [a for a in articles if (a.date or "").strip() >= start_s and (a.date or "").strip() <= end_s]
    except Exception:
        return articles


@app.get(
    "/category-summary",
    summary="获取指定分类的大模型汇总概要",
)
def get_category_summary(
    main_category: str = Query(..., description="主类别 ID"),
    end_date: Optional[str] = Query(None, description="周 end 日期 YYYY-MM-DD，与 days 同时传时仅汇总该周"),
    days: int = Query(7, ge=1, le=31, description="与 end_date 联用，表示从 end_date 往前 days 天"),
    articles: list[Article] = Depends(get_articles),
) -> dict:
    """根据当前数据用大模型生成该分类的 2～3 句话概要。可传 end_date+days 限定为近一周。"""
    mc = main_category.strip().lower()
    if mc not in settings.main_categories:
        raise HTTPException(status_code=400, detail="无效的 main_category")
    filtered = [a for a in articles if (a.main_category or "").lower() == mc]
    if end_date:
        filtered = _filter_articles_by_week(filtered, end_date, days)
    summary = _summarize_category_with_llm(mc, filtered)
    return {"main_category": mc, "summary": summary}
