# My Wiki：打造你的 LLM 知识大脑

> 面向小白的完整指南：从零开始构建个人知识库

---

## 一、这个项目能帮你做什么？

### 你是否遇到过这些问题？

❌ **收藏了无数文章，但从来不看**
- 微信收藏、浏览器书签、笔记软件...到处都是"以后再看"的内容
- 真正需要时，找不到了

❌ **看了很多内容，但记不住**
- 读完一篇好文章，过几天就忘了
- 想用时想不起来在哪看过

❌ **问 AI 问题，每次都要重新解释背景**
- "我之前跟你说过..."
- "上次我们讨论过..."
- 每次对话都是新的，没有积累

❌ **知识散落在各处，无法串联**
- 笔记在 Notion
- 文章在微信收藏
- PDF 在电脑某个文件夹
- 想找关联信息，要翻好几个地方

---

### My Wiki 的解决方案

✅ **统一入口** — 所有素材放进一个地方，自动整理

✅ **自动提炼** — LLM 帮你提取关键概念、人物、要点

✅ **结构沉淀** — 知识变成可搜索、可关联的结构化 wiki

✅ **持续复用** — 每次查询都在积累，知识越用越丰富

---

### 实际例子

**场景**：你读了一篇《Claude Code 源码架构深度解析》

**传统方式**：
- 读完 → 觉得很有用 → 收藏 → 忘了

**My Wiki 方式**：
```bash
# 1. 放入素材
把 PDF 放到 raw/pdfs/

# 2. 一键处理
wiki ingest raw/pdfs/claude-code-analysis.pdf

# 3. 自动生成
- wiki/sources/Claude-Code源码分析.md（摘要）
- wiki/concepts/Agent-Operating-System.md（概念页）
- wiki/concepts/Prompt编排.md（概念页）
- wiki/entities/Claude-Code.md（实体页）

# 4. 随时查询
wiki query "Claude Code 有哪些设计原则？"
# → 返回答案 + 相关概念链接
```

**结果**：
- PDF 的核心内容被提炼成结构化知识
- 相关概念自动关联
- 下次查相关内容，直接从 wiki 搜索
- 每次查询让 wiki 变得更丰富

---

## 二、核心原理：为什么这样设计？

### 传统知识管理的问题

大部分人管理知识的方式是 **"囤积"**：
- 收藏文章
- 做笔记
- 打标签

问题在于：**知识没有被激活**。每次要用，都要重新阅读、重新理解。

### RAG 的问题

很多人用 AI 的方式是 **RAG（检索增强生成）**：
- 上传文档
- 问问题时检索相关片段
- AI 生成答案

问题在于：**没有积累**。每次问问题都要重新检索、重新理解。下次问类似问题，又要重来。

### My Wiki 的方式

核心思想：**让 LLM 维护一个结构化的知识库**，而不是每次都从原始文档检索。

```
传统方式：
  文档 → 每次重新理解 → 答案

RAG 方式：
  文档 → 检索片段 → 每次重新理解 → 答案

My Wiki 方式：
  文档 → 编译成 wiki → 查询 wiki → 答案
         ↑                ↓
         └──── 知识持续积累 ────┘
```

**关键差异**：
- 知识被**编译**一次，持续复用
- 每次查询都在**积累**，而不是消耗
- wiki 是一个**活的知识体**，越用越丰富

---

## 三、架构设计：三层分离

My Wiki 采用三层架构，保证清晰和可维护：

### 第一层：raw/（原始素材）

**你负责**：把素材放进这里

**内容**：
- 文章（从网页保存）
- PDF 文档
- 音频/视频转录

**原则**：只读不改，保留原貌

### 第二层：wiki/（结构化知识）

**LLM 负责**：自动生成和维护

**内容**：
- `concepts/` — 概念页（什么是 X）
- `entities/` — 实体页（人物、项目、工具）
- `sources/` — 来源页（原始素材摘要）
- `outputs/` — 产出页（你的分析、对比）

**原则**：你不直接编辑，让 LLM 维护

### 第三层：你（用户）

**你的角色**：
- 策展 raw/（放什么素材）
- 查询 wiki/（问什么问题）
- 审阅结果（是否准确）

---

### 为什么这样设计？

| 问题 | 解决方案 |
|------|----------|
| 素材太多，没法整理 | 只需要"放"，LLM 自动整理 |
| 笔记容易乱 | wiki 由 LLM 维护，保证一致性 |
| 知识找不到 | 结构化 + 索引，快速定位 |
| 关联发现不了 | 双向链接，自动关联 |

---

## 四、安装部署：从零开始

### 前置要求

- Python 3.8+
- 一个 LLM API（OpenAI、Anthropic、或国内大模型）

### 方式一：直接使用（推荐新手）

```bash
# 1. 克隆项目
git clone https://github.com/Masongmx/my-wiki.git
cd my-wiki

# 2. 安装依赖
pip install click pyyaml loguru openai

# 3. 配置 API
# 复制配置模板
cp config/kb.yaml.example config/kb.yaml

# 编辑配置文件，填入你的 API key
# api_key: sk-your-api-key
```

