# Troubleshooting | 常见问题解答

> 本文档帮助你解决常见问题
> 
> This document helps you solve common issues

---

## Installation Issues | 安装问题

### Q: pip install failed | pip安装失败

**Cause | 原因**：Network issue or pip version too low | 网络问题或pip版本过低

**Solution | 解决方案**：
```bash
pip install --upgrade pip
pip install my-wiki --timeout 60
```

---

### Q: wiki command not found | wiki命令找不到

**Cause | 原因**：Command not in PATH | 命令未加入PATH

**Solution | 解决方案**：
```bash
# Check installation location | 检查安装位置
pip show my-wiki

# Add to PATH (if needed) | 添加到PATH（如需要）
export PATH="$HOME/.local/bin:$PATH"
```

---

## Configuration Issues | 配置问题

### Q: config/kb.yaml not found | 配置文件找不到

**Cause | 原因**：Not initialized or wrong path | 未初始化或路径错误

**Solution | 解决方案**：
```bash
# Initialize config | 初始化配置
wiki init

# Check config location | 检查配置位置
ls config/kb.yaml
```

---

### Q: API key not found | API密钥找不到

**Cause | 原因**：key.txt or environment variable missing | key.txt或环境变量缺失

**Solution | 解决方案**：
```bash
# Create key.txt | 创建key.txt
echo "YOUR_API_KEY" > key.txt

# Or set environment variable | 或设置环境变量
export BAILIAN_API_KEY="YOUR_API_KEY"
export OPENAI_API_KEY="YOUR_API_KEY"
```

---

## Ingest Issues | Ingest问题

### Q: ingest failed "unsupported file format" | 不支持的文件格式

**Cause | 原因**：File type not supported | 文件类型不在支持列表

**Solution | 解决方案**：

| Supported formats | 支持格式 |
|-------------------|----------|
| .md, .txt | ✅ Markdown, Text |
| .pdf, .docx, .pptx, .xlsx | ✅ Documents |
| .doc, .xls, .ppt | ⚠️ Old formats (need conversion) | ⚠️ 旧格式（需转换） |

```bash
# Convert .doc to .docx | 转换.doc为.docx
libreoffice --headless --convert-to docx file.doc

# Convert .xls to .xlsx | 转换.xls为.xlsx
libreoffice --headless --convert-to xlsx file.xls
```

---

### Q: ingest very slow | ingest速度很慢

**Cause | 原因**：Large files or many files | 文件过大或数量过多

**Solution | 解决方案**：
```bash
# Check file sizes | 检查文件大小
wiki status

# Process smaller batches | 分批处理
wiki ingest raw/articles/ --dry-run  # Preview first
```

---

## Query Issues | Query问题

### Q: query returns empty results | 查询返回空结果

**Cause | 原因**：Wiki not generated or concepts missing | Wiki未生成或概念缺失

**Solution | 解决方案**：
```bash
# Check wiki status | 检查wiki状态
wiki status

# Run lint to check | 运行lint检查
wiki lint --quick
```

---

### Q: query answer quality poor | 查询答案质量差

**Cause | 原因**：Insufficient context or model limitation | 上下文不足或模型限制

**Solution | 解决方案**：
```bash
# Use stronger model | 使用更强的模型
# Edit config/kb.yaml:
llm:
  model: gpt-4  # or bailian/qwen3-coder-next

# Save query for reference | 保存查询结果
wiki query "your question" --save
```

---

## Graph Issues | 图谱问题

### Q: wiki graph shows blank | 图谱显示空白

**Cause | 原因**：No backlinks data | 无反向链接数据

**Solution | 解决方案**：
```bash
# Check backlinks | 检查反向链接
ls wiki/_backlinks.json

# Re-run ingest to generate backlinks | 重新运行ingest生成反向链接
wiki ingest raw/articles/
```

---

### Q: God nodes list empty | 核心节点列表为空

**Cause | 原因**：No articles or all orphan pages | 无文章或全是孤儿页

**Solution | 解决方案**：
```bash
# Check articles | 检查文章数量
wiki status

# Run lint to fix orphan pages | 运行lint修复孤儿页
wiki lint --orphans
```

---

## Health Check Issues | 健康检查问题

### Q: health shows dependency missing | 依赖缺失

**Cause | 原因**：Optional dependencies not installed | 可选依赖未安装

**Solution | 解决方案**：

| Dependency | 依赖 | Purpose | 用途 |
|------------|------|---------|------|
| click | | Required | CLI framework |
| pyyaml | | Required | YAML config |
| loguru | | Required | Logging |
| openai | | Required | LLM API |
| playwright | | Optional | WeChat fetch | 微信抓取 |
| aiohttp | | Optional | Xiaohongshu | 小红书抓取 |

```bash
# Install optional dependencies | 安装可选依赖
pip install playwright aiohttp pycryptodome
```

---

## Other Issues | 其他问题

### Q: How to backup knowledge base | 如何备份知识库

**Solution | 解决方案**：
```bash
# Backup entire directory | 备份整个目录
tar -czf kb-backup.tar.gz data/

# Backup cache only | 仅备份缓存
wiki status  # Shows cache location
```

---

### Q: How to reset knowledge base | 如何重置知识库

**Solution | 解决方案**：
```bash
# ⚠️ This will delete all data | ⚠️ 这会删除所有数据
rm -rf data/wiki/
wiki init
```

---

## Get Help | 获取帮助

| Method | 方式 |
|--------|------|
| GitHub Issues | https://github.com/Masongmx/my-wiki/issues |
| Documentation | docs/ directory | docs/ 目录 |

---

**如果以上方案都不能解决问题，请提交Issue并附上：**
**If above solutions don't work, please submit Issue with:**

- `wiki health` output | wiki health输出
- `wiki lint --quick` output | wiki lint输出
- Error message | 错误信息