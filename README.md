## AI Trends Hub 项目说明

本项目是一个 **AI 行业趋势聚合服务**，自动抓取并整理全球主流网站上的 AI 硬件、软件、行业应用、融资并购及科研进展，并按模块展示。

项目采用 **三层架构**：

| 层级 | 职责 |
|------|------|
| **数据管理模块**（`ai_trends/data`） | 数据抓取、清洗、保存（含去重与快照）；支持两阶段抓取（URL 召回 + 联网核验） |
| **模型调用中间层**（`ai_trends/model`） | 大模型 API 接入、管理、调度 |
| **应用服务层**（`ai_trends/app`） | 前端内容展示、REST API 暴露 |

### 目录结构

```
ai_trends_hub/
├── ai_trends/
│   ├── config.py          # 全局配置（路径、时间窗口、两阶段/单阶段、LLM 配置等）
│   ├── models.py          # 共用数据模型（Article、Evidence、Metrics 等）
│   ├── data/              # 数据管理模块
│   │   ├── crawler.py     # 单阶段抓取（通过 model 层调用 LLM + web_search）
│   │   ├── recall.py      # 两阶段 Stage A：多轮检索召回候选 URL
│   │   ├── verify.py      # 两阶段 Stage B：联网核验并抽取结构化字段
│   │   ├── cleaner.py     # 清洗：原始/核验结果 → Article（含标题翻译、segment→main_category）
│   │   ├── storage.py     # 存储、去重、快照、备份、按日期保留
│   │   ├── pipeline.py    # 编排：抓取（单阶段或两阶段）→ 清洗 → 保存
│   │   ├── data_collection.py  # 数据收集入口（fetch_daily_news / run_pipeline）
│   │   ├── domains.py     # 域名白名单与渠道关键词
│   │   ├── url_utils.py   # URL/标题规范化、域名校验
│   │   └── llm_helpers.py # 数据层 LLM 调用封装（JSON 数组解析）
│   ├── model/             # 模型调用中间层
│   │   └── client.py      # LLM 客户端封装（API 接入与调度）
│   └── app/               # 应用服务层
│       └── api.py         # FastAPI 应用，/health、/articles
├── scripts/
│   ├── run_fetch.py       # 执行一次抓取并更新 data/news.json 与快照
│   └── run_api.py        # 启动 API 服务
├── data/
│   ├── news.json         # 聚合后的新闻数据（运行后生成）
│   └── snapshots/        # 每次抓取的结构化快照
├── env.example.sh        # 环境配置示例（复制为 env.sh 后编辑并 source 加载）
├── requirements.txt
└── README.md
```

### 数据流与依赖关系

- **应用服务层** 仅依赖 **数据管理模块** 的读接口（如 `load_articles`）和配置，用于展示与分页查询。
- **数据管理模块** 的抓取依赖 **模型中间层** 的 `call_responses`；清洗与存储不依赖模型。
- **模型中间层** 仅依赖 `config`，负责统一的大模型 API 接入与调用。

**抓取模式**（由 `AI_TRENDS_TWO_STAGE` 控制，默认 `true`）：
- **两阶段**：Stage A 多轮检索召回候选 URL → Stage B 逐条联网核验并抽取字段 → 清洗、去重、标题翻译 → 合并写入。适合需要“真实来源+证据”的 AI/GPU 情报。
- **单阶段**：单次大 prompt 召回并输出结构化条目 → 清洗 → 合并写入。

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

2. 配置环境变量（大模型 API）

**推荐：使用 `env.example.sh` 统一配置**

项目根目录下的 `env.example.sh` 已集中所有环境变量，按下列方式执行即可：

```bash
cd /mnt/cloud_disk/ai_trends_hub

# 1）复制为本地配置（不要提交 env.sh）
cp env.example.sh env.sh

# 2）编辑 env.sh：取消注释你要用的配置块（OpenAI 或某一国产模型），并填入真实 API Key 与模型名
vim env.sh   # 或 nano / 其他编辑器

# 3）在当前 shell 中加载环境（每次新开终端需重新执行）
source env.sh

# 4）之后可直接运行抓取或 API
python scripts/run_fetch.py
python scripts/run_api.py
```

说明：

- 脚本内已包含「方式一：OpenAI / 自定义网关」和「方式二：国产模型（智谱、月之暗面、通义、DeepSeek、豆包、MiniMax）」等示例，只需取消对应注释并填写 Key。
- 必须使用 `source env.sh` 加载，不能 `bash env.sh`，否则变量不会传入当前 shell。
- 若需临时生效，可在一行内完成：`source env.sh && python scripts/run_fetch.py`。

**手动配置**（不用脚本时）可设以下变量：

- `LLM_API_KEY` 或 `OPENAI_API_KEY`：API 密钥  
- `LLM_API_BASE`（可选）：自定义 Base URL  
- `AI_TRENDS_MODEL`（可选）：模型名，默认如 `gpt-4.1-mini`  
- `LLM_PROVIDER`（可选）：国产模型接入时使用，见下方

```bash
export LLM_API_KEY="your-api-key"
# export LLM_API_BASE="https://your-gateway/v1"  # 可选
```

**国产模型 API 接入**：设置 `LLM_PROVIDER` 后会自动使用对应厂商的 OpenAI 兼容 Base URL，无需再配 `LLM_API_BASE`。支持的厂商见下表。

### 大模型 API 接口支持情况

本项目在模型层会**识别当前是否支持 OpenAI Responses API**，并据此选择调用方式：

| 接入方式 | 识别条件 | Responses API | 说明 |
|----------|----------|----------------|------|
| **OpenAI 官方** | 未设置 `LLM_PROVIDER` 且未设置 `LLM_API_BASE`（或指向 OpenAI） | ✅ 支持 | 可使用 `/responses` 及 `web_search` 联网搜索，抓取为实时网页内容。 |
| **自定义网关** | 仅设置 `LLM_API_BASE` | ⚠️ 尝试 | 先请求 Responses API，若 404 则自动降级为 Chat Completions。 |
| **国产模型** | `LLM_PROVIDER` 为下表任一国产厂商 | ❌ 不支持 | 仅支持 Chat Completions，无联网搜索，结果基于模型知识。 |

国产厂商与 Responses API 支持关系：

| `LLM_PROVIDER` | 说明 | Responses API |
|----------------|------|----------------|
| `zhipu` | 智谱 AI | ❌ 仅 Chat Completions |
| `moonshot` | 月之暗面 Kimi | ❌ 仅 Chat Completions |
| `dashscope` / `qwen` | 通义千问 | ❌ 仅 Chat Completions |
| `doubao` | 豆包（火山引擎） | ❌ 仅 Chat Completions |
| `deepseek` | DeepSeek | ❌ 仅 Chat Completions |
| `minimax` | MiniMax | ❌ 仅 Chat Completions |

运行抓取时，程序会在 stderr 输出当前接入类型及支持情况（如「当前接入 [zhipu]：仅支持 Chat Completions，无联网搜索，结果基于模型知识。」）。代码中可通过 `ai_trends.model.supports_responses_api()` 与 `ai_trends.model.get_api_support_info()` 获取当前配置的支持情况。

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