### 方式二：作为 Python 包安装

```bash
# 安装
pip install git+https://github.com/Masongmx/my-wiki.git

# 使用
wiki init
wiki ingest raw/articles/xxx.md
wiki query "你的问题"
```

---

### 配置文件详解

`config/kb.yaml`:

```yaml
knowledge_base:
  root: /path/to/your/knowledge-base  # 知识库路径
  
llm:
  provider: openai        # LLM 提供商
  model: gpt-4o-mini      # 模型名称
  api_key: sk-xxx         # API 密钥
  base_url: https://api.openai.com/v1  # API 地址（可选）
```

**支持哪些 LLM？**

| 提供商 | provider | model 示例 |
|--------|----------|------------|
| OpenAI | openai | gpt-4o-mini, gpt-4o |
| Anthropic | anthropic | claude-3-opus |
| 国内大模型 | openai-compatible | 取决于具体模型 |

**国内用户推荐**：
- 百炼：`base_url: https://dashscope.aliyuncs.com/compatible-mode/v1`
- 智谱：`base_url: https://open.bigmodel.cn/api/paas/v4`

---

### 初始化知识库

```bash
# 创建目录结构
python3 -m tools.cli init

# 或者设置别名
alias wiki='python3 -m tools.cli'
wiki init
```

生成的目录结构：
```
knowledge-base/
├── raw/
│   ├── articles/     # 放文章
│   ├── pdfs/         # 放 PDF
│   └── transcripts/  # 放转录
├── wiki/
│   ├── concepts/     # 概念页（自动生成）
│   ├── entities/     # 实体页（自动生成）
│   ├── sources/      # 来源页（自动生成）
│   └── outputs/      # 产出页（自动生成）
└── config/
    └── kb.yaml       # 配置文件
```

---

## 五、使用流程：三步走

### 第一步：放入素材

把你想要处理的内容放到 `raw/` 目录：

```bash
# 文章
raw/articles/某篇文章.md

# PDF
raw/pdfs/某个报告.pdf

# 转录
raw/transcripts/某视频转录.txt
```

**如何获取素材？**

| 类型 | 推荐工具 |
|------|----------|
| 网页文章 | Obsidian Web Clipper、简悦 |
| PDF | 直接下载 |
| 视频 | Whisper 转录、剪映字幕导出 |
| 音频 | Whisper 转录 |

---

### 第二步：处理素材

```bash
# 处理单个文件
wiki ingest raw/articles/my-article.md

# 处理整个目录
wiki ingest raw/articles/

# 预览（不实际写入）
wiki ingest raw/articles/my-article.md --dry-run
```

**处理过程中发生了什么？**

1. LLM 读取素材内容
2. 提取关键洞察 → 写入 `sources/`
3. 识别概念 → 创建/更新 `concepts/`
4. 识别实体 → 创建/更新 `entities/`
5. 建立双向链接
6. 更新全局索引
7. 记录操作日志

**粒度控制**：
- 概念页：最多 20 个/来源
- 实体页：最多 10 个/来源
- 只提取核心，不会过度拆分

---

### 第三步：查询知识

```bash
# 问问题
wiki query "什么是 Agent Operating System?"

# 保存答案
wiki query "对比 Skill 和 MCP 的区别" --save
```

**支持的问题类型**：

| 类型 | 示例 | 输出 |
|------|------|------|
| 定义 | "什么是 X？" | 定义 + 要点 |
| 对比 | "X 和 Y 的区别" | 对比表 |
| 关系 | "X 和 Y 的关系" | 关系描述 |
| 列举 | "有哪些 X" | 列表 |
| 深度 | "详细解释 X" | 详细分析 |

---

## 六、进阶用法

### 与 Obsidian 配合

My Wiki 生成的 markdown 完全兼容 Obsidian：

1. 打开 Obsidian
2. 选择知识库目录作为 vault
3. 浏览 `wiki/concepts/`、`wiki/entities/`
4. 点击链接探索知识网络
5. 使用 Graph View 可视化关联

**双向链接示例**：
```
concepts/Agent-Operating-System.md
    ├── 相关概念：[[concepts/多-Agent-体系]]
    ├── 相关概念：[[concepts/Prompt-编排]]
    └── 反向引用：被 [[entities/Claude-Code]] 引用
```

在 Obsidian 中，点击链接即可跳转，形成知识网络。

---

### 健康检查

定期检查知识库健康状态：

```bash
# 完整检查
wiki lint

# 快速检查
wiki lint --quick
```

**检查项**：

| 问题 | 说明 |
|------|------|
| 缺失页 | wikilinks 指向不存在的页面 |
| 孤立页 | 没有被任何页面引用 |
| 矛盾 | 概念定义不一致 |
| 过时 | 来源超过 365 天 |

---

### 查看统计

```bash
# 基本信息
wiki status

# 最近操作
wiki status --recent
```

输出示例：
```
知识库状态
==========

Wiki 内容:
  来源页:   5
  概念页:  23
  实体页:   8
  产出页:   3
  总计:    39

Raw 素材:
  文章:    3
  PDF:     2
  总计:    5
```

