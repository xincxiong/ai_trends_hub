from __future__ import annotations

import sys
from pathlib import Path

# 保证项目根在 path 中，便于直接运行 python scripts/run_fetch.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ai_trends.data import run_pipeline


def main() -> None:
    articles = run_pipeline()
    print(f"Fetched and merged {len(articles)} articles.")


if __name__ == "__main__":
    main()

