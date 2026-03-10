## AI Trends Hub 项目说明

本项目是一个 **AI 行业趋势聚合服务**，自动抓取并整理全球主流网站上的 AI 硬件、软件、行业应用、融资并购及科研进展，并按模块展示。

项目采用 **三层架构**：

| 层级 | 职责 |
|------|------|
| **数据管理模块**（`ai_trends/data`） | 数据抓取、清洗、保存（含去重与快照） |
| **模型调用中间层**（`ai_trends/model`） | 大模型 API 接入、管理、调度 |
| **应用服务层**（`ai_trends/app`） | 前端内容展示、REST API 暴露 |

### 目录结构

```
ai_trends_hub/
├── ai_trends/
│   ├── config.py          # 全局配置（路径、时间窗口、主模块、LLM 配置等）
│   ├── models.py          # 共用数据模型（Article、Evidence、Metrics 等）
│   ├── data/              # 数据管理模块
│   │   ├── crawler.py     # 抓取（通过 model 层调用 LLM + web_search）
│   │   ├── cleaner.py     # 清洗：原始条目 → Article
│   │   ├── storage.py     # 存储、去重、快照
│   │   └── pipeline.py    # 编排：抓取 → 清洗 → 保存
│   ├── model/             # 模型调用中间层
│   │   └── client.py      # LLM 客户端封装（API 接入与调度）
│   └── app/               # 应用服务层
│       └── api.py        # FastAPI 应用，/health、/articles
├── scripts/
│   ├── run_fetch.py       # 执行一次抓取并更新 data/news.json 与快照
│   └── run_api.py        # 启动 API 服务
├── data/
│   ├── news.json         # 聚合后的新闻数据（运行后生成）
│   └── snapshots/        # 每次抓取的结构化快照
├── requirements.txt
└── README.md
```

### 数据流与依赖关系

- **应用服务层** 仅依赖 **数据管理模块** 的读接口（如 `load_articles`）和配置，用于展示与分页查询。
- **数据管理模块** 的抓取依赖 **模型中间层** 的 `call_responses`；清洗与存储不依赖模型。
- **模型中间层** 仅依赖 `config`，负责统一的大模型 API 接入与调用。

抓取结果以两种方式落盘：

- **聚合数据**：`data/news.json`（合并去重后的全量）
- **每次快照**：`data/snapshots/snapshot_{start}_to_{end}.json`

支持的主模块（`main_category`）：`ai_hardware`、`ai_software`、`ai_application`、`ai_funding_ma`、`ai_research`。

### 环境要求

- Python：建议 **3.10+**
- 网络：可访问 OpenAI 或兼容 OpenAI 协议的网关

### 快速开始

1. 创建环境并安装依赖：

```bash
cd /mnt/cloud_disk/ai_trends_hub
conda create -n ai-trends-hub python=3.10 -y
conda activate ai-trends-hub
pip install -r requirements.txt
```

2. 配置环境变量（大模型 API）：

- `LLM_API_KEY` 或 `OPENAI_API_KEY`：API 密钥  
- `LLM_API_BASE`（可选）：自定义 Base URL  
- `AI_TRENDS_MODEL`（可选）：模型名，默认如 `gpt-4.1-mini`  
- `LLM_PROVIDER`（可选）：国产模型接入时使用，见下方

```bash
export LLM_API_KEY="your-api-key"
# export LLM_API_BASE="https://your-gateway/v1"  # 可选
```

**国产模型 API 接入**：设置 `LLM_PROVIDER` 后会自动使用对应厂商的 OpenAI 兼容 Base URL，无需再配 `LLM_API_BASE`。支持的厂商：

| `LLM_PROVIDER` | 说明 |
|----------------|------|
| `zhipu` | 智谱 AI |
| `moonshot` | 月之暗面 Kimi |
| `dashscope` / `qwen` | 通义千问 |
| `doubao` | 豆包（火山引擎） |
| `deepseek` | DeepSeek |
| `minimax` | MiniMax |

示例（智谱）：

```bash
export LLM_PROVIDER=zhipu
export LLM_API_KEY="你的智谱 API Key"
export AI_TRENDS_MODEL="glm-4-flash"   # 或 glm-4、glm-4-long 等
```

示例（月之暗面）：

```bash
export LLM_PROVIDER=moonshot
export LLM_API_KEY="你的 Moonshot API Key"
export AI_TRENDS_MODEL="moonshot-v1-8k"
```

若厂商仅支持 Chat Completions 而不支持 Responses API（如 `web_search`），需使用支持该能力的网关或 OpenAI 官方接口进行抓取。

3. 执行一次抓取（更新 `data/news.json` 与快照）：

```bash
python scripts/run_fetch.py
```

4. 启动 API 服务：

```bash
python scripts/run_api.py
```

- `GET /health`：健康检查  
- `GET /articles`：按模块分页查询  
  - `main_category`：`ai_hardware` / `ai_software` / `ai_application` / `ai_funding_ma` / `ai_research`  
  - `limit`、`offset`：分页  
  - `q`：标题/摘要/来源关键字模糊搜索  
