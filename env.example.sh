#!/usr/bin/env bash
# AI Trends Hub 环境配置示例脚本
#
# 使用步骤：
#   1. 复制：cp env.example.sh env.sh
#   2. 编辑 env.sh，取消注释并填写你要用的配置块（二选一或自定义）
#   3. 加载：source env.sh
#   4. 运行：python scripts/run_fetch.py 或 python scripts/run_api.py

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

#############################
# 方式一：OpenAI 或自定义网关
#############################
# export LLM_API_KEY="你的-OpenAI-或网关-Key"
# export LLM_API_BASE="https://api.openai.com/v1"   # 可选，不设则用 OpenAI 默认
# export OPENAI_API_KEY="你的-OpenAI-Key"           # 未设 LLM_API_KEY 时回退使用
# export AI_TRENDS_MODEL="gpt-4.1-mini"

#############################
# 方式二：国产模型（选一个取消注释并填 Key）
#############################

# --- 智谱 AI ---
# export LLM_PROVIDER=zhipu
# export LLM_API_KEY="你的智谱-API-Key"
# export AI_TRENDS_MODEL="glm-4-flash"

# --- 月之暗面 Kimi ---
# export LLM_PROVIDER=moonshot
# export LLM_API_KEY="你的-Moonshot-API-Key"
# export AI_TRENDS_MODEL="moonshot-v1-8k"

# --- 通义千问 ---
# export LLM_PROVIDER=dashscope
# export LLM_API_KEY="你的-DashScope-API-Key"
# export AI_TRENDS_MODEL="qwen-plus"

# --- DeepSeek ---
# export LLM_PROVIDER=deepseek
# export LLM_API_KEY="你的-DeepSeek-API-Key"
# export AI_TRENDS_MODEL="deepseek-chat"

# --- 豆包（火山引擎）---
# export LLM_PROVIDER=doubao
# export LLM_API_KEY="你的-豆包-API-Key"
# export AI_TRENDS_MODEL="豆包模型名"

# --- MiniMax ---
# export LLM_PROVIDER=minimax
# export LLM_API_KEY="你的-MiniMax-API-Key"
# export AI_TRENDS_MODEL="abab6.5s-chat"

#############################
# 抓取与数据（可选，有默认值）
#############################
# export AI_TRENDS_WINDOW_DAYS=2    # 抓取最近几天
# export AI_TRENDS_MAX_ITEMS=400    # 单次最大条数

echo "AI Trends Hub 环境已加载 (SCRIPT_DIR=$SCRIPT_DIR)"
