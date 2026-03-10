from __future__ import annotations

import sys
from pathlib import Path

# 保证项目根在 path 中，便于直接运行 python scripts/run_fetch.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ai_trends.data import run_pipeline
from ai_trends.model import get_api_support_info


def main() -> None:
    info = get_api_support_info()
    if info["supports_responses_api"]:
        print("模式: Responses API（联网检索），可进行两阶段抓取。", file=sys.stderr)
    else:
        print("模式: Chat Completions（基于模型知识），单阶段抓取。", file=sys.stderr)

    articles = run_pipeline()
    print(f"Fetched and merged {len(articles)} articles.")


if __name__ == "__main__":
    main()

