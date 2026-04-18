#!/usr/bin/env python3
"""wiki health: 一键诊断知识库状态

功能：
1. 环境检测（Python、依赖）
2. 目录检测（raw/wiki/log）
3. 缓存状态
4. 备份状态
5. 知识库统计
6. 配置状态
"""

import click
import sys
import subprocess
from pathlib import Path
import json


def check_python_version() -> dict[str, str | None]:
    """检查Python版本"""
    version = sys.version_info
    return {
        "status": "✅" if version >= (3, 8) else "❌",
        "message": f"Python {version.major}.{version.minor}.{version.micro}",
        "detail": "需要 3.8+" if version < (3, 8) else None
    }


def check_dependency(package: str) -> dict[str, str | None]:
    """检查Python依赖"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {package}"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            return {"status": "✅", "message": f"{package} 已安装"}
        else:
            return {"status": "❌", "message": f"{package} 未安装", "detail": f"pip install {package}"}
    except Exception as e:
        return {"status": "❌", "message": f"{package} 检查失败", "detail": str(e)}


def check_directory(dir_path: Path, name: str) -> dict[str, str | None]:
    """检查目录"""
    if dir_path.exists():
        count = len(list(dir_path.glob("*")))
        return {"status": "✅", "message": f"{name} 存在 ({count} 个文件)"}
    else:
        return {"status": "❌", "message": f"{name} 不存在", "detail": str(dir_path)}


def check_cache(raw_dir: Path) -> dict[str, str | None]:
    """检查缓存"""
    cache_file = raw_dir / "_sync_cache.json"
    
    if not cache_file.exists():
        return {"status": "⚠️", "message": "缓存不存在（首次运行正常）"}
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        count = len(data.get("files", {}))
        last_sync = data.get("last_sync", "未知")
        
        return {
            "status": "✅",
            "message": f"缓存正常 ({count} 条)",
            "detail": f"最后同步: {last_sync}"
        }
    except Exception as e:
        return {"status": "❌", "message": "缓存读取失败", "detail": str(e)}


def check_backups(log_dir: Path) -> dict[str, str | None]:
    """检查备份"""
    backup_files = list(log_dir.glob("sync_cache_backup_*.json"))
    
    if not backup_files:
        return {"status": "⚠️", "message": "无备份文件"}
    
    latest = max(backup_files, key=lambda f: f.stat().st_mtime)
    return {
        "status": "✅",
        "message": f"备份正常 ({len(backup_files)} 个)",
        "detail": f"最新: {latest.name}"
    }


def get_kb_stats(raw_dir: Path, wiki_dir: Path) -> dict[str, int]:
    """统计知识库"""
    raw_count = len(list(raw_dir.glob("*.md")))
    wiki_count = len(list(wiki_dir.glob("*.md")))
    
    # 统计wiki文章类型
    concepts = len(list(wiki_dir.glob("concepts/*.md")))
    entities = len(list(wiki_dir.glob("entities/*.md")))
    sources = len(list(wiki_dir.glob("sources/*.md")))
    
    return {
        "raw": raw_count,
        "wiki": wiki_count,
        "concepts": concepts,
        "entities": entities,
        "sources": sources
    }


@click.command()
@click.pass_obj
def health(config: dict) -> None:
    """一键诊断知识库状态
    
    \b
    检查项：
    - Python版本和依赖
    - 目录结构
    - 缓存和备份
    - 知识库统计
    """
    kb_root = Path(config["knowledge_base"]["root"])
    raw_dir = kb_root / "raw"
    wiki_dir = kb_root / "wiki"
    log_dir = kb_root / "wiki" / "_meta"
    
    click.echo("\n🏥 知识库健康检查报告\n")
    
    # 环境检测
    click.echo("### 环境")
    python_check = check_python_version()
    click.echo(f"  {python_check['status']} {python_check['message']}")
    
    # 依赖检测
    dependencies = ["click", "yaml", "loguru"]
    for dep in dependencies:
        dep_check = check_dependency(dep)
        click.echo(f"  {dep_check['status']} {dep_check['message']}")
    
    # 目录检测
    click.echo("\n### 目录")
    for name, path in [("Raw", raw_dir), ("Wiki", wiki_dir), ("Log", log_dir)]:
        dir_check = check_directory(path, name)
        click.echo(f"  {dir_check['status']} {dir_check['message']}")
    
    # 缓存检测
    click.echo("\n### 缓存")
    cache_check = check_cache(raw_dir)
    click.echo(f"  {cache_check['status']} {cache_check['message']}")
    if cache_check.get("detail"):
        click.echo(f"     └─ {cache_check['detail']}")
    
    # 备份检测
    click.echo("\n### 备份")
    backup_check = check_backups(log_dir)
    click.echo(f"  {backup_check['status']} {backup_check['message']}")
    if backup_check.get("detail"):
        click.echo(f"     └─ {backup_check['detail']}")
    
    # 知识库统计
    click.echo("\n### 统计")
    stats = get_kb_stats(raw_dir, wiki_dir)
    click.echo(f"  Raw条目: {stats['raw']}")
    click.echo(f"  Wiki文章: {stats['wiki']}")
    click.echo(f"  - Concepts: {stats['concepts']}")
    click.echo(f"  - Entities: {stats['entities']}")
    click.echo(f"  - Sources: {stats['sources']}")
    
    # 总结
    click.echo("\n---")
    issues = []
    for check in [python_check]:
        if "❌" in check["status"]:
            issues.append(check.get("detail", check["message"]))
    
    if issues:
        click.echo(f"💡 建议:")
        for issue in issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("✅ 知识库健康状态良好")