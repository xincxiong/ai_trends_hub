# -*- coding: utf-8 -*-
"""抓取过程状态：供 run_fetch 定时打印模型 API 调用与当前抓取来源。"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict

_lock = threading.Lock()
_state: Dict[str, Any] = {
    "phase": "idle",
    "current_site": "",
    "current_url": "",
    "current_content": "",
    "api_calls": 0,
    "last_updated": 0.0,
}


def set_phase(phase: str) -> None:
    with _lock:
        _state["phase"] = phase
        _state["last_updated"] = time.time()


def set_current_site(site: str) -> None:
    with _lock:
        _state["current_site"] = site
        _state["last_updated"] = time.time()


def set_current_url(url: str) -> None:
    with _lock:
        _state["current_url"] = url
        _state["last_updated"] = time.time()


def set_current_content(content: str) -> None:
    with _lock:
        _state["current_content"] = (content or "")[:2000]
        _state["last_updated"] = time.time()


def inc_api_calls() -> None:
    with _lock:
        _state["api_calls"] = _state.get("api_calls", 0) + 1
        _state["last_updated"] = time.time()


def get_status() -> Dict[str, Any]:
    with _lock:
        return dict(_state)


def reset_status() -> None:
    with _lock:
        _state["phase"] = "idle"
        _state["current_site"] = ""
        _state["current_url"] = ""
        _state["current_content"] = ""
        _state["api_calls"] = 0
        _state["last_updated"] = time.time()
