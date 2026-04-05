#!/usr/bin/env python3
"""Search 页面 - 搜索知识库"""

import streamlit as st
from pathlib import Path
import yaml
import os
import re
import subprocess
from openai import OpenAI


def get_kb_root():
    return Path("/mnt/d/knowledge-base")


def load_config():
    """加载配置"""
    kb_root = get_kb_root()
    config_path = kb_root / "config" / "kb.yaml"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_api_key():
    """获取 API key"""
    kb_root = get_kb_root()
    
    # 从 key.txt 读取
    key_file = kb_root / "key.txt"
    if key_file.exists():
        with open(key_file, "r") as f:
            return f.read().strip()
    
    # 从环境变量
    api_key = os.getenv("BAILIAN_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    return None


def get_llm_client():
    """获取 LLM 客户端"""
    api_key = get_api_key()
    
    if not api_key:
        return None, None
    
    cfg = load_config()
    llm_config = cfg.get("llm", {})
    
    base_url = llm_config.get("base_url", "https://coding.dashscope.aliyuncs.com/v1")
    model = llm_config.get("model", "qwen3.5-plus")
    
    return OpenAI(
        api_key=api_key,
        base_url=base_url
    ), model


def classify_question(query):
    """分类问题类型"""
    query_lower = query.lower()
    
    if "什么是" in query or "何为" in query or "定义" in query:
        return "definition"
    
    if "对比" in query or "区别" in query or "比较" in query or "vs" in query_lower:
        return "comparison"
    
    if "关系" in query or "联系" in query or "关联" in query:
        return "relation"
    
    if "有哪些" in query or "列出" in query or "列举" in query:
        return "list"
    
    if "详细" in query or "深入" in query or "解析" in query or "深度" in query:
        return "deep"
    
    return "explore"


def extract_keywords(query):
    """提取关键词"""
    question_words = [
        "什么是", "何为", "什么叫",
        "如何", "怎么", "怎样",
        "为什么", "为何",
        "哪个", "哪些", "什么",
        "有没有", "是否存在",
        "能不能", "可以吗", "是否",
        "介绍一下", "讲一下", "说说",
        "帮我", "请", "请问",
        "对比", "区别", "比较", "vs",
        "详细", "深入", "解析",
        "？", "?", "！", "!", "。", ".", "，", ","
    ]
    
    cleaned = query
    for word in question_words:
        cleaned = cleaned.replace(word, "")
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    words = cleaned.split()
    keywords = [w for w in words if len(w) >= 2][:3]
    
    return keywords if keywords else [cleaned[:15]]


def search_files(kb_root, keywords, limit=5):
    """搜索相关文件"""
    exclude_dirs = [".obsidian", ".smart-env", ".git", ".venv", "node_modules", "__pycache__"]
    
    results = set()
    
    wiki_dirs = [
        kb_root / "wiki" / "concepts",
        kb_root / "wiki" / "entities",
        kb_root / "wiki" / "sources",
        kb_root / "wiki" / "outputs",
    ]
    
    for keyword in keywords:
        if not keyword:
            continue
        
        for wiki_dir in wiki_dirs:
            if wiki_dir.exists():
                files = grep_search(wiki_dir, keyword, exclude_dirs)
                results.update(files)
        
        if len(results) < limit:
            files = grep_search(kb_root, keyword, exclude_dirs)
            results.update(files)
    
    scored = []
    for file in results:
        score = 0
        file_str = str(file)
        for kw in keywords:
            if kw.lower() in file_str.lower():
                score += 1
        scored.append((score, file))
    
    scored.sort(key=lambda x: (-x[0], x[1]))
    
    return [f[1] for f in scored[:limit]]


def grep_search(directory, term, exclude_dirs):
    """grep 搜索"""
    results = set()
    
    try:
        cmd = ["rg", "-l", "-i", term, str(directory)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            for f in files:
                if f and not any(exc in f for exc in exclude_dirs):
                    results.add(Path(f))
            return results
    except FileNotFoundError:
        pass
    except Exception:
        pass
    
    try:
        cmd = ["grep", "-r", "-l", "-i", term, str(directory)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            for f in files:
                if f and not any(exc in f for exc in exclude_dirs):
                    results.add(Path(f))
    except Exception:
        pass
    
    return results


def read_file_content(file_path, max_length=2000):
    """读取文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if len(content) > max_length:
            content = content[:max_length] + "\n...[已截断]"
        
        return content
    except Exception:
        return ""


def generate_answer(client, model, query, contexts, question_type):
    """生成答案"""
    if not contexts:
        return "抱歉，没有找到相关内容。"
    
    context_text = "\n\n---\n\n".join([
        f"【来源: {ctx['file']}】\n{ctx['content']}"
        for ctx in contexts
    ])
    
    prompts = {
        "definition": f"""基于以下参考内容，简洁定义问题中的概念。

参考内容：
{context_text}

问题：{query}

请提供：
1. 一句话定义（不超过50字）
2. 核心要点（3-5个）
3. 相关概念链接（如有）""",
        
        "comparison": f"""基于以下参考内容，对比问题中的两个对象。

参考内容：
{context_text}

问题：{query}

请提供对比表格：
| 维度 | A | B |
|------|------|------|
| ... | ... | ... |

并简要总结核心差异。""",
        
        "relation": f"""基于以下参考内容，分析问题中对象的关系。

参考内容：
{context_text}

问题：{query}

请提供：
1. 关系描述
2. 共同点
3. 差异点""",
        
        "list": f"""基于以下参考内容，列举相关内容。

参考内容：
{context_text}

问题：{query}

请提供列表形式回答。""",
        
        "deep": f"""基于以下参考内容，深入解析问题。

参考内容：
{context_text}

问题：{query}

请提供详细分析，包含：
1. 背景/定义
2. 核心内容
3. 关键洞察
4. 实践建议""",
        
        "explore": f"""基于以下参考内容，回答问题。

参考内容：
{context_text}

问题：{query}

请提供清晰、准确的回答，标注参考来源。"""
    }
    
    prompt = prompts.get(question_type, prompts["explore"])
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"生成答案时出错: {e}"


def main():
    st.set_page_config(
        page_title="Search - My Wiki",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 搜索知识库")
    
    # 输入框
    query = st.text_input("输入问题或关键词", key="search_query")
    
    # 搜索选项
    col1, col2 = st.columns(2)
    
    with col1:
        use_llm = st.checkbox("使用 LLM 生成答案", value=True)
    
    with col2:
        limit = st.slider("参考文档数量", min_value=1, max_value=10, value=3)
    
    if not query:
        st.info("请输入问题或关键词")
        return
    
    kb_root = get_kb_root()
    
    # 提取关键词并搜索
    keywords = extract_keywords(query)
    
    with st.spinner("搜索中..."):
        files = search_files(kb_root, keywords, limit)
    
    if not files:
        st.warning("没有找到相关内容")
        return
    
    # 显示搜索结果
    st.subheader(f"找到 {len(files)} 个相关文档")
    
    contexts = []
    sources = []
    
    for file in files:
        content = read_file_content(file, 1500)
        if content:
            rel_path = file.relative_to(kb_root)
            contexts.append({
                "file": str(rel_path),
                "content": content
            })
            sources.append(str(rel_path))
            
            with st.expander(f"📄 {rel_path}"):
                st.markdown(content[:300] + "...")
    
    # 生成答案
    if use_llm and contexts:
        st.subheader("💡 生成的答案")
        
        client, model = get_llm_client()
        
        if client:
            question_type = classify_question(query)
            
            with st.spinner("生成答案中..."):
                answer = generate_answer(client, model, query, contexts, question_type)
            
            st.markdown(answer)
            
            # 参考来源
            st.markdown("---")
            st.caption("参考来源:")
            for src in sources:
                st.caption(f"- {src}")
        else:
            st.error("未配置 API key，无法生成答案")
            st.info("请设置环境变量 BAILIAN_API_KEY 或在知识库 config/key.txt 中配置")


if __name__ == "__main__":
    main()