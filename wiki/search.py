#!/usr/bin/env python3
"""kb search: 搜索知识库文件"""

import re
import subprocess
from pathlib import Path
from typing import Protocol

from loguru import logger


class _GrepSearchFn(Protocol):
    def __call__(self, directory: Path, term: str, exclude_dirs: list[str]) -> set[Path]: ...


def extract_keywords(query: str) -> list[str]:
    """提取搜索关键词"""
    question_words = [
        "什么是", "何为", "什么叫",
        "如何", "怎么", "怎样",
        "为什么", "为何",
        "哪个", "哪些", "什么",
        "有没有", "是否存在",
        "能不能", "可以吗", "是否",
        "介绍一下", "讲一下", "说说",
        "帮我", "请", "请问",
        "对比", "区别", "比较", "vs",
        "详细", "深入", "解析",
        "？", "?", "！", "!", "。", ".", "，", ","
    ]

    cleaned = query
    for word in question_words:
        cleaned = cleaned.replace(word, "")

    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    words = cleaned.split()
    keywords = [w for w in words if len(w) >= 2][:3]

    return keywords if keywords else [cleaned[:15]]


def _ripgrep_search(directory: Path, term: str, exclude_dirs: list[str]) -> set[Path]:
    """使用 ripgrep 搜索"""
    results: set[Path] = set()
    try:
        cmd = ["rg", "-l", "-i", term, str(directory)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            for f in result.stdout.strip().split("\n"):
                if f and not any(exc in f for exc in exclude_dirs):
                    results.add(Path(f))
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.debug(f"ripgrep 搜索失败: {e}")
    return results


def _grep_fallback(directory: Path, term: str, exclude_dirs: list[str]) -> set[Path]:
    """回退到 grep 搜索"""
    results: set[Path] = set()
    try:
        cmd = ["grep", "-r", "-l", "-i", term, str(directory)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            for f in result.stdout.strip().split("\n"):
                if f and not any(exc in f for exc in exclude_dirs):
                    results.add(Path(f))
    except Exception as e:
        logger.debug(f"grep 搜索失败: {e}")
    return results


_grep_search: _GrepSearchFn = _ripgrep_search  # prefer ripgrep


def search_files(kb_root: Path, keywords: list[str], limit: int = 5) -> list[Path]:
    """搜索相关文件"""
    exclude_dirs = [".obsidian", ".smart-env", ".git", ".venv", "node_modules", "__pycache__"]

    results: set[Path] = set()

    wiki_dirs = [
        kb_root / "wiki" / "concepts",
        kb_root / "wiki" / "entities",
        kb_root / "wiki" / "sources",
        kb_root / "wiki" / "outputs",
    ]

    for keyword in keywords:
        if not keyword:
            continue

        for wiki_dir in wiki_dirs:
            if wiki_dir.exists():
                results.update(_grep_search(wiki_dir, keyword, exclude_dirs))

        if len(results) < limit:
            results.update(_grep_search(kb_root, keyword, exclude_dirs))

    # 按相关性排序
    scored: list[tuple[int, Path]] = []
    for file in results:
        score = sum(1 for kw in keywords if kw.lower() in str(file).lower())
        scored.append((score, file))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [f for _, f in scored[:limit]]
