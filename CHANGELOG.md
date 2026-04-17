# CHANGELOG

## [2.0.0] - 2026-04-17

### 新增功能（New Features）

#### 链接抓取（Link Fetching）
- `wiki fetch` 命令：自动识别平台抓取内容
- 支持平台：X/Twitter、微博（Weibo）、通用网页
- 零依赖：Twitter和微博抓取无需额外安装
- 可选平台：微信公众号（需playwright）、小红书（需aiohttp）

#### 图谱可视化（Graph Visualization）
- `wiki graph` 命令：生成交互式知识图谱HTML
- 使用vis.js：支持点击、搜索、过滤
- 核心节点高亮：God Nodes（引用数Top 10）用金色标记
- `wiki god-nodes` 命令：单独显示核心节点列表

#### 健康检查（Health Check）
- `wiki health` 命令：一键诊断知识库状态
- 检查项：Python版本、依赖、目录、缓存、备份、统计
- 提供具体修复建议

#### 文档完善（Documentation）
- troubleshooting.md：常见问题解答（中英双语）
- README.md：中英文对照格式
- getting-started.md：更新为双语版本

### 改进（Improvements）

- 命令行版本升级：0.1.0 → 2.0.0
- cli.py 整合9个子命令（原5个）
- 代码结构：模块化拆分（graph.py、fetch.py、health.py）

---

## [0.1.0] - 2026-03-20

### 首次发布（Initial Release）

- `wiki init`: 初始化知识库目录结构
- `wiki ingest`: 处理 raw/ 素材，生成 sources/、concepts/、entities/
- `wiki query`: 搜索知识库，生成 answers 存 outputs/
- `wiki lint`: 健康检查（矛盾/孤立页/缺失页）
- `wiki status`: 统计信息 + 最近操作
- YAML配置格式（config/kb.yaml）
- 支持外部数据目录
- Obsidian兼容（markdown + wikilinks）
- Streamlit Web UI（基础版）

---

## Roadmap（规划）

- [ ] Web UI 完善（完整功能）
- [ ] Vector search（大规模知识库）
- [ ] Multi-language support
- [ ] Import from Notion/Roam
- [ ] Export to static site