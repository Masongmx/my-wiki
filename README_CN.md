<p align="center">
  <h1 align="center">📝 My Wiki</h1>
  <p align="center">
    <strong>LLM 驱动的个人知识库</strong>
  </p>
  <p align="center">
    <a href="README_CN.md">中文</a> | <a href="README.md">English</a>
  </p>
  <p align="center">
    <a href="#特性">特性</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="#使用方法">使用方法</a> •
    <a href="#架构设计">架构设计</a> •
    <a href="#贡献">贡献</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  </p>
</p>

---

## 什么是 My Wiki？

**My Wiki** 是一个由 LLM 驱动的个人知识管理系统。与传统 RAG 系统每次查询都重新检索不同，My Wiki 维护一个**持久化、结构化的 wiki**，让知识持续积累。

### 传统 RAG 的问题

```
传统 RAG：
  上传文件 → 检索片段 → 生成答案
  下次问题？重新开始。没有积累。
```

### 我们的方式

```
My Wiki：
  新素材 → 提取知识 → 整合到 wiki
  下次问题？搜索 wiki。知识持续累积。
```

**核心洞察**：与其每次都从原始文档检索，不如让 LLM 构建并维护一个结构化的 wiki。知识被编译一次，持续复用。

---

## 特性

- 🔄 **Ingest（摄入）** — 自动从文章、PDF、转录中提取概念、实体、洞察
- 🔍 **Query（查询）** — 用自然语言查询知识库
- 🏥 **Lint（检查）** — 健康检查：矛盾、孤立页、缺失链接
- 📊 **Status（状态）** — 追踪知识库增长
- 🔗 **双向链接** — 概念自动双向关联
- 📝 **Obsidian 兼容** — 无缝配合 Obsidian 可视化

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Masongmx/my-wiki.git
cd my-wiki

# 安装依赖
pip install click pyyaml loguru openai
```

### 配置

创建 `config/kb.yaml`：

```yaml
knowledge_base:
  # 数据目录（存放 raw/、wiki/）
  data_dir: ./data
  
  # 或使用绝对路径指向外部目录
  # data_dir: /path/to/your/knowledge-base
  
llm:
  provider: openai  # 或 bailian、anthropic 等
  model: gpt-4
  api_key: YOUR_API_KEY  # 或设置环境变量
  base_url: https://api.openai.com/v1  # 可选
```

**支持外部数据目录**：
- 可以把数据目录放在项目外部
- 多个环境共享同一份数据
- 方便备份和迁移

### 初始化

```bash
# 初始化知识库
wiki init

# 处理第一篇文章
wiki ingest raw/articles/my-article.md

# 查询知识
wiki query "主要概念是什么？"
```

---

## 使用方法

### Ingest（处理素材）

```bash
# 处理单个文件
wiki ingest raw/articles/article.md

# 处理整个目录
wiki ingest raw/articles/

# 预览（不写入）
wiki ingest raw/articles/article.md --dry-run
```

**处理流程：**
1. 读取素材内容
2. 提取关键洞察 → `wiki/sources/`
3. 提取概念 → `wiki/concepts/`
4. 提取实体 → `wiki/entities/`
5. 建立双向链接
6. 更新 `wiki/_index.md`
7. 记录到 `wiki/_meta/log.md`

### Query（查询）

```bash
# 提问
wiki query "什么是 Agent Operating System?"

# 保存答案供后续参考
wiki query "对比 Skill 和 MCP 的区别" --save
```

**支持的问题类型：**
| 类型 | 示例 | 输出 |
|------|------|------|
| 定义类 | "什么是 X？" | 定义 + 核心要点 |
| 对比类 | "X 和 Y 的区别？" | 对比表格 |
| 关系类 | "X 和 Y 有什么关系？" | 关系描述 |
| 列举类 | "有哪些 X？" | 列表 |

### Lint（健康检查）

```bash
# 完整检查
wiki lint

# 快速检查（仅 wiki/）
wiki lint --quick

# 检查特定问题
wiki lint --orphans    # 孤立页
wiki lint --outdated   # 过时内容
```

### Status（统计）

```bash
# 查看统计
wiki status

# 显示最近活动
wiki status --recent
```

---

## 架构设计

```
knowledge-base/
├── raw/                  # 原始素材（只读）
│   ├── articles/         # 文章
│   ├── pdfs/             # PDF 文档
│   └── transcripts/      # 音频/视频转录
│
├── wiki/                 # LLM 维护的结构化内容
│   ├── concepts/         # 概念页（定义）
│   ├── entities/         # 实体页（人物、项目、工具）
│   ├── sources/          # 来源页（摘要）
│   ├── outputs/          # 产出页（分析）
│   ├── _index.md         # 全局索引
│   └── _meta/
│       ├── log.md        # 操作日志
│       └── lint-report.md
│
└── config/
    └── kb.yaml           # 配置
```

### 三层分离

| 层 | 谁写 | 谁读 | 作用 |
|----|------|------|------|
| `raw/` | 你（策展）| LLM（读取）| 原始素材 |
| `wiki/` | LLM（生成）| 你（读取）| 结构化知识 |
| `outputs/` | LLM（生成）| 你（读取）| 你的分析 |

---

## 设计理念

### 6 条原则

1. **raw 只读** — 原始素材保持原貌
2. **wiki LLM 写** — LLM 保证一致性
3. **人只读 wiki** — 避免冲突
4. **每次操作都沉淀** — ingest 结果、query 答案都持久化
5. **增量更新** — 新素材更新现有页面
6. **双向链接** — 概念互相引用

---

## 与 Obsidian 配合

My Wiki 生成的 markdown 文件可以无缝配合 [Obsidian](https://obsidian.md)：

1. 打开 Obsidian
2. 选择 `knowledge-base` 文件夹作为 vault
3. 浏览 `wiki/concepts/`、`wiki/entities/` 等
4. 点击链接探索知识图谱
5. 使用 Graph View 可视化连接

---

## 示例

参见 `examples/demo-kb/`，包含：
- 示例文章
- 生成的概念和实体
- 示例查询和输出

---

## 路线图

- [ ] Web UI 浏览 wiki
- [ ] 大规模知识库的向量搜索
- [ ] 多语言支持
- [ ] 从 Notion、Roam 等导入
- [ ] 导出为静态网站

---

## 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md)。

---

## 致谢

灵感来自 [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 方法论。

---

## 许可证

[MIT License](LICENSE)