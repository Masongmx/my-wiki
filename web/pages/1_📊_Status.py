#!/usr/bin/env python3
"""Status 页面 - 知识库统计与健康状态"""

import streamlit as st
from pathlib import Path
import yaml
import re


def get_kb_root():
    return Path("/mnt/d/knowledge-base")


def count_files(directory):
    if directory.exists():
        return len(list(directory.glob("*.md")))
    return 0


def get_file_list(directory, limit=10):
    """获取文件列表（按修改时间排序）"""
    if not directory.exists():
        return []
    
    files = sorted(
        directory.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    return files[:limit]


def read_recent_logs(log_file, limit=10):
    """读取最近操作日志"""
    if not log_file.exists():
        return []
    
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    entries = re.findall(
        r'##\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*([^\|]+)\s*\|\s*([^\n]+)',
        content
    )
    
    return entries[::-1][:limit]


def check_health(kb_root):
    """检查健康状态"""
    lint_file = kb_root / "wiki" / "_meta" / "lint-report.md"
    
    if lint_file.exists():
        with open(lint_file, "r", encoding="utf-8") as f:
            content = f.read(500)
        
        match = re.search(r'total_issues:\s*(\d+)', content)
        if match:
            return int(match.group(1))
    
    return None


def main():
    st.set_page_config(
        page_title="Status - My Wiki",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 知识库状态")
    
    kb_root = get_kb_root()
    
    # Wiki 内容统计
    st.subheader("Wiki 内容")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("来源 (sources)", count_files(kb_root / "wiki" / "sources"))
    
    with col2:
        st.metric("概念 (concepts)", count_files(kb_root / "wiki" / "concepts"))
    
    with col3:
        st.metric("实体 (entities)", count_files(kb_root / "wiki" / "entities"))
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("产出 (outputs)", count_files(kb_root / "wiki" / "outputs"))
    
    with col5:
        st.metric("文章 (articles)", count_files(kb_root / "wiki" / "articles"))
    
    with col6:
        wiki_total = (
            count_files(kb_root / "wiki" / "sources") +
            count_files(kb_root / "wiki" / "concepts") +
            count_files(kb_root / "wiki" / "entities") +
            count_files(kb_root / "wiki" / "outputs")
        )
        st.metric("Wiki 总计", wiki_total)
    
    # Raw 素材统计
    st.subheader("Raw 素材")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("文章 (articles)", count_files(kb_root / "raw" / "articles"))
    
    with col2:
        st.metric("PDF (pdfs)", count_files(kb_root / "raw" / "pdfs"))
    
    with col3:
        st.metric("转录 (transcripts)", count_files(kb_root / "raw" / "transcripts"))
    
    # 健康状态
    st.subheader("🔍 健康状态")
    
    issues = check_health(kb_root)
    
    if issues is not None:
        if issues == 0:
            st.success("✅ 健康（无问题）")
        elif issues < 5:
            st.warning(f"⚠️ 轻度问题（{issues} 个）")
        else:
            st.error(f"❌ 需要修复（{issues} 个问题）")
    else:
        st.info("未运行 lint 检查")
    
    # 最近操作
    st.subheader("📅 最近操作")
    
    log_file = kb_root / "wiki" / "_meta" / "log.md"
    logs = read_recent_logs(log_file)
    
    if logs:
        for log in logs:
            st.text(f"{log[0]} | {log[1]} | {log[2]}")
    else:
        st.text("暂无操作记录")
    
    # 来源列表
    st.subheader("📚 来源列表")
    
    sources_dir = kb_root / "wiki" / "sources"
    source_files = get_file_list(sources_dir)
    
    if source_files:
        for src in source_files[:10]:
            st.text(f"- {src.stem}")
    else:
        st.text("暂无来源")


if __name__ == "__main__":
    main()