---

## 七、典型应用场景

### 场景 1：研究一个新领域

**问题**：想深入研究 AI Agent，不知道从哪开始

**解决方案**：
```bash
# 1. 收集素材
- 找 5-10 篇 Agent 相关文章
- 下载几份重要论文 PDF
- 放入 raw/

# 2. 批量处理
wiki ingest raw/

# 3. 形成知识体系
- concepts/ 下会生成 Agent 相关概念
- entities/ 下会生成重要项目/人物
- 概念之间自动关联

# 4. 查询探索
wiki query "Agent 的核心技术栈是什么？"
wiki query "对比不同 Agent 框架的优劣"
```

**收益**：
- 系统化理解，而不是碎片化阅读
- 可以随时查询，不用重新阅读
- 持续积累，越用越丰富

---

### 场景 2：构建个人技术知识库

**问题**：工作中积累了很多技术笔记，但很乱

**解决方案**：
```bash
# 1. 整理现有笔记
把笔记分类放入 raw/articles/

# 2. 批量处理
wiki ingest raw/articles/

# 3. 形成结构
- 自动提取技术概念
- 自动关联相关主题
- 形成知识网络

# 4. 日常使用
- 遇到问题：wiki query "..."
- 新学内容：放到 raw/，ingest
```

**收益**：
- 碎片笔记变成结构知识
- 查找快速，关联清晰
- 持续积累，形成个人知识资产

---

### 场景 3：学习一门新技术

**问题**：想学习 Rust，资料很多，学完就忘

**解决方案**：
```bash
# 1. 收集资料
- 官方教程
- 优秀博客文章
- 视频教程转录
- 放入 raw/

# 2. 构建 Rust 知识库
wiki ingest raw/

# 3. 查询巩固
wiki query "Rust 的所有权规则是什么？"
wiki query "对比 Rust 和 Go 的并发模型"

# 4. 持续更新
- 新学的内容继续 ingest
- 知识库越来越丰富
```

**收益**：
- 系统化学习，不是碎片化
- 随时查询巩固
- 形成可复用的知识资产

---

## 八、常见问题

### Q1: 我需要懂编程吗？

**不需要**。My Wiki 是命令行工具，但只有几个简单命令：
- `wiki ingest` — 处理素材
- `wiki query` — 查询知识
- `wiki lint` — 健康检查
- `wiki status` — 查看状态

复制粘贴就能用。

---

### Q2: API 费用贵吗？

**取决于你的使用量**。

估算：
- 处理一篇 3000 字文章：约 0.01-0.03 元（gpt-4o-mini）
- 查询一次：约 0.01-0.02 元

建议：
- 使用 gpt-4o-mini（便宜）
- 国内用户可用百炼/智谱（更便宜）

---

### Q3: 支持中文吗？

**完全支持**。My Wiki 对中英文内容都能处理。

---

### Q4: 和 Notion/Obsidian 有什么区别？

| 工具 | 定位 |
|------|------|
| Notion | 笔记 + 协作，手动整理 |
| Obsidian | 笔记 + 链接，手动整理 |
| My Wiki | 知识管理，**自动整理** |

My Wiki 的独特价值：
- **自动化**：LLM 帮你整理，不用手动
- **结构化**：概念、实体自动提取
- **关联化**：双向链接自动建立

**最佳实践**：My Wiki + Obsidian
- My Wiki 负责自动整理
- Obsidian 负责可视化浏览

---

### Q5: 数据安全吗？

**数据在你自己手里**：
- 所有数据存储在本地
- API 调用只发送需要处理的内容
- 不会上传到第三方服务器

**敏感内容处理**：
- API key 存在本地配置文件
- 不要把敏感信息（密码、密钥）放入 raw/

---

### Q6: 能处理图片/视频吗？

**当前版本**：
- 图片：暂不支持（计划中）
- 视频：需要先转录成文字（用 Whisper 等工具）

---

## 九、下一步

### 新手建议路径

1. **安装部署**（10 分钟）
   - 克隆项目
   - 安装依赖
   - 配置 API

2. **试用功能**（20 分钟）
   - 放入一篇文章
   - 执行 ingest
   - 执行 query
   - 在 Obsidian 查看

3. **日常使用**
   - 遇到好内容 → 放入 raw/
   - 有时间 → wiki ingest
   - 需要查询 → wiki query
   - 定期 → wiki lint

---

### 进阶探索

- **自定义配置**：修改 config/kb.yaml
- **批量处理**：wiki ingest raw/articles/
- **深度查询**：使用 --save 保存有价值答案
- **Obsidian 集成**：利用 Graph View 可视化

---

## 十、资源链接

- **GitHub 仓库**：https://github.com/Masongmx/my-wiki
- **中文文档**：README_CN.md
- **英文文档**：README.md
- **快速开始**：docs/getting-started.md

---

## 结语

My Wiki 的核心理念是：**让知识积累，而不是消耗**。

传统方式：每次都用完即弃
My Wiki：每次都在积累

你的知识应该像滚雪球一样，越滚越大，而不是每次都从零开始。

---

_最后更新：2026-04-05_