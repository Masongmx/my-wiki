#!/usr/bin/env python3
"""wiki graph: 生成交互式知识图谱

功能：
1. 从 _backlinks.json 提取节点和边
2. 使用 vis.js 生成交互式 HTML
3. 支持点击节点跳转到文章
4. 支持搜索、过滤、社区发现
"""

import click
import json
from pathlib import Path
from typing import Dict, List, Any
import webbrowser


def load_backlinks(wiki_dir: Path) -> Dict[str, List[str]]:
    """加载反向链接数据"""
    backlinks_file = wiki_dir / "_backlinks.json"
    if not backlinks_file.exists():
        return {}
    
    with open(backlinks_file, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_nodes_and_edges(backlinks: Dict[str, List[str]]) -> tuple:
    """提取节点和边数据"""
    nodes = []
    edges = []
    
    # 所有文章作为节点
    all_articles = set(backlinks.keys())
    for inbound_list in backlinks.values():
        for article in inbound_list:
            all_articles.add(article.replace(".md", ""))
    
    # 创建节点
    for article in sorted(all_articles):
        if article == "...":  # 忽略占位符
            continue
        inbound_count = len(backlinks.get(article, []))
        nodes.append({
            "id": article,
            "label": article.replace("-概览", ""),
            "group": article.split("-")[0] if "-" in article else "other",
            "value": inbound_count + 1,  # 节点大小
            "title": f"{article}\n引用数: {inbound_count}"
        })
    
    # 创建边（反向链接）
    for target, sources in backlinks.items():
        for source in sources:
            source_id = source.replace(".md", "")
            if source_id != "..." and target != "...":
                edges.append({
                    "from": source_id,
                    "to": target,
                    "arrows": "to"
                })
    
    return nodes, edges


def generate_graph_html(nodes: List[Dict], edges: List[Dict], wiki_dir: Path) -> str:
    """生成图谱HTML"""
    
    # 按引用数排序，找出God Nodes（核心节点）
    god_nodes = sorted(nodes, key=lambda x: x.get("value", 0), reverse=True)[:10]
    god_node_ids = [n["id"] for n in god_nodes]
    
    # God Nodes用金色标记
    for node in nodes:
        if node["id"] in god_node_ids:
            node["color"] = "#FFD700"  # 金色
            node["font"] = {"color": "#000", "size": 16}
    
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>知识图谱 | Knowledge Graph</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 0;
        }
        #network {
            width: 100%;
            height: 100vh;
            border: none;
        }
        #controls {
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        #search {
            width: 200px;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        #legend {
            position: absolute;
            bottom: 10px;
            left: 10px;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 5px;
        }
    </style>
