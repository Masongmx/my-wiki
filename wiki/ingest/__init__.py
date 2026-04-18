"""wiki.ingest - 处理 raw/ 素材到 wiki/

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
from typing import Any

from .llm import get_llm_client
from .processor import run_ingest, process_file, detect_source_type, extract_metadata


def setup_logging(level: str = "INFO") -> None:
    """配置日志"""
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


# 导出公共接口
__all__ = [
    "setup_logging",
    "load_config",
    "get_llm_client",
    "run_ingest",
    "process_file",
    "detect_source_type",
    "extract_metadata",
]


@click.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--config", "-c", type=click.Path(exists=True), help="配置文件路径")
@click.option("--batch", "-b", is_flag=True, help="批量处理（不交互）")
@click.option("--dry-run", "-d", is_flag=True, help="预览不写入")
@click.option("--force", "-f", is_flag=True, help="强制重新处理")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def ingest(
    file: str | None,
    config: str | None,
    batch: bool,
    dry_run: bool,
    force: bool,
    verbose: bool
) -> None:
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

    # 处理文件
    count = run_ingest(kb_root, raw_dir, client, model, file, force, dry_run)

    if count > 0:
        logger.success(f"处理完成！共处理 {count} 个文件")


# CLI 入口
if __name__ == "__main__":
    ingest()