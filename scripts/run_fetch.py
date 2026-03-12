from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

# 保证项目根在 path 中，便于直接运行 python scripts/run_fetch.py
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ai_trends.data import run_pipeline
from ai_trends.data.fetch_status import get_status

STATUS_INTERVAL = 10  # 秒


def _truncate(s: str, max_len: int = 120) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _print_status_loop() -> None:
    while True:
        time.sleep(STATUS_INTERVAL)
        s = get_status()
        phase = s.get("phase", "idle")
        site = s.get("current_site", "") or "(无)"
        url = _truncate(s.get("current_url") or "", 120)
        content = _truncate(s.get("current_content") or "", 200)
        calls = s.get("api_calls", 0)
        print("[状态] 阶段=%s | 当前抓取=%s | API 调用次数=%s" % (phase, site, calls), flush=True)
        if url:
            print("  当前地址: %s" % url, flush=True)
        if content:
            print("  抓取内容: %s" % content, flush=True)


def main() -> None:
    t = threading.Thread(target=_print_status_loop, daemon=True)
    t.start()
    articles = run_pipeline()
    print(f"Fetched and merged {len(articles)} articles.", flush=True)


if __name__ == "__main__":
    main()

