"""ingest processor module - 主处理流程"""

import re
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .llm import compute_file_hash, llm_extract_source, get_llm_client
from .state import load_state, save_state
from .writers import write_source_page, write_concept_page, write_entity_page, update_reverse_links
from .index import update_index, write_log


def detect_source_type(file_path: Path) -> str:
    """检测素材类型"""
    name = file_path.name.lower()

    if "transcript" in name or "转录" in name:
        return "transcript"
    if file_path.suffix == ".pdf" or "pdf" in name:
        return "pdf"
    if "tweet" in name:
        return "tweet"

    return "article"


def extract_metadata(content: str) -> dict[str, Any]:
    """从内容提取元信息"""
    metadata: dict[str, Any] = {
        "author": "Unknown",
        "date": "",
        "url": ""
    }

    # 尝试提取作者
    author_patterns = [
        r"作者[：:]\s*([^\n]+)",
        r"Author[：:]\s*([^\n]+)",
        r"By\s+([^\n]+)",
    ]
    for pattern in author_patterns:
        match = re.search(pattern, content)
        if match:
            metadata["author"] = match.group(1).strip()
            break

    # 尝试提取日期
    date_patterns = [
        r"日期[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"Date[：:]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, content)
        if match:
            metadata["date"] = match.group(1)
            break

    # 尝试提取 URL
    url_pattern = r"https?://[^\s<>\n]+"
    match = re.search(url_pattern, content)
    if match:
        metadata["url"] = match.group(0)

    return metadata


def process_file(
    kb_root: Path,
    raw_file: Path,
    client,
    model: str,
    dry_run: bool = False
) -> tuple[Optional[str], list[str], list[str], float] | None:
    """
    处理单个文件，返回 (source_file, concept_files, entity_files, elapsed) 或 None
    """
    start_time = datetime.now()

    # 读取内容
    try:
        with open(raw_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    if len(content) < 100:
        return None

    # 提取元信息
    metadata = extract_metadata(content)
    source_type = detect_source_type(raw_file)

    # 调用 LLM
    result = llm_extract_source(client, model, content, raw_file.name)

    if not result:
        return None

    if dry_run:
        # 预览模式
        return None

    # 写入 sources/
    source_file = write_source_page(kb_root, result, raw_file, source_type, metadata)

    # 写入 concepts/
    concept_files = []
    for concept in result.get("concepts", []):
        cf = write_concept_page(kb_root, concept, source_file)
        concept_files.append(cf)

    # 写入 entities/
    entity_files = []
    for entity in result.get("entities", []):
        ef = write_entity_page(kb_root, entity, source_file)
        entity_files.append(ef)

    # 更新反向引用
    update_reverse_links(kb_root, concept_files, entity_files, source_file)

    # 更新索引
    update_index(kb_root)

    elapsed = (datetime.now() - start_time).total_seconds()

    return source_file, concept_files, entity_files, elapsed


def get_files_to_process(
    kb_root: Path,
    raw_dir: Path,
    file_arg: str | None,
    force: bool
) -> list[Path]:
    """获取需要处理的文件列表"""
    if file_arg:
        target = Path(file_arg)
        if target.is_dir():
            files = list(target.rglob("*.md")) + list(target.rglob("*.txt"))
        else:
            files = [target]
            force = True  # 单文件强制处理
    else:
        files = list(raw_dir.rglob("*.md")) + list(raw_dir.rglob("*.txt"))

    if not files:
        return []

    # 筛选需要处理的文件
    state = load_state(kb_root)
    files_to_process = []

    for f in files:
        if force:
            files_to_process.append(f)
        else:
            current_hash = compute_file_hash(f)
            stored_hash = state["files"].get(f.name)
            if stored_hash != current_hash:
                files_to_process.append(f)

    return files_to_process


def run_ingest(
    kb_root: Path,
    raw_dir: Path,
    client,
    model: str,
    file_arg: str | None = None,
    force: bool = False,
    dry_run: bool = False
) -> int:
    """运行 ingest 主流程，返回处理文件数"""
    from loguru import logger

    files_to_process = get_files_to_process(kb_root, raw_dir, file_arg, force)

    if not files_to_process:
        logger.info("所有文件已处理，无需更新")
        return 0

    logger.info(f"处理 {len(files_to_process)} 个文件")

    state = load_state(kb_root)

    for raw_file in files_to_process:
        logger.info(f"处理: {raw_file.name}")

        result = process_file(kb_root, raw_file, client, model, dry_run)

        if result is None:
            if dry_run:
                continue
            else:
                continue

        source_file, concept_files, entity_files, elapsed = result

        # 更新状态
        state["files"][raw_file.name] = compute_file_hash(raw_file)

        # 写日志
        write_log(kb_root, raw_file, source_file, concept_files, entity_files,
                  status="完成", elapsed=elapsed)

    # 保存状态
    save_state(kb_root, state)

    return len(files_to_process)