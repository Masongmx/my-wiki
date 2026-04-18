#!/usr/bin/env python3
"""wiki: Knowledge Base CLI

整合 9 个子命令（v2.0）：
- wiki init: 初始化知识库目录结构
- wiki ingest: 处理 raw/ 素材，生成 sources/、concepts/、entities/
- wiki query: 搜索知识库，生成 answers 存 outputs/
- wiki lint: 健康检查（矛盾/孤立页/缺失页）
- wiki status: 统计信息 + 最近操作
- wiki graph: 生成交互式知识图谱
- wiki god-nodes: 显示核心节点（引用数Top 10）
- wiki fetch: 抓取链接内容（Twitter/微博/网页）
- wiki health: 一键诊断知识库状态
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
from graph import graph, god_nodes
from fetch import fetch
from health import health


@click.group()
@click.version_option(version="2.0.0")
def cli() -> None:
    """Knowledge Base CLI | 知识库管理命令行工具
    
    \b
    核心命令（Core commands）：
    - wiki init: 初始化知识库
    - wiki ingest: 处理素材
    - wiki query: 查询知识
    - wiki lint: 健康检查
    - wiki status: 统计信息
    
    \b
    新增命令（New in v2.0）：
    - wiki graph: 图谱可视化
    - wiki god-nodes: 核心节点发现
    - wiki fetch: 抓取链接
    - wiki health: 一键诊断
    
    \b
    使用示例（Examples）：
    wiki init
    wiki ingest raw/articles/
    wiki query "什么是Agent?"
    wiki graph --open
    wiki fetch "https://x.com/user/status/123"
    """
    pass


# 注册子命令
cli.add_command(init)
cli.add_command(ingest)
cli.add_command(query)
cli.add_command(lint)
cli.add_command(status)
cli.add_command(graph)
cli.add_command(god_nodes)
cli.add_command(fetch)
cli.add_command(health)


if __name__ == "__main__":
    cli()
