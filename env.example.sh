#!/usr/bin/env bash
# AI Trends Hub 环境配置示例
#
# 使用步骤：
#   1. 复制：cp env.example.sh env.sh
#   2. 编辑 env.sh，取消注释并填写你要用的配置块（方式一 或 方式二 选一）
#   3. 加载：source env.sh   （必须用 source，不要用 bash env.sh）
#   4. 运行：python scripts/run_fetch.py  或  python scripts/run_api.py
#
# 接口支持：方式一（OpenAI/自定义网关）支持 Responses API（含 web_search 联网搜索）；
#          方式二（国产模型）仅支持 Chat Completions，无联网搜索，结果基于模型知识。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:$PYTHONPATH}"

#############################
# 方式一：OpenAI 或自定义网关（支持 Responses API / web_search）
#############################
# export LLM_API_KEY="你的-OpenAI-或网关-Key"
# export LLM_API_BASE="https://api.openai.com/v1"   # 可选，不设则用 OpenAI 默认
# export OPENAI_API_KEY="你的-OpenAI-Key"           # 未设 LLM_API_KEY 时回退使用
# export AI_TRENDS_MODEL="gpt-4.1-mini"

#############################
# 方式二：国产模型（仅 Chat Completions，无联网搜索）
# 设置 LLM_PROVIDER 后会自动使用内置 Base URL，一般无需设 LLM_API_BASE。
# 仅在使用代理、私有化部署或厂商更换域名时，可取消下面 LLM_API_BASE 注释并填写。
#############################

# --- 智谱 AI ---
# export LLM_PROVIDER=zhipu
# export LLM_API_KEY="你的智谱-API-Key"
# export AI_TRENDS_MODEL="glm-4-flash"
# export LLM_API_BASE="https://open.bigmodel.cn/api/paas/v4/"   # 可选，不设则用内置默认

# --- 月之暗面 Kimi ---
# export LLM_PROVIDER=moonshot
# export LLM_API_KEY="你的-Moonshot-API-Key"
# export AI_TRENDS_MODEL="moonshot-v1-8k"
# export LLM_API_BASE="https://api.moonshot.cn/v1"   # 可选，不设则用内置默认

# --- 通义千问 ---
# export LLM_PROVIDER=dashscope
# export LLM_API_KEY="你的-DashScope-API-Key"
# export AI_TRENDS_MODEL="qwen-plus"
# export LLM_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"   # 可选，不设则用内置默认

# --- DeepSeek ---
# export LLM_PROVIDER=deepseek
# export LLM_API_KEY="你的-DeepSeek-API-Key"
# export AI_TRENDS_MODEL="deepseek-chat"
# export LLM_API_BASE="https://api.deepseek.com/v1"   # 可选，不设则用内置默认

# --- 豆包（火山引擎）---
# export LLM_PROVIDER=doubao
# export LLM_API_KEY="你的-豆包-API-Key"
# export AI_TRENDS_MODEL="豆包模型名"
# export LLM_API_BASE="https://ark.cn-beijing.volces.com/api/v3"   # 可选，区域可调，不设则用内置默认

# --- MiniMax ---
# export LLM_PROVIDER=minimax
# export LLM_API_KEY="你的-MiniMax-API-Key"
# export AI_TRENDS_MODEL="abab6.5s-chat"
# export LLM_API_BASE="https://api.minimax.chat/v1"   # 可选，不设则用内置默认

#############################
# 抓取与数据（可选，有默认值）
#############################
# 时间窗口与条数
# export AI_TRENDS_WINDOW_DAYS=2      # 抓取最近几天
# export AI_TRENDS_MAX_ITEMS=400      # 单次最大条数
# export AI_TRENDS_REPORT_TZ=Asia/Shanghai   # 时间窗口时区

# 抓取模式
# export AI_TRENDS_TWO_STAGE=true    # true=两阶段(召回+核验)，false=单阶段

# 本地参考样本（用于去重与召回引导）
# export AI_TRENDS_LOCAL_REF_PATH=    # 本地参考样本 JSON 路径（例如 /path/to/local_news.json）
# export AI_TRENDS_LOCAL_SAMPLE_SIZE=120  # 使用最近 N 条作为去重/召回参考

# 输出控制
# export AI_TRENDS_INCLUDE_EXISTING=true  # true=输出包含已存在并标记，false=仅输出新增

# Stage A 召回（两阶段模式）
# export AI_TRENDS_STAGE_A_PASSES=16          # 检索轮数
# export AI_TRENDS_STAGE_A_MAX_URLS=420       # 去重后的 URL 上限
# export AI_TRENDS_STAGE_A_PER_PASS_LIMIT=26  # 每轮最多召回 URL 数

# Stage B 核验（两阶段模式）
# export AI_TRENDS_VERIFY_BATCH_SIZE=10       # 每批核验的 URL 数
# export AI_TRENDS_VERIFY_MIN_CONFIDENCE=0.74  # 置信度阈值（0~1）
# export AI_TRENDS_VERIFY_REQUIRE_DATE=true   # true=必须核验出日期
# export AI_TRENDS_STRICT_DOMAIN_AFTER_VERIFY=false  # 核验后是否严格域名白名单

# 存储与增量
# export AI_TRENDS_NEWS_BACKUP_BEFORE_MERGE=true  # 合并前是否备份 news.json
# export AI_TRENDS_NEWS_KEEP_DAYS=30   # 聚合文件保留最近 N 天

echo "AI Trends Hub 环境已加载 (SCRIPT_DIR=$SCRIPT_DIR)"
