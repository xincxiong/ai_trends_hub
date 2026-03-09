#!/usr/bin/env bash

# AI Trends Hub 环境变量示例脚本
# 使用方法：
#   1. 复制本文件为 env.sh：cp env.example.sh env.sh
#   2. 编辑 env.sh，填入你自己的 key 和网关
#   3. 在当前 shell 中执行：source env.sh

#############################
# 大模型与网关配置
#############################

# 优先推荐统一使用 LLM_* 前缀
export LLM_API_KEY="你的 LLM key"                 # 优先读取的 API key
export LLM_API_BASE="https://api.openai.com/v1"   # 可选：自定义兼容 OpenAI 协议的网关

# 兼容旧配置：若未设置 LLM_API_KEY，会回退到 OPENAI_API_KEY
export OPENAI_API_KEY="你的 OpenAI key"

#############################
# 模型与抓取窗口配置
#############################

# Responses API 使用的模型名称
export AI_TRENDS_MODEL="gpt-4.1-mini"

# 抓取时间窗口与条数（可选）
export AI_TRENDS_WINDOW_DAYS=2         # 抓取最近 X 天
export AI_TRENDS_MAX_ITEMS=400         # 单次抓取最大条数

