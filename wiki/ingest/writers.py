"""ingest writers module - 写入 wiki 页面"""

import re
from pathlib import Path
from datetime import datetime
from typing import Any


def safe_filename(name: str) -> str:
    """生成安全的文件名"""
    # 替换非法字符
    safe = re.sub(r'[<>:"/\\|?*]', '-', name)
    # 去掉空格，用 - 连接
    safe = re.sub(r'\s+', '-', safe)
    return safe.strip('-')


def write_source_page(
    kb_root: Path,
    source: dict[str, Any],
    raw_file: Path,
    source_type: str,
    metadata: dict[str, Any]
) -> str:
    """写入 sources/ 页面"""
    sources_dir = kb_root / "wiki" / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(source["title"]) + ".md"
    filepath = sources_dir / filename

    # 构建 frontmatter
    fm = f"""---
type: source
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d')}
tags: [analysis, {source_type}]
source_type: {source_type}
raw_path: {raw_file.relative_to(kb_root)}
author: {metadata.get('author', 'Unknown')}
date: {metadata.get('date', '')}
url: {metadata.get('url', '')}
---

"""

    # 构建内容
    content = fm + f"# {source['title']}\n\n"
    content += "## 元信息\n\n"
    content += f"- 类型：{source_type}\n"
    content += f"- 作者：{metadata.get('author', 'Unknown')}\n"
    content += f"- 时间：{metadata.get('date', '')}\n"
    content += f"- URL：{metadata.get('url', '')}\n"
    content += f"- raw 路径：`{raw_file.relative_to(kb_root)}`\n\n"

    content += "## 概览\n\n"
    content += source.get("overview", "") + "\n\n"

    content += "## 核心洞察\n\n"
    for i, insight in enumerate(source.get("insights", []), 1):
        content += f"### {i}. {insight['title']}\n\n"
        content += insight.get("content", "") + "\n\n"

    # 提取的概念（先占位，后面更新）
    content += "## 提取的概念\n\n"
    for concept in source.get("concepts", []):
        concept_file = safe_filename(concept["name"])
        content += f"- [[concepts/{concept_file}]] — {concept.get('definition', '')[:50]}\n"
    content += "\n"

    # 提取的实体
    content += "## 提取的实体\n\n"
    for entity in source.get("entities", []):
        entity_file = safe_filename(entity["name"])
        content += f"- [[entities/{entity_file}]] — {entity.get('type', '')}\n"
    content += "\n"

    # 后续问题
    content += "## 后续问题\n\n"
    for q in source.get("follow_up_questions", []):
        content += f"- {q}\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


def write_concept_page(
    kb_root: Path,
    concept: dict[str, Any],
    source_file: str
) -> str:
    """写入 concepts/ 页面"""
    concepts_dir = kb_root / "wiki" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(concept["name"]) + ".md"
    filepath = concepts_dir / filename

    # 检查是否已存在
    if filepath.exists():
        # 更新已有页面：追加来源链接
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read()

        # 检查是否已引用此来源
        if source_file in existing:
            return filename

        # 追加来源链接（在 "来源" 部分）
        source_ref = f"- [[sources/{source_file}]]\n"

        # 找到 "来源" 部分
        if "## 来源" in existing:
            # 在来源部分追加
            parts = existing.split("## 来源")
            if len(parts) >= 2:
                new_content = parts[0] + "## 来源\n" + source_ref + parts[1]
            else:
                new_content = existing + "\n" + source_ref
        else:
            # 没有 "来源" 部分，添加
            new_content = existing + f"\n\n## 来源\n\n{source_ref}"

        # 更新 frontmatter.updated
        new_content = re.sub(
            r'updated:\s*\d{4}-\d{2}-\d{2}',
            f"updated: {datetime.now().strftime('%Y-%m-%d')}",
            new_content
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return filename

    # 创建新页面
    fm = f"""---
type: concept
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d')}
tags: [concept]
sources: [sources/{source_file}]
status: stable
---

"""

    content = fm + f"# {concept['name']}\n\n"
    content += "## 定义\n\n"
    content += concept.get("definition", "") + "\n\n"

    content += "## 核心要点\n\n"
    for point in concept.get("key_points", []):
        content += f"- {point}\n"
    content += "\n"

    content += "## 为什么重要\n\n"
    content += concept.get("importance", "") + "\n\n"

    content += "## 来源\n\n"
    content += f"- [[sources/{source_file}]]\n\n"

    content += "## 反向引用\n\n"
    content += "被以下页面引用：\n"
    content += "（待更新）\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


def write_entity_page(
    kb_root: Path,
    entity: dict[str, Any],
    source_file: str
) -> str:
    """写入 entities/ 页面"""
    entities_dir = kb_root / "wiki" / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(entity["name"]) + ".md"
    filepath = entities_dir / filename

    # 检查是否已存在
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing = f.read()

        if source_file in existing:
            return filename

        # 追加来源链接
        source_ref = f"- [[sources/{source_file}]]\n"

        if "## 来源" in existing:
            parts = existing.split("## 来源")
            if len(parts) >= 2:
                new_content = parts[0] + "## 来源\n" + source_ref + parts[1]
            else:
                new_content = existing + "\n" + source_ref
        else:
            new_content = existing + f"\n\n## 来源\n\n{source_ref}"

        new_content = re.sub(
            r'updated:\s*\d{4}-\d{2}-\d{2}',
            f"updated: {datetime.now().strftime('%Y-%m-%d')}",
            new_content
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return filename

    # 创建新页面
    fm = f"""---
type: entity
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d')}
tags: [entity]
entity_type: {entity.get('type', 'unknown')}
sources: [sources/{source_file}]
status: stable
---

"""

    content = fm + f"# {entity['name']}\n\n"
    content += "## 基本信息\n\n"
    content += f"- 类型：{entity.get('type', '')}\n"
    content += "- 时间：（待补充）\n"
    content += "- 链接：（待补充）\n"
    content += "- 作者/公司：（待补充）\n\n"

    content += "## 关键信息\n\n"
    content += entity.get("info", "") + "\n\n"

    content += "## 功能/特点\n\n"
    for feature in entity.get("features", []):
        content += f"- {feature}\n"
    content += "\n"

    content += "## 来源\n\n"
    content += f"- [[sources/{source_file}]]\n\n"

    content += "## 反向引用\n\n"
    content += "被以下页面引用：\n"
    content += "（待更新）\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


def update_reverse_links(
    kb_root: Path,
    concept_files: list[str],
    entity_files: list[str],
    source_file: str
) -> None:
    """更新反向引用"""
    # 更新概念的 "反向引用" 部分
    concepts_dir = kb_root / "wiki" / "concepts"
    for concept_file in concept_files:
        filepath = concepts_dir / concept_file
        if not filepath.exists():
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 在反向引用部分添加来源引用
        if "## 反向引用" in content:
            parts = content.split("## 反向引用")
            if len(parts) >= 2:
                reverse_section = parts[1]

                # 检查是否已有此来源
                if source_file not in reverse_section:
                    # 添加来源引用
                    new_reverse = reverse_section.replace(
                        "（待更新）",
                        f"- [[sources/{source_file}]]"
                    )
                    if "（待更新）" not in reverse_section:
                        new_reverse = reverse_section + f"- [[sources/{source_file}]]\n"

                    new_content = parts[0] + "## 反向引用" + new_reverse

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)