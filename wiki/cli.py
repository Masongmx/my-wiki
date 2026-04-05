#!/usr/bin/env python3
"""wiki: Knowledge Base CLI

整合 5 个子命令：
- wiki init: 初始化知识库目录结构
- wiki ingest: 处理 raw/ 素材，生成 sources/、concepts/、entities/
- wiki query: 搜索知识库，生成 answers 存 outputs/
- wiki lint: 健康检查（矛盾/孤立页/缺失页）
- wiki status: 统计信息 + 最近操作
"""

import click
import sys
from pathlib import Path

# 导入子模块
sys.path.insert(0, str(Path(__file__).parent))

# 导入命令函数
from init import init
from ingest import ingest
from query import query
from lint import lint
from status import status


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Knowledge Base CLI
    
    用法：
        wiki init              # 初始化知识库
        wiki ingest <file>     # 处理素材
        wiki query "问题"      # 查询知识库
        wiki lint              # 健康检查
        wiki status            # 查看状态
    """
    pass


# 注册子命令
cli.add_command(init)
cli.add_command(ingest)
cli.add_command(query)
cli.add_command(lint)
cli.add_command(status)


if __name__ == "__main__":
    cli()