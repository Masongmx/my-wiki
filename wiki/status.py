#!/usr/bin/env python3
"""kb status: 知识库状态统计

显示：
1. 统计信息（文件数、概念数、实体数等）
2. 最近操作（从 _meta/log.md 读取）
"""

import click
import yaml
from pathlib import Path
from loguru import logger
import re
from datetime import datetime
from typing import Optional, List


def setup_logging(level: str = "INFO"):
    logger.remove()
    logger.add(
        sink=lambda msg: click.echo(msg, nl=False),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True
    )


def load_config(config_path: Optional[Path] = None) -> dict:
    """加载配置"""
    if config_path is None:
        kb_root = Path(__file__).parent.parent
        config_path = kb_root / "config" / "kb.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def count_files(directory: Path) -> int:
    """统计目录中的 .md 文件数"""
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.md")))


def get_file_list(directory: Path, limit: int = 10) -> List[str]:
    """获取文件列表"""
    if not directory.exists():
        return []
    
    files = sorted(directory.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [f.stem for f in files[:limit]]


def read_recent_logs(log_file: Path, limit: int = 5) -> List[dict]:
    """读取最近操作日志"""
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 提取日志条目
        # 格式：## 日期 | 操作 | 文件
        entries = re.findall(
            r'##\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*([^\|]+)\s*\|\s*([^\n]+)',
            content
        )
        
        logs = []
        for entry in entries[-limit:]:
            logs.append({
                "time": entry[0],
                "action": entry[1].strip(),
                "file": entry[2].strip()
            })
        
        return logs[::-1]  # 最新在前
    except Exception as e:
        logger.warning(f"读取日志失败: {e}")
        return []


def get_kb_stats(kb_root: Path) -> dict:
    """获取知识库统计"""
    stats = {
        "sources": count_files(kb_root / "wiki" / "sources"),
        "concepts": count_files(kb_root / "wiki" / "concepts"),
        "entities": count_files(kb_root / "wiki" / "entities"),
        "outputs": count_files(kb_root / "wiki" / "outputs"),
        "articles": count_files(kb_root / "wiki" / "articles"),
        "raw_articles": count_files(kb_root / "raw" / "articles"),
        "raw_pdfs": count_files(kb_root / "raw" / "pdfs"),
        "raw_transcripts": count_files(kb_root / "raw" / "transcripts"),
    }
    
    # 总计
    stats["total_wiki"] = stats["sources"] + stats["concepts"] + stats["entities"] + stats["outputs"]
    stats["total_raw"] = stats["raw_articles"] + stats["raw_pdfs"] + stats["raw_transcripts"]
    
    return stats


@click.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="配置文件路径")
@click.option("--recent", "-r", is_flag=True, help="显示最近操作")
@click.option("--sources", "-s", is_flag=True, help="显示来源列表")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def status(config: Optional[str], recent: bool, sources: bool, verbose: bool):
    """知识库状态
    
    用法：
        kb status              # 统计信息
        kb status --recent     # 最近操作
        kb status --sources    # 来源列表
    """
    setup_logging("DEBUG" if verbose else "INFO")
    
    cfg = load_config(Path(config) if config else None)
    kb_root = Path(cfg["knowledge_base"].get("root") or cfg["knowledge_base"].get("data_dir", "./data"))
    
    # 统计信息
    stats = get_kb_stats(kb_root)
    
    click.echo("""
知识库状态
==========

📊 统计信息

Wiki 内容:
""")
    
    click.echo(f"  来源页 (sources/):   {stats['sources']}")
    click.echo(f"  概念页 (concepts/):  {stats['concepts']}")
    click.echo(f"  实体页 (entities/):  {stats['entities']}")
    click.echo(f"  产出页 (outputs/):   {stats['outputs']}")
    click.echo(f"  文章页 (articles/):  {stats['articles']}")
    click.echo(f"  总计:                {stats['total_wiki']}")
    
    click.echo("""
Raw 素材:
""")
    click.echo(f"  文章 (articles/):    {stats['raw_articles']}")
    click.echo(f"  PDF (pdfs/):         {stats['raw_pdfs']}")
    click.echo(f"  转录 (transcripts/): {stats['raw_transcripts']}")
    click.echo(f"  总计:                {stats['total_raw']}")
    
    # 最近操作
    if recent or verbose:
        log_file = kb_root / "wiki" / "_meta" / "log.md"
        logs = read_recent_logs(log_file, 5)
        
        click.echo("""
📅 最近操作
""")
        
        if logs:
            for log in logs:
                click.echo(f"  {log['time']} | {log['action']} | {log['file']}")
        else:
            click.echo("  （无操作记录）")
    
    # 来源列表
    if sources or verbose:
        sources_dir = kb_root / "wiki" / "sources"
        source_list = get_file_list(sources_dir, 10)
        
        click.echo("""
📚 来源列表
""")
        
        if source_list:
            for src in source_list:
                click.echo(f"  - {src}")
        else:
            click.echo("  （无来源）")
    
    # 健康状态（从 lint-report 读取）
    lint_file = kb_root / "wiki" / "_meta" / "lint-report.md"
    if lint_file.exists():
        try:
            with open(lint_file, "r", encoding="utf-8") as f:
                content = f.read(500)
            
            # 提取 total_issues
            match = re.search(r'total_issues:\s*(\d+)', content)
            if match:
                total_issues = int(match.group(1))
                
                click.echo(f"""
🔍 健康状态
""")
                
                if total_issues == 0:
                    click.echo("  ✅ 健康（无问题）")
                elif total_issues < 5:
                    click.echo(f"  ⚠️ 轻度问题（{total_issues} 个）")
                else:
                    click.echo(f"  ❌ 需要修复（{total_issues} 个问题）")
        except:
            pass