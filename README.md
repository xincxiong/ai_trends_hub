## AI Trends Hub 项目说明

本项目是一个 **AI 行业趋势聚合服务**，用于自动抓取并整理全球主流网站上的：

- AI 硬件（芯片、服务器、存储、网络等）
- AI 软件（模型、框架、工具链、平台、Agent 等）
- 行业应用（医疗、金融、制造、零售、教育、自动驾驶等）
- 融资并购（融资轮次、并购交易等）
- AI 科研进展（新算法/架构、强化学习、Agent、多智能体系统、评测基准等）

当前实现为一个 **MVP 版本**，并遵循「抓取模块解耦」的设计：

- **crawler 模块**：使用 OpenAI Responses API + `web_search` 工具，负责联网抓取 + 初步清洗，返回原始 JSON 对象列表
- **pipeline 模块**：只负责结构化为 `Article`、去重合并与持久化
- **storage 模块**：本地 JSON 存储、去重与快照写入
- **api 模块**：FastAPI 接口，按模块分页查询

抓取的数据会以两种方式保存在本地：

- 聚合数据：`data/news.json`（经过合并去重后的全量视图）
- 每次抓取快照：`data/snapshots/snapshot_{start}_to_{end}.json`

支持的主模块（`main_category`）包括：

- `ai_hardware`
- `ai_software`
- `ai_application`
- `ai_funding_ma`
- `ai_research`（科研/算法/强化学习/Agent 进展）

### 目录结构

- `ai_trends/`
  - `config.py`：配置与常量（路径、时间窗口、主模块列表等）
  - `models.py`：Pydantic 数据模型（`Article`、`Evidence` 等）
  - `storage.py`：本地 JSON 存储、去重与快照写入工具
  - `crawler.py`：解耦的抓取模块（OpenAI + web_search，专注联网抓取与初步清洗）
  - `pipeline.py`：抓取 + 结构化 + 去重 + 写入 `news.json` 与快照
  - `api.py`：FastAPI 应用，提供 `/health` 与 `/articles` 接口
- `scripts/`
  - `run_fetch.py`：执行一次抓取并更新 `data/news.json`，同时写入当次快照
  - `run_api.py`：启动 FastAPI 服务
- `data/news.json`：聚合后的新闻数据（运行后自动生成）
- `data/snapshots/`：每一次抓取的结构化数据快照
- `requirements.txt`：项目依赖

### 环境要求

- Python：建议 **3.10+**
- 网络：需要能访问 OpenAI 官方或兼容 OpenAI 协议的网关

### 快速开始

1. 使用 conda 创建并激活环境（推荐）：

```bash
cd /mnt/cloud_disk/ai_trends_hub

# 创建名为 ai-trends-hub 的新环境（你也可以改成自己喜欢的名字）
conda create -n ai-trends-hub python=3.10 -y
conda activate ai-trends-hub

# 在 conda 环境中安装项目依赖
pip install -r requirements.txt
```

2. 配置环境变量（推荐使用脚本）：

```bash
cd /mnt/cloud_disk/ai_trends_hub
cp env.example.sh env.sh        # 复制示例脚本
vim env.sh                      # 或任意编辑器，填入你的 key
source env.sh                   # 在当前 shell 中加载环境变量
```

3. 执行一次抓取（会写入 `data/news.json` 与 `data/snapshots/`）：

```bash
python scripts/run_fetch.py
```

4. 启动 API 服务：

```bash
python scripts/run_api.py
```

然后访问：

- `GET /health`：健康检查，返回简单的 JSON 状态
- `GET /articles`：按时间 + 模块（硬件/软件/应用/融资/科研）分页查询  
  - 支持参数：  
    - `main_category`：`ai_hardware` / `ai_software` / `ai_application` / `ai_funding_ma` / `ai_research`  
    - `limit`：每页条数（1–100）  
    - `offset`：偏移量（分页游标）  
    - `q`：按标题 / 摘要 / 来源的简单关键字模糊搜索

