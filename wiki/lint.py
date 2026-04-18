#!/usr/bin/env python3
"""kb lint: 知识库健康检查

检查项目（按 schema.md）：
1. 矛盾检测 — 概念定义不一致
2. 孤立页检测 — 无 inbound 链接
3. 缺失页检测 — 链接指向不存在的页面
4. 过时内容检测 — 来源过时
5. 日志格式检查
"""

import click
import yaml
from pathlib import Path
from loguru import logger
import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any
from collections import defaultdict


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sink=lambda msg: click.echo(msg, nl=False),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True
    )


def load_config(config_path: Path | None = None) -> dict:
    """加载配置"""
    if config_path is None:
        kb_root = Path(__file__).parent.parent
        config_path = kb_root / "config" / "kb.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_markdown_files(kb_root: Path, exclude_dirs: list[str]) -> list[Path]:
    """查找所有 Markdown 文件"""
    files = []
    
    for file in kb_root.rglob("*.md"):
        relative = file.relative_to(kb_root)
        if any(part in exclude_dirs for part in relative.parts):
            continue
        files.append(file)
    
    return files


def build_file_index(kb_root: Path, exclude_dirs: list[str]) -> dict[str, Path]:
    """构建文件名索引"""
    index = {}
    
    for file in kb_root.rglob("*.md"):
        relative = file.relative_to(kb_root)
        if any(part in exclude_dirs for part in relative.parts):
            continue
        index[file.stem] = file
        index[str(relative)[:-3]] = file
    
    return index


def extract_links(file_path: Path) -> dict[str, list[str]]:
    """提取链接"""
    links = {
        "wiki_links": [],
        "md_links": [],
        "embeds": []
    }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # [[wiki link]]
        wiki_pattern = r'\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]'
        for match in re.finditer(wiki_pattern, content):
            links["wiki_links"].append(match.group(1))
        
        # [text](url) 内部链接
        md_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(md_pattern, content):
            url = match.group(2)
            if not url.startswith(("http://", "https://", "mailto:")):
                links["md_links"].append(url)
        
        # ![[embed]]
        embed_pattern = r'!\[\[([^\]]+)\]\]'
        for match in re.finditer(embed_pattern, content):
            links["embeds"].append(match.group(1))
    
    except Exception as e:
        logger.warning(f"读取失败: {file_path}, {e}")
    
    return links


def resolve_link(kb_root: Path, link: str, index: dict[str, Path] | None = None) -> Path | None:
    """解析链接"""
    if index and link in index:
        return index[link]
    
    candidate = kb_root / f"{link}.md"
    if candidate.exists():
        return candidate
    
    return None


def check_broken_links(kb_root: Path, files: list[Path],
                       index: dict[str, Path]) -> dict[str, Any]:
    """检查缺失页（死链）"""
    results = {
        "total_links": 0,
        "broken_links": [],
        "files_with_broken": defaultdict(list)
    }
    
    for file in files:
        links = extract_links(file)
        rel_file = file.relative_to(kb_root)
        
        # Wiki 链接
        for link in links["wiki_links"]:
            results["total_links"] += 1
            target = resolve_link(kb_root, link, index)
            
            if not target:
                broken = f"[[{link}]]"
                results["broken_links"].append({
                    "file": str(rel_file),
                    "link": broken,
                    "type": "wiki"
                })
                results["files_with_broken"][str(rel_file)].append(broken)
        
        # Markdown 链接
        for link in links["md_links"]:
            results["total_links"] += 1
            target = kb_root / link
            
            if not target.exists():
                broken = f"[...]({link})"
                results["broken_links"].append({
                    "file": str(rel_file),
                    "link": broken,
                    "type": "markdown"
                })
                results["files_with_broken"][str(rel_file)].append(broken)
        
        # 嵌入
        for embed in links["embeds"]:
            results["total_links"] += 1
            found = False
            for ext in ["", ".md", ".png", ".jpg", ".jpeg", ".gif", ".pdf"]:
                candidate = kb_root / f"{embed}{ext}"
                if candidate.exists():
                    found = True
                    break
            
            if not found:
                broken = f"![[{embed}]]"
                results["broken_links"].append({
                    "file": str(rel_file),
                    "link": broken,
                    "type": "embed"
                })
                results["files_with_broken"][str(rel_file)].append(broken)
    
    return results


