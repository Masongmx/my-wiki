#!/usr/bin/env python3
"""My Wiki Web UI - 共享工具"""

from pathlib import Path
import yaml


def load_config() -> dict:
    """加载配置"""
    config_path = Path(__file__).parent.parent / "config" / "kb.yaml"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_kb_root() -> Path:
    """获取知识库根目录"""
    config = load_config()
    if config and "knowledge_base" in config:
        data_dir = config["knowledge_base"].get("data_dir", "./data")
        return Path(data_dir)
    # 默认使用 ./data
    return Path(__file__).parent.parent / "data"