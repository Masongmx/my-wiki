"""ingest index module - 索引更新和日志"""

import re
from pathlib import Path
from datetime import datetime


def update_index(kb_root: Path) -> None:
    """更新 _index.md"""
    index_file = kb_root / "wiki" / "_index.md"

    # 收集所有页面
    sources = sorted((kb_root / "wiki" / "sources").glob("*.md"))
    concepts = sorted((kb_root / "wiki" / "concepts").glob("*.md"))
    entities = sorted((kb_root / "wiki" / "entities").glob("*.md"))

    # 读取现有索引
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = ""

    # 构建新索引
    content = f"""# 知识库索引

> 最后更新：{datetime.now().strftime('%Y-%m-%d')}

## 来源（sources/）
"""

    for src in sources:
        title = src.stem
        # 尝试读取作者和日期
        author = "Unknown"
        date = ""
        try:
            with open(src, "r", encoding="utf-8") as f:
                fm_content = f.read(500)
                author_match = re.search(r'author:\s*([^\n]+)', fm_content)
                date_match = re.search(r'date:\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', fm_content)
                if author_match:
                    author = author_match.group(1).strip()
                if date_match:
                    date = date_match.group(1)
        except:
            pass

        content += f"- [[sources/{title}]] — {author} — {date}\n"

    content += "\n---\n\n## 概念（concepts/）\n\n"

    # 按类别分组概念
    agent_concepts = []
    vps_concepts = []
    other_concepts = []

    for concept in concepts:
        title = concept.stem
        # 尝试读取定义
        definition = ""
        try:
            with open(concept, "r", encoding="utf-8") as f:
                c = f.read()
                # 提取定义
                def_match = re.search(r'## 定义\n\n([^\n]+)', c)
                if def_match:
                    definition = def_match.group(1)[:50]
        except:
            pass

        entry = f"- [[concepts/{title}]] — {definition}"

        if "Agent" in title or "agent" in title.lower():
            agent_concepts.append(entry)
        elif "VPS" in title or "Hysteria" in title or "VLESS" in title:
            vps_concepts.append(entry)
        else:
            other_concepts.append(entry)

    if agent_concepts:
        content += "### Agent 相关\n"
        for entry in agent_concepts:
            content += entry + "\n"
        content += "\n"

    if vps_concepts:
        content += "### VPS/网络相关\n"
        for entry in vps_concepts:
            content += entry + "\n"
        content += "\n"

    if other_concepts:
        content += "### 其他\n"
        for entry in other_concepts:
            content += entry + "\n"

    content += "\n---\n\n## 实体（entities/）\n\n"

    for entity in entities:
        title = entity.stem
        entity_type = "unknown"
        try:
            with open(entity, "r", encoding="utf-8") as f:
                c = f.read(300)
                type_match = re.search(r'entity_type:\s*([^\n]+)', c)
                if type_match:
                    entity_type = type_match.group(1).strip()
        except:
            pass

        content += f"- [[entities/{title}]] — {entity_type}\n"

    content += f"\n---\n\n_索引生成时间：{datetime.now().strftime('%Y-%m-%d')}_\n"

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(content)


def write_log(
    kb_root: Path,
    raw_file: Path,
    source_file: str,
    concepts: list[str],
    entities: list[str],
    status: str = "完成",
    elapsed: float = 0
) -> None:
    """写入操作日志"""
    log_file = kb_root / "wiki" / "_meta" / "log.md"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有日志
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = "# 知识库操作日志\n\n"

    # 新增日志条目
    entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} | ingest | {raw_file.name}\n\n"
    entry += f"- 处理：`{raw_file.relative_to(kb_root)}`\n"
    entry += f"- 创建：`sources/{source_file}`\n"

    if concepts:
        entry += f"- 创建概念：{len(concepts)} 个\n"
        for c in concepts[:5]:
            entry += f"  - {c}\n"
        if len(concepts) > 5:
            entry += f"  - ...还有 {len(concepts) - 5} 个\n"

    if entities:
        entry += f"- 创建实体：{len(entities)} 个\n"
        for e in entities[:3]:
            entry += f"  - {e}\n"
        if len(entities) > 3:
            entry += f"  - ...还有 {len(entities) - 3} 个\n"

    entry += f"- 耗时：{elapsed:.1f} 秒\n"
    entry += f"- 状态：{status} ✅\n"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(existing + entry)