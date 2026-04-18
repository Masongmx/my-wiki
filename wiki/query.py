#!/usr/bin/env python3
"""kb query: 查询知识库

流程（按 schema.md）：
1. 问题分类（定义/对比/关系/列举/深度/探索）
2. 搜索相关页面
3. 合成答案
4. 可复用答案存 outputs/
"""

import click
import yaml
from pathlib import Path
from loguru import logger
import os
import json
import re
import subprocess
from datetime import datetime
from typing import Any
from openai import OpenAI


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sink=lambda msg: click.echo(msg, nl=False),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True
    )


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        kb_root = Path(__file__).parent.parent
        config_path = kb_root / "config" / "kb.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_key(config: dict[str, Any]) -> str:
    """获取 API key"""
    kb_root = Path(config["knowledge_base"]["root"])
    
    key_file = kb_root / "key.txt"
    if key_file.exists():
        with open(key_file, "r") as f:
            return f.read().strip()
    
    litellm_file = kb_root / "config" / "litellm_config.yaml"
    if litellm_file.exists():
        with open(litellm_file, "r") as f:
            litellm_cfg = yaml.safe_load(f)
            if litellm_cfg.get("model_list"):
                return litellm_cfg["model_list"][0]["litellm_params"]["api_key"]
    
    api_key = os.getenv("BAILIAN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    raise ValueError("找不到 API key")


def get_llm_client(config: dict[str, Any]) -> tuple[OpenAI, str]:
    """获取 LLM 客户端"""
    api_key = get_api_key(config)
    llm_config = config["llm"]
    
    return OpenAI(
        api_key=api_key,
        base_url=llm_config["base_url"]
    ), llm_config["model"]


def classify_question(query: str) -> str:
    """分类问题类型"""
    query_lower = query.lower()
    
    # 定义类
    if "什么是" in query or "何为" in query or "定义" in query:
        return "definition"
    
    # 对比类
    if "对比" in query or "区别" in query or "比较" in query or "vs" in query_lower:
        return "comparison"
    
    # 关系类
    if "关系" in query or "联系" in query or "关联" in query:
        return "relation"
    
    # 列举类
    if "有哪些" in query or "列出" in query or "列举" in query:
        return "list"
    
    # 深度类
    if "详细" in query or "深入" in query or "解析" in query or "深度" in query:
        return "deep"
    
    # 默认探索类
    return "explore"


def extract_keywords(query: str) -> list[str]:
    """提取关键词"""
    # 常见问题词
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
    
    # 分割关键词
    words = cleaned.split()
    keywords = [w for w in words if len(w) >= 2][:3]
    
    return keywords if keywords else [cleaned[:15]]


def search_files(kb_root: Path, keywords: list[str], limit: int = 5) -> list[Path]:
    """搜索相关文件"""
    exclude_dirs = [".obsidian", ".smart-env", ".git", ".venv", "node_modules", "__pycache__"]
    
    results = set()
    
    # 优先搜索 wiki 子目录
    wiki_dirs = [
        kb_root / "wiki" / "concepts",
        kb_root / "wiki" / "entities",
        kb_root / "wiki" / "sources",
        kb_root / "wiki" / "outputs",
    ]
    
    for keyword in keywords:
        if not keyword:
            continue
        
        # 先搜索 wiki 目录
        for wiki_dir in wiki_dirs:
            if wiki_dir.exists():
                files = _grep_search(wiki_dir, keyword, exclude_dirs)
                results.update(files)
        
        # 如果结果不足，搜索整个知识库
        if len(results) < limit:
            files = _grep_search(kb_root, keyword, exclude_dirs)
            results.update(files)
    
    # 按相关性排序
    scored = []
    for file in results:
        score = 0
        file_str = str(file)
        for kw in keywords:
            if kw.lower() in file_str.lower():
                score += 1
        scored.append((score, file))
    
    scored.sort(key=lambda x: (-x[0], x[1]))
    
    return [f[1] for f in scored[:limit]]


def _grep_search(directory: Path, term: str, exclude_dirs: list[str]) -> set[Path]:
    """grep 搜索"""
    results = set()
    
    # 尝试 ripgrep
    try:
        cmd = ["rg", "-l", "-i", term, str(directory)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            for f in files:
                if f and not any(exc in f for exc in exclude_dirs):
                    results.add(Path(f))
            return results
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.debug(f"ripgrep 搜索失败: {e}")
    
    # 回退 grep
    try:
        cmd = ["grep", "-r", "-l", "-i", term, str(directory)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            for f in files:
                if f and not any(exc in f for exc in exclude_dirs):
                    results.add(Path(f))
    except Exception as e:
        logger.debug(f"grep 搜索失败: {e}")
    
    return results


def read_file_content(file_path: Path, max_length: int = 2000) -> str:
    """读取文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 截断
        if len(content) > max_length:
            content = content[:max_length] + "\n...[已截断]"
        
        return content
    except Exception as e:
        logger.error(f"读取失败: {file_path}, {e}")
        return ""


def generate_answer(
    client: OpenAI,
    model: str,
    query: str,
    contexts: list[dict[str, str]],
    question_type: str
) -> str:
    """生成答案"""
    if not contexts:
        return "抱歉，没有找到相关内容。"
    
    # 构建上下文
    context_text = "\n\n---\n\n".join([
        f"【来源: {ctx['file']}】\n{ctx['content']}"
        for ctx in contexts
    ])
    
    # 根据问题类型调整提示
    prompts = {
        "definition": f"""基于以下参考内容，简洁定义问题中的概念。

参考内容：
{context_text}

问题：{query}

请提供：
1. 一句话定义（不超过50字）
2. 核心要点（3-5个）
3. 相关概念链接（如有）""",
        
        "comparison": f"""基于以下参考内容，对比问题中的两个对象。

参考内容：
{context_text}

问题：{query}

请提供对比表格：
| 维度 | A | B |
|------|------|------|
| ... | ... | ... |

并简要总结核心差异。""",
        
        "relation": f"""基于以下参考内容，分析问题中对象的关系。

参考内容：
{context_text}

问题：{query}

请提供：
1. 关系描述
2. 共同点
3. 差异点""",
        
        "list": f"""基于以下参考内容，列举相关内容。

参考内容：
{context_text}

问题：{query}

请提供列表形式回答。""",
        
        "deep": f"""基于以下参考内容，深入解析问题。

参考内容：
{context_text}

问题：{query}

请提供详细分析，包含：
1. 背景/定义
2. 核心内容
3. 关键洞察
4. 实践建议""",
        
        "explore": f"""基于以下参考内容，回答问题。

参考内容：
{context_text}

问题：{query}

请提供清晰、准确的回答，标注参考来源。"""
    }
    
    prompt = prompts.get(question_type, prompts["explore"])
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"生成答案失败: {e}")
        return f"生成答案时出错: {e}"


def save_output(
    kb_root: Path,
    query: str,
    answer: str,
    sources: list[str],
    question_type: str
) -> None:
    """保存可复用答案到 outputs/"""
    outputs_dir = kb_root / "wiki" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名
    safe_name = re.sub(r'[<>:"/\\|?*]', '-', query[:30])
    safe_name = re.sub(r'\s+', '-', safe_name)
    filename = f"{safe_name}.md"
    
    filepath = outputs_dir / filename
    
    # 构建 frontmatter
    fm = f"""---
type: output
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d')}
tags: [query, {question_type}]
output_type: {question_type}
query: "{query}"
---

"""
    
    content = fm + f"# {query[:50]}\n\n"
    content += "## 问题\n\n"
    content += query + "\n\n"
    content += "## 答案\n\n"
    content += answer + "\n\n"
    content += "## 使用的来源\n\n"
    for src in sources:
        content += f"- [[{src}]]\n"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.success(f"保存 outputs/{filename}")


def should_save_output(question_type: str, answer: str) -> bool:
    """判断是否保存答案"""
    # 对比类、深度类、列举类答案值得保存
    save_types = ["comparison", "deep", "list", "relation"]
    
    if question_type in save_types:
        return True
    
    # 答案超过 200 字才保存
    if len(answer) > 200:
        return True
    
    return False


@click.command()
@click.argument("query")
@click.option("--config", "-c", type=click.Path(exists=True), help="配置文件路径")
@click.option("--limit", "-l", default=3, help="参考文档数量")
@click.option("--save", "-s", is_flag=True, help="保存答案到 outputs/")
@click.option("--format", "-f", type=click.Choice(["text", "table", "markdown"]), 
              default="markdown", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def query(
    query: str,
    config: str | None,
    limit: int,
    save: bool,
    format: str,
    verbose: bool
) -> None:
    """查询知识库
    
    用法：
        kb query "问题"            # 搜索并回答
        kb query "问题" --save     # 回答并存入 outputs/
    """
    setup_logging("DEBUG" if verbose else "INFO")
    
    cfg = load_config(Path(config) if config else None)
    kb_root = Path(cfg["knowledge_base"]["root"])
    
    logger.info(f"问题: {query}")
    
    # 分类问题
    question_type = classify_question(query)
    logger.debug(f"问题类型: {question_type}")
    
    # 获取 LLM 客户端
    try:
        client, model = get_llm_client(cfg)
    except Exception as e:
        logger.error(f"初始化 LLM 失败: {e}")
        raise click.Abort()
    
    # 提取关键词搜索
    keywords = extract_keywords(query)
    logger.debug(f"关键词: {keywords}")
    
    files = search_files(kb_root, keywords, limit)
    
    if not files:
        click.echo("抱歉，没有找到相关内容来回答您的问题。")
        return
    
    # 收集上下文
    contexts = []
    sources = []
    for file in files:
        content = read_file_content(file, 1500)
        if content:
            rel_path = file.relative_to(kb_root)
            contexts.append({
                "file": str(rel_path),
                "content": content
            })
            sources.append(str(rel_path))
    
    if verbose:
        logger.info(f"参考 {len(contexts)} 个文档")
        for ctx in contexts:
            logger.debug(f"  - {ctx['file']}")
    
    # 生成答案
    answer = generate_answer(client, model, query, contexts, question_type)
    
    # 输出答案
    click.echo(f"\n{answer}\n")
    
    if verbose:
        click.echo("参考来源:")
        for src in sources:
            click.echo(f"  - {src}")
    
    # 判断是否保存
    if save or should_save_output(question_type, answer):
        save_output(kb_root, query, answer, sources, question_type)
        click.echo(f"\n答案已保存到 outputs/")