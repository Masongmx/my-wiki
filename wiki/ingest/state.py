"""ingest state management - 处理状态持久化"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any


def load_state(kb_root: Path) -> dict[str, Any]:
    """加载处理状态"""
    state_file = kb_root / ".ingest_state.json"
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}, "last_run": None}


def save_state(kb_root: Path, state: dict[str, Any]) -> None:
    """保存处理状态"""
    state_file = kb_root / ".ingest_state.json"
    state["last_run"] = datetime.now().isoformat()
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)