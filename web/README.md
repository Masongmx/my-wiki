# My Wiki Web UI

基于 Streamlit 的知识库 Web 界面。

## 功能

- **首页**: 统计概览、快速搜索、最近活动
- **📊 Status**: 知识库统计与健康状态
- **📚 Browse**: 浏览概念、实体、来源、产出
- **🔍 Search**: 深度搜索知识库（支持 LLM 生成答案）
- **📤 Upload**: 上传素材文件到 raw 目录

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 配置

API key 配置（用于搜索页生成答案）：

1. **环境变量**:
   ```bash
   export BAILIAN_API_KEY="your-api-key"
   ```

2. **或配置文件**:
   在 `/mnt/d/knowledge-base/config/key.txt` 中写入 API key

## 启动

```bash
# 启动 Web UI
streamlit run app.py

# 或指定端口
streamlit run app.py --server.port 8501
```

## 使用

### 首页

- 显示知识库统计（概念、实体、来源、产出数量）
- 快速搜索提示
- 最近操作记录

### Status 页面

- 详细统计（Wiki 内容、Raw 素材）
- 健康状态（lint 检查结果）
- 最近操作日志
- 来源列表

### Browse 页面

- 选择类型（concepts/entities/sources/outputs）
- 查看文件列表
- 预览和完整内容显示

### Search 页面

- 输入问题或关键词
- 自动提取关键词并搜索相关文档
- 可选使用 LLM 生成答案（需要配置 API key）
- 显示参考来源

### Upload 页面

- 选择素材类型（articles/pdfs/transcripts/assets）
- 上传文件
- 自动保存到对应的 raw 目录

## 后续处理

上传素材后，在命令行使用 `kb ingest` 处理：

```bash
# 处理单个文件
kb ingest raw/articles/your-file.md

# 批量处理
kb ingest --batch
```

## 技术栈

- **Streamlit**: Web UI 框架
- **OpenAI SDK**: LLM API 调用
- **复用现有代码**: wiki/query.py, wiki/status.py 等核心逻辑

## 知识库路径

- 知识库根目录: `/mnt/d/knowledge-base`
- 配置文件: `/mnt/d/knowledge-base/config/kb.yaml`
- Web UI 目录: `/mnt/d/my-wiki/web/`

## 注意事项

- API key 仅用于搜索页生成答案功能
- 上传功能仅保存文件，不自动处理
- 建议界面简洁，功能优先

## 开发说明

本项目遵循开发者铁律：

1. 不加用户没要求的功能
2. 不过度抽象
3. 先读代码再改代码
4. 复用现有逻辑

---

_开发者专注于代码质量。_