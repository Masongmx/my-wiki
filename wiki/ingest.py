#!/usr/bin/env python3
"""kb ingest: 处理 raw/ 素材到 wiki/

流程（按 schema.md）：
1. 读 raw/ 文件
2. 调用 LLM 提取洞察 → 写 sources/
3. 提取概念 → 更新 concepts/
4. 提取实体 → 更新 entities/
5. 维护双向链接
6. 更新 _index.md
7. 写 _meta/log.md

粒度控制：
- 概念：不超过 20 个/来源
- 实体：不超过 10 个/来源
"""

import click
import yaml
from pathlib import Path
from loguru import logger
import os
import json
import re
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from openai import OpenAI

# 配置日志
def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sink=lambda msg: click.echo(msg, nl=False),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True
    )


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        kb_root = Path(__file__).parent.parent
        config_path = kb_root / "config" / "kb.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_key(config: Dict[str, Any]) -> str:
    """从配置或 key.txt 获取 API key"""
    kb_root = Path(config["knowledge_base"]["root"])
    
    # 优先从 key.txt 读取
    key_file = kb_root / "key.txt"
    if key_file.exists():
        with open(key_file, "r") as f:
            return f.read().strip()
    
    # 其次从 litellm_config.yaml 读取
    litellm_file = kb_root / "config" / "litellm_config.yaml"
    if litellm_file.exists():
        with open(litellm_file, "r") as f:
            litellm_cfg = yaml.safe_load(f)
            if litellm_cfg.get("model_list"):
                return litellm_cfg["model_list"][0]["litellm_params"]["api_key"]
    
    # 最后从环境变量
    api_key = os.getenv("BAILIAN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    raise ValueError("找不到 API key（检查 key.txt 或 litellm_config.yaml）")


def get_llm_client(config: Dict[str, Any]) -> tuple[OpenAI, str]:
    """获取 LLM 客户端"""
    api_key = get_api_key(config)
    llm_config = config["llm"]
    
    return OpenAI(
        api_key=api_key,
        base_url=llm_config["base_url"]
    ), llm_config["model"]


def compute_file_hash(file_path: Path) -> str:
    """计算文件 hash"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_state(kb_root: Path) -> Dict[str, Any]:
    """加载处理状态"""
    state_file = kb_root / ".ingest_state.json"
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}, "last_run": None}


def save_state(kb_root: Path, state: Dict[str, Any]) -> None:
    """保存处理状态"""
    state_file = kb_root / ".ingest_state.json"
    state["last_run"] = datetime.now().isoformat()
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


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


def extract_metadata(content: str) -> Dict[str, Any]:
    """从内容提取元信息"""
    metadata = {
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


def llm_extract_source(client: OpenAI, model: str, content: str, filename: str) -> Optional[Dict[str, Any]]:
    """调用 LLM 提取来源页内容"""
    
    # JSON 示例（单独定义，避免 f-string 大括号冲突）
    json_example = '''{
  "title": "来源标题（简洁）",
  "overview": "整体概览（100-200字）",
  "insights": [
    {
      "title": "洞察标题",
      "content": "洞察内容（100-150字）"
    }
  ],
  "concepts": [
    {
      "name": "概念名称",
      "definition": "一句话定义（不超过50字）",
      "importance": "为什么重要（不超过100字）",
      "key_points": ["要点1", "要点2", "要点3"]
    }
  ],
  "entities": [
    {
      "name": "实体名称",
      "type": "tool|person|company|project",
      "info": "关键信息（不超过200字）",
      "features": ["特点1", "特点2"]
    }
  ],
  "follow_up_questions": ["值得深入探索的问题"]
}'''
    
    prompt = f"""分析以下内容，生成结构化的来源页（source page）。

内容（来自文件 {filename}）：
{content[:6000]}

请以 JSON 格式返回（只返回 JSON，不要其他内容）：
{json_example}

提取规则：
- concepts：不超过 20 个，只提取核心概念（全文围绕论述或首次定义）
- entities：不超过 10 个，只提取主要对象或关键配角
- insights：提取 3-5 个最有价值的洞察"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            logger.error(f"无法提取 JSON: {result_text[:200]}")
            return None
    except Exception as e:
        logger.error(f"LLM 调用失败: {e}")
        return None


def safe_filename(name: str) -> str:
    """生成安全的文件名"""
    # 替换非法字符
    safe = re.sub(r'[<>:"/\\|?*]', '-', name)
    # 去掉空格，用 - 连接
    safe = re.sub(r'\s+', '-', safe)
    return safe.strip('-')


def write_source_page(kb_root: Path, source: Dict[str, Any], raw_file: Path, source_type: str, metadata: Dict[str, Any]) -> str:
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
    
    logger.success(f"写入 sources/{filename}")
    return filename


def write_concept_page(kb_root: Path, concept: Dict[str, Any], source_file: str) -> str:
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
            logger.debug(f"概念 {concept['name']} 已引用 {source_file}")
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
        
        logger.info(f"更新 concepts/{filename}（追加来源）")
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
    
    logger.success(f"创建 concepts/{filename}")
    return filename


def write_entity_page(kb_root: Path, entity: Dict[str, Any], source_file: str) -> str:
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
            logger.debug(f"实体 {entity['name']} 已引用 {source_file}")
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
        
        logger.info(f"更新 entities/{filename}（追加来源）")
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
    
    logger.success(f"创建 entities/{filename}")
    return filename


def update_reverse_links(kb_root: Path, concept_files: List[str], entity_files: List[str], source_file: str) -> None:
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
    
    logger.success("更新 wiki/_index.md")


def write_log(kb_root: Path, raw_file: Path, source_file: str,
              concepts: List[str], entities: List[str],
              status: str = "完成", elapsed: float = 0) -> None:
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
    
    logger.debug("更新 wiki/_meta/log.md")


@click.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--config", "-c", type=click.Path(exists=True), help="配置文件路径")
@click.option("--batch", "-b", is_flag=True, help="批量处理（不交互）")
@click.option("--dry-run", "-d", is_flag=True, help="预览不写入")
@click.option("--force", "-f", is_flag=True, help="强制重新处理")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def ingest(file: Optional[str], config: Optional[str],
           batch: bool, dry_run: bool, force: bool, verbose: bool) -> None:
    """处理 raw/ 素材到 wiki/
    
    用法：
        kb ingest <file>          # 处理单个文件
        kb ingest raw/articles/   # 处理目录
        kb ingest --batch         # 批量处理
        kb ingest --dry-run       # 预览
    """
    setup_logging("DEBUG" if verbose else "INFO")
    
    cfg = load_config(Path(config) if config else None)
    kb_root = Path(cfg["knowledge_base"]["root"])
    raw_dir = kb_root / cfg["knowledge_base"]["raw_dir"]
    
    logger.info(f"知识库根目录: {kb_root}")
    
    # 获取 LLM 客户端
    try:
        client, model = get_llm_client(cfg)
        logger.info(f"LLM 模型: {model}")
    except Exception as e:
        logger.error(f"初始化 LLM 失败: {e}")
        raise click.Abort()
    
    # 确定处理文件
    if file:
        target = Path(file)
        if target.is_dir():
            # 处理目录
            files = list(target.rglob("*.md")) + list(target.rglob("*.txt"))
        else:
            files = [target]
            force = True  # 单文件强制处理
    else:
        # 处理 raw 目录
        files = list(raw_dir.rglob("*.md")) + list(raw_dir.rglob("*.txt"))
    
    if not files:
        logger.warning("没有找到要处理的文件")
        return
    
    # 加载状态
    state = load_state(kb_root)
    
    # 筛选需要处理的文件
    files_to_process = []
    for f in files:
        if force:
            files_to_process.append(f)
        else:
            current_hash = compute_file_hash(f)
            stored_hash = state["files"].get(f.name)
            if stored_hash != current_hash:
                files_to_process.append(f)
    
    if not files_to_process:
        logger.info("所有文件已处理，无需更新")
        return
    
    logger.info(f"处理 {len(files_to_process)} 个文件")
    
    # 处理每个文件
    for raw_file in files_to_process:
        start_time = datetime.now()
        logger.info(f"处理: {raw_file.name}")
        
        # 读取内容
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取失败: {raw_file.name}, {e}")
            continue
        
        if len(content) < 100:
            logger.warning(f"内容太短，跳过: {raw_file.name}")
            continue
        
        # 提取元信息
        metadata = extract_metadata(content)
        source_type = detect_source_type(raw_file)
        
        # 调用 LLM
        result = llm_extract_source(client, model, content, raw_file.name)
        
        if not result:
            logger.error(f"LLM 提取失败: {raw_file.name}")
            continue
        
        if dry_run:
            # 预览模式：只显示结果
            click.echo(f"\n预览 {raw_file.name}:")
            click.echo(f"  标题: {result.get('title', '')}")
            click.echo(f"  概念: {len(result.get('concepts', []))} 个")
            for c in result.get('concepts', []):
                click.echo(f"    - {c['name']}")
            click.echo(f"  实体: {len(result.get('entities', []))} 个")
            for e in result.get('entities', []):
                click.echo(f"    - {e['name']}")
            continue
        
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
        
        # 更新状态
        state["files"][raw_file.name] = compute_file_hash(raw_file)
        
        # 写日志
        elapsed = (datetime.now() - start_time).total_seconds()
        write_log(kb_root, raw_file, source_file, concept_files, entity_files, 
                  status="完成", elapsed=elapsed)
    
    # 保存状态
    save_state(kb_root, state)
    
    logger.success(f"处理完成！共处理 {len(files_to_process)} 个文件")