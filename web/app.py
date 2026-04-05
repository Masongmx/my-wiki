#!/usr/bin/env python3
"""My Wiki Web UI - 主入口"""

import streamlit as st
from pathlib import Path
import yaml


def load_config():
    """加载配置"""
    kb_root = Path("/mnt/d/knowledge-base")
    config_path = kb_root / "config" / "kb.yaml"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_kb_root():
    """获取知识库根目录"""
    return Path("/mnt/d/knowledge-base")


def main():
    st.set_page_config(
        page_title="My Wiki",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 自定义样式
    st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 标题
    st.markdown('<div class="main-header">📚 My Wiki</div>', unsafe_allow_html=True)
    
    kb_root = get_kb_root()
    
    # 快速统计（首页）
    col1, col2, col3, col4 = st.columns(4)
    
    def count_files(directory):
        if directory.exists():
            return len(list(directory.glob("*.md")))
        return 0
    
    with col1:
        st.metric("概念", count_files(kb_root / "wiki" / "concepts"))
    
    with col2:
        st.metric("实体", count_files(kb_root / "wiki" / "entities"))
    
    with col3:
        st.metric("来源", count_files(kb_root / "wiki" / "sources"))
    
    with col4:
        st.metric("产出", count_files(kb_root / "wiki" / "outputs"))
    
    st.markdown("---")
    
    # 快速搜索
    st.subheader("🔍 快速搜索")
    query = st.text_input("输入问题或关键词", key="home_search")
    
    if query:
        st.info(f"点击左侧 '🔍 Search' 页面进行深度搜索")
    
    # 最近活动
    st.subheader("📅 最近活动")
    log_file = kb_root / "wiki" / "_meta" / "log.md"
    
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 提取最近的几条日志
        import re
        entries = re.findall(
            r'##\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*\|\s*([^\|]+)\s*\|\s*([^\n]+)',
            content
        )
        
        if entries:
            for entry in entries[-5:]:
                st.text(f"{entry[0]} | {entry[1]} | {entry[2]}")
        else:
            st.text("暂无活动记录")
    else:
        st.text("暂无活动记录")
    
    # 页面导航提示
    st.markdown("---")
    st.markdown("""
    ### 📑 功能导航
    
    - **📊 Status**: 知识库统计与健康状态
    - **📚 Browse**: 浏览概念、实体、来源
    - **🔍 Search**: 深度搜索知识库
    - **📤 Upload**: 上传素材文件
    """)


if __name__ == "__main__":
    main()