def check_orphans(kb_root: Path, files: list[Path],
                  index: dict[str, Path]) -> dict[str, Any]:
    """检查孤立页"""
    results = {
        "total_files": len(files),
        "orphans": []
    }
    
    # 收集被引用的文件
    referenced = set()
    
    for file in files:
        links = extract_links(file)
        
        for link in links["wiki_links"]:
            target = resolve_link(kb_root, link, index)
            if target:
                referenced.add(target)
        
        for link in links["md_links"]:
            target = kb_root / link
            if target.exists():
                referenced.add(target)
    
    # 找孤立文件
    exclude_patterns = ["_index", "index", "README", "health-report", "lint-report", "log"]
    
    for file in files:
        rel = file.relative_to(kb_root)
        
        # 排除索引文件
        if any(pattern in file.stem for pattern in exclude_patterns):
            continue
        
        if file not in referenced:
            results["orphans"].append(str(rel))
    
    return results


def check_contradictions(kb_root: Path, files: list[Path]) -> dict[str, Any]:
    """检查矛盾（概念定义不一致）"""
    results = {
        "contradictions": []
    }
    
    # 收集所有概念页的定义
    concepts_dir = kb_root / "wiki" / "concepts"
    if not concepts_dir.exists():
        return results
    
    concept_defs = {}
    
    for concept_file in concepts_dir.glob("*.md"):
        try:
            with open(concept_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 提取定义
            def_match = re.search(r'## 定义\n\n([^\n]+)', content)
            if def_match:
                definition = def_match.group(1).strip()
                concept_defs[concept_file.stem] = {
                    "file": str(concept_file.relative_to(kb_root)),
                    "definition": definition
                }
        except:
            pass
    
    # 检查来源页中的描述是否与概念定义矛盾
    sources_dir = kb_root / "wiki" / "sources"
    if not sources_dir.exists():
        return results
    
    for source_file in sources_dir.glob("*.md"):
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 提取概念引用
            concept_refs = re.findall(r'\[\[concepts/([^\]]+)\]\]', content)
            
            for concept_name in concept_refs:
                if concept_name in concept_defs:
                    # 简单检查：概念名是否在来源中有所述
                    # （实际矛盾检测需要更复杂的语义分析）
                    # 这里只是标记可能需要人工检查的
                    pass
        except:
            pass
    
    # 简化：返回空（完整矛盾检测需要 LLM）
    return results


def check_outdated(kb_root: Path, days: int = 365) -> dict[str, Any]:
    """检查过时内容"""
    results = {
        "outdated": []
    }
    
    sources_dir = kb_root / "wiki" / "sources"
    if not sources_dir.exists():
        return results
    
    threshold = datetime.now() - timedelta(days=days)
    
    for source_file in sources_dir.glob("*.md"):
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read(500)
            
            # 提取日期
            date_match = re.search(r'date:\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', content)
            if date_match:
                date_str = date_match.group(1)
                try:
                    date = datetime.strptime(date_str.replace("/", "-"), "%Y-%m-%d")
                    
                    if date < threshold:
                        results["outdated"].append({
                            "file": str(source_file.relative_to(kb_root)),
                            "date": date_str,
                            "days_old": (datetime.now() - date).days
                        })
                except:
                    pass
        except:
            pass
    
    return results


def check_log_format(kb_root: Path) -> dict[str, Any]:
    """检查日志格式"""
    results = {
        "issues": []
    }
    
    log_file = kb_root / "wiki" / "_meta" / "log.md"
    if not log_file.exists():
        results["issues"].append("日志文件不存在")
        return results
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查格式
        # 每个日志条目应该有：## 日期 | 操作 | 文件
        entries = re.findall(r'##\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*([^\|]+)\s*\|\s*([^\n]+)', content)
        
        if not entries:
            results["issues"].append("日志格式不正确（缺少标准条目）")
        
    except Exception as e:
        results["issues"].append(f"读取日志失败: {e}")
    
    return results


def generate_report(kb_root: Path, results: dict[str, Any]) -> str:
    """生成 lint 报告"""
    report = f"""---
date: {datetime.now().strftime('%Y-%m-%d')}
total_issues: {sum(len(r) for r in results.values() if isinstance(r, list))}
---

# 健康检查报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 总览

| 检查项 | 数量 |
|--------|------|
| 缺失页（死链） | {len(results['broken']['broken_links'])} |
| 孤立页 | {len(results['orphans']['orphans'])} |
| 矛盾 | {len(results['contradictions']['contradictions'])} |
| 过时内容 | {len(results['outdated']['outdated'])} |
| 日志问题 | {len(results['log']['issues'])} |

## 缺失页（{len(results['broken']['broken_links'])} 处）

"""
    
    if results['broken']['broken_links']:
        for broken in results['broken']['broken_links'][:20]:
            report += f"- **{broken['file']}**: `{broken['link']}`\n"
        
        if len(results['broken']['broken_links']) > 20:
            report += f"\n...还有 {len(results['broken']['broken_links']) - 20} 个\n"
    else:
        report += "✅ 无缺失页\n"
    
    report += f"\n## 孤立页（{len(results['orphans']['orphans'])} 处）\n\n"
    
    if results['orphans']['orphans']:
        for orphan in results['orphans']['orphans'][:20]:
            report += f"- {orphan}\n"
        
        if len(results['orphans']['orphans']) > 20:
            report += f"\n...还有 {len(results['orphans']['orphans']) - 20} 个\n"
    else:
        report += "✅ 无孤立页\n"
    
    report += f"\n## 矛盾（{len(results['contradictions']['contradictions'])} 处）\n\n"
    
    if results['contradictions']['contradictions']:
        for c in results['contradictions']['contradictions']:
            report += f"- {c}\n"
    else:
        report += "✅ 无明显矛盾（需人工复核）\n"
    
    report += f"\n## 过时内容（{len(results['outdated']['outdated'])} 处）\n\n"
    
    if results['outdated']['outdated']:
        for old in results['outdated']['outdated']:
            report += f"- **{old['file']}**: {old['days_old']} 天前（{old['date']}）\n"
    else:
        report += "✅ 无过时内容\n"
    
    report += f"\n## 日志检查（{len(results['log']['issues'])} 处）\n\n"
    
    if results['log']['issues']:
        for issue in results['log']['issues']:
            report += f"- {issue}\n"
    else:
        report += "✅ 日志格式正确\n"
    
    report += "\n---\n\n_由 kb lint 自动生成_\n"
    
    return report


@click.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="配置文件路径")
@click.option("--quick", "-q", is_flag=True, help="快速检查（只检查 wiki/）")
@click.option("--fix", "-f", is_flag=True, help="自动修复可修复的问题")
@click.option("--orphans", is_flag=True, help="只检查孤立页")
@click.option("--links", is_flag=True, help="只检查死链")
@click.option("--outdated", is_flag=True, help="只检查过时内容")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def lint(config: str | None, quick: bool, fix: bool,
         orphans: bool, links: bool, outdated: bool, verbose: bool):
    """健康检查
    
    用法：
        kb lint               # 完整检查
        kb lint --quick       # 只检查 wiki/
        kb lint --orphans     # 只检查孤立页
        kb lint --links       # 只检查死链
        kb lint --fix         # 自动修复
    """
    setup_logging("DEBUG" if verbose else "INFO")
    
    cfg = load_config(Path(config) if config else None)
    kb_root = Path(cfg["knowledge_base"]["root"])
    exclude_dirs = cfg["lint"]["exclude_dirs"]
    
    logger.info(f"检查知识库: {kb_root}")
    
    # 构建索引
    index = build_file_index(kb_root, exclude_dirs)
    logger.debug(f"索引 {len(index)} 个文件")
    
    # 确定检查范围
    if quick:
        wiki_dir = kb_root / "wiki"
        files = find_markdown_files(wiki_dir, exclude_dirs)
        logger.info(f"快速模式: 检查 {len(files)} 个 wiki 文档")
    else:
        files = find_markdown_files(kb_root, exclude_dirs)
        logger.info(f"全量检查: {len(files)} 个文档")
    
    if not files:
        logger.warning("没有文件需要检查")
        return
    
    # 执行检查
    results = {
        "broken": {"broken_links": [], "files_with_broken": defaultdict(list), "total_links": 0},
        "orphans": {"orphans": [], "total_files": 0},
        "contradictions": {"contradictions": []},
        "outdated": {"outdated": []},
        "log": {"issues": []}
    }
    
    if links or not (orphans or outdated):
        logger.info("检查缺失页...")
        results["broken"] = check_broken_links(kb_root, files, index)
        logger.info(f"发现 {len(results['broken']['broken_links'])} 个缺失页")
    
    if orphans or not (links or outdated):
        logger.info("检查孤立页...")
        results["orphans"] = check_orphans(kb_root, files, index)
        logger.info(f"发现 {len(results['orphans']['orphans'])} 个孤立页")
    
    if outdated or not (links or orphans):
        logger.info("检查过时内容...")
        results["outdated"] = check_outdated(kb_root)
        logger.info(f"发现 {len(results['outdated']['outdated'])} 个过时来源")
    
    # 矛盾检测（简化）
    results["contradictions"] = check_contradictions(kb_root, files)
    
    # 日志检查
    results["log"] = check_log_format(kb_root)
    
    # 生成报告
    report = generate_report(kb_root, results)
    
    report_file = kb_root / "wiki" / "_meta" / "lint-report.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.success(f"报告已保存: {report_file}")
    
    # 控制台输出
    click.echo(f"""
健康检查完成
=============

📊 总览:
  - 检查文档: {len(files)}
  - 链接数: {results['broken']['total_links']}
  - 缺失页: {len(results['broken']['broken_links'])}
  - 孤立页: {len(results['orphans']['orphans'])}
  - 过时内容: {len(results['outdated']['outdated'])}

报告: {report_file}
""")