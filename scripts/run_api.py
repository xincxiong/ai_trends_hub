from __future__ import annotations

import sys
from pathlib import Path

# 保证项目根在 path 中，便于直接运行 python scripts/run_api.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import uvicorn


def main() -> None:
    uvicorn.run(
        "ai_trends.app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()