</head>
<body>
    <div id="controls">
        <input type="text" id="search" placeholder="搜索节点... | Search nodes...">
        <button onclick="fitToScreen()">适应屏幕</button>
    </div>
    <div id="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #FFD700;"></div>
            <span>核心节点 (Top 10)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #97c2fc;"></div>
            <span>普通节点</span>
        </div>
    </div>
    <div id="network"></div>
    
    <script>
        // 节点和边数据
        const nodes = new vis.DataSet(%s);
        const edges = new vis.DataSet(%s);
        
        // 网络配置
        const container = document.getElementById('network');
        const data = { nodes: nodes, edges: edges };
        const options = {
            nodes: {
                shape: 'dot',
                scaling: {
                    min: 10,
                    max: 30,
                    label: {
                        enabled: true,
                        min: 12,
                        max: 20
                    }
                },
                font: {
                    face: 'Arial',
                    color: '#333'
                }
            },
            edges: {
                smooth: {
                    type: 'continuous'
                },
                arrows: {
                    to: { enabled: true, scaleFactor: 0.5 }
                },
                color: { inherit: 'from' }
            },
            physics: {
                stabilization: {
                    iterations: 200
                },
                barnesHut: {
                    gravitationalConstant: -3000,
                    centralGravity: 0.3,
                    springLength: 100
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            }
        };
        
        // 创建网络
        const network = new vis.Network(container, data, options);
        
        // 点击节点跳转到文章
        network.on("click", function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const articlePath = nodeId + ".md";
                // 尝试打开文章（需要Obsidian或编辑器）
                // window.open(articlePath, '_blank');
                console.log("Clicked:", nodeId);
            }
        });
        
        // 搜索功能
        document.getElementById('search').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            nodes.forEach(function(node) {
                const label = node.label.toLowerCase();
                const id = node.id.toLowerCase();
                if (searchTerm === '' || label.includes(searchTerm) || id.includes(searchTerm)) {
                    nodes.update({ id: node.id, hidden: false });
                } else {
                    nodes.update({ id: node.id, hidden: true });
                }
            });
        });
        
        // 适应屏幕
        function fitToScreen() {
            network.fit({
                animation: {
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }
        
        // 初始适应屏幕
        network.once("stabilized", function() {
            fitToScreen();
        });
    </script>
</body>
</html>
"""
    
    # 填充节点和边数据
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)
    
    return html_template % (nodes_json, edges_json)


@click.command()
@click.option("--open", "open_browser", is_flag=True, help="生成后打开浏览器")
@click.pass_obj
def graph(config: dict, open_browser: bool):
    """生成交互式知识图谱
    
    \b
    功能：
    - 可视化知识关联
    - 点击节点查看文章
    - 搜索过滤节点
    - 自动发现核心节点（God Nodes）
    """
    kb_root = Path(config["knowledge_base"]["root"])
    wiki_dir = kb_root / "wiki"
    
    if not wiki_dir.exists():
        click.echo(f"❌ Wiki目录不存在: {wiki_dir}")
        return
    
    # 加载反向链接
    backlinks = load_backlinks(wiki_dir)
    
    if not backlinks:
        click.echo("❌ 未找到 _backlinks.json，请先运行 wiki ingest")
        return
    
    click.echo("📊 正在生成知识图谱...")
    
    # 提取节点和边
    nodes, edges = extract_nodes_and_edges(backlinks)
    
    click.echo(f"  - 节点数: {len(nodes)}")
    click.echo(f"  - 连接数: {len(edges)}")
    
    # 生成HTML
    html_content = generate_graph_html(nodes, edges, wiki_dir)
    
    # 保存到 wiki/graph.html
    graph_file = wiki_dir / "graph.html"
    with open(graph_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    click.echo(f"✅ 图谱已生成: {graph_file}")
    
    # 列出God Nodes
    click.echo("\n🌟 核心节点 (Top 10):")
    god_nodes = sorted(nodes, key=lambda x: x.get("value", 0), reverse=True)[:10]
    for i, node in enumerate(god_nodes, 1):
        click.echo(f"  {i}. {node['label']} (引用数: {node['value'] - 1})")
    
    # 打开浏览器
    if open_browser:
        webbrowser.open(str(graph_file))


@click.command()
@click.option("--top", default=10, help="显示前N个核心节点")
@click.pass_obj
def god_nodes(config: dict, top: int):
    """显示核心节点（引用数最多的文章）
    
    \b
    功能：
    - 分析反向链接
    - 按引用数排序
    - 显示Top N核心文章
    """
    kb_root = Path(config["knowledge_base"]["root"])
    wiki_dir = kb_root / "wiki"
    
    backlinks = load_backlinks(wiki_dir)
    
    if not backlinks:
        click.echo("❌ 未找到反向链接数据")
        return
    
    # 统计每个文章的引用数
    inbound_counts = {}
    for target, sources in backlinks.items():
        inbound_counts[target] = len(sources)
    
    # 按引用数排序
    sorted_articles = sorted(inbound_counts.items(), key=lambda x: x[1], reverse=True)[:top]
    
    click.echo(f"🌟 核心节点 (Top {top}):\n")
    for i, (article, count) in enumerate(sorted_articles, 1):
        article_name = article.replace("-概览", "").replace(".md", "")
        click.echo(f"  {i:2d}. {article_name:30s} (引用: {count})")